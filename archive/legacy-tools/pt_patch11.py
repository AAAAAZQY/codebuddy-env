# -*- coding: cp936 -*-
"""第 11 步：补算规则整定时优先用 general 特征（能识别目标变化，不会把减速当振荡）"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'

src = io.open(TARGET, encoding='latin-1', newline='').read()

old = '''                if _now > _rec * 2.0:
                    _f2 = closed_loop_feature_const(t, r, y)
                    an["rule_fallback"] = build_closed_analysis(
                        _f2, pid_used, mode, pref)'''

new = '''                if _now > _rec * 2.0:
                    # 优先用 general 特征: 它能识别"目标值在变"(减速段),
                    # 不会把减速当成振荡。退化时才用 const 版。
                    try:
                        _f2 = closed_loop_feature(t, r, y)
                    except Exception:       # noqa: BLE001
                        _f2 = closed_loop_feature_const(t, r, y)
                    an["rule_fallback"] = build_closed_analysis(
                        _f2, pid_used, mode, pref)'''

if src.count(old) != 1:
    print('anchor count =', src.count(old))
    sys.exit(1)

src = src.replace(old, new.encode('utf-8').decode('latin-1'))
out = src.encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('patched, bytes =', len(out))
