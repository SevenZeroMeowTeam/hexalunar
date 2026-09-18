#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""复合弓：按参考模型（模型/复合弓.bbmodel）的比例重建 GeckoLib 真骨骼方块模型。

参考网格是薄壳网格（体素化会满身破洞，实测 336 方块全是碎点），而且
GeckoLib 4.8.4 不渲染 poly_mesh，所以这里**按参考实测比例手工重建方块**：

  弓把（蓝阳极氧化，带视窗/箭台）、抓把、瞄具（带红点）、稳定杆、
  上/下弓片（阶梯拟合弧度）、上/下凸轮（环+轮毂）、弦（上下两段，可动）、
  弓缆（两根，静止）、箭（隐藏/搭上/随弦后移）。

  尺寸取自参考实测：总高 15.65px、弓片卡槽 y 4.0/11.4、凸轮 y 1.15/14.85、
  稳定杆前伸到 z≈-3.9、弓把 z 3.0~5.6、弦面 z 6.10。

拉弦物理：弦分两段绕凸轮转 φ，长度取拉满时所需（L=7.33），
φ=20.78° 时两端在 (y8.00, z8.70) 正好重合；未拉时两段在中点重叠 0.96px，
被弦中心缠绳（nock）盖住。凸轮同转角，弓片反向微屈。

朝向：箭飞向 -Z（北）。原点：握把中心（手持位置正确）。
贴图：各部件颜色从参考贴图采样中值色，再叠细纹理。

产出：
  geo/compound_bow.geo.json
  textures/models/compound_bow_geo.png (512)
  animations/compound_bow.animation.json   (idle / reload / draw / release)
  模型/复合弓_geo.bbmodel

