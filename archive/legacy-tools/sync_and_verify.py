# -*- coding: gbk -*-
"""把 motor_bldc.c 同步到编译目录并核对。"""
import hashlib
import io
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

M = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
T = (r'd:\aMyProject\Project\MIS-T160\XH\mis-t160\ptz_source_code'
     r'\source_code\application\motor_bldc.c')

raw = open(M, 'rb').read()
print('mirror %d 字节  sha=%s' % (len(raw), hashlib.sha256(raw).hexdigest()[:12]))


def read_target():
    url = 'http://127.0.0.1:37821/raw?p=' + urllib.parse.quote(T, safe='')
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={'User-Agent': 'curl/8'}),
        timeout=8).read()


try:
    cur = read_target()
    print('target %d 字节  一致=%s' % (len(cur), cur == raw))
    if cur != raw:
        io.open(T, 'wb').write(raw)
        cur = read_target()
        print('已重写 target，复核一致=%s' % (cur == raw))
except Exception as e:                              # noqa: BLE001
    print('同步服务不可用:', e)
    io.open(T, 'wb').write(raw)
    print('已直接写入 target')

print('')
print('--- target 侧参数 ---')
try:
    s = io.open(T, encoding='gbk', errors='replace').read()
except Exception:                                   # noqa: BLE001
    s = raw.decode('gbk', 'replace')
for name in ('position_pid', 'velocity_pid_pan'):
    i = s.find('const PID_t %s' % name)
    b = s[i:i + 430]
    vals = []
    for k in ('kp', 'ki', 'kd', 'integral_max', 'output_max'):
        m = re.search(r'\.%s\s*=\s*(-?[0-9.]+)' % k, b)
        vals.append('%s=%s' % (k, m.group(1) if m else '?'))
    print('  %-18s %s' % (name, '  '.join(vals)))
print('  MOTOR_COGGING_COMP 残留: %d' % s.count('MOTOR_COGGING_COMP'))
print('  uq_comp_18x 残留: %d' % s.count('uq_comp_18x'))
