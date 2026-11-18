# -*- coding: utf-8 -*-
"""Functional check: does integral_max actually change the simulation?"""
import importlib.util
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

spec = importlib.util.spec_from_file_location(
    'pid_tuner', r'D:\bProject\pid_tuner\pid_tuner.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print('simulate signature has integral_max:',
      'integral_max' in m.simulate.__code__.co_varnames)
print('module _INTEGRAL_MAX =', m._INTEGRAL_MAX)

kw = dict(K=1.0, T=1.0, tau=0.1, Kp=2.0, Ki=5.0, Kd=0.0,
          dt_sim=0.001, sp=1.0, T_end=12.0, dt_ctrl=0.01)

t0, y0, u0, _ = m.simulate(integral_max=None, **kw)
m._INTEGRAL_MAX = 0.5
t1, y1, u1, _ = m.simulate(**kw)          # picks up the module default
m._INTEGRAL_MAX = None
t2, y2, u2, _ = m.simulate(integral_max=0.5, **kw)   # explicit override

print('')
print('%-28s %10s %10s %10s' % ('case', 'max(y)', 'final y', 'max(u)'))
print('-' * 62)
for tag, ys, us in (('no limit', y0, u0),
                    ('module default 0.5', y1, u1),
                    ('explicit 0.5', y2, u2)):
    print('%-28s %10.4f %10.4f %10.4f' % (tag, max(ys), ys[-1], max(us)))

same_01 = all(abs(a - b) < 1e-12 for a, b in zip(y1, y2))
print('')
print('module default == explicit override :', same_01)
print('limit changes the response          :',
      any(abs(a - b) > 1e-6 for a, b in zip(y0, y2)))

m._INTEGRAL_MAX = 0.5
print('reset check, _INTEGRAL_MAX =', m._INTEGRAL_MAX)
