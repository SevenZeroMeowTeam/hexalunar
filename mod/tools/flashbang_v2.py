#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""震爆弹 v2：M84 风格圆柱弹体（八边形截面 + 泄气孔 + 蓝色色带）+ 引信/压把/拉环重做。

参考 模型/mtx.bbmodel（实测：圆柱体、底部加大底盖、上段有蓝色带、弹体上成排的圆孔、
压把在 -X 侧竖直、保险销沿 Z 从 -Z 侧拉出、拉环在 Y-Z 平面）。
沿用旧模型坐标约定（原点=弹体中心，半径 ≈1.7，骨骼 root/move/body/fuze/spoon/pin）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxlib as B  # noqa: E402

BODY = (80, 82, 74)          # 弹体灰绿
BODY_D = (62, 64, 57)
BAND = (52, 96, 112)         # 蓝色色带
FUZE = (68, 70, 68)          # 引信钢
CAP = (56, 58, 56)           # 顶盖
SPOON = (52, 54, 52)         # 压把
PIN = (142, 144, 148)        # 保险销/拉环

BONES = [
    ('root', None, (0.0, -1.224, -0.544)),
    ('move', 'root', (0.0, 0.0, 0.0)),
    ('body', 'move', (0.0, 0.0, 0.0)),
    ('fuze', 'body', (0.0, 2.516, 0.0)),
    ('spoon', 'fuze', (0.0, 3.332, -0.136)),
    ('pin', 'fuze', (0.0, 2.924, 0.0)),
]

CUBES = []


def detail_holes(img, rect, face, seed):
    """弹体侧面：成排泄气孔（外圈亮、孔内黑）+ 上下沿的明暗过渡。"""
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    if face in ('east', 'west', 'north', 'south'):
        d.line([(x, y + 1), (x + w - 1, y + 1)], fill=B.sh(BODY, 1.14))
        d.line([(x, y + h - 2), (x + w - 1, y + h - 2)], fill=B.sh(BODY, 0.80))
        cols = max(1, int(w / 9))
        rows = max(1, int(h / 9))
        r = max(1.0, min(w / cols, h / rows) * 0.20)
        for i in range(cols):
            for j in range(rows):
                cx = x + w * (i + 0.5) / cols
                cy = y + h * (j + 0.5) / rows
                d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1],
                          fill=B.sh(BODY, 1.34))
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(26, 27, 24, 255))
                d.ellipse([cx - r, cy - r, cx + r * 0.45, cy], fill=B.sh(BODY, 0.52))
    elif face == 'up':
        cx, cy = x + w / 2.0, y + h / 2.0
        r = min(w, h) * 0.30
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=B.sh(BODY, 0.72), width=1)


def detail_band(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=BAND)
    if face in ('east', 'west', 'north', 'south'):
        d.line([(x, y + 1), (x + w - 1, y + 1)], fill=B.sh(BAND, 1.35))
        d.line([(x, y + h - 2), (x + w - 1, y + h - 2)], fill=B.sh(BAND, 0.72))
        for i in range(0, w, 3):
            d.line([(x + i, y + 2), (x + i, y + h - 3)], fill=B.sh(BAND, 0.90))


