# -*- coding: utf-8 -*-
import io, struct, statistics as st

P = r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\5a41c2eb-f6c5-4954-8cb9-ef1949af0fb9\11.txt'
raw = io.open(P, encoding='utf-8', errors='ignore').read()
toks = [t for t in raw.split() if len(t) == 2]
d = bytes(int(t, 16) for t in toks)

fr = []
i = 0
while i + 28 <= len(d):
    if d[i + 24:i + 28] == b'\x00\x00\x80\x7f':
        fr.append(struct.unpack('<6f', d[i:i + 24]))
        i += 28
    else:
        i += 1

print('frames=%d  dur=%.2fs @10ms' % (len(fr), len(fr) * 0.01))
names = ['ch0 enc_vel', 'ch1 plan_vel', 'ch2 pos_err', 'ch3 Uq', 'ch4 target_v', 'ch5 gyro']
for k in range(6):
    v = [f[k] for f in fr]
    print('%-13s mean=%9.1f std=%8.1f min=%9.1f max=%9.1f' % (names[k], st.mean(v), st.pstdev(v), min(v), max(v)))

print()
print('check f4 == 7*f2 : %d / %d' % (sum(1 for f in fr if abs(f[4] - 7 * f[2]) < 10), len(fr)))
clip = [k for k, f in enumerate(fr) if abs(f[3]) >= 3999]
print('clip frames(|Uq|>=3999): %d / %d = %.1f%%' % (len(clip), len(fr), 100.0 * len(clip) / max(1, len(fr))))
if clip:
    print('first clip idx=%d  last clip idx=%d' % (clip[0], clip[-1]))

print()
print('== segments by plan velocity (segment break: |dplan|>200) ==')
segs = []
cur = [fr[0]]
for f in fr[1:]:
    if abs(f[1] - cur[-1][1]) > 200:
        segs.append(cur)
        cur = [f]
    else:
        cur.append(f)
segs.append(cur)

print(' idx frames  sec  plan_mean plan_std  Uq_mean  Uq_std  Uq_max  clip  pe_mean  pe_max  vel_mean  target_mean')
rows = []
for idx, s in enumerate(segs):
    if len(s) < 20:
        continue
    pl = [x[1] for x in s]
    uq = [x[3] for x in s]
    pe = [x[2] for x in s]
    vv = [x[0] for x in s]
    tv = [x[4] for x in s]
    c = sum(1 for x in s if abs(x[3]) >= 3999)
    print(' %3d %6d %5.2f %9.0f %8.1f %8.0f %7.0f %7.0f %5d %8.0f %7.0f %9.0f %9.0f' % (
        idx, len(s), len(s) * 0.01, st.mean(pl), st.pstdev(pl), st.mean(uq), st.pstdev(uq),
        max(abs(x) for x in uq), c, st.mean(pe), max(abs(x) for x in pe), st.mean(vv), st.mean(tv)))
    rows.append((idx, st.mean(pl), len(s), c, st.mean(uq), max(abs(x) for x in uq), st.mean(pe), max(abs(x) for x in pe), st.mean(vv), st.pstdev(pl)))

print()
print('== steady segments (plan std < 50) ==')
print(' plan   frames  Uq_mean  Uq_max  clip  pe_mean  pe_max  vel_mean  vel_err(plan-vel)')
for r in rows:
    if r[9] < 50:
        print(' %6.0f %7d %8.0f %7.0f %5d %8.0f %7.0f %9.0f %10.0f' % (
            r[1], r[2], r[4], r[5], r[3], r[6], r[7], r[8], r[1] - r[8]))

print()
print('== where Uq is NOT clipped but plan is high ==')
hi = [k for k, f in enumerate(fr) if f[1] > 15000 and abs(f[3]) < 3999]
print('count=%d' % len(hi))
for k in hi[:15]:
    x = fr[k]
    print('  i=%5d plan=%7.0f vel=%7.0f pe=%7.0f Uq=%7.0f target=%7.0f' % (k, x[1], x[0], x[2], x[3], x[4]))

print()
print('== sample: steady 20000 region, every 20th frame ==')
for k in range(0, len(fr), 20):
    x = fr[k]
    print('  i=%5d t=%6.2fs plan=%7.0f vel=%7.0f pe=%7.0f Uq=%7.0f target=%7.0f' % (
        k, k * 0.01, x[1], x[0], x[2], x[3], x[4]))
