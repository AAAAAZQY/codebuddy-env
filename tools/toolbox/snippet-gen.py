# -*- coding: utf-8 -*-
"""
snippet-gen.py -- 只为 bridge-edit.py 生成 UTF-8 的 old/new 临时片段，绝不写工程文件。

用法:
  python snippet-gen.py lines --file <path> --editor <json> --out-old <f> --out-new <f>
      [--encoding gbk|utf-8]
      editor JSON 为编辑列表，每项需 'at'(1起行号) 或 'match'(唯一子串)，
      以及 'set'(整行替换) / 'comment'(行首加 //) / 'uncomment'(去行首 //) 之一。

  python snippet-gen.py bitmap --file <path> --array <name>
      (--indices 2..41,0,5 | --modes 2,3,4,5)
      [--col-start N] [--col-end N] [--page-mask 0=0x0F,1=0xF8]
      [--width 30] [--height-pages 4] [--out-old <f> --out-new <f>]

输出:
  old/new 文件一律 LF 行尾 + UTF-8；打印摘要，再由 bridge-edit.py replace --dry 校验命中数。
  本工具只读源文件、只写两个临时片段文件；不碰工程、不调用桥。
"""
import argparse
import json
import re
import sys


def fail(msg):
    print('[FAIL] ' + msg)
    sys.exit(1)


def read_text(p, enc):
    try:
        with open(p, 'rb') as f:
            return f.read().decode(enc)
    except Exception as e:
        fail('cannot read %s: %s' % (p, e))


def write_snippet(p, text):
    t = text.replace('\r\n', '\n').replace('\r', '\n')
    try:
        with open(p, 'wb') as f:
            f.write(t.encode('utf-8'))
    except Exception as e:
        fail('cannot write %s: %s' % (p, e))


def split_lines(t):
    has_nl = t.endswith('\n')
    lines = t.replace('\r\n', '\n').split('\n')
    if has_nl:
        lines = lines[:-1]
    return lines, has_nl


# ---------------- lines ----------------

def cmd_lines(a):
    lines, has_nl = split_lines(read_text(a.file, a.encoding))
    try:
        edits = json.loads(read_text(a.editor, 'utf-8'))
    except Exception as e:
        fail('editor json parse failed: %s' % e)
    if not isinstance(edits, list) or not edits:
        fail('editor must be a non-empty JSON list')

    changes = {}
    for e in edits:
        if not isinstance(e, dict):
            fail('edit must be an object')
        if 'at' in e:
            i = int(e['at']) - 1
            if not (0 <= i < len(lines)):
                fail('line number out of range: %s' % e['at'])
        elif 'match' in e:
            hits = [k for k, l in enumerate(lines) if str(e['match']) in l]
            if len(hits) != 1:
                fail('match must hit exactly 1 line, got %d: %r' % (len(hits), e['match']))
            i = hits[0]
        else:
            fail('edit needs at or match')
        if i in changes:
            fail('duplicate edit on line %d' % (i + 1))
        if 'set' in e:
            changes[i] = str(e['set'])
        elif e.get('comment'):
            changes[i] = '//' + lines[i]
        elif e.get('uncomment'):
            changes[i] = lines[i][2:] if lines[i].startswith('//') else lines[i]
        else:
            fail('edit #%d needs set/comment/uncomment' % (i + 1))

    lo, hi = min(changes), max(changes)
    old = '\n'.join(lines[lo:hi + 1])
    new = '\n'.join(changes.get(i, lines[i]) for i in range(lo, hi + 1))
    write_snippet(a.out_old, old)
    write_snippet(a.out_new, new)
    print('[OK] lines entries=%d changed=%d range=%d..%d old=%d new=%d -> %s , %s'
          % (len(lines), len(changes), lo + 1, hi + 1, len(old), len(new), a.out_old, a.out_new))


# ---------------- bitmap ----------------

def mask_comments(s):
    out = list(s)
    i = 0
    while i < len(s):
        if s.startswith('//', i):
            j = s.find('\n', i)
            j = len(s) if j < 0 else j
            for k in range(i, j):
                out[k] = ' '
            i = j
        elif s.startswith('/*', i):
            j = s.find('*/', i + 2)
            j = len(s) if j < 0 else j + 2
            for k in range(i, j):
                if s[k] != '\n':
                    out[k] = ' '
            i = j
        else:
            i += 1
    return ''.join(out)


