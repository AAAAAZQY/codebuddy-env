# -*- coding: cp936 -*-
"""把 comp_pos 的声明从 if 块内移到函数开头（C89 要求）"""
import io
import sys

P = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'

s = io.open(P, encoding='gbk', newline='').read()

old1 = ('void bldc_velocity_loop(BLDC_t * bldc , Motor_Sensor_t * sensor)\r\n'
        '{\r\n'
        '    bldc->current_velocity')
new1 = ('void bldc_velocity_loop(BLDC_t * bldc , Motor_Sensor_t * sensor)\r\n'
        '{\r\n'
        '    int32_t comp_pos;\r\n'
        '\r\n'
        '    bldc->current_velocity')

old2 = '        int32_t comp_pos = bldc->current_position % 36000;'
new2 = '        comp_pos = bldc->current_position % 36000;'

for name, old, new in (('header', old1, new1), ('assign', old2, new2)):
    cnt = s.count(old)
    print('%s: %d' % (name, cnt))
    if cnt != 1:
        print('  !! abort')
        sys.exit(1)
    s = s.replace(old, new)

io.open(P, 'w', encoding='gbk', newline='').write(s)
print('ok')
