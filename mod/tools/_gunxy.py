#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在游戏截图里量出「武器轮廓」的范围，用来客观比较不同武器的持枪位置/角度。

判定：dark = 三通道最大值 < 70；light = 最小值 > 195 且彩度低（AWP 的白色印花）。
白色天空是蓝的（彩度高）会被彩度判据排除。

用法: python tools/_gunxy.py <png> <x0,y0,x1,y1> <dark|light|both> [min_luma=70]
输出: bbox、像素数、质心、以及「主方向」（对轮廓做 PCA 得到的长轴角度，屏幕坐标：0=水平）
"""
import os
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main(argv):
    png = argv[1]
    x0, y0, x1, y1 = [int(v) for v in argv[2].split(',')]
    mode = argv[3]
    thr = int(argv[4]) if len(argv) > 4 else 70

    im = np.array(Image.open(png).convert('RGB')).astype(np.int16)
    sub = im[y0:y1, x0:x1]
    mx = sub.max(axis=2)
    mn = sub.min(axis=2)
    dark = mx < thr
    light = (mn > 195) & ((mx - mn) < 45)
    mask = {'dark': dark, 'light': light, 'both': (dark | light)}[mode]

    ys, xs = np.nonzero(mask)
    if len(xs) < 50:
        print('%s: 没找到武器像素（%d）' % (os.path.basename(png), len(xs)))
        return
    gx = xs + x0
    gy = ys + y0
    print('%s  mode=%s  像素=%d' % (os.path.basename(png), mode, len(xs)))
    print('  bbox x[%d,%d] y[%d,%d]   质心 (%.0f,%.0f)'
          % (gx.min(), gx.max(), gy.min(), gy.max(), gx.mean(), gy.mean()))
    # PCA：轮廓主方向（屏幕坐标，+x 右 / +y 下，角度取「朝左上为正」的等效写法）
    pts = np.stack([gx - gx.mean(), -(gy - gy.mean())], axis=1).astype(np.float64)
    cov = pts.T @ pts / len(pts)
    w, v = np.linalg.eigh(cov)
    d = v[:, int(np.argmax(w))]
    if d[0] < 0:
        d = -d
    ang = np.degrees(np.arctan2(d[1], d[0]))
    print('  长轴方向: %.1f°（相对水平，向上为正）  伸长比 %.2f'
          % (ang, np.sqrt(w.max() / max(w.min(), 1e-6))))


if __name__ == '__main__':
    main(sys.argv)
