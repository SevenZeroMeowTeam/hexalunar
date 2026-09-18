#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GeckoLib geo 模型的「游戏内视角」预览：第一人称 / 武器在玩家手里。

变换链与 MC 一致：world = Trans(手部偏移+display平移) · Rx·Ry·Rz(display) · Scale(display) · x

用法:
  python tools/geo_item_view.py <geo.json> <texture.png> <out.png> --cam fp|hand|hand_side|iso
                              [--display <item.json>:<slot>]  [--yaw a] [--pitch b]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_view as gv  # noqa: E402
import north_align as na  # noqa: E402

ARM_FP = np.array([0.56, -0.52, -0.71]) * 16.0     # MC ItemInHandRenderer 手部偏移（像素）

CAMS = {
    'fp': dict(cam=(12.0, -2.0, 14.0), tgt=(10.0, -8.0, -30.0), fov=50.0,
               frame=(90.0, 0.0, 0.0), arm='fp', hand=False),
    'hand': dict(cam=(30.0, 24.0, -30.0), tgt=(2.0, -2.0, -2.0), fov=45.0,
                 frame=(0.0, 0.0, 0.0), arm=None, hand=True),
    'hand_side': dict(cam=(42.0, 10.0, 4.0), tgt=(0.0, -2.0, -6.0), fov=45.0,
                      frame=(0.0, 0.0, 0.0), arm=None, hand=True),
    'iso': dict(cam=(26.0, 20.0, 26.0), tgt=(0.0, 0.0, 0.0), fov=45.0,
                frame=(0.0, 0.0, 0.0), arm=None, hand=False),
}


def display_of(path, slot):
    if not path:
        return [0, 0, 0], [0, 0, 0], [1, 1, 1]
    d = (json.load(open(path, encoding='utf-8')).get('display') or {}).get(slot) or {}
    return (d.get('rotation') or [0, 0, 0], d.get('translation') or [0, 0, 0],
            d.get('scale') or [1, 1, 1])


def hand_boxes():
    hand = (-2.5, 2.5, -4.5, 1.5, -4, 6, (128, 136, 152))
    forearm = (-2.0, 2.0, -3.5, 1.0, 6, 22, (86, 92, 106))
    return [hand, forearm]


def main(argv):
    geo, tex, out = argv[1], argv[2], argv[3]

    def opt(name, default):
        return argv[argv.index(name) + 1] if name in argv else default

    cam = opt('--cam', 'hand')
    C = CAMS[cam]
    disp = opt('--display', None)
    slot = CAMS[cam].get('slot') or {'fp': 'firstperson_righthand',
                                     'hand': 'thirdperson_righthand',
                                     'hand_side': 'thirdperson_righthand',
                                     'iso': 'thirdperson_righthand'}[cam]
    rot, trans, scale = display_of(disp, slot) if disp else ([0, 0, 0], [0, 0, 0], [1, 1, 1])

    quads, g = gv.collect(geo)
    uv_w = g['description'].get('texture_width', 512)
    uv_h = g['description'].get('texture_height', 512)
    texture = Image.open(tex).convert('RGBA')

    R = np.array(na.rotmat_xyz(rot))
    S = np.diag(scale)
    F = np.array(na.rotmat_xyz(C['frame'])) if C.get('frame') else np.eye(3)
    off = ARM_FP if C.get('arm') == 'fp' else np.zeros(3)
    off = off + np.array(trans, dtype=float)

    polys = []
    for fname, pts, rect, nrm in quads:
        p3 = [F @ (np.array(p, dtype=float) @ S.T @ R.T + off) for p in pts]
        depth = float(np.mean([(np.array(p) - np.array(C['cam'])) @ np.array(p) for p in p3])) \
            if False else float(np.mean([np.linalg.norm(np.array(p) - np.array(C['cam'])) for p in p3]))
        polys.append((depth, p3, gv.sample(texture, rect, uv_w, uv_h, fname)))

    extra = []
    if C.get('hand'):
        # 示意手要跟武器同一个缩放/偏移，否则比例会对不上
        sx, sy, sz = scale
        for (x0, x1, y0, y1, z0, z1, col) in hand_boxes():
            extra.append((x0 * sx + off[0], x1 * sx + off[0],
                          y0 * sy + off[1], y1 * sy + off[1],
                          z0 * sz + off[2], z1 * sz + off[2], col))

    gv_render(polys, extra, C['cam'], C['tgt'], C['fov'], out,
              label='%s  slot=%s  rot=%s  scale=%s' % (os.path.basename(out), slot, rot, scale))


def gv_render(polys, extra, cam, tgt, fov, out, size=780, label=''):
    cam = np.asarray(cam, dtype=float)
    tgt = np.asarray(tgt, dtype=float)
    fwd = tgt - cam
    fwd /= max(np.linalg.norm(fwd), 1e-9)
    up0 = np.array([0.0, 1.0, 0.0])
    right = np.cross(fwd, up0)
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0.0, 0.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)

    def proj(p):
        d = np.asarray(p, dtype=float) - cam
        x, y, z = float(d @ right), float(d @ up), max(float(d @ fwd), 1e-3)
        fc = 0.5 * size / math.tan(math.radians(fov) / 2)
        return (size / 2 + x * fc / z, size / 2 - y * fc / z, z)

    draw_list = []
    for depth, p3, col in polys:
        draw_list.append((depth, [proj(p) for p in p3], col))
    for el in extra:
        x0, x1, y0, y1, z0, z1, col = el
        box = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
               (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
        quads = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (3, 2, 6, 7),
                 (0, 3, 7, 4), (1, 2, 6, 5)]
        for q in quads:
            p3 = [box[i] for i in q]
            d = float(np.mean([np.linalg.norm(np.array(p) - cam) for p in p3]))
            draw_list.append((d, [proj(p) for p in p3], col))
    draw_list.sort(key=lambda t: -t[0])
    img = Image.new('RGB', (size, size), (238, 240, 244))
    dr = ImageDraw.Draw(img)
    for _d, poly, col in draw_list:
        dr.polygon([(p[0], p[1]) for p in poly], fill=col)
    if label:
        dr.rectangle([0, 0, size, 22], fill=(255, 255, 255))
        dr.text((6, 6), label, fill=(0, 0, 0))
    img.save(out)
    print('wrote %s' % out)


if __name__ == '__main__':
    main(sys.argv)
