#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""第一人称预览：按原版手持变换链，把模型**从眼睛透视**渲染出来（离线，不开游戏）。

原版链条（`ItemInHandRenderer` + `ItemRenderer`，本项目的枪都跳过挥剑那两段）：
    相机 = Trans(±0.56, -0.52 - 0.6·equip, -0.72) · Trans(display.t/16) · R(display.rot) · S · (模型像素/16)
相机在眼睛处、朝 -Z 看、+Y 向上、+X 向右；竖直 FOV 默认 70°、画面 16:9。

用法:
  python tools\\_awpfp.py <geo.json> <tex.png> <out.png> [选项]
    --tx/-ty/--tz    display.firstperson_righthand.translation（默认取 AWP 的 -2.6/1.575/0.5）
    --rot rx,ry,rz   display 旋转（默认 0,0,0）
    --fov 70         竖直视场角
    --h 816 --aspect 1.79   输出高度 / 画幅比（默认就是 1462x816 那一档）
    --aim            叠加举枪（ADS）平移；--kick 0..1 开火后坐；--bp 0..1 拉栓进度
    --pitch -12.5    move 骨骼下压角（度，负 = 枪口下压）——默认 0（= 现在 Java 的做法：无额外旋转）
    --hands          把两只手臂画成方块（校核手有没有连在枪上）
    --svg            额外输出一张线框图（看枪管轴线在屏幕上的斜率）
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_texview as gv                                    # noqa: E402  复用逐面 UV 光栅化

# ---------------------------------------------------------------- 与原版一致的手部基准
ARM_X, ARM_Y, ARM_Z = 0.56, -0.52, -0.72
# AWP 的 display（models/item/awp.json → firstperson_righthand）
AWP_T = (-2.6, 1.575, 0.5)
# 举枪增量（WeaponMount.AWP_AIM_*；DY 随 AWP_TY 变：8.32 − 3.15 − TY）
AWP_AIM = (-6.36, 3.595, 1.4)
# 后坐 / move 骨骼 pivot
KICK_BACK = 1.9
MOVE_P = (0.0, -1.0725, 1.305)
# 拉栓
BOLT_P = (0.615, 1.50, 0.375)
BOLT_LIFT, BOLT_BACK = 62.0, 1.9
# 手臂（WeaponArms）
SHOULDER_R = (0.55, -0.85, -0.80)
SHOULDER_L = (-0.42, -0.85, -0.78)
ARM_LEN, THICK, HALF = 0.75, 0.85, 0.375
ROLL_R, ROLL_L = 155.0, 24.0
ARM_GRIP = (0.0, -1.07, 1.31)
ARM_SUPPORT = (0.0, -0.55, -3.30)


def rot_mat(rot_deg):
    return gv.rot_mat(rot_deg)


def xform(pts, rot, trans_px, pitch=0.0):
    """模型像素 → 相机空间（格）。rot 单位度（display 旋转），trans_px 单位模型像素。

    pitch = move 骨骼的 rotX（度，负 = 枪口下压，绕握把 pivot）——与 Java 的
    AwpGeoModel.computeMovePose / GunFrame.toCamera 同一套顺序：先绕 pivot 转，再加平移。
    """
    R = rot_mat(rot)
    a = math.radians(pitch)
    cp, sp = math.cos(a), math.sin(a)
    out = []
    for p in pts:
        q = np.asarray(p, dtype=float)
        if abs(pitch) > 1e-9:
            dy, dz = q[1] - MOVE_P[1], q[2] - MOVE_P[2]
            q = np.array([q[0], MOVE_P[1] + dy * cp - dz * sp, MOVE_P[2] + dy * sp + dz * cp])
        q = R @ q
        out.append((ARM_X + (trans_px[0] + q[0]) / 16.0,
                    ARM_Y + (trans_px[1] + q[1]) / 16.0,
                    ARM_Z + (trans_px[2] + q[2]) / 16.0))
    return out


