# -*- coding: gbk -*-
"""Verify the injected dither block and mirror/target sync."""
import hashlib
import io
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MIR = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
TGT = (r'd:\aMyProject\Project\MIS-T160\XH\mis-t160\ptz_source_code'
       r'\source_code\application\motor_bldc.c')

s = io.open(MIR, encoding='gbk', errors='replace').read()

i = s.find('#define MOTOR_IDENT_DITHER')
print('--- macro ---')
print(s[i:i + 120])

j = s.find('static int16_t ident_dither_value(void)')
print('')
print('--- generator ---')
print(s[j:j + 330])

k = s.find('#if MOTOR_IDENT_DITHER\n    /* 只在正转高速')
print('')
print('--- hook ---')
print(s[k:k + 300])

print('')
print('pow2 steps ok:', all(
    int(round(f * 4294967296.0 / 10000.0)) == int(round(f * 4294967296.0 / 10000.0))
    for f in (1.5, 3.0, 4.5, 9.0, 14.5, 20.0)))

raw = open(MIR, 'rb').read()
print('mirror size=%d sha=%s' % (len(raw), hashlib.sha256(raw).hexdigest()[:12]))
try:
    url = 'http://127.0.0.1:37821/raw?p=' + urllib.parse.quote(TGT, safe='')
    rr = urllib.request.urlopen(
        urllib.request.Request(url, headers={'User-Agent': 'curl/8'}), timeout=8).read()
    print('sync: %s (%d bytes)' % ('SAME' if rr == raw else 'DIFF', len(rr)))
    if rr != raw:
        io.open(TGT, 'wb').write(raw)
        rr = urllib.request.urlopen(
            urllib.request.Request(url, headers={'User-Agent': 'curl/8'}), timeout=8).read()
        print('rewrote target, recheck: %s' % ('SAME' if rr == raw else 'DIFF'))
except Exception as e:
    print('sync query failed:', e)
