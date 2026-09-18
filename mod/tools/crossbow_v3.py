#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""十字弩 v3：按参考照片（现代复合十字弩）重建 GeckoLib 真骨骼模型。

参考图特征（逐项对应）：
  - 弓片：两片黑色弓片从弓片座向外伸，略带弧度；**梢部各一个凸轮盘**（图左下能看到银色轮）
  - 复合缆绳：从两个凸轮沿导轨向后拉到托前的锚点，左右各两根
  - 导轨：长条形，顶部有箭槽（两壁 + 槽底）
  - 瞄准镜：长镜筒 + 前物镜环 + 后目镜环 + 两个镜环座 + 顶部/侧面调节钮
  - 手枪握把：在导轨中段下方，带扳机与扳机护圈
  - 肩托：后方实心托 + 托底板 + 背带环

★ 硬约束（CrossbowGeoModel 的拉弦数学依赖，绝不能动）：
  - 弦两段枢轴 = 弓片梢 = **精确 (±6.0, 0.0, -5.8)**；弦长 = hypot(6.0, DRAW_DZ)；
    拉满绕 Y 转 ∓atan2(3.40, 6.0)=∓29.54° 后两段内端落在 (0, -2.40)（= nock 后退 3.40）
    （原来是 2.60 / 23.43° / (0,-3.20)；用户要求白弦再往玩家方向拉）
  - 所以凸轮盘也以 (±6, 0, -5.8) 为圆心（弦绕凸轮走）
  - 骨骼名 string_left / string_right / nock / bolt 必须保留（Java 按名字取）
新增骨骼：cam_left / cam_right（凸轮盘，跟着弓片；Java 里随拉弦转动）
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxlib as B  # noqa: E402

C = B.cube

# ---------------------------------------------------------------- 材质配色（整体黑）
RAIL = (58, 60, 64)           # 导轨铝合金
RAIL_D = (42, 43, 47)
BODY = (50, 51, 55)           # 机身/机匣
BLACK = (34, 35, 38)          # 弓片/握把/托（哑黑）
CARBON = (44, 45, 48)
GLASS = (62, 132, 156)        # 镜片
STEEL = (142, 144, 148)       # 螺栓/凸轮毂
CAM = (92, 94, 98)            # 凸轮盘（图里偏银灰）
STRING = (206, 200, 182)
RUBBER = (32, 32, 34)
BOLT_SH = (120, 122, 126)
BOLT_HL = (176, 180, 186)
VANE = (214, 90, 44)
GLOVE = (46, 44, 48)          # 左手（战术手套：手背/手指）
GLOVE_CUFF = (34, 33, 36)     # 手套袖口（深一档）

BONES = [
    ('root', None, (0.0, -1.60, -1.00)),
    ('move', 'root', (0.0, 0.0, 0.0)),
    ('body', 'move', (0.0, 0.0, 0.0)),
    ('stock', 'body', (0.0, -0.20, 1.20)),
    ('grip', 'body', (0.0, -0.50, 0.60)),
    ('scope', 'body', (0.0, 1.44, -1.60)),
    ('prod_left', 'body', (-1.10, 0.0, -6.20)),
    ('prod_right', 'body', (1.10, 0.0, -6.20)),
    ('cam_left', 'prod_left', (-6.0, 0.0, -5.8)),
    ('cam_right', 'prod_right', (6.0, 0.0, -5.8)),
    ('string_left', 'body', (-6.0, 0.0, -5.8)),
    ('string_right', 'body', (6.0, 0.0, -5.8)),
    ('nock', 'body', (0.0, 0.0, -5.8)),
    ('bolt', 'body', (0.0, 0.0, -5.8)),
]

CUBES = []

