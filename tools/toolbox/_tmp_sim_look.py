import re

p = r'd:\aMyProject\Project\22b2\22bmain\1111\22b2\power_source_code\source_code\application\OLED_font.c'
src = open(p, 'rb').read().decode('gbk')
m = re.search(r'const uint8_t SIM_BMP\[\]\[120\]\s*=\s*\{(.*?)\n\};', src, re.S)
ab = [int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]{2})', m.group(1))]


def render(idx):
    b = ab[idx * 120:(idx + 1) * 120]
    for row in range(32):
        print('%2d ' % row + ''.join('#' if (b[(row // 8) * 30 + col] >> (row % 8)) & 1 else '.' for col in range(30)))


for idx in [30, 40]:
    print('=== SIM_BMP[%d] ===' % idx)
    render(idx)