def load_quads(geo_path, bolt_lift=0.0):
    """读 geo → 逐面世界点（相机空间之前）。bolt_lift 直接改 geo 里 bolt 骨骼的 rotZ。"""
    data = json.load(open(geo_path, encoding='utf-8'))
    g = data['minecraft:geometry'][0]
    if abs(bolt_lift) > 1e-6:
        for b in g['bones']:
            if b['name'] == 'bolt':
                b['rotation'] = [0.0, 0.0, bolt_lift]
    tmp = geo_path + '.tmp_fp.json'
    json.dump(data, open(tmp, 'w', encoding='utf-8'))
    try:
        quads, g2 = gv.collect(tmp)
    finally:
        os.remove(tmp)
    return quads, g2


def project(cam, W, H, fov_y):
    """相机空间点 → (屏幕x, 屏幕y, 1/深度)；在相机后面的点用 w<=0 标记。"""
    f = 1.0 / math.tan(math.radians(fov_y) / 2.0)
    aspect = W / float(H)
    out = []
    for x, y, z in cam:
        w = -z
        if w <= 0.02:
            out.append(None)
            continue
        sx = (x * f / aspect / w + 1.0) * 0.5 * W
        sy = (1.0 - y * f / w) * 0.5 * H
        out.append((sx, sy, 1.0 / w))
    return out


def render(geo, tex_path, out, trans=AWP_T, rot=(0.0, 0.0, 0.0), fov=70.0, size=900,
           aim=False, kick=0.0, bp=-1.0, hands=False, ss=2, aspect=None, pitch=0.0):
    quads, g = load_quads(geo, 0.0 if bp < 0 else bolt_lift_at(bp) * BOLT_LIFT)
    tw = float(g['description'].get('texture_width', 512))
    th = float(g['description'].get('texture_height', 512))
    tex = np.asarray(Image.open(tex_path).convert('RGB'), dtype=np.float32)
    TH, TW = tex.shape[0], tex.shape[1]
    ux, uy = TW / tw, TH / th

    # move 骨骼姿态（举枪平移 + 后坐 + 腰射下压角）——整个模型都挂在 move 下，
    # 所以下压角直接对所有顶点绕握把 pivot 转一次（和 Java 的 move 骨骼完全等价）
    pitch = 0.0 if aim else pitch
    t = [trans[0], trans[1], trans[2]]
    pose = [0.0, 0.0, 0.0]
    if aim:
        pose[0] += AWP_AIM[0]
        pose[1] += AWP_AIM[1]
        pose[2] += AWP_AIM[2]
    pose[2] += KICK_BACK * kick
    t[0] += pose[0]
    t[1] += pose[1]
    t[2] += pose[2]

    W = int(round(size * ss * (aspect if aspect else 1.0)))
    H = size * ss
    color = np.empty((H, W, 3), dtype=np.float32)
    color[:, :] = gv.BG
    zbuf = np.zeros((H, W), dtype=np.float64)

    def draw(verts, rect, shade, cols=(0, 1, 2), rgba=None):
        pp = project(xform(verts, rot, t, pitch), W, H, fov)
        if any(p is None for p in pp):
            return
        for tri in ((0, 1, 2), (0, 2, 3)):
            a, b, c = (pp[i] for i in tri)
            uva, uvb, uvc = (gv.UVQ[i] for i in tri)
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
            invz = w0 * a[2] + w1 * b[2] + w2 * c[2]          # 线性插值 1/z
            # 透视正确的 UV：插值 u/z、v/z 后除以 1/z
            uiw = (w0 * uva[0] * a[2] + w1 * uvb[0] * b[2] + w2 * uvc[0] * c[2]) / invz
            viw = (w0 * uva[1] * a[2] + w1 * uvb[1] * b[2] + w2 * uvc[1] * c[2]) / invz
            if rgba is None:
                u = uiw * rect[2] + rect[0]
                v = viw * rect[3] + rect[1]
                ui = np.clip((u * ux).astype(np.int32), 0, TW - 1)
                vi = np.clip((v * uy).astype(np.int32), 0, TH - 1)
                col = tex[vi, ui] * shade
            else:
                col = np.empty((gx.shape[0], gx.shape[1], 3), dtype=np.float32)
                col[:, :] = rgba
            sz = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            sc = color[ymin:ymax + 1, xmin:xmax + 1]
            m = inside & (invz > sz)
            sz[m] = invz[m]
            sc[m] = col[m]

    for fname, ps, rect in quads:
        draw(ps, rect, gv.SHADE.get(fname, 1.0))

    # ---------------- 手臂（近似成方块，只为校核「连没连在枪上」）
    if hands:
        for hand_px, shoulder, roll, right in (
                (ARM_GRIP, SHOULDER_R, ROLL_R, True),
                (ARM_SUPPORT, SHOULDER_L, ROLL_L, False)):
            h = xform([hand_px], rot, t, pitch)[0]
            draw_arm(draw, h, shoulder, roll, (214, 166, 133) if right else (196, 148, 118))

    img = Image.fromarray(np.clip(color, 0, 255).astype(np.uint8))
    if ss > 1:
        img = img.resize((W // ss, H // ss), Image.LANCZOS)
    img.save(out)

    # 顺带把枪管轴线投影出来，打印屏幕斜率（判断「平不平」）
    ax = xform([(0.0, 1.575, -0.0), (0.0, 1.575, -16.275)], rot, t, pitch)
    pp = project(ax, W, H, fov)
    if all(p is not None for p in pp):
        (x0, y0, _), (x1, y1, _) = pp
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))        # 屏幕 y 向下为正
        print('%-28s 枪管轴线：近端(%.0f,%.0f) → 远端(%.0f,%.0f)，屏幕倾角 %+.1f°（0 = 水平）'
              % (os.path.basename(out), x0 / ss, y0 / ss, x1 / ss, y1 / ss, ang))
    else:
        print('%-28s 枪管轴线有一部分在相机后面' % os.path.basename(out))