# ================================================================= 导轨 / 机身（body）
CUBES += [
    # 箭槽：槽底 + 两壁 + 两唇（弩箭与弦都在槽里走）
    C('body', 'rail_floor', (-0.34, 0.34), (-0.36, -0.16), (-6.60, 2.10), RAIL_D),
    C('body', 'rail_wall_l', (-0.34, -0.18), (-0.16, 0.26), (-6.60, 2.10), RAIL),
    C('body', 'rail_wall_r', (0.18, 0.34), (-0.16, 0.26), (-6.60, 2.10), RAIL),
    C('body', 'rail_lip_l', (-0.46, -0.32), (-0.10, 0.18), (-6.60, 2.10), RAIL_D),
    C('body', 'rail_lip_r', (0.32, 0.46), (-0.10, 0.18), (-6.60, 2.10), RAIL_D),
    # 机身下腹（握把/托都接在这上面）
    C('body', 'belly', (-0.50, 0.50), (-0.66, -0.30), (-6.00, 1.90), RAIL_D),
    # 弓片座（riser）：弓片插在这里；Z 必须完全落在弦面之前
    C('body', 'riser', (-1.10, 1.10), (-0.66, 0.48), (-7.10, -5.80), BODY),
    C('body', 'riser_face', (-1.10, 1.10), (-0.66, 0.48), (-7.24, -7.10), RAIL_D),
    C('body', 'riser_top', (-0.86, 0.86), (0.48, 0.62), (-7.04, -5.90), BODY),
    # 后端缆绳锚座（复合缆绳往后拉到这里）
    C('body', 'cable_anchor', (-0.62, 0.62), (0.10, 0.48), (0.36, 0.94), BODY),
    # 瞄准镜导轨（镜环座卡在这上面）
    C('body', 'scope_rail', (-0.30, 0.30), (0.50, 0.66), (-3.60, 0.40), RAIL),
    # 前脚踏环（U 形，参考图前端也有这一圈）
    C('body', 'stirrup_l', (-0.26, -0.14), (-0.86, 0.10), (-7.86, -7.20), STEEL),
    C('body', 'stirrup_r', (0.14, 0.26), (-0.86, 0.10), (-7.86, -7.20), STEEL),
    C('body', 'stirrup_b', (-0.26, 0.26), (-0.86, -0.74), (-7.86, -7.72), STEEL),
]
# 弓片座螺栓与散热片
for sx in (-1, 1):
    CUBES += B.bolt('body', 'riser_bolt_%d_a' % sx, sx * 1.10, 0.20, -6.40, 0.12, sx * 0.07,
                    STEEL, dark=RAIL_D)
    CUBES += B.bolt('body', 'riser_bolt_%d_b' % sx, sx * 1.10, -0.36, -6.86, 0.12, sx * 0.07,
                    STEEL, dark=RAIL_D)
CUBES += B.vents('body', 'riser_fin', (-0.54, 0.54, -0.46, 0.30, -7.16, -7.08), 3,
                 RAIL_D, along='x')

# ================================================================= 弓片（prod，复合弓片）
# 从弓片座 (|X|=1.10) 向外伸到梢部 (|X|=6.00)，梢端 Z 收回到 -5.80（凸轮圆心）
LIMB_SEGS = [
    (1.10, 2.40, 0.20, -6.48, -6.06),
    (2.40, 3.80, 0.18, -6.62, -6.20),
    (3.80, 5.10, 0.15, -6.46, -6.04),
    (5.10, 5.92, 0.12, -6.12, -5.70),
]
for i, (xa, xb, hy, za, zb) in enumerate(LIMB_SEGS):
    CUBES.append(C('prod_left', 'limb_l_%d' % i, (-xb, -xa), (-hy, hy), (za, zb), BLACK,
                   tag='prod'))
    CUBES.append(C('prod_right', 'limb_r_%d' % i, (xa, xb), (-hy, hy), (za, zb), BLACK,
                   tag='prod'))

# ================================================================= 凸轮（cam，绕 Y 转的盘）
for side, cname in ((-1, 'cam_left'), (1, 'cam_right')):
    cx = side * 6.0
    # 盘本体：十字双盒（八边形）+ 一道 45° 斜条 → 看起来是圆盘
    CUBES += B.cross_boxes(cname, 'cam_disc', -0.17, 0.17, 0.86, cx, -5.80, CAM, 'metal',
                           curv=('cyl', 'y', (cx, -5.80)))
    CUBES.append(B.cube(cname, 'cam_diag', (cx - 0.72, cx + 0.72), (-0.16, 0.16),
                        (-6.52, -5.08), CAM, rot=(0, 45, 0), piv=(cx, 0.0, -5.80),
                        kind='metal', curv=('cyl', 'y', (cx, -5.80))))
    # 轮毂螺栓
    CUBES.append(C(cname, 'cam_hub', (cx - 0.11, cx + 0.11), (-0.26, 0.26),
                   (-5.91, -5.69), STEEL))
    # 弦槽挡边
    CUBES.append(C(cname, 'cam_flange', (cx - 0.20, cx + 0.20), (-0.22, 0.22),
                   (-6.06, -5.94), RAIL_D))
    CUBES.append(C(cname, 'cam_flange2', (cx - 0.20, cx + 0.20), (-0.22, 0.22),
                   (-5.66, -5.54), RAIL_D))

