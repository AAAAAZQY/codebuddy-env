# -*- coding: cp936 -*-
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

path = sys.argv[1]
z = zipfile.ZipFile(path)
xml = z.read('word/document.xml').decode('utf-8', 'ignore')
xml = xml.replace('</w:p>', '</w:p>\n')

paras = []
for line in xml.split('\n'):
    texts = re.findall(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', line)
    if texts:
        s = ''.join(texts).strip()
        if s:
            paras.append(s)

print('paras =', len(paras))
kw = ['充电', '积分', '电量', '曲线', '检测', '关机充电', 'OSD', '续航']
hit = set()
for i, s in enumerate(paras):
    if any(k in s for k in kw):
        hit.add(i)

print('matched =', len(hit))
last = -9
for i in sorted(hit):
    if i > last + 1:
        print('  ---')
    print('[%03d] %s' % (i, paras[i][:200]))
    last = i
