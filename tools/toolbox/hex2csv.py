# -*- coding: gbk -*-
"""VOFA JustFloat hex dump -> CSV with named channels.

Frame layout: 6 x float32 (little endian) + tail 00 00 80 7F, 28 bytes.

PAN frame (speed loop = IMU gyro; ch5 = encoder ground truth), from bldc_vofa_task():
  ch0  velocity feedback (IMU gyro YAW=gz *100, alpha filtered)   0.01 deg/s
  ch1  plan velocity (plan_velocity_current)                 0.01 deg/s
  ch2  position error                                        0.01 deg
  ch3  target Uq                                             -
  ch4  target velocity                                       0.01 deg/s
  ch5  encoder velocity unfiltered (delta_angle/ANGLE_RATIO*FREQ)  0.01 deg/s

TILT frame (--tilt), same frame layout, different meaning:
  ch0  velocity feedback   ch1 plan velocity   ch2 position error
  ch3  target Uq           ch4 plan_accelerate_stage   ch5 current position

usage:
  python hex2csv.py [src] [dst] [dt]
  python hex2csv.py --clip              # read hex dump from clipboard
  python hex2csv.py --tilt [src] [dst] [dt]
  python hex2csv.py --ch5 aux|imu|enc   # ch5 relabelled: frame counter / raw gyro / encoder
  python hex2csv.py --list              # just print channel table
"""
import io
import os
import struct
import sys

NAME_PAN = ['vel_gyro', 'plan_vel', 'pos_err', 'uq', 'tgt_vel', 'enc_vel']
NAME_TILT = ['vel', 'plan_vel', 'pos_err', 'uq', 'acc_stage', 'pos']
UNIT_PAN = ['0.01deg/s', '0.01deg/s', '0.01deg', '-', '0.01deg/s', '0.01deg/s']
UNIT_TILT = ['0.01deg/s', '0.01deg/s', '0.01deg', '-', '-', '0.01deg']
DESC_PAN = ['gyro feedback (YAW=gz)*100, alpha=0.05 filtered', 'plan velocity', 'position error',
            'target Uq', 'target velocity', 'encoder velocity unfiltered (ground truth)']
DESC_TILT = ['feedback', 'plan velocity', 'position error',
             'target Uq', 'plan_accelerate_stage', 'current position']

CH5_ALIAS = {
    'enc': ('enc_vel', '0.01deg/s', 'encoder velocity unfiltered (ground truth)'),
    'imu': ('gyro_gz', '0.01deg/s', 'IMU gyro (YAW=gz) *100, raw unfiltered'),
    'aux': ('imu_cnt', '-', 'IMU frame counter (diff/10ms = frame rate)'),
}


def parse_args(argv):
    tilt = False
    clip = False
    ch5 = None
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--tilt':
            tilt = True
        elif a == '--clip':
            clip = True
        elif a == '--ch5':
            i += 1
            ch5 = argv[i].lower() if i < len(argv) else 'enc'
        elif a == '--list':
            return {'list': True}
        elif a in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        else:
            pos.append(a)
        i += 1

    src = pos[0] if len(pos) > 0 else r'D:\Codebuddy\tmp\vofa_hex44.txt'
    dst = pos[1] if len(pos) > 1 else os.path.splitext(src)[0] + '_named.csv'
    dt = float(pos[2]) if len(pos) > 2 else 0.01
    return {'list': False, 'src': src, 'dst': dst, 'dt': dt,
            'tilt': tilt, 'ch5': ch5, 'clip': clip}


def channel_table(tilt, ch5):
    names = list(NAME_TILT if tilt else NAME_PAN)
    units = list(UNIT_TILT if tilt else UNIT_PAN)
    desc = list(DESC_TILT if tilt else DESC_PAN)
    if (ch5 in CH5_ALIAS) and (not tilt):
        n, u, d = CH5_ALIAS[ch5]
        names[5], units[5], desc[5] = n, u, d
    return names, units, desc


def print_table(tilt, ch5):
    names, units, desc = channel_table(tilt, ch5)
    print('frame: %s   dt=%.4f s' % ('TILT' if tilt else 'PAN', 0.01))
    for k in range(6):
        print('  ch%d  %-12s %-10s %s' % (k, names[k], units[k], desc[k]))


def read_clipboard():
    """Return clipboard text. Tk first (no codepage issues), then PowerShell."""
    try:
        import tkinter
        win = tkinter.Tk()
        win.withdraw()
        txt = win.clipboard_get()
        win.destroy()
        return txt
    except Exception:
        pass
    try:
        import subprocess
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             '[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-Clipboard -Raw'],
            capture_output=True)
        return out.stdout.decode('utf-8', 'ignore')
    except Exception:
        return ''


