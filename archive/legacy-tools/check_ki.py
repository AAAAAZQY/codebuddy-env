# -*- coding: utf-8 -*-
"""Compare phase margin for ki=0.006 vs 0.06 on the fitted velocity-loop plant."""
import math

TS = 1e-4
K = 6.45       # fitted from measured |P| = 0.45 @ 12.56Hz
TAU = 0.181
TD = 1.5 * TS


def PC(kp, ki, f):
    w = 2 * math.pi * f
    C = complex(kp, -ki / TS / w)
    P = K / (1 + 1j * w * TAU)
    return C * P * complex(math.cos(-w * TD), math.sin(-w * TD))


def margin(kp, ki):
    lo, hi = 0.01, 20000.0
    for _ in range(100):
        mid = (lo * hi) ** 0.5
        if abs(PC(kp, ki, mid)) > 1:
            lo = mid
        else:
            hi = mid
    fc = (lo * hi) ** 0.5
    L = PC(kp, ki, fc)
    return fc, 180 + math.degrees(math.atan2(L.imag, L.real))


print('%-8s %-8s %10s %12s %14s' % ('kp', 'ki', 'fc(Hz)', 'PM(deg)', 'gain@12.56Hz'))
print('-' * 58)
for kp, ki, tag in ((0.85, 0.01, 'original'),
                    (0.425, 0.006, 'tuner advice'),
                    (0.383, 0.006, 'tuner w/ real kp'),
                    (0.383, 0.01, 'ki 10x too big?'),
                    (0.383, 0.06, 'CURRENT FILE')):
    fc, pm = margin(kp, ki)
    g = abs(PC(kp, ki, 12.56))
    flag = ''
    if pm < 15:
        flag = '  <== unstable/marginal'
    elif pm < 30:
        flag = '  <== thin'
    print('%-8.3f %-8.3f %10.1f %12.1f %14.2f  %-14s%s'
          % (kp, ki, fc, pm, g, tag, flag))

print('')
print('integral-path gain at 12.56Hz = ki / (Ts * w) :')
for ki in (0.006, 0.01, 0.02, 0.06):
    print('   ki=%-6.3f -> %.2f' % (ki, ki / TS / (2 * math.pi * 12.56)))
