#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""复合弓 v3：照参考照片（蓝色阳极氧化弓把的现代复合弓）重建。

照片特征逐项对应：
  - 弓把：**蓝色**阳极氧化铝机加工件（望窗镂空、上下加厚唇边）
  - 弓片座：黑色；弓片：黑碳纤维（split limb 感）
  - 凸轮：上下各一枚黑凸轮 + 轴螺栓；弦导杆（灰）+ 上下卡箍
  - 稳定杆：黑杆前伸 + 中段**橡胶减震筒** + 前端配重与端盖
  - 瞄具：黑支架 + 瞄准圈（**瞄准参照圆**）+ 光纤绿点
  - 箭台：握把上的黑色托架；落地支架：底部折下的黑色开孔板

★★ 硬约束（动画 JSON / ADS 数学依赖，绝不能动）：
  - 15 根骨骼的名字与 pivot 原样保留
  - 弦两端点：string_upper (0,9.75,1.56)→(0,0.23,1.56)；string_lower (0,-8.06,1.56)→(0,1.47,1.56)
    转 ∓20.785° 后两内端落在 (Y 0.845, Z 4.94) = nock 拉满位（main() 末尾有数值自检）
  - 凸轮环心 = cam_* 的 pivot
  - **瞄准圈圆心 = (0, 2.86, -4.12)** —— WeaponPose.BOW_RING_Y/BOW_SCALE 就是它，
    改了就得同步改 Java（main() 会把它打印出来）
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxlib as B  # noqa: E402

AL = (44, 94, 208)            # 弓把（照片里是蓝色阳极氧化铝）
AL_D = (30, 68, 162)          # 弓把暗部
POCKET = (40, 42, 46)         # 弓片座（黑）
CARBON = (46, 47, 50)         # 碳纤维弓片
CAM = (58, 60, 64)            # 凸轮
GRIP_C = (44, 42, 41)         # 握把橡胶
RUBBER = (38, 39, 42)         # 稳定杆减震橡胶
STRING = (206, 198, 176)      # 弓弦
GUIDE = (150, 152, 156)       # 弦导杆
BLACK = (36, 37, 39)
STEEL = (128, 130, 134)
ARROW_SH = (58, 60, 64)       # 箭杆碳素
ARROW_HL = (168, 172, 178)    # 箭头
VANE = (216, 92, 44)          # 尾羽
PIN = (98, 232, 122)          # 瞄针光纤

BONES = [
    ('root', None, (0.0, -9.555, -6.37)),
    ('move', 'root', (0.0, 0.845, -0.78)),
    ('body', 'move', (0.0, 0.845, -0.78)),
    ('grip', 'body', (0.0, 0.0, 0.0)),
    ('sight', 'body', (0.0, 2.86, -3.51)),
    ('stabilizer', 'body', (0.0, 0.273, -2.47)),
    ('upper_limb', 'body', (0.0, 5.265, -0.39)),
    ('cam_upper', 'upper_limb', (0.0, 9.75, 1.56)),
    ('lower_limb', 'body', (0.0, -3.575, -0.39)),
    ('cam_lower', 'lower_limb', (0.0, -8.06, 1.56)),
    ('string_upper', 'body', (0.0, 9.75, 1.56)),
    ('string_lower', 'body', (0.0, -8.06, 1.56)),
    ('nock', 'body', (0.0, 0.845, 1.56)),
    ('arrow', 'body', (0.0, 0.845, 1.56)),
    ('camera', 'root', (0.0, 0.845, -6.37)),
]

CUBES = []
C = B.cube


