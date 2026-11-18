# -*- coding: gbk -*-
"""给 vofa_report.py 增加 --profile（全程剖面，适合加减速/定位数据）。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'D:\Codebuddy\tools\vofa_report.py'
t = io.open(P, encoding='gbk').read()

OLD = '''def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]'''

NEW = '''def profile(frames, dt=0.01, tag='', segs=12):
    """全程剖面：不筛稳态，按时间分段看速度/目标/Uq 的走势。"""
    n = len(frames)
    if n < segs * 3:
        print('帧数太少')
        return
    print('=' * 78)
    print('  %s   全程剖面 (%d 帧, %.1f 秒)' % (tag or '数据', n, n * dt))
    print('=' * 78)
    print('  %-7s %9s %9s %9s %9s %9s'
          % ('t(s)', '实际速度', '目标速度', '跟踪差', 'Uq', '位置'))
    seg = max(1, n // segs)
    for k in range(segs):
        a, b = k * seg, min(n, (k + 1) * seg)
        blk = frames[a:b]
        v = [f[CH_Y] for f in blk]
        tg = [f[CH_TGT] for f in blk]
        uq = [f[CH_UQ] for f in blk]
        po = [f[CH_POS] for f in blk]
        print('  %-7.1f %9.0f %9.0f %9.0f %9.0f %9.0f'
              % (a * dt, statistics.mean(v), statistics.mean(tg),
                 statistics.mean(tg) - statistics.mean(v),
                 statistics.mean(uq), statistics.mean(po)))
    vs = [f[CH_Y] for f in frames]
    print('')
    print('  全程: 速度 %.0f ~ %.0f   目标 %.0f ~ %.0f'
          % (min(vs), max(vs), min(f[CH_TGT] for f in frames),
             max(f[CH_TGT] for f in frames)))
    print('')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    do_profile = '--profile' in sys.argv'''

assert OLD in t
t = t.replace(OLD, NEW, 1)

OLD2 = '''        r = analyse(fr, tag=tag)
        if r:
            results.append((tag, r))'''
NEW2 = '''        if do_profile:
            profile(fr, tag=tag)
            continue
        r = analyse(fr, tag=tag)
        if r:
            results.append((tag, r))'''
assert OLD2 in t
t = t.replace(OLD2, NEW2, 1)

io.open(P, 'w', encoding='gbk').write(t)
print('vofa_report.py 已增加 --profile')
