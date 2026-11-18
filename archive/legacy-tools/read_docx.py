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

# 段落 / 表格单元格按出现顺序切
xml = xml.replace('</w:p>', '</w:p>\n')
xml = xml.replace('</w:tc>', ' | ')
xml = xml.replace('</w:tr>', '\n')

out = []
for line in xml.split('\n'):
    texts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', line)
    if texts:
        s = ''.join(texts).strip()
        if s:
            out.append(s)

print('paragraphs =', len(out))
print('-' * 60)
for s in out:
    print(s)
