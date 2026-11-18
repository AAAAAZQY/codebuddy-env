# -*- coding: utf-8 -*-
"""Make the edit-A anchor of patch_fw_units.py unique (file is GBK encoded)."""
import io

P = r'D:\Codebuddy\tools\patch_fw_units.py'

t = io.open(P, encoding='gbk').read()

old = "txt, r = patch(txt, nl, '''_INTEGRAL_MAX = None\n''', '''_INTEGRAL_MAX = None\n"
new = ("txt, r = patch(txt, nl, "
       "'''_INTEGRAL_MAX = None\n\n\ndef _vofa_tokens(raw, limit=None):\n''', "
       "'''_INTEGRAL_MAX = None\n")

n = t.count(old)
print('anchor occurrences:', n)
if n != 1:
    print('FAIL: expected exactly 1')
    raise SystemExit(1)

io.open(P, 'w', encoding='gbk').write(t.replace(old, new))
print('patched anchor OK')
