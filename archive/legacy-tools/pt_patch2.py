# -*- coding: cp936 -*-
"""第 2 步：采样严重不足时，报告里加警告并降低推荐值可信度

字节级修改：目标文件是 UTF-8，用 latin-1 逐字节读写，
新内容先 encode('utf-8') 再 decode('latin-1')，写入后字节即 UTF-8。
"""
import io
import shutil
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'
BAK = r'D:\Codebuddy\backup\pid_tuner-20261028\pid_tuner.step1.py'


def L(s):
    """把普通字符串转成 latin-1 可往返的字节代理"""
    return s.encode('utf-8').decode('latin-1')


src = io.open(TARGET, encoding='latin-1', newline='').read()
shutil.copyfile(TARGET, BAK)
before = len(src.encode('latin-1'))

# ---------- A1: 初始化标记 ----------
a1 = '''    _ts_rec = recommended_sample_time(K, T, tau)
    _ts_now = analysis.get("dt_ctrl")'''
if src.count(a1) != 1:
    print('anchor A1 count =', src.count(a1))
    sys.exit(1)
src = src.replace(a1, a1 + L('\n    _sampling_bad = False'))

# ---------- A2: 采样受限时判定"严重不足" ----------
a2 = L('''                f"想再快只能提高采样率。")''')
if src.count(a2) != 1:
    print('anchor A2 count =', src.count(a2))
    sys.exit(1)
src = src.replace(a2, a2 + L('\n            _sampling_bad = _ts_now > _ts_rec * 2.0'))

# ---------- B: 方案对比表前插入警告 ----------
b1 = '''    for w in info["warnings"]:
        add(f"  [!] {w}")
    add("")'''
if src.count(b1) != 1:
    print('anchor B count =', src.count(b1))
    sys.exit(1)
warn = '''
    if _sampling_bad:
        add("  " + "!" * 74)
        add(f"  !! 采样严重不足: Ts={_ts_now:.4g}s, 该对象建议 <= {_ts_rec:.4g}s"
            f" (差 {_ts_now / _ts_rec:.1f} 倍)")
        add("  !! 这个采样率下辨识出的模型不可信, 下表只作趋势参考, 请勿直接上机")
        add("  !! 建议: 把采集间隔降到 10~20ms, 或提供 --current-pid 走规则整定")
        add("  " + "!" * 74)
        add("")
'''
src = src.replace(b1, b1 + L(warn))

# ---------- C: 推荐标签加"慎用" ----------
c1 = L('''            tag = "  <== 推荐"''')
if src.count(c1) != 1:
    print('anchor C count =', src.count(c1))
    sys.exit(1)
src = src.replace(c1, L('            tag = "  <== 推荐(采样不足, 慎用)" if _sampling_bad'
                        ' else "  <== 推荐"'))

out = src.encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('bytes: %d -> %d  (+%d)' % (before, len(out), len(out) - before))
print('backup:', BAK)