# ================================================================= 复合缆绳（左右各两根）
# 从凸轮后缘拉到后端锚座：一根按 X 方向的长条绕 Y 旋转对准（θ = atan2(-Δz, Δx)）
for side in (-1, 1):
    for k, (cy, cz) in enumerate(((0.24, -5.62), (0.34, -5.72))):
        x0 = side * 5.70
        x1 = side * 0.46
        z1 = cz + 6.30
        dx, dz = x1 - x0, z1 - cz
        ln = math.hypot(dx, dz)
        theta = math.degrees(math.atan2(-dz, dx))
        CUBES.append(C('body', 'cable_%d_%d' % (side, k), (min(x0, x0 + ln), max(x0, x0 + ln)),
                       (cy - 0.05, cy + 0.05), (cz - 0.06, cz + 0.06), CARBON,
                       rot=(0.0, theta, 0.0), piv=(x0, cy, cz), tag='cable'))

# ================================================================= 瞄准镜（scope）
CUBES += [
    C('scope', 'tube', (-0.34, 0.34), (1.10, 1.78), (-3.90, 0.20), BODY,
      curv=('cyl', 'z', (0.0, 1.44))),
    C('scope', 'bell', (-0.44, 0.44), (1.00, 1.88), (-4.28, -3.86), BODY,
      curv=('cyl', 'z', (0.0, 1.44))),
    C('scope', 'bell_rim', (-0.50, 0.50), (0.94, 1.94), (-4.40, -4.28), RAIL_D),
    C('scope', 'lens', (-0.40, 0.40), (1.04, 1.84), (-4.30, -4.26), GLASS, tag='lens',
      kind='flat'),
    C('scope', 'eyepiece', (-0.42, 0.42), (1.02, 1.86), (0.18, 0.54), BODY,
      curv=('cyl', 'z', (0.0, 1.44))),
    C('scope', 'eye_rim', (-0.48, 0.48), (0.96, 1.92), (0.52, 0.64), RAIL_D),
    # 两个镜环座（卡在镜导轨上）
    C('scope', 'ring_a', (-0.42, 0.42), (0.60, 1.16), (-3.08, -2.60), RAIL),
    C('scope', 'ring_b', (-0.42, 0.42), (0.60, 1.16), (-0.62, -0.14), RAIL),
    # 调节钮：顶上一个、侧面一个
    C('scope', 'turret_top', (-0.21, 0.21), (1.78, 2.06), (-2.62, -2.06), BODY,
      curv=('cyl', 'y', (0.0, -2.34))),
    C('scope', 'turret_top_kn', (-0.25, 0.25), (2.04, 2.14), (-2.66, -2.02), RAIL_D),
    C('scope', 'turret_side', (0.34, 0.64), (1.24, 1.64), (-2.62, -2.06), BODY,
      curv=('cyl', 'x', (1.44, -2.34))),
    C('scope', 'turret_side_kn', (0.62, 0.72), (1.20, 1.68), (-2.66, -2.02), RAIL_D),
]

