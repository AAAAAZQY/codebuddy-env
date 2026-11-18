# -*- coding: cp936 -*-
import os
import sys
from pptx import Presentation

path = os.path.join(os.path.expanduser('~'), 'Desktop', '试用期述职报告_赵庆斌_2026-10.pptx')
prs = Presentation(path)
for n in [int(x) for x in sys.argv[1:]]:
    s = prs.slides[n - 1]
    print('==== slide %d ====' % n)
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                t = ''.join(r.text for r in p.runs).strip()
                if t:
                    print('  ' + t)
