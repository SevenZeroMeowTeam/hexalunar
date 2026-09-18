#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""带贴图的正交渲染器（Z-buffer + 逐像素 UV 插值）。

把 GeckoLib geo.json 的每个面按逐面 UV 光栅化成三角形，用 Z-buffer 做遮挡，
不会有画家算法/粘贴错位的问题。（tools/geo_view.py 只取面中心一点的颜色，看不了贴图。）

用法: python tools/geo_texview.py <geo.json> <texture.png> <out.png>
        [--yaw 215] [--pitch -18] [--size 900] [--zoom 1.06] [--ss 2]
"""
import json
import math
import sys

import numpy as np
from PIL import Image

SHADE = {'up': 1.24, 'north': 1.06, 'south': 0.92, 'east': 0.86, 'west': 1.00, 'down': 0.74}
BG = (246, 247, 249)


def rot_mat(rot_deg):
    x, y, z = [math.radians(v) for v in rot_deg]
    Rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    Rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return Rx @ Ry @ Rz


def corners(o, s):
    """面 -> 4 个 uv 角 (0,0)/(1,0)/(1,1)/(0,1) 的方块局部坐标（Bedrock 约定）。"""
    x0, y0, z0 = o
    x1, y1, z1 = o[0] + s[0], o[1] + s[1], o[2] + s[2]
    return {
        'north': [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
        'south': [(x1, y1, z1), (x0, y1, z1), (x0, y0, z1), (x1, y0, z1)],
        'east': [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
        'west': [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
        'up': [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        'down': [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
    }


def collect(path):
    data = json.load(open(path, encoding='utf-8'))
    g = data['minecraft:geometry'][0]
    quads = []

    def walk(bone, pm):
        piv = np.array(bone.get('pivot', [0, 0, 0]), dtype=float)
        M = pm.copy()
        if bone.get('rotation'):
            R = rot_mat(bone['rotation'])
            T, Ti = np.eye(4), np.eye(4)
            T[:3, 3] = piv
            Ti[:3, 3] = -piv
            M = M @ T @ np.block([[R, np.zeros((3, 1))], [np.zeros((1, 3)), 1]]) @ Ti
        for c in bone.get('cubes', []):
            o = [float(v) for v in c['origin']]
            s = [float(v) for v in c['size']]
            cm = M.copy()
            if c.get('rotation'):
                cp = np.array(c.get('pivot') or [o[i] + s[i] / 2 for i in range(3)], dtype=float)
                R = rot_mat(c['rotation'])
                T, Ti = np.eye(4), np.eye(4)
                T[:3, 3] = cp
                Ti[:3, 3] = -cp
                cm = cm @ T @ np.block([[R, np.zeros((3, 1))], [np.zeros((1, 3)), 1]]) @ Ti
            uvspec = c.get('uv')
            for fname, pts in corners(o, s).items():
                spec = uvspec.get(fname) if isinstance(uvspec, dict) else None
                if not spec:
                    continue
                rect = (float(spec['uv'][0]), float(spec['uv'][1]),
                        float(spec['uv_size'][0]), float(spec['uv_size'][1]))
                w = [np.asarray(cm @ np.array([p[0], p[1], p[2], 1.0]))[:3] for p in pts]
                quads.append((fname, w, rect))
        for ch in g['bones']:
            if ch.get('parent') == bone.get('name'):
                walk(ch, M)

    for b in g['bones']:
        if not b.get('parent'):
            walk(b, np.eye(4))
    return quads, g


UVQ = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))


def render(geo, tex_path, out, yaw=-35.0, pitch=20.0, size=900, zoom=1.06, ss=2):
    quads, g = collect(geo)
    tw = float(g['description'].get('texture_width', 512))
    th = float(g['description'].get('texture_height', 512))
    tex = np.asarray(Image.open(tex_path).convert('RGB'), dtype=np.float32)
    TH, TW = tex.shape[0], tex.shape[1]
    ux, uy = TW / tw, TH / th

    allp = np.array([p for _f, ps, _r in quads for p in ps], dtype=float)
    lo, hi = allp.min(axis=0), allp.max(axis=0)
    ctr = (lo + hi) / 2.0
    ya, pa = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(ya), 0, math.sin(ya)], [0, 1, 0], [-math.sin(ya), 0, math.cos(ya)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(pa), -math.sin(pa)], [0, math.sin(pa), math.cos(pa)]])
    R = Rx @ Ry
    rel = (allp - ctr) @ R.T
    W = H = size * ss
    span = max(rel[:, 0].max() - rel[:, 0].min(), rel[:, 1].max() - rel[:, 1].min(), 1e-6)
    scale = (W * 0.90) / span * zoom
    cx0 = (rel[:, 0].max() + rel[:, 0].min()) / 2.0
    cy0 = (rel[:, 1].max() + rel[:, 1].min()) / 2.0

    color = np.empty((H, W, 3), dtype=np.float32)
    color[:, :] = BG
    zbuf = np.full((H, W), -1e18, dtype=np.float64)

    for fname, ps, rect in quads:
        pp = []
        for p in ps:
            r = (p - ctr) @ R.T
            pp.append((W / 2.0 + (r[0] - cx0) * scale, H / 2.0 - (r[1] - cy0) * scale, r[2]))
        sh = SHADE.get(fname, 1.0)
        for tri in ((0, 1, 2), (0, 2, 3)):
            a, b, c = (pp[i] for i in tri)
            uva, uvb, uvc = (UVQ[i] for i in tri)
            xmin = max(0, int(math.floor(min(a[0], b[0], c[0]))))
            xmax = min(W - 1, int(math.ceil(max(a[0], b[0], c[0]))))
            ymin = max(0, int(math.floor(min(a[1], b[1], c[1]))))
            ymax = min(H - 1, int(math.ceil(max(a[1], b[1], c[1]))))
            if xmax < xmin or ymax < ymin:
                continue
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-9:
                continue
            gx, gy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5,
                                 np.arange(ymin, ymax + 1) + 0.5)
            w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
            w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any():
                continue
            z = w0 * a[2] + w1 * b[2] + w2 * c[2]
            u = (w0 * uva[0] + w1 * uvb[0] + w2 * uvc[0]) * rect[2] + rect[0]
            v = (w0 * uva[1] + w1 * uvb[1] + w2 * uvc[1]) * rect[3] + rect[1]
            ui = np.clip((u * ux).astype(np.int32), 0, TW - 1)
            vi = np.clip((v * uy).astype(np.int32), 0, TH - 1)
            col = tex[vi, ui] * sh
            sz = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            sc = color[ymin:ymax + 1, xmin:xmax + 1]
            m = inside & (z > sz)
            sz[m] = z[m]
            sc[m] = col[m]

    img = Image.fromarray(np.clip(color, 0, 255).astype(np.uint8))
    if ss > 1:
        img = img.resize((size, size), Image.LANCZOS)
    img.save(out)
    print('wrote %-26s faces=%d yaw=%s pitch=%s' % (out.split('/')[-1], len(quads), yaw, pitch))


def main(argv):
    geo, tex, out = argv[1], argv[2], argv[3]

    def opt(n, dv):
        return float(argv[argv.index(n) + 1]) if n in argv else dv
    render(geo, tex, out, yaw=opt('--yaw', -35.0), pitch=opt('--pitch', 20.0),
           size=int(opt('--size', 900.0)), zoom=opt('--zoom', 1.06), ss=int(opt('--ss', 2.0)))


if __name__ == '__main__':
    main(sys.argv)
