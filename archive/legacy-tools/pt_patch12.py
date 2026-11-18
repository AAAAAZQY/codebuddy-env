# -*- coding: cp936 -*-
"""第 12 步：GUI 渲染里也把规则整定放到模型结果之前"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'


def L(s):
    return s.encode('utf-8').decode('latin-1')


src = io.open(TARGET, encoding='latin-1', newline='').read()

old = '''        else:
            _rmse = ("n/a" if inf.get("rmse") is None'''

new = '''        else:
            _fb = an.get("rule_fallback")
            if _fb:
                _fbc = _fb.get("current") or {}
                _fba = _fb.get("adjusted") or {}
                lines.append("=" * 118)
                lines.append("★ 经验规则整定 (采样不足, 以这条为准)")
                lines.append("=" * 118)
                if _fbc:
                    lines.append(f"当前参数: Kp={_fmt_pid(_fbc.get('Kp'))}   "
                                 f"Ki={_fmt_pid(_fbc.get('Ki'))}   "
                                 f"Kd={_fmt_pid(_fbc.get('Kd'))}")
                if _fb.get("action"):
                    lines.append(f"调整动作: {_fb['action']}")
                if _fba:
                    lines.append(f"建议参数: Kp={_fmt_pid(_fba.get('Kp'))}   "
                                 f"Ki={_fmt_pid(_fba.get('Ki'))}   "
                                 f"Kd={_fmt_pid(_fba.get('Kd'))}")
                for _n in (_fb.get("notes") or [])[:3]:
                    lines.append("  - " + _n)
                lines.append("-" * 118)
                lines.append("以下为模型整定结果 (采样不足, 仅供趋势参考)")
                lines.append("")
            _rmse = ("n/a" if inf.get("rmse") is None'''

if src.count(old) != 1:
    print('anchor count =', src.count(old))
    sys.exit(1)

src = src.replace(old, L(new))
out = src.encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('patched, bytes =', len(out))
