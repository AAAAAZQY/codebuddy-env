# -*- coding: cp936 -*-
"""修正第6页：去掉重复行、去掉残留的稳像表述、补一条移植原则"""
import io
import sys

LASER = "'激光测距：55AA 帧解析、单次 / 连续测距、命令透传与应答回显',"
OLD_DUP = LASER + "\n        " + LASER + "\n"
NEW_DUP = LASER + "\n"

OLD_SENS = "        ('数值敏感：稳像增益与行程限位必须按整机重新整定，不能照抄其他机型', 1),"
NEW_SENS = ("        '移植原则：不改动原工程控制逻辑，按最小改动接入，逐项联调验证',\n"
            "        ('接线与协议按目标机型重新核对：串口占用、引脚定义、方向控制脚', 1),")


def patch(path):
    s = io.open(path, encoding='cp936', newline='').read()
    s = s.replace('\r\n', '\n')
    n1 = s.count(OLD_DUP)
    s = s.replace(OLD_DUP, NEW_DUP)
    n2 = s.count(OLD_SENS)
    s = s.replace(OLD_SENS, NEW_SENS)
    s = s.replace('\n', '\r\n')
    io.open(path, 'w', encoding='cp936', newline='').write(s)
    print('patched %s  dup=%d sens=%d  remain_wenxiang=%d'
          % (path, n1, n2, s.count('稳像')))

    # 打印第 6 页片段供核对
    lines = s.split('\r\n')
    for i, ln in enumerate(lines):
        if '配件模块移植' in ln:
            for j in range(i, min(i + 9, len(lines))):
                print('   ' + lines[j])
            break


for p in sys.argv[1:]:
    patch(p)