def draw_arm(draw, hand, shoulder, roll_deg, rgb):
    """和 WeaponArms.drawArm 同一套几何：从 shoulder 伸到 hand 的方块。"""
    y = np.array([hand[0] - shoulder[0], hand[1] - shoulder[1], hand[2] - shoulder[2]])
    dist = float(np.linalg.norm(y))
    if dist < 1e-4 or dist > 3.0:
        return
    s = dist / ARM_LEN
    y = y / dist
    ref = np.array([0.0, 1.0, 0.0])
    if abs(float(y @ ref)) > 0.95:
        ref = np.array([0.0, 0.0, -1.0])
    z = np.cross(y, ref)
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    x /= np.linalg.norm(x)
    r = math.radians(roll_deg)
    xr = x * math.cos(r) + z * math.sin(r)
    zr = z * math.cos(r) - x * math.sin(r)
    dx = (-HALF if rgb[0] > 205 else HALF) * THICK
    o = xr * dx + y * (ARM_LEN * s)
    org = np.array(hand) - o
    hw = 0.125 * THICK
    verts = []
    for sx in (-1, 1):
        for sy in (0, 1):
            for sz in (-1, 1):
                verts.append(org + xr * (sx * hw) + y * (sy * ARM_LEN * s) + zr * (sz * hw))
    # 6 面（顺序无所谓，Z-buffer 自己判遮挡）
    faces = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6),
             (0, 2, 6, 4), (1, 3, 7, 5)]
    for f in faces:
        draw([tuple(verts[i]) for i in f], (0, 0, 0, 0), 1.0, rgba=rgb)


def bolt_lift_at(bp):
    if bp < 0:
        return 0.0
    if bp < 0.20:
        return bp / 0.20
    if bp > 0.85:
        return min(1.0, max(0.0, (1.0 - bp) / 0.15))
    return 1.0


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return
    geo, tex, out = argv[1], argv[2], argv[3]
    opt = {}

    def val(name, default):
        if name in argv:
            return argv[argv.index(name) + 1]
        return default

    tx = float(val('--tx', AWP_T[0]))
    ty = float(val('--ty', AWP_T[1]))
    tz = float(val('--tz', AWP_T[2]))
    rot = tuple(float(v) for v in val('--rot', '0,0,0').split(','))
    render(geo, tex, out,
           trans=(tx, ty, tz), rot=rot,
           fov=float(val('--fov', 70.0)), size=int(val('--h', 816)),
           aspect=float(val('--aspect', 1.79)),
           aim=('--aim' in argv), kick=float(val('--kick', 0.0)),
           bp=float(val('--bp', -1.0)), hands=('--hands' in argv),
           pitch=float(val('--pitch', 0.0)))


if __name__ == '__main__':
    main(sys.argv)
