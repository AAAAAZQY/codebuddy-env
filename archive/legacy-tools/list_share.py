# -*- coding: cp936 -*-
import io
import os

BASE = r'\\192.168.0.6\ptz'
L1 = os.path.join(BASE, 'AF&PTZ共享目录')
L2 = os.path.join(L1, '2-课题分享')

lines = []
lines.append('L1 exists: %s  (%s)' % (os.path.isdir(L1), L1))
if os.path.isdir(L1):
    for n in os.listdir(L1):
        lines.append('  [D] ' + n)

lines.append('L2 exists: %s  (%s)' % (os.path.isdir(L2), L2))
if os.path.isdir(L2):
    for n in os.listdir(L2):
        p = os.path.join(L2, n)
        if os.path.isdir(p):
            lines.append('  [D] ' + n)
            try:
                for m in os.listdir(p):
                    mp = os.path.join(p, m)
                    lines.append('      - %s   %d' % (m, os.path.getsize(mp)))
            except Exception as e:
                lines.append('      ! ' + str(e))
        else:
            lines.append('  [F] %s   %d' % (n, os.path.getsize(p)))

with io.open(r'D:\Codebuddy\tmp\share_tree.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('OK, lines=%d' % len(lines))
