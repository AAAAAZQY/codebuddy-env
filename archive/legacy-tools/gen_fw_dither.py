# -*- coding: gbk -*-
"""在 motor_bldc.c 里加入辨识用多频激励(dither)。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'

FS = 10000.0
FREQS = [1.5, 3.0, 4.5, 9.0, 14.5, 20.0]
AMP = 80

# 256 点正弦表, 幅值 1000
tab = [int(round(1000.0 * __import__('math').sin(2 * 3.141592653589793 * k / 256.0)))
       for k in range(256)]
rows = []
for r in range(0, 256, 12):
    rows.append('    ' + ', '.join('%5d' % v for v in tab[r:r + 12]) + ',')
tab_text = '\n'.join(rows)

steps = [int(round(f * 4294967296.0 / FS)) for f in FREQS]
step_text = '\n'.join('    %10du,   /* %4.1f Hz */' % (s, f) for s, f in zip(steps, FREQS))

BLOCK = '''/* ---- 辨识用多频激励 (dither) ------------------------------------------
 * 目的: 不加阶跃、不停机, 直接测出速度环对象 P(s) 的频率响应。
 * 做法: 在 target_Uq 上叠加 6 个已知频率的小幅正弦, 均值 0。
 *       抓 time / Uq / 速度 三列, 在激励频率上算 P(w) = V(w) / U(w)。
 * 参数: 幅值 %d (6 个叠加峰值 <= %d), 工作点约 2272, 离 4000 限幅还有余量。
 * 频率: 全部避开 18 次/圈的梳状成分
 *       (5.58/6.97/11.16/11.86/12.55/13.25/16.74 Hz), 以免和负载纹波混淆。
 * 诊断用: 采完数据请把 MOTOR_IDENT_DITHER 改回 0。 */
#define MOTOR_IDENT_DITHER    1
#define IDENT_DITHER_AMP      %d

#if MOTOR_IDENT_DITHER
/* 256 点正弦表, 幅值 1000 */
static const int16_t ident_sin_256[256] =
{
%s
};

/* 相位步进 = f * 2^32 / 10000 (10kHz 控制节拍), 索引取相位高 8 位 */
static const uint32_t ident_phase_step[6] =
{
%s
};

static int16_t ident_dither_value(void)
{
    static uint32_t ph[6] = {0, 0, 0, 0, 0, 0};
    int32_t sum = 0;
    uint8_t i;

    for(i = 0; i < 6; i++)
    {
        ph[i] += ident_phase_step[i];
        sum += ident_sin_256[ph[i] >> 24];
    }

    return (int16_t)((sum * IDENT_DITHER_AMP) / 1000);
}
#endif

''' % (AMP, AMP * 6, AMP, tab_text, step_text)

HOOK = '''    bldc->target_Uq = pid_calculate(&(bldc->pid_velocity), bldc->target_velocity - bldc->current_velocity);

#if MOTOR_IDENT_DITHER
    /* 只在正转高速、且离限幅还远时注入, 保证 Uq 不被削顶 */
    if((bldc->current_velocity > 15000) &&
       (bldc->target_Uq > -3000) && (bldc->target_Uq < 3000))
    {
        bldc->target_Uq += ident_dither_value();
    }
#endif
'''

s = io.open(P, encoding='gbk', errors='replace').read()

anchor1 = '#define MOTOR_COGGING_COMP    0\n\n'
anchor2 = ('    bldc->target_Uq = pid_calculate(&(bldc->pid_velocity), '
           'bldc->target_velocity - bldc->current_velocity);\n\n')

ok = True
for a, name in ((anchor1, 'macro'), (anchor2, 'hook')):
    n = s.count(a)
    print('anchor %-6s occurrences = %d' % (name, n))
    if n != 1:
        ok = False

if not ok:
    print('FAIL: 未写入')
    raise SystemExit(1)

if 'MOTOR_IDENT_DITHER' in s:
    print('已存在 MOTOR_IDENT_DITHER, 不重复插入')
    raise SystemExit(0)

s = s.replace(anchor1, anchor1 + BLOCK)
s = s.replace(anchor2, HOOK + '\n')

io.open(P, 'w', encoding='gbk', errors='replace').write(s)
print('')
print('已写入 motor_bldc.c')
print('  幅值 %d, 峰值 <= %d' % (AMP, AMP * 6))
for f, st in zip(FREQS, steps):
    print('  %4.1f Hz  step=%u' % (f, st))
