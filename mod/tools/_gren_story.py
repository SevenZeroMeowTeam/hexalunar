# -*- coding: utf-8 -*-
"""手雷/震爆弹第一人称故事板：拔销 / 投掷各阶段「雷 + 双臂」长什么样。

和 Java 侧 `client/GrenadePose` 用同一套公式（move 骨骼姿态 + 手部目标点 +
`WeaponArms.drawArm` 的手臂摆法），所以能在不进游戏的情况下先看：
  · 右手是不是握在弹体上（不是悬空 / 不是穿模）
  · 左手是不是搭在保险销的拉环上、并随着销被拔出一起外移
  · 投掷时左手有没有跟着甩（要求：只有右手做动作）

用法:
  python tools/_gren_story.py mud              # 碎片手雷
  python tools/_gren_story.py flashbang        # 震爆弹
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dblhold as D      # noqa: E402
import geo_view as gv     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'src/main/resources/assets/hexalunar_calamity')

# ---------------------------------------------------------------- Java 侧同名常数
PIN_PULL_DIST = 1.05          # 销被拉出的最大距离（模型像素）
PIN_ROT_Z_DEG = 16.0          # 拔销：手腕外翻
PIN_ROT_X_DEG = -8.0          # 拔销：抬腕
PIN_POS_Y = 1.6               # 拔销：抬手（模型像素）
PIN_POS_Z = 0.8               # 拔销：往身前
THROW_ROT_X_DEG = -34.0       # 投掷：甩手
THROW_POS_Y = 2.6
THROW_POS_Z = -3.6
SHAKE_ROT_Z_DEG = 3.0         # 引信快烧完时的抖（故事板里不演）

# 右手握点（模型像素）：弹体右后下方的表面
RIGHT_HAND = {'mud': (1.55, -0.50, 1.05), 'flashbang': (1.60, -2.20, 1.15)}
# 左手抓点（模型像素）：保险销的**拉环圆心**（从 geo 里量出来的）
PIN_RING = {'mud': (0.0, 2.68, -1.65), 'flashbang': (0.0, 2.28, -2.86)}


def move_pose(pin, kick):
    """{pos(fx,fy,fz), rot(rx,ry,rz)}：拔销 + 甩手"""
    rx = math.radians(PIN_ROT_X_DEG * pin + THROW_ROT_X_DEG * kick)
    rz = math.radians(PIN_ROT_Z_DEG * pin)
    py = PIN_POS_Y * pin + THROW_POS_Y * kick
    pz = PIN_POS_Z * pin + THROW_POS_Z * kick
    return np.array([0.0, py, pz]), (rx, 0.0, rz)


def xform(p, rot, pos):
    """move 骨骼：pivot = 原点 ⇒ p' = R·p + pos"""
    R = D.rx(math.degrees(rot[0])) @ D.ry(math.degrees(rot[1])) @ D.rz(math.degrees(rot[2]))
    return np.asarray(p, dtype=float) @ R.T + pos


# 肩点（与 Java 的 WeaponArms.SHOULDER_R/L 同一套；这里可以换组试，挑一个最不挡视野的）
SHOULDERS = {
    'a': {'right': (0.55, -0.85, -0.80), 'left': (-0.42, -0.85, -0.78)},
    'b': {'right': (0.72, -1.02, -0.92), 'left': (-0.58, -1.02, -0.90)},
    'c': {'right': (0.88, -1.18, -1.02), 'left': (-0.72, -1.18, -1.00)},
}


def main(argv):
    which = argv[1] if len(argv) > 1 else 'mud'
    sh_key = argv[argv.index('--sh') + 1] if '--sh' in argv else 'a'
    SHOULDER = SHOULDERS[sh_key]
    item_id = 'frag_grenade' if which == 'mud' else 'flashbang'
    geo_f = os.path.join(A, 'geo/%s.geo.json' % which)
    tex_f = os.path.join(A, 'textures/models/%s_geo.png' % which)
    item_f = os.path.join(A, 'models/item/%s.json' % item_id)

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

    # (拔销进度, 甩手冲量, 左手是否在画面上)
    steps = [(0.0, 0.0, False), (0.0, 0.0, True), (0.5, 0.0, True),
             (1.0, 0.0, True), (1.0, 0.35, True), (1.0, 1.0, False)]

    tiles = []
    for (pin, kick, show_left) in steps:
        pos, rot_m = move_pose(pin, kick)
        gun = [[xform(p, rot_m, pos) @ np.diag(scale) @ rm.T + off for p in pts]
               for (_f, pts, _r, _n) in quads]
        gun_uv = [(_r, _f) for (_f, pts, _r, _n) in quads]

        ring = list(PIN_RING[which])
        ring[2] -= PIN_PULL_DIST * pin              # 销被拉出：沿 -Z 走
        targets = [('right', RIGHT_HAND[which])]
        if show_left:
            targets.append(('left', tuple(ring)))
        boxes = []
        for side, px_target in targets:
            hand = D.cam(xform(px_target, rot_m, pos), trans, rot, scale)
            origin, s, ang, err, basis = D.arm_frame(side, hand, SHOULDER[side])
            faces = D.box_faces(origin * D.PX, s, basis, D.ARM_XC[side] * D.PX)
            # 手心标记：手点上一个小立方体（0.7 像素），确认「手有没有搭在弹体 / 拉环上」
            m = 0.35
            mp = hand * D.PX
            corners = [mp + np.array([sx * m, sy * m, sz * m])
                       for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
            idx = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4),
                   (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
            faces = faces + [[corners[i] for i in q] for q in idx]
            boxes.append(faces)
            print('pin=%.2f kick=%.2f %-5s 手=模型点 %s  相机空间 (%.3f, %.3f, %.3f)  臂长倍率 %.2f'
                  % (pin, kick, side, tuple(round(v, 2) for v in px_target),
                     hand[0], hand[1], hand[2], s))

        out_rel = 'build/_gren_%s_p%02d_k%02d_L%d.png' % (which, int(pin * 100), int(kick * 100),
                                                         1 if show_left else 0)
        for back, tag in ((0.45, 'a'), (0.00, 'b')):
            o = out_rel.replace('.png', '_%s.png' % tag)
            D.render(gun, gun_uv, boxes, texture, uv_w, uv_h, back, o)
            tiles.append(os.path.join(ROOT, o))

    cols, rows = 4, 3
    ims = [Image.open(t) for t in tiles]
    w, h = ims[0].size
    sheet = Image.new('RGB', (w * cols, h * rows), (238, 240, 244))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    out = os.path.join(ROOT, 'build', '_gren_%s_%s.png' % (which, sh_key))
    sheet.save(out)
    print('wrote %s  （上：远景 0.45 格 / 下：游戏视角）' % out)


if __name__ == '__main__':
    main(sys.argv)
