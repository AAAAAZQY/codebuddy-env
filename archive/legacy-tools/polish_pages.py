# -*- coding: gbk -*-
"""S8~S12：小结改成 17pt 正式条目 + 补「能力沉淀」+ 润色措辞。"""
import copy
import sys

from pptx import Presentation
from pptx.text.text import _Paragraph
from pptx.util import Pt
from pptx.dml.color import RGBColor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v10.pptx'
prs = Presentation(P)

BODY = RGBColor(0x24, 0x33, 0x3B)
DASH = RGBColor(0xE9, 0x61, 0x71)


def body_of(idx):
    for sh in prs.slides[idx].shapes:
        if sh.has_text_frame and sh.text_frame.text.strip().startswith('—'):
            return sh
    raise AssertionError('S%d 找不到正文' % (idx + 1))


def set_bullet(para, text):
    """把段落整理成标准条目：破折号 15pt + 正文 17pt 深色。"""
    runs = para.runs
    assert len(runs) >= 2, 'run 不足'
    runs[0].text = '—  '
    runs[0].font.size = Pt(15.0)
    runs[0].font.color.rgb = DASH
    runs[1].text = text
    runs[1].font.size = Pt(17.0)
    runs[1].font.bold = False
    runs[1].font.color.rgb = BODY
    for r in runs[2:]:
        r.text = ''


def append_bullet(tf, text):
    tpl = None
    for p in tf.paragraphs:
        if p.runs and p.runs[0].text.strip().startswith('—') and len(p.runs) >= 2:
            tpl = copy.deepcopy(p._p)
    assert tpl is not None
    tf._txBody.append(tpl)
    para = _Paragraph(tpl, tf)
    set_bullet(para, text)


PLAN = {
    7: [   # S8 OLED
        '海洋王 6126b、球芯全系：开机花屏、个别开机 Y 轴反转，根因是初始化顺序与上电时序',
        'SM S100：OLED 显示定制，按客户需求调整显示项与界面排布',
        '能力沉淀：掌握 I?C 通信时序与 OLED 显示原理，能独立完成显示定制与花屏类问题定位',
    ],
    8: [   # S9 日夜与灯光
        'LMD B110 / 国信 B130：实现软/硬光敏切换与日夜状态判定',
        '国信 B130：白光灯自动切换，按环境照度联动日夜模式',
        'ir-cut 状态误判是普遍问题：状态上报错误会让机芯切错滤光片，表现为网页端画面异常',
        '能力沉淀：理解光敏采样与日夜切换的状态机逻辑；阈值必须现场实测，能定位误切与画面异常',
    ],
    9: [   # S10 外设与模块
        'XH T160：红外补光灯、激光测距两个模块对接移植',
        'KB T160：新增外设查询协议',
        '馥鸿 B130：双串口改单串口；抓机芯数据时发现对方下发异常，定位后推动修正',
        '能力沉淀：熟悉串口协议解析与模块移植流程；协议问题先对齐帧、再补解析分支',
    ],
    10: [  # S11 电量管理
        '硬件条件：整板无充电管理芯片、无 CHRG/STDBY 引脚，只有一路电池电压进 ADC，充电状态只能由软件判定',
        '放电：厂家曲线按 5 格间隔取点建表，先查单调性再插值，越界取端点',
        '充电判定三段式：进入看端压净涨、维持看去抖、退出看回落；不能只看绝对电压，满电静置也在恒压点之上',
        '充电积分：CC 段按 I/(C×60) 折算（3A/4.5Ah ≈ 1.1 格/分），CV 段按 K×(100?SOC)（τ ≈ 23 分），再乘 1.1~1.2 补偿',
        '上界钳位到电压法读数，防止积分跑飞',
        '能力沉淀：无硬件电流检测时，用端压趋势 + 分段积分做出可用的电量估算',
    ],
    11: [  # S12 关机充电记账
        '问题：关机后软件不运行，这段时间的电量变化没有任何记录，可能被补电、自放电，也可能拆下充满再装回',
        '做法：EEPROM 存「关机时的电压法值」当基线，开机与当前电压法值比较；存电压法值而非积分值，误差相减抵消',
        '关键坑：充电中关机不能写电压基线，端压虚高会抬高基线，下次开机误判「没充过电」，充进去的电全丢',
        '兜底：魔数不符或越界直接用电压值；开机端压 ≥12.55V 按满电；充电中掉电重启，存值作下界、电压值作上界',
        '效果：关机充电引起的重启跳变从 ±20 格压到 ±5 格以内',
        '能力沉淀：用 EEPROM 存基线、按误差相减，解决掉电期间状态不可观测的问题',
    ],
}

for idx, lines in PLAN.items():
    body = body_of(idx)
    tf = body.text_frame
    paras = list(tf.paragraphs)
    # 先把前 N 段改写（N = 现有段数，至少为 1）
    for i, p in enumerate(paras):
        if i < len(lines):
            set_bullet(p, lines[i])
        else:
            p._p.getparent().remove(p._p)
    # 超出现有段数的，追加
    for extra in lines[len(paras):]:
        append_bullet(tf, extra)
    print('S%-2d 现有 %d 条: %s' % (idx + 1, len(tf.paragraphs), lines[-1][:44]))

DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v10.pptx', '_v11.pptx')
    prs.save(DST)
    print('v10 被占用，改存 v11')
print('已保存:', DST)
