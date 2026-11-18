# -*- coding: cp936 -*-
"""按行修正：打印剩余"稳像"位置，并修第6页重复行/残留句"""
import io
import sys


def show(path):
    s = io.open(path, encoding='cp936', newline='').read().replace('\r\n', '\n')
    lines = s.split('\n')
    print('==== %s ====' % path)
    for i, ln in enumerate(lines, 1):
        if '稳像' in ln:
            print('  [wenxiang] %d: %s' % (i, ln.strip()))
    for i, ln in enumerate(lines):
        if '配件模块移植' in ln and 'content_slide' in ln or '配件模块移植' in ln and ("('" in ln):
            print('  --- page6 head at %d ---' % (i + 1))
            for j in range(i, min(i + 9, len(lines))):
                print('   %s' % lines[j])
            break
    return s


def fix(path):
    s = io.open(path, encoding='cp936', newline='').read().replace('\r\n', '\n')
    lines = s.split('\n')
    out = []
    seen_laser_after_module_port = False
    removed_dup = 0
    replaced_sens = 0
    for ln in lines:
        if '激光测距：55AA' in ln:
            if seen_laser_after_module_port:
                removed_dup += 1
                continue
            seen_laser_after_module_port = True
            out.append(ln)
            continue
        if '数值敏感：稳像增益' in ln:
            indent = ln[:len(ln) - len(ln.lstrip())]
            out.append(indent + "'移植原则：不改动原工程控制逻辑，按最小改动接入，逐项联调验证',")
            out.append(indent + "('接线与协议按目标机型重新核对：串口占用、引脚定义、方向控制脚', 1),")
            replaced_sens += 1
            continue
        out.append(ln)
    s2 = '\n'.join(out)
    io.open(path, 'w', encoding='cp936', newline='').write(s2.replace('\n', '\r\n'))
    print('fixed %s  removed_dup=%d replaced_sens=%d remain_wenxiang=%d'
          % (path, removed_dup, replaced_sens, s2.count('稳像')))


for p in sys.argv[1:]:
    show(p)
    fix(p)
