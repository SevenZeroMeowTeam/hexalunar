#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""十字弩 v2：重建 crossbow_geo.geo.json（**实际被 CrossbowGeoModel 使用的那份**）。

★ 硬约束（CrossbowGeoModel 程序化拉弦数学依赖，不能改）：
  - 12 根骨骼的名字与 pivot 原样保留；
  - TIP_X = 6.0 / DRAW_DZ = 2.60 / NOCK_Z0 = -5.80
  - 弦两段必须是「从弓臂梢枢轴 (±6,0,-5.8) 指向弦心」的直杆，长度 6.54：
      string_left  立方体 X ∈ [-6.00, +0.54]
      string_right 立方体 X ∈ [-0.54, +6.00]
    这样绕 Y 转 ∓atan2(2.60, 6.0)=∓23.43° 后末端正好到 (X 0, Z -3.20)，
    即 nock 后退 DRAW_DZ 的位置。已数值验证。
新设计：导轨带「箭槽」（两壁+槽底），弩箭真正坐在槽里；弓臂改成扁平弓片；
瞄准镜做八边形镜筒 + 物镜/目镜环 + 调节钮；加扳机护圈与脚踏环。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxlib as B  # noqa: E402

RAIL = (74, 76, 80)           # 导轨铝合金
RAIL_D = (56, 58, 62)
STOCK = (40, 41, 43)          # 枪托聚合物
CARBON = (46, 47, 50)         # 弓片碳素
SCOPE_B = (50, 52, 55)        # 镜筒
GLASS = (54, 128, 154)        # 镜片
STEEL = (140, 142, 146)
STRING = (208, 200, 178)
RUBBER = (34, 34, 36)
BOLT_SH = (56, 58, 62)
BOLT_HL = (166, 170, 176)
VANE = (214, 90, 44)

BONES = [
    ('root', None, (0.0, -2.6, -3.6)),
    ('move', 'root', (0.0, 0.0, 0.0)),
    ('body', 'move', (0.0, 0.0, 0.0)),
    ('stock', 'body', (0.0, -1.0, 1.6)),
    ('grip', 'body', (0.0, -0.4, 0.4)),
    ('scope', 'body', (0.0, 1.8, -2.0)),
    ('prod_left', 'body', (-1.2, 0.0, -5.0)),
    ('prod_right', 'body', (1.2, 0.0, -5.0)),
    ('string_left', 'body', (-6.0, 0.0, -5.8)),
    ('string_right', 'body', (6.0, 0.0, -5.8)),
    ('nock', 'body', (0.0, 0.0, -5.8)),
    ('bolt', 'body', (0.0, 0.0, -5.8)),
]

C = B.cube
CUBES = []

# ================================================================= 导轨 / 机匣（body）
CUBES += [
    # 箭槽：槽底 + 两壁（弩箭/弦都在槽里跑）
    C('body', 'rail_floor', (-0.40, 0.40), (-0.32, -0.12), (-6.70, 1.92), RAIL_D),
    C('body', 'rail_wall_l', (-0.40, -0.22), (-0.12, 0.30), (-6.70, 1.92), RAIL),
    C('body', 'rail_wall_r', (0.22, 0.40), (-0.12, 0.30), (-6.70, 1.92), RAIL),
    C('body', 'rail_lip_l', (-0.54, -0.38), (-0.06, 0.22), (-6.70, 1.92), RAIL_D),
    C('body', 'rail_lip_r', (0.38, 0.54), (-0.06, 0.22), (-6.70, 1.92), RAIL_D),
    C('body', 'belly', (-0.58, 0.58), (-0.72, -0.28), (-6.20, 1.60), RAIL_D),
    # 弓片座（★ Z 必须收在弦面 -5.87..-5.73 之前，否则会把弦的中段埋掉，
    #   看起来像弦"从前面那块里长出来"，而不是压在玩家这一侧）
    C('body', 'riser', (-1.24, 1.24), (-0.58, 0.46), (-7.00, -6.00), RAIL),
    C('body', 'riser_face', (-1.24, 1.24), (-0.58, 0.46), (-7.12, -7.00), RAIL_D),
    C('body', 'riser_bolt_l', (-1.18, -0.66), (-0.30, 0.30), (-6.40, -6.02), STEEL),
    C('body', 'riser_bolt_r', (0.66, 1.18), (-0.30, 0.30), (-6.40, -6.02), STEEL),
    # 脚踏环（弩前端的 U 形环）
    C('body', 'stirrup_l', (-0.30, -0.18), (-0.78, 0.26), (-7.62, -6.92), STEEL),
    C('body', 'stirrup_r', (0.18, 0.30), (-0.78, 0.26), (-7.62, -6.92), STEEL),
    C('body', 'stirrup_front', (-0.30, 0.30), (-0.78, -0.60), (-7.62, -6.92), STEEL),
    # 扳机护圈 + 扳机
    C('body', 'guard_front', (-0.24, 0.24), (-1.08, -0.62), (-1.42, -1.18), STOCK),
    C('body', 'guard_bottom', (-0.24, 0.24), (-1.08, -0.88), (-1.42, 0.34), STOCK),
    C('body', 'guard_rear', (-0.24, 0.24), (-1.08, -0.58), (0.14, 0.38), STOCK),
    C('body', 'trigger', (-0.07, 0.07), (-1.02, -0.58), (-1.02, -0.86), STEEL),
]