# ================================================================= 肩托（stock）
CUBES += [
    C('stock', 'stock_main', (-0.58, 0.58), (-0.56, 0.36), (0.60, 3.30), BLACK),
    C('stock', 'stock_top', (-0.50, 0.50), (0.36, 0.58), (0.66, 2.72), BODY),
    C('stock', 'stock_belly', (-0.48, 0.48), (-0.86, -0.52), (0.80, 2.90), BLACK),
    C('stock', 'butt', (-0.62, 0.62), (-0.78, 0.46), (3.30, 3.50), RUBBER),
    C('stock', 'butt_plate', (-0.66, 0.66), (-0.84, 0.50), (3.48, 3.60), BLACK),
    C('stock', 'cheek', (-0.44, 0.44), (0.58, 0.76), (1.00, 2.60), BODY),
]
for sx in (-1, 1):
    CUBES += B.bolt('stock', 'butt_scr_%d' % sx, sx * 0.40, 0.20, 3.60, 0.12, 0.05,
                    STEEL, axis='z', dark=BLACK)
CUBES += B.ring('stock', 'sling', -0.62, -0.72, 2.30, 0.20, 0.075, STEEL, 'metal',
                axis='x', seg=6)

# ================================================================= 手枪握把（grip）
CUBES += [
    C('grip', 'grip_main', (-0.44, 0.44), (-1.66, -0.24), (0.26, 0.94), BLACK),
    C('grip', 'grip_back', (-0.38, 0.38), (-1.58, -0.30), (0.88, 1.08), BLACK),
    C('grip', 'trigger', (-0.07, 0.07), (-0.66, -0.34), (0.92, 1.02), STEEL),
    # 扳机护圈（三段小盒拼的方环）
    C('grip', 'guard_f', (-0.08, 0.08), (-0.86, -0.62), (1.00, 1.08), BLACK),
    C('grip', 'guard_b', (-0.08, 0.08), (-1.06, -0.88), (0.42, 1.08), BLACK),
    C('grip', 'guard_r', (-0.08, 0.08), (-0.86, -0.54), (0.40, 0.50), BLACK),
]
CUBES += B.vents('grip', 'grip_rib', (-0.44, 0.44, -1.60, -0.30, 0.24, 0.92), 3,
                 RAIL_D, along='y', fill=0.30)

# ================================================================= 弦（长度必须 = sqrt(TIP_X²+DRAW_DZ²)）
# ★ 拉弦几何（CrossbowGeoModel 依赖）：弦两段枢轴 = 弓片梢 (±TIP_X, 0, NOCK_Z)，
#   拉满绕 Y 转 ∓atan2(DRAW_DZ, TIP_X)，**两段内端必须在 x=0 相遇** ——
#   所以弦长只能 = hypot(TIP_X, DRAW_DZ)，否则拉满时弦从中间断开。
#   用户要求「白弦再往玩家方向拉」：DRAW_DZ 2.60 → 3.40（弦心 z 从 -3.20 到 -2.40）
TIP_X = 6.0
DRAW_DZ = 3.40
NOCK_Z = -5.80
STR_HALF = math.hypot(TIP_X, DRAW_DZ)          # 6.896（原来是 6.54）

CUBES += [
    # 枢轴 (-6,0,-5.8) → 末端 (0.896,0,-5.8)：拉满后内端正好落在弦心
    C('string_left', 'string_l', (-TIP_X, -TIP_X + STR_HALF), (-0.045, 0.045),
      (NOCK_Z - 0.045, NOCK_Z + 0.045), STRING, kind='flat'),
    C('string_right', 'string_r', (TIP_X - STR_HALF, TIP_X), (-0.045, 0.045),
      (NOCK_Z - 0.045, NOCK_Z + 0.045), STRING, kind='flat'),
]
# ================================================================= 弦心（nock）
CUBES.append(C('nock', 'nock_serve', (-0.58, 0.58), (-0.26, 0.26),
               (NOCK_Z - 0.22, NOCK_Z + 0.22), RUBBER))

