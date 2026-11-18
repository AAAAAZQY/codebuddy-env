# -*- coding: utf-8 -*-
"""
bridge-edit.py -- 通过本地桥(37821) + python 直读直写，安全修改 DLP 加密工程。

用法:
  python bridge-edit.py ping
  python bridge-edit.py read <path> [--out FILE]
  python bridge-edit.py write <path> --from FILE [--bytes] [--dry]
  python bridge-edit.py replace <path> (--old-file F --new-file F | --old S --new S)
                  [--expect N] [--dry] [--verify-delay S]
  python bridge-edit.py byte-edit <path> --plan <json-file|json> [--expect N] [--dry] [--verify-delay S]
  python bridge-edit.py verify <path> [--snapshot DIR] [--delay S] [--atrest]

约定:
  - 文本/临时文件一律 UTF-8；写盘前统一 UTF-8 -> GBK 字节，不做 GBK 解码再编码。
  - 行尾先归一 LF，再按命中文本风格决定是否转 CRLF（幂等，杜绝 \\r\\r\\n）。
  - 每次真实写盘: 先落快照(回滚点) -> 写盘回读 SHA -> 索引刷新 -> 延迟独立复查。
  - --dry 只统计不写盘；--expect 用于拦截命中数/编辑数不符。
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BRIDGE_PORT = int(os.environ.get('BRIDGE_PORT', '37821'))
BACKUP_DIR = r'D:\Codebuddy\backup\bridge-edit'
VERIFY_SCRIPT = r'D:\Codebuddy\toolbox\bridge-verify.py'
INDEX_SCRIPT = r'D:\Codebuddy\toolbox\project-index.py'
VERIFY_DELAY_SEC = 3.0


def fail(msg, code=1):
    print('[FAIL] ' + msg)
    sys.exit(code)


def http_get(path, qs):
    url = 'http://127.0.0.1:%d%s?%s' % (BRIDGE_PORT, path, urllib.parse.urlencode(qs))
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def fetch_raw(p):
    """python 受 DLP 信任：open() 返回解密后的明文字节；磁盘仍为密文。"""
    try:
        with open(p, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return None


def read_utf8(p, what):
    try:
        with open(p, 'rb') as f:
            return f.read().decode('utf-8')
    except Exception as e:
        fail('cannot read %s %s: %s' % (what, p, e))


def encode_text(s, style):
    """UTF-8 文本 -> GBK 字节。先归一 LF，再按 style 转 CRLF；幂等。"""
    b = s.encode('gbk').replace(b'\r\n', b'\n')
    return b.replace(b'\n', b'\r\n') if style == 'crlf' else b


def line_style(b):
    crlf = b.count(b'\r\n')
    return 'crlf' if crlf > (b.count(b'\n') - crlf) else 'lf'


def text_variants(s):
    """旧文本的 LF / CRLF 变体，供匹配命中。"""
    b = s.encode('gbk').replace(b'\r\n', b'\n')
    return [b, b.replace(b'\n', b'\r\n')] if b'\n' in b else [b]


def cmd_ping(_):
    st, body = http_get('/ping', {})
    d = json.loads(body)
    print('[OK] bridge pid=%s build=%s roots=%d' % (d.get('pid'), d.get('build'), len(d.get('roots', []))))


def cmd_read(a):
    raw = fetch_raw(a.path)
    if raw is None:
        fail('file not found: %s' % a.path)
    if a.out:
        with open(a.out, 'wb') as f:
            f.write(raw)
        print('[OK] saved %d bytes -> %s  sha256=%s' % (len(raw), a.out, hashlib.sha256(raw).hexdigest()[:8]))
    else:
        sys.stdout.reconfigure(errors='replace')
        print(raw.decode('gbk', 'replace'))


def save_snapshot(p, pre, post, kind='edit'):
    """回滚点前置：BACKUP_DIR/<时间戳>/<basename> + manifest.json。"""
    ms = int(time.time() * 1000) % 1000
    d = os.path.join(BACKUP_DIR, time.strftime('%Y%m%d-%H%M%S') + '-%03d' % ms)
    os.makedirs(d, exist_ok=True)
    base = os.path.basename(p)
    if pre is not None:
        with open(os.path.join(d, base), 'wb') as f:
            f.write(pre)
    after_path = os.path.join(d, base + '.after')
    with open(after_path, 'wb') as f:
        f.write(post)
    man = {
        'version': 1, 'kind': kind,
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'real_path': p, 'base': base,
        'existed_before': pre is not None,
        'after_file': after_path,
        'sha_before': hashlib.sha256(pre).hexdigest() if pre is not None else None,
        'sha_after': hashlib.sha256(post).hexdigest(),
        'size_before': len(pre) if pre is not None else None,
        'size_after': len(post),
    }
    with open(os.path.join(d, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(man, f, ensure_ascii=True)
    return d


def write_bytes(p, data):
    try:
        with open(p, 'wb') as f:
            f.write(data)
    except Exception as e:
        fail('/write %s -> %s' % (p, e))
    back = open(p, 'rb').read()
    h = hashlib.sha256(data).hexdigest()
    if hashlib.sha256(back).hexdigest() != h:
        fail('write-back verify FAILED: sent=%s readback=%s' % (h[:8], hashlib.sha256(back).hexdigest()[:8]))
    return h


def refresh_index(p):
    try:
        subprocess.run([sys.executable, INDEX_SCRIPT, '--update', '--path', p],
                       timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print('[WARN] index refresh skipped: %s' % e)


def run_post_verify(p, snap_dir, delay):
    if not os.path.isfile(VERIFY_SCRIPT):
        fail('verify script missing: %s' % VERIFY_SCRIPT)
    cmd = [sys.executable, VERIFY_SCRIPT, p, '--snapshot', snap_dir, '--delay', str(delay)]
    try:
        r = subprocess.run(cmd, timeout=180)
    except Exception as e:
        fail('post-write verification could not run: %s | snapshot=%s' % (e, snap_dir))
    if r.returncode != 0:
        fail('post-write verification FAILED (see [VERIFY FAIL] above) | snapshot=%s' % snap_dir)


def commit(p, pre, post, label, delay):
    """统一提交：快照前置 -> 写盘 -> 索引刷新 -> 延迟复查 -> 一行结果。"""
    snap = save_snapshot(p, pre, post)
    h = write_bytes(p, post)
    refresh_index(p)
    run_post_verify(p, snap, delay)
    print('[OK] %s %s  (%d -> %d bytes)  sha256=%s  snapshot=%s'
          % (label, p, len(pre) if pre is not None else 0, len(post), h[:8], snap))


def cmd_write(a):
    if a.bytes:
        with open(a.src, 'rb') as f:
            data = f.read()
    else:
        txt = read_utf8(a.src, 'source')
        data = encode_text(txt, line_style(txt.encode('gbk')))
    if a.dry:
        print('[DRY] would write %d bytes (sha256=%s) -> %s' % (len(data), hashlib.sha256(data).hexdigest()[:8], a.path))
        return
    commit(a.path, fetch_raw(a.path), data, 'wrote', a.verify_delay)


def cmd_replace(a):
    if bool(a.old_file) != bool(a.new_file):
        fail('--old-file 与 --new-file 必须成对')
    if a.old_file:
        old_txt, new_txt = read_utf8(a.old_file, 'old'), read_utf8(a.new_file, 'new')
    else:
        old_txt, new_txt = a.old, a.new
    raw = fetch_raw(a.path)
    if raw is None:
        fail('file not found: %s' % a.path)
    hit, old_b = 0, None
    for ob in text_variants(old_txt):
        n = raw.count(ob)
        if n:
            hit, old_b = n, ob
            break
    if not hit:
        fail('old text not found in %s (0 matches)' % a.path)
    if hit != a.expect:
        fail('old text matched %d times, expected %d -- abort, nothing written' % (hit, a.expect))
    new_b = encode_text(new_txt, line_style(old_b))
    post = raw.replace(old_b, new_b)
    if a.dry:
        print('[DRY] %s: %d match(es), %d -> %d bytes, nothing written'
              % (a.path, hit, len(raw), len(post)))
        return
    commit(a.path, raw, post, 'replaced %d occurrence(s) in' % hit, a.verify_delay)


def parse_hex_bytes(v, what):
    if isinstance(v, int):
        if not (0 <= v <= 255):
            fail('%s: byte out of range: %r' % (what, v))
        return bytes([v])
    t = str(v).lower().replace('0x', '').replace(' ', '').replace(',', '').replace('\t', '')
    if (not t) or (len(t) % 2):
        fail('%s: bad hex string: %r' % (what, v))
    try:
        return bytes.fromhex(t)
    except ValueError:
        fail('%s: bad hex string: %r' % (what, v))


def load_edit_plan(spec):
    txt = spec if spec.lstrip().startswith(('[', '{')) else read_utf8(spec, 'plan')
    try:
        d = json.loads(txt)
    except Exception as e:
        fail('plan json parse failed: %s' % e)
    if isinstance(d, dict):
        d = d.get('edits')
    if not isinstance(d, list) or not d:
        fail('plan must be a non-empty list (or {"edits":[...]})')
    return d


def edit_pos(raw, e, idx):
    if 'offset' in e and 'anchor' in e:
        fail('edit #%d: offset and anchor are mutually exclusive' % idx)
    if 'offset' in e:
        return int(e['offset'])
    if 'anchor' in e:
        ab = encode_text(str(e['anchor']), 'lf')
        occ, pos = int(e.get('occurrence', 0)), -1
        for _ in range(occ + 1):
            pos = raw.find(ab, pos + 1)
            if pos < 0:
                fail('edit #%d: anchor not found (occurrence %d): %r' % (idx, occ, e['anchor']))
        return pos + int(e.get('rel', 0))
    fail('edit #%d: missing offset/anchor' % idx)


def cmd_byte_edit(a):
    plan = load_edit_plan(a.plan)
    raw = fetch_raw(a.path)
    if raw is None:
        fail('file not found: %s' % a.path)
    if a.expect is not None and len(plan) != a.expect:
        fail('plan has %d edits, expected %d -- abort, nothing written' % (len(plan), a.expect))
    buf, used, changed = bytearray(raw), [], 0
    for i, e in enumerate(plan):
        if 'new' not in e:
            fail('edit #%d: missing new' % i)
        nb = parse_hex_bytes(e['new'], 'edit #%d new' % i)
        pos = edit_pos(raw, e, i)
        if pos < 0 or pos + len(nb) > len(buf):
            fail('edit #%d: range out of file: %d+%d > %d' % (i, pos, len(nb), len(buf)))
        if 'old' in e:
            ob = parse_hex_bytes(e['old'], 'edit #%d old' % i)
            if len(ob) != len(nb):
                fail('edit #%d: old/new length differ (%d vs %d)' % (i, len(ob), len(nb)))
            if raw[pos:pos + len(ob)] != ob:
                fail('edit #%d: old mismatch at %d: got %s expected %s'
                     % (i, pos, raw[pos:pos + len(ob)].hex(), ob.hex()))
        for p0, p1 in used:
            if not (pos + len(nb) <= p0 or pos >= p1):
                fail('edit #%d: overlaps previous edit (%d..%d)' % (i, p0, p1))
        used.append((pos, pos + len(nb)))
        if buf[pos:pos + len(nb)] != nb:
            changed += 1
        buf[pos:pos + len(nb)] = nb
    post = bytes(buf)
    if a.dry:
        print('[DRY] byte-edit %s: %d edit(s), %d changed, %d -> %d bytes, nothing written'
              % (a.path, len(plan), changed, len(raw), len(post)))
        return
    commit(a.path, raw, post, 'byte-edited %d edit(s), %d range(s) changed in' % (len(plan), changed), a.verify_delay)


def cmd_verify(a):
    cmd = [sys.executable, VERIFY_SCRIPT, a.path]
    if a.snapshot:
        cmd += ['--snapshot', a.snapshot]
    if a.delay is not None:
        cmd += ['--delay', str(a.delay)]
    if a.atrest:
        cmd += ['--atrest']
    sys.exit(subprocess.run(cmd).returncode)


def main():
    global BRIDGE_PORT
    ap = argparse.ArgumentParser(description='edit real project files via codebuddy bridge')
    ap.add_argument('--port', type=int, default=BRIDGE_PORT)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('ping')
    p = sub.add_parser('read'); p.add_argument('path'); p.add_argument('--out')
    p = sub.add_parser('write'); p.add_argument('path'); p.add_argument('--from', dest='src', required=True)
    p.add_argument('--bytes', action='store_true'); p.add_argument('--dry', action='store_true')
    p.add_argument('--verify-delay', type=float, default=VERIFY_DELAY_SEC)
    p = sub.add_parser('replace'); p.add_argument('path')
    p.add_argument('--old-file'); p.add_argument('--new-file'); p.add_argument('--old'); p.add_argument('--new')
    p.add_argument('--expect', type=int, default=1); p.add_argument('--dry', action='store_true')
    p.add_argument('--verify-delay', type=float, default=VERIFY_DELAY_SEC)
    p = sub.add_parser('byte-edit'); p.add_argument('path'); p.add_argument('--plan', required=True)
    p.add_argument('--expect', type=int); p.add_argument('--dry', action='store_true')
    p.add_argument('--verify-delay', type=float, default=VERIFY_DELAY_SEC)
    p = sub.add_parser('verify'); p.add_argument('path'); p.add_argument('--snapshot')
    p.add_argument('--delay', type=float); p.add_argument('--atrest', action='store_true')
    a = ap.parse_args()
    BRIDGE_PORT = a.port
    {'ping': cmd_ping, 'read': cmd_read, 'write': cmd_write, 'replace': cmd_replace,
     'byte-edit': cmd_byte_edit, 'verify': cmd_verify}[a.cmd](a)


if __name__ == '__main__':
    main()
