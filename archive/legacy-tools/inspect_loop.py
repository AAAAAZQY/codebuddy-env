# -*- coding: utf-8 -*-
"""Show exact text around the cogging macro and the velocity loop."""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
s = io.open(P, encoding='gbk', errors='replace').read()

i = s.find('#define MOTOR_COGGING_COMP')
print('--- macro context ---')
print(repr(s[i - 80:i + 40]))

j = s.find('void bldc_velocity_loop')
print('')
print('--- velocity loop ---')
print(s[j:j + 760])

print('')
print('has arm_math include:', 'arm_math.h' in s)
