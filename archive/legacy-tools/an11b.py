# -*- coding: utf-8 -*-
import io, struct, statistics as st

P = r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\bfa0b7ff-ef7c-49d3-aaa9-b35963df7580\11.txt'
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

def seg_stat(name, s):
    uq = [x[3] for x in s]
    pe = [x[2] for x in s]
    v = [x[0] for x in s]
    pl = [x[1] for x in s]
    tv = [x[4] for x in s]
    clip = sum(1 for x in s if abs(x[3]) >= 3999)
    print('--- %s : %d frames (%.2f s), plan=%.0f ---' % (name, len(s), len(s) * 0.01, st.mean(pl)))
    print('   Uq      mean=%7.0f  std=%6.0f  min=%7.0f  max=%7.0f  peak/mean=%.2f' % (
        st.mean(uq), st.pstdev(uq), min(uq), max(uq), max(uq) / max(1e-6, st.mean(uq))))
    print('   enc_vel mean=%7.0f  std=%6.0f' % (st.mean(v), st.pstdev(v)))
    print('   pos_err mean=%7.1f  std=%6.1f  min=%7.1f  max=%7.1f' % (st.mean(pe), st.pstdev(pe), min(pe), max(pe)))
    print('   target  mean=%7.0f  std=%6.0f      plan  mean=%7.0f std=%6.0f' % (st.mean(tv), st.pstdev(tv), st.mean(pl), st.pstdev(pl)))
    print('   clip frames=%d (%.1f%%)' % (clip, 100.0 * clip / len(s)))
    print('   Uq above 3800: %.1f%%   above 3500: %.1f%%' % (
        100.0 * sum(1 for x in uq if x > 3800) / len(s),
        100.0 * sum(1 for x in uq if x > 3500) / len(s)))

segs = []
cur = [fr[0]]
for f in fr[1:]:
    if abs(f[1] - cur[-1][1]) > 200:
        segs.append(cur)
        cur = [f]
    else:
        cur.append(f)
segs.append(cur)

want = []
for s in segs:
    if len(s) < 100:
        continue
    pm = st.mean([x[1] for x in s])
    ps = st.pstdev([x[1] for x in s])
    if ps < 100:
        want.append((pm, s))
for pm, s in want:
    seg_stat('plan=%.0f' % pm, s)

print()
print('== steady Uq vs speed ==')
print('  plan_units   deg/s   Uq_mean   pe/v')
for pm, s in want:
    if abs(pm) < 10:
        continue
    print('  %11.0f %8.1f %9.0f %9.4f' % (pm, pm / 100.0, st.mean([x[3] for x in s]),
                                          st.mean([x[2] for x in s]) / pm))

print()
print('== time series at plan=25107, first 40 frames ==')
for pm, s in want:
    if abs(pm - 25107) < 60:
        for k in range(0, min(40, len(s))):
            x = s[k]
            print('   t=%5.2fs plan=%6.0f vel=%6.0f pe=%6.0f target=%6.0f Uq=%7.0f' % (
                k * 0.01, x[1], x[0], x[2], x[4], x[3]))
        break
