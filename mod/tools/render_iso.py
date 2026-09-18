#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 .bbmodel 的 mesh 渲染成指定 yaw/pitch 的正交视图（带简单明暗），用于看清真实形状。"""
import base64
import io
import json
import math
import sys

from PIL import Image, ImageDraw


def load_texture(data):
    for tex in data.get('textures', []):
        src = tex.get('source') or ''
        if src.startswith('data:image'):
            raw = base64.b64decode(src.split(',', 1)[1])
            return Image.open(io.BytesIO(raw)).convert('RGBA')
    return None


def render(data, out_path, yaw_deg, pitch_deg, size=900, margin=24,
           zscale=1.0, label=''):
    el = data['elements'][0]
    verts = el['vertices']
    faces = el['faces']
    tex = load_texture(data)
    uv_w = (data.get('resolution') or {}).get('width', 16) or 16
    uv_h = (data.get('resolution') or {}).get('height', 16) or 16
    tw, th = (tex.size if tex else (uv_w, uv_h))
    tpx = tex.load() if tex else None

    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    def rot(v):
        x, y, z = v[0], v[1], v[2]
        x, z = x * cy - z * sy, x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        return (x, y, z)

    rv = {k: rot(v) for k, v in verts.items()}
    xs = [p[0] for p in rv.values()]
    ys = [p[1] for p in rv.values()]
    zs = [p[2] for p in rv.values()]
    spanx = max(max(xs) - min(xs), 1e-6)
    spany = max(max(ys) - min(ys), 1e-6)
    scale = min((size - 2 * margin) / spanx, (size - 2 * margin) / spany)
    ox = margin + ((size - 2 * margin) - spanx * scale) / 2
    oy = margin + ((size - 2 * margin) - spany * scale) / 2

    def proj(p):
        return (ox + (p[0] - min(xs)) * scale, size - (oy + (p[1] - min(ys)) * scale))

    tris = []
    for f in faces.values():
        vs = f['vertices']
        if len(vs) < 3:
            continue
        uvmap = f.get('uv') or {}
        c = (170, 170, 170, 255)
        if uvmap and tpx is not None:
            us = [p[0] for p in uvmap.values()]
            vv = [p[1] for p in uvmap.values()]
            sx = int(round(sum(us) / len(us) / uv_w * tw)) % tw
            sy_ = int(round(sum(vv) / len(vv) / uv_h * th)) % th
            c = tpx[sx, sy_]
        # 简易明暗：用面的法线（取前三点）与光照方向点乘
        a, b, cpt = (rv[vs[0]], rv[vs[1]], rv[vs[2]])
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        w = (cpt[0] - a[0], cpt[1] - a[1], cpt[2] - a[2])
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
        n = (n[0] / ln, n[1] / ln, n[2] / ln)
        light = max(0.25, min(1.35, 0.62 + 0.55 * (n[0] * 0.4 + n[1] * -0.6 + n[2] * 0.7)))
        c = (min(255, int(c[0] * light)), min(255, int(c[1] * light)), min(255, int(c[2] * light)), 255)
        depth = sum(rv[k][2] for k in vs) / len(vs)
        tris.append((depth, [rv[k] for k in vs], c))
    tris.sort(key=lambda t: t[0])

    img = Image.new('RGBA', (size, size), (248, 248, 242, 255))
    d = ImageDraw.Draw(img)
    for _, vlist, c in tris:
        poly = [proj(v) for v in vlist]
        if len(poly) >= 3:
            d.polygon(poly, fill=c)

    if label:
        axes = [
            ((0, 0, 0), (5, 0, 0), (220, 60, 60), '+X'),
            ((0, 0, 0), (0, 5, 0), (40, 170, 60), '+Y'),
            ((0, 0, 0), (0, 0, 5), (60, 100, 230), '+Z'),
        ]
        for a, b, col, txt in axes:
            p0 = proj(rot(a))
            p1 = proj(rot(b))
            d.line([p0, p1], fill=col, width=5)
            d.text((p1[0] + 6, p1[1] - 8), txt, fill=col)
        o = proj(rot((0, 0, 0)))
        d.ellipse([o[0] - 5, o[1] - 5, o[0] + 5, o[1] + 5], fill=(0, 0, 0))

    img.convert('RGB').save(out_path)
    print('wrote %-28s yaw=%-4s pitch=%-4s tris=%d' % (out_path, yaw_deg, pitch_deg, len(tris)))


def main():
    path = sys.argv[1]
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    base = '模型/_iso'
    render(data, base + '_y-35_p20.png', -35, 20, label='axes')
    render(data, base + '_y35_p20.png', 35, 20)
    render(data, base + '_y0_p0.png', 0, 0, label='axes')
    render(data, base + '_top.png', 0, 90, label='axes')

    verts = list(data['elements'][0]['vertices'].values())
    n = len(verts)
    mx = sum(v[0] for v in verts) / n
    mz = sum(v[2] for v in verts) / n
    sxx = sum((v[0] - mx) ** 2 for v in verts) / n
    szz = sum((v[2] - mz) ** 2 for v in verts) / n
    sxz = sum((v[0] - mx) * (v[2] - mz) for v in verts) / n
    ang = 0.5 * math.atan2(2 * sxz, sxx - szz)
    print('centroid XZ = (%.2f, %.2f)  principal yaw = %.1f deg' % (mx, mz, math.degrees(ang)))


if __name__ == '__main__':
    main()
