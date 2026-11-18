import io, re

src = io.open('pid_tuner.py', encoding='utf-8').read()
print("总行数:", src.count("\n") + 1)
print()
print("=== 死代码 ===")
dead = [n for n in re.findall(r'^def (\w+)', src, re.M)
        if len(re.findall(r'\b%s\b' % re.escape(n), src)) <= 1]
print("  " + (", ".join(dead) if dead else "无"))
print()
print("=== 关键函数引用数 ===")
for n in ("_solve_linear", "_lin_interp", "_logspace", "_crossing_time",
          "_smooth", "_fopdt_predict", "metrics", "diagnose",
          "score_response", "tune_imc", "tune_imc_pid", "tune_zn",
          "tune_cohen_coon", "tune_zn_closed", "recommended_sample_time",
          "apply_guardrails", "_mk_param", "_from_parallel", "tune_all",
          "_extract_dt_hint", "time_axis_note", "make_sample",
          "make_closed_sample", "refine_fopdt"):
    print("  %-26s %d" % (n, len(re.findall(r'\b%s\b' % re.escape(n), src))))
