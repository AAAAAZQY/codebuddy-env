# -*- coding: gbk -*-
"""把 vofa ch5（PAN）从位置改成速度环积分；只产出到中转文件，由 PowerShell 落盘。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
MID = r'D:\Codebuddy\tmp\mb_edit.csv'

t = io.open(SRC, encoding='gbk', errors='replace').read()

OLD = '            send_buf[5] = (float)g_bldc[MOTOR_PORT_PAN].current_position;'
NEW = '            send_buf[5] = g_bldc[MOTOR_PORT_PAN].pid_velocity.integral;'

n = t.count(OLD)
print('PAN ch5 锚点命中 %d 次' % n)
if n != 1:
    print('FAIL: 锚点不唯一，未生成')
    raise SystemExit(1)

# 顺手把注释里的通道说明补上
t = t.replace(OLD, NEW, 1)

io.open(MID, 'w', encoding='gbk', newline='').write(t)
print('已生成中转文件:', MID)
print('  替换行: send_buf[5] = pid_velocity.integral')

# 复核
chk = io.open(MID, encoding='gbk', errors='replace').read()
i = chk.find('send_buf[5] = g_bldc[MOTOR_PORT_PAN]')
print('  复核:', chk[i:i + 66].splitlines()[0])
