# -*- coding: utf-8 -*-
import io, struct, statistics as st, sys

P = sys.argv[1]
raw = io.open(P, encoding='utf-8', errors='ignore').read()
d = bytes(int(t, 16) for t in raw.split() if len(t) == 2)
fr = []
i = 0
while i + 28 <= len(d):
    if d[i + 24:i + 28] == b'\x00\x00\x80\x7f':
        fr.append(struct.unpack('<6f', d[i:i + 24]))
        i += 28
    else:
        i += 1

print('FILE %s' % P.split('\\')[-2][:8])
print('frames=%d  dur=%.2fs @10ms' % (len(fr), len(fr) * 0.01))
for k, nm in enumerate(['enc_vel', 'plan_vel', 'pos_err', 'Uq', 'target_v', 'gyro']):
    v = [f[k] for f in fr]
    print('  %-9s mean=%9.1f std=%8.1f min=%9.1f max=%9.1f' % (nm, st.mean(v), st.pstdev(v), min(v), max(v)))

clip = [k for k, f in enumerate(fr) if abs(f[3]) >= 3999]
print('clip total: %d / %d = %.1f%%' % (len(clip), len(fr), 100.0 * len(clip) / max(1, len(fr))))

# constant-plan windows
print()
print('== constant-plan windows (plan std < 50, len>=100) ==')
segs = []
cur = [fr[0]]
for f in fr[1:]:
    if abs(f[1] - cur[-1][1]) > 200:
        segs.append(cur)
        cur = [f]
    else:
        cur.append(f)
segs.append(cur)
for s in segs:
    if len(s) < 100:
        continue
    pm = st.mean([x[1] for x in s])
    ps = st.pstdev([x[1] for x in s])
    if ps >= 50:
        continue
    uq = [x[3] for x in s]
    vv = [x[0] for x in s]
    pe = [x[2] for x in s]
    c = sum(1 for x in s if abs(x[3]) >= 3999)
    su = sorted(uq)
    print(' plan=%7.0f n=%4d(%.2fs)  Uq mean=%5.0f std=%4.0f min=%5.0f max=%5.0f p5=%5.0f p95=%5.0f  clip=%3d(%.1f%%)  vel=%6.0f+-%.0f  err=%+.1f  pe=%5.0f' % (
        pm, len(s), len(s) * 0.01, st.mean(uq), st.pstdev(uq), min(uq), max(uq),
        su[int(0.05 * len(su))], su[int(0.95 * len(su))], c, 100.0 * c / len(s),
        st.mean(vv), st.pstdev(vv), pm - st.mean(vv), st.mean(pe)))
    m = st.mean(uq)
    zc = [k for k in range(1, len(uq)) if (uq[k - 1] - m) < 0 <= (uq[k] - m)]
    if len(zc) > 2:
        gaps = [zc[k + 1] - zc[k] for k in range(len(zc) - 1)]
        mu, mv = st.mean(uq), st.mean(vv)
        cov = sum((a - mu) * (b - mv) for a, b in zip(uq, vv)) / len(uq)
        print('        period=%.0f ms  corr(Uq,vel)=%.2f' % (st.median(gaps) * 10, cov / (st.pstdev(uq) * st.pstdev(vv) + 1e-9)))
