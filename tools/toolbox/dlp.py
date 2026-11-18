#!/usr/bin/env python
# dlp.py - DLP helper (toolbox). Keep this file plaintext.
# Trusted images (python.exe / git.exe / rg.exe) read decrypted plaintext and
# write re-encrypted-at-rest. Untrusted (node / powershell / cmd) read ciphertext
# and any write leaves PLAINTEXT at rest (breaks encryption) - never write with them.
#
# usage:
#   python dlp.py status   <file> [<file>...]   # py-plaintext size + at-rest state
#   python dlp.py reencrypt <file> [<file>...]  # python rewrite -> re-encrypt at rest
#   python dlp.py scan     <root>                # list *.c/*.h plaintext-at-rest files
import sys, os, subprocess

EXE = r'D:\Codebuddy\CodeBuddy CN\CodeBuddy CN.exe'
NODE_CODE = "const fs=require('fs');const b=fs.readFileSync(process.argv[1]);process.stdout.write(b.slice(0,12).toString('latin1'))"


def node_head(path):
    env = dict(os.environ)
    env['ELECTRON_RUN_AS_NODE'] = '1'
    r = subprocess.run([EXE, '-e', NODE_CODE, path], capture_output=True, env=env)
    return r.stdout.decode('latin1')


def at_rest(path):
    try:
        return 'cipher' if node_head(path).startswith('%TSD') else 'plain'
    except Exception:
        return '??'


def cmd_status(files):
    for p in files:
        try:
            py = open(p, 'rb').read()
            print('%-52s py=%6d  atrest=%s' % (os.path.basename(p), len(py), at_rest(p)))
        except Exception as e:
            print('%-52s ERROR %s' % (os.path.basename(p), e))


def cmd_reencrypt(files):
    for p in files:
        data = open(p, 'rb').read()
        open(p, 'wb').write(data)
        back = open(p, 'rb').read()
        print('%-52s reencrypted atrest=%s equal=%s' % (os.path.basename(p), at_rest(p), back == data))


def cmd_scan(root):
    n = 0
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f.lower().endswith(('.c', '.h')):
                p = os.path.join(dp, f)
                if at_rest(p) == 'plain':
                    print('PLAIN', os.path.relpath(p, root))
                    n += 1
    print('plaintext-at-rest files:', n)


def main():
    if len(sys.argv) < 3:
        print('usage: dlp.py status|reencrypt <files...> | scan <root>')
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'status':
        cmd_status(args)
    elif cmd == 'reencrypt':
        cmd_reencrypt(args)
    elif cmd == 'scan':
        cmd_scan(args[0])
    else:
        print('unknown cmd', cmd)


if __name__ == '__main__':
    main()
