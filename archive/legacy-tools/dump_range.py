# -*- coding: cp936 -*-
import sys
from pptx import Presentation

path = sys.argv[1]
a = int(sys.argv[2])
b = int(sys.argv[3])
prs = Presentation(path)
for i, s in enumerate(prs.slides, 1):
    if i < a or i > b:
        continue
    print('==== [%02d] ====' % i)
    for sh in s.shapes:
        if sh.has_text_frame:
            for ln in sh.text_frame.text.split('\n'):
                ln = ln.strip()
                if ln:
                    print('  ' + ln)