# ================================================================= 枪托（stock）
CUBES += [
    C('stock', 'stock_neck', (-0.55, 0.55), (-0.78, 0.02), (0.30, 1.62), STOCK),
    C('stock', 'stock_body', (-0.72, 0.72), (-1.08, 0.14), (1.62, 3.12), STOCK),
    C('stock', 'stock_comb', (-0.56, 0.56), (0.14, 0.58), (1.10, 2.96), STOCK),
    C('stock', 'stock_butt', (-0.86, 0.86), (-1.56, 0.34), (3.12, 4.12), STOCK),
    C('stock', 'butt_pad', (-0.90, 0.90), (-1.62, 0.40), (4.12, 4.30), RUBBER),
    C('stock', 'stock_sling', (-0.30, 0.30), (-1.28, -1.02), (2.30, 2.86), STEEL),
]

# ================================================================= 握把（grip）
CUBES += [
    C('grip', 'grip_up', (-0.40, 0.40), (-0.86, -0.06), (0.06, 0.86), STOCK,
      kind='plastic', tag='grip'),
    C('grip', 'grip_dn', (-0.46, 0.46), (-1.52, -0.80), (0.16, 1.00), STOCK,
      kind='plastic', tag='grip'),
    C('grip', 'grip_plate_l', (-0.52, -0.42), (-1.40, -0.20), (0.16, 0.90), RUBBER),
    C('grip', 'grip_plate_r', (0.42, 0.52), (-1.40, -0.20), (0.16, 0.90), RUBBER),
]

# ================================================================= 瞄准镜（scope）
SCY = 1.40          # 镜筒轴线高度
CUBES += [
    # 八边形镜筒（十字双盒拟圆）
    C('scope', 'tube_a', (-0.46, 0.46), (SCY - 0.19, SCY + 0.19), (-3.55, -0.85), SCOPE_B),
    C('scope', 'tube_b', (-0.19, 0.19), (SCY - 0.46, SCY + 0.46), (-3.55, -0.85), SCOPE_B),
    # 物镜 / 目镜环
    C('scope', 'obj_a', (-0.60, 0.60), (SCY - 0.25, SCY + 0.25), (-3.78, -3.48), SCOPE_B),
    C('scope', 'obj_b', (-0.25, 0.25), (SCY - 0.60, SCY + 0.60), (-3.78, -3.48), SCOPE_B),
    C('scope', 'eye_a', (-0.54, 0.54), (SCY - 0.22, SCY + 0.22), (-1.10, -0.78), SCOPE_B),
    C('scope', 'eye_b', (-0.22, 0.22), (SCY - 0.54, SCY + 0.54), (-1.10, -0.78), SCOPE_B),
    # 镜片
    C('scope', 'lens_front', (-0.42, 0.42), (SCY - 0.42, SCY + 0.42), (-3.84, -3.76), GLASS,
      kind='plastic'),
    C('scope', 'lens_back', (-0.38, 0.38), (SCY - 0.38, SCY + 0.38), (-0.80, -0.74), GLASS,
      kind='plastic'),
    # 调节钮
    C('scope', 'turret_top', (-0.24, 0.24), (SCY + 0.46, SCY + 0.84), (-2.62, -2.18), SCOPE_B),
    C('scope', 'turret_side', (0.46, 0.86), (SCY - 0.20, SCY + 0.20), (-2.58, -2.14), SCOPE_B),
    # 镜座
    C('scope', 'mount_front', (-0.36, 0.36), (0.24, 0.98), (-3.06, -2.62), RAIL_D),
    C('scope', 'mount_rear', (-0.36, 0.36), (0.24, 0.98), (-1.58, -1.14), RAIL_D),
]

