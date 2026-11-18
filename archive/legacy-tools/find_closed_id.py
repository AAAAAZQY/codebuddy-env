# -*- coding: utf-8 -*-
"""Where does the tool decide closed_identify vs step-identification?"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

L = io.open(r'D:\bProject\pid_tuner\pid_tuner.py',
            encoding='utf-8', errors='replace').read().splitlines()

print('--- lines mentioning closed_identify / osc_id / closed_id ---')
n = 0
for i, l in enumerate(L, 1):
    if re.search(r'closed_identify|\bosc_id\b|\bclosed_id\b', l):
        print('%5d| %s' % (i, l.strip()[:120]))
        n += 1
        if n > 40:
            break

print('')
print('--- identify(): how it treats non-step data / retry ---')
for i, l in enumerate(L, 1):
    if re.match(r'^\s*def identify\(', l):
        for k in range(i - 1, min(i + 60, len(L))):
            print('%5d| %s' % (k + 1, L[k].rstrip()[:120]))
        break
