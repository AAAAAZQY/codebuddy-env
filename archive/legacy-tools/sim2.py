# -*- coding: utf-8 -*-
"""sim2.py - same loop model but with encoder quantisation, stiction and a hard
plan_velocity reset (what the firmware does when plan_distance hits 0)."""
import io, struct, statistics as st, sys, math

PATH = sys.argv[1] if len(sys.argv) > 1 else \
    r'C:\Users\myages2026\AppData\Local\Temp\codebuddy-dropped-files\a1ac2e9f-1fd9-455f-88f9-bede973e2aca\11.txt'
TAIL = b'\x00\x00\x80\x7f'

J = 0.45          # Uq per (deg/s^2)
F_K = 2831.0      # kinetic friction, Uq
F_S = 2000.0      # break-away, Uq
KPV, KIV, IMAX, UMAX = 0.35, 0.01, 270000.0, 4000.0
DT = 1e-4
POS_DIV = 10
ACC = 36.0
VMAX = 25000.0
J_U = J / 100.0   # Uq per (unit/s^2), unit = 0.01 deg/s


def run(mode, kp_pos, hard_stop=False, quant=True):
    v = 0.0
    pos = 0.0          # exact position (units)
    pos_q = 0.0        # quantised position seen by the loop
    tpos = 0.0
    integ = 0.0
    ff = 0.0
    plan_v = 0.0
    stage = 0
    stages = int(round(VMAX / (ACC * 1000.0) * 1000))
    t_acc = VMAX / (ACC * 1000.0)
    t_hold = 2.0
    T = t_acc + t_hold + t_acc + 1.0
    n = int(T / DT)
    rec = []
    vprev = 0.0
    for k in range(n):
        t = k * DT
        if k % POS_DIV == 0:
            if t < t_acc:
                stage += 1
                plan_v = VMAX * stage / stages
            elif t < t_acc + t_hold:
                plan_v = VMAX
            elif t < t_acc + t_hold + t_acc:
                stage = max(0, stage - 1)
                plan_v = VMAX * stage / stages
            else:
                plan_v = 0.0
            if hard_stop and t >= t_acc + t_hold + t_acc * 0.55:
                plan_v = 0.0                      # firmware line 571 behaviour
            tpos += plan_v * 1e-3
            pe = tpos - pos_q
            tv = kp_pos * pe
            if mode == 'FF':
                tv += plan_v
            elif mode == 'FFR':                 # 20 ms ramp, as implemented in firmware
                ff += (plan_v - ff) * 0.05
                tv += ff
            tv = max(-VMAX * 1.2, min(VMAX * 1.2, tv))
        # velocity measurement (quantised: 1 count per 0.1 ms => 1000 units)
        vm = (pos_q - vprev) / DT if quant else v
        vprev = pos_q
        e = tv - vm
        integ += e
        integ = max(-IMAX, min(IMAX, integ))
        u = KPV * e + KIV * integ
        u = max(-UMAX, min(UMAX, u))
        # friction + stiction
        if abs(v) < 1.0 and abs(u) < F_S:
            a = 0.0
        else:
            fr = F_K if v > 0 else (-F_K if v < 0 else 0.0)
            a = (u - fr) / J_U
        v += a * DT
        pos += v * DT
        if quant:
            pos_q = float(int(pos + 0.5))
        else:
            pos_q = pos
        if k % 10 == 0:
            rec.append((t, plan_v, v, tpos - pos, u, tv))
    return rec, t_acc


def show(tag, rec, t_acc):
    t_hold_end = t_acc + 2.0
    hold = [r for r in rec if t_acc + 0.2 < r[0] < t_hold_end]
    end = [r for r in rec if r[0] > t_hold_end + t_acc + 0.6]
    vs = [r[2] for r in hold]
    print('%-22s steady: pe=%6.0f  vel=%6.0f  Uq mean=%5.0f std=%4.0f  peak=%5.0f  overshoot=%+5.1f%%' % (
        tag, st.mean([r[3] for r in hold]), st.mean(vs), st.mean([r[4] for r in hold]),
        st.pstdev([r[4] for r in hold]), max(r[4] for r in hold), 100.0 * (max(vs) - VMAX) / VMAX))
    print('%-22s end:    pe=%7.1f  |vel| max=%6.1f  reverse creep=%6.1f  Uq peak=%5.0f' % (
        '', st.mean([r[3] for r in end]), max(abs(r[2]) for r in end),
        min(r[2] for r in end), max(abs(r[4]) for r in end)))


for hs in (False, True):
    print()
    print('============== %s ==============' % ('HARD plan reset at decel (firmware behaviour)' if hs else 'normal ramped deceleration'))
    for mode, kp, nm in (('NONE', 7.0, 'A  no feedforward'), ('FF', 7.0, 'B  ideal FF'),
                         ('FFR', 7.0, 'D  FF + 20ms ramp (new fw)'), ('FFR', 3.0, 'E  FF ramp + kp_pos 3')):
        rec, ta = run(mode, kp, hard_stop=hs)
        show(nm, rec, ta)
