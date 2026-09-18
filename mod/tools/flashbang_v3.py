#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""震爆弹 v3：按参考照片重建（M84 型）—— 真骨骼 root/move/body/fuze/spoon/pin。

参考照片逐项对应：
  - 弹体：**八棱柱**（十字双盒拟八边形；curv 按 y 轴圆柱烘 8 个面各自的朝向明暗）
  - 泄气孔：**三排大圆孔**（色带上方 2 排、色带下方 1 排），每排 8 个（每个棱面一个）；
    画在贴图上 —— 孔口受光倒角 + 孔内上暗下亮（照片里孔底有反光弧）
  - 色带：弹体中段一圈**凸起的青蓝色带**（照片里最醒目的特征）
  - 底部：暗绿领圈，印 "USPAT 6,814,993.0"（两行 3x5 像素字，照照片的位置）
  - 肩部：印 "S-84"
  - 顶部：收窄的绿色引信块 + 钢垫圈 + 螺栓（顶面一字槽）
  - 侧面：钢**压把**（-X 侧自上而下贴体；Java 里绕 Z 弹开）
  - 拉环：**保险销沿 Z 穿过引信块**，-Z 端折下接一枚大号开口环（照片里挂在弹体一侧）
    —— Java 里整个 pin 骨骼沿 -Z 滑出 = 拔销

★ 坐标约定（同旧模型，display 全 identity）：
  原点 = 弹体中心，前向 -Z、上 +Y；骨骼名 root/move/body/fuze/spoon/pin **必须保留**
  （FlashbangGeoModel 按名字取 pin / spoon）。
