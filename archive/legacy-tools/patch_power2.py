# -*- coding: cp936 -*-
"""按 S100 电量方案文档重写电量页（拆 2 页），并修正品牌名"""
import io

P = r'D:\Codebuddy\tools\gen_pptx3.py'
s = io.open(P, encoding='cp936', newline='').read().replace('\r\n', '\n')

# ---------- 1) 品牌名与第 5 页表述 ----------
PAIRS = [
    ("'5100 森美：OLED", "'森曼 S100：OLED"),
    ('国传信 B130', '国信 B130'),
    ("'电源与电量：充电曲线积分计算电量、充电检测、OSD 层电量显示',",
     "'电源与电量：无充电检测硬件，靠端压趋势判充电，曲线查表 + 分段积分 + 关机记账',"),
]
for old, new in PAIRS:
    if old in s:
        s = s.replace(old, new)
    else:
        print('MISS:', old[:26])

# ---------- 2) 替换第 10 页，并新增第 11 页 ----------
NEW_PAGES = '''# ================= 10 专项 电量管理（方案） =================
content('专项 · 电量管理', 'POWER   MANAGEMENT', 10, [
    '硬件条件：整板无充电管理芯片、无 CHRG/STDBY 引脚，只有一路电池电压进 ADC —— 充电状态只能由软件判定',
    '放电：厂家曲线按 5 格间隔取点建表，先查单调性再插值，越界取端点',
    '充电判定三段式：进入看端压净涨、维持看去抖、退出看回落；不能只看绝对电压，满电静置也在恒压点之上',
    '充电积分：CC 段按 I/(C×60) 折算（3A/4.5Ah ≈ 1.1 格/分），CV 段按 K×(100?SOC)（τ ≈ 23 分），再乘 1.1~1.2 补偿',
    ('上界钳位到电压法读数，防止积分跑飞', 1),
], size=16, gap=13)

# ================= 11 专项 关机充电记账 =================
content('专项 · 关机充电记账', 'CHARGING   WHILE   POWERED   OFF', 11, [
    '问题：关机后软件不运行，这段时间的电量变化没有任何记录 —— 可能被补电、自放电，也可能拆下充满再装回',
    '做法：EEPROM 存「关机时的电压法值」当基线，开机与当前电压法值比较；存电压法值而非积分值，误差相减抵消',
    '关键坑：充电中关机不能写电压基线 —— 端压虚高会抬高基线，下次开机误判「没充过电」，充进去的电全丢',
    '兜底：魔数不符或越界直接用电压值；开机端压 ≥12.55V 按满电；充电中掉电重启，存值作下界、电压值作上界',
    ('效果：关机充电引起的重启跳变从 ±20 格压到 ±5 格以内', 1),
], size=16, gap=13)

'''

a = s.find('# ================= 10 专项 电量管理 =================')
b = s.find('# ================= 11 收获方法协作 =================')
if a < 0 or b < 0 or b < a:
    raise SystemExit('anchors not found')
s = s[:a] + NEW_PAGES + s[b:]

# ---------- 3) 后续页码后移一位（从大到小） ----------
s = s.replace("'15 / %d'", "'16 / %d'")
s = s.replace("section('04', '总结与建议', 'SUMMARY   &   SUGGESTIONS', 14)",
              "section('04', '总结与建议', 'SUMMARY   &   SUGGESTIONS', 15)")
s = s.replace("content('工作计划', 'PLAN', 13,", "content('工作计划', 'PLAN', 14,")
s = s.replace("section('03', '工作计划', 'WHAT   I   WILL   DO', 12)",
              "section('03', '工作计划', 'WHAT   I   WILL   DO', 13)")
s = s.replace("content('收获 · 排查方法与协作', 'METHOD   &   TEAMWORK', 11,",
              "content('收获 · 排查方法与协作', 'METHOD   &   TEAMWORK', 12,")
s = s.replace('TOTAL = 16', 'TOTAL = 17')
s = s.replace("'试用期述职报告_赵庆斌_v4.pptx'", "'试用期述职报告_赵庆斌_v5.pptx'")

io.open(P, 'w', encoding='cp936', newline='').write(s.replace('\n', '\r\n'))
print('ok: s100=%d guoxin=%d total17=%d v5=%d'
      % (s.count('森曼 S100'), s.count('国信 B130'), s.count('TOTAL = 17'), s.count('_v5.pptx')))
