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

def fold(tag, P, plan_val, period_deg):
    fr = load(P)
    # take the constant-plan window
    segs = []
    cur = [fr[0]]
    for f in fr[1:]:
        if abs(f[1] - cur[-1][1]) > 200:
            segs.append(cur); cur = [f]
        else:
            cur.append(f)
    segs.append(cur)
    s = None
    for cand in segs:
        if len(cand) > 200 and st.pstdev([x[1] for x in cand]) < 50 and abs(st.mean([x[1] for x in cand]) - plan_val) < 200:
            s = cand
    if s is None:
        print('%s: window not found' % tag); return
    # integrate velocity -> position (units 0.01 deg)
    pos = 0.0
    pts = []
    for x in s:
        pos += x[0] * 0.01          # 0.01deg/s * 10ms
        pts.append((pos, x[3]))
    per = period_deg * 100.0        # in 0.01deg units
    NB = 40
    bins = [[] for _ in range(NB)]
    for p, u in pts:
        b = int((p % per) / per * NB) % NB
        bins[b].append(u)
    means = [st.mean(b) if b else 0 for b in bins]
    uall = [u for _, u in pts]
    gm = st.mean(uall)
    # variance explained by the folded waveform
    var_tot = st.pstdev(uall) ** 2
    resid = []
    for p, u in pts:
        b = int((p % per) / per * NB) % NB
        resid.append(u - means[b])
    var_res = st.pstdev(resid) ** 2
    print('%s  plan=%.0f  n=%d  period=%.0f deg' % (tag, plan_val, len(s), period_deg))
    print('   Uq mean=%6.0f  sigma=%5.0f   folded-waveform sigma=%5.0f   residual sigma=%5.0f'
          % (gm, var_tot ** 0.5, max(means) - min(means), var_res ** 0.5))
    print('   variance explained by folded waveform = %.1f%%' % (100.0 * (1 - var_res / var_tot)))
    print('   folded peak-to-peak = %.0f Uq' % (max(means) - min(means)))
    line = ''
    for k in range(0, NB, 2):
        line += '%5.0f' % means[k]
    print('   folded (40 bins, every 2): %s' % line)

A = r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\5a41c2eb-f6c5-4954-8cb9-ef1949af0fb9\11.txt'
B = r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\df6d1461-943a-4b2a-b212-3de349d463d7\11.txt'
for per in (20.0, 18.0, 22.5, 36.0):
    print('====== period %.1f deg ======' % per)
    fold('OLD 200deg/s kp0.70', A, 20000, per)
    fold('NEW 250deg/s kp lower', B, 25107, per)
    print()