# ================================================================= 弓片（prod，反曲）
# ★「反曲」按用户要求的方向：弓片从弓片座向外伸出的同时**向内侧（朝玩家）弯曲** ——
#   即根部最靠前（-Z），越往外越往回收（+Z），梢端回到弦所在的平面，弦就压在
#   玩家这一侧（不要做成向前鼓出的形状，那是「往外弯」，用户明确否掉了）。
# ★ 硬约束：
#   a) 弦面 = Z -5.87..-5.73（枢轴 Z -5.80，被拉弦数学写死）：除梢端外，弓片所有段的
#      **后表面**都必须比 -5.87 更靠前，否则未拉时弦会被埋进弓片里（看起来没有弦）。
#   b) 弦端固定在 |X|=6.00，所以梢端必须**越过 |X|=6.00**（这里到 6.45）并在 Z/Y 上包住
#      弦端，否则从玩家视角看就是「弦横向伸出弓臂之外」。
RECURVE_SEGS = [
    # (x_in, x_out, 半高 hy, z_前, z_后)
    (1.10, 2.60, 0.19, -6.62, -6.34),   # 根部（插进弓片座，最靠前）
    (2.60, 3.90, 0.18, -6.46, -6.18),   # 向外 + 往回收
    (3.90, 5.10, 0.16, -6.28, -6.02),
    (5.10, 5.80, 0.14, -6.12, -5.88),
    (5.80, 6.45, 0.12, -5.98, -5.70),   # 梢端：勾回弦面、包住弦端
]
for i, (xa, xb, hy, za, zb) in enumerate(RECURVE_SEGS):
    CUBES.append(C('prod_left', 'prod_l_%d' % i, (-xb, -xa),
                   (-hy, hy), (za, zb), CARBON, tag='prod'))
    CUBES.append(C('prod_right', 'prod_r_%d' % i, (xa, xb),
                   (-hy, hy), (za, zb), CARBON, tag='prod'))

# ================================================================= 弦（长度/端点不可改！）
CUBES += [
    # 枢轴 (-6,0,-5.8) → 末端 (0.54,0,-5.8)：长度 6.54；细弦 0.09
    C('string_left', 'string_l', (-6.00, 0.54), (-0.045, 0.045), (-5.845, -5.755),
      STRING, kind='flat'),
    # 枢轴 (6,0,-5.8) → 末端 (-0.54,0,-5.8)
    C('string_right', 'string_r', (-0.54, 6.00), (-0.045, 0.045), (-5.845, -5.755),
      STRING, kind='flat'),
]

# ================================================================= 弦心（nock）
# ★ 宽 1.16：弦两段各长 6.54（拉满闭合所需），未拉时在中点互相重叠 1.08 ——
#   缠绳必须盖住整段重叠，否则两段共面重叠会 z-fighting（出现闪条）。
CUBES.append(C('nock', 'nock_serve', (-0.58, 0.58), (-0.26, 0.26), (-6.02, -5.58),
               RUBBER))

# ================================================================= 细节件（r42）
# ★ 弓片座螺栓 / 镜座螺丝 / 托底螺丝 / 散热片 / 背带环 与扳机护圈螺栓
CUBES += B.vents('body', 'riser_fin', (-0.50, 0.50, -0.44, 0.28, -7.06, -6.98), 3,
                 RAIL_D, along='x')
