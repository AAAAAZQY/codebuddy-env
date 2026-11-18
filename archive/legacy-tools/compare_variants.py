# -*- coding: gbk -*-
"""对比各副本的参数，判断“最初状态”该用哪套值。"""
import io
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FILES = [
    r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c',
    r'd:\plain_view\66T\mis-t160-main-ptz\application\motor_bldc.c',
    r'd:\plain_view\mis-t160-main-ptz\application\motor_bldc.c',
    (r'D:\aMyProject\Project\MIS-T160\mian\main\mis-t160\ptz_source_code'
     r'\source_code\application\motor_bldc.c'),
    (r'D:\aMyProject\Project\MIS-T160\LI-T160SW\mis-t160\ptz_source_code'
     r'\source_code\application\motor_bldc.c'),
]

for p in FILES:
    if not os.path.isfile(p):
        print('缺失:', p)
        continue
    s = io.open(p, encoding='gbk', errors='replace').read()
    st = os.stat(p)

    def blk(n):
        i = s.find('const PID_t %s' % n)
        return s[i:i + 460] if i >= 0 else ''

    def v(b, k):
        m = re.search(r'\.%s\s*=\s*(-?[0-9.]+)f' % k, b)
        return m.group(1) if m else '-'

    vp, pp = blk('velocity_pid_pan'), blk('position_pid')
    short = os.path.abspath(p)
    print('%s' % short)
    print('    %6d 字节  %s  COGGING=%s'
          % (st.st_size, time.strftime('%m-%d %H:%M', time.localtime(st.st_mtime)),
             (re.search(r'#define MOTOR_COGGING_COMP\s+(\d)', s) or ['', '无'])[1]
             if re.search(r'#define MOTOR_COGGING_COMP\s+(\d)', s) else '无宏'))
    print('    velocity  kp=%-6s ki=%-7s kd=%-6s imax=%-9s out=%s'
          % (v(vp, 'kp'), v(vp, 'ki'), v(vp, 'kd'),
             v(vp, 'integral_max'), v(vp, 'output_max')))
    print('    position  kp=%-6s ki=%-7s kd=%-6s out=%s'
          % (v(pp, 'kp'), v(pp, 'ki'), v(pp, 'kd'), v(pp, 'output_max')))
    print('')
