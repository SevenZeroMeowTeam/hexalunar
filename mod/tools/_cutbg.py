#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把离线预览图的纯色背景换成深色（白色武器在浅灰背景上几乎看不见）。

用法: python tools/_cutbg.py <in.png> <out.png> [bg_r,bg_g,bg_b=auto] [tol=10]
      bg 省略时取左上角像素当作背景色。
"""
import os
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main(argv):
    src, dst = argv[1], argv[2]
    im = np.array(Image.open(src).convert('RGB')).astype(np.int16)
    bg = np.array([int(v) for v in argv[3].split(',')]) if len(argv) > 3 \
        else im[2, 2].copy()
    tol = int(argv[4]) if len(argv) > 4 else 10
    mask = (np.abs(im - bg).max(axis=2) <= tol)
    im[mask] = (26, 26, 30)
    Image.fromarray(im.astype(np.uint8)).save(dst)
    print('wrote %s  bg=%s  changed=%.1f%%' % (os.path.basename(dst), tuple(bg),
                                               100.0 * mask.mean()))


if __name__ == '__main__':
    main(sys.argv)
