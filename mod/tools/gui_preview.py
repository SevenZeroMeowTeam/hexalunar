#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按 Minecraft 的物品显示变换把 forge:obj 模型渲染成 GUI 预览图。

用法: python tools/gui_preview.py <item.json> <out.png> [slot] [size]
例如: python tools/gui_preview.py src/.../models/item/crossbow.json build/preview/gui_new.png gui 256

变换与 ItemRenderer 一致：v' = T(0.5) ∘ [ T(t/16) ∘ Rx ∘ Ry ∘ Rz ∘ S ] ∘ T(-0.5) ∘ v
GUI 投影：screen = (16*x'+8, -(16*y'+8))，正交画家算法。
"""
import json
import math
import os
import re
import sys

from PIL import Image, ImageDraw

LIGHT = (-0.35, 0.62, -0.70)


def load_obj(path):
    verts, vts, tris = [], [], []
    cur_vt = []
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if line.startswith('v '):
                p = line.split()
                verts.append([float(p[1]), float(p[2]), float(p[3])])
            elif line.startswith('vt '):
                p = line.split()
                vts.append([float(p[1]), float(p[2])])
            elif line.startswith('f '):
                corners = []
                for tok in line.split()[1:]:
                    a = tok.split('/')
                    vi = int(a[0]) - 1
                    ti = int(a[1]) - 1 if len(a) > 1 and a[1] else 0
                    corners.append((vi, ti))
                for k in range(1, len(corners) - 1):
                    tris.append([corners[0], corners[k], corners[k + 1]])
            elif line.startswith('mtllib'):
                cur_vt.append(line.strip().split()[1])
    return verts, vts, tris, (cur_vt[0] if cur_vt else None)


def load_tex(json_path, mtl_name):
    base = os.path.dirname(json_path)
    assets = os.path.abspath(os.path.join(base, '..', '..'))
    p = os.path.join(assets, 'textures', 'models', 'crossbow.png')
    if os.path.exists(p):
        return Image.open(p).convert('RGBA')
    return None


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return lambda v: (v[0], c * v[1] - s * v[2], s * v[1] + c * v[2])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return lambda v: (c * v[0] + s * v[2], v[1], -s * v[0] + c * v[2])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return lambda v: (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])


def main(json_path, out, slot='gui', size=256, zoom=6):
    with open(json_path, 'r', encoding='utf-8') as fh:
        spec = json.load(fh)
    disp = (spec.get('display') or {}).get(slot) or {}
    rot = disp.get('rotation') or [0, 0, 0]
    tra = [(x / 16.0) for x in (disp.get('translation') or [0, 0, 0])]
    sca = disp.get('scale') or [1, 1, 1]
    obj_rel = spec['model'].split(':')[-1]          # models/item/crossbow.obj
    obj_path = os.path.join(os.path.dirname(json_path), os.path.basename(obj_rel))
    verts, vts, tris, mtl = load_obj(obj_path)
    tex = load_tex(json_path, mtl)
    print('slot=%s rot=%s tra=%s sca=%s verts=%d tris=%d tex=%s' % (
        slot, rot, tra, sca, len(verts), len(tris), tex.size if tex else None))
    rx, ry, rz = (math.radians(a) for a in rot)
    fx, fy, fz = rot_x(rx), rot_y(ry), rot_z(rz)

    def xform(v):
        p = (v[0] - 0.5, v[1] - 0.5, v[2] - 0.5)
        p = (p[0] * sca[0], p[1] * sca[1], p[2] * sca[2])
        p = fx(p)
        p = fy(p)
        p = fz(p)
        return (p[0] + 0.5 + tra[0], p[1] + 0.5 + tra[1], p[2] + 0.5 + tra[2])

    tv = [xform(v) for v in verts]
    s = size / 16.0 * zoom / 6.0
    ox = size / 2.0
    oy = size / 2.0

    def proj(p):
        return (ox + (p[0] - 0.5) * 16 * s, oy - (p[1] - 0.5) * 16 * s)

    img = Image.new('RGBA', (size, size), (26, 27, 31, 255))
    d = ImageDraw.Draw(img)
    order = []
    for tri in tris:
        a, b, c = (tv[i] for i, _ in tri)
        u = [b[i] - a[i] for i in range(3)]
        w = [c[i] - a[i] for i in range(3)]
        n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
        ln = math.sqrt(sum(x * x for x in n)) or 1.0
        n = [x / ln for x in n]
        depth = (a[2] + b[2] + c[2]) / 3
        order.append((depth, [a, b, c], n, tri))
    order.sort(key=lambda t: t[0])
    for _, pts, n, tri in order:
        cols = []
        for _, ti in tri:
            if tex and ti < len(vts):
                u, v = vts[ti]
                x = int(round(u * tex.size[0])) % tex.size[0]
                y = int(round((1.0 - v) * tex.size[1])) % tex.size[1]
                cols.append(tex.getpixel((x, y))[:3])
            else:
                cols.append((170, 170, 175))
        col = tuple(sum(c[i] for c in cols) // len(cols) for i in range(3))
        sh = max(0.0, -(n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]))
        f = 0.62 + 0.62 * sh
        col = tuple(min(255, int(c * f)) for c in col)
        d.polygon([proj(p) for p in pts], fill=col + (255,))
    img.convert('RGB').save(out)
    print('wrote', out)


if __name__ == '__main__':
    a = sys.argv[1:]
    main(a[0], a[1], a[2] if len(a) > 2 else 'gui', int(a[3]) if len(a) > 3 else 256)
