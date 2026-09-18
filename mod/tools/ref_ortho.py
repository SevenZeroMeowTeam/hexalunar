#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""参考模型精确测量：正交三视图（带 1 单位网格）+ 沿长轴的剖面表 + 每段贴图均色。

用法:
    python tools/ref_ortho.py <model.bbmodel> <out_prefix> [--bins 16] [--axis z]

输出:
    <prefix>_side.png   沿 -X 看  (水平=Z, 垂直=Y)
    <prefix>_top.png    沿 -Y 看  (水平=Z, 垂直=X)
    <prefix>_front.png  沿 -Z 看  (水平=X, 垂直=Y)
    <prefix>_tex.png    提取的贴图原图
并打印沿轴分段表: 段号 / 轴范围 / 顶点数 / 另两轴 min..max / 贴图均色
"""
import base64
import io
import json
import sys

from PIL import Image, ImageDraw

LIGHT = (-0.40, 0.80, 0.45)


def jacobi3(a):
    """对称 3x3 的 Jacobi 特征分解，返回 (特征值, 特征向量列)。"""
    import math
    a = [row[:] for row in a]
    v = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
    for _ in range(60):
        off = abs(a[0][1]) + abs(a[0][2]) + abs(a[1][2])
        if off < 1e-12:
            break
        for p, q in ((0, 1), (0, 2), (1, 2)):
            if abs(a[p][q]) < 1e-15:
                continue
            theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
            t = (1 if theta >= 0 else -1) / (abs(theta) + math.sqrt(theta * theta + 1))
            c = 1 / math.sqrt(t * t + 1)
            s = t * c
            for k in range(3):
                akp, akq = a[k][p], a[k][q]
                a[k][p] = c * akp - s * akq
                a[k][q] = s * akp + c * akq
            for k in range(3):
                apk, aqk = a[p][k], a[q][k]
                a[p][k] = c * apk - s * aqk
                a[q][k] = s * apk + c * aqk
            for k in range(3):
                vkp, vkq = v[k][p], v[k][q]
                v[k][p] = c * vkp - s * vkq
                v[k][q] = s * vkp + c * vkq
    return [a[i][i] for i in range(3)], v


def align_frame(verts, tris):
    """PCA 找到枪管轴，返回 (新顶点, 新三角形, 轴名)。约定 前向=-Z, 上=+Y。"""
    import math
    n = len(verts)
    cx = sum(p[0] for p in verts) / n
    cy = sum(p[1] for p in verts) / n
    cz = sum(p[2] for p in verts) / n
    # 按三角形面积加权协方差（更符合"形状"
    cov = [[0.0] * 3 for _ in range(3)]
    for tri, _u in tris:
        pts = [verts[i] for i in tri]
        ax = (pts[1][0] + pts[2][0]) / 2 - pts[0][0]
        ay = (pts[1][1] + pts[2][1]) / 2 - pts[0][1]
        az = (pts[1][2] + pts[2][2]) / 2 - pts[0][2]
        bx = (pts[2][0] + pts[0][0]) / 2 - pts[1][0]
        by = (pts[2][1] + pts[0][1]) / 2 - pts[1][1]
        bz = (pts[2][2] + pts[0][2]) / 2 - pts[1][2]
        nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
        w = math.sqrt(nx * nx + ny * ny + nz * nz) / 2
        if w <= 0:
            continue
        m = [(pts[0][i] + pts[1][i] + pts[2][i]) / 3 - (cx, cy, cz)[i] for i in range(3)]
        for i in range(3):
            for j in range(3):
                cov[i][j] += w * m[i] * m[j]
    ev, evec = jacobi3(cov)
    order = sorted(range(3), key=lambda i: -ev[i])
    cols = [[evec[r][i] for r in range(3)] for i in range(3)]
    longv = cols[order[0]]
    # 剩下两轴中方差大的当作"上"
    up = cols[order[1]] if ev[order[1]] >= ev[order[2]] else cols[order[2]]
    side = cols[order[2]] if ev[order[1]] >= ev[order[2]] else cols[order[1]]
    # 上方向定号：整枪质心在机匣中心之下（弹匣/握把/枪托下沿）
    def dot(p, d):
        return p[0] * d[0] + p[1] * d[1] + p[2] * d[2]
    # 机匣带 = 长轴中间 45%~55%
    lv = [dot(p, longv) for p in verts]
    lo, hi = min(lv), max(lv)
    mid = [p for p, t in zip(verts, lv) if lo + 0.45 * (hi - lo) <= t <= lo + 0.55 * (hi - lo)]
    mv = sum(dot(p, up) for p in mid) / max(len(mid), 1)
    gv = sum(dot((p[0] - cx, p[1] - cy, p[2] - cz), up) for p in verts) / n
    if gv > mv:
        up = [-x for x in up]
    side = [-x for x in side]
    new_v = []
    for p in verts:
        d = (p[0] - cx, p[1] - cy, p[2] - cz)
        # 前向 = -Z  =>  long 映射到 -Z
        new_v.append([-dot(d, side), dot(d, up), -dot(d, longv)])
    # 前向定号：枪口端(截面更细)应在 -Z
    zs = [p[2] for p in new_v]
    zlo, zhi = min(zs), max(zs)
    def band_extent(a, b):
        sel = [p for p in new_v if a <= p[2] <= b]
        if not sel:
            return 1e9
        dx = max(p[0] for p in sel) - min(p[0] for p in sel)
        dy = max(p[1] for p in sel) - min(p[1] for p in sel)
        return dx * dy
    span = zhi - zlo
    thin_lo = band_extent(zlo, zlo + 0.10 * span)
    thin_hi = band_extent(zhi - 0.10 * span, zhi)
    if thin_hi < thin_lo:
        new_v = [[-p[0], p[1], -p[2]] for p in new_v]
    return new_v, tris, ('long', 'up', 'side', order, ev)


def _tri_axis(verts, tri):
    return sum(verts[i][2] for i in tri) / 3.0


def _tri_area(verts, tri):
    pts = [verts[i] for i in tri]
    ax = (pts[1][0] + pts[2][0]) / 2 - pts[0][0]
    ay = (pts[1][1] + pts[2][1]) / 2 - pts[0][1]
    az = (pts[1][2] + pts[2][2]) / 2 - pts[0][2]
    bx = (pts[2][0] + pts[0][0]) / 2 - pts[1][0]
    by = (pts[2][1] + pts[0][1]) / 2 - pts[1][1]
    bz = (pts[2][2] + pts[0][2]) / 2 - pts[1][2]
    nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
    return (nx * nx + ny * ny + nz * nz) ** 0.5 / 2


def load(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    tex = None
    for t in data.get('textures', []):
        src = t.get('source') or ''
        if src.startswith('data:image'):
            tex = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGBA')
            break
    res = data.get('resolution') or {}
    uv_w = float(res.get('width') or 16)
    uv_h = float(res.get('height') or 16)
    verts, tris = [], []
    for el in data.get('elements', []):
        if 'vertices' not in el:
            # cube 型
            frm, to = el['from'], el['to']
            keys = list(el['vertices'].keys()) if 'vertices' in el else []
            continue
        keys = list(el['vertices'].keys())
        base_i = len(verts)
        kidx = {k: i for i, k in enumerate(keys)}
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
                        x = int(round(uvp[0] / uv_w * tex.size[0])) % tex.size[0]
                        y = int(round(uvp[1] / uv_h * tex.size[1])) % tex.size[1]
                        uvs.append((x, y))
                    else:
                        uvs.append(None)
                tris.append(([kidx[k] + base_i for k in tri], uvs))
    return data, verts, tris, tex


def norm(p, q, r):
    ux, uy, uz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
    vx, vy, vz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
    return nx / ln, ny / ln, nz / ln


def sample(tex, xy):
    if tex is None or xy is None:
        return None
    try:
        px = tex.getpixel(xy)
    except Exception:
        return None
    if px[3] < 8:
        return None
    return px


def render_view(verts, tris, tex, hues, horizon, vertical, flip_h, out, title):
    """horizon/vertical = 世界轴索引 (0=X,1=Y,2=Z)；flip_h 是否水平翻转。"""
    SIZE = 1100
    PAD = 46
    hs = [v[horizon] for v in verts]
    vs = [v[vertical] for v in verts]
    lo_h, hi_h = min(hs), max(hs)
    lo_v, hi_v = min(vs), max(vs)
    sh = (SIZE - 2 * PAD) / max(hi_h - lo_h, 1e-6)
    sv = (SIZE - 2 * PAD) / max(hi_v - lo_v, 1e-6)
    sc = min(sh, sv)
    img = Image.new('RGBA', (SIZE, SIZE), (250, 250, 250, 255))
    dr = ImageDraw.Draw(img)

    def proj(p):
        h = (p[horizon] - lo_h) * sc + PAD
        if flip_h:
            h = SIZE - h
        v = SIZE - ((p[vertical] - lo_v) * sc + PAD)
        return (h, v)

    depth_axis = 3 - horizon - vertical
    order = []
    for idx, (tri, uvs) in enumerate(tris):
        pts = [verts[i] for i in tri]
        n = norm(*pts)
        d = abs(n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2])
        d = 0.42 + 0.58 * d
        col = None
        if uvs and uvs[0] is not None:
            col = sample(tex, uvs[0])
        if col is None:
            col = (150, 150, 150, 255)
        c = (int(col[0] * d), int(col[1] * d), int(col[2] * d), 255)
        depth = sum(p[depth_axis] for p in pts) / len(pts)
        order.append((depth, [proj(p) for p in pts], c, idx))
    order.sort(key=lambda t: t[0])
    for _, poly, c, _ in order:
        dr.polygon(poly, fill=c)
    # 网格
    import math
    start = math.floor(lo_h)
    end = math.ceil(hi_h)
    for g in range(int(start), int(end) + 1):
        h = (g - lo_h) * sc + PAD
        if flip_h:
            h = SIZE - h
        if not (PAD - 1 <= h <= SIZE - PAD + 1):
            continue
        major = (g % 5 == 0)
        dr.line([(h, PAD), (h, SIZE - PAD)], fill=(255, 90, 90, 160) if major else (170, 200, 235, 130),
                width=2 if major else 1)
        if major:
            dr.text((h + 3, 6), str(g), fill=(200, 0, 0, 255))
    start = math.floor(lo_v)
    end = math.ceil(hi_v)
    for g in range(int(start), int(end) + 1):
        v = SIZE - ((g - lo_v) * sc + PAD)
        if not (PAD - 1 <= v <= SIZE - PAD + 1):
            continue
        major = (g % 5 == 0)
        dr.line([(PAD, v), (SIZE - PAD, v)], fill=(255, 90, 90, 160) if major else (170, 200, 235, 130),
                width=2 if major else 1)
        if major:
            dr.text((6, v - 12), str(g), fill=(200, 0, 0, 255))
    dr.text((PAD, PAD - 16), title, fill=(0, 0, 0, 255))
    img.convert('RGB').save(out)
    return img


def main():
    path = sys.argv[1]
    prefix = sys.argv[2]
    bins = 16
    axis = 2
    for i, a in enumerate(sys.argv):
        if a == '--bins':
            bins = int(sys.argv[i + 1])
        if a == '--axis':
            axis = 'XYZ'.index(sys.argv[i + 1].upper())
    data, verts, tris, tex = load(path)
    if '--align' in sys.argv:
        verts, tris, info = align_frame(verts, tris)
        print('aligned (PCA). eigen order', info[3], ['%.4f' % e for e in info[4]])
        # 输出对齐后的网格，方便后续分解
        out = prefix + '_aligned.json'
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump({'verts': [[round(c, 5) for c in p] for p in verts]}, fh)
        print('wrote', out)
    print('verts %d  tris %d  tex %s' % (len(verts), len(tris), tex.size if tex else None))
    for i, n in enumerate('XYZ'):
        v = [p[i] for p in verts]
        print('%s  %8.3f .. %8.3f   span %7.3f' % (n, min(v), max(v), max(v) - min(v)))
    # 剖面表
    vals = [p[axis] for p in verts]
    lo, hi = min(vals), max(vals)
    step = (hi - lo) / bins
    other = [i for i in range(3) if i != axis]
    print()
    print('%-4s %-14s %7s %9s %9s %9s %9s  %-18s' % (
        'bin', 'range', 'vert', '%s min' % 'XYZ'[other[0]], '%s max' % 'XYZ'[other[0]],
        '%s min' % 'XYZ'[other[1]], '%s max' % 'XYZ'[other[1]], 'avg tex color'))
    for b in range(bins):
        a = lo + b * step
        z = lo + (b + 1) * step
        sel = [v for v in verts if (a <= v[axis] < z) or (b == bins - 1 and v[axis] == hi)]
        if not sel:
            print('%-4d %-14s %7d' % (b, '%.2f..%.2f' % (a, z), 0))
            continue
        o0 = [v[other[0]] for v in sel]
        o1 = [v[other[1]] for v in sel]
        # 该段内三角形的贴图均色
        cols = []
        for tri, uvs in tris:
            c = sum(verts[i][axis] for i in tri) / 3.0
            if a <= c < z or (b == bins - 1 and c <= hi):
                for u in uvs:
                    px = sample(tex, u)
                    if px:
                        cols.append(px)
        avg = ''
        if cols:
            r = sum(c[0] for c in cols) / len(cols)
            g = sum(c[1] for c in cols) / len(cols)
            bl = sum(c[2] for c in cols) / len(cols)
            avg = '(%3d,%3d,%3d)' % (r, g, bl)
        print('%-4d %-14s %7d %9.2f %9.2f %9.2f %9.2f  %-18s' % (
            b, '%.2f..%.2f' % (a, z), len(sel), min(o0), max(o0), min(o1), max(o1), avg))
    if tex is not None:
        tex.save(prefix + '_tex.png')
    render_view(verts, tris, tex, None, 2, 1, False, prefix + '_side.png',
                'SIDE  view along -X   horiz=Z  vert=Y')
    render_view(verts, tris, tex, None, 2, 0, False, prefix + '_top.png',
                'TOP   view along -Y   horiz=Z  vert=X')
    render_view(verts, tris, tex, None, 0, 1, False, prefix + '_front.png',
                'FRONT view along -Z   horiz=X  vert=Y')
    print('wrote', prefix + '_{side,top,front,tex}.png')


if __name__ == '__main__':
    main()
