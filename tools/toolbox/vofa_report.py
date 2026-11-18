# -*- coding: gbk -*-
"""vofa 六通道数据统一分析工具（取代之前的一堆一次性脚本）。

用法:
    python vofa_report.py                    # 读剪贴板
    python vofa_report.py a.txt              # 读文件
    python vofa_report.py a.txt b.txt c.txt  # 多文件对比

通道顺序(本工程): 0=实际速度 1=规划速度 2=位置误差 3=Uq 4=目标速度 5=位置
"""
import cmath
import io
import math
import os
import statistics
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CH_Y, CH_PLAN, CH_PERR, CH_UQ, CH_TGT, CH_POS = 0, 1, 2, 3, 4, 5
TARGET_VEL = 25107.0
STEADY_TOL = 900.0        # 实际速度落在目标 ±900 内才算稳态
ORDER_LIST = (1, 2, 8, 10, 16, 17, 18, 19, 24, 32)


# ---------------------------------------------------------------- 读取
def read_clipboard():
    try:
        import subprocess
        r = subprocess.run(['powershell', '-NoProfile', '-Command', 'Get-Clipboard -Raw'],
                           capture_output=True)
        return r.stdout.decode('utf-8', 'ignore')
    except Exception:                               # noqa: BLE001
        return ''


def parse(raw):
    toks = [t for t in raw.split() if len(t) == 2]
    if len(toks) < 84:          # 至少 3 帧
        return []
    data = bytes(int(t, 16) for t in toks)
    fr, i = [], 0
    while i + 28 <= len(data):
        c = data[i:i + 28]
        if c[24:28] == b'\x00\x00\x80\x7f':
            fr.append(struct.unpack('<6f', c[:24]))
            i += 28
        else:
            i += 1
    return fr


# ---------------------------------------------------------------- 分析
def lockin_amp(vals, pos, order):
    """位置锁定(角度同步)锁相，返回该阶次幅值。"""
    n = len(vals)
    m = sum(vals) / n
    s = 0j
    for v, p in zip(vals, pos):
        s += (v - m) * cmath.exp(-1j * 2 * math.pi * order * (p % 36000.0) / 36000.0)
    return 2 * abs(s) / n


