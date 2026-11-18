# -*- coding: gbk -*-
"""GUI 分析前降采样(长数据)+ 忙光标, 避免看起来像卡死。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'D:\bProject\pid_tuner\pid_tuner.py'


def load(path):
    with io.open(path, 'r', encoding='utf-8', newline='') as f:
        txt = f.read()
    nl = '\r\n' if '\r\n' in txt else '\n'
    return txt, nl


def patch(txt, nl, old, new, tag):
    old = old.replace('\n', nl)
    new = new.replace('\n', nl)
    n = txt.count(old)
    if n != 1:
        print('  [FAIL] %-30s 命中 %d 次' % (tag, n))
        return txt, False
    print('  [ok]   %-30s +%d 行' % (tag, new.count(nl) - old.count(nl)))
    return txt.replace(old, new), True


txt, nl = load(P)
print('换行符=%s' % ('CRLF' if nl == '\r\n' else 'LF'))
ok = True

# 1. 模块级降采样函数
FUNC = '''_MAX_ANALYZE_POINTS = 700


def _decimate(t, u, y, r, limit=_MAX_ANALYZE_POINTS):
    """块平均降采样: 点数超过 limit 时按整块平均, 保持 dt 一致。

    目的是把纯 Python 仿真的耗时压到可接受范围 —— 1500+ 点时寻优要在
    上百组候选参数上各跑一遍完整仿真, 界面会几十秒无响应。
    """
    n = len(t)
    if n <= limit or n < 4:
        return t, u, y, r, 1
    k = int(math.ceil(n / float(limit)))
    dt = (t[1] - t[0]) if n > 1 else 1.0
    nt, nu, ny, nr = [], [], [], []
    for i in range(0, n - k + 1, k):
        nt.append(t[i] + 0.5 * (k - 1) * dt)
        nu.append(sum(u[i:i + k]) / k)
        ny.append(sum(y[i:i + k]) / k)
        nr.append(sum(r[i:i + k]) / k if r is not None else None)
    if nr and nr[0] is None:
        nr = None
    return nt, nu, ny, nr, k


'''

txt, r = patch(txt, nl, 'def _fit_to_info(fb, t, u, y, r):\n', FUNC + 'def _fit_to_info(fb, t, u, y, r):\n',
               '1 降采样函数')
ok &= r

# 2. do_analyze 里降采样 + 忙光标
txt, r = patch(txt, nl, '''        try:
            info, an = analyze(t, u, y, r=r, mode=current_mode(),
                               current_pid=_cur_pid,
                               do_optimize=True, do_robust=True,
                               pref=state.get("pref"), dt_ctrl=_ts)
        except Exception as e:                      # noqa: BLE001
            _fail("分析失败", e)
            return''',
               '''        # 长数据先降采样: 1566 点会让寻优跑几十秒, 界面看起来像卡死。
        _n0 = len(t)
        t, u, y, r, _k = _decimate(t, u, y, r)
        if _k > 1:
            state["data"] = (t, u, y, r)     # 后续「重新计算」也用降采样后的
            set_text("分析中… %d 点 -> %d 点(1/%d 降采样), 请稍候"
                     % (_n0, len(t), _k))
        else:
            set_text("分析中… %d 点, 请稍候" % _n0)
        try:
            root.config(cursor="watch")
            root.update_idletasks()
        except Exception:                           # noqa: BLE001
            pass
        try:
            info, an = analyze(t, u, y, r=r, mode=current_mode(),
                               current_pid=_cur_pid,
                               do_optimize=True, do_robust=True,
                               pref=state.get("pref"), dt_ctrl=_ts)
        except Exception as e:                      # noqa: BLE001
            try:
                root.config(cursor="")
            except Exception:                       # noqa: BLE001
                pass
            _fail("分析失败", e)
            return
        try:
            root.config(cursor="")
        except Exception:                           # noqa: BLE001
            pass''', '2 do_analyze 降采样+忙光标')
ok &= r

if ok:
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print('')
    print('已写入')
else:
    print('')
    print('!! 有失败, 未写入')
