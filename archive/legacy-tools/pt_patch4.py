# -*- coding: cp936 -*-
"""第 4 步：
1) parse_data 入口识别 vofa hex 文本（让 GUI 粘贴也能用）
2) 转换时打印通道统计，便于确认 y/r/u 映射
"""
import io
import shutil
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'
BAK = r'D:\Codebuddy\backup\pid_tuner-20261028\pid_tuner.step3.py'


def L(s):
    return s.encode('utf-8').decode('latin-1')


src = io.open(TARGET, encoding='latin-1', newline='').read()
shutil.copyfile(TARGET, BAK)
before = len(src.encode('latin-1'))

# ---------- A: 全局诊断容器 ----------
a = '_VOFA_USED = [False]'
if src.count(a) != 1:
    print('anchor A count =', src.count(a))
    sys.exit(1)
src = src.replace(a, a + '\n_VOFA_DIAG = [None]')

# ---------- B: 转换时统计并打印各通道 ----------
b = '    lines = [head]'
if src.count(b) != 1:
    print('anchor B count =', src.count(b))
    sys.exit(1)
stat_code = '''
    _stat = []
    for _ch in range(len(frames[0])):
        _v = [fr[_ch] for fr in frames]
        _stat.append((_ch, min(_v), max(_v), sum(_v) / len(_v)))
    _VOFA_DIAG[0] = _stat
    _role = {}
    for _k, _idx in pick.items():
        if _idx is not None:
            _role[_idx] = _k
    print("  [vofa] \\u5171 %d \\u5e27, \\u901a\\u9053\\u7edf\\u8ba1(\\u786e\\u8ba4\\u6620\\u5c04):"
          % len(frames))
    for _ch, _lo, _hi, _mn in _stat:
        _tag = _role.get(_ch)
        print("    \\u901a\\u9053%d: min=%10.1f  max=%10.1f  mean=%10.1f  %s"
              % (_ch, _lo, _hi, _mn,
                 ("<== " + _tag) if _tag else ""))
'''
src = src.replace(b, stat_code + b)

# ---------- C: parse_data 入口识别 vofa 文本 ----------
c = L('    text = normalize_text(text)          # 全角标点/数字 -> 半角')
if src.count(c) != 1:
    print('anchor C count =', src.count(c))
    sys.exit(1)
vofa_hook = L('''

    # 粘贴进来的 vofa hex 文本也直接识别（GUI「粘贴数据」走这条路）
    try:
        _probe = text.encode("latin-1", "ignore")
        if _maybe_vofa(_probe):
            _csv = _vofa_to_csv(_probe, dt, _VOFA_MAP)
            if _csv:
                _VOFA_USED[0] = True
                text = _csv
    except Exception:       # noqa: BLE001
        pass''')
src = src.replace(c, c + vofa_hook)

out = src.encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('bytes: %d -> %d (+%d)' % (before, len(out), len(out) - before))
