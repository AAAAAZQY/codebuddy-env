# -*- coding: gbk -*-
"""去掉阻塞等待, 加快速模式开关。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'D:\bProject\pid_tuner\pid_tuner.py'

NEW = '''        import queue
        import threading
        # 不再拦截"上一轮还在跑": 每次点击都立即开新一轮, 旧结果回来时代号已变就丢弃。
        # 这样某一轮再慢, 用户也随时能改参数重算, 不会被锁住。
        state["data"] = (t, u, y, r)     # 先存数据, 频域辨识随时可用
        state["gen"] = state.get("gen", 0) + 1
        _gen = state["gen"]
        _fast = bool(fast_var.get())
        _opt = not _fast
        set_text("分析中… %d 点%s, 界面可继续操作"
                 % (len(t), " (快速模式, 跳过寻优)" if _fast else ""))
        try:
            root.config(cursor="watch")
            root.update_idletasks()
        except Exception:                           # noqa: BLE001
            pass

        def _finish(_g, info, an):
            if _g != state.get("gen"):
                return                              # 过期结果, 直接丢弃
            state["busy"] = False
            try:
                root.config(cursor="")
            except Exception:                       # noqa: BLE001
                pass
            state["info"] = info
            state["analysis"] = an
            state["kind"] = an.get("kind")
            state["lam"] = None
            if an.get("kind") == "closed":
                lam_lbl.config(text="(无 u 模式不使用)")
            else:
                rec = max(info["tau"], 0.5 * info["T"])
                lo, hi = 0.05 * info["T"], 4.0 * info["T"]
                rec = min(max(rec, lo), hi)
                state["lam"] = rec
                lam_var.set((rec - lo) / (hi - lo) if hi > lo else 0.5)
                lam_lbl.config(text=f"{rec:.4g}")
            try:
                redraw_original()
                render()
            except Exception as e:                  # noqa: BLE001
                _fail("绘图/渲染失败", e)

        _q = queue.Queue()

        def _worker():
            try:
                _q.put((_gen, "ok",
                        analyze(t, u, y, r=r, mode=current_mode(),
                                current_pid=_cur_pid,
                                do_optimize=_opt, do_robust=_opt,
                                pref=state.get("pref"), dt_ctrl=_ts)))
            except Exception as e:                  # noqa: BLE001
                _q.put((_gen, "err", e))

        def _poll():
            try:
                _g, _kind, _payload = _q.get_nowait()
            except queue.Empty:
                root.after(150, _poll)
                return
            if _g != state.get("gen"):
                return                              # 已被新一轮取代, 停止轮询
            if _kind == "err":
                state["busy"] = False
                try:
                    root.config(cursor="")
                except Exception:                   # noqa: BLE001
                    pass
                _fail("分析失败", _payload)
                return
            _finish(_g, _payload[0], _payload[1])

        if state.get("sync_mode"):
            # 冒烟测试等自动化场景需要立即拿到结果, 走同步路径。
            try:
                _info, _an = analyze(t, u, y, r=r, mode=current_mode(),
                                     current_pid=_cur_pid,
                                     do_optimize=True, do_robust=True,
                                     pref=state.get("pref"), dt_ctrl=_ts)
            except Exception as e:                  # noqa: BLE001
                try:
                    root.config(cursor="")
                except Exception:                   # noqa: BLE001
                    pass
                _fail("分析失败", e)
                return
            _finish(_gen, _info, _an)
            return
        state["busy"] = True
        threading.Thread(target=_worker, daemon=True).start()
        root.after(150, _poll)'''

txt = io.open(P, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in txt else '\n'
lines = txt.split(nl)

# 定位: do_analyze 内的 import queue  ->  root.after(150, _poll)
a = b = None
for i, l in enumerate(lines):
    if l.strip() == 'import queue' and i > 5900:
        a = i
        break
if a is not None:
    for j in range(a, len(lines)):
        if 'root.after(150, _poll)' in lines[j]:
            b = j
            break
print('区间 行 %s..%s' % (a + 1 if a is not None else '?', b + 1 if b is not None else '?'))
if a is None or b is None or b <= a:
    print('FAIL: 未定位, 未写入')
    raise SystemExit(1)
print('首行:', lines[a].strip()[:50])
print('末行:', lines[b].strip()[:50])

lines[a:b + 1] = NEW.split('\n')
txt = nl.join(lines)

# 加「快速模式」勾选(紧跟在固件单位之后)
OLD_CB = ('    fw_var = tk.BooleanVar(value=False)\n'
          '    ttk.Checkbutton(pid_holder, text="固件单位", variable=fw_var).pack(\n'
          '        side="left", padx=(8, 0))\n')
NEW_CB = OLD_CB + (
    '    # 快速模式: 跳过寻优/鲁棒性检验。寻优要在上百组候选参数上各跑一遍\n'
    '    # 完整仿真, 1650 点/16 秒的数据会跑好几分钟, 先给结果再谈优化。\n'
    '    fast_var = tk.BooleanVar(value=True)\n'
    '    ttk.Checkbutton(pid_holder, text="快速模式", variable=fast_var).pack(\n'
    '        side="left", padx=(8, 0))\n')
OLD_CB = OLD_CB.replace('\n', nl)
NEW_CB = NEW_CB.replace('\n', nl)
n = txt.count(OLD_CB)
print('勾选框锚点命中 %d 次' % n)
if n != 1:
    print('FAIL: 勾选框锚点不唯一, 未写入')
    raise SystemExit(1)
txt = txt.replace(OLD_CB, NEW_CB)

io.open(P, 'w', encoding='utf-8', newline='').write(txt)
print('已写入')
