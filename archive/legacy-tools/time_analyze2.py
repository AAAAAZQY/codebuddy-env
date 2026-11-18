# -*- coding: gbk -*-
"""用能辨识成功的阶跃数据测耗时, 并测点数的影响。"""
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


def load(path):
    rows = io.open(path, encoding='utf-8').read().splitlines()[1:]
    t, u, y = [], [], []
    for ln in rows:
        p = ln.split(',')
        t.append(float(p[0]))
        u.append(float(p[1]))
        y.append(float(p[2]))
    return t, u, y


def run(tag, dat, opt, rob, limit=120.0):
    t, u, y = dat
    box = {}

    def work():
        t0 = time.time()
        try:
            info, an = m.analyze(t, u, y, mode='balanced',
                                 do_optimize=opt, do_robust=rob,
                                 dt_ctrl=0.0001)
            box['r'] = 'kind=%s pts=%d' % (an.get('kind'), len(t))
        except Exception as e:                      # noqa: BLE001
            box['r'] = 'ERR %s' % str(e)[:60]
        box['s'] = time.time() - t0

    th = threading.Thread(target=work, daemon=True)
    th.start()
    th.join(limit)
    if th.is_alive():
        print('%-30s > %.0f s  (abandoned)' % (tag, limit))
    else:
        print('%-30s %7.2f s   %s' % (tag, box.get('s', -1), box.get('r', '?')))


d = load(r'D:\bProject\pid_tuner\sample_data.csv')
print('sample_data: %d 点, %.1f s' % (len(d[0]), d[0][-1] - d[0][0]))
run('sample  fast (no opt)', d, False, False)
run('sample  full (opt+robust)', d, True, True)

# 放大 4 倍(重复拼接)模拟长数据
t, u, y = d
k = 4
T, U, Y = [], [], []
for i in range(k):
    off = i * (t[-1] - t[0] + (t[1] - t[0]))
    T += [v + off for v in t]
    U += u
    Y += y
print('')
print('放大后: %d 点, %.1f s' % (len(T), T[-1] - T[0]))
run('x4     fast (no opt)', (T, U, Y), False, False)
run('x4     full (opt+robust)', (T, U, Y), True, True)
