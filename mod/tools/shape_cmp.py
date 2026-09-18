#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""比较 bbmodel 与 obj 是否真的是同一个形状（旋转不变指纹 / 顶点数）。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import north_align as na  # noqa: E402


def fingerprint(pts):
    c = pts.mean(axis=0)
    r = np.linalg.norm(pts - c, axis=1)
    q = [10, 25, 50, 75, 90, 99, 100]
    return [float(np.percentile(r, k)) for k in q]


def main():
    for name, cfg in na.MODELS.items():
        bb = na.load_bb(cfg['bb'])[1]
        lines, idx, obj = na.read_obj(os.path.join(na.ITEM, cfg['obj']))
        uq_bb = np.unique(np.round(bb, 3), axis=0)
        uq_obj = np.unique(np.round(obj * 16.0, 3), axis=0)
        fb = fingerprint(uq_bb)
        fo = fingerprint(uq_obj)
        print('%-14s 顶点 %6d / %6d   ' % (name, len(uq_bb), len(uq_obj))
              + '半径分位 bb=%s' % ' '.join('%.1f' % x for x in fb))
        print('%-14s                    obj=%s'
              % ('', ' '.join('%.1f' % x for x in fo)))


if __name__ == '__main__':
    main()
