# -*- coding: cp936 -*-
"""改文案：三类工作去掉自夸说法、定制化突出 U 款球机、电量写具体实现"""
import io

P = r'D:\Codebuddy\tools\gen_pptx.py'
s = io.open(P, encoding='cp936', newline='').read()

PAIRS = [
    ("'三类工作：问题修复、定制化项目（如双串口改单串口）、自主研究（电量管理与低电保护由我独立完成）',",
     "'三类工作：问题修复、定制化项目（如 U 款球机对接零位机芯）、新功能开发（电量管理、模块移植）',"),
    ("'运动链路理解：20H U 款完成电机调参与零位机芯对接，理清限位、零点与加减速的关系',",
     "'定制对接能力：U 款球机对接第三方零位机芯（VBM-5100），完成电机调参与协议适配',"),
    ("'电量逻辑：电量计算与低电保护由我独立实现；5100 森曼 修复电量来回跳（采样 → 换算 → 刷新）与 OLED 花屏缺键',",
     "'电量管理：按充电曲线积分计算电量，含充电检测与 OSD 层电量显示；5100 森曼 修复电量来回跳与 OLED 花屏缺键',"),
]

hit = 0
for old, new in PAIRS:
    if old in s:
        s = s.replace(old, new)
        hit += 1
    else:
        print('MISS:', old[:34])

io.open(P, 'w', encoding='cp936', newline='').write(s)
print('replaced=%d  U款=%d  充电曲线=%d' % (hit, s.count('U 款球机'), s.count('充电曲线')))
