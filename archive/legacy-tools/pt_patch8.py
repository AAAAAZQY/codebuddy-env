# -*- coding: cp936 -*-
"""第 8 步：识别 vofa 时跳过 # 注释行，容忍粘贴框里预填的示例文字"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'


def L(s):
    return s.encode('utf-8').decode('latin-1')


src = io.open(TARGET, encoding='latin-1', newline='').read()

old = '''def _maybe_vofa(raw):
    """Quick sniff: vofa JustFloat binary frames, or whitespace separated hex text."""
    if raw.find(_VOFA_TAIL) >= 0:
        return True
    head = raw[:400].decode("latin-1", "ignore").replace(",", " ").split()
    if len(head) < 24:
        return False
    for tok in head[:24]:
        if len(tok) != 2:
            return False
        try:
            int(tok, 16)
        except ValueError:
            return False
    return True


def _vofa_bytes(raw):
    """Normalise vofa payload (binary or hex text) into one byte string."""
    if raw.find(_VOFA_TAIL) >= 0:
        return raw
    txt = raw.decode("latin-1", "ignore").replace(",", " ")
    toks = [t for t in txt.split() if len(t) == 2]
    if len(toks) < 48:
        return b""
    out = bytearray()
    for tok in toks:
        try:
            out.append(int(tok, 16))
        except ValueError:
            return b""
    return bytes(out)'''

new = '''def _vofa_tokens(raw, limit=None):
    """抽出 hex 文本里的字节 token, 跳过 # 开头的注释行。

    粘贴框里预填的示例文字(如 "# time,u,y")会混在数据前面,
    不跳过的话第一个 token 不是 hex, 整段就被当成普通 CSV 了。
    """
    txt = raw.decode("latin-1", "ignore").replace(",", " ")
    toks = []
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for tok in line.split():
            if len(tok) == 2:
                toks.append(tok)
                if limit is not None and len(toks) >= limit:
                    return toks
    return toks


def _maybe_vofa(raw):
    """Quick sniff: vofa JustFloat binary frames, or whitespace separated hex text."""
    if raw.find(_VOFA_TAIL) >= 0:
        return True
    head = _vofa_tokens(raw[:800], limit=24)
    if len(head) < 24:
        return False
    for tok in head:
        try:
            int(tok, 16)
        except ValueError:
            return False
    return True


def _vofa_bytes(raw):
    """Normalise vofa payload (binary or hex text) into one byte string."""
    if raw.find(_VOFA_TAIL) >= 0:
        return raw
    toks = _vofa_tokens(raw)
    if len(toks) < 48:
        return b""
    out = bytearray()
    for tok in toks:
        try:
            out.append(int(tok, 16))
        except ValueError:
            return b""
    return bytes(out)'''

if src.count(old) != 1:
    print('anchor count =', src.count(old))
    sys.exit(1)

out = src.replace(old, L(new)).encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('patched, bytes =', len(out))
