# -*- coding: cp936 -*-
"""第 3 步：采样不足的警告里补一条"怎么拿到可信结论"的指引"""
import io
import shutil
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'
BAK = r'D:\Codebuddy\backup\pid_tuner-20261028\pid_tuner.step2.py'


def L(s):
    return s.encode('utf-8').decode('latin-1')


src = io.open(TARGET, encoding='latin-1', newline='').read()
shutil.copyfile(TARGET, BAK)
before = len(src.encode('latin-1'))

anchor = L('        add("  !! 建议: 把采集间隔降到 10~20ms, 或提供 --current-pid 走规则整定")')
if src.count(anchor) != 1:
    print('anchor count =', src.count(anchor))
    sys.exit(1)

extra = L('\n        add("  !! 现在就要可信结论: 去掉 u 重跑(加 --vofa-map \\"y=0,r=1\\"), "\n'
          '            "工具会按振荡特征走规则整定, 比上表可靠")')
src = src.replace(anchor, anchor + extra)

out = src.encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('bytes: %d -> %d (+%d)' % (before, len(out), len(out) - before))
