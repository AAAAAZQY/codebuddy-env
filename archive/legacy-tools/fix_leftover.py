# -*- coding: gbk -*-
"""删掉区间替换后残留的旧代码 6030..6059。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'D:\bProject\pid_tuner\pid_tuner.py'
txt = io.open(P, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in txt else '\n'
lines = txt.split(nl)

a, b = 6029, 6059        # 0-based, 删除 [a, b)
print('将删除 行 %d..%d' % (a + 1, b))
print('  首行:', repr(lines[a][:60]))
print('  末行:', repr(lines[b - 1][:60]))
assert lines[a].strip() == 'return', 'first line mismatch'
assert 'root.after(150, _poll)' in lines[b - 1], 'last line mismatch'

del lines[a:b]
io.open(P, 'w', encoding='utf-8', newline='').write(nl.join(lines))
print('已删除 %d 行, 新总行数 %d' % (b - a, len(lines)))
