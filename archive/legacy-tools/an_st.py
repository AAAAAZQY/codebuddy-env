# -*- coding: utf-8 -*-
import io, struct, statistics as st

P = r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\5a41c2eb-f6c5-4954-8cb9-ef1949af0fb9\11.txt'
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

def stat(name, s, plan):
    uq = [x[3] for x in s]; vv = [x[0] for x in s]; pe = [x[2] for x in s]
    c = sum(1 for x in s if abs(x[3]) >= 3999)
    print('%s frames=%d (%.2fs) plan=%.0f' % (name, len(s), len(s) * 0.01, plan))
    print('   Uq  mean=%6.0f std=%6.0f min=%6.0f max=%6.0f  clip=%d (%.1f%%)' % (
        st.mean(uq), st.pstdev(uq), min(uq), max(uq), c, 100.0 * c / len(s)))
    print('   vel mean=%7.0f std=%6.0f min=%7.0f max=%7.0f  err=plan-vel %+.1f' % (
        st.mean(vv), st.pstdev(vv), min(vv), max(vv), plan - st.mean(vv)))
    print('   pe  mean=%7.0f std=%6.1f min=%7.0f max=%7.0f   (plan/7=%.0f)' % (
        st.mean(pe), st.pstdev(pe), min(pe), max(pe), plan / 7.0))
    print('   Uq p5=%6.0f p50=%6.0f p95=%6.0f  above3500=%.1f%% above3800=%.1f%%' % (
        sorted(uq)[int(0.05 * len(uq))], sorted(uq)[int(0.5 * len(uq))], sorted(uq)[int(0.95 * len(uq))],
        100.0 * sum(1 for x in uq if x > 3500) / len(s), 100.0 * sum(1 for x in uq if x > 3800) / len(s)))

# settled steady window
w = [f for k, f in enumerate(fr) if 200 <= k <= 700]
stat('ST-STEADY idx200-700', w, 20000)

# full constant plan window
w2 = [f for k, f in enumerate(fr) if k >= 140 and f[1] > 19900]
stat('CONST-PLAN idx>=140', w2, 20000)

print()
print('== clip distribution by time window (plan=20000 only) ==')
for a in range(140, 741, 50):
    s = [f for k, f in enumerate(fr) if a <= k < a + 50 and f[1] > 19900]
    if not s:
        continue
    c = sum(1 for x in s if abs(x[3]) >= 3999)
    print('  idx %3d-%3d  n=%2d  Uq_mean=%6.0f  Uq_std=%5.0f  clip=%2d  vel=%7.0f  pe=%6.0f' % (
        a, a + 49, len(s), st.mean([x[3] for x in s]), st.pstdev([x[3] for x in s]), c,
        st.mean([x[0] for x in s]), st.mean([x[2] for x in s])))

print()
print('== Uq vs vel correlation in settled window ==')
uq = [x[3] for x in w]; vv = [x[0] for x in w]
mu_u, mu_v = st.mean(uq), st.mean(vv)
cov = sum((a - mu_u) * (b - mu_v) for a, b in zip(uq, vv)) / len(uq)
print('  corr = %.3f' % (cov / (st.pstdev(uq) * st.pstdev(vv))))

print()
print('== slow oscillation: zero-crossings of (Uq - mean) ==')
m = st.mean(uq)
zc = [k for k in range(1, len(uq)) if (uq[k - 1] - m) < 0 <= (uq[k] - m)]
if len(zc) > 2:
    gaps = [zc[k + 1] - zc[k] for k in range(len(zc) - 1)]
    print('  crossings=%d  median period=%.0f ms' % (len(gaps), st.median(gaps) * 10))

print()
print('== breakdown of the 227 clip frames ==')
for k in range(60, 160, 10):
    x = fr[k]
    print('  i=%3d plan=%7.0f vel=%7.0f pe=%6.0f Uq=%7.0f' % (k, x[1], x[0], x[2], x[3]))
