# -*- coding: cp936 -*-
"""重建 motor_bldc.c 的"改动前"版本，用于并排对比"""
import io
import shutil

SRC = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
DST = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc_before.c'

shutil.copyfile(SRC, DST)
s = io.open(DST, encoding='gbk', newline='').read()

# 1) 删掉前馈补偿表（含前面注释）
i1 = s.find('/* 机械摩擦角度前馈补偿表')
if i1 < 0:
    raise SystemExit('table not found')
j1 = s.find('};', s.find('uq_comp_36', i1)) + 2
while j1 < len(s) and s[j1] in '\r\n':
    j1 += 1
s = s[:i1] + s[j1:]

# 2) 删掉补偿调用块
i2 = s.find('    /* 高速段机械摩擦角度前馈补偿')
if i2 < 0:
    raise SystemExit('call block not found')
j2 = s.find('    bldc_set_phase_voltage', i2)
s = s[:i2] + s[j2:]

# 3) vofa 帧 6 -> 5 通道
reps = [
    ('const float *buf6', 'const float *buf5'),
    ('uint8_t frame[28];', 'uint8_t frame[24];'),
    ('memcpy(frame, buf6, 24);', 'memcpy(frame, buf5, 20);'),
    ('memcpy(&frame[24], vofa_tail, 4);', 'memcpy(&frame[20], vofa_tail, 4);'),
    ('board_uart_cmd_send(serial, frame, 28);', 'board_uart_cmd_send(serial, frame, 24);'),
    ('    float send_buf[6];', '    float send_buf[5];'),
    ('            send_buf[5] = (float)g_bldc[MOTOR_PORT_PAN].current_position;\r\n', ''),
    ('            send_buf[5] = (float)g_bldc[MOTOR_PORT_TILT].current_position;\r\n', ''),
    ('28 字节约 560B/s', '24 字节约 480B/s'),
    ('    int32_t comp_pos;\r\n\r\n', ''),
]
for old, new in reps:
    n = s.count(old)
    print('%-52s %d' % (old.strip()[:50], n))
    s = s.replace(old, new)

io.open(DST, 'w', encoding='gbk', newline='').write(s)
print('before-version written:', DST)
