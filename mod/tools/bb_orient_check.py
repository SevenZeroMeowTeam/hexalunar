#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""判断一个 bbmodel 在工程坐标系里的朝向：扫 Y 轴旋转找“长轴对齐 Z”的角度，
再报告对齐后宽端（弓臂）落在 +Z 还是 -Z。

用法: python tools/bb_orient_check.py <model.bbmodel> [...]
"""
import json
import math
import sys


def load_verts(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    vs = []
    for el in data.get('elements', []):
        vs += [tuple(v) for v in el['vertices'].values()]
    return vs


def rot(pts, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(x * ca + z * sa, y, -x * sa + z * ca) for (x, y, z) in pts]


def main(paths):
    for p in paths:
        pts = load_verts(p)
        best = None
        for i in range(0, 3600):
            ang = -180 + i * 0.1
            rp = rot(pts, ang)
            sz = max(v[2] for v in rp) - min(v[2] for v in rp)
            sx = max(v[0] for v in rp) - min(v[0] for v in rp)
            if best is None or sz > best[0]:
                best = (sz, ang, sx)
        sz, ang, sx = best
        rp = rot(pts, ang)
        zs = sorted(v[2] for v in rp)
        z0, z1 = zs[0], zs[-1]
        front = [v for v in rp if v[2] > z1 - (z1 - z0) / 3]
        rear = [v for v in rp if v[2] < z0 + (z1 - z0) / 3]
        fw = (max(v[0] for v in front) - min(v[0] for v in front)) if front else 0
        rw = (max(v[0] for v in rear) - min(v[0] for v in rear)) if rear else 0
        print('%s\n  对齐角 yaw=%7.2f  Z跨度=%.2f X跨度=%.2f | +Z端X宽=%.2f  -Z端X宽=%.2f -> 宽端(弓臂)在 %s'
              % (p, ang, sz, sx, fw, rw, '+Z' if fw > rw else '-Z'))


if __name__ == '__main__':
    main(sys.argv[1:])