def parse_index_list(spec, n):
    out = set()
    for part in str(spec).split(','):
        part = part.strip()
        if not part:
            continue
        if '..' in part:
            p, q = part.split('..')
            out.update(range(int(p), int(q) + 1))
        else:
            out.add(int(part))
    bad = sorted(i for i in out if not (0 <= i < n))
    if bad:
        fail('indices out of range: %s' % bad[:8])
    return sorted(out)


def indices_from_modes(spec, n):
    out = set()
    for mode in [int(x) for x in str(spec).split(',')]:
        for signal in range(5):
            for net in range(2):
                idx = ((mode - 2) * 5 + signal) * 2 + net + 2
                if not (0 <= idx < n):
                    fail('mode %d -> index %d out of range' % (mode, idx))
                out.add(idx)
    return sorted(out)


def parse_page_masks(spec):
    out = {}
    for part in spec.split(','):
        k, v = part.split('=')
        out[int(k)] = int(v, 0)
    return out


def cmd_bitmap(a):
    text = read_text(a.file, a.encoding)
    pat = (r'(const\s+uint8_t\s+' + re.escape(a.array) +
           r'\s*\[\s*\]\s*\[\s*\d+\s*\]\s*=\s*\{)(.*?)(\n\};)')
    m = re.search(pat, text, re.S)
    if not m:
        fail('array not found: %s' % a.array)
    body = m.group(2)
    toks = list(re.finditer(r'0[xX][0-9a-fA-F]+|\d+', mask_comments(body)))
    per = a.width * a.height_pages
    if not toks or len(toks) % per:
        fail('token count %d not divisible by %d' % (len(toks), per))
    n = len(toks) // per

    if a.indices:
        idxs = parse_index_list(a.indices, n)
    elif a.modes:
        idxs = indices_from_modes(a.modes, n)
    else:
        fail('need --indices or --modes')
    masks = parse_page_masks(a.page_mask)
    if any(p < 0 or p >= a.height_pages for p in masks):
        fail('page-mask page out of range')

    targets = {}
    for idx in idxs:
        for page, mask in masks.items():
            for col in range(a.col_start, a.col_end + 1):
                if not (0 <= col < a.width):
                    fail('column out of range: %d' % col)
                targets[idx * per + page * a.width + col] = mask

    out, last, changed = [], 0, 0
    for k, t in enumerate(toks):
        out.append(body[last:t.start()])
        orig = t.group()
        val = int(orig, 0)
        if k in targets:
            nv = val & targets[k]
            if nv != val:
                changed += 1
            out.append('0x%02X' % nv)
        else:
            out.append(orig)
        last = t.end()
    out.append(body[last:])

    old_full = m.group(0)
    new_full = m.group(1) + ''.join(out) + m.group(3)
    write_snippet(a.out_old, old_full)
    write_snippet(a.out_new, new_full)
    print('[OK] bitmap entries=%d tokens=%d indices=%d bytes_changed=%d old=%d new=%d -> %s , %s'
          % (n, len(toks), len(idxs), changed, len(old_full), len(new_full), a.out_old, a.out_new))


def main():
    ap = argparse.ArgumentParser(description='generate old/new UTF-8 snippets for bridge-edit.py')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('lines')
    p.add_argument('--file', required=True)
    p.add_argument('--editor', required=True)
    p.add_argument('--encoding', default='gbk')
    p.add_argument('--out-old', required=True)
    p.add_argument('--out-new', required=True)
    p.set_defaults(func=cmd_lines)

    p = sub.add_parser('bitmap')
    p.add_argument('--file', required=True)
    p.add_argument('--array', required=True)
    p.add_argument('--indices')
    p.add_argument('--modes')
    p.add_argument('--col-start', type=int, default=4)
    p.add_argument('--col-end', type=int, default=16)
    p.add_argument('--page-mask', default='0=0x0F,1=0xF8')
    p.add_argument('--width', type=int, default=30)
    p.add_argument('--height-pages', type=int, default=4)
    p.add_argument('--encoding', default='gbk')
    p.add_argument('--out-old', required=True)
    p.add_argument('--out-new', required=True)
    p.set_defaults(func=cmd_bitmap)

    a = ap.parse_args()
    a.func(a)


if __name__ == '__main__':
    main()
