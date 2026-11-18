# -*- coding: cp936 -*-
"""检查目录下所有文件是否明文（未被 DLP 加密）"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

root = sys.argv[1]
bad = 0
total = 0
for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d != '__pycache__']
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, root)
        size = os.path.getsize(p)
        with open(p, 'rb') as f:
            head = f.read(16)
        enc = head.startswith(b'%TSD-Header')
        align = (size % 8192 == 0)
        total += 1
        if enc:
            bad += 1
        print('%-22s %9d  %s' % (rel, size, 'ENCRYPTED' if enc else 'plain'))
print('total=%d  encrypted=%d' % (total, bad))