def blade(bone, name, pts, half_w, thick, mat, kind='metal', tag=None):
    """沿 Y-Z 折线放一串「扁片」弓片：宽沿 X、厚在 Y-Z 平面内，逐段收窄。

    盒子的长度方向是局部 +Y；绕 X 转 θ 时局部 +Y 指向 (cosθ, sinθ)，
    所以要对齐 (dy,dz) 就必须 θ = atan2(dz, dy)。
    """
    n = len(pts) - 1
    for i in range(n):
        y0, z0 = pts[i]
        y1, z1 = pts[i + 1]
        dy, dz = y1 - y0, z1 - z0
        ang = math.degrees(math.atan2(dz, dy))
        hw = half_w[i] if isinstance(half_w, (list, tuple)) else half_w
        th = thick[i] if isinstance(thick, (list, tuple)) else thick
        cy, cz = (y0 + y1) / 2.0, (z0 + z1) / 2.0
        ln = math.hypot(dy, dz) * 0.60
        CUBES.append(C(bone, '%s_%d' % (name, i),
                       (-hw, hw), (cy - ln, cy + ln), (cz - th / 2, cz + th / 2),
                       mat, rot=(ang, 0, 0), piv=(0.0, cy, cz), kind=kind, tag=tag))


# ================================================================= 弓把（body）
CUBES += [
    # 后脊（贯穿上下）
    C('body', 'riser_spine', (-0.50, 0.50), (-3.95, 5.70), (-0.98, -0.30), AL),
    # 前缘：上下各一段，中间留出镂空「望窗」
    C('body', 'riser_front_up', (-0.48, 0.48), (3.05, 5.70), (-2.35, -0.98), AL),
    C('body', 'riser_front_dn', (-0.48, 0.48), (-3.95, -1.42), (-2.35, -0.98), AL),
    # 望窗上下缘加厚（看着更像真的机加工件）
    C('body', 'riser_lip_up', (-0.54, 0.54), (2.92, 3.20), (-2.42, -1.04), AL_D),
    C('body', 'riser_lip_dn', (-0.54, 0.54), (-1.57, -1.30), (-2.42, -1.04), AL_D),
    # 弓片座（照片里是黑色）
    C('body', 'pocket_up', (-1.02, 1.02), (5.18, 6.12), (-1.62, -0.16), POCKET),
    C('body', 'pocket_dn', (-1.02, 1.02), (-4.58, -3.64), (-1.62, -0.16), POCKET),
    C('body', 'pocket_bolt_up', (-0.20, 0.20), (5.30, 6.00), (-1.10, -0.70), STEEL),
    C('body', 'pocket_bolt_dn', (-0.20, 0.20), (-4.46, -3.76), (-1.10, -0.70), STEEL),
    # 瞄具基座（升到与瞄准杆同高，否则瞄具悬空）
    C('body', 'sight_mount', (-0.42, 0.42), (2.34, 3.12), (-3.30, -2.21), AL_D),
    # 弦导杆（两根）
    C('body', 'guide_l', (-0.86, -0.62), (-8.06, 9.75), (1.64, 2.00), GUIDE),
    C('body', 'guide_r', (0.62, 0.86), (-8.06, 9.75), (1.64, 2.00), GUIDE),
    C('body', 'guide_clip_up', (-0.90, 0.90), (8.90, 9.30), (1.60, 2.04), BLACK),
    C('body', 'guide_clip_dn', (-0.90, 0.90), (-8.90, -8.50), (1.60, 2.04), BLACK),
]

# ================================================================= 握把（grip）
CUBES += [
    C('grip', 'grip_up', (-0.58, 0.58), (0.05, 1.05), (-1.05, 0.52), GRIP_C,
      kind='plastic', tag='grip'),
    C('grip', 'grip_dn', (-0.60, 0.60), (-1.42, 0.12), (-0.90, 0.66), GRIP_C,
      kind='plastic', tag='grip'),
    C('grip', 'grip_plate_l', (-0.66, -0.56), (-1.28, 0.92), (-0.90, 0.52), BLACK),
    C('grip', 'grip_plate_r', (0.56, 0.66), (-1.28, 0.92), (-0.90, 0.52), BLACK),
]