def detail_fuze(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    for i in range(0, h, 2):
        d.line([(x + 1, y + i), (x + w - 2, y + i)], fill=B.sh(FUZE, 0.90))
    d.line([(x, y + 1), (x + w - 1, y + 1)], fill=B.sh(FUZE, 1.18))


def detail_cap(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    if w > 4 and h > 4:
        d.rectangle([x + 1, y + 1, x + w - 2, y + h - 2], outline=B.sh(CAP, 1.25))


def detail_spoon(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    d.line([(x, y + 1), (x + w - 1, y + 1)], fill=B.sh(SPOON, 1.30))
    d.line([(x, y + h - 2), (x + w - 1, y + h - 2)], fill=B.sh(SPOON, 0.72))


def detail_ring(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    d.line([(x, y + 1), (x + w - 1, y + 1)], fill=B.sh(PIN, 1.20))


DETAILS = {'holes': detail_holes, 'band': detail_band, 'fuze': detail_fuze,
           'cap': detail_cap, 'spoon': detail_spoon, 'ring': detail_ring}


def cyl(bone, name, y0, y1, r, mat, kind, tag=None, cx=0.0, cz=0.0, k=0.414):
    return B.cross_boxes(bone, name, y0, y1, r, cx, cz, mat, kind, tag=tag, k=k)


# ------------------------------------------------------------ 弹体
CUBES += cyl('body', 'base_plate', -2.86, -2.62, 1.94, B.sh(BODY, 0.88), 'metal', 'holes')
CUBES += cyl('body', 'base_ring', -2.62, -2.34, 1.80, BODY, 'metal', 'holes')
CUBES += cyl('body', 'cyl_main', -2.34, 1.72, 1.72, BODY, 'metal', 'holes')
CUBES += cyl('body', 'shoulder', 1.72, 2.28, 1.80, B.sh(BODY, 1.05), 'metal', 'holes')
CUBES += cyl('body', 'band', 2.28, 2.68, 1.86, BAND, 'metal', 'band')
CUBES += cyl('body', 'waist', 2.68, 2.86, 1.42, B.sh(BODY, 0.92), 'metal', 'fuze')

# ------------------------------------------------------------ 引信
CUBES += cyl('fuze', 'fuze_low', 2.86, 3.18, 1.36, FUZE, 'metal', 'fuze')
CUBES += cyl('fuze', 'fuze_head', 3.18, 3.44, 1.24, B.sh(FUZE, 1.10), 'metal', 'fuze')
CUBES += cyl('fuze', 'fuze_top', 3.44, 3.54, 0.92, CAP, 'flat', 'cap')

# ------------------------------------------------------------ 压把（-X 侧竖直）
SPOON_PATH = [(-1.34, 3.26), (-1.62, 3.00), (-1.86, 2.60), (-1.98, 2.06),
              (-1.94, 1.36), (-1.90, 0.52), (-1.88, -0.36), (-1.86, -1.30),
              (-1.86, -2.10), (-1.74, -2.60)]
CUBES += B.arc_boxes('spoon', 'spoon', SPOON_PATH, thick=0.17, half_w=0.29,
                     mat=SPOON, kind='flat', plane='xy')
CUBES.append(B.cube('spoon', 'spoon_hinge', (-0.30, 0.30), (3.22, 3.52), (0.22, 0.90),
                    SPOON, kind='flat', tag='spoon'))

# ------------------------------------------------------------ 保险销 + 拉环
CUBES.append(B.cube('pin', 'pin_rod', (-0.12, 0.12), (2.76, 3.00), (-2.46, 1.18),
                    PIN, kind='brushed'))
CUBES.append(B.cube('pin', 'pin_head', (-0.19, 0.19), (2.68, 3.08), (1.06, 1.28),
                    PIN, kind='brushed'))
CUBES += B.ring('pin', 'pin_ring', 0.0, 2.52, -2.94, 0.62, 0.15, PIN, 'brushed',
                axis='x', seg=8)
CUBES.append(B.cube('pin', 'pin_ring_link', (-0.08, 0.08), (2.66, 2.90), (-2.52, -2.30),
                    PIN, kind='brushed'))


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # ---------------- 细节件（r42）：防滑环带 / 上环带 / 顶盖螺钉
    CUBES.extend(B.ring('body', 'knurl', 0.0, -1.80, 0.0, 1.98, 0.14, (30, 32, 29), 'metal',
                        axis='y', seg=10))
    CUBES.extend(B.ring('body', 'band_up', 0.0, 2.30, 0.0, 1.96, 0.12, (36, 38, 34), 'metal',
                        axis='y', seg=10))
    for _i, (_bx, _bz) in enumerate(((0.0, 0.85), (0.74, -0.42), (-0.74, -0.42))):
        CUBES.extend(B.bolt('fuze', 'cap_scr_%d' % _i, _bx, 3.54, _bz, 0.13, 0.06,
                            (128, 130, 134), axis='y', dark=(26, 26, 28)))
    geo, img = B.build(BONES, CUBES, 'geometry.flashbang', details=DETAILS)
    B.write(geo, img, os.path.join(root, 'build', 'flashbang_v2.geo.json'),
            os.path.join(root, 'build', 'flashbang_v2.png'))


if __name__ == '__main__':
    main()
