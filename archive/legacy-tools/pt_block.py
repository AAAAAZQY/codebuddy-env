_VOFA_TAIL = b"\x00\x00\x80\x7f"
_VOFA_MAP = "y=0,r=1,u=3"
_VOFA_USED = [False]


def _maybe_vofa(raw):
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
    return bytes(out)


def _vofa_to_csv(raw, dt, chan_map):
    """Convert vofa JustFloat frames (N float + 00 00 80 7F) into CSV text.

    chan_map: "y=0,r=1,u=3" style. u is optional; without u the tool runs
    closed-loop identification, with u it runs model identification.
    """
    import struct

    data = _vofa_bytes(raw)
    if not data:
        return ""

    n = 5
    step = n * 4 + 4
    frames = []
    i = 0
    while i + step <= len(data):
        chunk = data[i:i + step]
        if chunk[n * 4:] != _VOFA_TAIL:
            i += 1
            continue
        frames.append(struct.unpack("<%df" % n, chunk[:n * 4]))
        i += step
    if len(frames) < 8:
        return ""

    pick = {"y": 0, "r": 1, "u": None}
    for part in str(chan_map).split(","):
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        key = key.strip().lower()
        if key not in pick:
            continue
        try:
            pick[key] = int(val)
        except ValueError:
            pass

    if pick["u"] is not None:
        head = "time,u,y"
    elif pick["r"] is not None:
        head = "time,r,y"
    else:
        return ""

    lines = [head]
    for idx, fr in enumerate(frames):
        t = idx * dt
        if pick["u"] is not None:
            lines.append("%.6f,%.6f,%.6f" % (t, fr[pick["u"]], fr[pick["y"]]))
        else:
            lines.append("%.6f,%.6f,%.6f" % (t, fr[pick["r"]], fr[pick["y"]]))
    return "\n".join(lines) + "\n"


