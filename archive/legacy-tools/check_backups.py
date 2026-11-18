# -*- coding: gbk -*-
"""确认这两个 .c 是否被工程引用，以及与 motor_bldc.c 的关系。"""
import glob
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'd:\plain_view\66T\mis-t160-XH-ptz'
TGT = [os.path.join(BASE, 'application', n)
       for n in ('motor_bldc_before.c', 'motor_bldc_gbk_backup.c',
                 'motor_bldc.c')]

for p in TGT:
    raw = open(p, 'rb').read()
    print('%-30s %6d  sha=%s' % (os.path.basename(p), len(raw),
                                 hashlib.sha256(raw).hexdigest()[:10]))
    head = raw[:80]
    print('      头: %r' % head)
    try:
        s = io.open(p, encoding='gbk', errors='replace').read()
        print('      行数 %d  含 MOTOR_IDENT_DITHER=%s  kp(pos)=%s'
              % (len(s.splitlines()), 'MOTOR_IDENT_DITHER' in s,
                 'yes' if '.kp = 6.0f' in s else ('7.0' if '.kp = 7.0f' in s else '?')))
    except Exception as e:                          # noqa: BLE001
        print('      读取失败', e)
    print('')

print('--- 工程文件是否引用这两个名字 ---')
hits = 0
for pat in ('*.uvproj', '*.uvprojx', '*.uvopt', '*.uvoptx', '*.cproject',
            '*.ewp', '*.cbp', 'Makefile', '*.mk'):
    for f in glob.glob(os.path.join(BASE, '**', pat), recursive=True):
        try:
            s = io.open(f, encoding='gbk', errors='replace').read()
        except Exception:                           # noqa: BLE001
            continue
        for key in ('motor_bldc_before', 'motor_bldc_gbk_backup'):
            if key in s:
                print('  !! %s 引用了 %s' % (os.path.basename(f), key))
                hits += 1
if not hits:
    print('  未被任何工程文件引用')
