#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AKM v3：按参考照片（木家具 + 黑色磷化钢的 AKM）重建的方块版 GeckoLib 真骨骼模型。

参照照片逐项对齐：
  - 金属：**近黑磷化钢**（照片里机匣/枪管/弹匣几乎全黑，不是 v2 那种灰）
  - 木家具：红棕色清漆木（枪托 / 上下护木 / 握把），带木纹与清漆高光
  - 弹匣：强烈弧度的 30 发钢弹匣 + 竖向加强肋
  - 其余：斜切枪口制退器 / 准星座与护耳 / 导气箍与导气管 / 照门 / 保险机柄 / 拉机柄

★ 几何约定**不能动**（ADS 对准与动画都靠它）：
  - 前向 = -Z，上 = +Y，原点 = 握把；枪管轴线 Y = BORE = 1.75
  - **瞄准线必须水平**：照门顶与准星顶同高 = SIGHT_Y = 3.44、都在 X = 0
    （WeaponPose.AKM_SIGHT_Y 就是它；改了小面上这个数就得同步改 Java）
  - 骨骼名 root/move/body/barrel/sights/handguard/dust_cover/bolt/magazine/trigger/
    grip/stock/selector/camera/left_hand 不能改（动画 JSON 与 AkmGeoModel 都按名字取）
  - left_hand（左手手套）的父骨骼是 move：举枪偏移/跑步摆动都作用在 move 上，
    手才能一直跟着枪；换弹与拉栓动作由 AkmGeoModel 按进度程序化推。

