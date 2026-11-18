# -*- coding: cp936 -*-
"""强调三类工作（修问题 / 定制 / 自主研究），电量逻辑标注为独立实现"""
import io
import sys

PAIRS = [
    ("'工作方式：接需求 → 复现问题 → 定位根因 → 最小改动修复 → 自测交付',",
     "'三类工作：问题修复、定制化项目（如双串口改单串口）、自主研究（电量管理与低电保护由我独立完成）',"),
    ("'除问题修复外，完成激光测距与红外补光灯两个模块的移植接入',",
     "'统一流程：接需求 → 理清方案 → 定位或实现 → 自测交付；另有激光测距、补光灯两个模块移植',"),
    ("'电量链路：5100 森曼 电量来回跳（采样 → 换算 → 刷新）、OLED 开机花屏与缺键',",
     "'电量逻辑：电量计算与低电保护由我独立实现；5100 森曼 修复电量来回跳（采样 → 换算 → 刷新）与 OLED 花屏缺键',"),
]

for p in sys.argv[1:]:
    s = io.open(p, encoding='cp936', newline='').read()
    hit = 0
    for old, new in PAIRS:
        if old in s:
            s = s.replace(old, new)
            hit += 1
        else:
            print('MISS %s : %s' % (p, old[:26]))
    io.open(p, 'w', encoding='cp936', newline='').write(s)
    print('%s  replaced=%d  zizhu=%d' % (p, hit, s.count('独立实现')))
