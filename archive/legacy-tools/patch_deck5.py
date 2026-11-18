# -*- coding: cp936 -*-
"""让 pptx 保存更健壮：先删旧文件，失败则落 v2 文件名"""
import io

P = r'D:\Codebuddy\tools\gen_pptx.py'
OLD = ("out = os.path.join(desktop, '试用期述职报告_赵庆斌_2026-10.pptx')\r\n"
       "prs.save(out)")
NEW = ("out = os.path.join(desktop, '试用期述职报告_赵庆斌_2026-10.pptx')\r\n"
       "try:\r\n"
       "    if os.path.exists(out):\r\n"
       "        os.remove(out)\r\n"
       "    prs.save(out)\r\n"
       "except Exception as e:\r\n"
       "    print('primary save failed: %s' % e)\r\n"
       "    out = os.path.join(desktop, '试用期述职报告_赵庆斌_2026-10_v2.pptx')\r\n"
       "    prs.save(out)")

s = io.open(P, encoding='cp936', newline='').read()
if OLD in s:
    s = s.replace(OLD, NEW)
    io.open(P, 'w', encoding='cp936', newline='').write(s)
    print('patched save logic')
else:
    print('anchor not found')
