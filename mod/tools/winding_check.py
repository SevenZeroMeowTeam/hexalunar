#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查 mesh 面的顶点顺序是否是“从外侧看逆时针”(CCW-outward)。

对每个三角面用右手定则算法线，与「面心 - 网格中心」比较，统计朝外比例。
用法: python tools/winding_check.py <model.bbmodel> [model.obj]
"""
import json
import sys


def tri_normal(a, b, c):
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def report(name, verts, tris):
    if not verts or not tris:
        print(name, 'no data')
        return
    cx = [sum(v[i] for v in verts) / len(verts) for i in range(3)]
    pos = neg = 0
    for idx in tris:
        a, b, c = (verts[i] for i in idx)
        n = tri_normal(a, b, c)
        mid = [(a[i] + b[i] + c[i]) / 3 - cx[i] for i in range(3)]
        d = dot(n, mid)
        if d > 0:
            pos += 1
        elif d < 0:
            neg += 1
    print('%s: faces=%d 朝外(CCW)=%d (%.1f%%)  朝内=%d (%.1f%%)' % (
        name, len(tris), pos, 100.0 * pos / max(1, pos + neg), neg, 100.0 * neg / max(1, pos + neg)))


def from_bbmodel(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    el = data['elements'][0]
    keys = list(el['vertices'].keys())
    kidx = {k: i for i, k in enumerate(keys)}
    verts = [el['vertices'][k] for k in keys]
    tris = []
    for f in el['faces'].values():
        vs = f['vertices']
        for i in range(1, len(vs) - 1):
            tris.append([kidx[vs[0]], kidx[vs[i]], kidx[vs[i + 1]]])
    report('bbmodel ' + path, verts, tris)


def from_obj(path):
    verts = []
    tris = []
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if line.startswith('v '):
                p = line.split()
                verts.append([float(p[1]), float(p[2]), float(p[3])])
            elif line.startswith('f '):
                p = line.split()[1:]
                idx = [int(x.split('/')[0]) - 1 for x in p]
                for i in range(1, len(idx) - 1):
                    tris.append([idx[0], idx[i], idx[i + 1]])
    report('obj ' + path, verts, tris)


if __name__ == '__main__':
    from_bbmodel(sys.argv[1])
    if len(sys.argv) > 2:
        from_obj(sys.argv[2])
