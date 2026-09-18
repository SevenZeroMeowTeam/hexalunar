# -*- coding: utf-8 -*-
"""双手持枪：算第一人称双臂（右手握把 + 左手托护木）的摆放，并渲染预览。

坐标系
  · 相机空间：相机在原点、+x 右、+y 上、−z 前（与 WeaponMount 一致）
  · 几何用**像素**（16 px = 1 格），与原版 display / 物品渲染同一口径

原版事实（1.20.1 源码核对过）
  · 放物品的位置 = Trans(±0.56, −0.52, −0.72) · Trans(display/16) · S ·（模型像素）
  · PlayerRenderer.renderHand 会 resetPose()，所以手臂方块在 **pose 坐标** 里占：
      右臂 x[-0.5,-0.25] y[0,0.75] z[-0.125,0.125]
      左臂 x[ 0.25,0.5]  y[0,0.75] z[-0.125,0.125]      （单位：格）
    即原点那一端是肩膀，+0.75 那一端是手。
  · 所以「把手放到 H」= 原点平移 H − s·R·(方块x中心, 0.75, 0)

用法: python tools/_dblhold.py [--out build/_dblhold.png]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_view as gv  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, 'src/main/resources/assets/hexalunar_calamity/geo/akm.geo.json')
TEX = os.path.join(ROOT, 'src/main/resources/assets/hexalunar_calamity/textures/models/akm_geo.png')
ITEM = os.path.join(ROOT, 'src/main/resources/assets/hexalunar_calamity/models/item/akm.json')

PX = 16.0                                            # 像素 → 格
ARM_FP = np.array([0.56, -0.52, -0.72])              # 格
ARM_W, ARM_L, ARM_D = 0.25, 0.75, 0.25               # 手臂方块（格）
ARM_XC = {'right': -0.375, 'left': 0.375}            # 方块在 pose 坐标系里的 x 中心
# 手臂粗细倍率（对应 Java 的 WeaponArms.THICK）
THICK = 0.85

# 可调参数（格）：肩点 / 手要放到的模型像素点 / 掌朝向自转
# ★ 必须与 WeaponArms.SHOULDER_R / SHOULDER_L 一致
SHOULDER = {'right': np.array([0.55, -0.85, -0.80]), 'left': np.array([-0.42, -0.85, -0.78])}
HAND_PX = {'right': [0.0, 0.55, -0.15], 'left': [0.0, 2.05, -6.30]}
HAND_NUDGE = {'right': np.array([0.0, 0.0, 0.0]), 'left': np.array([0.0, 0.0, 0.0])}
ROLL = {'right': 155.0, 'left': 24.0}


def rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler_from(Rm):
    """Rx(a)·Ry(b)·Rz(c) = Rm → (a, b, c)（度）"""
    b = math.asin(max(-1.0, min(1.0, float(Rm[0, 2]))))
    a = math.atan2(-float(Rm[1, 2]), float(Rm[2, 2]))
    c = math.atan2(-float(Rm[0, 1]), float(Rm[0, 0]))
    return math.degrees(a), math.degrees(b), math.degrees(c)


def arm_frame(side, hand, shoulder):
    y = np.asarray(hand, dtype=float) - np.asarray(shoulder, dtype=float)
    dist = float(np.linalg.norm(y))
    s = dist / ARM_L
    y = y / dist
    ref = np.array([0.0, 1.0, 0.0])
    if abs(float(np.dot(ref, y))) > 0.95:
        ref = np.array([0.0, 0.0, -1.0])
    z = np.cross(y, ref)
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    r = math.radians(ROLL[side])
    xr = x * math.cos(r) + z * math.sin(r)
    zr = -x * math.sin(r) + z * math.cos(r)
    basis = np.stack([xr, y, zr], axis=1)
    a, b, c = euler_from(basis)
    back = rx(a) @ ry(b) @ rz(c)
    err = float(np.abs(back - basis).max())
    # 只沿手臂长度方向拉伸（粗细保持原版），否则整条胳膊会变成大棒子
    origin = np.asarray(hand, dtype=float) - basis @ np.array([ARM_XC[side] * THICK, ARM_L * s, 0.0])
    return origin, s, (a, b, c), err, basis


def cam(p_px, trans, rot, scale):
    rm = rx(rot[0]) @ ry(rot[1]) @ rz(rot[2])
    return ARM_FP + np.asarray(trans, dtype=float) / PX + rm @ (np.array(scale) * np.asarray(p_px) / PX)


def box_faces(origin_px, s, basis, xc_px):
    """手臂方块 6 个面（像素；局部几何 = resetPose 后的方块，宽厚 4px / 长 12px）

    只有长度方向乘 s，粗细不变 —— 对应 Java 里的 pose.scale(1, s, 1)。
    """
    xs = [xc_px - 2.0 * THICK, xc_px + 2.0 * THICK]
    ys = [0.0, 12.0 * s]
    zs = [-2.0 * THICK, 2.0 * THICK]
    pts = [origin_px + (basis @ np.array([x, y, z]))
           for x in xs for y in ys for z in zs]
    idx = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
    return [[pts[i] for i in q] for q in idx]


def main():
    disp = json.load(open(ITEM, encoding='utf-8'))['display']['firstperson_righthand']
    trans = disp.get('translation', [0, 0, 0])
    rot = disp.get('rotation', [0, 0, 0])
    scale = disp.get('scale', [1, 1, 1])

    arms = []
    print('== 可直接写进 Java 的常数（相机空间；位移单位=格，Java 里再 *16 用像素也行）')
    for side in ('right', 'left'):
        hand_px = np.array(HAND_PX[side], dtype=float) + HAND_NUDGE[side] * PX
        hand = cam(hand_px, trans, rot, scale)
        origin, s, ang, err, basis = arm_frame(side, hand, SHOULDER[side])
        print('[%s] 手 = (%.3f, %.3f, %.3f)  缩放 %.3f  欧拉角(%.2f, %.2f, %.2f)  误差 %.1e'
              % (side, hand[0], hand[1], hand[2], s, ang[0], ang[1], ang[2], err))
        print('       原点 = (%.3f, %.3f, %.3f)  = 像素 (%.2f, %.2f, %.2f)'
              % (origin[0], origin[1], origin[2], origin[0] * PX, origin[1] * PX, origin[2] * PX))
        arms.append((origin * PX, s, basis, ARM_XC[side] * PX))

    quads, g = gv.collect(GEO)
    uv_w = g['description'].get('texture_width', 512)
    uv_h = g['description'].get('texture_height', 512)
    texture = Image.open(TEX).convert('RGBA')
    rm = rx(rot[0]) @ ry(rot[1]) @ rz(rot[2])
    off = ARM_FP * PX + np.asarray(trans, dtype=float)      # 像素

    gun = [[np.asarray(p, dtype=float) @ np.diag(scale) @ rm.T + off
            for p in pts] for (_f, pts, _r, _n) in quads]
    gun_uv = [(_r, _f) for (_f, pts, _r, _n) in quads]
    arm_boxes = [box_faces(origin, s, basis, xc) for (origin, s, basis, xc) in arms]

    render(gun, gun_uv, arm_boxes, texture, uv_w, uv_h, 0.0, 'build/_dblhold.png')
    render(gun, gun_uv, arm_boxes, texture, uv_w, uv_h, 0.45, 'build/_dblhold_back.png')


def render(gun, gun_uv, arm_boxes, texture, uv_w, uv_h, back_px_blocks, out_rel):
    """相机在 (0,0,back) 看向 -Z（back=0 就是游戏第一人称），16:9 / 垂直 FOV 70"""
    w, h = 780, 439
    f = (h / 2.0) / math.tan(math.radians(70.0) / 2.0)
    cam_z = back_px_blocks * PX

    def proj(p):
        x, y = float(p[0]), float(p[1])
        depth = cam_z - float(p[2])
        depth = max(depth, 0.05)
        return (w / 2.0 + f * x / depth, h / 2.0 - f * y / depth, depth)

    draw = []

    def push(p3, col):
        d = float(np.mean([cam_z - np.asarray(p)[2] for p in p3]))
        draw.append((d, [proj(p) for p in p3], col))

    for quad, (rect, fname) in zip(gun, gun_uv):
        push(quad, gv.sample(texture, rect, uv_w, uv_h, fname))
    for i, faces in enumerate(arm_boxes):
        col = (198, 86, 70) if i == 0 else (72, 140, 196)
        for q in faces:
            push(q, col)
    draw.sort(key=lambda t: -t[0])

    img = Image.new('RGB', (w, h), (238, 240, 244))
    dr = ImageDraw.Draw(img)
    for _d, poly, col in draw:
        dr.polygon([(p[0], p[1]) for p in poly], fill=col)
    out = os.path.join(ROOT, out_rel)
    img.save(out)
    print('wrote %s' % out)


if __name__ == '__main__':
    main()
