# -*- coding: cp936 -*-
"""生成与 pptx 内容一致的 HTML 幻灯片（UTF-8 输出，浏览器可演示/打印 PDF）"""
import os

CSS = """
* { box-sizing: border-box; }
body { margin:0; background:#e9edf3; font-family:"微软雅黑","Microsoft YaHei",system-ui,sans-serif; color:#3a414a; }
.slide { position:relative; width:1280px; height:720px; margin:28px auto; background:#fff;
         box-shadow:0 8px 28px rgba(16,40,70,.14); padding:60px 72px; overflow:hidden;
         page-break-after:always; }
.slide .bar { position:absolute; left:72px; top:64px; width:7px; height:44px; background:#1e6fba; }
.slide h1 { margin:0 0 4px 22px; font-size:30px; color:#0e2a47; letter-spacing:.5px; }
.slide .en { margin:0 0 0 23px; font-size:11px; color:#6b7481; letter-spacing:2px; text-transform:uppercase; }
.slide .hr { height:1px; background:#d8dfe8; margin:26px 0 30px; }
.slide .pg { position:absolute; right:72px; top:62px; font-size:20px; font-weight:700; color:#c3cdda; }
.slide ul { list-style:none; margin:0; padding:0; }
.slide li { position:relative; padding-left:30px; margin-bottom:16px; font-size:19px; line-height:1.65; }
.slide li:before { content:"■"; position:absolute; left:0; top:1px; color:#1e6fba; font-size:14px; }
.slide li.sub { color:#6b7481; font-size:16px; padding-left:52px; }
.slide li.sub:before { content:"·"; left:32px; color:#9aa6b5; font-size:18px; }
.foot { position:absolute; left:72px; bottom:26px; font-size:10px; color:#8b95a3; letter-spacing:1px; }
.cover, .end { background:#0e2a47; color:#fff; padding:0; }
.cover .side, .end .side { position:absolute; left:0; top:0; width:26px; height:100%; background:#1e6fba; }
.cover .wrap { position:absolute; left:150px; top:250px; }
.cover .acc { width:110px; height:6px; background:#3e9add; margin-bottom:26px; }
.cover h2 { margin:0; font-size:46px; letter-spacing:2px; }
.cover .sub { margin-top:16px; font-size:13px; color:#3e9add; letter-spacing:4px; }
.cover .meta { margin-top:52px; font-size:15px; line-height:2.1; color:#c9d6e4; }
.end .wrap { position:absolute; left:150px; top:300px; }
.end h2 { margin:0; font-size:44px; letter-spacing:8px; }
.end .acc { width:110px; height:6px; background:#3e9add; margin:26px 0 20px; }
.end p { margin:0; font-size:16px; color:#c9d6e4; }
.toc .left { position:absolute; left:0; top:0; width:437px; height:100%; background:#f4f7fb; }
.toc .left .side { position:absolute; left:0; top:0; width:24px; height:100%; background:#1e6fba; }
.toc .left h2 { position:absolute; left:96px; top:245px; margin:0; font-size:34px; color:#0e2a47; letter-spacing:2px; }
.toc .left .cn { position:absolute; left:97px; top:335px; font-size:16px; color:#6b7481; }
.toc ul { position:absolute; left:513px; top:120px; width:700px; }
.toc li { position:static; padding:0 0 26px 0; margin-bottom:26px; border-bottom:1px solid #e3e9f1; }
.toc li:before { content:none; }
.toc .num { display:inline-block; width:64px; font-size:24px; font-weight:700; color:#3e9add; vertical-align:top; }
.toc .t { display:inline-block; font-size:21px; font-weight:700; color:#0e2a47; }
.toc .d { display:block; margin:8px 0 0 64px; font-size:12px; color:#6b7481; }
.nav { position:fixed; right:18px; bottom:14px; font-size:12px; color:#7b8492; background:rgba(255,255,255,.9);
       padding:6px 12px; border-radius:14px; box-shadow:0 2px 8px rgba(0,0,0,.08); }
.cards .grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:20px 22px; margin-top:6px; }
.cards .card { background:#f4f7fb; border-top:5px solid #1e6fba; padding:18px 18px; min-height:196px; }
.cards .card h3 { margin:0 0 12px; font-size:15px; color:#0e2a47; }
.cards .card p { margin:0; font-size:12.5px; line-height:1.95; color:#6b7481; }

@media print {
  body { background:#fff; }
  .slide { margin:0; box-shadow:none; width:100%; height:auto; min-height:700px; }
  .nav { display:none; }
}
"""


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def slide(title, en, items, page):
    lis = []
    for it in items:
        if isinstance(it, tuple):
            lis.append('<li class="sub">%s</li>' % esc(it[0]))
        else:
            lis.append('<li>%s</li>' % esc(it))
    return (
        '<section class="slide">\n'
        '  <div class="bar"></div>\n'
        '  <h1>%s</h1>\n'
        '  <div class="en">%s</div>\n'
        '  <div class="pg">%02d</div>\n'
        '  <div class="hr"></div>\n'
        '  <ul>\n    %s\n  </ul>\n'
        '  <div class="foot">MYTECH 名扬时代  |  试用期述职报告</div>\n'
        '</section>\n' % (esc(title), esc(en), page, '\n    '.join(lis))
    )


