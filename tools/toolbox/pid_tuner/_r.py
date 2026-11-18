import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pid_tuner as P

# 模拟"继电器反馈试验"：输出方波 u = ±MAX_OUT 驱动对象，记录 (u, y)
Kt, Tt, taut = 2.5, 0.8, 0.15
dt, MAXOUT, n = 0.02, 10.0, 1500

dly = int(round(taut / dt))
buf = [0.0] * (dly + 1)
y = 1.0                      # 从稳态附近起振
t_l, u_l, y_l = [], [], []
for i in range(n):
    # 继电器：y 高于目标给负、低于给正（带一点滞环）
    u = MAXOUT if y < 1.0 else -MAXOUT
    buf.append(u)
    u_d = buf.pop(0)
    y += dt / Tt * (Kt * u_d - y)
    t_l.append(i * dt)
    u_l.append(u)
    y_l.append(y)

print("方波试验: 点数=%d  u 取值=%s  y 范围 %.3f~%.3f"
      % (n, sorted(set(u_l)), min(y_l), max(y_l)))

print()
print("--- 工具怎么判这条数据 ---")
print("is_closed_loop_dataset(u) =", P.is_closed_loop_dataset(u_l))
info, an = P.analyze(t_l, u_l, y_l)
print("路线: kind=%s source=%s" % (an.get("kind"), an.get("source")))
print("反推对象: K=%.4f T=%.4f tau=%.4f   (真值 %.2f/%.2f/%.2f)"
      % (info["K"], info["T"], info["tau"], Kt, Tt, taut))
err = [abs(info["K"] - Kt) / Kt, abs(info["T"] - Tt) / Tt,
       abs(info["tau"] - taut) / max(taut, 1e-9)]
print("相对误差: K %.1f%%  T %.1f%%  tau %.1f%%"
      % tuple(100 * e for e in err))
print("拟合 RMSE=%.4f   方案数=%d  有曲线=%s"
      % (info["rmse"], len(an["rows"]),
         bool(an["rows"] and an["rows"][0].get("curve"))))
