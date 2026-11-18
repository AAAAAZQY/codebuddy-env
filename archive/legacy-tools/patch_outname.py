# -*- coding: cp936 -*-
"""输出文件名换成带日期版本，避开被占用的旧文件"""
import io

P = r'D:\Codebuddy\tools\gen_pptx.py'
s = io.open(P, encoding='cp936', newline='').read()

OLD = """out = os.path.join(desktop, '试用期述职报告_赵庆斌_2026-10.pptx')
try:
    if os.path.exists(out):
        os.remove(out)
    prs.save(out)
except Exception as e:
    print('primary save failed: %s' % e)
    out = os.path.join(desktop, '试用期述职报告_赵庆斌_2026-10_v2.pptx')
    prs.save(out)"""

NEW = """out = os.path.join(desktop, '试用期述职报告_赵庆斌_2026-10-28.pptx')
prs.save(out)"""

if OLD in s:
    s = s.replace(OLD, NEW)
    print('output name updated')
else:
    # 已经是新格式时，再兜底替换一次路径
    s = s.replace("'试用期述职报告_赵庆斌_2026-10.pptx'", "'试用期述职报告_赵庆斌_2026-10-28.pptx'")
    print('fallback replaced')

io.open(P, 'w', encoding='cp936', newline='').write(s)
print('done')
