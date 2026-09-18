#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AKM v2：按参考模型比例手工重建的方块版 AKM（GeckoLib cube 模型 + 512² 贴图）。

设计来源：模型/akm.bbmodel 的 PCA 对齐测量（tools/ref_ortho.py / ref_parts.py），
配色来自参考贴图分区采样（见 tools/ref_parts.py 注释）。

坐标系（与 mod 约定一致）：前向 = -Z，上 = +Y，原点 = 握把。枪管轴线 Y = 1.75。
输出：build/akm_v2.geo.json + build/akm_v2.png
"""
import json
import math
import os

from PIL import Image, ImageDraw

SIZE = 512
BORE = 1.75          # 枪管轴线高度
S = 11.0             # 每模型单位分配的贴图像素数（贴图密度）

# ------------------------------------------------------------------ 调色板
STEEL_RCV = (84, 79, 77)     # 机匣（磷化钢）
STEEL_DC = (94, 89, 87)      # 机匣盖
STEEL_BAR = (60, 59, 57)     # 枪管 / 准星座 / 导气箍
STEEL_GAS = (71, 70, 67)     # 导气管 / 通条
MZ = (50, 49, 48)            # 枪口制退器（发蓝）
BOLT = (116, 118, 122)       # 枪机 / 拉机柄（精加工钢）
MAG = (74, 71, 69)           # 弹匣（冲压钢）
WOOD_HG = (176, 100, 52)     # 护木（清漆木）
WOOD_STK = (154, 84, 44)     # 枪托（清漆木，略深）
GRIP = (78, 48, 40)          # 握把（胶木）
RUBBER = (46, 44, 46)        # 托底板
SIGHT = (44, 43, 44)         # 照门 / 准星
SEL = (66, 66, 68)           # 保险机柄
BRASS = (168, 132, 62)       # 黄铜（弹匣内可见的弹头）

FACE_SEED = {'north': 11, 'south': 29, 'east': 47, 'west': 71, 'up': 89, 'down': 103}


# ------------------------------------------------------------------ 图集
class Pack(object):
    """512² 货架式装箱：每个面单独一块，保证比例正确、可做逐面 AO。"""

    def __init__(self, size=SIZE):
        self.size = size
        self.x = 1
        self.y = 1
        self.rowh = 0
        self.boxes = {}

    def alloc(self, key, w, h):
        w = max(2, int(math.ceil(w)))
        h = max(2, int(math.ceil(h)))
        if self.x + w > self.size - 1:
            self.x = 1
            self.y += self.rowh + 1
            self.rowh = 0
        if self.y + h > self.size - 1:
            raise RuntimeError('atlas overflow at %s (%d,%d)' % (key, w, h))
        r = (self.x, self.y, w, h)
        self.x += w + 1
        self.rowh = max(self.rowh, h)
        self.boxes[key] = r
        return r


class LC(object):
    def __init__(self, seed):
        self.s = (seed * 1103515245 + 12345) & 0x7FFFFFFF or 1

    def f(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s / float(0x7FFFFFFF)

    def r(self, a, b):
        return a + (b - a) * self.f()

    def ri(self, a, b):
        return int(self.r(a, b + 0.999))


def cl(v):
    return int(max(0, min(255, v)))


def sh(c, f, add=0):
    return (cl(c[0] * f + add), cl(c[1] * f + add), cl(c[2] * f + add))


# ------------------------------------------------------------------ 各材质画法
def paint(img, rect, mat, face, tag, seed):
    """在 rect 里画一个面。face ∈ up/down/north/south/east/west。"""
    x, y, w, h = rect
    px = img.load()
    rn = LC(seed)
    base = mat
    horiz = w >= h          # 长边水平 → 纹理沿水平走

    # 底色 + 噪声
    if mat in (WOOD_HG, WOOD_STK):
        for j in range(h):
            grain = math.sin(j * rn.r(0.55, 0.95) + seed) * 0.5 + 0.5
            f = 0.90 + 0.16 * grain + rn.r(-0.05, 0.05)
            band = 1.0
            for k in range(2):        # 木纹长条
                if (j + k * 9) % 13 == 0:
                    band = 0.84
            for i in range(w):
                c = sh(base, f * band * (1.0 - 0.06 * abs(i / max(w - 1, 1) - 0.5) * 2))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
        # 清漆高光
        for j in range(h):
            if rn.f() < 0.12:
                f = rn.r(1.10, 1.18)
                for i in range(w):
                    c = px[x + i, y + j]
                    px[x + i, y + j] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)
    elif mat == GRIP:
        for j in range(h):
            for i in range(w):
                chk = 0.86 if ((i // 2 + j // 2) % 2 == 0) else 1.06
                c = sh(base, chk * rn.r(0.94, 1.06))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
    elif mat == MAG:
        for j in range(h):
            rib = (j % 4 == 0 or j % 4 == 1)
            f = 0.86 if rib else 1.05
            for i in range(w):
                c = sh(base, f * rn.r(0.95, 1.05))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
            px[x + w - 1, y + j] = sh(base, 0.70)
    elif mat in (BOLT,):
        for j in range(h):
            for i in range(w):
                f = 0.94 + 0.10 * math.sin(i * 0.8 + seed) + rn.r(-0.035, 0.035)
                c = sh(base, f)
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
    else:
        # 通用钢：细噪声 + 轻微磨损斑 + 长向拉丝
        for j in range(h):
            rowf = 1.0 + rn.r(-0.045, 0.045)
            for i in range(w):
                c = sh(base, rowf * rn.r(0.955, 1.045))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
        for _ in range(int(w * h / 45) + 1):
            bx, by = rn.ri(0, w - 1), rn.ri(0, h - 1)
            f = rn.r(0.80, 0.90) if rn.f() < 0.6 else rn.r(1.06, 1.14)
            n = rn.ri(1, max(1, (w if horiz else h) // 4))
            for k in range(n):
                if horiz:
                    xx, yy = min(w - 1, bx + k), by
                else:
                    xx, yy = bx, min(h - 1, by + k)
                c = px[x + xx, y + yy]
                px[x + xx, y + yy] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)

    # ---- 逐面细节 ----
    if tag == 'receiver_r':          # 抛壳口 + 铆钉
        px_x0, px_x1 = int(w * 0.62), int(w * 0.82)
        py0, py1 = int(h * 0.16), int(h * 0.44)
        d = ImageDraw.Draw(img)
        d.rectangle([x + px_x0, y + py0, x + px_x1, y + py1], fill=(22, 22, 24, 255))
        d.line([(x + px_x0, y + py0), (x + px_x1, y + py0)], fill=(132, 134, 138, 255))
        d.line([(x + px_x0, y + py1), (x + px_x1, y + py1)], fill=(16, 16, 18, 255))
        d.line([(x + px_x1, y + py0), (x + px_x1, y + py1)], fill=(112, 114, 118, 255))
        # 机匣铆钉
        for rx in (0.12, 0.42):
            for ry in (0.30, 0.74):
                cx, cy = x + int(w * rx), y + int(h * ry)
                d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(122, 124, 128, 255))
                d.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=(72, 74, 78, 255))
    elif tag == 'receiver_l':        # 左侧：光学导轨 + 铆钉
        d = ImageDraw.Draw(img)
        d.rectangle([x + int(w * 0.14), y + int(h * 0.16), x + int(w * 0.62), y + int(h * 0.34)],
                    fill=(77, 77, 79, 255))
        d.rectangle([x + int(w * 0.14), y + int(h * 0.16), x + int(w * 0.62), y + int(h * 0.19)],
                    fill=(112, 112, 116, 255))
        for rx in (0.08, 0.30, 0.86):
            cx, cy = x + int(w * rx), y + int(h * 0.80)
            d.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=(112, 114, 118, 255))
    elif tag == 'dust_cover_top':
        d = ImageDraw.Draw(img)
        for i in range(int(w * 0.72), w - 2, 3):   # 后端散热加强筋
            d.line([(x + i, y + 2), (x + i, y + h - 3)], fill=sh(base, 0.80))
    elif tag == 'handguard_side':
        d = ImageDraw.Draw(img)
        for k in range(3):                          # 护木上的三道指槽
            cx = int(w * (0.28 + 0.20 * k))
            d.line([(x + cx, y + 2), (x + cx, y + h - 3)], fill=sh(base, 0.74))
            d.line([(x + cx + 1, y + 2), (x + cx + 1, y + h - 3)], fill=sh(base, 1.12))
    elif tag == 'mag_side':
        d = ImageDraw.Draw(img)
        d.rectangle([x, y + h - 4, x + w - 1, y + h - 1], fill=sh(MAG, 1.14))
    elif tag == 'barrel_side':
        d = ImageDraw.Draw(img)
        d.line([(x, y + 1), (x + w - 1, y + 1)], fill=sh(base, 1.16))
    elif tag == 'grip_side':
        d = ImageDraw.Draw(img)
        for i in range(2, h - 2, 3):                # 胶木防滑纹
            d.line([(x + 1, y + i), (x + w - 2, y + i)], fill=sh(base, 0.82))

    # ---- 抛光层：竖向光泽渐变 + 倒角高光带 + 镜面高光斑（与 boxlib 的抛光一致）----
    for j in range(h):
        t = j / float(max(h - 1, 1))
        f = 1.0 + 0.085 * (1.0 - t) ** 1.6
        for i in range(w):
            c = px[x + i, y + j]
            px[x + i, y + j] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)

    # ---- 边缘 AO / 倒角：上沿给高光（磨亮的棱），下沿给反光暗带；左右仍轻微收暗 ----
    b = 1 if min(w, h) <= 10 else 2
    hi = (1.28, 1.13)
    lo = (0.72, 0.87)
    for i in range(w):
        for k in range(b):
            f = hi[k]
            c = px[x + i, y + k]
            px[x + i, y + k] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)
            f = lo[k]
            c = px[x + i, y + h - 1 - k]
            px[x + i, y + h - 1 - k] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)
    for j in range(h):
        for k in range(b):
            f = 1.0 - 0.15 * (1.0 - k / float(b))
            for xx in (x + k, x + w - 1 - k):
                c = px[xx, y + j]
                px[xx, y + j] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)
    # 高光斑：上半部几道短亮线（抛光金属的反光痕）
    if min(w, h) >= 6 and mat not in (WOOD_HG, WOOD_STK, GRIP):
        for _ in range(int(w * h / 300.0) + 1):
            bx, by = rn.ri(0, max(0, w - 1)), rn.ri(0, max(0, h // 3))
            ln = rn.ri(1, max(1, w // 3))
            fl = rn.r(1.20, 1.42)
            for kk in range(ln):
                xx = min(w - 1, bx + kk)
                c = px[x + xx, y + by]
                px[x + xx, y + by] = (cl(c[0] * fl), cl(c[1] * fl), cl(c[2] * fl), 255)
    if face == 'up':
        for i in range(w):
            for k in range(b + 1):
                c = px[x + i, y + k]
                px[x + i, y + k] = (cl(c[0] * 1.10), cl(c[1] * 1.10), cl(c[2] * 1.10), 255)
    if face == 'down':
        for i in range(w):
            for k in range(b + 1):
                c = px[x + i, y + h - 1 - k]
                px[x + i, y + h - 1 - k] = (cl(c[0] * 0.86), cl(c[1] * 0.86), cl(c[2] * 0.86), 255)


# ------------------------------------------------------------------ 几何
def C(bone, name, x, y, z, mat, rot=None, piv=None, tag=None, mirror_uv=False):
    return {'bone': bone, 'name': name, 'x': x, 'y': y, 'z': z, 'mat': mat,
            'rot': rot, 'piv': piv, 'tag': tag, 'mirror': mirror_uv}


BONES = [
    # name,        parent,  pivot
    ('root', None, (0.0, BORE, 0.0)),
    ('move', 'root', (0.0, BORE, 0.0)),
    ('body', 'move', (0.0, BORE, -2.60)),
    ('barrel', 'body', (0.0, BORE, -9.30)),
    ('sights', 'body', (0.0, 2.40, -8.00)),
    ('handguard', 'body', (0.0, 2.20, -6.30)),
    ('dust_cover', 'body', (0.0, 2.96, -4.50)),
    ('bolt', 'body', (0.0, 2.55, -3.60)),
    ('magazine', 'body', (0.0, 1.45, -3.78)),
    ('trigger', 'body', (0.0, 1.25, -1.55)),
    ('grip', 'body', (0.0, 1.30, -0.05)),
    ('stock', 'body', (0.0, 2.00, 0.22)),
    ('selector', 'body', (0.0, 2.60, -4.30)),
    ('camera', 'body', (0.0, 2.65, -1.85)),
]

CUBES = [
    # ---------------- 枪口 / 枪管 / 准星 / 导气箍（barrel）
    C('barrel', 'muzzle_low', (-0.22, 0.22), (1.52, 1.68), (-11.34, -10.88), MZ, tag='barrel_side'),
    C('barrel', 'muzzle_mid', (-0.22, 0.22), (1.68, 1.84), (-11.26, -10.88), MZ, tag='barrel_side'),
    C('barrel', 'muzzle_high', (-0.22, 0.22), (1.84, 1.98), (-11.18, -10.88), MZ, tag='barrel_side'),
    C('barrel', 'muzzle_ring', (-0.25, 0.25), (1.49, 2.01), (-10.98, -10.88), MZ),
    C('barrel', 'barrel', (-0.19, 0.19), (1.56, 1.94), (-10.96, -5.30), STEEL_BAR, tag='barrel_side'),
    C('barrel', 'barrel_ring1', (-0.22, 0.22), (1.53, 1.97), (-10.44, -10.36), STEEL_GAS),
    C('barrel', 'barrel_ring2', (-0.22, 0.22), (1.53, 1.97), (-9.74, -9.66), STEEL_GAS),
    C('barrel', 'fsb', (-0.25, 0.25), (1.48, 2.02), (-11.04, -10.30), STEEL_BAR, tag='barrel_side'),
    C('barrel', 'fsb_top', (-0.21, 0.21), (2.02, 2.28), (-10.98, -10.40), STEEL_BAR),
    # 准星柱加高到与照门叶片顶齐平（Y 3.44）—— 瞄准时才是「枪身上方一条平行于枪管的直线」；
    # 两侧护耳（3.34）略低于柱顶，柱尖仍露出来。
    C('barrel', 'fs_post', (-0.09, 0.09), (2.20, 3.44), (-10.86, -10.58), SIGHT),
    C('barrel', 'fs_ear_l', (-0.24, -0.12), (2.24, 3.34), (-10.88, -10.56), STEEL_BAR),
    C('barrel', 'fs_ear_r', (0.12, 0.24), (2.24, 3.34), (-10.88, -10.56), STEEL_BAR),
    C('barrel', 'gas_block', (-0.27, 0.27), (1.42, 2.14), (-9.32, -8.58), STEEL_GAS),
    C('barrel', 'gas_block_up', (-0.24, 0.24), (2.04, 2.50), (-9.28, -8.62), STEEL_GAS,
      rot=(20, 0, 0), piv=(0, 2.04, -8.62)),
    C('barrel', 'gas_block_clamp', (-0.26, 0.26), (1.96, 2.22), (-9.44, -9.22), STEEL_GAS),
    C('barrel', 'cleaning_rod', (-0.07, 0.07), (1.38, 1.52), (-10.90, -7.00), STEEL_GAS),
    C('barrel', 'sling_loop_front', (-0.16, 0.16), (1.16, 1.40), (-9.62, -9.38), BOLT),
    # ---------------- 导气管 / 照门（sights）
    C('sights', 'gas_tube_a', (-0.21, 0.21), (2.04, 2.52), (-8.60, -5.34), STEEL_GAS, tag='barrel_side'),
    C('sights', 'gas_tube_b', (-0.15, 0.15), (1.98, 2.58), (-8.60, -5.34), STEEL_GAS, tag='barrel_side'),
    C('sights', 'rear_sight_base', (-0.34, 0.34), (2.86, 3.24), (-5.34, -4.36), STEEL_BAR),
    C('sights', 'rear_sight_leaf', (-0.26, 0.26), (3.24, 3.40), (-5.06, -4.42), SIGHT,
      rot=(-8, 0, 0), piv=(0, 3.24, -4.42)),
    C('sights', 'rear_sight_knob', (0.34, 0.46), (3.02, 3.20), (-4.98, -4.64), BOLT),
    # ---------------- 细节件（r42）：机匣铆钉 / 护木散热片 / 背带环 / 托底板
    C('body', 'rcv_bolt_l0', (-0.68, -0.62), (1.58, 1.82), (-4.46, -4.22), STEEL_BAR),
    C('body', 'rcv_bolt_r0', (0.60, 0.66), (1.58, 1.82), (-4.46, -4.22), STEEL_BAR),
    C('body', 'rcv_bolt_l1', (-0.68, -0.62), (1.58, 1.82), (-2.84, -2.60), STEEL_BAR),
    C('body', 'rcv_bolt_r1', (0.60, 0.66), (1.58, 1.82), (-2.84, -2.60), STEEL_BAR),
    C('body', 'rcv_bolt_l2', (-0.68, -0.62), (1.58, 1.82), (-1.22, -0.98), STEEL_BAR),
    C('body', 'rcv_bolt_r2', (0.60, 0.66), (1.58, 1.82), (-1.22, -0.98), STEEL_BAR),
    C('handguard', 'hg_fin_l0', (-0.57, -0.47), (2.84, 2.96), (-7.05, -6.85), STEEL_BAR),
    C('handguard', 'hg_fin_r0', (0.47, 0.57), (2.84, 2.96), (-7.05, -6.85), STEEL_BAR),
    C('handguard', 'hg_fin_l1', (-0.57, -0.47), (2.84, 2.96), (-6.65, -6.45), STEEL_BAR),
    C('handguard', 'hg_fin_r1', (0.47, 0.57), (2.84, 2.96), (-6.65, -6.45), STEEL_BAR),
    C('handguard', 'hg_fin_l2', (-0.57, -0.47), (2.84, 2.96), (-6.25, -6.05), STEEL_BAR),
    C('handguard', 'hg_fin_r2', (0.47, 0.57), (2.84, 2.96), (-6.25, -6.05), STEEL_BAR),
    C('handguard', 'hg_fin_l3', (-0.57, -0.47), (2.84, 2.96), (-5.85, -5.65), STEEL_BAR),
    C('handguard', 'hg_fin_r3', (0.47, 0.57), (2.84, 2.96), (-5.85, -5.65), STEEL_BAR),
    C('stock', 'sling_t', (-0.70, -0.56), (1.84, 1.98), (3.56, 4.20), STEEL_BAR),
    C('stock', 'sling_b', (-0.70, -0.56), (1.06, 1.20), (3.56, 4.20), STEEL_BAR),
    C('stock', 'sling_f', (-0.70, -0.56), (1.06, 1.98), (3.56, 3.70), STEEL_BAR),
    C('stock', 'sling_r', (-0.70, -0.56), (1.06, 1.98), (4.06, 4.20), STEEL_BAR),
    C('stock', 'butt_plate', (-0.52, 0.52), (0.66, 2.90), (4.84, 4.94), SIGHT),
    C('stock', 'butt_bolt_a', (-0.26, 0.26), (1.32, 1.44), (4.94, 5.00), STEEL_BAR),
    C('stock', 'butt_bolt_b', (-0.26, 0.26), (2.06, 2.18), (4.94, 5.00), STEEL_BAR),    # ---------------- 护木（handguard）
    C('handguard', 'hg_lower', (-0.55, 0.55), (1.42, 2.06), (-7.30, -5.34), WOOD_HG, tag='handguard_side'),
    C('handguard', 'hg_lower_belly', (-0.46, 0.46), (1.34, 1.46), (-7.10, -5.44), WOOD_HG),
    C('handguard', 'hg_upper', (-0.46, 0.46), (2.06, 2.84), (-7.26, -5.36), WOOD_HG, tag='handguard_side'),
    C('handguard', 'hg_cap_front', (-0.50, 0.50), (1.40, 2.88), (-7.40, -7.24), STEEL_BAR),
    C('handguard', 'hg_cap_rear', (-0.50, 0.50), (1.40, 2.88), (-5.44, -5.30), STEEL_BAR),
    # ---------------- 机匣盖（dust_cover）
    C('dust_cover', 'dc_top', (-0.42, 0.42), (3.14, 3.28), (-4.50, 0.22), STEEL_DC, tag='dust_cover_top'),
    C('dust_cover', 'dc_left', (-0.55, -0.34), (2.92, 3.18), (-4.50, 0.22), STEEL_DC),
    C('dust_cover', 'dc_right', (0.34, 0.55), (2.92, 3.18), (-4.50, 0.22), STEEL_DC),
    C('dust_cover', 'dc_front', (-0.55, 0.55), (2.92, 3.26), (-4.56, -4.32), STEEL_DC),
    C('dust_cover', 'dc_rear', (-0.55, 0.55), (2.86, 3.24), (0.06, 0.30), STEEL_DC),
    # ---------------- 枪机 / 拉机柄（bolt）
    C('bolt', 'bolt_carrier', (-0.32, 0.32), (2.40, 2.90), (-4.48, 0.14), BOLT),
    C('bolt', 'charging_handle', (0.32, 0.94), (2.50, 2.78), (-3.78, -3.30), BOLT),
    # ---------------- 机匣（body）
    C('body', 'receiver', (-0.55, 0.55), (1.16, 2.94), (-5.32, 0.22), STEEL_RCV, tag='receiver_r'),
    C('body', 'receiver_trunnion', (-0.58, 0.58), (1.16, 3.00), (-5.34, -4.90), STEEL_RCV),
    C('body', 'mag_well', (-0.54, 0.54), (1.02, 1.42), (-4.36, -3.18), STEEL_RCV),
    C('body', 'mag_well_flare', (-0.59, 0.59), (0.92, 1.06), (-4.40, -3.14), STEEL_RCV),
    C('body', 'stock_tang', (-0.30, 0.30), (2.36, 2.94), (0.22, 0.70), STEEL_RCV),
    C('body', 'receiver_rail', (-0.62, -0.55), (2.20, 2.62), (-4.30, -1.20), SEL),
    # ---------------- 弹匣（magazine）：弧形分段
    C('magazine', 'mag_feed', (-0.53, 0.53), (1.40, 1.60), (-4.36, -3.18), MAG),
    # ---------------- 扳机 / 护圈（trigger）
    C('trigger', 'tg_front', (-0.28, 0.28), (0.72, 1.22), (-1.54, -1.32), STEEL_RCV),
    C('trigger', 'tg_bottom', (-0.28, 0.28), (0.72, 0.90), (-1.54, 0.20), STEEL_RCV),
    C('trigger', 'tg_rear', (-0.28, 0.28), (0.72, 1.26), (0.02, 0.26), STEEL_RCV),
    C('trigger', 'trigger', (-0.09, 0.09), (0.92, 1.44), (-0.90, -0.72), BOLT,
      rot=(14, 0, 0), piv=(0, 1.44, -0.90)),
    # ---------------- 握把（grip）
    C('grip', 'grip_upper', (-0.35, 0.35), (0.94, 1.46), (-0.64, 0.28), GRIP, tag='grip_side'),
    C('grip', 'grip_lower', (-0.42, 0.42), (0.28, 1.00), (-0.56, 0.46), GRIP, tag='grip_side'),
    C('grip', 'grip_cap', (-0.42, 0.42), (0.22, 0.32), (-0.58, 0.48), STEEL_RCV),
    # ---------------- 枪托（stock）
    C('stock', 'stock_wrist', (-0.40, 0.40), (1.62, 2.72), (0.22, 1.10), WOOD_STK, tag='handguard_side'),
    C('stock', 'stock_1', (-0.50, 0.50), (1.50, 2.78), (1.10, 2.30), WOOD_STK, tag='handguard_side'),
    C('stock', 'stock_2', (-0.54, 0.54), (1.26, 2.85), (2.30, 3.50), WOOD_STK, tag='handguard_side'),
    C('stock', 'stock_3', (-0.56, 0.56), (0.94, 2.89), (3.50, 4.58), WOOD_STK, tag='handguard_side'),
    C('stock', 'stock_band', (-0.58, 0.58), (0.88, 2.93), (4.46, 4.60), STEEL_RCV),
    C('stock', 'butt_plate', (-0.58, 0.58), (0.84, 2.94), (4.60, 4.84), RUBBER),
    C('stock', 'sling_swivel', (-0.10, 0.10), (0.62, 0.92), (3.86, 4.08), BOLT),
    C('stock', 'stock_bolt', (-0.38, 0.38), (2.40, 2.80), (1.04, 1.16), BOLT),
    # ---------------- 保险机柄（selector）
    C('selector', 'sel_body', (0.48, 0.60), (2.10, 3.06), (-4.52, -2.16), SEL),
    C('selector', 'sel_flag', (0.48, 0.60), (2.84, 3.12), (-4.52, -4.08), SEL),
    C('selector', 'sel_tab', (0.60, 0.80), (2.28, 2.58), (-3.10, -2.78), SEL),
]

MAG_SEGS = 7
MAG_STEP = 0.485
MAG_ANG = 5.2


def build_magazine():
    """弹匣主体：从弹匣井往下前方弯的弧形分段。"""
    out = []
    y0, z0 = 1.42, -3.77        # 顶面中心
    ang = 0.0
    for i in range(MAG_SEGS):
        a = math.radians(ang)
        dy, dz = -MAG_STEP * math.cos(a), -MAG_STEP * math.sin(a)
        y1, z1 = y0 + dy, z0 + dz
        w = 0.52 if i < MAG_SEGS - 1 else 0.54
        d = 0.58
        rot = ang if i else None
        out.append(C('magazine', 'mag_%d' % i,
                     (-w, w), (min(y0, y1), max(y0, y1)), (z0 - d / 2, z0 + d / 2),
                     MAG, rot=(rot, 0, 0) if rot is not None else None,
                     piv=(0, y0, z0), tag='mag_side'))
        y0, z0 = y1, z1
        ang += MAG_ANG
    a = math.radians(ang - MAG_ANG)
    out.append(C('magazine', 'mag_floor', (-0.55, 0.55), (y0 - 0.16, y0 + 0.02),
                 (z0 - 0.36, z0 + 0.36), STEEL_RCV, rot=(ang - MAG_ANG, 0, 0), piv=(0, y0, z0)))
    return out


CUBES += build_magazine()


# ------------------------------------------------------------------ 生成
def face_uv(pack, img, key, mat, face, tag, pw, ph, seed):
    rect = pack.alloc(key, pw, ph)
    paint(img, rect, mat, face, tag, seed)
    x, y, w, h = rect
    return [float(x), float(y)], [float(w), float(h)]


def build():
    img = Image.new('RGBA', (SIZE, SIZE), (12, 12, 12, 255))
    pack = Pack()
    geo_bones = {b[0]: {'name': b[0], 'pivot': list(b[2])} for b in BONES}
    for name, parent, _p in BONES:
        if parent:
            geo_bones[name]['parent'] = parent
        geo_bones[name]['cubes'] = []

    n = 0
    for cube in CUBES:
        n += 1
        x0, x1 = cube['x']
        y0, y1 = cube['y']
        z0, z1 = cube['z']
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        cube_def = {
            'origin': [round(x0, 4), round(y0, 4), round(z0, 4)],
            'size': [round(sx, 4), round(sy, 4), round(sz, 4)],
        }
        if cube['rot']:
            cube_def['rotation'] = [float(v) for v in cube['rot']]
            cube_def['pivot'] = [float(v) for v in (cube['piv'] or (0, 0, 0))]
        uv = {}
        # 面 -> (宽, 高)  单位模型像素
        faces = {
            'north': (sx, sy), 'south': (sx, sy),
            'east': (sz, sy), 'west': (sz, sy),
            'up': (sx, sz), 'down': (sx, sz),
        }
        for face, (fw, fh) in faces.items():
            tag = cube['tag'] or ''
            tag_f = tag
            if tag == 'receiver_r':
                tag_f = 'receiver_r' if face == 'east' else ('receiver_l' if face == 'west' else '')
            elif tag == 'handguard_side':
                tag_f = tag if face in ('east', 'west') else ''
            elif tag == 'mag_side':
                tag_f = tag if face in ('east', 'west') else ''
            elif tag == 'grip_side':
                tag_f = tag if face in ('east', 'west') else ''
            elif tag == 'dust_cover_top':
                tag_f = tag if face == 'up' else ''
            elif tag == 'barrel_side':
                tag_f = tag if face in ('east', 'west') else ''
            key = '%s/%s/%s' % (cube['bone'], cube['name'], face)
            u, us = face_uv(pack, img, key, cube['mat'], face, tag_f,
                            max(2, fw * S), max(2, fh * S),
                            n * 977 + FACE_SEED[face])
            uv[face] = {'uv': u, 'uv_size': us}
        cube_def['uv'] = uv
        geo_bones[cube['bone']]['cubes'].append(cube_def)

    # 去掉空 cubes 数组以外的键顺序整理
    bones_out = []
    for name, parent, pivot in BONES:
        b = geo_bones[name]
        if not b['cubes']:
            b.pop('cubes')
        bones_out.append(b)

    geo = {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.akm',
                'texture_width': SIZE,
                'texture_height': SIZE,
                'visible_bounds_width': 3,
                'visible_bounds_height': 3,
                'visible_bounds_offset': [0, 0, 0],
            },
            'bones': bones_out,
        }],
    }
    return geo, img


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    geo, img = build()
    p1 = os.path.join(root, 'build', 'akm_v2.geo.json')
    p2 = os.path.join(root, 'build', 'akm_v2.png')
    with open(p1, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, separators=(',', ':'))
    img.save(p2)
    nb = sum(len(b.get('cubes', [])) for b in geo['minecraft:geometry'][0]['bones'])
    print('bones %d  cubes %d' % (len(geo['minecraft:geometry'][0]['bones']), nb))
    print('wrote', p1)
    print('wrote', p2)


if __name__ == '__main__':
    main()
