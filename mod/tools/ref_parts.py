#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把参考 mesh 按连通分量拆成部件，输出每块零件的包围盒 / 体积 / 贴图均色。

用法: python tools/ref_parts.py <model.bbmodel> [--align] [--min-tris 8] [--sort z]
"""
import base64
import io
import json
import sys

from PIL import Image


def jacobi3(a):
    import math
    a = [r[:] for r in a]
    v = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
    for _ in range(60):
        if abs(a[0][1]) + abs(a[0][2]) + abs(a[1][2]) < 1e-12:
            break
        for p, q in ((0, 1), (0, 2), (1, 2)):
            if abs(a[p][q]) < 1e-15:
                continue
            th = (a[q][q] - a[p][p]) / (2 * a[p][q])
            t = (1 if th >= 0 else -1) / (abs(th) + math.sqrt(th * th + 1))
            c = 1 / math.sqrt(t * t + 1)
            s = t * c
            for k in range(3):
                kp, kq = a[k][p], a[k][q]
                a[k][p] = c * kp - s * kq
                a[k][q] = s * kp + c * kq
            for k in range(3):
                pk, qk = a[p][k], a[q][k]
                a[p][k] = c * pk - s * qk
                a[q][k] = s * pk + c * qk
            for k in range(3):
                kp, kq = v[k][p], v[k][q]
                v[k][p] = c * kp - s * kq
                v[k][q] = s * kp + c * kq
    return [a[i][i] for i in range(3)], v


def load(path):
    data = json.load(open(path, encoding='utf-8'))
    tex = None
    for t in data.get('textures', []):
        src = t.get('source') or ''
        if src.startswith('data:image'):
            tex = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGBA')
            break
    res = data.get('resolution') or {}
    uw = float(res.get('width') or 16)
    uh = float(res.get('height') or 16)
    verts, tris = [], []
    for el in data.get('elements', []):
        if 'vertices' not in el:
            continue
        keys = list(el['vertices'].keys())
        base = len(verts)
        ki = {k: i for i, k in enumerate(keys)}
        for k in keys:
            v = el['vertices'][k]
            verts.append([v[0], v[1], v[2]])
        for f in el['faces'].values():
            vs = f['vertices']
            uvmap = f.get('uv') or {}
            for i in range(1, len(vs) - 1):
                tri = [vs[0], vs[i], vs[i + 1]]
                uvs = []
                for k in tri:
                    uvp = uvmap.get(k)
                    if uvp and tex:
                        uvs.append((int(round(uvp[0] / uw * tex.size[0])) % tex.size[0],
                                    int(round(uvp[1] / uh * tex.size[1])) % tex.size[1]))
                    else:
                        uvs.append(None)
                tris.append(([ki[k] + base for k in tri], uvs))
    return data, verts, tris, tex


def align(verts, tris):
    import math
    n = len(verts)
    c0 = [sum(p[i] for p in verts) / n for i in range(3)]
    cov = [[0.0] * 3 for _ in range(3)]
    for tri, _u in tris:
        pts = [verts[i] for i in tri]
        ax = [(pts[1][i] + pts[2][i]) / 2 - pts[0][i] for i in range(3)]
        bx = [(pts[2][i] + pts[0][i]) / 2 - pts[1][i] for i in range(3)]
        nx = (ax[1] * bx[2] - ax[2] * bx[1], ax[2] * bx[0] - ax[0] * bx[2], ax[0] * bx[1] - ax[1] * bx[0])
        w = math.sqrt(sum(x * x for x in nx)) / 2
        if w <= 0:
            continue
        m = [sum(pts[k][i] for k in range(3)) / 3 - c0[i] for i in range(3)]
        for i in range(3):
            for j in range(3):
                cov[i][j] += w * m[i] * m[j]
    ev, evec = jacobi3(cov)
    order = sorted(range(3), key=lambda i: -ev[i])
    cols = [[evec[r][i] for r in range(3)] for i in range(3)]
    longv, up, side = cols[order[0]], cols[order[1]], cols[order[2]]
    dot = lambda p, d: p[0] * d[0] + p[1] * d[1] + p[2] * d[2]
    lv = [dot(p, longv) for p in verts]
    lo, hi = min(lv), max(lv)
    mid = [p for p, t in zip(verts, lv) if lo + 0.45 * (hi - lo) <= t <= lo + 0.55 * (hi - lo)]
    mv = sum(dot(p, up) for p in mid) / max(len(mid), 1)
    gv = sum(dot([p[i] - c0[i] for i in range(3)], up) for p in verts) / n
    if gv > mv:
        up = [-x for x in up]
    side = [-x for x in side]
    nv = [[-dot([p[i] - c0[i] for i in range(3)], side), dot([p[i] - c0[i] for i in range(3)], up),
           -dot([p[i] - c0[i] for i in range(3)], longv)] for p in verts]
    zs = [p[2] for p in nv]
    zlo, zhi = min(zs), max(zs)
    band = lambda a, b: (lambda s: (max(p[0] for p in s) - min(p[0] for p in s)) *
                                    (max(p[1] for p in s) - min(p[1] for p in s)))([p for p in nv if a <= p[2] <= b])
    if band(zhi - 0.1 * (zhi - zlo), zhi) < band(zlo, zlo + 0.1 * (zhi - zlo)):
        nv = [[-p[0], p[1], -p[2]] for p in nv]
    return nv


def main():
    path = sys.argv[1]
    do_align = '--align' in sys.argv
    min_tris = 8
    for i, a in enumerate(sys.argv):
        if a == '--min-tris':
            min_tris = int(sys.argv[i + 1])
    data, verts, tris, tex = load(path)
    if do_align:
        verts = align(verts, tris)

    # 并查集：按共享顶点合并三角形
    parent = list(range(len(verts)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    for tri, _u in tris:
        a = tri[0]
        for b in tri[1:]:
            union(a, b)
    comps = {}
    for ti, (tri, uvs) in enumerate(tris):
        comps.setdefault(find(tri[0]), []).append(ti)

    rows = []
    for root, tlist in comps.items():
        if len(tlist) < min_tris:
            continue
        vs = set()
        cols = []
        for ti in tlist:
            tri, uvs = tris[ti]
            vs.update(tri)
            for u in uvs:
                if u and tex:
                    try:
                        px = tex.getpixel(u)
                    except Exception:
                        continue
                    if px[3] > 8:
                        cols.append(px)
        pts = [verts[i] for i in vs]
        bb = [(min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3)]
        avg = (0, 0, 0)
        if cols:
            avg = (int(sum(c[0] for c in cols) / len(cols)), int(sum(c[1] for c in cols) / len(cols)),
                   int(sum(c[2] for c in cols) / len(cols)))
        rows.append({'tris': len(tlist), 'verts': len(vs), 'bb': bb, 'avg': avg,
                     'size': [round(bb[i][1] - bb[i][0], 3) for i in range(3)]})
    rows.sort(key=lambda r: r['bb'][2][0])
    print('components(>=%d tris): %d' % (min_tris, len(rows)))
    print('%-5s %-5s  %-22s %-22s %-22s %-20s %-16s' % ('tris', 'v', 'X lo..hi (w)', 'Y lo..hi (h)', 'Z lo..hi (l)', 'size XYZ', 'avg color'))
    for r in rows:
        bb = r['bb']
        print('%-5d %-5d  %7.3f..%7.3f %7.3f..%7.3f %7.3f..%7.3f  %6.2f %6.2f %6.2f  %-16s' % (
            r['tris'], r['verts'], bb[0][0], bb[0][1], bb[1][0], bb[1][1], bb[2][0], bb[2][1],
            r['size'][0], r['size'][1], r['size'][2],
            '(%3d,%3d,%3d)' % r['avg']))


if __name__ == '__main__':
    main()
