# -*- coding: cp936 -*-
"""第 7 步：在 vofa 识别处加诊断日志，定位粘贴失败的环节"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'


def L(s):
    return s.encode('utf-8').decode('latin-1')


src = io.open(TARGET, encoding='latin-1', newline='').read()

old = L('''    # 粘贴进来的 vofa hex 文本也直接识别（GUI「粘贴数据」走这条路）
    try:
        _probe = text.encode("latin-1", "ignore")
        if _maybe_vofa(_probe):
            _csv = _vofa_to_csv(_probe, dt, _VOFA_MAP)
            if _csv:
                _VOFA_USED[0] = True
                text = _csv
    except Exception:       # noqa: BLE001
        pass''')

new = L('''    # 粘贴进来的 vofa hex 文本也直接识别（GUI「粘贴数据」走这条路）
    try:
        _probe = text.encode("latin-1", "ignore")
        _hit = _maybe_vofa(_probe)
        _csv = _vofa_to_csv(_probe, dt, _VOFA_MAP) if _hit else ""
        try:
            with open(r"D:\\Codebuddy\\tmp\\vofa_diag.log", "a", encoding="utf-8") as _lf:
                _lf.write("textlen=%d hit=%s raw=%d csvlen=%d map=%r first=%r\\n"
                          % (len(text), _hit, len(_vofa_bytes(_probe)),
                             len(_csv), _VOFA_MAP, _probe[:60]))
        except Exception:   # noqa: BLE001
            pass
        if _csv:
            _VOFA_USED[0] = True
            text = _csv
    except Exception as _e:       # noqa: BLE001
        try:
            with open(r"D:\\Codebuddy\\tmp\\vofa_diag.log", "a", encoding="utf-8") as _lf:
                _lf.write("EXC %s: %s\\n" % (type(_e).__name__, _e))
        except Exception:   # noqa: BLE001
            pass''')

if src.count(old) != 1:
    print('anchor count =', src.count(old))
    sys.exit(1)

out = src.replace(old, new).encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('diag added, bytes =', len(out))
