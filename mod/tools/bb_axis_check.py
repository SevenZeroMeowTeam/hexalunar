#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比 bbmodel 网格与导出 OBJ 的坐标范围，并做主成分分析（找长轴/宽轴朝向）。"""
import json
import math
import sys


def pca(pts):
    n = len(pts)
    mean = [sum(p[i] for p in pts) / n for i in range(3)]
    cov = [[0.0] * 3 for _ in range(3)]
    for p in pts:
        d = [p[i] - mean[i] for i in range(3)]
        for i in range(3):
            for j in range(3):
                cov[i][j] += d[i] * d[j]
    for i in range(3):
        for j in range(3):
            cov[i][j] /= n
    # 幂迭代求最大特征向量
    v = [1.0, 0.5, 0.2]
    for _ in range(200):
        w = [sum(cov[i][j] * v[j] for j in range(3)) for i in range(3)]
        norm = math.sqrt(sum(x * x for x in w)) or 1.0
        v = [x / norm for x in w]
    return mean, v


def main(bbmodel, obj=None):
    with open(bbmodel, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    el = data['elements'][0]
    verts = list(el['vertices'].values())
    lo = [min(v[i] for v in verts) for i in range(3)]
    hi = [max(v[i] for v in verts) for i in range(3)]
    print('bbmodel verts=%d  min=%s max=%s size=%s' % (
        len(verts), [round(x, 3) for x in lo], [round(x, 3) for x in hi],
        [round(hi[i] - lo[i], 3) for i in range(3)]))
    mean, v = pca(verts)
    print('  element rotation=%s origin=%s' % (el.get('rotation'), el.get('origin')))
    print('  长轴方向(PCA) = [%.3f, %.3f, %.3f]  长度轴与 +Z 夹角=%.1f° 与 +X 夹角=%.1f°' % (
        v[0], v[1], v[2],
        math.degrees(math.acos(min(1, abs(v[2])))),
        math.degrees(math.acos(min(1, abs(v[0]))))))
    if obj:
        vs = []
        with open(obj, 'r', encoding='utf-8', errors='replace') as fh:
            for line in fh:
                if line.startswith('v '):
                    parts = line.split()
                    vs.append([float(parts[1]), float(parts[2]), float(parts[3])])
        if vs:
            olo = [min(v[i] for v in vs) for i in range(3)]
            ohi = [max(v[i] for v in vs) for i in range(3)]
            print('obj verts=%d  min=%s max=%s size=%s' % (
                len(vs), [round(x, 3) for x in olo], [round(x, 3) for x in ohi],
                [round(ohi[i] - olo[i], 3) for i in range(3)]))
            print('  ratio to bbmodel = %s' % [round((ohi[i] - olo[i]) / max(1e-9, hi[i] - lo[i]), 3) for i in range(3)])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
