# -*- coding: gbk -*-
"""冒烟测试需要同步结果: 加 sync_mode 分支。"""
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
        print('  [FAIL] %-28s 命中 %d 次' % (tag, n))
        return txt, False
    print('  [ok]   %-28s +%d 行' % (tag, new.count(nl) - old.count(nl)))
    return txt.replace(old, new), True


txt, nl = load(P)
print('换行符=%s' % ('CRLF' if nl == '\r\n' else 'LF'))
ok = True

txt, r = patch(txt, nl, '''        state["busy"] = True
        threading.Thread(target=_worker, daemon=True).start()
        root.after(150, _poll)''',
               '''        if state.get("sync_mode"):
            # 冒烟测试等自动化场景需要立即拿到结果, 走原来的同步路径。
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
            _finish(_info, _an)
            return
        state["busy"] = True
        threading.Thread(target=_worker, daemon=True).start()
        root.after(150, _poll)''', '同步分支')
ok &= r

txt, r = patch(txt, nl, '''        def _smoke():
            try:''',
               '''        def _smoke():
            state["sync_mode"] = True
            try:''', '冒烟测试标记')
ok &= r

if ok:
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print('')
    print('已写入')
else:
    print('')
    print('!! 有失败, 未写入')
