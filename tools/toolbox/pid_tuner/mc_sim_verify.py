#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCU 软件在环仿真 —— 离线提前验证脚本
=========================================================================
用途:
    在没有硬件的情况下, 用 Python 精确复现 application/pid_sim.c 的算法,
    生成"与串口输出一模一样"的 CSV 文本, 再用 pid_tuner 去辨识,
    确认这条链路是通的:

        虚拟对象 + PID  -->  CSV -->  整定工具  能反推出正确的 K/T/tau

    跑通之后, 再把固件烧进板子采真实数据, 结果应当是一致的。

重要:
    下面这些常量必须和 application/inc/pid_sim.h 里的宏保持一致。
    改了宏就同步改这里, 否则两边对不上。

用法:
    python mc_sim_verify.py
    (会在同目录生成 mc_sim_export.csv, 可直接喂给 pid_tuner.py)
"""

import math
import os

import pid_tuner as pt

# ---------------- 与 pid_sim.h 保持一致的参数 ----------------
PLANT_K = 2.5          # PID_SIM_PLANT_K
PLANT_T = 0.8          # PID_SIM_PLANT_T
PLANT_TAU = 0.15       # PID_SIM_PLANT_TAU
KP, KI, KD = 1.5, 3.0, 0.05     # PID_SIM_KP / KI / KD (有明显超调但不饱和)
PERIOD_MS = 20         # PID_SIM_PERIOD_MS
STEP_MS = 1000         # PID_SIM_STEP_TIME_MS
SP_TOGGLE_MS = 1000    # PID_SIM_SP_TOGGLE_MS (目标值变化间隔: 每 1 秒变一次)
SP_RAMP_MS = 30000     # PID_SIM_SP_RAMP_MS (爬完一个量程的耗时 = 斜率, 不封顶)
SP_WIGGLE_PCT = 30     # PID_SIM_SP_WIGGLE_PCT (摆动幅度 %)
RUN_MS = 30000         # PID_SIM_RUN_TIME_MS (单轮最长时长)
MIN_TIME_MS = 3000     # PID_SIM_MIN_TIME_MS
STEADY_MS = 400        # PID_SIM_STEADY_MS
STEADY_BAND = 0.02     # PID_SIM_STEADY_BAND
# PID_SIM_EARLY_END: 固件默认已改成 OFF —— ±2% 的稳态带会让 y 一到 0.98
# 就判"达标"提前结束并 reset, 既掩盖稳态误差又砍掉最后那段趋近曲线。
EARLY_END = False      # PID_SIM_EARLY_END
SP_LOW, SP_HIGH = 0.0, 1.0       # PID_SIM_SP_LOW / SP_HIGH
U_MAX, U_MIN = 10.0, -10.0
# 积分限幅(PID_SIM_INTEGRAL_MAX)。None = 不限幅, 与旧版行为一致。
INTEGRAL_MAX = None       # PID_SIM_U_MAX / U_MIN
DELAY_MAX = 128        # PID_SIM_DELAY_MAX
STREAM_PREFIX = "pid"  # PID_SIM_STREAM_PREFIX (FireWater/VOFA+ 的通道组名前缀)


def run_mcu_like_sim(ramp_ms=None, wiggle_pct=None):
    """逐拍复现 pid_sim.c 的 pid_sim_task()。

    返回 (rows, end_ms); rows 为 (t, r, u, y) 列表。
    同样复现了"跑满上限 / 达标提前结束"两种收工条件。

    ramp_ms / wiggle_pct: 目标值形状。默认用固件的"斜坡 + 摆动";
               传 ramp_ms=0 且 wiggle_pct=0 即可得到"只跳一次"的经典单阶跃数据
               —— 场景 2(没有 u)必须用它, 见那边的说明。
    """
    if ramp_ms is None:
        ramp_ms = SP_RAMP_MS
    if wiggle_pct is None:
        wiggle_pct = SP_WIGGLE_PCT
    dt = PERIOD_MS / 1000.0
    dly_len = int(PLANT_TAU * 1000.0 / PERIOD_MS + 0.5)

    buf = [0.0] * DELAY_MAX
    idx = 0
    y = PLANT_K * SP_LOW
    integ = 0.0
    e_prev = 0.0

    rows = []
    elapsed = 0
    steady_ms = 0
    band = STEADY_BAND * abs(SP_HIGH - SP_LOW)

    while elapsed < RUN_MS:
        # 1. 目标值: 斜坡 + 摆动(局部一会增一会降, 整体一路往上爬)
        #    与固件 pid_sim_task() 里的算法逐字对应
        if elapsed < STEP_MS:
            sp = SP_LOW
        else:
            span = SP_HIGH - SP_LOW
            wig = wiggle_pct / 100.0 * span
            rm = elapsed - STEP_MS
            # 不封顶: 基线一路往上爬(RAMP_MS 只决定斜率)
            frac = 1.0 if ramp_ms == 0 else rm / ramp_ms
            base = SP_LOW + (span - wig) * frac
            n_tog = elapsed // SP_TOGGLE_MS
            sp = base + wig if (n_tog % 2 == 1) else base

        # 2. PID (并联式)
        e = sp - y
        integ += KI * e * dt
        if INTEGRAL_MAX is not None:
            integ = max(-INTEGRAL_MAX, min(INTEGRAL_MAX, integ))
        deriv = (e - e_prev) / dt
        u = KP * e + integ + KD * deriv

        # 限幅 + 抗积分饱和
        if u > U_MAX:
            u = U_MAX
            integ -= KI * e * dt
        elif u < U_MIN:
            u = U_MIN
            integ -= KI * e * dt
        e_prev = e

        # 3. 虚拟对象: 一阶惯性 + 纯滞后
        buf[idx] = u
        idx_read = (idx + DELAY_MAX - dly_len) % DELAY_MAX
        u_d = buf[idx_read]
        idx = (idx + 1) % DELAY_MAX
        y += (dt / PLANT_T) * (PLANT_K * u_d - y)

        rows.append((elapsed, sp, u, y))

        # 4. 计时与收工判断(与固件顺序一致)
        elapsed += PERIOD_MS
        if EARLY_END and elapsed > STEP_MS and abs(sp - y) <= band:
            steady_ms += PERIOD_MS
        else:
            steady_ms = 0
        if elapsed >= RUN_MS or (EARLY_END and elapsed >= MIN_TIME_MS
                                 and steady_ms >= STEADY_MS):
            break

    return rows, elapsed


def rows_to_csv_text(rows):
    """生成与 pid_sim.c 串口输出等价的文本(含注释行与表头)。"""
    out = [
        "",
        "# ===== PID software-in-loop test =====",
        "# plant  : K=%.4f  T=%.4f  tau=%.4f" % (PLANT_K, PLANT_T, PLANT_TAU),
        "# pid    : Kp=%.4f  Ki=%.4f  Kd=%.4f" % (KP, KI, KD),
        "# period : %d ms    run: %d ms    step at: %d ms"
        % (PERIOD_MS, RUN_MS, STEP_MS),
        "# round  : 1",
        "# dt_s   : %.4f" % (PERIOD_MS / 1000.0),
        "%s:r,u,y" % STREAM_PREFIX,
    ]
    for (t, sp, u, y) in rows:
        # FireWater/VOFA+ 风格: "<any>:ch0,ch1,ch2\n"
        # 不带时间列: VOFA+ 波形才干净(时间会被它当成一条曲线画成锯齿)
        out.append("%s:%.4f,%.4f,%.4f" % (STREAM_PREFIX, sp, u, y))

    # 轮结束摘要 —— 与固件新增的打印保持一致
    last = rows[-1]
    err_pct = abs(last[1] - last[3]) / max(abs(SP_HIGH - SP_LOW), 1e-9) * 100.0
    out.append("# ===== round 1 end (%d ms) =====" % (len(rows) * PERIOD_MS))
    out.append("# result : y=%.4f  err=%.4f%%  u=%.4f" % (last[3], err_pct,
                                                          last[2]))
    return "\n".join(out) + "\n"


def strip_r_column(text):
    """把 "pid:r,u,y" 改写成 "pid:u,y"

    用来模拟"只采到控制量和实际值, 没有目标值"的情况。
    """
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith(STREAM_PREFIX + ":"):
            body = s[len(STREAM_PREFIX) + 1:].strip()
            parts = [p.strip() for p in body.split(",")]
            if len(parts) == 3:
                try:
                    [float(p) for p in parts]
                except ValueError:
                    out.append("%s:u,y" % STREAM_PREFIX)      # 表头行
                    continue
                out.append("%s:%s,%s" % (STREAM_PREFIX, parts[1], parts[2]))
                continue
        out.append(ln)
    return "\n".join(out)


def _check(name, info, an, strict=True):
    """打印一次辨识结果与真值的对比, 返回是否达标。

    strict=False 用于"没有 u"的场景: 那种情况只能靠闭环辨识,
    存在参数耦合, 精度天然差一截, 所以阈值放宽。
    """
    src = an.get("source")
    if not (an.get("kind") == "model"
            and src in ("generic", "closed_identify", "direct")):
        print("  [%s] 没能走模型整定路线, 实际: %s / %s"
              % (name, an.get("kind"), src))
        return False
    route = {
        "generic": "通用拟合(直接用实测 u 当对象输入)",
        "closed_identify": "闭环辨识(由已知 PID 反推对象)",
        "direct": "开环阶跃辨识",
    }.get(src, src)

    ek = abs(info["K"] - PLANT_K) / PLANT_K * 100
    et = abs(info["T"] - PLANT_T) / PLANT_T * 100
    el = abs(info["tau"] - PLANT_TAU) / PLANT_TAU * 100
    print("  [%s] 路线: %s" % (name, route))
    print("        反推对象: K=%.4f(%.1f%%)  T=%.4f(%.1f%%)  tau=%.4f(%.1f%%)"
          % (info["K"], ek, info["T"], et, info["tau"], el))
    print("        拟合 RMSE: %.5f" % info["rmse"])
    bp = an["best"]["pid"]
    print("        推荐参数: Kp=%.4f  Ki=%.4f  Kd=%.4f   (当前 %.2f / %.2f / %.3f)"
          % (bp["Kp"], bp["Ki"], bp["Kd"], KP, KI, KD))
    if strict:
        return ek < 10.0 and et < 15.0 and el < 40.0
    return ek < 60.0 and et < 60.0 and el < 60.0


def main():
    rows, end_ms = run_mcu_like_sim()
    text = rows_to_csv_text(rows)

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "mc_sim_export.csv")
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(text)

    print("=" * 76)
    print("  MCU 软件在环仿真 —— 离线验证")
    print("=" * 76)
    print("  模拟拍数   : %d  (实际 %d ms / 上限 %d ms, 周期 %d ms)"
          % (len(rows), end_ms, RUN_MS, PERIOD_MS))
    print("  生成文件   : %s" % path)
    _upeak = max(abs(r[2]) for r in rows)
    print("  u 峰值     : %.3f  (限幅 %.1f) -> %s"
          % (_upeak, U_MAX, "已饱和(数据会失真!)" if _upeak >= U_MAX * 0.999
             else "未饱和"))
    print("  y 终值     : %.4f  (目标 %.1f)" % (rows[-1][3], SP_HIGH))
    print("  对象真值   : K=%.4f  T=%.4f  tau=%.4f" % (PLANT_K, PLANT_T, PLANT_TAU))
    # 每 1 秒取一个目标值(= 一个摆动段), 覆盖整轮
    # —— 直观看出"全程一直在爬 + 局部上下摆动"
    _seg = [r for (_t, r, _u, _y) in rows][::int(SP_TOGGLE_MS / PERIOD_MS)]
    print("  目标值形状 : %s"
          % " ".join("%.2f" % v for v in _seg))
    print("               (每秒一个点: 高低相间 = 局部上下; 整体逐段抬高 = 一直往上爬)")
    print("=" * 76)

    t, u, y, r = pt.parse_data(text)
    print("  数据解析   : %d 点, u=%s, r=%s"
          % (len(t), "有" if u is not None else "无",
             "有" if r is not None else "无"))
    for _ln in text.splitlines():
        if _ln.startswith(STREAM_PREFIX + ":"):
            print("  协议示例   : %s" % _ln)
            print("     剥前缀后: %s" % pt._strip_stream_prefix(_ln))
            break
    print("  数据性质   : %s"
          % ("闭环运行记录(控制量在动态调节)" if pt.is_closed_loop_dataset(u)
             else "开环阶跃响应"))
    print()

    print(">>> 场景 1: 完整数据 (r, u, y) + 已知当前 PID")
    info1, an1 = pt.analyze(t, u, y, r=r, current_pid={"Kp": KP, "Ki": KI, "Kd": KD})
    ok1 = _check("场景1", info1, an1)
    print()

    print(">>> 场景 2: 只有 (r, y), 没有 u, 但知道当前 PID")
    # ★ 这条路线**必须**用单次阶跃数据: 上位机的闭环辨识在数学上假设
    #   "目标值只跳一次"(用 sp0 -> sp 的阶跃参数化去仿真 y), 方波会让它
    #   拟合不上而退回经验规则 —— 这是路线本身的适用边界, 不是 bug。
    #   所以这里另生成一份单阶跃数据(等价于把固件 SP_TOGGLE_MS 填成一个
    #   大于 RUN_TIME_MS 的大数)来验证这条路线。
    print("    注: 闭环辨识假设「目标值只跳一次」, 故本场景改用单次阶跃数据;")
    print("        固件的方波数据必须带上 u(走场景 1/3/4 的通用拟合)。")
    _rows_st, _ = run_mcu_like_sim(ramp_ms=0, wiggle_pct=0)
    t2, _u2, y2, r2 = pt.parse_data(rows_to_csv_text(_rows_st))
    info2, an2 = pt.analyze(t2, None, y2, r=r2,
                            current_pid={"Kp": KP, "Ki": KI, "Kd": KD})
    ok2 = _check("场景2", info2, an2, strict=False)
    print()

    print(">>> 场景 3: (r, u, y) 都有, 但没记录当前 PID —— 看能否自动反推")
    est = pt.estimate_pid_from_data(t, r, y, u)
    if est is None:
        print("  自动反推失败")
        ok3 = False
    else:
        print("  反推 PID : Kp=%.4f  Ki=%.4f  Kd=%.4f   (拟合残差 %.2f%%)"
              % (est["Kp"], est["Ki"], est["Kd"], est["fit_error"] * 100))
        print("  真实 PID : Kp=%.4f  Ki=%.4f  Kd=%.4f" % (KP, KI, KD))
        info3, an3 = pt.analyze(t, u, y, r=r)      # 不给 current_pid
        ok3 = _check("场景3", info3, an3)
    print()

    print(">>> 场景 4: 只有 (u, y), 连目标值 r 都没有")
    text_uy = strip_r_column(text)
    t4, u4, y4, r4 = pt.parse_data(text_uy)
    print("    解析结果: u=%s   r=%s   y有(必然)"
          % ("有" if u4 is not None else "无",
             "有" if r4 is not None else "无"))
    info4, an4 = pt.analyze(t4, u4, y4)          # 不给 r
    ok4 = _check("场景4", info4, an4)
    print()

    print("=" * 76)
    print("  汇总: 场景1 %s | 场景2 %s | 场景3 %s | 场景4 %s"
          % ("通过" if ok1 else "未通过",
             "通过" if ok2 else "未通过",
             "通过" if ok3 else "未通过",
             "通过" if ok4 else "未通过"))
    print("  说明: 本脚本只验证算法一致性。真机数据会带量化与串口抖动,")
    print("        辨识误差略大, 但量级一致。")
    print("        生成的文件可直接用: python pid_tuner.py --csv mc_sim_export.csv")
    print("=" * 76)
    return 0 if (ok1 and ok2 and ok3 and ok4) else 1


if __name__ == "__main__":
    raise SystemExit(main())
