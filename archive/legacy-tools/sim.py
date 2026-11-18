# -*- coding: utf-8 -*-
"""sim.py - PTZ position+velocity loop simulator (permanent tool).

Fits J and friction from a measured dataset, then compares control variants:
  A  current      : target_velocity = 7 * pos_err
  B  velocity FF  : target_velocity = plan_velocity + 7 * pos_err
  C  FF + lower kp: target_velocity = plan_velocity + 3 * pos_err
"""
import io, struct, statistics as st, sys

PATH = sys.argv[1] if len(sys.argv) > 1 else \
    r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\a1ac2e9f-1fd9-455f-88f9-bede973e2aca\11.txt'

TAIL = b'\x00\x00\x80\x7f'


def load(p):
    raw = io.open(p, encoding='utf-8', errors='ignore').read()
    d = bytes(int(t, 16) for t in raw.split() if len(t) == 2)
    fr, i = [], 0
    while i + 28 <= len(d):
        if d[i + 24:i + 28] == TAIL:
            fr.append(struct.unpack('<6f', d[i:i + 24]))
            i += 28
        else:
            i += 1
    return fr


fr = load(PATH)

# ---- fit Uq = J*dv/dt + F*sign(v) ----
dv, uq, vv = [], [], []
for k in range(1, len(fr)):
    if abs(fr[k][1]) < 500:
        continue
    d = (fr[k][0] - fr[k - 1][0]) / 0.01          # units/s
    if abs(fr[k][3]) > 3990:
        continue
    dv.append(d / 100.0)                          # deg/s^2
    uq.append(fr[k][3])
    vv.append(fr[k][0])

n = len(dv)
md, mu = st.mean(dv), st.mean(uq)
cov = sum((a - md) * (b - mu) for a, b in zip(dv, uq)) / n
var = sum((a - md) ** 2 for a in dv) / n
J = cov / var
F = mu - J * md
print('fit from %d frames: J = %.2f Uq per (deg/s^2)   F = %.0f Uq   (dv/dt range %.0f..%.0f)' % (
    n, J, F, min(dv), max(dv)))

# ---- simulation ----
KPV, KIV, IMAX, UMAX = 0.35, 0.01, 270000.0, 4000.0
DT = 1e-4          # 10 kHz velocity loop
POS_DIV = 10       # position loop at 1 kHz
ACC = 36.0         # units per ms  (MOTOR_ACCELERATE_1MS)
VMAX = 25000.0     # units
T_ACC = VMAX / (ACC * 1000.0)
T_HOLD = 2.0
T_DEC = T_ACC
J_DEG = J / 100.0  # Uq per (unit/s^2)   (units = 0.01deg/s)


def run(mode, kp_pos, quant=0.0):
    v = 0.0
    acc = 0.0
    pos = 0.0
    tpos = 0.0
    integ = 0.0
    plan_v = 0.0
    plan_stage = 0
    plan_stage_total = int(round(T_ACC * 1000))
    t = 0.0
    n = int((T_ACC + T_HOLD + T_DEC + 1.0) / DT)
    rec = []
    for k in range(n):
        t = k * DT
        if k % POS_DIV == 0:
            # planner (1 kHz)
            if t < T_ACC:
                plan_stage += 1
                plan_v = VMAX * plan_stage / plan_stage_total
            elif t < T_ACC + T_HOLD:
                plan_v = VMAX
            elif t < T_ACC + T_HOLD + T_DEC:
                plan_stage -= 1
                if plan_stage < 0:
                    plan_stage = 0
                plan_v = VMAX * plan_stage / plan_stage_total
            else:
                plan_v = 0.0
            tpos += plan_v * 1e-3
            # position loop (1 kHz)
            pe = tpos - pos
            tv = kp_pos * pe
            if mode == 'FF':
                tv += plan_v
            if tv > VMAX * 1.2:
                tv = VMAX * 1.2
            if tv < -VMAX * 1.2:
                tv = -VMAX * 1.2
        # velocity loop (10 kHz)
        e = tv - v
        integ += e
        if integ > IMAX:
            integ = IMAX
        if integ < -IMAX:
            integ = -IMAX
        u = KPV * e + KIV * integ
        if u > UMAX:
            u = UMAX
        elif u < -UMAX:
            u = -UMAX
        net = u - (F if v > 1 else (-F if v < -1 else F * v))
        v += net / J_DEG * DT
        pos += v * DT
        if k % 10 == 0:
            rec.append((t, plan_v, v, tpos - pos, u, tv))
    return rec


def summarise(tag, rec):
    hold = [r for r in rec if T_ACC + 0.15 < r[0] < T_ACC + T_HOLD]
    settle = [r for r in rec if r[0] > T_ACC + T_HOLD + T_DEC + 0.5]
    ramp = [r for r in rec if 0.05 < r[0] < T_ACC]
    vs = [r[2] for r in hold]
    print('%-14s steady: pe=%6.1f  vel=%6.0f  Uq=%5.0f   overshoot=%+5.1f%%' % (
        tag, st.mean([r[3] for r in hold]), st.mean(vs), st.mean([r[4] for r in hold]),
        100.0 * (max(vs) - VMAX) / VMAX))
    print('%-14s ramp:  max|target-plan|=%5.0f  (plan-vel) avg=%+5.0f' % (
        '', max(abs(r[5] - r[1]) for r in ramp), st.mean([r[1] - r[2] for r in ramp])))
    tau = [r[3] for r in settle]
    print('%-14s end:   pe=%7.1f  vel=%6.1f  oscillation(|pe| max)=%.0f' % (
        '', st.mean(tau), st.mean([r[2] for r in settle]), max(abs(x) for x in tau)))


print()
print('--- variant A: current (target = 7*pe, no feedforward) ---')
summarise('A', run('NONE', 7.0))
print()
print('--- variant B: velocity feedforward (target = plan + 7*pe) ---')
summarise('B', run('FF', 7.0))
print()
print('--- variant C: feedforward + kp_pos 3 ---')
summarise('C', run('FF', 3.0))
