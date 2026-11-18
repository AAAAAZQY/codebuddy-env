# -*- coding: cp936 -*-
"""把 motor_bldc.c 从 GBK 转成 UTF-8 (带 BOM)，并备份原文件"""
import io
import shutil
import sys
import time

P = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
BAK = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc_gbk_backup.c'

raw = open(P, 'rb').read()
print('before: %d bytes' % len(raw))

# 备份
shutil.copyfile(P, BAK)

# 已经是 UTF-8 就不转
try:
    raw.decode('utf-8')
    print('already utf-8, nothing to do')
    sys.exit(0)
except UnicodeDecodeError:
    pass

s = raw.decode('gbk')
out = s.encode('utf-8-sig')          # 带 BOM，Keil/VSCode 都能识别
open(P, 'wb').write(out)
print('after : %d bytes (UTF-8 with BOM)' % len(out))
print('backup: %s' % BAK)

# 验证
chk = open(P, 'rb').read()
print('re-decode OK:', bool(chk.decode('utf-8')))
print('has BOM     :', chk[:3] == b'\xef\xbb\xbf')
