# -*- coding: cp936 -*-
"""修掉 GBK 无法表示的 U+2212 减号"""
import io

P = r'D:\Codebuddy\tools\gen_pptx3.py'
s = io.open(P, encoding='cp936', newline='').read()
bad = 'K\u00d7(100\u2212SOC)'
good = 'K\u00d7(100-SOC)'
if bad in s:
    s = s.replace(bad, good)
    print('minus fixed')
else:
    print('pattern not found, try generic')
    s = s.replace('\u2212', '-')
    print('replaced all U+2212')

io.open(P, 'w', encoding='cp936', newline='').write(s)
print('done, bad left =', s.count('\u2212'))
