# -*- coding: gbk -*-
"""把 GUI 的分析改成后台线程: 不再降采样, 界面也不冻结。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'D:\bProject\pid_tuner\pid_tuner.py'

NEW = '''        import queue
        import threading
        if state.get("busy"):
            set_text("上一轮分析还在跑, 请等它结束(界面可以正常操作)")
            return
        state["data"] = (t, u, y, r)     # 原始数据全量保留, 不降采样
        set_text("分析中… %d 点, 界面保持可用, 请稍候" % len(t))
        try:
            root.config(cursor="watch")
            root.update_idletasks()
        except Exception:                           # noqa: BLE001
            pass

        def _finish(info, an):
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
            # 纯计算放后台线程, 主线程只等待+渲染, 界面全程不冻结。
            try:
                _q.put(("ok", analyze(t, u, y, r=r, mode=current_mode(),
                                      current_pid=_cur_pid,
                                      do_optimize=True, do_robust=True,
                                      pref=state.get("pref"), dt_ctrl=_ts)))
            except Exception as e:                  # noqa: BLE001
                _q.put(("err", e))

        def _poll():
            try:
                _kind, _payload = _q.get_nowait()
            except queue.Empty:
                root.after(150, _poll)
                return
            if _kind == "err":
                state["busy"] = False
                try:
                    root.config(cursor="")
                except Exception:                   # noqa: BLE001
                    pass
                _fail("分析失败", _payload)
                return
            _finish(*_payload)

        state["busy"] = True
        threading.Thread(target=_worker, daemon=True).start()
        root.after(150, _poll)'''

txt = io.open(P, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in txt else '\n'
lines = txt.split(nl)
print('换行符=%s  总行数=%d' % ('CRLF' if nl == '\r\n' else 'LF', len(lines)))

# 定位待替换区间: 从「长数据先降采样」注释到「绘图/渲染失败」那行
a = b = None
for i, l in enumerate(lines):
    if '长数据先降采样' in l:
        a = i
    if a is not None and '绘图/渲染失败' in l:
        b = i
        break
print('替换区间 行 %s..%s' % (a + 1 if a is not None else '?', b + 1 if b is not None else '?'))
if a is None or b is None or b <= a:
    print('FAIL: 未找到区间, 未写入')
    raise SystemExit(1)

print('首行: %s' % lines[a].strip()[:60])
print('末行: %s' % lines[b].strip()[:60])

lines[a:b + 1] = NEW.split('\n')
io.open(P, 'w', encoding='utf-8', newline='').write(nl.join(lines))
print('已写入, 新总行数=%d' % len(lines))