def next_dump_path(tmpdir=r'D:\Codebuddy\tmp'):
    os.makedirs(tmpdir, exist_ok=True)
    n = 1
    for f in os.listdir(tmpdir):
        if f.startswith('vofa_hex') and f.endswith('.txt'):
            core = f[len('vofa_hex'):-len('.txt')]
            if core.isdigit():
                n = max(n, int(core) + 1)
    return os.path.join(tmpdir, 'vofa_hex%d.txt' % n)


def load_frames(src):
    raw = io.open(src, encoding='utf-8', errors='ignore').read()
    toks = [t for t in raw.replace('0x', ' ').replace('0X', ' ').split() if len(t) == 2]
    data = bytes(int(t, 16) for t in toks)

    frames = []
    skipped = 0
    i = 0
    n = len(data)
    while i + 28 <= n:
        if data[i + 24:i + 28] == b'\x00\x00\x80\x7f':
            frames.append(struct.unpack('<6f', data[i:i + 24]))
            i += 28
        else:
            i += 1
            skipped += 1
    info = {'total_bytes': n, 'skipped': skipped,
            'tail_ratio': (len(frames) * 28.0 / n) if n else 0.0}
    return frames, info


def sanity_check(frames, finfo):
    """Self-check: byte accounting, tail hit rate, physical value ranges.
    Returns list of warning strings; empty list = clean."""
    warns = []
    n = finfo['total_bytes']
    if n == 0:
        return ['0 bytes parsed']
    if finfo['tail_ratio'] < 0.98:
        warns.append('tail hit ratio %.1f%% < 98%% (frame misaligned or truncated data)'
                     % (finfo['tail_ratio'] * 100))
    if finfo['skipped'] > max(28, len(frames) * 0.02):
        warns.append('%d stray bytes skipped (>2%% of frames)' % finfo['skipped'])
    if len(frames) == 0:
        warns.append('0 frames')

    # ch0/ch1/ch4 velocity-like: |v| <= 40000 (0.01 deg/s)
    # ch3 Uq: |v| <= 6000
    # ch2: -40000..40000 (position on PAN, position error on TILT)
    for ch, lo, hi, tag in ((0, -40000, 40000, 'velocity-like'),
                            (1, -40000, 40000, 'velocity-like'),
                            (2, -40000, 40000, 'pos/pos_err'),
                            (3, -6000, 6000, 'Uq'),
                            (4, -40000, 40000, 'velocity-like')):
        vals = [fr[ch] for fr in frames]
        mn, mx = min(vals), max(vals)
        if mn < lo or mx > hi:
            warns.append('ch%d out of %s range: [%.0f, %.0f]' % (ch, tag, mn, mx))
    return warns


def stats(vals):
    n = len(vals)
    if n == 0:
        return (0.0, 0.0, 0.0, 0.0)
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / n
    return (min(vals), max(vals), mean, var ** 0.5)


def main():
    opt = parse_args(sys.argv[1:])
    if opt.get('list'):
        print_table(False, None)
        return

    src, dst, dt = opt['src'], opt['dst'], opt['dt']
    names, units, desc = channel_table(opt['tilt'], opt['ch5'])

    if opt.get('clip'):
        txt = read_clipboard()
        if not txt.strip():
            print('ERROR: clipboard is empty')
            return
        src = next_dump_path()
        with io.open(src, 'w', encoding='utf-8', newline='') as f:
            f.write(txt)
        dst = os.path.splitext(src)[0] + '_named.csv'
        print('clipboard saved to: %s' % src)

    if not os.path.isfile(src):
        print('ERROR: no such file: %s' % src)
        return

    frames, finfo = load_frames(src)
    if not frames:
        print('ERROR: 0 frames parsed from %s' % src)
        return

    print('sanity: bytes=%d  frames*28=%d  skipped=%d  tail_ratio=%.1f%%'
          % (finfo['total_bytes'], len(frames) * 28, finfo['skipped'],
             finfo['tail_ratio'] * 100))
    warns = sanity_check(frames, finfo)
    if warns:
        for w in warns:
            print('SANITY WARN: %s' % w)
    else:
        print('sanity: OK')

    header = ['time_s'] + ['ch%d_%s' % (k, names[k]) for k in range(6)]
    with io.open(dst, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(','.join(header) + '\n')
        for k, fr in enumerate(frames):
            f.write('%.4f' % (k * dt))
            for v in fr:
                f.write(',%.3f' % v)
            f.write('\n')

    print('src    : %s' % src)
    print('dst    : %s' % dst)
    print('frames : %d   dt=%.4f s   span=%.2f s' % (len(frames), dt, len(frames) * dt))
    print('')
    for k in range(6):
        print('  ch%d  %-12s %-10s %s' % (k, names[k], units[k], desc[k]))
    print('')
    print('ch   name          unit          min          max         mean        std')
    for k in range(6):
        vals = [fr[k] for fr in frames]
        mn, mx, mean, sd = stats(vals)
        print('ch%d  %-13s %-13s %11.1f %12.1f %12.1f %10.1f'
              % (k, names[k], units[k], mn, mx, mean, sd))


if __name__ == '__main__':
    main()
