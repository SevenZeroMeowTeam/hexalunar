#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AKM 重建：手写方块 + GeckoLib 真骨骼（参考 模型/akm.bbmodel 的照片贴图取色）。

为什么重建：参考 mesh 自带 ~10.8° 俯仰倾斜（枪口端 Y≈3.9、枪托端 Y≈0.9），
体素化出来必然是"斜楼梯"，在手里就是一团。这里按真实 AKM 比例手摆。

坐标：单位 = 1/16 格；枪口朝 **-Z（north）**；上 +Y；右 +X；原点在握把中段（手持点）。
部件（对齐真实 AKM，长 16.4 / 高 ~5.4 单位 = 1.03 格长 / 34cm 高）：
  枪管 + 枪口制退器 + 通气管 + 通条、准星座/照门、护木（上/下，木）、
  机匣（带抛壳口）+ 机匣盖、枪机框 + 拉机柄（亮钢）、弹匣（前弯，3 节）、
  扳机 + 护圈、握把（后倾 22°）、枪托 + 托底板、快慢机（保险）拨杆、背带环。
骨骼：root > move > body > {handguard, barrel, sights, dust_cover, bolt,
      magazine, trigger, selector, grip, stock, camera(无方块，驱动第一人称相机)}

动画（SuperbWarfare/BOCEK 规范）：idle/run/run_fast[loop]、fire、bolt（拉机柄上膛）、
      reload（换弹匣）、safety（拨保险/快慢机）。

产出：geo/akm.geo.json、textures/models/akm_geo.png、animations/akm.animation.json、
      模型/akm_geo.bbmodel（Blockbench geckolib_model 工程，可直接打开改）

