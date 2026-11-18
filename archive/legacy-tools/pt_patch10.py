# -*- coding: cp936 -*-
"""第 10 步：vofa 转 CSV 时, 带 u 也保留 r（输出 time,u,y,r 四列）

否则有 u 就丢掉 r, 规则整定需要 r 才能算振荡特征。
"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'

src = io.open(TARGET, encoding='latin-1', newline='').read()

old = '''    if pick["u"] is not None:
        head = "time,u,y"
    elif pick["r"] is not None:
        head = "time,r,y"
    else:
        return ""'''

new = '''    if pick["u"] is not None and pick["r"] is not None:
        head = "time,u,y,r"
    elif pick["u"] is not None:
        head = "time,u,y"
    elif pick["r"] is not None:
        head = "time,r,y"
    else:
        return ""'''

if src.count(old) != 1:
    print('anchor1 count =', src.count(old))
    sys.exit(1)
src = src.replace(old, new)

old2 = '''    lines = [head]
    for idx, fr in enumerate(frames):
        t = idx * dt
        if pick["u"] is not None:
            lines.append("%.6f,%.6f,%.6f" % (t, fr[pick["u"]], fr[pick["y"]]))
        else:
            lines.append("%.6f,%.6f,%.6f" % (t, fr[pick["r"]], fr[pick["y"]]))
    return "\\n".join(lines) + "\\n"'''

new2 = '''    lines = [head]
    for idx, fr in enumerate(frames):
        t = idx * dt
        if pick["u"] is not None and pick["r"] is not None:
            lines.append("%.6f,%.6f,%.6f,%.6f"
                         % (t, fr[pick["u"]], fr[pick["y"]], fr[pick["r"]]))
        elif pick["u"] is not None:
            lines.append("%.6f,%.6f,%.6f" % (t, fr[pick["u"]], fr[pick["y"]]))
        else:
            lines.append("%.6f,%.6f,%.6f" % (t, fr[pick["r"]], fr[pick["y"]]))
    return "\\n".join(lines) + "\\n"'''

if src.count(old2) != 1:
    print('anchor2 count =', src.count(old2))
    sys.exit(1)
src = src.replace(old2, new2)

out = src.encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('patched, bytes =', len(out))
