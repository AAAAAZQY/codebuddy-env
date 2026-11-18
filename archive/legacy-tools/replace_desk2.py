# -*- coding: cp936 -*-
"""重试替换桌面 pptx（旧文件可能被 DLP/预览进程短暂锁定）"""
import os
import time

desk = os.path.join(os.path.expanduser('~'), 'Desktop')
old = os.path.join(desk, '试用期述职报告_赵庆斌_2026-10.pptx')
new = os.path.join(desk, '试用期述职报告_赵庆斌_2026-10_v2.pptx')

if not os.path.exists(new):
    print('no v2')
else:
    ok = False
    for i in range(10):
        try:
            if os.path.exists(old):
                os.remove(old)
            os.rename(new, old)
            ok = True
            break
        except Exception as e:
            print('try %d: %s' % (i + 1, e))
            time.sleep(1.2)
    print('REPLACED' if ok else 'FAILED, keep v2')

for f in os.listdir(desk):
    if f.startswith('试用期述职报告'):
        print('  %s  %d B' % (f, os.path.getsize(os.path.join(desk, f))))
