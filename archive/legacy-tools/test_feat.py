# -*- coding: cp936 -*-
"""对比两种闭环特征对同一段数据的整定结论"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, r'D:\bProject\pid_tuner')
import pid_tuner as pt

pt._VOFA_MAP = "y=0,r=1,u=3"
t, u, y, r = pt.read_data_file(r'D:\Codebuddy\tmp\vofa_hex7.txt', dt=0.05)
cur = {"Kp": 0.56, "Ki": 0.01, "Kd": 0.0}
print('n=%d  r_none=%s' % (len(t), r is None))

for name, fn in (('const', pt.closed_loop_feature_const),
                 ('general', pt.closed_loop_feature)):
    try:
        f = fn(t, r, y)
        adj, notes, act = pt.rule_based_tune(f, cur)
        print('--- %s ---' % name)
        print('  action  :', act)
        print('  adjusted:', {k: adj[k] for k in ('Kp', 'Ki', 'Kd')})
        print('  ripple=%.3f decay=%s period=%s' % (
            f.get('ripple', 0), f.get('decay'), f.get('period')))
    except Exception as exc:
        print('--- %s FAILED: %s: %s' % (name, type(exc).__name__, exc))
