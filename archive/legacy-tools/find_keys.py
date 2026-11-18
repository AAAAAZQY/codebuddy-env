# -*- coding: utf-8 -*-
"""Locate where the suggested PID lives in the analysis dict and how the report prints it."""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'D:\bProject\pid_tuner\pid_tuner.py'
L = io.open(SRC, encoding='utf-8', errors='replace').read().splitlines()

pat = re.compile(r'(best_pid|best|cur_pid|current|pid_best|pid_cur|fba|fbc)')
print('--- lines mentioning fba / fbc / best_pid ---')
n = 0
for i, l in enumerate(L, 1):
    if ('fba' in l or 'fbc' in l or 'best_pid' in l) and ('=' in l or 'get' in l):
        print('%5d| %s' % (i, l.strip()[:110]))
        n += 1
        if n > 30:
            break

print('')
print('--- return dict of build_analysis (search "return {") ---')
for i, l in enumerate(L, 1):
    if 'return {' in l and 4000 < i < 4300:
        for k in range(i - 1, min(i + 22, len(L))):
            print('%5d| %s' % (k + 1, L[k].rstrip()[:110]))
        break
