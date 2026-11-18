# -*- coding: cp936 -*-
"""通过桥接（受信进程）读取明文，再由非受信进程写入 D:\\bProject，落盘为明文"""
import json
import os
import sys
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

API = 'http://127.0.0.1:37821'
SRC = r'D:\aMyProject\Project\22b2\22bmain\22b2\ptz_source_code\source_code\tools\pid_tuner'
DST = r'D:\bProject\pid_tuner'
SKIP = {'__pycache__', '.git', '.svn'}


def listdir(p):
    u = API + '/list?p=' + urllib.parse.quote(p, safe='')
    with urllib.request.urlopen(u, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def raw(p):
    u = API + '/raw?p=' + urllib.parse.quote(p, safe='')
    with urllib.request.urlopen(u, timeout=120) as r:
        return r.read()


def walk(src, dst, depth=0):
    if depth > 4:
        return
    try:
        j = listdir(src)
    except Exception as e:
        print('LIST FAIL %s : %s' % (src, e))
        return
    if not j.get('ok'):
        print('LIST NOT OK %s : %s' % (src, j))
        return
    if not os.path.isdir(dst):
        os.makedirs(dst, exist_ok=True)
    for e in j.get('entries', []):
        n = e.get('n', '')
        if (not n) or (n in SKIP):
            continue
        s = os.path.join(src, n)
        d = os.path.join(dst, n)
        if e.get('d'):
            walk(s, d, depth + 1)
        else:
            try:
                data = raw(s)
                with open(d, 'wb') as f:
                    f.write(data)
                print('OK  %-24s %8d' % (n, len(data)))
            except Exception as ex:
                print('FAIL %-24s %s' % (n, ex))


walk(SRC, DST)
print('DONE')
