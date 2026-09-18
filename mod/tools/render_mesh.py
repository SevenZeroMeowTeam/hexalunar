#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 .bbmodel 里的 mesh 渲染成几个正交视图，方便看清形状与配色。"""
import base64
import io
import json
import math
import sys
from collections import defaultdict

from PIL import Image, ImageDraw

VIEWS = {
    'side':  (2, 1),   # 沿 +X 看: 屏幕 x=Z, 屏幕 y=Y
    'top':   (0, 2),   # 俯视:     屏幕 x=X, 屏幕 y=Z
    'front': (0, 1),   # 从前看:   屏幕 x=X, 屏幕 y=Y
}


def load_texture(data, fallback_png=None):
    for tex in data.get('textures', []):
        src = tex.get('source') or ''
        if src.startswith('data:image'):
            raw = base64.b64decode(src.split(',', 1)[1])
            return Image.open(io.BytesIO(raw)).convert('RGBA')
    if fallback_png:
        return Image.open(fallback_png).convert('RGBA')
    return None


def sample(tex, u, v, uv_w, uv_h):
    if tex is None:
        return (180, 180, 180, 255)
    w, h = tex.size
    x = int(round(u / uv_w * w)) % w
    y = int(round(v / uv_h * h)) % h
    return tex.getpixel((x, y))


def render(data, view, out_path, size=900, margin=20):
    el = data['elements'][0]
    verts = el['vertices']
    faces = el['faces']
    tex = load_texture(data, out_path and None)
    uv_w = data.get('resolution', {}).get('width', 16) or 16
    uv_h = data.get('resolution', {}).get('height', 16) or 16

    ax, ay = VIEWS[view]
    pts = [(v[ax], v[ay]) for v in verts.values()]
    minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts); maxy = max(p[1] for p in pts)
    spanx = max(maxx - minx, 1e-6); spany = max(maxy - miny, 1e-6)
    scale = min((size - 2 * margin) / spanx, (size - 2 * margin) / spany)
    ox = margin + ((size - 2 * margin) - spanx * scale) / 2
    oy = margin + ((size - 2 * margin) - spany * scale) / 2

    def proj(v):
        return (ox + (v[ax] - minx) * scale, size - (oy + (v[ay] - miny) * scale))

    # 深度轴：side 视图用 X，top 用 Y，front 用 Z
    depth_axis = 3 - ax - ay
    tris = []
    for f in faces.values():
        vs = f['vertices']
        if len(vs) < 3:
            continue
        uvmap = f.get('uv') or {}
        c = (170, 170, 170, 255)
        if uvmap:
            us = [p[0] for p in uvmap.values()]
            vv = [p[1] for p in uvmap.values()]
            c = sample(tex, sum(u for u in us) / len(us), sum(v for v in vv) / len(vv), uv_w, uv_h)
        d = sum(verts[k][depth_axis] for k in vs) / len(vs)
        tris.append((d, [verts[k] for k in vs], c))
    tris.sort(key=lambda t: t[0])

    img = Image.new('RGBA', (size, size), (250, 250, 245, 255))
    d = ImageDraw.Draw(img)
    for _, vlist, c in tris:
        poly = [proj(v) for v in vlist]
        if len(poly) >= 3:
            d.polygon(poly, fill=c)
    img.convert('RGB').save(out_path)
    print('wrote', out_path, 'tris=%d' % len(tris), 'x:%.2f..%.2f y:%.2f..%.2f' % (minx, maxx, miny, maxy))


def main():
    path = sys.argv[1]
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    tex = load_texture(data)
    if tex:
        print('texture image size:', tex.size)
        tex.convert('RGB').save('模型/_tex_view.png')
    for view in VIEWS:
        render(data, view, '模型/_view_%s.png' % view)


if __name__ == '__main__':
    main()
