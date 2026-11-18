# -*- coding: cp936 -*-
"""按带 u 的映射检查 rule_fallback 是否挂上"""
import io
import sys
import traceback

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, r'D:\bProject\pid_tuner')
import pid_tuner as pt

pt._VOFA_MAP = "y=0,r=1,u=3"
t, u, y, r = pt.read_data_file(r'D:\Codebuddy\tmp\vofa_hex7.txt', dt=0.05)
print('n=%d  u_is_none=%s  r_is_none=%s' % (len(t), u is None, r is None))

info, an = pt.analyze(t, u, y, r=r,
                      current_pid={"Kp": 0.56, "Ki": 0.01, "Kd": 0.0})
print('kind =', an.get('kind'))
print('has rule_fallback =', 'rule_fallback' in an)
fb = an.get('rule_fallback')
if fb:
    print('  action =', fb.get('action'))
    print('  adjusted =', fb.get('adjusted'))
else:
    # 手工复算一次, 看是哪一步出错
    print('--- manual recompute ---')
    try:
        rec = pt.recommended_sample_time(an['ident']['K'], an['ident']['T'],
                                         an['ident']['tau'])
        now = t[1] - t[0]
        print('  rec=%.6g  now=%.6g  slow=%s' % (rec, now, now > rec * 2.0))
        f2 = pt.closed_loop_feature_const(t, r, y)
        a2 = pt.build_closed_analysis(f2, {"Kp": 0.56, "Ki": 0.01, "Kd": 0.0},
                                      "balanced", None)
        print('  manual OK, adjusted =', a2.get('adjusted'))
    except Exception as exc:
        print('  manual FAILED:', type(exc).__name__, exc)
        traceback.print_exc()