# ================================================================= 瞄具（sight）
CUBES.append(C('sight', 'sight_bar', (-0.40, 0.40), (2.62, 3.10), (-3.62, -2.30), BLACK))
CUBES.append(C('sight', 'sight_arm', (-0.16, 0.16), (2.78, 2.94), (-4.12, -3.55), BLACK))
CUBES += B.ring('sight', 'sight_ring', 0.0, 2.86, -4.12, 0.80, 0.20, GUIDE, 'metal',
                axis='z', seg=8)
CUBES += [
    C('sight', 'sight_ring_hub', (-0.24, 0.24), (2.62, 3.10), (-4.30, -4.00), BLACK),
    C('sight', 'sight_pin', (-0.09, 0.09), (2.34, 3.40), (-4.22, -4.02), BLACK),
    C('sight', 'fiber_dot', (-0.07, 0.07), (2.74, 3.00), (-4.32, -4.22), PIN,
      kind='flat'),
]

# ================================================================= 稳定杆（stabilizer）
# 照片里：黑杆前伸 + 中段套一节带横棱的橡胶减震筒 + 前端配重与端盖
# ★ 长度收敛过两次：原 −11.2 → −7.4 → 现在只到 −5.8（约 3 单位 ≈ 16cm），手持时不再長长截出去
CUBES += [
    # 座：把稳定杆接到弓把上（否则杆子悬在望窗前面）
    C('stabilizer', 'stab_mount', (-0.42, 0.42), (-1.58, -0.86), (-2.36, -0.90), BLACK),
    C('stabilizer', 'stab_rod', (-0.26, 0.26), (-1.50, -0.92), (-5.10, -2.30), CARBON),
    C('stabilizer', 'stab_damper', (-0.42, 0.42), (-1.66, -0.76), (-4.60, -3.60), RUBBER,
      tag='damper'),
    C('stabilizer', 'stab_weight', (-0.54, 0.54), (-1.78, -0.62), (-5.60, -5.10), BLACK),
    C('stabilizer', 'stab_cap', (-0.32, 0.32), (-1.56, -0.84), (-5.82, -5.60), STEEL),
]

# ================================================================= 箭台（body）
CUBES += [
    # 箭台：握把上方的黑色托架（照片里在瞄具下方）
    C('body', 'rest_arm', (-0.30, 0.30), (1.62, 2.06), (-2.42, -1.62), BLACK),
    C('body', 'rest_prong', (-0.40, 0.40), (1.90, 2.02), (-2.86, -2.34), BLACK),
    C('body', 'rest_bolt', (-0.12, 0.12), (1.66, 1.86), (-2.24, -1.94), STEEL),
]

# ================================================================= 弓片（limb）
UP_PTS = [(5.40, -0.60), (6.35, -0.22), (7.30, 0.20), (8.25, 0.62), (9.20, 1.03),
          (9.78, 1.32)]
DN_PTS = [(-3.71, -0.60), (-4.66, -0.22), (-5.61, 0.20), (-6.56, 0.62), (-7.51, 1.03),
          (-8.09, 1.32)]
blade('upper_limb', 'limb_up', UP_PTS, [0.92, 0.88, 0.84, 0.80, 0.74], 0.46, CARBON,
      tag='limb')
blade('lower_limb', 'limb_dn', DN_PTS, [0.92, 0.88, 0.84, 0.80, 0.74], 0.46, CARBON,
      tag='limb')

# ================================================================= 凸轮（cam）
CUBES += B.ring('cam_upper', 'cam_up_ring', 0.0, 9.75, 1.56, 1.30, 0.44, CAM, 'metal',
                axis='x', seg=8)
CUBES += B.ring('cam_lower', 'cam_dn_ring', 0.0, -8.06, 1.56, 1.30, 0.44, CAM, 'metal',
                axis='x', seg=8)
