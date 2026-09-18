#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对参考 mesh 做「空间裁剪 + 连通分量」拆件：只保留落在给定区域的三角形，再分连通块。

用法: python tools/ref_split.py <model.bbmodel> --box x0,x1,y0,y1,z0,z1 [--min-tris 20]
"""
import sys

sys.path.insert(0, 'tools')
from ref_parts import load  # noqa: E402


def main():
    path = sys.argv[1]
    box = None
    mn = 20
    for i, a in enumerate(sys.argv):
        if a == '--box':
            box = [float(v) for v in sys.argv[i + 1].split(',')]
        if a == '--min-tris':
            mn = int(sys.argv[i + 1])
    _d, verts, tris, _tex = load(path)
    if box:
        keep = []
        for tri, uv in tris:
            pts = [verts[i] for i in tri]
            cx = sum(p[0] for p in pts) / 3
            cy = sum(p[1] for p in pts) / 3
            cz = sum(p[2] for p in pts) / 3
            if box[0] <= cx <= box[1] and box[2] <= cy <= box[3] and box[4] <= cz <= box[5]:
                keep.append((tri, uv))
        tris = keep
        print('kept tris', len(tris))
    # 按共享顶点并查集
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for tri, _u in tris:
        for b in tri[1:]:
            union(tri[0], b)
    groups = {}
    for tri, _u in tris:
        groups.setdefault(find(tri[0]), []).append(tri)
    rows = sorted(groups.values(), key=lambda g: -len(g))
    print('components: %d (展示 >=%d tris)' % (len(rows), mn))
    for g in rows:
        if len(g) < mn:
            continue
        ids = sorted({i for tri in g for i in tri})
        pts = [verts[i] for i in ids]
        bb = [(min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3)]
        c = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
        print('  tris=%-5d X %7.2f..%7.2f Y %7.2f..%7.2f Z %7.2f..%7.2f   size %5.2f x %5.2f x %5.2f   c=(%.2f,%.2f,%.2f)'
              % (len(g), bb[0][0], bb[0][1], bb[1][0], bb[1][1], bb[2][0], bb[2][1],
                 bb[0][1] - bb[0][0], bb[1][1] - bb[1][0], bb[2][1] - bb[2][0], c[0], c[1], c[2]))


if __name__ == '__main__':
    main()
