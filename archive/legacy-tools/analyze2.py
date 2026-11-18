# -*- coding: cp936 -*-
import sys
from collections import Counter

from pptx import Presentation

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def rgb_of(shape):
    try:
        if shape.fill.type == 1:
            c = shape.fill.fore_color
            if c.rgb is not None:
                return str(c.rgb)
    except Exception:
        pass
    return None


def walk(shapes, out):
    for sh in shapes:
        out.append(sh)
        if sh.shape_type == 6:
            walk(sh.shapes, out)


for p in sys.argv[1:]:
    colors = Counter()
    fonts = Counter()
    sizes = Counter()
    prs = Presentation(p)
    print('=' * 66)
    print('%s  slides=%d' % (p.split('\\')[-1], len(prs.slides)))
    for i, slide in enumerate(prs.slides, 1):
        shapes = []
        walk(slide.shapes, shapes)
        first = ''
        for sh in shapes:
            if sh.has_text_frame:
                for para in sh.text_frame.paragraphs:
                    t = ''.join(r.text for r in para.runs).strip()
                    if t and not first:
                        first = t
                    for r in para.runs:
                        if r.font.name:
                            fonts[r.font.name] += 1
                        if r.font.size:
                            sizes[int(r.font.size.pt)] += 1
            c = rgb_of(sh)
            if c:
                colors[c] += 1
        print('[%02d] n=%-3d %s' % (i, len(shapes), first[:46]))
    print('colors:', colors.most_common(6))
    print('fonts :', fonts.most_common(4))
    print('sizes :', sizes.most_common(6))
