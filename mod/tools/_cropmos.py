# -*- coding: utf-8 -*-
"""把 build/_mos_cur_<view>.png 的指定矩形裁出来放大，方便看细节。

用法::  python tools/_cropmos.py <view> <x0> <y0> <x1> <y1> [scale] [out]
"""
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    a = sys.argv
    view = a[1] if len(a) > 1 else 'side'
    x0, y0, x1, y1 = (int(a[i]) for i in (2, 3, 4, 5))
    scale = int(a[6]) if len(a) > 6 else 3
    src = os.path.join(ROOT, 'build', '_mos_cur_%s.png' % view)
    out = a[7] if len(a) > 7 else os.path.join(ROOT, 'build', '_mos_crop_%s.png' % view)
    im = Image.open(src)
    box = (max(0, x0), max(0, y0), min(im.width, x1), min(im.height, y1))
    im = im.crop(box).resize(((box[2] - box[0]) * scale, (box[3] - box[1]) * scale),
                            Image.NEAREST)
    im.save(out)
    print('src %dx%d  crop %s -> %s  %dx%d' % (Image.open(src).size[0],
                                               Image.open(src).size[1], box,
                                               os.path.relpath(out, ROOT),
                                               im.width, im.height))


if __name__ == '__main__':
    main()