parts = []

# 封面
parts.append(
    '<section class="slide cover">\n'
    '  <div class="side"></div>\n'
    '  <div class="wrap">\n'
    '    <div class="acc"></div>\n'
    '    <h2>试用期述职报告</h2>\n'
    '    <div class="sub">PROBATION WORK REVIEW</div>\n'
    '    <div class="meta">汇报人：赵庆斌&nbsp;&nbsp;&nbsp;&nbsp;研发部 · 单片机软件<br>'
    '入职日期：2026.8.3&nbsp;&nbsp;&nbsp;&nbsp;汇报日期：2026.10</div>\n'
    '  </div>\n'
    '</section>\n'
)

# 目录
toc_items = [
    ('01', '试用期回顾', '17 个项目 / 五个方向 / 模块移植 / 调试排障'),
    ('02', '工作收获', '技术 / 架构 / 方法 / 协作'),
    ('03', '工作计划', '短期 / 中期 / 长期'),
    ('04', '总结与建议', '总体总结 / 对团队的建议'),
]
toc_lis = ''.join(
    '<li><span class="num">%s</span><span class="t">%s</span>'
    '<span class="d">%s</span></li>\n' % (n, esc(t), esc(d)) for n, t, d in toc_items
)
parts.append(
    '<section class="slide toc">\n'
    '  <div class="left"><div class="side"></div><h2>CONTENTS</h2><div class="cn">目 录</div></div>\n'
    '  <ul>\n' + toc_lis + '  </ul>\n'
    '</section>\n'
)