def spectrum(vals, dt, topn=8):
    n = len(vals)
    m = sum(vals) / n
    x = [v - m for v in vals]
    for k in range(n):                      # 去掉线性趋势，避免低频伪峰
        x[k] -= (x[-1] - x[0]) * k / max(1, n - 1)
    out = []
    for fi in range(1, n // 2):
        s = 0j
        for k in range(n):
            s += x[k] * cmath.exp(-2j * math.pi * fi * k / n)
        out.append((fi / (n * dt), 2 * abs(s) / n))
    out.sort(key=lambda t: -t[1])
    return out[:topn]


def analyse(frames, dt=0.01, tag=''):
    st = [f for f in frames
          if f[CH_Y] > 15000 and abs(f[CH_Y] - TARGET_VEL) < STEADY_TOL]
    if len(st) < 100:
        print('!! %s 稳态帧不足(%d)，无法分析' % (tag, len(st)))
        return None

    y = [f[CH_Y] for f in st]
    uq = [f[CH_UQ] for f in st]
    pos = [f[CH_POS] for f in st]
    err = [f[CH_Y] - TARGET_VEL for f in st]
    ys = sorted(y)
    p5p95 = ys[int(len(ys) * .95)] - ys[int(len(ys) * .05)]
    std = statistics.pstdev(y)

    print('=' * 66)
    print('  %s' % (tag or '数据分析'))
    print('=' * 66)
    print('  总帧 %d   稳态 %d 帧 (%.1f 秒)' % (len(frames), len(st), len(st) * dt))
    print('')
    print('  【速度】')
    print('    p5-p95 %5.0f  (%.1f%%)   std %4.0f   均值 %.0f'
          % (p5p95, 100.0 * p5p95 / TARGET_VEL, std, statistics.mean(y)))
    print('    偏离目标 %+5.0f   min %.0f  max %.0f'
          % (statistics.mean(err), min(y), max(y)))
    print('')
    print('  【控制量 Uq】')
    print('    均值 %5.0f   std %4.0f   min %.0f   max %.0f'
          % (statistics.mean(uq), statistics.pstdev(uq), min(uq), max(uq)))
    print('')
    print('  【位置锁定阶次】(角度同步锁相)')
    amps = {}
    for o in ORDER_LIST:
        amps[o] = lockin_amp(y, pos, o)
    print('    ' + '  '.join('%d:%.0f' % (o, amps[o]) for o in ORDER_LIST))
    rms = math.sqrt(sum((a / 1.414) ** 2 for a in amps.values()))
    print('    合计 rms %.0f   占总方差 %.0f%%' % (rms, 100.0 * rms ** 2 / std ** 2))
    print('')
    print('  【频谱峰值】')
    f0 = statistics.mean(y) / 100.0 / 360.0
    for f, a in spectrum(y, dt):
        o = round(f / f0) if f0 else 0
        print('    %6.2f Hz  %5.0f   ~%2d 阶' % (f, a, o))
    print('')
    return {'p5p95': p5p95, 'std': std, 'amps': amps, 'n': len(st)}


def profile(frames, dt=0.01, tag='', segs=12):
    """全程剖面：不筛稳态，按时间分段看速度/目标/Uq 的走势。"""
    n = len(frames)
    if n < segs * 3:
        print('帧数太少')
        return
    print('=' * 78)
    print('  %s   全程剖面 (%d 帧, %.1f 秒)' % (tag or '数据', n, n * dt))
    print('=' * 78)
    print('  %-7s %9s %9s %9s %9s %9s'
          % ('t(s)', '实际速度', '目标速度', '跟踪差', 'Uq', '位置'))
    seg = max(1, n // segs)
    for k in range(segs):
        a, b = k * seg, min(n, (k + 1) * seg)
        blk = frames[a:b]
        v = [f[CH_Y] for f in blk]
        tg = [f[CH_TGT] for f in blk]
        uq = [f[CH_UQ] for f in blk]
        po = [f[CH_POS] for f in blk]
        print('  %-7.1f %9.0f %9.0f %9.0f %9.0f %9.0f'
              % (a * dt, statistics.mean(v), statistics.mean(tg),
                 statistics.mean(tg) - statistics.mean(v),
                 statistics.mean(uq), statistics.mean(po)))
    vs = [f[CH_Y] for f in frames]
    print('')
    print('  全程: 速度 %.0f ~ %.0f   目标 %.0f ~ %.0f'
          % (min(vs), max(vs), min(f[CH_TGT] for f in frames),
             max(f[CH_TGT] for f in frames)))
    print('')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    do_profile = '--profile' in sys.argv
    if args:
        jobs = [(os.path.basename(p), p) for p in args]
    else:
        raw = read_clipboard()
        if not raw.strip():
            print('剪贴板没有数据。先把 vofa hex 复制到剪贴板，或直接传文件路径。')
            return 1
        tmp = r'D:\Codebuddy\tmp\vofa_clip.txt'
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        io.open(tmp, 'w', encoding='utf-8').write(raw)
        jobs = [('剪贴板', tmp)]

    results = []
    for tag, path in jobs:
        if not os.path.isfile(path):
            print('文件不存在:', path)
            continue
        fr = parse(io.open(path, encoding='utf-8', errors='replace').read())
        if not fr:
            print('解析失败(不是 vofa hex 格式):', path)
            continue
        if do_profile:
            profile(fr, tag=tag)
            continue
        r = analyse(fr, tag=tag)
        if r:
            results.append((tag, r))

    if len(results) > 1:
        print('=' * 66)
        print('  汇总对比')
        print('=' * 66)
        print('  %-22s %8s %7s %8s %8s' % ('数据', 'p5-p95', 'std', '18阶', '稳态帧'))
        for tag, r in results:
            print('  %-22s %8.0f %7.0f %8.0f %8d'
                  % (tag[:22], r['p5p95'], r['std'], r['amps'][18], r['n']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
