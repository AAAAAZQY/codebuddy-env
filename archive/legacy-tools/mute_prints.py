# -*- coding: cp936 -*-
"""静音生成脚本的打印输出"""
import io
import re

FILES = [
    r'D:\Codebuddy\tools\gen_pptx3.py',
    r'D:\Codebuddy\tools\pptx2html.py',
]

for p in FILES:
    s = io.open(p, encoding='cp936', newline='').read()
    lines = s.replace('\r\n', '\n').split('\n')
    out = []
    n = 0
    for ln in lines:
        st = ln.strip()
        if st.startswith('print(') and not st.startswith('print("\\n"):
            indent = ln[:len(ln) - len(ln.lstrip())]
            out.append(indent + '# ' + ln.strip())
            n += 1
        else:
            out.append(ln)
    io.open(p, 'w', encoding='cp936', newline='').write('\n'.join(out).replace('\n', '\r\n'))
    print('%s  muted=%d' % (p.split('\\')[-1], n))
