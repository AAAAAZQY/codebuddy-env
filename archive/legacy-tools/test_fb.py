# -*- coding: cp936 -*-
"""定位 rule_fallback 补算失败的原因"""
import io
import sys
import traceback

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, r'D:\bProject\pid_tuner')
import pid_tuner as pt

t, u, y, r = pt.read_data_file(r'D:\Codebuddy\tmp\vofa_hex7.txt', dt=0.05)
print('n=%d  r_is_none=%s' % (len(t), r is None))

try:
    f = pt.closed_loop_feature_const(t, r, y)
    print('feat keys:', sorted(f.keys())[:12])
except Exception as exc:
    print('closed_loop_feature_const FAILED:', type(exc).__name__, exc)
    traceback.print_exc()
    sys.exit(1)

try:
    an = pt.build_closed_analysis(f, {"Kp": 0.56, "Ki": 0.01, "Kd": 0.0},
                                  "balanced", None)
    print('build_closed_analysis OK, keys:', sorted(an.keys()))
    print('  action =', an.get('action'))
    print('  adjusted =', an.get('adjusted'))
except Exception as exc:
    print('build_closed_analysis FAILED:', type(exc).__name__, exc)
    traceback.print_exc()
    sys.exit(1)

try:
    rec = pt.recommended_sample_time(8.02318, 0.637144, 0.0617549)
    print('recommended_sample_time =', rec, ' dt=0.05 > 2x ?', 0.05 > rec * 2.0)
except Exception as exc:
    print('recommended_sample_time FAILED:', type(exc).__name__, exc)

# 走完整 analyze，看 rule_fallback 有没有挂上
info, an2 = pt.analyze(t, u, y, r=r, current_pid={"Kp": 0.56, "Ki": 0.01, "Kd": 0.0})
print('analyze kind =', an2.get('kind'), ' rule_fallback =',
      'YES' if an2.get('rule_fallback') else 'NO')
