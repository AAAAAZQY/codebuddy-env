# -*- coding: cp936 -*-
"""复现失败场景：粘贴框预填的示例注释 + 用户 hex 数据混合"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, r'D:\bProject\pid_tuner')
import pid_tuner as pt

hexdata = io.open(r'D:\Codebuddy\tmp\vofa_hex6.txt', encoding='utf-8').read()

tpl = ("# 例1: 有控制器输出 u (推荐, 走模型整定):\n"
       "#   time,u,y\n"
       "#   0.00,0.20,0.500\n"
       "#   0.04,0.70,0.512\n"
       "#\n"
       "# 例2: 只有目标值 r, 走经验规则整定(需填当前 PID)\n"
       "#   time,r,y\n"
       "#   0.00,0.0,0.000\n"
       "#   0.04,1.0,0.010\n")

mixed = tpl + hexdata
print('mixed tokens =', len(mixed.split()), ' len =', len(mixed))
t, u, y, r = pt.parse_data(mixed, dt=0.05)
print('parse OK: n=%d  u_is_none=%s  r_is_none=%s' % (len(t), u is None, r is None))

# 只贴示例（应该报错，说明没有被误判成 vofa）
try:
    pt.parse_data(tpl, dt=0.05)
    print('template-only: parsed (unexpected)')
except Exception as exc:
    print('template-only correctly rejected:', type(exc).__name__)
