# -*- coding: utf-8 -*-
"""vac.py - VOFA hex frame analyzer (reusable).

usage: python vac.py <file1.txt> [file2.txt ...] [--fold DEG]

frame = 6 x float32 (LE) + tail 00 00 80 7F  (28 bytes)
ch0 enc_vel(0.01deg/s) ch1 plan_vel ch2 pos_err ch3 Uq ch4 target_vel ch5 gyro*100
"""
import io, struct, statistics as st, sys, math

TAIL = b'\x00\x00\x80\x7f'


def load(path):
    raw = io.open(path, encoding='utf-8', errors='ignore').read()
    toks = [t for t in raw.split() if len(t) == 2]
    d = bytes(int(t, 16) for t in toks)
    fr, i = [], 0
    while i + 28 <= len(d):
        if d[i + 24:i + 28] == TAIL:                       # 6-channel frame
            fr.append(struct.unpack('<6f', d[i:i + 24]))
            i += 28
        elif d[i + 28:i + 32] == TAIL:                     # 7-channel frame (ch6 = obs)
            fr.append(struct.unpack('<7f', d[i:i + 28]))
            i += 32
        else:
            i += 1
    return fr


def windows(fr, minlen=100):
    segs, cur = [], [fr[0]]
    for f in fr[1:]:
        if abs(f[1] - cur[-1][1]) > 200:
            segs.append(cur)
            cur = [f]
        else:
            cur.append(f)
    segs.append(cur)
    out = []
    for s in segs:
        if len(s) >= minlen and st.pstdev([x[1] for x in s]) < 50:
            out.append(s)
    return out


def dft_phase(x, dt, f):
    n = len(x)
    m = st.mean(x)
    y = [v - m for v in x]
    w = 2.0 * math.pi * f * dt
    re = sum(y[k] * math.cos(w * k) for k in range(n))
    im = sum(y[k] * math.sin(w * k) for k in range(n))
    return math.atan2(im, re), 2.0 * math.sqrt(re * re + im * im) / n


def periodogram(x, dt, fmin=2.0, fmax=60.0, step=0.25):
    n = len(x)
    m = st.mean(x)
    y = [v - m for v in x]
    best = []
    f = fmin
    while f <= fmax:
        w = 2.0 * math.pi * f * dt
        re = sum(y[k] * math.cos(w * k) for k in range(n))
        im = sum(y[k] * math.sin(w * k) for k in range(n))
        amp = 2.0 * math.sqrt(re * re + im * im) / n
        best.append((amp, f))
        f += step
    best.sort(reverse=True)
    return best[:3]


def fold_by_position(s, period_deg, nb=40):
    pos, pts = 0.0, []
    for x in s:
        pos += x[0] * 0.01
        pts.append((pos, x[3]))
    per = period_deg * 100.0
    bins = [[] for _ in range(nb)]
    for p, u in pts:
        bins[int((p % per) / per * nb) % nb].append(u)
    means = [st.mean(b) if b else float('nan') for b in bins]
    uall = [u for _, u in pts]
    var_tot = st.pstdev(uall) ** 2
    resid = []
    for p, u in pts:
        b = int((p % per) / per * nb) % nb
        resid.append(u - means[b])
    var_res = st.pstdev(resid) ** 2
    return means, max(means) - min(means), 100.0 * (1 - var_res / var_tot)


def detect_ch2(fr):
    """ch2 is pos_err (slope vs enc_vel ~ 1/7) or the alpha-beta shadow (~1.0)."""
    mv = [(f[0], f[2]) for f in fr if abs(f[0]) > 5000]
    if len(mv) < 50:
        return True, 'pos_err', 0.0
    xs = [a for a, b in mv]
    ys = [b for a, b in mv]
    mx, my = st.mean(xs), st.mean(ys)
    var = sum((a - mx) ** 2 for a in xs) / len(xs)
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / len(xs)
    slope = cov / var if var > 0 else 0.0
    return slope < 0.5, ('pos_err' if slope < 0.5 else 'obs_shdw'), slope


