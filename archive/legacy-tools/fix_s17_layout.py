# -*- coding: gbk -*-
"""修 S17：建议卡片收紧高度，概述灰底加高包住第三行。"""
import sys

from pptx import Presentation
from pptx.util import Cm

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆赟_v13.pptx'
prs = Presentation(P)

s17 = prs.slides[16]
for sh in s17.shapes:
    x = sh.left / 360000.0
    y = sh.top / 360000.0
    w = sh.width / 360000.0
    h = sh.height / 360000.0
    # 概述灰底 + 左侧竖条：6.2cm 起，加高到 3.3
    if abs(y - 6.2) < 0.2 and w > 20:
        sh.height = Cm(3.3)
        print('概述灰底高度 %.1f -> 3.3' % h)
    elif abs(y - 6.2) < 0.2 and w < 1.0:
        sh.height = Cm(3.3)
        print('左侧竖条高度 %.1f -> 3.3' % h)
    # 建议卡片底框：10.0 起 4.4 高 -> 2.6
    elif abs(y - 10.0) < 0.2 and w > 20:
        sh.height = Cm(2.6)
        print('建议卡片高度 %.1f -> 2.6' % h)
    # 建议正文框：11.5 起 2.5 高 -> 0.9
    elif abs(y - 11.5) < 0.2:
        sh.height = Cm(1.0)
        print('建议正文高度 %.1f -> 1.0' % h)

prs.save(P)
print('已保存:', P)
