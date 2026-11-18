# -*- coding: utf-8 -*-
"""Sweep kp/ki, report crossover, phase margin and 12.56Hz disturbance amplification."""
import math

Ts = 1e-4
K = 6.45        # fitted from measured |P| = 0.45 @ 12.56Hz
TAU = 0.181     # fitted from measured phase -86 deg @ 12.56Hz
TD = 1.5 * Ts   # PWM + sampling delay


def PC(kp, ki, f):
    w = 2 * math.pi * f
    C = complex(kp, -ki / Ts / w)
    P = K / (1 + 1j * w * TAU)
    dly = complex(math.cos(-w * TD), math.sin(-w * TD))
    return C * P * dly


def margin(kp, ki):
    lo, hi = 0.1, 8000.0
    for _ in range(90):
        mid = (lo * hi) ** 0.5
        if abs(PC(kp, ki, mid)) > 1:
            lo = mid
        else:
            hi = mid
    fc = (lo * hi) ** 0.5
    L = PC(kp, ki, fc)
    pm = 180 + math.degrees(math.atan2(L.imag, L.real))
    return fc, pm


print('%-6s %-6s %9s %10s %12s %10s' % ('kp', 'ki', 'fc(Hz)', 'PM(deg)', 'amp@12.56', 'PM@6Hz'))
print('-' * 60)
for kp in (0.7, 1.0, 1.5, 2.0, 2.5, 3.0):
    for ki in (0.01,):
        fc, pm = margin(kp, ki)
        amp = abs(1.0 / (1.0 + PC(kp, ki, 12.56)))
        print('%-6.2f %-6.3f %9.1f %10.1f %12.2f' % (kp, ki, fc, pm, amp))
print('')
print('amplification < 1 means the closed loop actually suppresses that frequency')
