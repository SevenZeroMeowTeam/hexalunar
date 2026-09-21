# -*- coding: utf-8 -*-
"""离线看**原版 JSON 物品模型**（`elements` 那种）的三维效果 —— 不用开游戏。

用法::

    python tools/jsonmodel_view.py <模型.json> <贴图.png> <out.png> [--yaw 35] [--pitch 20]
                                   [--zoom 40] [--size 700] [--views]

做的事：读 elements（含绕 Y 轴旋转）→ 造 8 个角 → 按面做背面剃除 →
画家算法排序 → 正交投影成图；每面颜色取贴图对应 UV 区域的平均色。
（子弹这种小物件用平均色足够了；要看贴图细节请进游戏或 Blockbench。）
"""
import io
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FACE_DEFS = {
    # face: (4 个角的索引（逆时针，从外面看）, 法线轴)
    'north': ((0, 1, 3, 2), (0, 0, -1)),
    'south': ((5, 4, 6, 7), (0, 0, 1)),
    'west': ((4, 0, 2, 6), (-1, 0, 0)),
    'east': ((1, 5, 7, 3), (1, 0, 0)),
    'up': ((2, 3, 7, 6), (0, 1, 0)),
    'down': ((4, 5, 1, 0), (0, -1, 0)),
}


def rot_y(p, origin, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    x, y, z = p[0] - origin[0], p[1] - origin[1], p[2] - origin[2]
    return (origin[0] + x * c + z * s, y + origin[1], origin[2] - x * s + z * c)


def element_quads(e):
    f, t = e['from'], e['to']
    corners = [
        (f[0], f[1], f[2]), (t[0], f[1], f[2]), (f[0], t[1], f[2]), (t[0], t[1], f[2]),
        (f[0], f[1], t[2]), (t[0], f[1], t[2]), (f[0], t[1], t[2]), (t[0], t[1], t[2]),
    ]
    rot = e.get('rotation')
    if rot and rot.get('axis') == 'y' and abs(rot.get('angle', 0)) > 1e-6:
        origin = rot['origin']
        corners = [rot_y(p, origin, rot['angle']) for p in corners]
    out = []
    for face, (idx, n) in FACE_DEFS.items():
        fd = e.get('faces', {}).get(face)
        if not fd:
            continue
        pts = [corners[i] for i in idx]
        nrm = n
        if rot and rot.get('axis') == 'y' and abs(rot.get('angle', 0)) > 1e-6:
            nrm = rot_y(n, (0, 0, 0), rot['angle'])
        out.append((face, pts, nrm, tuple(fd['uv'])))
    return out


def avg_color(img, uv):
    x0, y0, x1, y1 = [int(round(v)) for v in uv]
    x0, y0 = max(0, min(x0, img.width - 1)), max(0, min(y0, img.height - 1))
    x1, y1 = max(x0 + 1, min(x1, img.width)), max(y0 + 1, min(y1, img.height))
    box = img.crop((x0, y0, x1, y1)).convert('RGBA').resize((1, 1), Image.BOX)
    return box.getpixel((0, 0))


def project(p, yaw, pitch, cx, cy, z):
    """正交投影：先绕 Y 转 yaw，再绕 X 转 pitch"""
    a, b = math.radians(yaw), math.radians(pitch)
    x = p[0] * math.cos(a) + p[2] * math.sin(a)
    zz = -p[0] * math.sin(a) + p[2] * math.cos(a)
    y = p[1] * math.cos(b) - zz * math.sin(b)
    d = p[1] * math.sin(b) + zz * math.cos(b)
    return (cx + x * z, cy - y * z, d)


def render(model_path, tex_path, out, yaw=35.0, pitch=18.0, zoom=46.0, size=700,
           view_label=None):
    model = json.load(io.open(model_path, encoding='utf-8'))
    img = Image.open(tex_path).convert('RGBA')
    # 模型包围盒（用于居中）
    xs, ys = [], []
    for e in model['elements']:
        for q in element_quads(e):
            for p in q[1]:
                xs.append(p[0])
                ys.append(p[1])
    cx_model = (min(xs) + max(xs)) / 2.0 if xs else 0.0
    y0_model = min(ys) if ys else 0.0

    quads = []
    view = (math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)),
            math.sin(math.radians(pitch)),
            math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)))
    # ★ 按**元素**分组排序：画家算法按"单个面"排会在小方块交错时画错层
    #   （子弹的肩/颈/弹头都是小方块叠在一起）—— 元素是凸体，按元素排就不会穿插。
    groups = []
    for e in model['elements']:
        faces = element_quads(e)
        if not faces:
            continue
        pts_all = [(p[0] - cx_model, p[1] - y0_model, p[2]) for _f, pts, _n, _uv in faces
                   for p in pts]
        ctr = (sum(p[0] for p in pts_all) / len(pts_all),
               sum(p[1] for p in pts_all) / len(pts_all),
               sum(p[2] for p in pts_all) / len(pts_all))
        depth = project(ctr, yaw, pitch, size / 2.0, size * 0.62, zoom)[2]
        groups.append((depth, e))
    groups.sort(key=lambda g: g[0])          # 远的元素先画

    for _gdepth, e in groups:
        for face, pts, nrm, uv in element_quads(e):
            pts = [(p[0] - cx_model, p[1] - y0_model, p[2]) for p in pts]
            dot = nrm[0] * view[0] + nrm[1] * view[1] + nrm[2] * view[2]
            if dot <= 0.001:                 # 背面剔除
                continue
            proj = [project(p, yaw, pitch, size / 2.0, size * 0.62, zoom) for p in pts]
            depth = sum(p[2] for p in proj) / len(proj)
            quads.append((depth, [(p[0], p[1]) for p in proj], avg_color(img, uv), dot))

    quads.sort(key=lambda q: q[0])          # 远的先画
    im = Image.new('RGBA', (size, size), (245, 245, 248, 255))
    d = ImageDraw.Draw(im)
    for _depth, poly, col, dot in quads:
        shade = 0.72 + 0.28 * min(1.0, dot)
        c = (int(col[0] * shade), int(col[1] * shade), int(col[2] * shade),
             255 if col[3] > 8 else 0)
        d.polygon(poly, fill=c)
        # ★ 棱边描线：不画线的话「平均色填面」会把八棱柱糊成一根方柱，看不出形状
        d.line(list(poly) + [poly[0]], fill=(52, 42, 22, 150), width=1)
    im.save(out)
    return len(quads)


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return
    model, tex, out = argv[1], argv[2], argv[3]

    def opt(name, default):
        return float(argv[argv.index(name) + 1]) if name in argv else default

    yaw, pitch = opt('--yaw', 35.0), opt('--pitch', 18.0)
    zoom, size = opt('--zoom', 46.0), int(opt('--size', 700))
    n = render(model, tex, out, yaw, pitch, zoom, size)
    print('wrote %s  faces=%d  yaw=%.0f pitch=%.0f' % (out, n, yaw, pitch))


if __name__ == '__main__':
    main(sys.argv)
