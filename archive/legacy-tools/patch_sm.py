# -*- coding: cp936 -*-
"""按用户原文修正：申威 T160、U 款描述、S100 的 ircut、电量页标注机型"""
import io

P = r'D:\Codebuddy\tools\gen_pptx3.py'
s = io.open(P, encoding='cp936', newline='').read()

# 1) 全局品牌名
s = s.replace('申盛', '申威')

PAIRS = [
    # 第 7 页 U 款
    ("'U 款球机：独立完成速度曲线调整，把机械参数（行程、负载）映射到速度曲线，配合第三方零位机芯（VBM-5100）完成上电找零',",
     "'U 款球机：独立完成速度曲线调整，把机械参数（行程、负载）映射到速度曲线，实现不丢步、不撞头、速度适中',"),
    # 第 7 页 T160（换成用户给的真实根因）
    ("'申威 T160：丢步与撞头源于限位与零点偏差，使行程被提前截断，调参数与加减速后恢复',",
     "'申威 T160：丢步是头太重、电机力矩不够，增大常态力矩解决；撞头是行程太大、自检没找到光耦，增大自检行程后解决',"),
    # 第 8 页 S100
    ("'森曼 S100：OLED 开机花屏与缺 CU 键，定位到初始化与按键扫描时序冲突',",
     "'森曼 S100：修复 OLED 开机花屏（初始化与按键扫描时序）与 ircut 潜在问题',"),
    # 电量两页标注机型
    ("content('专项 · 电量管理', 'POWER   MANAGEMENT', 10,",
     "content('专项 · 电量管理 ｜ SM S100', 'POWER   MANAGEMENT', 10,"),
    ("content('专项 · 关机充电记账', 'CHARGING   WHILE   POWERED   OFF', 11,",
     "content('专项 · 关机充电记账 ｜ SM S100', 'CHARGING   WHILE   POWERED   OFF', 11,"),
    # 输出改名
    ("'试用期述职报告_赵庆斌_v5.pptx'", "'试用期述职报告_赵庆斌_v6.pptx'"),
]

hit = 0
for old, new in PAIRS:
    if old in s:
        s = s.replace(old, new)
        hit += 1
    else:
        print('MISS:', old[:32])

io.open(P, 'w', encoding='cp936', newline='').write(s)
print('hit=%d  shenwei=%d  ircut=%d  v6=%d'
      % (hit, s.count('申威'), s.count('ircut'), s.count('_v6.pptx')))