def report(path, fold_deg=None):
    fr = load(path)
    tag = path.split('\\')[-2][:8]
    is_pe, ch2nm, slope = detect_ch2(fr)
    print('=' * 74)
    print('FILE %s   frames=%d   dur=%.2fs @10ms   [ch2=%s, slope=%.2f]' % (
        tag, len(fr), len(fr) * 0.01, ch2nm, slope))
    for k, nm in enumerate(['enc_vel', 'plan_vel', ch2nm, 'Uq', 'target_v', 'gyro']):
        v = [f[k] for f in fr]
        print('  %-9s mean=%9.1f std=%8.1f min=%9.1f max=%9.1f' % (nm, st.mean(v), st.pstdev(v), min(v), max(v)))
    tot = sum(1 for f in fr if abs(f[3]) >= 3999)
    print('  clip total %d/%d = %.1f%%' % (tot, len(fr), 100.0 * tot / len(fr)))

    for s in windows(fr):
        w_pe, w_nm, w_slope = detect_ch2(s)
        uq = [x[3] for x in s]
        vv = [x[0] for x in s]
        tv = [x[4] for x in s]
        pe = [x[2] for x in s]
        e = [a - b for a, b in zip(tv, vv)]
        c = sum(1 for x in uq if abs(x) >= 3999)
        pm = st.mean([x[1] for x in s])
        su = sorted(uq)
        print('-' * 74)
        print('  WINDOW plan=%7.0f  n=%4d (%.2fs)  [ch2=%s]' % (
            pm, len(s), len(s) * 0.01, w_nm))
        print('    Uq  mean=%5.0f std=%4.0f min=%5.0f max=%5.0f p5=%5.0f p95=%5.0f  clip=%3d (%.1f%%)' % (
            st.mean(uq), st.pstdev(uq), min(uq), max(uq),
            su[int(0.05 * len(su))], su[int(0.95 * len(su))], c, 100.0 * c / len(s)))
        if w_pe:
            print('    vel mean=%6.0f std=%4.0f   plan-vel=%+.1f   pe mean=%5.0f std=%4.0f' % (
                st.mean(vv), st.pstdev(vv), pm - st.mean(vv), st.mean(pe), st.pstdev(pe)))
        else:
            mo = st.mean(pe)
            cvo = sum((a - st.mean(vv)) * (b - mo) for a, b in zip(vv, pe)) / len(vv)
            print('    vel mean=%6.0f std=%4.0f   plan-vel=%+.1f   OBS sigma=%.0f corr(obs,enc)=%.2f' % (
                st.mean(vv), st.pstdev(vv), pm - st.mean(vv), st.pstdev(pe),
                cvo / (st.pstdev(vv) * st.pstdev(pe) + 1e-9)))
        if abs(pm) > 1000:
            print('    ripple spectrum (top3): ' + '  '.join(
                '%.2fHz amp=%.0f' % (f, a) for a, f in periodogram(uq, 0.01)))
            gy = [x[5] for x in s]
            mu_, mg = st.mean(vv), st.mean(gy)
            cov = sum((a - mu_) * (b - mg) for a, b in zip(vv, gy)) / len(vv)
            cc = cov / (st.pstdev(vv) * st.pstdev(gy) + 1e-9)
            print('    vel noise split: enc sigma=%.0f  gyro sigma=%.0f  corr=%.2f' % (
                st.pstdev(vv), st.pstdev(gy), cc))
            if len(s[0]) == 7:
                ov = [x[6] for x in s]
                mo = st.mean(ov)
                covo = sum((a - mu_) * (b - mo) for a, b in zip(vv, ov)) / len(vv)
                print('    OBS(ch6): sigma=%.0f  corr(obs,enc)=%.2f  mean-diff=%.1f' % (
                    st.pstdev(ov), covo / (st.pstdev(vv) * st.pstdev(ov) + 1e-9),
                    st.mean(ov) - mu_))
            print('      gyro spectrum (top3): ' + '  '.join(
                '%.2fHz amp=%.0f' % (f, a) for a, f in periodogram(gy, 0.01)))
            print('      enc  spectrum (top3): ' + '  '.join(
                '%.2fHz amp=%.0f' % (f, a) for a, f in periodogram(vv, 0.01)))
            print('      tgt  spectrum (top3): ' + '  '.join(
                '%.2fHz amp=%.0f' % (f, a) for a, f in periodogram(tv, 0.01)))
            print('      pe   spectrum (top3): ' + '  '.join(
                '%.2fHz amp=%.0f' % (f, a) for a, f in periodogram(pe, 0.01)))
            f0 = periodogram(uq, 0.01)[0][1]
            pu, au = dft_phase(uq, 0.01, f0)
            pg, ag = dft_phase(gy, 0.01, f0)
            pv, av = dft_phase(vv, 0.01, f0)
            du = (pu - pg) * 180.0 / math.pi
            du = (du + 180) % 360 - 180
            dv = (pu - pv) * 180.0 / math.pi
            dv = (dv + 180) % 360 - 180
            print('      phase at %.2fHz: Uq-leads-gyro=%+.0f deg  Uq-leads-enc=%+.0f deg' % (f0, du, dv))
            print('      (0 deg = pumping, -180 = damping, +90 = inertia only)')
            # slow / fast split (centered moving average, 510 ms)
            W = 51
            slow = []
            for k in range(len(uq)):
                a2 = max(0, k - W // 2)
                b2 = min(len(uq), k + W // 2 + 1)
                slow.append(st.mean(uq[a2:b2]))
            fast = [u - s2 for u, s2 in zip(uq, slow)]
            print('    slow component (0.5s avg): mean=%5.0f std=%4.0f  min=%5.0f max=%5.0f' % (
                st.mean(slow), st.pstdev(slow), min(slow), max(slow)))
            print('    fast component (ripple):   std=%4.0f  peak=%5.0f' % (
                st.pstdev(fast), max(abs(f2) for f2 in fast)))
            clip_slow = sum(1 for u, s2 in zip(uq, slow) if abs(u) >= 3999 and s2 > 3400)
            print('    clip frames where slow>3400: %d / %d clip frames' % (clip_slow, c))
            if st.mean(vv) > 1000:
                deg = st.mean(vv) * 0.01
                top = periodogram(uq, 0.01)[0][1]
                print('    dominant f=%.2f Hz -> %.1f deg per cycle (speed %.1f deg/s)' % (
                    top, deg / top, deg))
        if fold_deg:
            means, pp, expl = fold_by_position(s, fold_deg)
            print('    fold@%.1fdeg: waveform peak-to-peak=%.0f Uq, explains %.1f%% of variance' % (
                fold_deg, pp, expl))
            half = (max(means) + min(means)) / 2.0
            print('    fold waveform (40 bins over %.0f deg, Uq, DC removed):' % fold_deg)
            print('      ' + ' '.join('%+5.0f' % (m - half) for m in means))

    # post-stop behaviour: everything after the last frame that still has a plan
    last = 0
    for k, f in enumerate(fr):
        if abs(f[1]) > 50:
            last = k
    tail = fr[last + 1:]
    if len(tail) > 20:
        vv = [x[0] for x in tail]
        uq = [x[3] for x in tail]
        pe = [x[2] for x in tail]
        travel = sum(v * 0.01 for v in vv)          # 0.01deg units -> deg
        rev = sum(v * 0.01 for v in vv if v < 0)
        print('-' * 74)
        print('  POST-STOP after i=%d : n=%d (%.2fs)' % (last, len(tail), len(tail) * 0.01))
        print('    vel  mean=%6.0f  min=%6.0f  max=%6.0f   reverse travel=%.2f deg (total %.2f deg)' % (
            st.mean(vv), min(vv), max(vv), rev, travel))
        print('    Uq   mean=%6.0f  min=%6.0f  max=%6.0f' % (st.mean(uq), min(uq), max(uq)))
        print('    %s mean=%6.1f  min=%6.0f  max=%6.0f' % (ch2nm, st.mean(pe), min(pe), max(pe)))


def ramp_diag(fr, tag):
    # ramp frames: plan changes by >50 per frame
    nm2 = detect_ch2(fr)[1]
    ramp = [k for k in range(1, len(fr)) if abs(fr[k][1] - fr[k - 1][1]) > 50]
    print('-' * 74)
    print('  RAMP DIAG (frames with dplan>50): %d' % len(ramp))
    if ramp:
        a, b = ramp[0], ramp[-1]
        s = fr[max(0, a - 5):b + 6]
        print('    from i=%d to i=%d  (%.2fs)' % (a, b, (b - a) * 0.01))
        plan = [x[1] for x in s]
        vel = [x[0] for x in s]
        tv = [x[4] for x in s]
        pe = [x[2] for x in s]
        uq = [x[3] for x in s]
        print('    plan  %6.0f -> %6.0f   (rate %.0f units/frame = %.0f deg/s^2)' % (
            plan[0], plan[-1], (plan[-1] - plan[0]) / max(1, len(plan) - 1),
            (plan[-1] - plan[0]) / max(1, len(plan) - 1) * 0.01 * 100))
        print('    peak Uq during ramp = %.0f   clip frames = %d / %d' % (
            max(uq), sum(1 for x in uq if abs(x) >= 3999), len(s)))
        dif = [a2 - b2 for a2, b2 in zip(plan, tv)]
        print('    (plan - target): mean=%+6.0f  min=%+6.0f  max=%+6.0f  -> target lags plan by %.1f deg/s avg'
              % (st.mean(dif), min(dif), max(dif), st.mean(dif) * 0.01))
        dif2 = [a2 - b2 for a2, b2 in zip(plan, vel)]
        print('    (plan - vel):    mean=%+6.0f  min=%+6.0f  max=%+6.0f' % (st.mean(dif2), min(dif2), max(dif2)))
        print('    target sigma during ramp = %.0f   %s: %.0f -> %.0f' % (
            st.pstdev(tv), nm2, pe[0], pe[-1]))
    # overshoot after ramp: plan constant at its max
    mx = max(x[1] for x in fr)
    if mx < 100:            # no motion in this file, nothing to compare against
        print('    no motion segment (plan max=%.0f) - ramp/overshoot skipped' % mx)
        return
    tail = [x for x in fr if x[1] > mx - 50]
    if tail:
        vv = [x[0] for x in tail]
        print('    after ramp (plan=%.0f const, n=%d): vel mean=%.0f max=%.0f  overshoot=%+.1f%%  sigma=%.0f' % (
            mx, len(tail), st.mean(vv), max(vv), 100.0 * (max(vv) - mx) / mx, st.pstdev(vv)))
        pe = [x[2] for x in tail]
        if nm2 == 'pos_err':
            print('    %s there: mean=%.0f max=%.0f std=%.0f  (plan/7=%.0f)' % (
                nm2, st.mean(pe), max(pe), st.pstdev(pe), mx / 7.0))
        else:
            print('    %s there: mean=%.0f max=%.0f std=%.0f' % (
                nm2, st.mean(pe), max(pe), st.pstdev(pe)))


def trace(fr, step):
    print('-' * 74)
    print('  TRACE (every %d frames)  i  t  plan  vel  pe  Uq  target  (target-plan)' % step)
    for k in range(0, len(fr), step):
        x = fr[k]
        print('   %5d %6.2f %7.0f %7.0f %6.0f %6.0f %7.0f %+7.0f' % (
            k, k * 0.01, x[1], x[0], x[2], x[3], x[4], x[4] - x[1]))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    fold, tr = None, None
    for a in sys.argv[1:]:
        if a.startswith('--fold'):
            fold = float(a.split('=')[1])
        if a.startswith('--trace'):
            tr = int(a.split('=')[1])
    for p in args:
        report(p, fold)
        ramp_diag(load(p), p.split('\\')[-2][:8])
        if tr:
            trace(load(p), tr)