输出：build/akm_v3.geo.json + build/akm_v3.png
"""
import json
import math
import os

from PIL import Image, ImageDraw

SIZE = 512
BORE = 1.75          # 枪管轴线高度
SIGHT_Y = 3.44       # 瞄准线高度（照门顶 = 准星顶）
S = 13.0             # 每模型单位分配的贴图像素数（贴图密度）

# ------------------------------------------------------------------ 调色板（照照片）
STEEL_RCV = (48, 47, 48)     # 机匣（黑磷化）
STEEL_DC = (58, 57, 58)      # 机匣盖（略亮）
STEEL_BAR = (38, 38, 40)     # 枪管 / 准星座 / 导气箍
STEEL_GAS = (46, 45, 46)     # 导气管 / 通条
MZ = (30, 30, 32)            # 枪口制退器（发蓝）
BOLT = (122, 124, 128)       # 枪机 / 拉机柄（精加工钢）
MAG = (60, 57, 54)           # 弹匣（冲压钢）
WOOD_HG = (168, 92, 48)      # 护木（红棕清漆木）
WOOD_STK = (150, 78, 40)     # 枪托（略深）
GRIP = (140, 74, 40)         # 握把（照片里也是木的）
RUBBER = (40, 38, 40)        # 托底板
SIGHT = (30, 30, 32)         # 照门 / 准星
SEL = (50, 50, 52)           # 保险机柄
RAIL = (66, 68, 72)          # 顶部配件导轨（齿）
RAIL_D = (46, 47, 51)        # 导轨座
OPTIC = (42, 43, 47)         # 瞄具壳体（红点/倍镜）
OPTIC_D = (30, 31, 34)       # 瞄具暗面
GLASS = (66, 138, 158)       # 镜片
DOT_RED = (255, 66, 48)      # 红点
BRASS = (168, 132, 62)       # 黄铜（弹匣内可见的弹头）
BRASS_HI = (214, 174, 84)    # 黄铜亮面（刚抛出来的弹壳）
BRASS_D = (108, 82, 38)      # 黄铜暗面（壳身底部/凹槽）
GLOVE = (46, 44, 48)         # 左手（战术手套：掌心/手指）
GLOVE_CUFF = (34, 33, 36)    # 手套袖口（深一档）

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
        # ★ 木纹不能用「等间距条纹」：木件是好几段方块拼的，条纹方向一旦跟 UV 轴对不上，
        #   侧视图里就会变成一层层木板/栅栏。改成**无方向性的细噪点 + 清漆光泽**，
        #   不管 UV 怎么摆都是均匀清漆木。
        for j in range(h):
            rowf = 1.0 + rn.r(-0.030, 0.030)
            for i in range(w):
                c = sh(base, rowf * rn.r(0.965, 1.035))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
        # 清漆高光
        for j in range(h):
            if rn.f() < 0.10:
                f = rn.r(1.05, 1.11)
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
        # 加强肋**沿弹匣长度方向**走（照片里是纵向肋，不是一圈圈横箍）
        for i in range(w):
            rib = (i % 4 == 0 or i % 4 == 1)
            f = 0.86 if rib else 1.05
            for j in range(h):
                c = sh(base, f * rn.r(0.95, 1.05))
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
        for j in range(h):
            px[x + w - 1, y + j] = sh(base, 0.70)
    elif mat in (BOLT,):
        for j in range(h):
            for i in range(w):
                f = 0.94 + 0.10 * math.sin(i * 0.8 + seed) + rn.r(-0.035, 0.035)
                c = sh(base, f)
                px[x + i, y + j] = (c[0], c[1], c[2], 255)
    elif mat in (GLOVE, GLOVE_CUFF):
        # 手套：细织纹噪点，不要金属拉丝/镜面高光
        for j in range(h):
            rowf = 1.0 + rn.r(-0.02, 0.02)
            for i in range(w):
                wv = 1.035 if (i + j) % 3 == 0 else 0.985
                c = sh(base, rowf * wv * rn.r(0.98, 1.02))
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
    elif tag == 'glove_side':
        d = ImageDraw.Draw(img)
        d.line([(x, y + 1), (x + w - 1, y + 1)], fill=sh(base, 1.24))       # 指节缝线
        d.line([(x, y + h - 2), (x + w - 1, y + h - 2)], fill=sh(base, 0.80))
    elif tag == 'rail_side':
        # 导轨道面：沿长边一条亮线（轨面磨亮）+ 齿根一道暗缝
        d = ImageDraw.Draw(img)
        d.line([(x, y + 1), (x + w - 1, y + 1)], fill=sh(base, 1.30))
        d.line([(x, y + h - 2), (x + w - 1, y + h - 2)], fill=sh(base, 0.72))

    # ---- 抛光层：竖向光泽渐变 + 倒角高光带 + 镜面高光斑（与 boxlib 的抛光一致）----
    for j in range(h):
        t = j / float(max(h - 1, 1))
        f = 1.0 + 0.085 * (1.0 - t) ** 1.6
        for i in range(w):
            c = px[x + i, y + j]
            px[x + i, y + j] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)

    # ---- 边缘 AO / 倒角：上沿给高光（磨亮的棱），下沿给反光暗带；左右仍轻微收暗 ----
    # ★ 弹匣是 9 段小方块拼出的弧：每段再描上下边就成了一截截“百叶/分叉”，这里只留左右收暗。
    b = 1 if min(w, h) <= 10 else 2
    if mat != MAG:
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
    # 左右边缘收暗：★ 木件**不做** —— 枪托/护木是好几段方块拼的，而 uv 的 u 轴正好是
    # 长度方向，逐段收暗就会在每条接缝上留下一条竖线，看起来像一层层木板。
    if mat not in (WOOD_HG, WOOD_STK):
        for j in range(h):
            for k in range(b):
                f = 1.0 - 0.15 * (1.0 - k / float(b))
                for xx in (x + k, x + w - 1 - k):
                    c = px[xx, y + j]
                    px[xx, y + j] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)
    # 高光斑：上半部几道短亮线（抛光金属的反光痕）
    if min(w, h) >= 6 and mat not in (WOOD_HG, WOOD_STK, GRIP, GLOVE, GLOVE_CUFF):
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
    # ★ 用户要求：**不要实体手方块** —— 左手换弹/拉栓靠枪自身的动作表现：
    #   空弹匣从弹匣井抽出来往下/向前飞出视野、满弹匣从下方升上来卡入、枪机后拉复进，
    #   再配 animation.json 里 move 的摆动（低头、侧倾、顿挫）就看得明白。
    # 两个瞄具骨骼（默认隐藏，由物品 NBT 决定显示哪个 —— AkmGeoModel.sightNbt）：
    #   红点参照 (0, 3.79, -5.50)；4 倍镜光轴 Y=4.00。两者都在 X=0。
    ('dot_sight', 'body', (0.0, 3.79, -5.50)),
    ('scope_4x', 'body', (0.0, 4.00, -5.60)),
    # ★ 抛壳动画（AkmGeoModel.driveCasings）：4 根弹壳骨骼轮流用，全自动时同时在空中的
    #   弹壳就像一串往外冒；pivot = 抛壳口 (0.95, 2.62, -2.30)，弹壳绕它打转往外飞。
    ('casing_0', 'body', (0.95, 2.62, -2.30)),
    ('casing_1', 'body', (0.95, 2.62, -2.30)),
    ('casing_2', 'body', (0.95, 2.62, -2.30)),
    ('casing_3', 'body', (0.95, 2.62, -2.30)),
]

CUBES = [
    # ---------------- 枪口 / 枪管 / 准星 / 导气箍（barrel）
    # 斜切枪口制退器（AKM 标志件）：下巴最长、往上逐级后退 → 斜口朝上前方
    C('barrel', 'muzzle_1', (-0.22, 0.22), (1.50, 1.66), (-11.60, -11.02), MZ, tag='barrel_side'),
    C('barrel', 'muzzle_2', (-0.22, 0.22), (1.66, 1.82), (-11.52, -11.02), MZ, tag='barrel_side'),
    C('barrel', 'muzzle_3', (-0.22, 0.22), (1.82, 1.98), (-11.44, -11.02), MZ, tag='barrel_side'),
    C('barrel', 'muzzle_ring', (-0.26, 0.26), (1.46, 2.02), (-11.12, -11.02), MZ),
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
    # 照门叶片：顶沿精确落在瞄准线 SIGHT_Y = 3.44（与准星柱顶齐平），中间留出 U 形缺口
    C('sights', 'rear_sight_leaf', (-0.26, 0.26), (3.26, 3.40), (-5.06, -4.42), SIGHT),
    C('sights', 'rs_notch_l', (-0.26, -0.06), (3.40, SIGHT_Y), (-5.06, -4.42), SIGHT),
    C('sights', 'rs_notch_r', (0.06, 0.26), (3.40, SIGHT_Y), (-5.06, -4.42), SIGHT),
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
    # ★ 照 AKM 实枪加长：原来只有 ~0.9 单位（≈50mm），太短了；AK 的握把从机匣下沿
    #   再往下 ~1.5 单位（≈80mm），而且是**向后斜**的 → 三块统一绕握把顶端后倾 14°
    C('grip', 'grip_upper', (-0.35, 0.35), (0.80, 1.60), (-0.70, 0.28), GRIP,
      rot=(-14, 0, 0), piv=(0, 1.46, -0.20), tag='grip_side'),
    C('grip', 'grip_lower', (-0.42, 0.42), (-0.62, 0.86), (-0.58, 0.40), GRIP,
      rot=(-14, 0, 0), piv=(0, 1.46, -0.20), tag='grip_side'),
    C('grip', 'grip_cap', (-0.42, 0.42), (-0.76, -0.58), (-0.60, 0.42), STEEL_RCV,
      rot=(-14, 0, 0), piv=(0, 1.46, -0.20)),
    # ---------------- 枪托（stock）
    # （枪托不要用 handguard_side 标签：那是护木的三道指槽，打到枪托上会变成“拼板竖缝”）
    C('stock', 'stock_wrist', (-0.40, 0.40), (1.62, 2.72), (0.22, 1.10), WOOD_STK),
    C('stock', 'stock_1', (-0.50, 0.50), (1.50, 2.78), (1.10, 2.30), WOOD_STK),
    C('stock', 'stock_2', (-0.54, 0.54), (1.26, 2.85), (2.30, 3.50), WOOD_STK),
    C('stock', 'stock_3', (-0.56, 0.56), (0.94, 2.89), (3.50, 4.58), WOOD_STK),
    C('stock', 'stock_band', (-0.58, 0.58), (0.88, 2.93), (4.46, 4.60), STEEL_RCV),
    C('stock', 'butt_plate', (-0.58, 0.58), (0.84, 2.94), (4.60, 4.84), RUBBER),
    C('stock', 'sling_swivel', (-0.10, 0.10), (0.62, 0.92), (3.86, 4.08), BOLT),
    C('stock', 'stock_bolt', (-0.38, 0.38), (2.40, 2.80), (1.04, 1.16), BOLT),
    # ---------------- 保险机柄（selector）
    C('selector', 'sel_body', (0.48, 0.60), (2.10, 3.06), (-4.52, -2.16), SEL),
    C('selector', 'sel_flag', (0.48, 0.60), (2.84, 3.12), (-4.52, -4.08), SEL),
    C('selector', 'sel_tab', (0.60, 0.80), (2.28, 2.58), (-3.10, -2.78), SEL),

    # ---------------- 细节件（照照片补：卡笋 / 铆钉 / 通条头 / 导气箍调节钮 / 卡箍）
    C('body', 'mag_release', (-0.16, 0.16), (0.94, 1.18), (-3.14, -2.88), BOLT),
    C('body', 'rcv_rivet_a', (-0.60, -0.53), (2.60, 2.72), (-4.12, -3.98), BOLT),
    C('body', 'rcv_rivet_b', (-0.60, -0.53), (2.60, 2.72), (-2.24, -2.10), BOLT),
    C('body', 'rcv_rivet_c', (0.53, 0.60), (2.60, 2.72), (-4.12, -3.98), BOLT),
    C('body', 'rcv_rivet_d', (0.53, 0.60), (2.60, 2.72), (-2.24, -2.10), BOLT),
    C('dust_cover', 'dc_latch', (-0.28, 0.28), (2.88, 3.18), (0.16, 0.46), BOLT),
    C('dust_cover', 'dc_rib_0', (-0.36, 0.36), (3.28, 3.34), (-1.34, -1.14), STEEL_DC),
    C('dust_cover', 'dc_rib_1', (-0.36, 0.36), (3.28, 3.34), (-0.74, -0.54), STEEL_DC),
    C('barrel', 'rod_tip', (-0.09, 0.09), (1.36, 1.56), (-11.06, -10.86), BOLT),
    C('barrel', 'barrel_ring3', (-0.22, 0.22), (1.53, 1.97), (-8.64, -8.56), STEEL_GAS),
    C('barrel', 'gas_reg', (0.24, 0.36), (1.84, 2.08), (-9.22, -8.84), BOLT),
    C('sights', 'gas_tube_ret', (-0.25, 0.25), (2.00, 2.56), (-5.46, -5.24), STEEL_GAS),
    C('magazine', 'mag_lug', (-0.22, 0.22), (1.24, 1.48), (-4.56, -4.30), MAG),
    C('trigger', 'tg_tab', (-0.16, 0.16), (0.72, 0.98), (0.24, 0.44), STEEL_RCV),
    C('grip', 'grip_ferrule', (-0.40, 0.40), (0.92, 1.06), (-0.62, 0.32), BOLT,
      rot=(-14, 0, 0), piv=(0, 1.46, -0.20)),
]

MAG_SEGS = 9
MAG_STEP = 0.42
MAG_ANG = 6.0


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
                     (-w, w), (min(y0, y1) - 0.05, max(y0, y1) + 0.05),
                     (z0 - d / 2, z0 + d / 2),
                     MAG, rot=(rot, 0, 0) if rot is not None else None,
                     piv=(0, y0, z0), tag='mag_side'))
        y0, z0 = y1, z1
        ang += MAG_ANG
    a = math.radians(ang - MAG_ANG)
    out.append(C('magazine', 'mag_floor', (-0.55, 0.55), (y0 - 0.16, y0 + 0.02),
                 (z0 - 0.36, z0 + 0.36), STEEL_RCV, rot=(ang - MAG_ANG, 0, 0), piv=(0, y0, z0)))
    return out


CUBES += build_magazine()


# ------------------------------------------------------------------ 左手
# 持握手护木的左手（拳）：掌心贴在护木左侧、四指从上方包过去、拇指压在护木下侧，
# 后面接一段袖口。尺寸按模型比例来：护木剖面 1.14×1.62，手包住它就好。
HAND_PIVOT = (0.0, 2.15, -6.60)


def build_hand():
    """（已弃用）用户要求不要实体手方块 —— 保留空函数避免旧引用报错。"""
    return []


CUBES += build_hand()


# ------------------------------------------------------------------ 顶部配件导轨
# 用户要求「延申方便装配件」：把导轨从照门前方一路往前铺到护木前端（z −4.58 → −7.24），
# 轨面 Y=2.96（= 护木顶面）、齿顶 3.16；照门顶/准星顶在 Y=3.44 ⇒ 导轨不会挡住铁瞄。
def build_rail():
    out = [C('handguard', 'rail_base', (-0.30, 0.30), (2.96, 3.06), (-7.24, -4.58), RAIL_D,
             tag='rail_side')]
    z = -7.24
    i = 0
    while z + 0.20 <= -4.58 + 0.001:
        out.append(C('handguard', 'rail_tooth_%d' % i, (-0.30, 0.30), (3.06, 3.16),
                     (z, z + 0.20), RAIL, tag='rail_side'))
        z += 0.36
        i += 1
    return out


CUBES += build_rail()


# ------------------------------------------------------------------ 瞄具（挂在导轨上，默认隐藏）
# ★ 坐标硬约束（Java 里的 ADS 参照点必须与这里一致）：
#   - 红点圆心 = 模型 (0, 3.79, -5.50)   → WeaponMount.AKM_DOT_Y = 3.79
#   - 4 倍镜光轴 = 模型 Y 4.00           → WeaponMount.AKM_SCOPE_Y = 4.00
#   - 两者都压在 X=0（与枪管轴线同面）⇒ ADS 时它们才会落在屏幕正中
RAIL_TOP = 3.16              # 导轨齿顶（build_rail 的轨面高度）
# 4 倍镜整体后移量（模型像素）。枪口在 -Z，所以 +Z = 往射手/枪托方向后移。
# 0.5（第一次「稍微后移」）+ 0.8（按用户箭头再平移）= 1.3
SC_BACK = 1.3


def build_dot_sight():
    """小红点：底座 + 立柱 + 开口护罩 + 镜片 + 中心一颗红点。"""
    cy, cz = 3.79, -5.50
    return [
        C('dot_sight', 'dot_mount', (-0.42, 0.42), (RAIL_TOP, 3.26), (-6.20, -4.80), RAIL_D,
          tag='rail_side'),
        C('dot_sight', 'dot_riser', (-0.26, 0.26), (3.26, 3.58), (-5.80, -5.20), OPTIC),
        # 护罩：左右壁 + 顶桥（中间是通的，才能“看到枪的本体”）
        C('dot_sight', 'dot_hood_l', (-0.34, -0.22), (3.58, 3.98), (-5.92, -5.08), OPTIC),
        C('dot_sight', 'dot_hood_r', (0.22, 0.34), (3.58, 3.98), (-5.92, -5.08), OPTIC),
        C('dot_sight', 'dot_hood_top', (-0.34, 0.34), (3.90, 3.98), (-5.92, -5.08), OPTIC_D),
        # 镜片（倾斜一点，看起来是玻琅）
        C('dot_sight', 'dot_lens', (-0.21, 0.21), (3.62, 3.96), (-5.46, -5.40), GLASS),
        # 红点本体（圆心 = ADS 参照点）
        C('dot_sight', 'dot_core', (-0.06, 0.06), (cy - 0.06, cy + 0.06), (-5.42, -5.36),
          DOT_RED, tag='dot_core'),
    ]


def build_scope_4x():
    """4 倍镜：镜环座 + 镜筒（八棱截面）+ 前后镜环 + 物镜镜片。

    ★ 整镜沿 Z 后移 SC_BACK（枪口在 -Z，所以 +Z = 往射手方向后移，镜筒离眼睛更近）：
      镜筒 / 镜环 / 镜片 / 镜座全部一起平移（纯平移，不改变相对位置）。
    ★ 镜座收窄到 ±0.40：后移后镜座后半段会落进机匣盖里
      （dc_top: x ±0.42、Y 3.14..3.28、Z -4.50..0.22），宽度相同就会两侧共面，
      渲染时 z-fighting 闪烁，所以比机匣盖窄 0.02。
    """
    cy = 4.00
    b = SC_BACK
    out = [
        C('scope_4x', 'sc_mount', (-0.40, 0.40), (RAIL_TOP, 3.26), (-6.60 + b, -4.60 + b),
          RAIL_D, tag='rail_side'),
        C('scope_4x', 'sc_ring_f', (-0.40, 0.40), (cy - 0.38, cy + 0.38),
          (-4.98 + b, -4.80 + b), OPTIC),
        C('scope_4x', 'sc_ring_r', (-0.40, 0.40), (cy - 0.38, cy + 0.38),
          (-6.46 + b, -6.28 + b), OPTIC),
        C('scope_4x', 'sc_lens', (-0.30, 0.30), (cy - 0.30, cy + 0.30),
          (-6.30 + b, -6.24 + b), GLASS),
    ]
    for i, (z0, z1) in enumerate(((-4.80, -5.70), (-5.74, -6.28))):
        out.append(C('scope_4x', 'sc_tube_%d' % i, (-0.30, 0.30),
                     (cy - 0.40, cy + 0.40), (z0 + b, z1 + b), OPTIC))
    return out


CUBES += build_dot_sight()
CUBES += build_scope_4x()


# ------------------------------------------------------------------ 空弹壳（抛壳动画用）
# ★ 每个弹壳骨骼 = 一枚 7.62×39 空壳，静止时就摆在抛壳口 (0.95, 2.62, -2.30) 上，
#   由 Java（AkmGeoModel.driveCasings）按「开火后过了几 tick」让它往外飞 + 打转，
#   飞完就 setHidden(true)。真实弹壳只有 0.6px，太小看不见，这里放大到 ~2.4px。
CASE_PIVOT = (0.95, 2.62, -2.30)


def build_casings():
    out = []
    for i in range(4):
        bone = 'casing_%d' % i
        px, py, pz = CASE_PIVOT
        # 壳身（沿枪管方向躺着）+ 底部抽壳钩槽 + 颈部收口
        out.append(C(bone, 'case_%d_body' % i, (px - 0.35, px + 0.35), (py - 0.35, py + 0.35),
                     (pz - 1.20, pz + 0.95), BRASS_HI, tag='brass'))
        out.append(C(bone, 'case_%d_rim' % i, (px - 0.42, px + 0.42), (py - 0.42, py + 0.42),
                     (pz + 0.95, pz + 1.20), BRASS, tag='brass'))
        out.append(C(bone, 'case_%d_groove' % i, (px - 0.36, px + 0.36), (py - 0.36, py + 0.36),
                     (pz + 0.55, pz + 0.72), BRASS_D, tag='brass'))
        out.append(C(bone, 'case_%d_neck' % i, (px - 0.20, px + 0.20), (py - 0.20, py + 0.20),
                     (pz - 1.45, pz - 1.20), BRASS_HI, tag='brass'))
    return out


CUBES += build_casings()


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

    # 先把每个面登记下来，**按面高度从大到小**再装箱：货架式装箱对高度接近的块利用率最高，
    # 不排序的话后面塞进来的小块（手套的手指）会把行高撑大，整个图集就得多降一档密度。
    jobs = []
    for n, cube in enumerate(CUBES, start=1):
        x0, x1 = cube['x']
        y0, y1 = cube['y']
        z0, z1 = cube['z']
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        cube_def = {
            'origin': [round(x0, 4), round(y0, 4), round(z0, 4)],
            'size': [round(sx, 4), round(sy, 4), round(sz, 4)],
            'uv': {},
        }
        if cube['rot']:
            cube_def['rotation'] = [float(v) for v in cube['rot']]
            cube_def['pivot'] = [float(v) for v in (cube['piv'] or (0, 0, 0))]
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
            seed = n * 977 + FACE_SEED[face]
            if cube['mat'] in (WOOD_HG, WOOD_STK):
                # 木纹只跟面朝向挂钩 → 同面所有木件花纹一致，拼缝消失
                seed = FACE_SEED[face] * 3 + 11
            jobs.append({
                'def': cube_def, 'mat': cube['mat'], 'face': face, 'tag': tag_f, 'seed': seed,
                'key': '%s/%s/%s' % (cube['bone'], cube['name'], face),
                'w': max(2, fw * S), 'h': max(2, fh * S),
            })
        geo_bones[cube['bone']]['cubes'].append(cube_def)

    jobs.sort(key=lambda j: (-j['h'], -j['w'], j['key']))
    for job in jobs:
        x, y, w, h = pack.alloc(job['key'], job['w'], job['h'])
        paint(img, (x, y, w, h), job['mat'], job['face'], job['tag'], job['seed'])
        job['def']['uv'][job['face']] = {'uv': [float(x), float(y)], 'uv_size': [float(w), float(h)]}

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
    global S
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    geo = img = None
    for dens in (13.0, 12.0, 11.0, 10.0):
        S = dens
        try:
            geo, img = build()
            break
        except RuntimeError as e:
            print('density %.0f 图集放不下（%s），降一档重试' % (dens, e))
    if geo is None:
        raise SystemExit('图集怎么都放不下')
    p1 = os.path.join(root, 'build', 'akm_v3.geo.json')
    p2 = os.path.join(root, 'build', 'akm_v3.png')
    with open(p1, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, separators=(',', ':'))
    img.save(p2)
    nb = sum(len(b.get('cubes', [])) for b in geo['minecraft:geometry'][0]['bones'])
    print('bones %d  cubes %d  density %.0f' % (
        len(geo['minecraft:geometry'][0]['bones']), nb, S))
    print('wrote', p1)
    print('wrote', p2)

    # ---------------- 自检：瞄准线必须水平且居中（WeaponPose 的 ADS 数学靠这个）
    need = {'root', 'move', 'body', 'barrel', 'sights', 'handguard', 'dust_cover',
            'bolt', 'magazine', 'trigger', 'grip', 'stock', 'selector', 'camera',
            'dot_sight', 'scope_4x'}
    have = set(b[0] for b in BONES)
    print('骨骼名检查: %s' % ('OK' if need <= have else '缺 %s' % (need - have)))
    for cb in CUBES:
        if cb['name'] in ('rs_notch_l', 'fs_post', 'fs_ear_l', 'fs_ear_r'):
            print('  %-16s X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
                  % (cb['name'], cb['x'][0], cb['x'][1], cb['y'][0], cb['y'][1],
                     cb['z'][0], cb['z'][1]))
    hand = [c for c in CUBES if c['bone'] == 'left_hand']
    if hand:
        hy = max(c['y'][1] for c in hand)
        hx0 = min(c['x'][0] for c in hand)
        print('左手：%d 方块  X %.2f..%.2f  最高 Y=%.2f（瞄准线 %.2f，余量 %.2f）'
              % (len(hand), hx0, max(c['x'][1] for c in hand), hy, SIGHT_Y, SIGHT_Y - hy))
    for bone, tag, ref in (('dot_sight', '红点  ', 3.79), ('scope_4x', '4倍镜', 4.00)):
        cs = [c for c in CUBES if c['bone'] == bone]
        if not cs:
            continue
        print('%s：%d 方块  X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f  参照点 Y=%.2f'
              % (tag, len(cs), min(c['x'][0] for c in cs), max(c['x'][1] for c in cs),
                 min(c['y'][0] for c in cs), max(c['y'][1] for c in cs),
                 min(c['z'][0] for c in cs), max(c['z'][1] for c in cs), ref))
    rail = [c for c in CUBES if c['name'].startswith('rail_')]
    if rail:
        rz = (min(c['z'][0] for c in rail), max(c['z'][1] for c in rail))
        ry = max(c['y'][1] for c in rail)
        print('顶部导轨：%d 方块  Z %.2f..%.2f  齿顶 Y=%.2f（瞄准线 %.2f，余量 %.2f）%s'
              % (len(rail), rz[0], rz[1], ry, SIGHT_Y, SIGHT_Y - ry,
                 'OK' if ry < SIGHT_Y - 0.2 else '!! 太高会挡铁瞄'))
    tabs = {c['name']: c for c in CUBES}
    nl, nr, post = tabs.get('rs_notch_l'), tabs.get('rs_notch_r'), tabs.get('fs_post')
    if nl and nr and post:
        top = min(nl['y'][1], nr['y'][1])
        dy = abs(top - post['y'][1])
        gap_c = (nl['x'][1] + nr['x'][0]) / 2.0        # 照门缺口中心
        post_c = (post['x'][0] + post['x'][1]) / 2.0   # 准星柱中心
        off = abs(gap_c - post_c)
        print('瞄准线：缺口顶 Y=%.2f 准星顶 Y=%.2f 高差 %.3f（要 0）；缺口/准星偏心 %.3f（要 0）%s'
              % (top, post['y'][1], dy, off,
                 'OK' if dy < 0.01 and off < 0.01 else '!! 瞄准线不水平/不居中'))


if __name__ == '__main__':
    main()
