# -*- coding: cp936 -*-
import sys
from collections import Counter

from pptx import Presentation
from pptx.util import Emu

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

COLORS = Counter()
FONTS = Counter()
SIZES = Counter()


def rgb_of(shape):
    try:
        if shape.fill.type is not None and shape.fill.type == 1:
            c = shape.fill.fore_color
            if c.type is not None and c.rgb is not None:
                return str(c.rgb)
    except Exception:
        pass
    return None


def walk(shapes, out):
    for sh in shapes:
        out.append(sh)
        if sh.shape_type == 6:
            walk(sh.shapes, out)


def analyze(path, name):
    prs = Presentation(path)
    print('=' * 70)
    print('%s    slides=%d   size=%.2f x %.2f in'
          % (name, len(prs.slides), prs.slide_width / 914400, prs.slide_height / 914400))
    for i, slide in enumerate(prs.slides, 1):
        shapes = []
        walk(slide.shapes, shapes)
        texts = []
        for sh in shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = ''.join(r.text for r in p.runs).strip()
                    if t:
                        texts.append(t)
                        for r in p.runs:
                            if r.font.name:
                                FONTS[r.font.name] += 1
                            if r.font.size:
                                SIZES[int(r.font.size.pt)] += 1
            c = rgb_of(sh)
            if c:
                COLORS[c] += 1
        head = ' / '.join(texts[:3])[:70]
        print('[%02d] shapes=%-3d  %s' % (i, len(shapes), head))
    print('-- top colors:', COLORS.most_common(8))
    print('-- top fonts :', FONTS.most_common(5))
    print('-- top sizes :', SIZES.most_common(8))


for p in sys.argv[1:]:
    try:
        analyze(p, p.split('\\')[-1])
    except Exception as e:
        print('FAIL', p, e)
