# -*- coding: cp936 -*-
"""把刚才插入的 UTF-8 中文注释替换成 ASCII，修复 GBK 文件里的乱码"""
import io
import sys

P = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'

raw = open(P, 'rb').read()
before = len(raw)

old1 = ('/* 机械摩擦角度前馈补偿表 (每 10 度一个点, 单位与 target_Uq 相同)\n'
        ' * 来源: 25107 (251deg/s) 匀速段 3.7 圈实测统计, 已做 3 点平滑\n'
        ' * 注意: 只对应本台样机, 换机器需重新标定 (摩擦分布形状每台不同) */').encode('utf-8')

new1 = (b'/* Friction angle feed-forward table: one point per 10 deg,\n'
        b' * same unit as target_Uq.\n'
        b' * Source: 25107 (251 deg/s) steady run, 3.7 turns, 3-point smoothed.\n'
        b' * NOTE: valid for THIS prototype only; recalibrate when swapping unit. */')

old2 = ('/* 高速段机械摩擦角度前馈补偿: 每圈 1 次的周期性阻力, 按角度查表直接补到 Uq\n'
        '     * 只在 150deg/s 以上启用 —— 该表是在 251deg/s 下标定的, 低速摩擦特性不同 */').encode('utf-8')

new2 = (b'/* Friction feed-forward for high speed: 1-cycle-per-rev periodic load.\n'
        b'     * Enabled above 150 deg/s only -- table was calibrated at 251 deg/s. */')

for name, old, new in (('table comment', old1, new1), ('call comment', old2, new2)):
    cnt = raw.count(old)
    print('%s: found %d' % (name, cnt))
    if cnt != 1:
        print('  !! abort')
        sys.exit(1)
    raw = raw.replace(old, new)

open(P, 'wb').write(raw)
print('bytes %d -> %d' % (before, len(raw)))