用法: python tools/bow_gen.py [--tex 512] [--no-bbmodel]
"""
import base64
import io
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
from akm_voxel_gen import load_ref, rotate_tris

REF = '模型/复合弓.bbmodel'
GEO_OUT = 'src/main/resources/assets/hexalunar_calamity/geo/compound_bow.geo.json'
TEX_OUT = 'src/main/resources/assets/hexalunar_calamity/textures/models/compound_bow_geo.png'
ANIM_OUT = 'src/main/resources/assets/hexalunar_calamity/animations/compound_bow.animation.json'
BB_OUT = '模型/复合弓_geo.bbmodel'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')

# 弦几何（见文件头说明）
CAM_Y_U, CAM_Y_L, CAM_Z = 14.85, 1.15, 6.10
NOCK_Y, DRAW_DZ = 8.00, 2.60
SEG_LEN = math.sqrt((CAM_Y_U - NOCK_Y) ** 2 + DRAW_DZ ** 2)          # 7.333
PHI = math.degrees(math.atan2(DRAW_DZ, CAM_Y_U - NOCK_Y))            # 20.78°

# GeckoLib 的物品渲染只吃「几何本身」，不看 model json 里的 display，
# 所以手持大小/位置必须做进模型：整体放大 + 根骨骼绕 Y 转到物品平面
SCALE = 1.30
ROOT_YAW = 90.0
HAND_OFF = (0.0, 0.0, 0.0)      # 手持微调（模型空间，单位像素，先缩放后平移）

# 骨骼：(名字, 父, pivot)
# 层级参考 SuperbWarfare 的 BOCEK 复合弓：move 包住弓身（跑动摆动），
# camera 是无方块的空骨骼（拉弦/放箭时抖第一人称视角）
BONES = [
    ('root', None, (0.0, 0.0, 0.0)),
    ('move', 'root', (0.0, 8.00, 4.30)),
    ('body', 'move', (0.0, 8.00, 4.30)),
    ('grip', 'body', (0.0, 7.35, 4.90)),
    ('sight', 'body', (0.0, 9.55, 2.20)),
    ('stabilizer', 'body', (0.0, 7.56, 3.00)),
    ('upper_limb', 'body', (0.0, 11.40, 4.60)),
    ('cam_upper', 'upper_limb', (0.0, CAM_Y_U, CAM_Z)),
    ('lower_limb', 'body', (0.0, 4.60, 4.60)),
    ('cam_lower', 'lower_limb', (0.0, CAM_Y_L, CAM_Z)),
    ('string_upper', 'body', (0.0, CAM_Y_U, CAM_Z)),
    ('string_lower', 'body', (0.0, CAM_Y_L, CAM_Z)),
    ('nock', 'body', (0.0, NOCK_Y, CAM_Z)),
    ('arrow', 'body', (0.0, NOCK_Y, CAM_Z)),
    ('camera', 'root', (0.0, 8.00, 0.0)),
]

# 部件：(骨骼, x0,x1, y0,y1, z0,z1, 材质)
PARTS = [
    # 弓把（上段全深；中段只留后侧+抓把，前侧凹出视窗缺口；下段全深）
    ('body', -0.70, 0.70, 8.90, 11.40, 3.00, 5.60, 'riser'),
    ('body', -0.70, 0.70, 4.60, 6.40, 3.00, 5.60, 'riser'),
    ('body', -0.70, 0.70, 6.40, 8.90, 4.55, 5.60, 'riser'),      # 视窗后脊
    ('body', -0.70, 0.70, 8.60, 9.05, 2.30, 3.20, 'riser'),      # 箭台（前伸）
    ('body', -0.86, 0.86, 11.40, 12.05, 4.00, 5.35, 'riser'),    # 上弓片卡槽
    ('body', -0.86, 0.86, 3.95, 4.60, 4.00, 5.35, 'riser'),      # 下弓片卡槽
    # 抓把
    ('grip', -0.94, 0.94, 6.30, 8.20, 4.30, 5.62, 'grip'),
    # 瞄具（方环 + 红点）
    ('sight', -0.35, 0.35, 9.30, 9.72, 2.00, 3.10, 'dark'),
    ('sight', -0.30, 0.30, 10.10, 10.45, 1.40, 2.10, 'dark'),
    ('sight', -0.30, 0.30, 8.95, 9.30, 1.40, 2.10, 'dark'),
    ('sight', -0.30, -0.10, 9.30, 10.10, 1.40, 2.10, 'dark'),
    ('sight', 0.10, 0.30, 9.30, 10.10, 1.40, 2.10, 'dark'),
    ('sight', -0.13, 0.13, 9.56, 9.86, 1.50, 1.80, 'red'),
    # 稳定杆（下移，避开箭）
    ('stabilizer', -0.36, 0.36, 6.30, 7.00, -2.60, 3.00, 'dark'),
    ('stabilizer', -0.62, 0.62, 6.04, 7.26, -3.90, -2.60, 'dark'),
    # 上弓片（阶梯拟合弧度）
    ('upper_limb', -0.62, 0.62, 11.40, 12.60, 4.10, 5.40, 'limb'),
    ('upper_limb', -0.55, 0.55, 12.60, 13.70, 4.60, 5.90, 'limb'),
    ('upper_limb', -0.48, 0.48, 13.70, 14.60, 5.20, 6.40, 'limb'),
    ('upper_limb', -0.42, 0.42, 14.60, 14.95, 4.80, 6.20, 'limb'),
    # 下弓片
    ('lower_limb', -0.62, 0.62, 3.40, 4.60, 4.10, 5.40, 'limb'),
    ('lower_limb', -0.55, 0.55, 2.30, 3.40, 4.60, 5.90, 'limb'),
    ('lower_limb', -0.48, 0.48, 1.40, 2.30, 5.20, 6.40, 'limb'),
    ('lower_limb', -0.42, 0.42, 1.05, 1.40, 4.80, 6.20, 'limb'),
    # 弦（两段可动）与缠绳
    ('string_upper', -0.17, 0.17, CAM_Y_U - SEG_LEN, CAM_Y_U, CAM_Z - 0.17, CAM_Z + 0.17, 'string'),
    ('string_lower', -0.17, 0.17, CAM_Y_L, CAM_Y_L + SEG_LEN, CAM_Z - 0.17, CAM_Z + 0.17, 'string'),
    ('nock', -0.46, 0.46, NOCK_Y - 0.80, NOCK_Y + 0.80, CAM_Z - 0.40, CAM_Z + 0.40, 'string'),
    # 弓缆（静止，两根）
    ('body', -0.64, -0.42, CAM_Y_L, CAM_Y_U, CAM_Z + 0.10, CAM_Z + 0.34, 'cable'),
    ('body', 0.42, 0.64, CAM_Y_L, CAM_Y_U, CAM_Z + 0.10, CAM_Z + 0.34, 'cable'),
    # 箭（杆浅碳灰、刀片暗、羽翼更暗，避免与稳定杆混在一起）
    ('arrow', -0.22, 0.22, 7.78, 8.22, -0.90, 6.30, 'shaft'),
    ('arrow', -0.34, 0.34, 7.66, 8.34, -1.60, -0.90, 'tip'),
    ('arrow', -0.07, 0.07, 7.93, 8.07, -2.15, -1.60, 'tip'),
    ('arrow', -0.52, -0.30, 7.70, 8.30, 4.10, 5.60, 'fletch'),
    ('arrow', 0.30, 0.52, 7.70, 8.30, 4.10, 5.60, 'fletch'),
    ('arrow', -0.18, 0.18, 8.30, 8.52, 4.10, 5.60, 'fletch'),
]

# 从参考贴图采样的部件区域（旋转 180° 后坐标系；x 用参考原始值域 -7.3~-2.7）
SAMPLES = {
    'riser': (-6.60, -4.20, 6.00, 12.20, 3.40, 5.60),
    'limb': (-6.00, -4.00, 12.20, 15.20, 3.80, 6.60),
    'cam': (-7.60, -2.40, 0.30, 2.60, 2.40, 5.20),
    'dark': (-6.40, -3.60, 8.60, 10.60, 0.60, 3.00),
    'string': (-5.60, -4.40, 9.00, 14.00, 6.20, 8.60),
    'cable': (-5.60, -4.40, 9.00, 14.00, 6.20, 8.60),
    'shaft': (-6.20, -4.20, 4.00, 6.00, 5.60, 8.20),
    'tip': (-6.20, -4.20, 4.00, 6.00, 5.60, 8.20),
}
FALLBACK = {'riser': (32, 66, 122), 'limb': (52, 54, 58), 'cam': (78, 92, 84),
            'grip': (34, 34, 36), 'dark': (40, 40, 42), 'string': (168, 168, 170),
            'cable': (120, 122, 126), 'shaft': (150, 148, 142), 'tip': (58, 60, 64),
            'fletch': (26, 26, 28), 'red': (192, 44, 38)}


def sample_colors(tris, tex, uv_w, uv_h):
    """按 SAMPLES 的区域从参考贴图取中值色。"""
    cw, ch = tex.size
    px = tex.load()
    out = {}
    for mat in FALLBACK:
        spec = SAMPLES.get(mat)
        cols = []
        if spec:
            x0, x1, y0, y1, z0, z1 = spec
        for t in (tris if spec else []):
            cy = sum(p[1] for p in t[:3]) / 3.0
            cz = sum(p[2] for p in t[:3]) / 3.0
            cx = sum(p[0] for p in t[:3]) / 3.0
            if not (x0 <= cx <= x1 and y0 <= cy <= y1 and z0 <= cz <= z1):
                continue
            for k in range(3):
                u, v = t[3 + k]
                ix = int(u * cw / float(uv_w)) % cw
                iy = int(v * ch / float(uv_h)) % ch
                c = px[ix, iy]
                if len(c) > 3 and c[3] < 128:
                    continue
                cols.append(c[:3])
        if not cols:
            out[mat] = FALLBACK[mat]
            continue
        cols.sort(key=lambda c: c[0] * 3 + c[1] * 6 + c[2])
        out[mat] = cols[len(cols) // 2]
    return out


def build_texture(colors, tex_size):
    """512 贴图：每种材质一块 64x64 色块，叠细纹理（竖向渐变 + 噪点 + 边缘略暗）。"""
    im = Image.new('RGB', (tex_size, tex_size), (24, 24, 26))
    dr = ImageDraw.Draw(im)
    rng = random.Random(20260917)
    slots = {}
    for i, (mat, col) in enumerate(sorted(colors.items())):
        ox, oy = (i % 8) * 64, (i // 8) * 64
        slots[mat] = (ox, oy)
        for y in range(64):
            shade = 1.0 + 0.06 * (0.5 - y / 63.0)          # 上亮下暗
            base = tuple(max(0, min(255, int(c * shade))) for c in col)
            dr.line([(ox, oy + y), (ox + 63, oy + y)], fill=base)
        for _ in range(150):                                # 噪点/磨砂
            x = ox + rng.randrange(64)
            y = oy + rng.randrange(64)
            c = im.getpixel((x, y))
            d = rng.choice((-1, 1)) * rng.randint(3, 9)
            im.putpixel((x, y), tuple(max(0, min(255, v + d)) for v in c))
        for x in range(64):                                 # 左右边缘略暗
            for xx in (ox, ox + 63):
                c = im.getpixel((xx, oy + x))
                im.putpixel((xx, oy + x), tuple(int(v * 0.88) for v in c))
    return im, slots


def main(argv):
    tex_size = 512
    if '--tex' in argv:
        tex_size = int(argv[argv.index('--tex') + 1])
    root_yaw = ROOT_YAW
    if '--roty' in argv:
        root_yaw = float(argv[argv.index('--roty') + 1])
    _v, tris, tex, uv_w, uv_h = load_ref(REF)
    tris = rotate_tris(tris, 180.0)                     # 箭飞向 -Z（北）
    colors = sample_colors(tris, tex, uv_w, uv_h)
    for k in sorted(colors):
        print('  材质 %-8s = %s' % (k, colors[k]))
    atlas, slots = build_texture(colors, tex_size)
    os.makedirs(os.path.dirname(TEX_OUT), exist_ok=True)
    atlas.save(TEX_OUT)

    # ---- 方块 ----
    cubes = {b[0]: [] for b in BONES}

    def add(bone, x0, x1, y0, y1, z0, z1, mat):
        u, v = slots[mat]
        face = {'uv': [u + 0.5, v + 0.5], 'uv_size': [63.0, 63.0]}
        cubes[bone].append({
            'origin': [round(x0, 3), round(y0, 3), round(z0, 3)],
            'size': [round(x1 - x0, 3), round(y1 - y0, 3), round(z1 - z0, 3)],
            'uv': {f: dict(face) for f in FACES},
        })

    for bone, x0, x1, y0, y1, z0, z1, mat in PARTS:
        add(bone, x0, x1, y0, y1, z0, z1, mat)

    # 凸轮：8 块围成环 + 轮毂 + 轮轴
    for bone, yc in (('cam_upper', CAM_Y_U), ('cam_lower', CAM_Y_L)):
        for i in range(8):
            a = math.radians(i * 45.0)
            cy = yc + 1.30 * math.cos(a)
            cz = CAM_Z + 1.30 * math.sin(a)
            add(bone, -0.60, 0.60, cy - 0.53, cy + 0.53, cz - 0.53, cz + 0.53, 'cam')
        add(bone, -0.62, 0.62, yc - 0.58, yc + 0.58, CAM_Z - 0.58, CAM_Z + 0.58, 'cam')
        add(bone, -0.72, 0.72, yc - 0.17, yc + 0.17, CAM_Z - 0.17, CAM_Z + 0.17, 'dark')

    # ---- 原点平移到握把中心，再整体缩放 + 手持微调 ----
    gp = dict((b[0], b[2]) for b in BONES)['grip']
    delta = (-gp[0] * SCALE + HAND_OFF[0], -gp[1] * SCALE + HAND_OFF[1],
             -gp[2] * SCALE + HAND_OFF[2])
    for name in cubes:
        for c in cubes[name]:
            c['origin'] = [round(c['origin'][i] * SCALE + delta[i], 3) for i in range(3)]
            c['size'] = [round(v * SCALE, 3) for v in c['size']]

    out_bones = []
    for name, parent, piv in BONES:
        b = {'name': name,
             'pivot': [round(piv[i] * SCALE + delta[i], 4) for i in range(3)]}
        if parent:
            b['parent'] = parent
        # 根骨骼不再做朝向旋转：统一让几何自己保持「箭向 -Z、上为 +Y」，
        # 手持姿态交给 model json 的 display（与投掷物同一套，已验证正常）
        if cubes.get(name):
            b['cubes'] = cubes[name]
        out_bones.append(b)

    total = sum(len(cubes[b[0]]) for b in BONES)
    geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': 'geometry.compound_bow',
                        'texture_width': tex_size, 'texture_height': tex_size,
                        'visible_bounds_width': 2, 'visible_bounds_height': 3,
                        'visible_bounds_offset': [0, 0, 0]},
        'bones': out_bones}]}
    with open(GEO_OUT, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, indent=1)
    print('模型 -> %s（%d 骨骼 / %d 方块）' % (GEO_OUT, len(out_bones), total))

    write_anims(delta)
    if '--no-bbmodel' not in argv:
        write_bbmodel(out_bones, cubes, tex_size)
    return 0


def _kf(pairs):
    """[(time, [x,y,z])] -> 关键帧 dict"""
    return dict((('%g' % t), {'post': [round(v, 3) for v in val]}) for t, val in pairs)


def _kfv(pairs):
    # 位移单位是模型像素，几何放大后要同步放大，否则拉弦距离对不上弦长
    return dict((('%g' % t), {'vector': [round(v * SCALE, 3) for v in val]})
                for t, val in pairs)


def write_anims(_delta):
    """动画配置照 SuperbWarfare 的 BOCEK 复合弓规范（同名同播放类型）：
      animation.compound_bow.idle / run / run_fast  loop
      animation.compound_bow.pull                   hold_on_last_frame（拉满保持）
      animation.compound_bow.fire / reload          play_once
    结构必须是 骨骼 → rotation|position → 时间 → post|vector（GeckoLib 按通道名取）。
    """
    P = 'animation.compound_bow.'
    idle = {'loop': True, 'animation_length': 1.8667, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.93, [0.35, 0, 0.25]), (1.87, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (0.93, [-0.3, 0, -0.2]), (1.87, [0, 0, 0])])},
        'arrow': {'position': _kfv([(0.0, [0, -40, 0])])},
    }}
    run = {'loop': True, 'animation_length': 0.8333, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.21, [2.6, 0, -0.8]), (0.42, [0, 0, 0]),
                                  (0.63, [-2.2, 0, 0.6]), (0.83, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.21, [0, -0.5, 0]), (0.42, [0, 0, 0]),
                                   (0.63, [0, 0.5, 0]), (0.83, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (0.42, [1.2, 0, 1.6]), (0.83, [0, 0, 0])])},
        'arrow': {'position': _kfv([(0.0, [0, -40, 0])])},
    }}
    run_fast = {'loop': True, 'animation_length': 0.6, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.15, [4.0, 0, -1.4]), (0.30, [0, 0, 0]),
                                  (0.45, [-3.4, 0, 1.0]), (0.60, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.15, [0, -0.9, 0]), (0.30, [0, 0, 0]),
                                   (0.45, [0, 0.9, 0]), (0.60, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (0.30, [1.8, 0, 2.4]), (0.60, [0, 0, 0])])},
        'arrow': {'position': _kfv([(0.0, [0, -40, 0])])},
    }}
    pull = {'loop': 'hold_on_last_frame', 'animation_length': 1.0, 'bones': {
        'string_upper': {'rotation': _kf([(0.0, [0, 0, 0]), (0.25, [2.0, 0, 0]), (1.0, [-PHI, 0, 0])])},
        'string_lower': {'rotation': _kf([(0.0, [0, 0, 0]), (0.25, [-2.0, 0, 0]), (1.0, [PHI, 0, 0])])},
        'nock': {'position': _kfv([(0.0, [0, 0, 0]), (1.0, [0, 0, DRAW_DZ])])},
        'arrow': {'position': _kfv([(0.0, [0, -40, 0]), (0.22, [0, 0, 0]), (1.0, [0, 0, DRAW_DZ])])},
        'cam_upper': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [-38, 0, 0])])},
        'cam_lower': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [-38, 0, 0])])},
        'upper_limb': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [-2.6, 0, 0])])},
        'lower_limb': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [2.6, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [0.8, 0, 0])])},
        'move': {'position': _kfv([(0.0, [0, 0, 0]), (1.0, [0, 0, -0.6])])},
        'camera': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [-1.6, 0.8, 0])])},
    }}
    fire = {'loop': False, 'animation_length': 0.4, 'bones': {
        'string_upper': {'rotation': _kf([(0.0, [-PHI, 0, 0]), (0.12, [4.2, 0, 0]), (0.4, [0, 0, 0])])},
        'string_lower': {'rotation': _kf([(0.0, [PHI, 0, 0]), (0.12, [-4.2, 0, 0]), (0.4, [0, 0, 0])])},
        'nock': {'position': _kfv([(0.0, [0, 0, DRAW_DZ]), (0.12, [0, 0, -0.6]), (0.4, [0, 0, 0])])},
        'arrow': {'position': _kfv([(0.0, [0, 0, DRAW_DZ]), (0.1, [0, 0, -10]), (0.4, [0, -40, 0])])},
        'cam_upper': {'rotation': _kf([(0.0, [-38, 0, 0]), (0.4, [0, 0, 0])])},
        'cam_lower': {'rotation': _kf([(0.0, [-38, 0, 0]), (0.4, [0, 0, 0])])},
        'upper_limb': {'rotation': _kf([(0.0, [-2.6, 0, 0]), (0.16, [1.6, 0, 0]), (0.4, [0, 0, 0])])},
        'lower_limb': {'rotation': _kf([(0.0, [2.6, 0, 0]), (0.16, [-1.6, 0, 0]), (0.4, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0.8, 0, 0]), (0.1, [-1.4, 0, 0]), (0.4, [0, 0, 0])])},
        'move': {'position': _kfv([(0.0, [0, 0, -0.6]), (0.1, [0, 0, 0.9]), (0.4, [0, 0, 0])])},
        'camera': {'rotation': _kf([(0.0, [-1.6, 0.8, 0]), (0.1, [-4.2, -0.6, 0]), (0.4, [0, 0, 0])])},
    }}
    reload_ = {'loop': False, 'animation_length': 0.35, 'bones': {
        'arrow': {'position': _kfv([(0.0, [0, -40, 7]), (0.18, [0, 0, 7]), (0.28, [0, 0, 0]),
                                    (0.35, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (0.18, [0, 0, -2.2]), (0.35, [0, 0, 0])])},
        'string_upper': {'rotation': _kf([(0.0, [0, 0, 0]), (0.22, [3.4, 0, 0]), (0.35, [0, 0, 0])])},
        'string_lower': {'rotation': _kf([(0.0, [0, 0, 0]), (0.22, [-3.4, 0, 0]), (0.35, [0, 0, 0])])},
        'nock': {'position': _kfv([(0.0, [0, 0, 0]), (0.22, [0, 0, 0.8]), (0.35, [0, 0, 0])])},
    }}
    anims = {'format_version': '1.8.0', 'animations': {
        P + 'idle': idle, P + 'run': run, P + 'run_fast': run_fast,
        P + 'pull': pull, P + 'fire': fire, P + 'reload': reload_}}
    os.makedirs(os.path.dirname(ANIM_OUT), exist_ok=True)
    with open(ANIM_OUT, 'w', encoding='utf-8') as fh:
        json.dump(anims, fh, ensure_ascii=False, indent=1)
    print('动画 -> %s（BOCEK 规范：idle/run/run_fast[loop]、pull[hold_on_last_frame]、'
          'fire/reload[play_once]；φ=%.2f° 弦长 %.2f）' % (ANIM_OUT, PHI, SEG_LEN))
    return 0


def write_bbmodel(out_bones, cubes, tex_size):
    elements, groups = [], []
    for name, parent, _piv in BONES:
        cs = cubes.get(name) or []
        if not cs:
            continue
        piv = dict((b['name'], b['pivot']) for b in out_bones)[name]
        uu = _uuid(name)
        for i, c in enumerate(cs):
            elements.append({'name': '%s_%d' % (name, i), 'type': 'cube',
                             'uuid': _uuid('%s_%d' % (name, i)), 'origin': c['origin'],
                             'size': c['size'], 'inflate': 0, 'uv': c['uv'],
                             'visibility': True, 'export': True, 'locked': False})
        groups.append({'name': name, 'uuid': uu, 'origin': piv, 'rotation': [0, 0, 0],
                       'children': [_uuid('%s_%d' % (name, i)) for i in range(len(cs))],
                       'visibility': True, 'autouv': 0, 'color': 0, 'export': True,
                       'locked': False, 'isOpen': False, 'parent': parent or 'root'})
    with open(TEX_OUT, 'rb') as fh:
        durl = 'data:image/png;base64,' + base64.b64encode(fh.read()).decode()
    bb = {'meta': {'format_version': '4.5', 'model_format': 'geckolib_model', 'box_uv': False},
          'name': 'compound_bow_geo', 'resolution': {'width': tex_size, 'height': tex_size},
          'elements': elements, 'outliner': [g['uuid'] for g in groups], 'groups': groups,
          'textures': [{'path': '', 'name': 'compound_bow_geo.png', 'folder': 'block',
                        'namespace': '', 'id': '0', 'particle': False,
                        'render_mode': 'default', 'visible': True, 'mode': 'bitmap',
                        'saved': True, 'uuid': _uuid('tex'), 'source': durl}],
          'animations': [], 'animation_controllers': []}
    with open(BB_OUT, 'w', encoding='utf-8') as fh:
        json.dump(bb, fh, ensure_ascii=False)
    print('工程 -> %s（%.2f MB）' % (BB_OUT, os.path.getsize(BB_OUT) / 1048576))
    return 0


def _uuid(s):
    import hashlib
    h = hashlib.md5(s.encode('utf-8')).hexdigest()
    return '%s-%s-%s-%s-%s' % (h[:8], h[8:12], h[12:16], h[16:20], h[20:32])


if __name__ == '__main__':
    sys.exit(main(sys.argv))
