# -*- coding: gbk -*-
"""删除 motor_bldc.c 里的 18 次/圈前馈（宏、表、钩子），并还原 PID 参数。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
txt = io.open(P, encoding='gbk', errors='replace').read()
nl = '\r\n' if '\r\n' in txt else '\n'
L = txt.split(nl)
print('换行符=%s 原行数=%d' % ('CRLF' if nl == '\r\n' else 'LF', len(L)))


def idx(pred, start=0):
    for i in range(start, len(L)):
        if pred(L[i]):
            return i
    return -1


# ---- 1. 定位三个区块（用内容断言，不依赖硬编码行号）----
i_cmt = idx(lambda s: 'Periodic load locked to shaft angle' in s)
i_def = idx(lambda s: s.strip().startswith('#define MOTOR_COGGING_COMP'))
i_tab = idx(lambda s: 'static const int16_t uq_comp_18x' in s)
assert i_cmt > 0 and i_def > i_cmt and i_tab > i_def, '宏/表定位失败'

# 表结束的 }; 行
i_tab_end = idx(lambda s: s.strip() == '};', i_tab)
assert i_tab_end > i_tab, '表结束行定位失败'

# ---- 2. 循环内的两个 #if 块 ----
i_if1 = idx(lambda s: s.strip() == '#if MOTOR_COGGING_COMP',
            idx(lambda s: 'void bldc_velocity_loop' in s))
assert i_if1 > 0, '#if(声明) 未找到'
i_end1 = idx(lambda s: s.strip() == '#endif', i_if1)
i_if2 = idx(lambda s: s.strip() == '#if MOTOR_COGGING_COMP', i_end1 + 1)
assert i_if2 > i_end1, '第二个 #if 未找到'
i_end2 = idx(lambda s: s.strip() == '#endif', i_if2)

print('注释块 %d, 宏 %d, 表 %d..%d, #if块1 %d..%d, #if块2 %d..%d'
      % (i_cmt + 1, i_def + 1, i_tab + 1, i_tab_end + 1,
         i_if1 + 1, i_end1 + 1, i_if2 + 1, i_end2 + 1))

# ---- 3. 从后往前删（保留各块后的一个空行）----
del L[i_if2:i_end2 + 2]      # 第二个 #if 块 + 其后空行
del L[i_if1:i_end1 + 1]      # 第一个 #if 块（声明）
del L[i_cmt:i_tab_end + 2]   # 注释 + 宏 + 表 + 其后空行

txt = nl.join(L)

# ---- 4. 还原参数 ----
RESTORE = {
    'velocity_pid_pan': {'kp': '0.70', 'ki': '0.01', 'kd': '0.0',
                         'integral_max': '270000.0', 'output_max': '4000.0'},
    'position_pid': {'kp': '7.0'},
}
for name, kv in RESTORE.items():
    i = txt.find('const PID_t %s' % name)
    assert i > 0, '%s 未找到' % name
    j = txt.find('};', i)
    blk = txt[i:j]
    new = blk
    for k, val in kv.items():
        pat = re.compile(r'(\.%s\s*=\s*)(-?[0-9.]+f)' % k)
        assert pat.search(new), '%s.%s 未找到' % (name, k)
        old = pat.search(new).group(2)
        new = pat.sub(lambda m: m.group(1) + val + 'f', new, count=1)
        print('  %s.%s: %s -> %sf' % (name, k, old, val))
    txt = txt[:i] + new + txt[j:]

io.open(P, 'w', encoding='gbk', errors='replace').write(txt)

after = txt.split(nl)
print('')
print('新行数=%d  残留检查: MOTOR_COGGING_COMP=%d  uq_comp_18x=%d  comp_pos=%d'
      % (len(after), txt.count('MOTOR_COGGING_COMP'),
         txt.count('uq_comp_18x'), txt.count('comp_pos')))
