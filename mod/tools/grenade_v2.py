#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""碎片手雷 v2：球体真正做圆（9 层八边形截面），引信/压把/保险销+拉环重做。

参考 模型/mud.bbmodel（实测：球体直径 10.87、球心 Y≈5.2、引信 ≈±1.94、压把在 +Z 侧、
保险销沿 Z 轴从 -Z 侧拉出、拉环在 Y-Z 平面）。
沿用旧模型的坐标约定（原点=弹体中心，球半径 2.0，骨骼 root/move/body/fuze/spoon/pin），
这样现有 Java 与动画不用改。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxlib as B  # noqa: E402

OLIVE = (98, 112, 68)        # 弹体军绿
OLIVE_D = (74, 86, 52)       # 弹体下缘
FUZE = (82, 84, 82)          # 引信深灰钢
SPOON = (58, 60, 58)         # 压把黑钢
PIN = (132, 134, 138)        # 保险销银灰
RING = (126, 128, 132)       # 拉环

BONES = [
    ('root', None, (0.0, -1.9, -2.052)),
    ('move', 'root', (0.0, 0.0, 0.0)),
    ('body', 'move', (0.0, 0.0, 0.0)),
    ('fuze', 'body', (0.0, 2.128, 0.0)),
    ('spoon', 'fuze', (0.0, 3.553, 1.216)),
    ('pin', 'fuze', (0.0, 2.736, 0.0)),
]

R = 2.0          # 弹体半径
NSLAB = 15       # 球体分层数

CUBES = []


def detail_body(img, rect, face, seed):
    """弹体：上缘提亮 / 下缘压暗，做出球面的层间过渡。"""
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    if face in ('east', 'west', 'north', 'south'):
        d.line([(x, y + 1), (x + w - 1, y + 1)], fill=B.sh(OLIVE, 1.16))
        d.line([(x, y + h - 2), (x + w - 1, y + h - 2)], fill=B.sh(OLIVE, 0.78))
    elif face == 'up':
        d.line([(x + 1, y + 1), (x + w - 2, y + 1)], fill=B.sh(OLIVE, 1.14))


def detail_seam(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    d.line([(x, y + h // 2), (x + w - 1, y + h // 2)], fill=(34, 38, 26, 255))
    d.line([(x, y + h // 2 + 1), (x + w - 1, y + h // 2 + 1)], fill=B.sh(OLIVE, 1.30))


def detail_fuze(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    for i in range(0, h, 2):
        d.line([(x + 1, y + i), (x + w - 2, y + i)], fill=B.sh(FUZE, 0.88))
    d.line([(x, y + 1), (x + w - 1, y + 1)], fill=B.sh(FUZE, 1.20))
    d.line([(x, y + h - 1), (x + w - 1, y + h - 1)], fill=B.sh(FUZE, 0.70))


def detail_cap(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    d.rectangle([x + 1, y + 1, x + w - 2, y + h - 2], outline=B.sh(FUZE, 0.66))
    if face == 'up':
        cx, cy = x + w / 2.0, y + h / 2.0
        r = min(w, h) * 0.28
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=B.sh(FUZE, 1.30))


DETAILS = {'body': detail_body, 'seam': detail_seam, 'fuze': detail_fuze, 'cap': detail_cap}

# ---------------------------------------------------------------- 弹体（球）
for i, (y0, y1, r) in enumerate(B.sphere_slabs(R, 0.0, NSLAB, shrink=1.0)):
    lo, hi = i < NSLAB / 2, i >= NSLAB / 2
    col = OLIVE if not lo else B.sh(OLIVE, 0.94)
    CUBES += B.cross_boxes('body', 'sphere_%d' % i, y0, y1, r * 0.985, 0.0, 0.0,
                           col, 'metal', tag='body', curv=('sphere', (0.0, 0.0, 0.0)))
# 腰部接缝
CUBES += B.cross_boxes('body', 'seam', -0.07, 0.07, R * 1.012, 0.0, 0.0,
                       B.sh(OLIVE, 0.86), 'flat', tag='seam')

# ---------------------------------------------------------------- 引信
CUBES += B.cross_boxes('fuze', 'fx_collar', 1.78, 2.34, 0.88, 0.0, 0.0, FUZE, 'metal', tag='fuze')
CUBES += B.cross_boxes('fuze', 'fx_neck', 2.34, 2.88, 0.70, 0.0, 0.0, B.sh(FUZE, 1.06),
                       'metal', tag='fuze')
CUBES += B.cross_boxes('fuze', 'fx_head', 2.88, 3.32, 0.78, 0.0, 0.0, FUZE, 'metal', tag='cap')
CUBES += B.cross_boxes('fuze', 'fx_cap', 3.32, 3.62, 0.66, 0.0, 0.0, B.sh(FUZE, 1.12),
                       'metal', tag='cap')

# ---------------------------------------------------------------- 压把（Y-Z 平面，+Z 侧，贴着球面）
R_SP = R + 0.16
SPOON_PATH = [(3.34, 0.76), (2.94, 0.90), (2.42, 0.98), (2.00, 1.02),
              (1.60, 1.35), (0.90, 1.92), (0.10, 2.14), (-0.72, 2.04),
              (-1.42, 1.66), (-1.90, 1.16)]
CUBES += B.arc_boxes('spoon', 'spoon', SPOON_PATH, thick=0.16, half_w=0.27,
                     mat=SPOON, kind='flat', plane='yz', offset=0.0)
# 压把根部（铰链座）
CUBES.append(B.cube('spoon', 'spoon_hinge', (-0.30, 0.30), (3.32, 3.62), (0.36, 0.98),
                    SPOON, kind='flat'))

# ---------------------------------------------------------------- 保险销 + 拉环
CUBES.append(B.cube('pin', 'pin_rod', (-0.12, 0.12), (2.64, 2.88), (-1.34, 0.78),
                    PIN, kind='brushed'))
CUBES.append(B.cube('pin', 'pin_head', (-0.18, 0.18), (2.58, 2.94), (0.68, 0.88),
                    PIN, kind='brushed'))
CUBES += B.ring('pin', 'pin_ring', 0.0, 1.92, -1.26, 0.66, 0.15, RING, 'brushed',
                axis='x', seg=8)
CUBES.append(B.cube('pin', 'pin_ring_link', (-0.08, 0.08), (2.52, 2.70), (-1.40, -1.18),
                    RING, kind='brushed'))


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # ---------------- 细节件（r42）：颈圈 / 引信螺纹 / 顶盖螺钉
    CUBES.extend(B.ring('body', 'collar', 0.0, 1.90, 0.0, 1.34, 0.13, (28, 30, 26), 'metal',
                        axis='y', seg=10))
    CUBES.extend(B.ring('fuze', 'fx_thread', 0.0, 2.58, 0.0, 0.76, 0.09, (40, 42, 38),
                        'metal', axis='y', seg=10))
    for _i, (_bx, _bz) in enumerate(((0.0, 0.48), (0.42, -0.24), (-0.42, -0.24))):
        CUBES.extend(B.bolt('fuze', 'cap_scr_%d' % _i, _bx, 3.62, _bz, 0.11, 0.06,
                            (120, 122, 126), axis='y', dark=(24, 24, 26)))
    geo, img = B.build(BONES, CUBES, 'geometry.mud', details=DETAILS)
    B.write(geo, img, os.path.join(root, 'build', 'mud_v2.geo.json'),
            os.path.join(root, 'build', 'mud_v2.png'))


if __name__ == '__main__':
    main()
