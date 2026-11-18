# -*- coding: gbk -*-
"""修 dt 默认值(1.0 -> 0.01) 并给频域辨识加采样率守卫。"""
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
        print('  [FAIL] %-32s 命中 %d 次' % (tag, n))
        return txt, False
    print('  [ok]   %-32s +%d 行' % (tag, new.count(nl) - old.count(nl)))
    return txt.replace(old, new), True


txt, nl = load(P)
print('换行符=%s' % ('CRLF' if nl == '\r\n' else 'LF'))
ok = True

# 1. dt 输入框预填 0.01
txt, r = patch(txt, nl, '''    dt_var = tk.StringVar(value="")''',
               '''    dt_var = tk.StringVar(value="0.01")''', '1 dt 预填 0.01')
ok &= r

# 2. read_dt 兜底改成 0.01
txt, r = patch(txt, nl, '''            v = float(dt_var.get())
            return v if v > 0 else 1.0
        except ValueError:
            return 1.0''',
               '''            v = float(dt_var.get())
            return v if v > 0 else 0.01
        except ValueError:
            return 0.01''', '2 read_dt 兜底 0.01')
ok &= r

# 3. 频域辨识前的采样率守卫
txt, r = patch(txt, nl, '''    if len(u) != len(y):
        return "u 与 y 长度不一致, 请检查数据列映射。"''',
               '''    if len(u) != len(y):
        return "u 与 y 长度不一致, 请检查数据列映射。"
    # 20Hz 的激励至少要比 Nyquist 低一个量级, dt 大于 50ms 时会被折叠成假峰。
    if dt is None or dt <= 0 or dt > 0.05:
        return ("采样间隔 dt = %s 太大, 无法分析 1.5~20 Hz 的激励。\\n"
                "请在「采样周期 dt」里填真实值 (vofa 10ms 就填 0.01)。" % dt)''',
               '3 dt 守卫')
ok &= r

if ok:
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print('')
    print('已写入')
else:
    print('')
    print('!! 有失败, 未写入')
