# -*- coding: utf-8 -*-
"""把任意图按矩形裁剪放大（看参考照片细节用）。

用法::  python tools/_cropimg.py <src> <x0> <y0> <x1> <y1> [scale] [out]
"""
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    a = sys.argv
    src = a[1] if not os.path.isabs(a[1]) else a[1]
    if not os.path.exists(src):
        src = os.path.join(ROOT, a[1])
    x0, y0, x1, y1 = (int(a[i]) for i in (2, 3, 4, 5))
    scale = int(a[6]) if len(a) > 6 else 3
    out = a[7] if len(a) > 7 else os.path.join(ROOT, 'build', '_crop.png')
    im = Image.open(src)
    box = (max(0, x0), max(0, y0), min(im.width, x1), min(im.height, y1))
    im2 = im.crop(box).resize(((box[2] - box[0]) * scale, (box[3] - box[1]) * scale),
                             Image.NEAREST)
    im2.save(out)
    print('src %dx%d crop %s -> %s %dx%d' % (im.width, im.height, box,
                                             os.path.relpath(out, ROOT),
                                             im2.width, im2.height))


if __name__ == '__main__':
    main()
