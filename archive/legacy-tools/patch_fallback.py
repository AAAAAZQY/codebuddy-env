# -*- coding: gbk -*-
"""analyze() 里 identify() 失败时, 回退到「任意激励仿真拟合」, 不再抛异常。"""
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

# 1. info 构造器
txt, r = patch(txt, nl, '''def _fit_sim(y, u, dt):''', '''def _fit_to_info(fb, t, u, y, r):
    """把任意激励拟合结果包装成与 identify() 同构的 info。"""
    import math
    rel, K, T, tau = fb
    n = len(t)
    dt = (t[1] - t[0]) if n > 1 else 0.01
    return {"K": K, "T": T, "tau": tau, "dt": dt,
            "t_step": t[0] if n else 0.0, "i_step": 0,
            "du": None, "dy": None, "dr": None,
            "rmse": math.sqrt(max(0.0, rel)),
            "warnings": ["对象模型由「任意激励仿真拟合」得到(数据里没有阶跃), "
                         "相对残差 %.1f%%。" % (math.sqrt(max(0.0, rel)) * 100.0)],
            "t": t, "u": u, "y": y, "r": r,
            "sim_fit": True}


def _fit_sim(y, u, dt):''', '1 _fit_to_info')
ok &= r

# 2. identify 失败回退
txt, r = patch(txt, nl, '''        if not bad_scale:
            info = identify(t, u, y)
            return _model_route(info, info, "direct", _pid_cmp)''',
               '''        if not bad_scale:
            try:
                info = identify(t, u, y)
                return _model_route(info, info, "direct", _pid_cmp)
            except Exception as _e_step:            # noqa: BLE001
                # 数据里没有可用阶跃: 改用「任意激励仿真拟合」
                # (用实测 u 驱动模型, 最小化与实测 y 的误差, 不需要阶跃)
                _dt0 = (t[1] - t[0]) if len(t) > 1 else 0.01
                _fb = _fit_sim(y, u, _dt0)
                _rel = (math.sqrt(max(0.0, _fb[0])) if _fb else 1.0)
                if _fb is not None and _rel <= 0.35:
                    info = _fit_to_info(_fb, t, u, y, r)
                    return _model_route(info, info, "sim_fit", _pid_cmp)
                _route_warns.append(
                    "阶跃法失败(%s); 任意激励拟合残差 %.0f%%, 超过 35%% 阈值, "
                    "已放弃, 请采一段 u 有变化且不饱和的数据。"
                    % (str(_e_step), _rel * 100.0))''', '2 identify 失败回退')
ok &= r

if ok:
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print('')
    print('已写入')
else:
    print('')
    print('!! 有失败, 未写入')