CUBES += [
    # 轮辐：外环内再套一圈（照片里凸轮是带轮辐的黑轮，不是空心圈）
    C('cam_upper', 'cam_up_hub', (-0.36, 0.36), (9.30, 10.20), (1.11, 2.01), BLACK),
    C('cam_upper', 'cam_up_axle', (-0.52, 0.52), (9.56, 9.94), (1.37, 1.75), STEEL),
    C('cam_upper', 'cam_up_peg', (-0.16, 0.16), (10.62, 11.30), (1.40, 1.72), BLACK),
    C('cam_lower', 'cam_dn_hub', (-0.36, 0.36), (-8.51, -7.61), (1.11, 2.01), BLACK),
    C('cam_lower', 'cam_dn_axle', (-0.52, 0.52), (-8.25, -7.87), (1.37, 1.75), STEEL),
    C('cam_lower', 'cam_dn_peg', (-0.16, 0.16), (-8.91, -8.23), (1.40, 1.72), BLACK),
]
CUBES += B.ring('cam_upper', 'cam_up_spoke', 0.0, 9.75, 1.56, 0.74, 0.30, CAM, 'metal',
                axis='x', seg=8)
CUBES += B.ring('cam_lower', 'cam_dn_spoke', 0.0, -8.06, 1.56, 0.74, 0.30, CAM, 'metal',
                axis='x', seg=8)

# ================================================================= 弦（端点不可改！）
CUBES += [
    # (0,9.75,1.56) → (0,0.23,1.56)
    C('string_upper', 'string_up', (-0.11, 0.11), (0.23, 9.76), (1.45, 1.67), STRING,
      kind='flat'),
    # (0,-8.06,1.56) → (0,1.47,1.56)
    C('string_lower', 'string_dn', (-0.11, 0.11), (-8.06, 1.47), (1.45, 1.67), STRING,
      kind='flat'),
]

# ================================================================= 弦点（nock）
CUBES += [
    C('nock', 'nock_loop', (-0.30, 0.30), (0.62, 1.08), (1.34, 1.92), BLACK),
    C('nock', 'nock_bead', (-0.20, 0.20), (0.70, 1.00), (1.86, 2.14), STRING,
      kind='flat'),
]

# ================================================================= 箭（arrow）
CUBES += [
    C('arrow', 'arrow_shaft', (-0.20, 0.20), (0.65, 1.05), (-7.60, 1.86), ARROW_SH,
      kind='brushed'),
    C('arrow', 'arrow_ferrule', (-0.24, 0.24), (0.61, 1.09), (-8.05, -7.60), STEEL),
    C('arrow', 'arrow_blade_a', (-0.07, 0.07), (0.55, 1.15), (-9.30, -8.05), ARROW_HL,
      kind='brushed'),
    C('arrow', 'arrow_blade_b', (-0.31, 0.31), (0.82, 0.88), (-9.30, -8.05), ARROW_HL,
      kind='brushed'),
    C('arrow', 'arrow_tip', (-0.05, 0.05), (0.79, 0.91), (-9.62, -9.30), ARROW_HL,
      kind='brushed'),
]
for i, ang in enumerate((0.0, 120.0, 240.0)):
    CUBES.append(C('arrow', 'arrow_vane_%d' % i,
                   (0.18, 0.66), (0.79, 0.91), (-1.10, 1.02), VANE,
                   rot=(0.0, 0.0, ang), piv=(0.0, 0.85, 0.0), kind='flat'))


