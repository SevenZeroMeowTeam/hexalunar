#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""渲染 GeckoLib / Bedrock 几何模型（geo.json + 贴图）成正交视图，用于检查形状与朝向。

支持：骨骼层级 + bone rotation、cube 的 origin/size/uv（box-UV 或逐面 UV）、
cube rotation（绕 pivot，默认自身中心）、inflate、mirror。

用法:
  python tools/geo_view.py <geo.json> <texture.png> <out.png> [--yaw -90] [--pitch 0]
                           [--size 900] [--zoom 1.05] [--grid] [--axes]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

# Bedrock box-UV 各面在 box 里的相对位置（u0, v0, w, h），单位 = 像素
FACES = ['north', 'east', 'south', 'west', 'up', 'down']


def rot_mat(rot_deg, order='xyz'):
    """Bedrock 的 rotation 顺序：X → Y → Z（右手系，度）。"""
    x, y, z = [math.radians(v) for v in rot_deg]
    Rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    Rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return Rx @ Ry @ Rz


def box_uv_layout(u, v, sx, sy, sz):
    """标准 Minecraft box-UV 展开，返回 {face: (u0, v0, w, h)}（像素，左上原点）。"""
    return {
        'north': (u + sz, v + sz, sx, sy),
        'east': (u, v + sz, sz, sy),
        'south': (u + sz + sx, v + sz, sx, sy),
        'west': (u + sz + 2 * sx, v + sz, sz, sy),
        'up': (u + sz, v, sx, sz),
        'down': (u + sz + sx, v, sx, sz),
    }


