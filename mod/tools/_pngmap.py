"""把贴图缩成字符图（亮度 + alpha），一眼看出「哪儿有亮条/暗角」。

用法: python tools\_pngmap.py <png> [列数]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAMP = ' .:-=+*#%@'


def main(argv):
    path = argv[1]
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    cols = int(argv[2]) if len(argv) > 2 else 48
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    rows = max(4, int(cols * h / float(w) * 0.5))
    small = im.resize((cols, rows), Image.BOX)
    px = small.load()
    print('%s  %dx%d  -> %dx%d  (字符=alpha 深度, " "=全透明)' % (
        os.path.basename(path), w, h, cols, rows))
    for j in range(rows):
        line = []
        for i in range(cols):
            r, g, b, a = px[i, j]
            lvl = int(a / 256.0 * 10)
            if a == 0:
                line.append(' ')
            elif r + g + b > 3 * 190:
                line.append(RAMP[min(9, max(1, lvl))] if lvl >= 3 else 'o')   # 亮 + 有 alpha
            else:
                line.append(RAMP[min(9, lvl)])
        print('|' + ''.join(line) + '|')
    # 最亮/最透的点
    mx = max(((px[i, j][3] * (1 if sum(px[i, j][:3]) > 400 else -1), i, j) for j in range(rows)
              for i in range(cols)))[0:1]
    print('峰值信息：%s' % (mx,))


if __name__ == '__main__':
    main(sys.argv)
