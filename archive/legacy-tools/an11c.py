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

segs = []
cur = [fr[0]]
for f in fr[1:]:
    if abs(f[1] - cur[-1][1]) > 200:
        segs.append(cur)
        cur = [f]
    else:
        cur.append(f)
segs.append(cur)

print('== settle after stop: plan=0 segments ==')
for s in segs:
    if len(s) < 100:
        continue
    if abs(st.mean([x[1] for x in s])) > 10:
        continue
    print('--- %d frames ---' % len(s))
    for k in range(0, len(s), max(1, len(s) // 25)):
        x = s[k]
        print('   t=%5.2fs  pe=%7.1f  target=%7.0f  vel=%7.0f  Uq=%7.0f' % (
            k * 0.01, x[2], x[4], x[0], x[3]))
    x = s[-1]
    print('   last: pe=%.1f target=%.0f vel=%.0f Uq=%.0f' % (x[2], x[4], x[0], x[3]))

print()
print('== amplitude of Uq swing in steady 25107 segment ==')
for s in segs:
    if len(s) < 300:
        continue
    if abs(st.mean([x[1] for x in s]) - 25107) > 60:
        continue
    uq = [x[3] for x in s[100:]]
    v = [x[0] for x in s[100:]]
    print('   Uq: p5=%.0f p50=%.0f p95=%.0f  max=%.0f' % (
        sorted(uq)[int(0.05 * len(uq))], sorted(uq)[int(0.5 * len(uq))], sorted(uq)[int(0.95 * len(uq))], max(uq)))
    print('   vel: p5=%.0f p50=%.0f p95=%.0f' % (
        sorted(v)[int(0.05 * len(v))], sorted(v)[int(0.5 * len(v))], sorted(v)[int(0.95 * len(v))]))
    # zero crossing period estimate on (Uq - mean)
    m = st.mean(uq)
    zc = []
    for k in range(1, len(uq)):
        if (uq[k - 1] - m) < 0 <= (uq[k] - m):
            zc.append(k)
    if len(zc) > 2:
        gaps = [zc[k + 1] - zc[k] for k in range(len(zc) - 1)]
        print('   Uq mean-crossing period = %.1f ms (n=%d)' % (st.median(gaps) * 10.0, len(gaps)))
    break
