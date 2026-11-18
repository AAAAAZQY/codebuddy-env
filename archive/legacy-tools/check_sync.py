# -*- coding: cp936 -*-
"""校验副本与真实工程是否一致（SHA256）"""
import hashlib
import io
import sys
import time
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

REAL_ROOT = r'd:\aMyProject\Project\MIS-T160\XH\mis-t160\ptz_source_code\source_code'
COPY_ROOT = r'd:\plain_view\66T\mis-t160-XH-ptz'
REL = r'application\motor_bldc.c'

copy_path = COPY_ROOT + '\\' + REL
real_path = REAL_ROOT + '\\' + REL


def sha_local(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def fetch_real(p):
    url = 'http://127.0.0.1:37821/raw?p=' + urllib.parse.quote(p, safe='')
    req = urllib.request.Request(url, headers={'User-Agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read()


c = sha_local(copy_path)
print('copy : %s  (%d bytes)' % (c[:16], len(open(copy_path, 'rb').read())))

for attempt in range(3):
    try:
        raw = fetch_real(real_path)
        r = hashlib.sha256(raw).hexdigest()
        print('real : %s  (%d bytes)' % (r[:16], len(raw)))
        print('match: %s' % ('YES' if c == r else 'NO'))
        break
    except Exception as e:
        print('fetch attempt %d failed: %s' % (attempt + 1, e))
        time.sleep(2)
