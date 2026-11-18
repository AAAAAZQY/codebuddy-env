# -*- coding: gbk -*-
"""定位 motor_bldc.c 里前馈相关代码的全部位置。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
L = io.open(P, encoding='gbk', errors='replace').read().splitlines()

for i, l in enumerate(L):
    if 'MOTOR_COGGING_COMP' in l or 'uq_comp_18x' in l or 'comp_pos' in l:
        print('%4d| %s' % (i + 1, l.rstrip()[:100]))

print('')
print('=== 宏定义附近 (前 12 行 + 后 4 行) ===')
for i, l in enumerate(L):
    if l.strip().startswith('#define MOTOR_COGGING_COMP'):
        for k in range(max(0, i - 12), min(len(L), i + 5)):
            print('%4d| %s' % (k + 1, L[k].rstrip()[:100]))
        break