for sx in (-1, 1):
    CUBES += B.bolt('body', 'riser_bolt_%d_a' % sx, sx * 1.24, 0.12, -6.34, 0.11, sx * 0.06,
                    STEEL, dark=RAIL_D)
    CUBES += B.bolt('body', 'riser_bolt_%d_b' % sx, sx * 1.24, -0.30, -6.70, 0.11,
                    sx * 0.06, STEEL, dark=RAIL_D)
    CUBES += B.bolt('stock', 'butt_bolt_%d' % sx, sx * 0.48, -0.05, 4.30, 0.12, 0.05,
                    STEEL, axis='z', dark=RAIL_D)
    CUBES += B.bolt('scope', 'scope_scr_%d' % sx, sx * 0.86, 1.24, -3.10, 0.10, sx * 0.05,
                    STEEL, dark=RAIL_D)
# 枪托左侧背带环（六边形小环）
CUBES += B.ring('stock', 'sling', -0.94, -1.16, 2.90, 0.20, 0.075, STEEL, 'metal',
                axis='x', seg=6)
# 握把防滑纹：三道横条
CUBES += B.vents('grip', 'grip_rib', (-0.52, 0.52, -1.46, -0.10, 0.10, 0.94), 3,
                 RAIL_D, along='y', fill=0.30)

# ================================================================= 弩箭（bolt）
CUBES += [
    C('bolt', 'bolt_shaft', (-0.17, 0.17), (-0.06, 0.28), (-9.80, -5.52), BOLT_SH,
      kind='brushed'),
    C('bolt', 'bolt_ferrule', (-0.20, 0.20), (-0.09, 0.31), (-10.10, -9.80), STEEL),
    C('bolt', 'bolt_point', (-0.08, 0.08), (0.02, 0.20), (-10.56, -10.10), BOLT_HL,
      kind='brushed'),
    C('bolt', 'bolt_nock', (-0.12, 0.12), (-0.01, 0.23), (-5.52, -5.24), RUBBER),
]
for i, ang in enumerate((0.0, 120.0, 240.0)):
    CUBES.append(C('bolt', 'bolt_vane_%d' % i, (0.17, 0.52), (0.055, 0.165),
                   (-7.30, -5.86), VANE, rot=(0.0, 0.0, ang), piv=(0.0, 0.11, 0.0),
                   kind='flat'))


def detail_grip(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    for j in range(1, h - 1, 3):
        d.line([(x + 1, y + j), (x + w - 2, y + j)], fill=B.sh(STOCK, 0.74))


def detail_prod(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    if face in ('up', 'down'):
        for j in range(1, h - 1, 3):
            d.line([(x + 1, y + j), (x + w - 2, y + j)], fill=B.sh(CARBON, 1.34))


DETAILS = {'grip': detail_grip, 'prod': detail_prod}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 镜筒是圆柱：按 'z' 轴圆柱烘连续明暗（让八边形镜筒看起来是圆的）
    for _c in CUBES:
        if _c['bone'] == 'scope' and _c['curv'] is None:
            _c['curv'] = ('cyl', 'z', (0.0, 1.24))
    geo, img = B.build(BONES, CUBES, 'geometry.crossbow_geo', details=DETAILS, density=13.0)
    B.write(geo, img, os.path.join(root, 'build', 'crossbow_v2.geo.json'),
            os.path.join(root, 'build', 'crossbow_v2.png'))
    tip_x, dz, nz = 6.0, 2.60, -5.80
    phi = math.atan2(dz, tip_x)
    # 绕 Y 转 θ：(x,z) -> (x cosθ + z sinθ, -x sinθ + z cosθ)
    for label, px, sign in (('string_left ', -tip_x, -1.0), ('string_right', tip_x, 1.0)):
        # 末端相对枢轴的 Δx：左段末端在 X=+0.54（Δx=+6.54），右段末端在 X=-0.54（Δx=-6.54）
        dx = -6.54 * sign
        th = phi * sign
        ex = px + dx * math.cos(th)
        ez = nz + (-dx * math.sin(th))
        print('%s end -> X %+0.3f  Z %+0.3f   (目标 X 0.000  Z %+0.3f)'
              % (label, ex, ez, nz + dz))


if __name__ == '__main__':
    main()
