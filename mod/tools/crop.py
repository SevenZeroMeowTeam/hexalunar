"""放大裁剪贴图的一块区域，用于肉眼核对印字/细节。

用法: python tools/crop.py <png> <x0> <y0> <x1> <y1> <out> [scale]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    src, x0, y0, x1, y1, out = argv[1], int(argv[2]), int(argv[3]), int(argv[4]), \
        int(argv[5]), argv[6]
    sc = int(argv[7]) if len(argv) > 7 else 6
    im = Image.open(os.path.join(ROOT, src)).convert('RGB')
    c = im.crop((x0, y0, x1, y1))
    c = c.resize((c.width * sc, c.height * sc), Image.NEAREST)
    dst = os.path.join(ROOT, out)
    c.save(dst)
    print('wrote %s  %dx%d -> %dx%d' % (out, x1 - x0, y1 - y0, c.width, c.height))


if __name__ == '__main__':
    main(sys.argv)