body = [
    ('试用期回顾 · 总览', 'OVERVIEW', [
        '入职三个月跟进 17 个项目，覆盖电机、显示、电源、光敏、协议五个方向',
        '三类工作：问题修复、定制化项目（U 款球机对接零位机芯等）、新功能开发（电量管理、模块移植）',
        '讲法：每条按「现象 → 判断依据 → 处理」展开，重点在怎么定位，而不是改了什么',
        ('项目名按实际型号写，不做改写', 1),
    ], 3),
    ('收获 · 电机与云台', 'MOTOR & GIMBAL', [
        'U 款球机定制对接：第三方零位机芯（VBM-5100）报文对不上，先抓串口逐帧对齐格式与时序，再按零位脉冲修正电机零点，实现上电自动找零',
        '申盛 T160：低速丢步与自检撞头，定位到限位与零点偏差使行程被提前截断，调整电机参数与加减速曲线后恢复',
        'PM 球机：自检撞头与角度不准，重新核对行程与零点后修正',
        '5d6750：完成精度与速度测试，形成可复现的测试方法',
        ('共性：运动类问题先查限位、零点、加减速曲线，再怀疑电机本身', 1),
    ], 4),
    ('收获 · 显示与电源', 'DISPLAY & POWER', [
        '电量管理：按充电曲线积分累计电量，识别充放电状态并在 OSD 层输出百分比；5100 森美 电量来回跳，靠采样滤波 + 刷新节流解决',
        '5100 森美：OLED 开机花屏与缺 CU 键，定位为初始化顺序与按键扫描时序问题',
        '海洋王 6126b：电源板屏幕 y 板反转，修正初始化与显示方向配置',
        '球芯全系、海洋王 60d：电源板开机花屏与画面异常，判断为共性问题后统一处理',
        ('共性：花屏与异常多出在初始化顺序和刷新节流，不在图像链路', 1),
    ], 5),
    ('收获 · 光敏与协议', 'LIGHT & PROTOCOL', [
        'k13 T160：新增 my 查询协议（帧格式、超时重发），并增加垂直电机跟随，解决变倍后画面上下偏移',
        '标配 5 寸：特殊预置位（巡航等）无法调用、云台报警信息查不到，补齐协议解析分支',
        'LMD B1105C：新增软 / 硬光敏切换逻辑',
        '国传信 B130：增加白光灯自动切换模式',
        '5SKS / BS7：修复虚标与自动翻转异常，并按现场光照调整光敏切换阈值',
    ], 6),
    ('收获 · 排查方法与协作', 'METHOD & TEAMWORK', [
        '66d：尾线不能查询数据，逐层排除后确认为硬件问题，没有在软件上反复试；锐明 IRC4t、B3AA P8L2 同样先定位再动手',
        '固定顺序：复现现象 → 查最近改动 → 查逻辑与时序 → 查标定 → 最后怀疑硬件',
        '遇到不懂的先问，和硬件、测试同事把信息对齐再动手',
        '交付习惯：最小改动、可回退、可追溯，不擅自改安全阈值与协议码',
    ], 7),
    ('配件模块移植', 'MODULE PORTING', [
        '激光测距：55AA 帧解析、单次 / 连续测距、命令透传与应答回显',
        '红外补光灯：开关、亮度、角度随变倍联动、上电强制关灯保护',
        '移植原则：不改动原工程控制逻辑，按最小改动接入并逐项联调验证',
        ('接线与协议按目标机型核对：串口占用、引脚定义、方向控制脚', 1),
    ], 8),
    ('工作计划', 'PLAN', [
        '短期：深入研究伺服电机控制，从电流环响应、参数自整定入手，提升低速平稳性',
        '短期：参与稳像功能的调参与优化，改善抖动抑制效果与异常工况稳定性',
        '中期：学习 RTOS 的任务调度与优先级设计，尝试引入工程，改善多任务实时性',
        '中期：研究模糊 PID，针对负载变化、装配差异等不确定因素做自适应补偿',
        '长期：把重复问题沉淀成自检清单与案例库，参与控制模块平台化',
    ], 9),
    ('总结与建议', 'SUMMARY & SUGGESTIONS', [
        '总结：三个月完成从协助到独立跟进项目的过渡，问题覆盖电机、显示、电源、光敏与协议',
        '建议一：建立整机联调自检清单与常见问题案例库，新机型可直接复用',
        '建议二：限位值、标定值、PID 与电机参数按机型版本化记录，避免换机后参数错配',
        '建议三：软硬件接口（串口分配、协议码、引脚定义）统一维护一份，减少联调沟通成本',
    ], 10),
]

for t, en, items, pg in body:
    parts.append(slide(t, en, items, pg if pg < 4 else pg + 1))

# 结束页
parts.append(
    '<section class="slide end">\n'
    '  <div class="side"></div>\n'
    '  <div class="wrap">\n'
    '    <h2>谢 谢</h2>\n'
    '    <div class="acc"></div>\n'
    '    <p>请各位领导批评指正</p>\n'
    '  </div>\n'
    '</section>\n'
)

HTML = (
    '<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
    '<title>试用期述职报告 - 赵庆斌</title>\n<style>' + CSS + '</style>\n</head>\n<body>\n'
    + ''.join(parts) +
    '<div class="nav">← → 翻页 ｜ F 全屏 ｜ Ctrl+P 打印/导出 PDF</div>\n'
    '<script>\n'
    'var idx = 0, ss = document.querySelectorAll(".slide");\n'
    'function go(i) { idx = Math.max(0, Math.min(ss.length - 1, i));'
    ' ss[idx].scrollIntoView({behavior:"smooth", block:"center"}); }\n'
    'document.addEventListener("keydown", function (e) {\n'
    '  if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") { e.preventDefault(); go(idx + 1); }\n'
    '  if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); go(idx - 1); }\n'
    '  if (e.key === "f" || e.key === "F") { if (!document.fullscreenElement) document.documentElement.requestFullscreen();'
    ' else document.exitFullscreen(); }\n'
    '});\n'
    '</script>\n</body>\n</html>\n'
)

desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
if not os.path.isdir(desktop):
    desktop = 'D:\\Codebuddy\\output'
    os.makedirs(desktop, exist_ok=True)
out = os.path.join(desktop, '试用期述职报告_赵庆斌_2026-10.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)
print('SAVED ' + out)
print('size ' + str(os.path.getsize(out)) + ' bytes')
print('slides ' + str(len(parts)))