用法: python tools/akm_rebuild.py [--tex 512] [--no-bbmodel]
"""
import base64
import hashlib
import io
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
from akm_voxel_gen import load_ref            # noqa: E402

REF = '模型/akm.bbmodel'
GEO_OUT = 'src/main/resources/assets/hexalunar_calamity/geo/akm.geo.json'
TEX_OUT = 'src/main/resources/assets/hexalunar_calamity/textures/models/akm_geo.png'
ANIM_OUT = 'src/main/resources/assets/hexalunar_calamity/animations/akm.animation.json'
BB_OUT = '模型/akm_geo.bbmodel'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')

GRIP = (0.0, -1.75, 0.85)      # 原点：握把中段（手持点）
CAM_PIVOT = (0.0, 0.90, -1.00)  # 相机骨（无方块）

BONES = [
    ('root', None, (0.0, 0.0, 0.0)),
    ('move', 'root', (0.0, 0.0, 0.0)),
    ('body', 'move', (0.0, 0.0, 0.0)),
    ('stock', 'body', (0.0, -0.60, 3.60)),
    ('grip', 'body', (0.0, -0.90, 0.85)),
    ('handguard', 'body', (0.0, 0.20, -5.40)),
    ('barrel', 'body', (0.0, 0.0, -6.80)),
    ('sights', 'body', (0.0, 1.00, -3.70)),
    ('dust_cover', 'body', (0.0, 1.38, -1.10)),
    ('bolt', 'body', (0.0, 0.45, -0.20)),
    ('magazine', 'body', (0.0, -0.95, -2.25)),
    ('trigger', 'body', (0.0, -0.95, -0.75)),
    ('selector', 'body', (0.0, 0.35, -1.55)),
    ('camera', 'body', CAM_PIVOT),
]

# 材质采样区（在**摆正后**的参考 bbox 里按比例取，fx/fy/fz 均为 0..1）
SAMPLES = {
    'wood_hand': (0.00, 1.00, 0.30, 1.00, 0.26, 0.47),
    'wood_stock': (0.00, 1.00, 0.00, 0.80, 0.80, 0.98),
    'wood_grip': (0.00, 1.00, 0.00, 0.55, 0.63, 0.78),
    'metal_recv': (0.00, 1.00, 0.35, 0.90, 0.45, 0.62),
    'metal_cover': (0.00, 1.00, 0.55, 1.00, 0.45, 0.62),
    'metal_barrel': (0.00, 1.00, 0.30, 0.80, 0.04, 0.26),
    'metal_mag': (0.00, 1.00, 0.00, 0.45, 0.28, 0.42),
    'metal_sight': (0.00, 1.00, 0.70, 1.00, 0.06, 0.20),
    'bolt_steel': (0.55, 1.00, 0.45, 0.85, 0.46, 0.60),
    'lever': (0.55, 1.00, 0.40, 0.80, 0.60, 0.76),
    'black': (0.00, 1.00, 0.00, 0.45, 0.94, 1.00),
    'sling': (0.00, 1.00, 0.00, 0.40, 0.66, 0.74),
}
MATERIAL = {'wood_hand': (150, 105, 58), 'wood_stock': (140, 96, 52),
            'wood_grip': (110, 72, 40), 'metal_recv': (58, 60, 62),
            'metal_cover': (70, 72, 74), 'metal_barrel': (48, 50, 52),
            'metal_mag': (62, 62, 60), 'metal_sight': (44, 46, 48),
            'bolt_steel': (168, 170, 172), 'lever': (66, 68, 70),
            'black': (30, 30, 32), 'sling': (46, 44, 40)}


# ---------------------------------------------------------------- 参考预处理
def straighten(tris):
    """摆正参考 mesh：用 PCA 求 Z-Y 平面主轴倾角，绕 X 轴转平；并把 X 居中。

    返回 (tris, x_center, y_axis)，y_axis = 摆正后枪管轴线所在 Y（= 主轴中位）。
    """
    pts = [p for t in tris for p in t[:3]]
    n = len(pts)
    mz = sum(p[2] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    szz = sum((p[2] - mz) ** 2 for p in pts) / n
    syy = sum((p[1] - my) ** 2 for p in pts) / n
    szy = sum((p[2] - mz) * (p[1] - my) for p in pts) / n
    ang = 0.5 * math.atan2(2.0 * szy, szz - syy)     # 主轴相对 Z 轴的倾角
    ca, sa = math.cos(-ang), math.sin(-ang)
    mx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2.0

    def f(p):
        x, y, z = p[0] - mx, p[1] - my, p[2] - mz
        return (x, y * ca - z * sa, y * sa + z * ca)

    out = [(f(t[0]), f(t[1]), f(t[2]), t[3], t[4], t[5]) for t in tris]
    ys = [q[1] for t in out for q in t[:3]]
    # 轴线：取中位 Y（长杆件的主体，枪管/机匣一线）
    y_axis = sorted(ys)[int(len(ys) * 0.62)]
    print('摆正：主轴倾角 %.2f°（枪口端 %s），X 居中偏移 %.2f，轴线 Y=%.2f'
          % (math.degrees(ang), '低' if ang > 0 else '高', mx, y_axis))
    return out, mx, y_axis


def shade(patch, base):
    px = list(patch.getdata())
    lums = sorted(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2] for c in px)
    mid = lums[len(lums) // 2] or 1.0
    out = Image.new('RGB', patch.size)
    out.putdata([tuple(max(0, min(255, int(v * max(0.72, min(1.28,
                    0.52 + 0.53 * ((0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / mid))))))
                 for v in base) for c in px])
    return out


def sample_patches(tris, tex, uv_w, uv_h, size=112):
    cw, ch = tex.size
    pts = [p for t in tris for p in t[:3]]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    print('摆正后 bbox  X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]  尺寸 %.2f x %.2f x %.2f'
          % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2],
             hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))

    def box(fx, fy, fz):
        return (lo[0] + fx[0] * (hi[0] - lo[0]), lo[0] + fx[1] * (hi[0] - lo[0]),
                lo[1] + fy[0] * (hi[1] - lo[1]), lo[1] + fy[1] * (hi[1] - lo[1]),
                lo[2] + fz[0] * (hi[2] - lo[2]), lo[2] + fz[1] * (hi[2] - lo[2]))

    out = {}
    for mat, spec in SAMPLES.items():
        x0, x1, y0, y1, z0, z1 = box(spec[0:2], spec[2:4], spec[4:6])
        uvs = []
        for t in tris:
            cx = sum(p[0] for p in t[:3]) / 3.0
            cy = sum(p[1] for p in t[:3]) / 3.0
            cz = sum(p[2] for p in t[:3]) / 3.0
            if not (x0 <= cx <= x1 and y0 <= cy <= y1 and z0 <= cz <= z1):
                continue
            for k in range(3):
                u, v = t[3 + k]
                uvs.append((u * cw / float(uv_w), v * ch / float(uv_h)))
        if not uvs:
            out[mat] = shade(Image.new('RGB', (size, size), MATERIAL[mat]), MATERIAL[mat])
            print('  %-12s 无采样 -> 纯色 %s' % (mat, MATERIAL[mat]))
            continue
        mu = sorted(u[0] for u in uvs)[len(uvs) // 2]
        mv = sorted(u[1] for u in uvs)[len(uvs) // 2]
        h = size // 2
        b = (int(mu) - h, int(mv) - h, int(mu) + h, int(mv) + h)
        patch = Image.new('RGB', (size, size), MATERIAL[mat])
        clip = (max(b[0], 0), max(b[1], 0), min(b[2], cw), min(b[3], ch))
        if clip[2] > clip[0] and clip[3] > clip[1]:
            patch.paste(tex.crop(clip).convert('RGB'),
                        (clip[0] - b[0], clip[1] - b[1]))
        shrunk = shade(patch, MATERIAL[mat])
        px = list(shrunk.getdata())
        r = sum(c[0] for c in px) // len(px)
        g = sum(c[1] for c in px) // len(px)
        bl = sum(c[2] for c in px) // len(px)
        print('  %-12s uv=(%6.1f,%6.1f) n=%5d 均值=(%3d,%3d,%3d)' % (mat, mu, mv, len(uvs), r, g, bl))
        out[mat] = shrunk
    return out


def build_texture(patches, tex_size, cell=128, pad=8):
    im = Image.new('RGB', (tex_size, tex_size), (26, 26, 28))
    dr = ImageDraw.Draw(im)
    slots, names = {}, sorted(SAMPLES)
    per_row = tex_size // cell
    for i, mat in enumerate(names):
        ox, oy = (i % per_row) * cell, (i // per_row) * cell
        slots[mat] = (ox, oy)
        im.paste(patches[mat].resize((cell - 2 * pad, cell - 2 * pad), Image.LANCZOS),
                 (ox + pad, oy + pad))
        dr.rectangle([ox, oy, ox + cell - 1, oy + cell - 1], outline=(34, 36, 36))
    return im, slots


# ------------------------------------------------------------------- 主构建
def build(argv):
    tex_size = 512
    if '--tex' in argv:
        tex_size = int(argv[argv.index('--tex') + 1])
    _v, tris, tex, uv_w, uv_h = load_ref(REF)
    if tex is None:
        raise SystemExit('参考模型里没找到内嵌贴图')
    tris, _xc, _ya = straighten(tris)
    atlas, slots = build_texture(sample_patches(tris, tex, uv_w, uv_h), tex_size)
    os.makedirs(os.path.dirname(TEX_OUT), exist_ok=True)
    atlas.save(TEX_OUT)

    cubes = {b[0]: [] for b in BONES}

    def add(bone, x, y, z, mat, rot=None, pivot=None):
        """x/y/z = ((x0,x1),(y0,y1),(z0,z1))，gun 空间；rot 为绕 pivot 的欧拉角(度)。"""
        u, v = slots[mat]
        c = {'origin': [round((x[0] - GRIP[0]), 3), round((y[0] - GRIP[1]), 3),
                        round((z[0] - GRIP[2]), 3)],
             'size': [round(x[1] - x[0], 3), round(y[1] - y[0], 3), round(z[1] - z[0], 3)],
             'uv': {f: {'uv': [u + 9.0, v + 9.0], 'uv_size': [110.0, 110.0]} for f in FACES}}
        if rot:
            c['pivot'] = [round(pivot[i] - GRIP[i], 3) for i in range(3)]
            c['rotation'] = [round(r, 3) for r in rot]
        cubes[bone].append(c)

    # ---- 枪管组 ----
    add('barrel', (-0.38, 0.38), (-0.38, 0.38), (-9.60, -3.90), 'metal_barrel')
    add('barrel', (-0.45, 0.45), (-0.45, 0.45), (-9.95, -9.60), 'black')      # 枪口制退器
    add('barrel', (-0.42, 0.42), (0.38, 0.98), (-8.70, -8.10), 'metal_sight')  # 准星座
    add('barrel', (-0.42, -0.28), (0.98, 1.60), (-8.66, -8.14), 'metal_sight')  # 准星护翼 L
    add('barrel', (0.28, 0.42), (0.98, 1.60), (-8.66, -8.14), 'metal_sight')   # 准星护翼 R
    add('barrel', (-0.09, 0.09), (0.98, 1.66), (-8.52, -8.34), 'metal_sight')  # 准星
    add('barrel', (-0.40, 0.40), (0.38, 1.18), (-7.30, -6.70), 'metal_sight')  # 导气箍
    add('barrel', (-0.30, 0.30), (0.70, 1.22), (-6.90, -3.90), 'metal_barrel')  # 通气管
    add('barrel', (-0.11, 0.11), (-0.62, -0.40), (-9.40, -4.70), 'metal_barrel')  # 通条

    # ---- 护木（木）----
    add('handguard', (-0.80, 0.80), (-0.95, 0.45), (-6.85, -3.95), 'wood_hand')  # 下护木
    add('handguard', (-0.68, 0.68), (0.45, 1.30), (-6.85, -3.95), 'wood_hand')   # 上护木
    add('handguard', (-0.82, 0.82), (-0.85, 1.26), (-7.06, -6.84), 'metal_sight')  # 护木卡箍

    # ---- 照门 ----
    add('sights', (-0.55, 0.55), (0.38, 1.30), (-4.05, -3.35), 'metal_sight')   # 照门座
    add('sights', (-0.45, 0.45), (1.30, 1.62), (-3.95, -3.55), 'metal_sight')   # 照门片

    # ---- 机匣（带抛壳口）----
    add('body', (-0.72, 0.72), (-0.95, -0.30), (-3.55, 1.75), 'metal_recv')     # 机匣底
    add('body', (-0.72, -0.54), (-0.30, 0.95), (-3.55, 1.75), 'metal_recv')     # 左壁
    add('body', (0.54, 0.72), (-0.30, 0.95), (-3.55, -1.20), 'metal_recv')      # 右壁(前)
    add('body', (0.54, 0.72), (-0.30, 0.95), (0.25, 1.75), 'metal_recv')        # 右壁(后)
    add('body', (0.54, 0.72), (-0.30, 0.10), (-1.20, 0.25), 'metal_recv')       # 抛壳口下沿
    add('body', (-0.75, 0.75), (-0.95, 0.98), (-3.80, -3.20), 'metal_recv')     # 前节套
    add('body', (-0.70, 0.70), (-0.95, 0.88), (1.75, 2.00), 'metal_recv')       # 后节套
    add('body', (-0.78, 0.78), (-1.12, -0.62), (-7.00, -6.70), 'black')         # 前背带环
    add('body', (-0.78, -0.42), (-1.12, -0.62), (1.55, 1.88), 'black')          # 后背带环

    # ---- 机匣盖 ----
    add('dust_cover', (-0.66, 0.66), (0.95, 1.38), (-3.60, 1.30), 'metal_cover')
    add('dust_cover', (-0.68, 0.68), (1.30, 1.42), (-2.90, -2.50), 'metal_cover')  # 加强筋
    add('dust_cover', (-0.68, 0.68), (1.30, 1.42), (0.25, 0.65), 'metal_cover')

    # ---- 枪机框 + 拉机柄（亮钢）----
    add('bolt', (-0.50, 0.50), (0.05, 0.88), (-2.40, 0.60), 'bolt_steel')
    add('bolt', (0.50, 1.45), (0.18, 0.58), (-0.55, 0.25), 'bolt_steel')
    add('bolt', (1.45, 1.66), (0.06, 0.70), (-0.78, 0.48), 'bolt_steel')

    # ---- 弹匣（前弯三节 + 底板，逐节绕 X 前倾）----
    mp = (0.0, -0.95, -2.25)
    add('magazine', (-0.62, 0.62), (-1.88, -0.90), (-3.06, -1.44), 'metal_mag')
    add('magazine', (-0.60, 0.60), (-2.70, -1.80), (-3.14, -1.52), 'metal_mag', (10, 0, 0), mp)
    add('magazine', (-0.58, 0.58), (-3.42, -2.60), (-3.30, -1.68), 'metal_mag', (20, 0, 0), mp)
    add('magazine', (-0.60, 0.60), (-3.80, -3.44), (-3.46, -1.84), 'metal_mag', (22, 0, 0), mp)

    # ---- 扳机 + 护圈 ----
    add('trigger', (-0.14, 0.14), (-1.58, -0.95), (-0.98, -0.56), 'black', (-8, 0, 0), (0, -0.98, -0.95))
    add('body', (-0.16, 0.16), (-1.62, -1.40), (-1.38, -0.88), 'black')
    add('body', (-0.16, 0.16), (-1.72, -1.52), (-1.38, 0.12), 'black')

    # ---- 握把（后倾 22°）----
    add('grip', (-0.60, 0.60), (-2.62, -0.90), (0.32, 1.36), 'wood_grip',
        (-22, 0, 0), (0.0, -0.90, 0.85))

    # ---- 枪托 + 托底板 ----
    add('stock', (-0.62, 0.62), (-1.35, 0.60), (2.00, 3.62), 'wood_stock')
    add('stock', (-0.72, 0.72), (-1.95, 0.70), (3.62, 6.10), 'wood_stock')
    add('stock', (-0.74, 0.74), (-2.05, 0.80), (6.10, 6.45), 'black')

    # ---- 快慢机（保险拨杆，模型默认在"连发"位）----
    add('selector', (0.72, 0.95), (0.10, 0.55), (-1.55, 0.90), 'lever', (0, 0, 0), (0, 0, -1.55))
    add('selector', (0.58, 0.80), (0.16, 0.48), (-1.78, -1.36), 'lever')

    out_bones = []
    for name, parent, piv in BONES:
        b = {'name': name, 'pivot': [round(piv[i] - GRIP[i], 3) for i in range(3)]}
        if parent:
            b['parent'] = parent
        if cubes.get(name):
            b['cubes'] = cubes[name]
        out_bones.append(b)

    total = sum(len(cubes[b[0]]) for b in BONES)
    geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': 'geometry.akm', 'texture_width': tex_size,
                        'texture_height': tex_size, 'visible_bounds_width': 2,
                        'visible_bounds_height': 2, 'visible_bounds_offset': [0, 0, 0]},
        'bones': out_bones}]}
    os.makedirs(os.path.dirname(GEO_OUT), exist_ok=True)
    with open(GEO_OUT, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, indent=1)
    print('模型 -> %s（%d 骨骼 / %d 方块）'
          % (GEO_OUT, len(out_bones), total))
    write_anims()
    if '--no-bbmodel' not in argv:
        write_bbmodel(out_bones, cubes, tex_size)
    return 0


def _kf(pairs):
    return dict((('%g' % t), {'post': [round(v, 3) for v in val]}) for t, val in pairs)


def _kfv(pairs):
    return dict((('%g' % t), {'vector': [round(v, 3) for v in val]}) for t, val in pairs)


def write_anims():
    P = 'animation.akm.'
    idle = {'loop': True, 'animation_length': 2.6, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (1.3, [0.45, 0, 0.28]), (2.6, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (1.3, [0, -0.11, 0]), (2.6, [0, 0, 0])])},
        'camera': {'rotation': _kf([(0.0, [0, 0, 0]), (1.3, [0.30, 0.20, 0]), (2.6, [0, 0, 0])])},
    }}
    run = {'loop': True, 'animation_length': 0.8333, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.21, [3.2, 0, -1.0]), (0.42, [0, 0, 0]),
                                  (0.63, [-2.6, 0, 0.9]), (0.83, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.21, [0, -0.5, 0]), (0.42, [0, 0, 0]),
                                   (0.63, [0, 0.5, 0]), (0.83, [0, 0, 0])])},
        'camera': {'rotation': _kf([(0.0, [0, 0, 0]), (0.21, [1.2, 0.6, 0]), (0.42, [0, 0, 0]),
                                    (0.63, [-1.0, -0.6, 0]), (0.83, [0, 0, 0])])},
    }}
    run_fast = {'loop': True, 'animation_length': 0.6, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.15, [4.8, 0, -1.6]), (0.30, [0, 0, 0]),
                                  (0.45, [-3.8, 0, 1.3]), (0.60, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.15, [0, -0.9, 0]), (0.30, [0, 0, 0]),
                                   (0.45, [0, 0.9, 0]), (0.60, [0, 0, 0])])},
        'camera': {'rotation': _kf([(0.0, [0, 0, 0]), (0.15, [1.9, 1.0, 0]), (0.30, [0, 0, 0]),
                                    (0.45, [-1.6, -0.9, 0]), (0.60, [0, 0, 0])])},
    }}
    # 开火：枪机后坐复进 + 机体后座 + 相机上跳
    fire = {'loop': False, 'animation_length': 0.30, 'bones': {
        'bolt': {'position': _kfv([(0.0, [0, 0, 0]), (0.07, [0, 0, 2.3]), (0.17, [0, 0, 0]),
                                   (0.30, [0, 0, 0])])},
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.05, [-2.8, 0, 0.6]), (0.13, [1.5, 0, -0.3]),
                                  (0.30, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.05, [0, 0.15, 0.45]), (0.30, [0, 0, 0])])},
        'dust_cover': {'rotation': _kf([(0.0, [0, 0, 0]), (0.07, [-0.8, 0, 0]), (0.20, [0, 0, 0])])},
        'magazine': {'rotation': _kf([(0.0, [0, 0, 0]), (0.06, [-0.7, 0, 0]), (0.22, [0, 0, 0])])},
        'trigger': {'rotation': _kf([(0.0, [0, 0, 0]), (0.04, [-7, 0, 0]), (0.22, [0, 0, 0])])},
        'camera': {'rotation': _kf([(0.0, [0, 0, 0]), (0.05, [-1.7, 0.5, 0]), (0.30, [0, 0, 0])])},
    }}
    # 拉机柄上膛
    bolt = {'loop': False, 'animation_length': 0.80, 'bones': {
        'bolt': {'position': _kfv([(0.0, [0, 0, 0]), (0.24, [0, 0, 3.6]), (0.36, [0, 0, 3.6]),
                                   (0.52, [0, 0, -0.30]), (0.66, [0, 0, 0]), (0.80, [0, 0, 0])])},
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.30, [1.2, 0, -1.5]), (0.62, [0, 0, 0])])},
        'camera': {'rotation': _kf([(0.0, [0, 0, 0]), (0.30, [0.6, 0, -1.1]), (0.62, [0, 0, 0])])},
    }}
    # 换弹匣：旧匣脱落 → 新匣插入 → 拉机柄上膛
    reload_ = {'loop': False, 'animation_length': 2.10, 'bones': {
        'magazine': {'position': _kfv([(0.0, [0, 0, 0]), (0.30, [0, -0.5, 0]), (0.62, [0, -6.5, 0]),
                                       (0.80, [0, -6.5, 0]), (1.30, [0, -2.2, 0]), (1.60, [0, 0, 0]),
                                       (1.76, [0, -0.35, 0]), (2.10, [0, 0, 0])]),
                     'rotation': _kf([(0.0, [0, 0, 0]), (0.62, [-30, 0, 0]), (0.80, [-30, 0, 0]),
                                      (1.30, [-6, 0, 0]), (1.60, [0, 0, 0])])},
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.55, [7, 0, 0]), (1.15, [5.5, 0, -6]),
                                  (1.68, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.55, [0, -1.2, 0]), (1.30, [0, -1.0, 0]),
                                   (1.68, [0, 0, 0])])},
        'bolt': {'position': _kfv([(0.0, [0, 0, 0]), (1.58, [0, 0, 0]), (1.86, [0, 0, 3.4]),
                                   (2.02, [0, 0, 0])])},
        'camera': {'rotation': _kf([(0.0, [0, 0, 0]), (0.62, [2.0, 0, -6]), (1.20, [1.6, 0, -7]),
                                    (1.72, [0, 0, 0])])},
    }}
    # 拨保险（0 = 连发位，负角抬到保险位再放下）
    safety = {'loop': False, 'animation_length': 0.55, 'bones': {
        'selector': {'rotation': _kf([(0.0, [0, 0, 0]), (0.16, [-46, 0, 0]), (0.30, [-38, 0, 0]),
                                      (0.44, [-44, 0, 0]), (0.55, [0, 0, 0])])},
        'camera': {'rotation': _kf([(0.0, [0, 0, 0]), (0.16, [0.4, -0.6, 0]), (0.55, [0, 0, 0])])},
    }}
    anims = {'format_version': '1.8.0', 'animations': {
        P + 'idle': idle, P + 'run': run, P + 'run_fast': run_fast, P + 'fire': fire,
        P + 'bolt_pull': bolt, P + 'reload': reload_, P + 'safety': safety}}
    os.makedirs(os.path.dirname(ANIM_OUT), exist_ok=True)
    with open(ANIM_OUT, 'w', encoding='utf-8') as fh:
        json.dump(anims, fh, ensure_ascii=False, indent=1)
    print('动画 -> %s（idle/run/run_fast[loop]、fire/bolt/reload/safety[play_once]）' % ANIM_OUT)


def write_bbmodel(out_bones, cubes, tex_size):
    elements, groups = [], []
    pivots = dict((b['name'], b['pivot']) for b in out_bones)
    for name, parent, _piv in BONES:
        cs = cubes.get(name) or []
        ids = []
        for i, c in enumerate(cs):
            uid = _uuid('%s_%d' % (name, i))
            ids.append(uid)
            el = {'name': '%s_%d' % (name, i), 'type': 'cube', 'uuid': uid,
                  'origin': c['origin'], 'size': c['size'], 'inflate': 0,
                  'uv': c['uv'], 'visibility': True, 'export': True, 'locked': False}
            if c.get('rotation'):
                el['rotation'] = c['rotation']
                el['pivot'] = c['pivot']
            elements.append(el)
        groups.append({'name': name, 'uuid': _uuid(name), 'origin': pivots[name],
                       'rotation': [0, 0, 0], 'children': ids, 'visibility': True,
                       'autouv': 0, 'color': 0, 'export': True, 'locked': False,
                       'isOpen': False, 'parent': parent or 'root'})
    with open(TEX_OUT, 'rb') as fh:
        durl = 'data:image/png;base64,' + base64.b64encode(fh.read()).decode()
    bb = {'meta': {'format_version': '4.5', 'model_format': 'geckolib_model', 'box_uv': False},
          'name': 'akm_geo', 'resolution': {'width': tex_size, 'height': tex_size},
          'elements': elements, 'outliner': [g['uuid'] for g in groups], 'groups': groups,
          'textures': [{'path': '', 'name': 'akm_geo.png', 'folder': 'block', 'namespace': '',
                        'id': '0', 'particle': False, 'render_mode': 'default',
                        'visible': True, 'mode': 'bitmap', 'saved': True,
                        'uuid': _uuid('tex'), 'source': durl}],
          'animations': [], 'animation_controllers': []}
    with open(BB_OUT, 'w', encoding='utf-8') as fh:
        json.dump(bb, fh, ensure_ascii=False)
    print('工程 -> %s（%d 元素 / %.2f MB）'
          % (BB_OUT, len(elements), os.path.getsize(BB_OUT) / 1048576))


def _uuid(s):
    h = hashlib.md5(s.encode('utf-8')).hexdigest()
    return '%s-%s-%s-%s-%s' % (h[:8], h[8:12], h[12:16], h[16:20], h[20:32])


if __name__ == '__main__':
    sys.exit(build(sys.argv))
