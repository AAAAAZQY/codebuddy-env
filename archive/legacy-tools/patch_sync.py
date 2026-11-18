# -*- coding: cp936 -*-
"""同步用户在 PPT 里的修改：KB T160、BM S100、新增 22B2 SST"""
import io

P = r'D:\Codebuddy\tools\gen_pptx3.py'
s = io.open(P, encoding='cp936', newline='').read().replace('\r\n', '\n')

# 1) k13 → KB（全局）
s = s.replace('k13 T160', 'KB T160')

# 2) 第 9 页：标配 5 寸 → BM S100
OLD9 = "'标配 5 寸：特殊预置位无法调用、报警信息查不到，补齐协议解析分支',"
NEW9 = "'BM S100：特殊预置位无法调用，修复状态机 bug 后解决',"
if OLD9 in s:
    s = s.replace(OLD9, NEW9)
else:
    print('MISS page9')

# 3) 第 7 页：插入 22B2 SST，字号调整
OLD7 = """content('收获 · 电机与云台', 'MOTOR   &   GIMBAL', 7, [
    'U 款球机：独立完成速度曲线调整，把机械参数（行程、负载）映射到速度曲线，实现不丢步、不撞头、速度适中',
    '申威 T160：丢步是头太重、电机力矩不够，增大常态力矩解决；撞头是行程太大、自检没找到光耦，增大自检行程后解决',
    'PM 球机 / 5d6750：修正自检撞头与角度偏差，完成精度与速度测试',
    '运动类问题先查限位、零点、加减速曲线，再怀疑电机本体',
], size=18, gap=16)"""

NEW7 = """content('收获 · 电机与云台', 'MOTOR   &   GIMBAL', 7, [
    'U 款球机：独立完成速度曲线调整，把机械参数（行程、负载）映射到速度曲线，实现不丢步、不撞头、速度适中',
    '申威 T160：丢步是头太重、电机力矩不够，增大常态力矩解决；撞头是行程太大、自检没找到光耦，增大自检行程后解决',
    '22B2 SST：结构特殊导致找不到光耦，新增绕过限制直接发脉冲的函数，确保能找到光耦',
    'PM 球机 / 5d6750：修正自检撞头与角度偏差，完成精度与速度测试',
    '运动类问题先查限位、零点、加减速曲线，再怀疑电机本体',
], size=17, gap=12)"""

if OLD7 in s:
    s = s.replace(OLD7, NEW7)
else:
    print('MISS page7')

# 4) 第 5 页协议那条同步 KB
s = s.replace("'协议与定制：KB T160 查询协议、标配 5 寸特殊预置位、馥鸿 B130 串口改造',",
              "'协议与定制：KB T160 查询协议、BM S100 特殊预置位、馥鸿 B130 串口改造',")

s = s.replace("'试用期述职报告_赵庆斌_v6.pptx'", "'试用期述职报告_赵庆斌_v7.pptx'")

io.open(P, 'w', encoding='cp936', newline='').write(s.replace('\n', '\r\n'))
print('ok: kb=%d bm=%d 22b2=%d v7=%d'
      % (s.count('KB T160'), s.count('BM S100'), s.count('22B2 SST'), s.count('_v7.pptx')))
