# -*- coding: gbk -*-
"""诊断 motor_bldc.c 的字节内容 / 编码是否被写坏。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

for P in (r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c',
          r'd:\plain_view\66T\mis-t160-main-ptz\application\motor_bldc.c'):
    raw = open(P, 'rb').read()
    print('=' * 70)
    print(P)
    print('  大小 %d' % len(raw))
    print('  前 120 字节: %r' % raw[:120])
    ctrl = sum(1 for b in raw if b < 0x09 or (0x0E <= b <= 0x1F) or b == 0x7F)
    print('  控制字符(非 \\r\\n\\t) 个数: %d  占比 %.3f%%'
          % (ctrl, 100.0 * ctrl / len(raw)))
    for enc in ('utf-8', 'gbk', 'latin-1'):
        try:
            s = raw.decode(enc)
            bad = sum(1 for ch in s if ord(ch) < 0x20 and ch not in '\r\n\t')
            print('  按 %-8s 解码: 成功, 长度 %d, 控制字符 %d' % (enc, len(s), bad))
        except UnicodeDecodeError as e:
            print('  按 %-8s 解码: 失败 (%s)' % (enc, str(e)[:60]))
    # 以 GBK 读出来的前几行
    try:
        s = raw.decode('gbk')
        print('  GBK 前 3 行:')
        for ln in s.splitlines()[:3]:
            print('      %s' % ln[:90])
    except Exception as e:                          # noqa: BLE001
        print('  GBK 读取异常:', e)
    print('')
