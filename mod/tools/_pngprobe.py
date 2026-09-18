"""打印一张贴图若干位置的 RGBA（判断「中心是否真透明」这类问题）。

用法: python tools\_pngprobe.py <png> [点 ...]   点形如 0.5,0.5（比例）
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    path = argv[1]
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    print('%s  %dx%d' % (os.path.basename(path), w, h))
    pts = argv[2:] or ['0.5,0.5', '0.5,0.1', '0.1,0.5', '0.9,0.9', '0.5,0.92', '0.05,0.05',
                       '0.5,0.2', '0.5,0.8', '0.2,0.2']
    px = im.load()
    for p in pts:
        fx, fy = (float(v) for v in p.split(','))
        x, y = min(w - 1, int(fx * w)), min(h - 1, int(fy * h))
        print('  (%4.2f,%4.2f) -> (%4d,%4d)  RGBA=%s' % (fx, fy, x, y, px[x, y]))


if __name__ == '__main__':
    main(sys.argv)
