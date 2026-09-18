# -*- coding: utf-8 -*-
"""换弹故事板：按换弹进度 p 渲几帧「枪 + 双臂」，检查左手有没有跟到该跟的部件上。

与 Java 侧同一套公式（AkmGeoModel.leftHandPx / magPoint / boltPoint + WeaponArms.drawArm），
所以能提前发现手没摸到弹匣 / 拉机柄这类问题，不用反复进游戏。

用法: python tools/_armstory.py akm|crossbow
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dblhold as D  # noqa: E402
import geo_view as gv  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'src/main/resources/assets/hexalunar_calamity')

# ---------------------------------------------------------------- Java 侧同名常数
AKM_RIGHT = (0.0, 0.55, -0.15)
AKM_HANDGUARD = (0.0, 2.05, -6.30)
AKM_MAG = (-0.50, -0.20, -4.30)
AKM_BOLT = (0.70, 2.64, -3.54)
MAG_PIVOT = (0.0, 1.45, -3.78)
MAG_DROP, MAG_TILT, BOLT_TRAVEL = 9.8, 34.0, 1.9

CB_RIGHT = (0.0, -0.90, 0.60)
CB_SUPPORT = (0.0, -0.65, -6.30)
CB_FETCH = (0.20, -1.30, -7.20)
CB_DRAW_DZ, CB_NOCK_Z = 1.80, -5.20


def ease(t):
    x = min(1.0, max(0.0, t))
    return x * x * (3.0 - 2.0 * x)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def mag_drop_at(p):
    if p < 0.18:
        return 0.0
    if p < 0.42:
        return MAG_DROP * ease((p - 0.18) / 0.24)
    if p < 0.55:
        return MAG_DROP
    if p < 0.82:
        return MAG_DROP * (1.0 - ease((p - 0.55) / 0.27))
    return -0.22 * math.sin(((p - 0.82) / 0.18) * math.pi)


def mag_tilt_at(p):
    if p < 0.18:
        return 0.0
    if p < 0.42:
        return -MAG_TILT * ease((p - 0.18) / 0.24)
    if p < 0.55:
        return -MAG_TILT
    if p < 0.82:
        return -MAG_TILT * (1.0 - ease((p - 0.55) / 0.27))
    return 0.0


def bolt_back(p):
    if p <= 0.85:
        return 0.0
    t = (p - 0.85) / 0.15
    return ease(t / 0.5) if t < 0.5 else (1.0 - ease((t - 0.5) / 0.5))


def akm_left(p):
    def mag_point():
        th = math.radians(mag_tilt_at(p))
        dx = AKM_MAG[0] - MAG_PIVOT[0]
        dy = AKM_MAG[1] - MAG_PIVOT[1]
        dz = AKM_MAG[2] - MAG_PIVOT[2]
        return (MAG_PIVOT[0] + dx,
                MAG_PIVOT[1] + (dy * math.cos(th) - dz * math.sin(th)) - mag_drop_at(p),
                MAG_PIVOT[2] + (dy * math.sin(th) + dz * math.cos(th)))

    def bolt_point():
        return (AKM_BOLT[0], AKM_BOLT[1], AKM_BOLT[2] + bolt_back(p) * BOLT_TRAVEL)

    if p < 0.10:
        return lerp(AKM_HANDGUARD, mag_point(), ease(p / 0.10))
    if p < 0.82:
        return mag_point()
    if p < 0.90:
        return lerp(mag_point(), bolt_point(), ease((p - 0.82) / 0.08))
    if p < 0.97:
        return bolt_point()
    return lerp(bolt_point(), AKM_HANDGUARD, ease((p - 0.97) / 0.03))


def cb_left(p):
    def string_point(draw):
        return (0.26, 1.30, CB_NOCK_Z + draw * CB_DRAW_DZ + 0.30)

    def bolt_point():
        draw = min(1.0, p / 0.65) if p >= 0 else 0.0
        return (0.20, 1.41, -5.80 + draw * CB_DRAW_DZ)

    if p < 0.05:
        return CB_SUPPORT
    if p < 0.15:
        return lerp(CB_SUPPORT, string_point(0.0), ease((p - 0.05) / 0.10))
    if p < 0.62:
        return string_point(min(1.0, p / 0.65))
    if p < 0.70:
        return lerp(string_point(1.0), CB_FETCH, ease((p - 0.62) / 0.08))
    if p < 0.84:
        return lerp(CB_FETCH, bolt_point(), ease((p - 0.70) / 0.14))
    if p < 0.97:
        return bolt_point()
    return lerp(bolt_point(), CB_SUPPORT, ease((p - 0.97) / 0.03))


def main(argv):
    which = argv[1] if len(argv) > 1 else 'akm'
    if which == 'akm':
        geo_f = os.path.join(A, 'geo/akm.geo.json')
        tex_f = os.path.join(A, 'textures/models/akm_geo.png')
        item_f = os.path.join(A, 'models/item/akm.json')
        right, left_of = AKM_RIGHT, akm_left
        steps = [0.0, 0.12, 0.30, 0.48, 0.62, 0.80, 0.88, 0.95]
    else:
        geo_f = os.path.join(A, 'geo/crossbow_geo.geo.json')
        tex_f = os.path.join(A, 'textures/models/crossbow_geo.png')
        item_f = os.path.join(A, 'models/item/crossbow.json')
        right, left_of = CB_RIGHT, cb_left
        steps = [0.0, 0.10, 0.25, 0.45, 0.62, 0.72, 0.80, 0.92]

    disp = json.load(open(item_f, encoding='utf-8'))['display']['firstperson_righthand']
    trans = disp.get('translation', [0, 0, 0])
    rot = disp.get('rotation', [0, 0, 0])
    scale = disp.get('scale', [1, 1, 1])

    quads, g = gv.collect(geo_f)
    uv_w = g['description'].get('texture_width', 512)
    uv_h = g['description'].get('texture_height', 512)
    texture = Image.open(tex_f).convert('RGBA')
    rm = D.rx(rot[0]) @ D.ry(rot[1]) @ D.rz(rot[2])
    off = D.ARM_FP * D.PX + np.asarray(trans, dtype=float)      # 像素

    gun = [[np.asarray(p, dtype=float) @ np.diag(scale) @ rm.T + off for p in pts]
           for (_f, pts, _r, _n) in quads]
    gun_uv = [(_r, _f) for (_f, pts, _r, _n) in quads]

    tiles = []
    for p in steps:
        boxes = []
        for side, px_target in (('right', right), ('left', left_of(p))):
            hand = D.cam(px_target, trans, rot, scale)          # 相机空间（格）
            sh = D.SHOULDER[side]
            origin, s, ang, err, basis = D.arm_frame(side, hand, sh)
            boxes.append(D.box_faces(origin * D.PX, s, basis, D.ARM_XC[side] * D.PX))
        out_rel = 'build/_story_%s_%03d.png' % (which, int(p * 100))
        D.render(gun, gun_uv, boxes, texture, uv_w, uv_h, 0.45, out_rel)
        tiles.append(os.path.join(ROOT, out_rel))
        print('p=%.2f  左手模型点 %s' % (p, tuple(round(v, 2) for v in left_of(p))))

    # 拼成一张（横向 4 列 × 2 行）
    cols, rows = 4, 2
    ims = [Image.open(t) for t in tiles]
    w, h = ims[0].size
    sheet = Image.new('RGB', (w * cols, h * rows), (238, 240, 244))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    out = os.path.join(ROOT, 'build', '_story_%s.png' % which)
    sheet.save(out)
    print('wrote %s' % out)


if __name__ == '__main__':
    main(sys.argv)
