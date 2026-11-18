# -*- coding: cp936 -*-
"""第 13 步：把"闭环辨识未通过"改成准确表述（数据无阶跃，不是出错）"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'


def L(s):
    return s.encode('utf-8').decode('latin-1')


src = io.open(TARGET, encoding='latin-1', newline='').read()

old = L('''                head = "闭环辨识未通过, 已退回经验规则整定"
                sub = ("具体原因见下方 [!] 提示(会指出数据本身的问题, "
                       "例如单拍跳变/数据太短/残差超标), 下方按经验规则给出调整建议")''')

new = L('''                head = "无法闭环辨识 —— 已按振荡特征给出规则整定"
                sub = ("闭环辨识要靠「已知控制器反推对象」, 前提是目标值有阶跃激励; "
                       "本段 r 是斜坡加速/恒定, 反推不出对象参数。"
                       "振荡特征(波动幅度/衰减比)仍然可靠, 下方建议参数可直接用。")''')

if src.count(old) != 1:
    print('anchor count =', src.count(old))
    sys.exit(1)

src = src.replace(old, new)
out = src.encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('patched, bytes =', len(out))
