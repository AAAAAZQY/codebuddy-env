# -*- coding: cp936 -*-
"""把 motor_bldc.c 里 7 行中文注释改成英文，使文件回到纯 ASCII"""
import io
import sys

P = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'

s = io.open(P, encoding='utf-8', newline='').read()

pairs = [
    ('/* 机械摩擦角度前馈补偿表 (每 10 度一个点, 单位与 target_Uq 相同)\r\n'
     ' * 来源: 25107 (251deg/s) 匀速段 3.7 圈实测统计, 已做 3 点平滑\r\n'
     ' * 注意: 只对应本台样机, 换机器需重新标定 (摩擦分布形状每台不同) */',
     '/* Friction angle feed-forward table: one point per 10 deg,\r\n'
     ' * same unit as target_Uq.\r\n'
     ' * Source: 25107 (251 deg/s) steady run, 3.7 turns, 3-point smoothed.\r\n'
     ' * NOTE: valid for THIS prototype only; recalibrate when replacing the unit. */'),

    ('/* vofa JustFloat 帧：5 个 float + 帧尾 00 00 80 7F，共 24 字节。\r\n'
     ' * 走 board_uart_cmd_send() 是因为 RS485 半双工需要切方向脚。 */',
     '/* vofa JustFloat frame: N floats + tail 00 00 80 7F.\r\n'
     ' * board_uart_cmd_send() is used because RS485 half-duplex needs the DE pin. */'),

    ('    /* 50ms 一帧：9600bps 下 24 字节约 480B/s，留一半带宽给 Pelco 通信 */',
     '    /* 50ms per frame: ~480B/s at 9600bps, leaves half the bandwidth for Pelco */'),

    ('        /* 调试期：PAN 轴一旦开始运动就发，不依赖 plot_switch（该变量全工程没有赋值点） */',
     '        /* Debug: send while PAN is moving; plot_switch is never set in this project */'),
]

for old, new in pairs:
    cnt = s.count(old)
    print('%-46s %d' % (old.strip().split('\r\n')[0][:44], cnt))
    if cnt != 1:
        print('  !! abort')
        sys.exit(1)
    s = s.replace(old, new)

io.open(P, 'w', encoding='utf-8', newline='').write(s)

raw = open(P, 'rb').read()
bad = sum(1 for b in raw if b > 127)
print()
print('size = %d, non-ascii bytes = %d' % (len(raw), bad))
print('pure ASCII:', bad == 0)
