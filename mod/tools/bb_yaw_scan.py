#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""暴力搜索让网格长轴对齐 +Z 的 Y 轴旋转角（按包围盒最小体积/最大 Z 跨度判定）。"""
import json
import math
import sys


def main(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    verts = list(data['elements'][0]['vertices'].values())
    best = []
    for i in range(0, 1800):
        yaw = -90 + i * 0.1
        a = math.radians(yaw)
        ca, sa = math.cos(a), math.sin(a)
        xs = [v[0] * ca + v[2] * sa for v in verts]
        zs = [-v[0] * sa + v[2] * ca for v in verts]
        ys = [v[1] for v in verts]
        sx, sy, sz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
        best.append((sz, sx, sy, yaw, min(xs), max(xs), min(zs), max(zs), min(ys), max(ys)))
    best.sort(reverse=True)
    print('按 Z 跨度最大的前 6 个角度:')
    for b in best[:6]:
        print('  yaw=%7.2f  X=%.3f Y=%.3f Z=%.3f   X[%.2f..%.2f] Z[%.2f..%.2f]' % (
            b[3], b[1], b[2], b[0], b[4], b[5], b[6], b[7]))


if __name__ == '__main__':
    main(sys.argv[1])