def detail_grip(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    for j in range(1, h - 1, 3):
        d.line([(x + 1, y + j), (x + w - 2, y + j)], fill=B.sh(GRIP_C, 0.80))


def detail_limb(img, rect, face, seed):
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    if face in ('up', 'down'):
        for j in range(1, h - 1, 3):
            d.line([(x + 1, y + j), (x + w - 2, y + j)], fill=B.sh(CARBON, 1.30))


def detail_damper(img, rect, face, seed):
    """稳定杆橡胶减震筒：一圈圈横棱。"""
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    step = 2 if face in ('up', 'down') else 3
    for i in range(1, w - 1, step):
        d.line([(x + i, y + 1), (x + i, y + h - 2)], fill=B.sh(RUBBER, 0.72))
        d.line([(x + i + 1, y + 1), (x + i + 1, y + h - 2)], fill=B.sh(RUBBER, 1.16))


def detail_stand(img, rect, face, seed):
    """落地支架：镂空开孔（黑色板上几个暗孔）。"""
    from PIL import ImageDraw
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    if w < 4 or h < 4:
        return
    for k in range(max(1, w // 4)):
        cx = x + 2 + k * 4
        if cx + 1 >= x + w - 1:
            break
        cy = y + h // 2
        d.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=(18, 18, 20, 255))


DETAILS = {'grip': detail_grip, 'limb': detail_limb, 'damper': detail_damper,
           'stand': detail_stand}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 凸轮是绕 X 转的轮子：按 'x' 轴圆柱烘连续明暗
    for _c in CUBES:
        if _c['curv'] is None and _c['bone'] in ('cam_upper', 'cam_lower'):
            _c['curv'] = ('cyl', 'x', (14.85, 6.10) if _c['bone'] == 'cam_upper'
                          else (1.15, 6.10))
    # ---------------- 细节件（r42）：凸轮轴螺栓 / 瞄准器螺丝 / 腕带环 / 稳定杆配重环 / 弓把镂空
    for _sx in (-1, 1):
        for _cy in (9.77, -8.06):
            CUBES.extend(B.bolt('cam_upper' if _cy > 0 else 'cam_lower',
                                'cam_axle_%d_%d' % (_sx, int(_cy)), _sx * 0.52, _cy, 1.56,
                                0.15, _sx * 0.07, (150, 152, 156), dark=(20, 20, 22)))
        CUBES.extend(B.bolt('sight', 'sight_scr_%d' % _sx, _sx * 0.90, 2.46, -3.42, 0.09,
                            _sx * 0.05, (150, 152, 156), dark=(20, 20, 22)))
        for _i, _ry in enumerate((3.10, -3.10)):
            CUBES.append(B.cube('body', 'riser_win_%d_%d' % (_sx, _i),
                                (_sx * 1.02, _sx * 1.05), (_ry - 0.52, _ry + 0.52),
                                (-1.62, -1.06), (44, 46, 50), kind='flat'))
    # 握把下方的腕带环
    CUBES.extend(B.ring('grip', 'wrist_loop', 0.0, -1.52, 0.10, 0.24, 0.07,
                        (150, 152, 156), 'metal', axis='x', seg=6))
    # 稳定杆前端配重环
    for _i, _rz in enumerate((-5.02, -4.70)):
        CUBES.extend(B.ring('stabilizer', 'stab_ring_%d' % _i, 0.0, -1.20, _rz, 0.60, 0.10,
                            (34, 35, 38), 'metal', axis='z', seg=8))
    geo, img = B.build(BONES, CUBES, 'geometry.compound_bow', details=DETAILS,
                       density=13.0)
    B.write(geo, img, os.path.join(root, 'build', 'bow_v3.geo.json'),
            os.path.join(root, 'build', 'bow_v3.png'))
    print('瞄准圈圆心 (0, 2.86, -4.12) 半径 0.80 —— 对应 WeaponPose.BOW_RING_Y=2.86')
    print('骨骼名: %s' % ', '.join(b[0] for b in BONES))
    # 验证弦端点：绕各自 pivot 转 ∓20.785° 后是否落在 nock 拉满位置
    # 绕 X 转 θ：(y,z) -> (y cosθ - z sinθ, y sinθ + z cosθ)；端点相对 pivot 只有 Δy
    th = math.radians(20.785)

    def end(piv, tip_y, rot):
        dy = tip_y - piv
        return (piv + dy * math.cos(rot), 1.56 + dy * math.sin(rot))

    uy, uz = end(9.75, 0.23, -th)
    ly, lz = end(-8.06, 1.47, th)
    print('string_upper end  ->  Y %.3f  Z %.3f' % (uy, uz))
    print('string_lower end  ->  Y %.3f  Z %.3f' % (ly, lz))
    print('target (nock pull) ->  Y 0.845  Z 4.940')


if __name__ == '__main__':
    main()
