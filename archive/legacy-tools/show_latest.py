# -*- coding: cp936 -*-
import glob
import os
import sys
from pptx import Presentation

desk = os.path.join(os.path.expanduser('~'), 'Desktop')
files = sorted(glob.glob(os.path.join(desk, '试用期述职报告*.pptx')), key=os.path.getmtime)
path = files[-1]
print('file:', os.path.basename(path), os.path.getsize(path), 'B')
prs = Presentation(path)
print('slides =', len(prs.slides))
for n in [int(x) for x in sys.argv[1:]]:
    s = prs.slides[n - 1]
    print('==== slide %d ====' % n)
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                t = ''.join(r.text for r in p.runs).strip()
                if t:
                    print('  ' + t)
