# -*- coding: cp936 -*-
"""按行在第 9 页插入馥鸿条目；输出改为 v4"""
import io

P = r'D:\Codebuddy\tools\gen_pptx3.py'
s = io.open(P, encoding='cp936', newline='').read()
lines = s.replace('\r\n', '\n').split('\n')
out = []
done = False
for ln in lines:
    if ('标配 5 寸：特殊预置位无法调用' in ln) and not done:
        out.append(ln)
        out.append("    '馥鸿 B130：双串口改单串口；抓机芯数据时发现对方下发数据异常，定位后推动修正',")
        done = True
        continue
    if '协议类问题两步：先对齐帧' in ln and ln.strip().startswith("'") and done:
        indent = ln[:len(ln) - len(ln.lstrip())]
        out.append(indent + "('协议类问题两步：先对齐帧，再补解析分支；阈值必须现场实测', 1),")
        continue
    if ln.strip() == "], size=18, gap=16)" and done:
        out.append("], size=16, gap=12)")
        continue
    out.append(ln)

s2 = '\n'.join(out).replace('\n', '\r\n')
s2 = s2.replace("'试用期述职报告_赵庆斌_v3.pptx'", "'试用期述职报告_赵庆斌_v4.pptx'")
io.open(P, 'w', encoding='cp936', newline='').write(s2)
print('done: fuhong=%d v4=%d page9size=%d'
      % (s2.count('馥鸿 B130'), s2.count('_v4.pptx'), s2.count('], size=16, gap=12)')))
