# -*- coding: cp936 -*-
import os
from pptx import Presentation

path = os.path.join(os.path.expanduser('~'), 'Desktop', '试用期述职报告_赵庆斌_2026-10.pptx')
prs = Presentation(path)
print('slides =', len(prs.slides))
print('size =', prs.slide_width, 'x', prs.slide_height)
for i, s in enumerate(prs.slides, 1):
    texts = []
    for sh in s.shapes:
        if sh.has_text_frame:
            t = sh.text_frame.text.strip().replace('\n', ' / ')
            if t:
                texts.append(t)
    joined = ' | '.join(texts)
    print('[%02d] %s' % (i, joined[:110]))
