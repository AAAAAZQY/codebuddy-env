# -*- coding: gbk -*-
"""measure analyze() cost with/without the optimizer on a 1652-point record."""
import importlib.util
import io
import sys
import threading
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

spec = importlib.util.spec_from_file_location(
    'pid_tuner', r'D:\bProject\pid_tuner\pid_tuner.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

rows = io.open(r'D:\Codebuddy\tmp\fw_full.csv', encoding='utf-8').read().splitlines()[1:]
t, u, y = [], [], []
for ln in rows:
    p = ln.split(',')
    t.append(float(p[0]))
    u.append(float(p[1]))
    y.append(float(p[2]))
print('points = %d, span = %.1f s' % (len(t), t[-1] - t[0]))


def run(tag, opt, rob, limit=90.0):
    box = {}

    def work():
        t0 = time.time()
        try:
            info, an = m.analyze(t, u, y, mode='balanced',
                                 do_optimize=opt, do_robust=rob,
                                 dt_ctrl=0.0001)
            box['r'] = 'kind=%s' % an.get('kind')
        except Exception as e:                      # noqa: BLE001
            box['r'] = 'ERR %s' % e
        box['s'] = time.time() - t0

    th = threading.Thread(target=work, daemon=True)
    th.start()
    th.join(limit)
    if th.is_alive():
        print('%-22s > %.0f s  (still running, abandoned)' % (tag, limit))
    else:
        print('%-22s %6.2f s   %s' % (tag, box.get('s', -1), box.get('r', '?')))


run('fast (no opt/robust)', False, False, 90)
run('optimize only', True, False, 90)
run('full (opt+robust)', True, True, 90)
