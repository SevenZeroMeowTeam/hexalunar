#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用坐标渐变给原始网格上色渲染，用来无歧义地判断各部件位置。
红=+X(前/弓臂端) 蓝=-X(后/枪托端) 绿高=+Y"""
import base64
import io
import json
import math
import sys

from PIL import Image, ImageDraw

SIZE = 760


def main(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    el = data['elements'][0]
    verts = el['vertices']
    faces = el['faces']
    xs = [v[0] for v in verts.values()]
    ys = [v[1] for v in verts.values()]
    zs = [v[2] for v in verts.values()]
    bounds = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    print('bounds X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % bounds)

    yaw = math.radians(0)
    pitch = math.radians(0)

    def rot(v):
        return v

    tris = []
    for f in faces.values():
        vs = f['vertices']
        if len(vs) < 3:
            continue
        pts = [rot(verts[k]) for k in vs]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        cz = sum(p[2] for p in pts) / len(pts)
        tx = (cx - bounds[0]) / max(bounds[1] - bounds[0], 1e-6)
        ty = (cy - bounds[2]) / max(bounds[3] - bounds[2], 1e-6)
        r = int(40 + 215 * tx)
        g = int(40 + 215 * ty)
        b = int(230 - 180 * tx)
        depth = cz
        tris.append((depth, pts, (r, g, b, 255)))
    tris.sort(key=lambda t: t[0])

    spanx = bounds[1] - bounds[0]
    spany = bounds[3] - bounds[2]
    sc = min((SIZE - 60) / spanx, (SIZE - 60) / spany)
    ox = 30 + ((SIZE - 60) - spanx * sc) / 2
    oy = 30 + ((SIZE - 60) - spany * sc) / 2

    def proj(p):
        return (ox + (p[0] - bounds[0]) * sc, SIZE - (oy + (p[1] - bounds[2]) * sc))

    img = Image.new('RGBA', (SIZE, SIZE), (250, 250, 250, 255))
    d = ImageDraw.Draw(img)
    for _, pts, col in tris:
        d.polygon([proj(p) for p in pts], fill=col)
    d.rectangle([0, 0, SIZE - 1, 20], fill=(255, 255, 255, 255))
    d.text((6, 4), 'RED = +X (bow end)      BLUE = -X (butt end)      GREEN bright = +Y (top)', fill=(0, 0, 0))
    img.convert('RGB').save('build/cmp/orig_axis_profile.png')

    # 同时也渲染 bow 视图（沿 X 看）
    tris2 = []
    for f in faces.values():
        vs = f['vertices']
        if len(vs) < 3:
            continue
        pts = [verts[k] for k in vs]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        cz = sum(p[2] for p in pts) / len(pts)
        tx = (cx - bounds[0]) / max(bounds[1] - bounds[0], 1e-6)
        ty = (cy - bounds[2]) / max(bounds[3] - bounds[2], 1e-6)
        r = int(40 + 215 * tx)
        g = int(40 + 215 * ty)
        b = int(230 - 180 * tx)
        tris2.append((cx, pts, (r, g, b, 255)))
    tris2.sort(key=lambda t: t[0])
    spanx2 = bounds[5] - bounds[4]
    spany2 = bounds[3] - bounds[2]
    sc2 = min((SIZE - 60) / spanx2, (SIZE - 60) / spany2)
    ox2 = 30 + ((SIZE - 60) - spanx2 * sc2) / 2
    oy2 = 30 + ((SIZE - 60) - spany2 * sc2) / 2

    def proj2(p):
        return (ox2 + (p[2] - bounds[4]) * sc2, SIZE - (oy2 + (p[1] - bounds[2]) * sc2))

    img2 = Image.new('RGBA', (SIZE, SIZE), (250, 250, 250, 255))
    d2 = ImageDraw.Draw(img2)
    for _, pts, col in tris2:
        d2.polygon([proj2(p) for p in pts], fill=col)
    d2.text((6, 4), 'view along X: horizontal = Z (bow span), vertical = Y', fill=(0, 0, 0))
    img2.convert('RGB').save('build/cmp/orig_axis_bow.png')
    print('wrote build/cmp/orig_axis_profile.png and orig_axis_bow.png')


if __name__ == '__main__':
    main('模型/十字弩.bbmodel')