def face_corners(origin, size):
    x0, y0, z0 = origin
    x1, y1, z1 = origin[0] + size[0], origin[1] + size[1], origin[2] + size[2]
    return {
        'north': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
        'east': [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
        'south': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        'west': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
        'up': [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        'down': [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
    }


def face_normal(name):
    return {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0),
            'west': (-1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0)}[name]


def collect(geo_path, include_bones=None):
    """展开所有骨骼，返回 [(face_name, 4个世界点, 贴图uv矩形, 法线)]。"""
    data = json.load(open(geo_path, encoding='utf-8'))
    g = data['minecraft:geometry'][0]
    quads = []

    def walk(bone, parent_m):
        name = bone.get('name')
        piv = np.array(bone.get('pivot', [0, 0, 0]), dtype=float)
        M = parent_m.copy()
        if bone.get('rotation'):
            R = rot_mat(bone['rotation'])
            T = np.eye(4)
            T[:3, 3] = piv
            Ti = np.eye(4)
            Ti[:3, 3] = -piv
            M = M @ T @ np.block([[R, np.zeros((3, 1))], [np.zeros((1, 3)), 1]]) @ Ti
        for c in bone.get('cubes', []):
            o = np.array(c['origin'], dtype=float)
            s = np.array(c['size'], dtype=float)
            inf = float(c.get('inflate', 0) or 0)
            o = o - inf
            s = s + 2 * inf
            cubeM = M.copy()
            if c.get('rotation'):
                cp = np.array(c.get('pivot') or (o + s / 2), dtype=float)
                R = rot_mat(c['rotation'])
                T = np.eye(4)
                T[:3, 3] = cp
                Ti = np.eye(4)
                Ti[:3, 3] = -cp
                cubeM = cubeM @ T @ np.block([[R, np.zeros((3, 1))],
                                              [np.zeros((1, 3)), 1]]) @ Ti
            uvspec = c.get('uv')
            if isinstance(uvspec, list):
                lay = box_uv_layout(uvspec[0], uvspec[1], s[0], s[1], s[2])
            else:
                lay = None
            for fname, pts in face_corners(list(o), list(s)).items():
                if lay:
                    rect = lay[fname]
                elif isinstance(uvspec, dict) and fname in uvspec:
                    u = uvspec[fname].get('uv', [0, 0])
                    us = uvspec[fname].get('uv_size', [s[0], s[1]])
                    rect = (u[0], u[1], us[0], us[1])
                else:
                    rect = None
                wpts = []
                for p in pts:
                    v = cubeM @ np.array([p[0], p[1], p[2], 1.0])
                    wpts.append(v[:3])
                quads.append((fname, wpts, rect, face_normal(fname)))
        # poly_mesh（GeckoLib 网格骨骼）：直接按三角形/多边形画
        pmesh = bone.get('poly_mesh')
        if pmesh:
            pos = pmesh.get('positions') or []
            uvs = pmesh.get('uvs') or []
            norm = bool(pmesh.get('normalized_uvs'))
            for poly in (pmesh.get('polys') or []):
                pts, us = [], []
                for item in poly:
                    i = item[0] if isinstance(item, (list, tuple)) else item
                    if not (0 <= i < len(pos)):
                        continue
                    w = M @ np.array([pos[i][0], pos[i][1], pos[i][2], 1.0])
                    pts.append(w[:3])
                    if i < len(uvs):
                        us.append(uvs[i])
                if len(pts) < 3 or not us:
                    continue
                u = sum(q[0] for q in us) / len(us)
                v = sum(q[1] for q in us) / len(us)
                if norm:                       # 归一化 UV -> 像素
                    u *= 1.0
                quads.append(('mesh', pts, (u, v, 0.0, 0.0), (0.0, 1.0, 0.0)))
        return M

    byname = {b['name']: b for b in g['bones']}
    roots = [b for b in g['bones'] if not b.get('parent')]

    def rec(bone, pm):
        M = walk(bone, pm)
        for ch in g['bones']:
            if ch.get('parent') == bone['name']:
                rec(ch, M)

    for r in roots:
        rec(r, np.eye(4))
    return quads, g


def sample(tex, rect, uv_w, uv_h, face):
    if tex is None or rect is None:
        return (170, 172, 180)
    u, v, w, h = rect
    W, H = tex.size
    # 用面中心取样（近似平涂），并做一点明暗
    px = int(round((u + w / 2) / uv_w * W)) % W
    py = int(round((v + h / 2) / uv_h * H)) % H
    r, g, b = tex.convert('RGB').getpixel((px, py))
    shade = {'up': 1.0, 'north': 0.92, 'south': 0.82, 'east': 0.75, 'west': 0.88,
             'down': 0.62}.get(face, 1.0)
    return (int(r * shade), int(g * shade), int(b * shade))


def render(geo_path, tex_path, out, yaw=-35.0, pitch=20.0, size=900, zoom=1.05,
           grid=False, axes=False):
    quads, g = collect(geo_path)
    uv_w = g['description'].get('texture_width', 64)
    uv_h = g['description'].get('texture_height', 64)
    tex = Image.open(tex_path).convert('RGBA') if tex_path and os.path.exists(tex_path) else None

    pts = [p for _, ps, _, _ in quads for p in ps]
    arr = np.array(pts)
    ctr = (arr.min(axis=0) + arr.max(axis=0)) / 2
    span = float(np.linalg.norm(arr.max(axis=0) - arr.min(axis=0)))

    ya, pa = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(ya), 0, math.sin(ya)], [0, 1, 0], [-math.sin(ya), 0, math.cos(ya)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(pa), -math.sin(pa)], [0, math.sin(pa), math.cos(pa)]])
    R = Rx @ Ry

    rel = [(p - ctr) @ R.T for p in pts]
    xs = [p[0] for p in rel]
    ys = [p[1] for p in rel]
    scale = (size * 0.86) / max(max(xs) - min(xs), max(ys) - min(ys), 1e-6) * zoom
    ox = size / 2 - (max(xs) + min(xs)) / 2 * scale
    oy = size / 2 + (max(ys) + min(ys)) / 2 * scale

    def proj(p):
        return (ox + p[0] * scale, oy - p[1] * scale)

    polys = []
    i = 0
    for fname, ps, rect, nrm in quads:
        a = [(p - ctr) @ R.T for p in ps]
        depth = float(np.mean([p[2] for p in a]))
        col = sample(tex, rect, uv_w, uv_h, fname)
        polys.append((depth, [proj(p) for p in a], col))
        i += 1
    polys.sort(key=lambda t: -t[0])

    img = Image.new('RGB', (size, size), (246, 247, 249))
    dr = ImageDraw.Draw(img)
    if grid:
        for k in range(0, size, size // 16):
            dr.line([(k, 0), (k, size)], fill=(226, 228, 232), width=1)
            dr.line([(0, k), (size, k)], fill=(226, 228, 232), width=1)
    for depth, poly, col in polys:
        dr.polygon([(p[0], p[1]) for p in poly], fill=col)
    if axes:
        o = np.array([0.0, 0.0, 0.0])
        for v, col, tag in ((( 8, 0, 0), (200, 60, 60), '+X'), ((0, 8, 0), (60, 170, 60), '+Y'),
                            ((0, 0, 8), (70, 90, 210), '+Z'), ((0, 0, -8), (30, 40, 140), '-Z N')):
            p0 = proj((o - ctr) @ R.T)
            p1 = proj((np.array(v, dtype=float) - ctr) @ R.T)
            dr.line([p0, p1], fill=col, width=4)
            txt = tag
            dr.text((p1[0] + 6, p1[1] - 8), txt, fill=col)
    img.save(out)
    print('wrote %-28s yaw=%s pitch=%s faces=%d  bbox_center=(%.2f,%.2f,%.2f)'
          % (os.path.basename(out), yaw, pitch, len(quads), ctr[0], ctr[1], ctr[2]))


def main(argv):
    geo, tex, out = argv[1], argv[2], argv[3]

    def opt(name, default):
        return float(argv[argv.index(name) + 1]) if name in argv else default

    render(geo, tex, out, yaw=opt('--yaw', -35.0), pitch=opt('--pitch', 20.0),
           size=int(opt('--size', 900)), zoom=opt('--zoom', 1.05),
           grid='--grid' in argv, axes='--axes' in argv)


if __name__ == '__main__':
    main(sys.argv)
