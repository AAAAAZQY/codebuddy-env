# -*- coding: cp936 -*-
import io
import os
import sys
import zipfile

try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False

path = sys.argv[1]
out = r'D:\Codebuddy\tmp\media'
os.makedirs(out, exist_ok=True)

z = zipfile.ZipFile(path)
rows = []
for n in z.namelist():
    if not n.startswith('ppt/media/'):
        continue
    data = z.read(n)
    w = h = 0
    if HAS_PIL:
        try:
            im = Image.open(io.BytesIO(data))
            w, h = im.size
        except Exception:
            pass
    rows.append((n, len(data), w, h))

rows.sort(key=lambda r: -r[1])
print('media files =', len(rows))
for n, size, w, h in rows:
    print('%-28s %8d B  %5dx%-5d' % (os.path.basename(n), size, w, h))

# 导出所有图片到本地，方便挑
for n, size, w, h in rows:
    dst = os.path.join(out, os.path.basename(n))
    with open(dst, 'wb') as f:
        f.write(z.read(n))
print('exported to', out)
