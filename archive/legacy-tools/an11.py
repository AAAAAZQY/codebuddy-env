# -*- coding: utf-8 -*-
import io, struct, statistics as st

P = r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\bfa0b7ff-ef7c-49d3-aaa9-b35963df7580\11.txt'
raw = io.open(P, encoding='utf-8', errors='ignore').read()
toks = [t for t in raw.split() if len(t) == 2]
try:
    d = bytes(int(t, 16) for t in toks)
except ValueError:
    d = b''

fr = []
i = 0
while i + 28 <= len(d):
    if d[i + 24:i + 28] == b'\x00\x00\x80\x7f':
        fr.append(struct.unpack('<6f', d[i:i + 24]))
        i += 28
    else:
        i += 1

print('frames=%d  duration=%.2f s (10ms/frame)' % (len(fr), len(fr) * 0.01))
names = ['ch0 enc_vel', 'ch1 plan_vel', 'ch2 pos_err', 'ch3 Uq', 'ch4 target_v', 'ch5 gyro']
for k in range(6):
    v = [f[k] for f in fr]
    print('%-13s mean=%10.1f std=%9.1f min=%10.1f max=%10.1f' % (names[k], st.mean(v), st.pstdev(v), min(v), max(v)))

print()
print('check f4 == 7*f2 :', sum(1 for f in fr if abs(f[4] - 7 * f[2]) < 8), '/', len(fr))

segs = []
cur = [fr[0]]
for f in fr[1:]:
    if abs(f[1] - cur[-1][1]) > 200:
        segs.append(cur)
        cur = [f]
    else:
        cur.append(f)
segs.append(cur)

print()
print('== segments (len>=50 frames) ==')
print('  #   frames  sec   plan_mean  plan_std   Uq_mean  Uq_max   pe_mean  pe_max  clip  vel_mean')
rows = []
for idx, s in enumerate(segs):
    if len(s) < 50:
        continue
    pl = [x[1] for x in s]
    uq = [x[3] for x in s]
    pe = [x[2] for x in s]
    v = [x[0] for x in s]
    clip = sum(1 for x in s if abs(x[3]) >= 3999)
    print(' %2d %6d %5.2f %10.0f %9.0f %9.0f %7.0f %8.0f %7.0f %5d %9.0f' % (
        idx, len(s), len(s) * 0.01, st.mean(pl), st.pstdev(pl), st.mean(uq),
        max(abs(x) for x in uq), st.mean(pe), max(abs(x) for x in pe), clip, st.mean(v)))
    rows.append((st.mean(pl), st.mean(uq), max(abs(x) for x in uq), st.mean(pe), max(abs(x) for x in pe), clip, len(s), st.pstdev(pl)))

print()
print('== steady segments (plan std < 100) ==')
print('  plan  Uq_mean  Uq_max  pe_mean  pe_max  clip  frames')
ste = [r for r in rows if r[7] < 100 and abs(r[0]) > 1]
for r in sorted(ste, key=lambda x: abs(x[0])):
    print(' %6.0f %8.0f %7.0f %8.1f %7.0f %5d %7d' % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))

print()
still = [f for f in fr if abs(f[1]) < 1]
print('== standstill (plan=0): frames=%d ==' % len(still))
if still:
    print('  Uq     mean=%.0f std=%.0f max=%.0f' % (st.mean([x[3] for x in still]), st.pstdev([x[3] for x in still]), max(abs(x[3]) for x in still)))
    print('  pos_err mean=%.1f max=%.0f' % (st.mean([x[2] for x in still]), max(abs(x[2]) for x in still)))
    print('  target mean=%.1f' % st.mean([x[4] for x in still]))
    print('  enc_vel mean=%.1f std=%.0f' % (st.mean([x[0] for x in still]), st.pstdev([x[0] for x in still])))
    print('  gyro   mean=%.1f std=%.1f' % (st.mean([x[5] for x in still]), st.pstdev([x[5] for x in still])))

print()
tot = sum(1 for f in fr if abs(f[3]) >= 3999)
print('clip frames (|Uq|>=3999): %d / %d = %.1f%%' % (tot, len(fr), 100.0 * tot / max(1, len(fr))))
