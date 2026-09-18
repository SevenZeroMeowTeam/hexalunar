#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 模型/十字弩.bbmodel（原始静态网格）和 build/_mine.geo.json（新建方块模型）
在同一正交投影下并排渲染，用于逐视图比对形状。

用法: python tools/compare.py
输出: build/cmp_<view>.png
"""
import base64
import io
import json
import math
import os

from PIL import Image, ImageDraw

TEX_MINE = 'src/main/resources/assets/hexalunar_calamity/textures/item/crossbow_geo.png'
SIZE = 520


def load_bbmodel(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    el = data['elements'][0]
    verts = el['vertices']
    tris = []
    uv_w = (data.get('resolution') or {}).get('width', 16) or 16
    uv_h = (data.get('resolution') or {}).get('height', 16) or 16
    tex = None
    for t in data.get('textures', []):
        src = t.get('source') or ''
        if src.startswith('data:image'):
            tex = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGBA')
            break
    px = tex.load() if tex else None
    tw, th = tex.size if tex else (uv_w, uv_h)
    for f in el['faces'].values():
        vs = f['vertices']
        if len(vs) < 3:
            continue
        uvmap = f.get('uv') or {}
        col = (150, 150, 155, 255)
        if uvmap and px:
            us = [p[0] for p in uvmap.values()]
            vv = [p[1] for p in uvmap.values()]
            col = px[int(round(sum(us) / len(us) / uv_w * tw)) % tw,
                     int(round(sum(vv) / len(vv) / uv_h * th)) % th]
        tris.append([verts[k] for k in vs] + [col])
    return tris, 'original_mesh'


def load_geo(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    geo = data['minecraft:geometry'][0]
    tex = Image.open(TEX_MINE).convert('RGBA')
    px = tex.load()
    tw, th = tex.size
    quads = []
    for bone in geo['bones']:
        for cu in bone.get('cubes', []):
            o = cu['origin']
            s = cu['size']
            x0, y0, z0 = o
            x1, y1, z1 = o[0] + s[0], o[1] + s[1], o[2] + s[2]
            rot = cu.get('rotation')
            piv = cu.get('pivot', [0, 0, 0])
            corners = {
                'n': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
                's': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
                'e': [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
                'w': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
                'u': [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
                'd': [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
            }
            for face, pts in corners.items():
                if rot:
                    pts = [rot_point(p, rot, piv) for p in pts]
                uv = cu.get('uv')
                col = (150, 150, 155, 255)
                if isinstance(uv, dict) and face in uv:
                    e = uv[face]
                    u = e['uv'][0] + e['uv_size'][0] / 2.0
                    v = e['uv'][1] + e['uv_size'][1] / 2.0
                    col = px[int(u) % tw, int(v) % th]
                quads.append([to_orig_axes(p) for p in pts] + [col])
    return quads, 'block_model'


def rot_point(p, rot, piv):
    rx, ry, rz = [math.radians(a) for a in rot]
    x, y, z = p[0] - piv[0], p[1] - piv[1], p[2] - piv[2]
    if rz:
        x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    if ry:
        x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    if rx:
        y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    return (x + piv[0], y + piv[1], z + piv[2])


def to_orig_axes(p):
    """新模型：-Z 为前、X 为弓臂展开方向；原模型：+X 为前、Z 为展开方向。
    映射：X_orig = -z, Y_orig = y, Z_orig = x"""
    return (-p[2], p[1], p[0])


VIEWS = {
    'profile': (0, 0),
    'iso': (-35, 20),
    'top': (0, 89.9),
    'bow': (-90, 0),
}


def render(polys, yaw_deg, pitch_deg, size=SIZE, margin=16, label=''):
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    def rot(v):
        x, y, z = v
        x, z = x * cy - z * sy, x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        return (x, y, z)

    rp = [[rot(p) for p in poly[:-1]] + [poly[-1]] for poly in polys]
    xs = [p[0] for poly in rp for p in poly[:-1]]
    ys = [p[1] for poly in rp for p in poly[:-1]]
    spanx = max(max(xs) - min(xs), 1e-6)
    spany = max(max(ys) - min(ys), 1e-6)
    sc = min((size - 2 * margin) / spanx, (size - 2 * margin) / spany)
    ox = margin + ((size - 2 * margin) - spanx * sc) / 2
    oy = margin + ((size - 2 * margin) - spany * sc) / 2
    minx, miny = min(xs), min(ys)

    def proj(p):
        return (ox + (p[0] - minx) * sc, size - (oy + (p[1] - miny) * sc))

    out = []
    for poly in rp:
        pts, col = poly[:-1], poly[-1]
        a, b, c = pts[0], pts[1], pts[2]
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        ln = math.sqrt(sum(k * k for k in n)) or 1.0
        lt = max(0.35, min(1.25, 0.66 + 0.5 * ((n[0] / ln) * 0.35 + (n[1] / ln) * -0.6 + (n[2] / ln) * 0.72)))
        shade = (min(255, int(col[0] * lt)), min(255, int(col[1] * lt)), min(255, int(col[2] * lt)), 255)
        depth = sum(p[2] for p in pts) / len(pts)
        out.append((depth, [proj(p) for p in pts], shade))
    out.sort(key=lambda t: t[0])

    img = Image.new('RGBA', (size, size), (244, 244, 238, 255))
    d = ImageDraw.Draw(img)
    for _, poly, col in out:
        if len(poly) >= 3:
            d.polygon(poly, fill=col)
    if label:
        d.rectangle([0, 0, size - 1, 22], fill=(38, 38, 44, 255))
        d.text((8, 6), label, fill=(240, 240, 240, 255))
    return img


def main():
    orig, n1 = load_bbmodel('模型/十字弩.bbmodel')
    mine, n2 = load_geo('build/_mine.geo.json')
    os.makedirs('build/cmp', exist_ok=True)
    for name, (yaw, pitch) in VIEWS.items():
        a = render(orig, yaw, pitch, label='ORIGINAL  13.1 x 4.7 x 15.7')
        b = render(mine, yaw, pitch, label='REBUILT')
        canvas = Image.new('RGB', (SIZE * 2 + 8, SIZE), (255, 255, 255))
        canvas.paste(a.convert('RGB'), (0, 0))
        canvas.paste(b.convert('RGB'), (SIZE + 8, 0))
        canvas.save('build/cmp/cmp_%s.png' % name)

    def bbox(polys):
        xs = [p[0] for poly in polys for p in poly[:-1]]
        ys = [p[1] for poly in polys for p in poly[:-1]]
        zs = [p[2] for poly in polys for p in poly[:-1]]
        return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))

    o, m = bbox(orig), bbox(mine)
    print('ORIGINAL  L x H x W = %.2f x %.2f x %.2f   ratios H/L=%.3f W/L=%.3f' % (
        o[0], o[1], o[2], o[1] / o[0], o[2] / o[0]))
    print('REBUILT   L x H x W = %.2f x %.2f x %.2f   ratios H/L=%.3f W/L=%.3f' % (
        m[0], m[1], m[2], m[1] / m[0], m[2] / m[0]))


if __name__ == '__main__':
    main()
