# -*- coding: cp936 -*-
"""按幻灯片列出引用的图片，并导出这些图片"""
import io
import os
import re
import sys
import zipfile
from PIL import Image

path = sys.argv[1]
out = r'D:\Codebuddy\tmp\media'
os.makedirs(out, exist_ok=True)
z = zipfile.ZipFile(path)

names = set(z.namelist())


def size_of(data):
    try:
        im = Image.open(io.BytesIO(data))
        return im.size
    except Exception:
        return (0, 0)


# slideN.xml.rels -> 图片
for n in sorted(names):
    m = re.match(r'ppt/slides/_rels/slide(\d+)\.xml\.rels$', n)
    if not m:
        continue
    idx = int(m.group(1))
    if idx < 9 or idx > 20:
        continue
    rels = z.read(n).decode('utf-8', 'ignore')
    imgs = re.findall(r'Target="\.\./media/([^"]+)"', rels)
    if not imgs:
        continue
    print('==== slide %02d ====' % idx)
    for img in dict.fromkeys(imgs):
        p = 'ppt/media/' + img
        if p not in names:
            continue
        data = z.read(p)
        w, h = size_of(data)
        print('   %-16s %8d B  %5dx%-5d' % (img, len(data), w, h))
        with open(os.path.join(out, img), 'wb') as f:
            f.write(data)

print('exported ->', out)
