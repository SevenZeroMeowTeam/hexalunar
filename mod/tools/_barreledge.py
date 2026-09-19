#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""量「枪管上沿」：逐列取最上面的武器像素，再最小二乘拟合直线 → 得到枪管在屏幕上的倾角。

用法: python tools/_barreledge.py <png> <x0> <x1> <y0> <y1> <dark|light> [step=20]
输出: 每列的上沿 y、拟合斜率、倾角（度）、以及 y 随 x 的关系式
"""
import os
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main(argv):
    png = argv[1]
    x0, x1, y0, y1 = (int(argv[i]) for i in (2, 3, 4, 5))
    mode = argv[6]
    step = int(argv[7]) if len(argv) > 7 else 20

    im = np.array(Image.open(png).convert('RGB')).astype(np.int16)
    sub = im[y0:y1, x0:x1]
    mx = sub.max(axis=2)
    mn = sub.min(axis=2)
    mask = (mx < 70) if mode == 'dark' else ((mn > 195) & ((mx - mn) < 45))

    xs, ys = [], []
    for i in range(0, sub.shape[1], step):
        col = np.nonzero(mask[:, i])[0]
        if len(col) == 0:
            continue
        xs.append(x0 + i)
        ys.append(y0 + int(col[0]))
    if len(xs) < 3:
        print('%s: 有效列太少' % os.path.basename(png))
        return
    print('%s  %s  上沿点: %s' % (os.path.basename(png), mode,
                                  ' '.join('(%d,%d)' % (a, b) for a, b in zip(xs, ys))))
    k, b = np.polyfit(xs, ys, 1)
    print('  拟合 y = %.3f x + %.1f   → 屏幕倾角 %.1f°（正 = 远端在上）'
          % (k, b, np.degrees(np.arctan(-k))))


if __name__ == '__main__':
    main(sys.argv)