# ================================================================= 弩箭（bolt）
# ★ 箭尾总是坐在弦心上，所以拉弦行程加大后箭也跟着后移；这里把箭杆/箭头
#   前伸 0.8，让拉满时箭尖仍然露出弓片前方同样多（否则箭会被吞进弩身里）。
BOLT_EXT = DRAW_DZ - 2.60                       # 0.8
CUBES += [
    C('bolt', 'bolt_shaft', (-0.17, 0.17), (-0.06, 0.28), (-9.80 - BOLT_EXT, -5.52), BOLT_SH,
      kind='brushed'),
    C('bolt', 'bolt_ferrule', (-0.20, 0.20), (-0.09, 0.31), (-10.10 - BOLT_EXT, -9.80 - BOLT_EXT),
      STEEL),
    C('bolt', 'bolt_point', (-0.08, 0.08), (0.02, 0.20), (-10.56 - BOLT_EXT, -10.10 - BOLT_EXT),
      BOLT_HL),
    C('bolt', 'bolt_nock', (-0.12, 0.12), (-0.01, 0.23), (-5.52, -5.24), RUBBER),
    C('bolt', 'vane_up', (-0.04, 0.04), (0.26, 0.44), (-8.40 - BOLT_EXT * 0.5, -7.90 - BOLT_EXT * 0.5), VANE),
    C('bolt', 'vane_dl', (-0.24, -0.16), (0.02, 0.20), (-8.40 - BOLT_EXT * 0.5, -7.90 - BOLT_EXT * 0.5), VANE),
    C('bolt', 'vane_dr', (0.16, 0.24), (0.02, 0.20), (-8.40 - BOLT_EXT * 0.5, -7.90 - BOLT_EXT * 0.5), VANE),
]


# ================================================================= 左手（不做实体手方块）
# ★ 用户明确要求：十字弩/AKM 不需要实体手方块 —— 拉弦/装弹全部靠**弩自身的动作**表现：
#   弦两段绕弓臂梢转、弦心后退、弩箭滑上弦（CrossbowGeoModel 程序化推），
#   弩整体也跟着摆（animation.json 的 move）。


# ---------------------------------------------------------------- 逐面细节
def detail_glove(img, rect, face, seed):
    """手套指节/袖口：一条亮缝线 + 一条暗底缝"""
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    d.line([(x, y + 1), (x + w - 1, y + 1)], fill=B.sh(GLOVE, 1.24))
    d.line([(x, y + h - 2), (x + w - 1, y + h - 2)], fill=B.sh(GLOVE, 0.80))
def detail_lens(img, rect, face, seed):
    """镜片：中心亮、边缘暗（像玻璃反光）"""
    import math as _m
    x, y, w, h = rect
    px = img.load()
    cx, cy = x + w * 0.5, y + h * 0.5
    rr = max(1.0, min(w, h) * 0.5)
    for j in range(h):
        for i in range(w):
            d = _m.hypot(i - w * 0.5, j - h * 0.5) / rr
            f = 0.55 + 0.85 * max(0.0, 1.0 - d * d)
            c = px[x + i, y + j]
            px[x + i, y + j] = (B.cl(c[0] * f), B.cl(c[1] * f), B.cl(c[2] * f), 255)


DETAILS = {'lens': detail_lens, 'glove': detail_glove}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 镜筒是圆柱：按 'z' 轴圆柱烘连续明暗
    for c in CUBES:
        if c['bone'] == 'scope' and c['curv'] is None and c.get('kind') != 'flat':
            c['curv'] = ('cyl', 'z', (0.0, 1.44))
    geo, img = B.build(BONES, CUBES, 'geometry.crossbow_geo', details=DETAILS, density=13.0)
    B.write(geo, img, os.path.join(root, 'build', 'crossbow_v3.geo.json'),
            os.path.join(root, 'build', 'crossbow_v3.png'), quiet=True)
    print('bones %d  cubes %d' % (len(BONES), len(CUBES)))
    print('wrote build/crossbow_v3.geo.json / .png')
    # 自检：弦绕 Y 转 ∓atan2(DRAW_DZ,TIP_X) 后内端必须落在 (0, NOCK_Z+DRAW_DZ)
    phi = math.atan2(DRAW_DZ, TIP_X)
    for label, sign in (('string_left ', -1.0), ('string_right', 1.0)):
        dx = -sign * STR_HALF         # 立方体从枢轴朝内伸 STR_HALF
        th = sign * phi
        ex = sign * TIP_X + dx * math.cos(th)
        ez = NOCK_Z - dx * math.sin(th)
        print('%s  end -> X %+.3f  Z %+.3f   (目标 X 0.000  Z %+.3f)'
              % (label, ex, ez, NOCK_Z + DRAW_DZ))


if __name__ == '__main__':
    main()
