# -*- coding: utf-8 -*-
"""Check the scale: what integral_max value actually bites in the tuner's units."""
import importlib.util
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

spec = importlib.util.spec_from_file_location(
    'pid_tuner', r'D:\bProject\pid_tuner\pid_tuner.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# typical identified plant from the user's data
K, T, tau = 2.5, 0.8, 0.15
kw = dict(K=K, T=T, tau=tau, Kp=0.85, Ki=0.01, Kd=0.05,
          dt_sim=0.001, sp=1.0, T_end=8.0, dt_ctrl=0.0001)

t0, y0, u0, _ = m.simulate(integral_max=None, **kw)
print('steady u (no limit) = %.4f   peak u = %.4f' % (u0[-1], max(u0)))
print('')
print('%-12s %10s %10s   %s' % ('integral_max', 'final y', 'max u', 'differs from unlimited?'))
print('-' * 64)
for imax in (2000.0, 200.0, 20.0, 2.0, 0.5, 0.4, 0.3, 0.2):
    ts, ys, us, _ = m.simulate(integral_max=imax, **kw)
    diff = max(abs(a - b) for a, b in zip(ys, y0))
    print('%-12g %10.4f %10.4f   %s (%.2e)'
          % (imax, ys[-1], max(us), 'NO' if diff < 1e-9 else 'YES', diff))
print('')
print('firmware equivalent: ki * integral_max = 0.01 * 200000 = 2000 [Uq units]')
print('but tuner u is normalised: steady u = 1/K = %.3f' % (1.0 / K))
print('=> ratio firmware/tuner = %.0f' % (2272.0 / (1.0 / K)))
print('=> correct tuner entry  = 2000 / %.0f = %.3f' % (2272.0 / (1.0 / K), 2000.0 / (2272.0 / (1.0 / K))))
