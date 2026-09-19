#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把两张图按比例混合（用来对齐「离线第一人称预览」与「游戏截图」）。

用法: python tools/_blend2.py <a.png> <b.png> <out.png> [alpha=0.5]
      alpha 越大越偏向 b。
"""
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main(argv):
    a = Image.open(argv[1]).convert('RGBA')
    b = Image.open(argv[2]).convert('RGBA')
    if a.size != b.size:
        b = b.resize(a.size)
    al = float(argv[4]) if len(argv) > 4 else 0.5
    Image.blend(a, b, al).convert('RGB').save(argv[3])
    print('wrote %s  %dx%d' % (os.path.basename(argv[3]), a.size[0], a.size[1]))


if __name__ == '__main__':
    main(sys.argv)
