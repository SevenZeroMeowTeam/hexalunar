#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 mesh 型 bbmodel（多元素）渲染成带光照的预览图。

用法: python tools/preview.py <model.bbmodel> <out_prefix> [--yaw deg] [--grid]
输出 <prefix>_iso.png / _side.png / _top.png / _front.png / _tex.png
"""
import base64
import io
import json
import math
import os
import sys

from PIL import Image, ImageDraw

LIGHT = (-0.42, 0.78, 0.46)


def load(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    verts, tris = [], []
    tex = None
    for t in data.get('textures', []):
        src = t.get('source') or ''
        if src.startswith('data:image'):
            tex = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGBA')
            break
    uv_w = float((data.get('resolution') or {}).get('width') or 16)
    uv_h = float((data.get('resolution') or {}).get('height') or 16)
    for el in data.get('elements', []):
        keys = list(el['vertices'].keys())
        base_i = len(verts)
        kidx = {k: i for i, k in enumerate(keys)}
        for k in keys:
            v = el['vertices'][k]
            verts.append([v[0], v[1], v[2]])
        for f in el['faces'].values():
            vs = f['vertices']
            for i in range(1, len(vs) - 1):
                tri = [vs[0], vs[i], vs[i + 1]]
                uvs = []
                for k in tri:
                    uvp = (f.get('uv') or {}).get(k)
                    if uvp:
                        x = int(round(uvp[0] / uv_w * tex.size[0])) % tex.size[0] if tex else 0
                        y = int(round(uvp[1] / uv_h * tex.size[1])) % tex.size[1] if tex else 0
                        uvs.append((x, y))
                    else:
                        uvs.append((0, 0))
                tris.append(([kidx[k] + base_i for k in tri], uvs))
    return data, verts, tris, tex


def rotate(pts, yaw, pitch, center):
    ya, pa = math.radians(yaw), math.radians(pitch)
    cy, sy = math.cos(ya), math.sin(ya)
    cp, sp = math.cos(pa), math.sin(pa)
    out = []
    for p in pts:
        x, y, z = p[0] - center[0], p[1] - center[1], p[2] - center[2]
        x, z = cy * x + sy * z, -sy * x + cy * z
        y, z = cp * y - sp * z, sp * y + cp * z
        out.append((x, y, z))
    return out


def shade(n, tex_col):
    d = max(0.0, -(n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]))
    f = 0.60 + 0.58 * d
    return (min(255, int(tex_col[0] * f)), min(255, int(tex_col[1] * f)),
            min(255, int(tex_col[2] * f)), 255)


def render(verts, tris, tex, out, yaw=-35.0, pitch=20.0, size=900, margin=24, draw_grid=False):
    lo = [min(v[i] for v in verts) for i in range(3)]
    hi = [max(v[i] for v in verts) for i in range(3)]
    center = [(lo[i] + hi[i]) / 2 for i in range(3)]
    rp = rotate(verts, yaw, pitch, center)
    xs = [p[0] for p in rp]
    ys = [p[1] for p in rp]
    spanx, spany = max(xs) - min(xs), max(ys) - min(ys)
    scale = min((size - 2 * margin) / max(spanx, 1e-6), (size - 2 * margin) / max(spany, 1e-6))
    ox = margin + ((size - 2 * margin) - spanx * scale) / 2
    oy = margin + ((size - 2 * margin) - spany * scale) / 2
    px = lambda p: (ox + (p[0] - min(xs)) * scale, size - (oy + (p[1] - min(ys)) * scale))
    img = Image.new('RGBA', (size, size), (247, 247, 243, 255))
    d = ImageDraw.Draw(img)
    order = []
    for tri, uvs in tris:
        a, b, c = (rp[i] for i in tri)
        n = (0.0, 0.0, 0.0)
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        ln = math.sqrt(sum(x * x for x in n)) or 1.0
        n = tuple(x / ln for x in n)
        depth = (a[2] + b[2] + c[2]) / 3
        order.append((depth, [a, b, c], n, uvs))
    order.sort(key=lambda t: t[0])
    for _, pts, n, uvs in order:
        cols = []
        for (x, y) in uvs:
            if tex:
                cols.append(tex.getpixel((min(x, tex.size[0] - 1), min(y, tex.size[1] - 1))))
            else:
                cols.append((180, 180, 180, 255))
        col = tuple(sum(c[i] for c in cols) // len(cols) for i in range(3))
        d.polygon([px(p) for p in pts], fill=shade(n, col))
    if draw_grid:
        for i in range(1, int(hi[1] - lo[1]) + 1):
            y = lo[1] + i
            pts = [(lo[0], y, lo[2]), (hi[0], y, lo[2])]
            r = rotate(pts, yaw, pitch, center)
            d.line([px(r[0]), px(r[1])], fill=(210, 210, 205))
    img.convert('RGB').save(out)
    return out


def main():
    path, prefix = sys.argv[1], sys.argv[2]
    yaw = -35.0
    if '--yaw' in sys.argv:
        yaw = float(sys.argv[sys.argv.index('--yaw') + 1])
    data, verts, tris, tex = load(path)
    os.makedirs(os.path.dirname(prefix) or '.', exist_ok=True)
    if tex:
        tex.convert('RGB').save(prefix + '_tex.png')
    render(verts, tris, tex, prefix + '_iso.png', yaw, 22.0)
    render(verts, tris, tex, prefix + '_side.png', 90.0, 0.0)
    render(verts, tris, tex, prefix + '_top.png', 0.0, 89.0)
    render(verts, tris, tex, prefix + '_front.png', 0.0, 0.0)
    print('rendered %s (elements=%d tris=%d)' % (prefix, len(data.get('elements', [])), len(tris)))


if __name__ == '__main__':
    main()