"""
import math
import os
import sys

from PIL import ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxlib as B  # noqa: E402

C = B.cube

# ---------------------------------------------------------------- 配色（照照片取色）
BODY = (96, 102, 78)          # 军绿弹体
BODY_D = (76, 82, 62)         # 暗部 / 底部领圈
BAND = (96, 186, 200)         # 青蓝色带
BUZA = (86, 92, 70)           # 顶部引信块
STEEL = (146, 150, 154)       # 钢（垫圈 / 螺栓 / 销 / 拉环）
STEEL_D = (112, 116, 120)
SPOON = (122, 126, 130)       # 压把
INK = (200, 204, 194, 255)    # 印字

DENS = 13.0                   # 贴图密度（与 build(density=DENS) 一致，逐面细节要用）
R = 1.80                      # 弹体半径（八棱柱外接圆）
RING_R = 1.15                 # 大拉环半径
RING_Y, RING_Z = 1.15, -3.12  # 大拉环圆心（-Z 侧，挂在引信块的销上）
Y_PIN = 2.93                  # 保险销高度（穿过引信块）

# 纵向分段（原点 = 弹体中心）
Y_BOT = -3.80                 # 底面
Y_CAP = -3.70                 # 底裙下沿
Y_LIP = -3.40                 # 底裙上沿
Y_COL1 = -2.00                # 领圈上沿 = 弹体主段下沿
Y_BAND0, Y_BAND1 = -0.86, -0.14   # 色带
Y_BODY1 = 2.06                # 弹体主段上沿
Y_SHLD1 = 2.60                # 肩部上沿
Y_BUZA1 = 3.28                # 引信块上沿
Y_WASH1 = 3.44                # 垫圈上沿
Y_TOP = 3.80                  # 螺栓顶

HOLES_Y = (1.54, 0.40, -1.44)  # 三排孔中心（模型 y）：色带上方 2 排、下方 1 排
HOLE_R = 0.50                  # 孔径半径（模型单位）

BONES = [
    ('root', None, (0.0, -1.55, -0.50)),
    ('move', 'root', (0.0, 0.0, 0.0)),
    ('body', 'move', (0.0, 0.0, 0.0)),
    ('fuze', 'body', (0.0, Y_SHLD1, 0.0)),
    ('spoon', 'fuze', (0.0, 2.80, 0.0)),
    ('pin', 'fuze', (0.0, Y_PIN, 0.0)),
]

CUBES = []

# ================================================================ 弹体（body 骨骼）
CUBES += B.cross_boxes('body', 'cap', Y_BOT, Y_CAP, R - 0.08, 0.0, 0.0,
                       (54, 58, 46), 'metal', tag='metal')
CUBES += B.cross_boxes('body', 'lip', Y_CAP, Y_LIP, R + 0.08, 0.0, 0.0,
                       (68, 73, 55), 'metal', tag='metal')
CUBES += B.cross_boxes('body', 'collar', Y_LIP, Y_COL1, R, 0.0, 0.0,
                       BODY_D, 'metal', tag='mark')
CUBES += B.cross_boxes('body', 'main', Y_COL1, Y_BODY1, R, 0.0, 0.0,
                       BODY, 'metal', tag='holes')
CUBES += B.cross_boxes('body', 'band', Y_BAND0, Y_BAND1, R + 0.07, 0.0, 0.0,
                       BAND, 'metal', tag='band')
CUBES += B.cross_boxes('body', 'shoulder', Y_BODY1, Y_SHLD1, R + 0.05, 0.0, 0.0,
                       (88, 94, 72), 'metal', tag='mark2')

# 分段处的压铸分模线（细凸法兰片。★ 不能用 ring(seg=8) 拟圆环：段长超过内接弦长，
# 4 个角会戳出弹体轮廓，看起来像横刺）
CUBES += B.cross_boxes('body', 'mold_lo', Y_COL1 - 0.06, Y_COL1 + 0.06, R + 0.05,
                       0.0, 0.0, (70, 76, 58), 'metal', tag='metal')
CUBES += B.cross_boxes('body', 'mold_hi', Y_BODY1 - 0.06, Y_BODY1 + 0.06, R + 0.11,
                       0.0, 0.0, (72, 78, 60), 'metal', tag='metal')

# 底盖铆钉
for _i, (_rx, _rz) in enumerate(((0.92, 0.0), (-0.92, 0.0), (0.0, 0.92), (0.0, -0.92))):
    CUBES += B.bolt('body', 'base_scr%d' % _i, _rx, Y_BOT, _rz, 0.15, -0.08,
                    (132, 136, 140), axis='y', dark=(38, 38, 40))

# ================================================================ 顶部引信块（fuze 骨骼）
CUBES += B.cross_boxes('fuze', 'buza', Y_SHLD1, Y_BUZA1, 1.26, 0.0, 0.0,
                       BUZA, 'metal', tag='buza')
CUBES += B.cross_boxes('fuze', 'washer', Y_BUZA1, Y_WASH1, 0.88, 0.0, 0.0,
                       STEEL_D, 'brushed', tag='steel')
CUBES += B.cross_boxes('fuze', 'bolt', Y_WASH1, Y_TOP, 0.54, 0.0, 0.0,
                       STEEL, 'metal', tag='steel')
CUBES.append(C('fuze', 'bolt_slot', (-0.36, 0.36), (Y_TOP, Y_TOP + 0.05), (-0.07, 0.07),
               (44, 46, 48), kind='flat'))

for _i, _rx in enumerate((-0.45, 0.45)):   # 引信块正面两颗螺钉
    CUBES += B.bolt('fuze', 'buza_scr%d' % _i, _rx, 2.94, -1.22, 0.13, -0.10,
                    (134, 138, 142), axis='z', dark=(40, 40, 42))

# ================================================================ 压把（spoon 骨骼，-X 侧）
SPOON_PATH = [(-1.86, 2.58), (-1.94, 2.10), (-1.98, 1.30), (-2.00, 0.40),
              (-1.98, -0.50), (-1.94, -1.30), (-1.88, -1.86)]
CUBES += B.arc_boxes('spoon', 'spoon', SPOON_PATH, thick=0.17, half_w=0.30,
                     mat=SPOON, kind='metal', tag='spoon', plane='xy')
CUBES.append(C('spoon', 'spoon_hinge', (-2.34, -1.60), (2.34, 2.86), (-0.44, 0.44),
               SPOON, kind='metal', tag='spoon'))

# ================================================================ 保险销 + 大拉环（pin 骨骼）
CUBES.append(C('pin', 'pin_rod', (-0.10, 0.10), (Y_PIN - 0.11, Y_PIN + 0.11),
               (-2.96, 1.44), STEEL, kind='brushed', tag='steel'))
CUBES.append(C('pin', 'pin_bend', (-0.10, 0.10), (2.34, Y_PIN + 0.11), (-2.96, -2.76),
               STEEL, kind='brushed', tag='steel'))
CUBES += B.ring('pin', 'pin_eye', 0.0, 2.28, -2.86, 0.20, 0.13, STEEL, 'brushed',
                axis='z', seg=8)                       # 销尾小环
CUBES += B.ring('pin', 'pin_head', 0.0, Y_PIN, 1.36, 0.19, 0.13, STEEL, 'brushed',
                axis='x', seg=8)                       # 销头小环（+Z 端）
CUBES += B.ring('pin', 'pin_ring', 0.0, RING_Y, RING_Z, RING_R, 0.16, STEEL,
                'brushed', axis='x', seg=10)           # 大开口环


# ================================================================ 逐面细节
# 3x5 点阵字表与边缘光都在 boxlib 里（字表只维护一份，碎片手雷也用它印钢印字）
_edge = B.edge
_tw = B.text_w


def _text(d, x, y, s, color):
    B.text(d, x, y, s, color)


def detail_holes(img, rect, face, seed):
    """弹体主段：三排大泄气孔（孔口倒角 + 孔内上暗下亮）。

    小面（1.49 宽）整面可见 → 孔画在正中间；宽面中线被埋 → 画了也看不见（无害）。
    """""
    if face in ('up', 'down'):
        return
    x, y, w, h = rect
    px = img.load()
    _edge(img, rect, 1.10, 0.84)
    if w / DENS < 1.2:
        return
    rad = min(HOLE_R, (w / DENS) * 0.30) * DENS
    r_in = max(1.0, rad - 1.1)
    d = ImageDraw.Draw(img)
    cx = x + w * 0.5
    for my in HOLES_Y:
        cy = y + (Y_BODY1 - my) / (Y_BODY1 - Y_COL1) * h
        # 孔口外圈：受光倒角（下缘更亮，像倒角反光）
        for j in range(int(cy - rad - 2), int(cy + rad + 3)):
            for i in range(int(cx - rad - 2), int(cx + rad + 3)):
                if i < x or i >= x + w or j < y or j >= y + h:
                    continue
                if math.hypot(i - cx, j - cy) <= rad + 1.5:
                    c = px[i, j]
                    f = 1.32 if j > cy else 1.03
                    px[i, j] = (B.cl(c[0] * f), B.cl(c[1] * f), B.cl(c[2] * f), 255)
        d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(28, 30, 26, 255))
        d.arc([cx - r_in + 1, cy - r_in + 1, cx + r_in - 1, cy + r_in - 1],
              start=52, end=128, fill=(112, 118, 100, 255))
        d.arc([cx - r_in + 1, cy - r_in + 1, cx + r_in - 1, cy + r_in - 1],
              start=232, end=308, fill=(44, 46, 40, 255))


def detail_band(img, rect, face, seed):
    """青蓝色带：细竖棱 + 上下沿亮暗。"""
    if face in ('up', 'down'):
        return
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    for i in range(0, w, 2):
        d.line([(x + i, y + 1), (x + i, y + h - 2)], fill=B.sh(BAND, 0.93))
    d.line([(x, y), (x + w - 1, y)], fill=B.sh(BAND, 1.30))
    d.line([(x, y + h - 1), (x + w - 1, y + h - 1)], fill=B.sh(BAND, 0.70))


def detail_mark(img, rect, face, seed):
    """底部领圈：分模线 + 专利号印字。

    ★ 只能印在**小面**上：十字双盒八棱柱的宽面（3.6 宽）中线被另一根盒子埋住，
    宽面上印字只会从两侧倒角缝里漏出两片碎片（看起来像坏图）。
    小面 = 4 个轴向面（各 1.49 宽 ≈ 20px），正好放得下 3 行 3x5 短字。
    """
    if face in ('up', 'down'):
        return
    x, y, w, h = rect
    _edge(img, rect, 1.12, 0.82)
    if w / DENS > 2.4:
        return
    d = ImageDraw.Draw(img)
    for i, s in enumerate(('USPAT', '6814', '9930')):
        if _tw(s) > w:
            continue
        _text(d, x + (w - _tw(s)) / 2.0, y + 1 + i * 6, s, INK)


def detail_mark2(img, rect, face, seed):
    """肩部：分模线 + 型号 "S-84"（同样只印小面）。"""
    if face in ('up', 'down'):
        return
    x, y, w, h = rect
    _edge(img, rect, 1.14, 0.84)
    if w / DENS > 2.4 or h < 7:
        return
    d = ImageDraw.Draw(img)
    s = 'S-84'
    _text(d, x + (w - _tw(s)) / 2.0, y + 1, s, INK)


def detail_buza(img, rect, face, seed):
    """引信块：横向铸纹 + 上下沿。"""
    x, y, w, h = rect
    px = img.load()
    _edge(img, rect, 1.14, 0.84)
    for j in range(y + 2, y + h - 2):
        if (j - y) % 3 == 0:
            for i in range(x, x + w):
                c = px[i, j]
                px[i, j] = (B.cl(c[0] * 0.92), B.cl(c[1] * 0.92), B.cl(c[2] * 0.92), 255)


def detail_steel(img, rect, face, seed):
    """钢件：上沿亮、下沿暗（车削反光）。"""
    x, y, w, h = rect
    px = img.load()
    for i in range(w):
        for k, f in ((y, 1.22), (y + 1, 1.10), (y + h - 2, 0.86), (y + h - 1, 0.74)):
            if y <= k < y + h:
                c = px[x + i, k]
                px[x + i, k] = (B.cl(c[0] * f), B.cl(c[1] * f), B.cl(c[2] * f), 255)


def detail_spoon(img, rect, face, seed):
    x, y, w, h = rect
    _edge(img, rect, 1.20, 0.80)


def detail_metal(img, rect, face, seed):
    x, y, w, h = rect
    px = img.load()
    _edge(img, rect, 1.12, 0.86)
    if face in ('up', 'down'):
        return
    cx = x + w * 0.5
    for j in range(y + 1, y + h - 1):
        for i in range(x + 1, x + w - 1):
            if abs(i - cx) < 0.9:
                c = px[i, j]
                px[i, j] = (B.cl(c[0] * 1.06), B.cl(c[1] * 1.06), B.cl(c[2] * 1.06), 255)


DETAILS = {'holes': detail_holes, 'band': detail_band, 'mark': detail_mark,
           'mark2': detail_mark2, 'buza': detail_buza, 'steel': detail_steel,
           'spoon': detail_spoon, 'metal': detail_metal}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    need = {'root', 'move', 'body', 'fuze', 'spoon', 'pin'}
    have = set(b[0] for b in BONES)
    print('bones %d  cubes %d' % (len(BONES), len(CUBES)))
    print('骨骼名检查: %s' % ('OK' if need <= have else '缺 %s' % (need - have)))

    geo, img = B.build(BONES, CUBES, 'geometry.flashbang', details=DETAILS,
                       density=DENS)
    B.write(geo, img, os.path.join(root, 'build', 'flashbang_v3.geo.json'),
            os.path.join(root, 'build', 'flashbang_v3.png'), quiet=True)
    print('wrote build/flashbang_v3.geo.json / .png')

    # ---- 自检 1：大拉环最靠近弹体轴的那一点必须在弹体半径之外
    gap = abs(RING_Z) - RING_R - R
    print('拉环最近处 z=%.3f  弹体半径 %.2f  间隙 %.3f  %s'
          % (RING_Z + RING_R, R, gap, 'OK' if gap > 0.05 else '!! 会插进弹体'))
    # ---- 自检 2：三排孔必须落在弹体主段内、且避开色带
    for my in HOLES_Y:
        ok = (Y_COL1 + HOLE_R < my < Y_BODY1 - HOLE_R) and \
             (my < Y_BAND0 - HOLE_R or my > Y_BAND1 + HOLE_R)
        print('孔排 y=%+.2f  %s' % (my, 'OK' if ok else '!! 越界/压色带'))
    # ---- 自检 3：销往 -Z 拔出 1.15 后仍在拉环那一层，不会被弹体卡住
    print('销 z 范围 -2.96 .. 1.44（Java 拔销沿 -Z 平移 %.2f）' % 1.15)
    h = float(sum(c['y'][1] - c['y'][0] for c in CUBES) / max(1, len(CUBES)))
    print('总高 %.2f  直径 %.2f  平均件高 %.2f' % (Y_TOP + 0.05 - Y_BOT, 2 * R, h))


if __name__ == '__main__':
    main()
