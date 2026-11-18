# -*- coding: cp936 -*-
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE = r'\\192.168.0.6\ptz'
L1 = os.path.join(BASE, 'AF&PTZ共享目录')
L2 = os.path.join(L1, '2-课题分享')

print('L1 exists:', os.path.isdir(L1))
if os.path.isdir(L1):
    for n in sorted(os.listdir(L1)):
        print('  [D]', n)

print('L2 exists:', os.path.isdir(L2))
if os.path.isdir(L2):
    for n in sorted(os.listdir(L2)):
        p = os.path.join(L2, n)
        if os.path.isdir(p):
            print('  [D]', n)
            for m in sorted(os.listdir(p)):
                mp = os.path.join(p, m)
                try:
                    print('      -', m, os.path.getsize(mp))
                except Exception as e:
                    print('      !', m, e)
        else:
            print('  [F]', n, os.path.getsize(p))
