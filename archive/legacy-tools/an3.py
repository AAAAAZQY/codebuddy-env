# -*- coding: utf-8 -*-
import io, struct, statistics as st, sys

def load(P):
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
    return fr

def window(fr, plan_val):
    segs = []
    cur = [fr[0]]
    for f in fr[1:]:
        if abs(f[1] - cur[-1][1]) > 200:
            segs.append(cur); cur = [f]
        else:
            cur.append(f)
    segs.append(cur)
    out = []
    for s in segs:
        if len(s) < 100: continue
        pm = st.mean([x[1] for x in s]); ps = st.pstdev([x[1] for x in s])
        if ps < 50 and abs(pm - plan_val) < 200:
            out.append(s)
    return out

def analyse(tag, P, plan_val):
    fr = load(P)
    for s in window(fr, plan_val):
        uq = [x[3] for x in s]
        vv = [x[0] for x in s]
        tv = [x[4] for x in s]
        e = [a - b for a, b in zip(tv, vv)]
        # least squares kp from the oscillating part
        me, mu = st.mean(e), st.mean(uq)
        cov = sum((a - me) * (b - mu) for a, b in zip(e, uq)) / len(e)
        var = sum((a - me) ** 2 for a in e) / len(e)
        kp = cov / var if var > 0 else 0
        pterm = [kp * x for x in e]
        resid = [b - p for b, p in zip(uq, pterm)]   # integral contribution
        c = sum(1 for x in uq if abs(x) >= 3999)
        print('%s plan=%.0f n=%d(%.2fs)' % (tag, st.mean([x[1] for x in s]), len(s), len(s) * 0.01))
        print('   sigma Uq=%5.0f  sigma e=%5.0f  sigma vel=%5.0f' % (st.pstdev(uq), st.pstdev(e), st.pstdev(vv)))
        print('   kp estimated from data = %.3f   (P term sigma = %.0f)' % (kp, st.pstdev(pterm)))
        print('   integral-term: mean=%6.0f  sigma=%5.0f   (share of Uq ripple: %.0f%%)' % (
            st.mean(resid), st.pstdev(resid), 100.0 * st.pstdev(resid) ** 2 / (st.pstdev(uq) ** 2)))
        print('   clip=%d (%.1f%%)  Uq mean=%.0f  e mean=%.0f' % (c, 100.0 * c / len(s), mu, me))

A = r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\5a41c2eb-f6c5-4954-8cb9-ef1949af0fb9\11.txt'
B = r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\df6d1461-943a-4b2a-b212-3de349d463d7\11.txt'
analyse('OLD(200deg/s)', A, 20000)
print()
analyse('NEW(250deg/s)', B, 25107)
