#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AKM（GeckoLib 真骨骼版）一体生成器。

产出：
  src/main/resources/assets/hexalunar_calamity/geo/akm.geo.json           骨骼模型
  src/main/resources/assets/hexalunar_calamity/textures/models/akm_geo.png 512x512 贴图
  src/main/resources/assets/hexalunar_calamity/animations/akm.animation.json 换弹/拉栓/待机
  模型/akm_geckolib.bbmodel                                               Blockbench 工程

坐标约定（与 mod 一致）：枪口朝 -Z（北），Y 向上，X 向右（AK 拉机柄在 +X）。
16 单位 = 1 方块；弹匣朝前下方弯，握把后倾。

用法: python tools/akm_gen.py [--no-bbmodel] [--preview]
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

TEX_W = TEX_H = 512
DENSITY = 22.0                      # 每单位多少像素（自动选择时作为兜底）
GEO_OUT = 'src/main/resources/assets/hexalunar_calamity/geo/akm.geo.json'
TEX_OUT = 'src/main/resources/assets/hexalunar_calamity/textures/models/akm_geo.png'
ANIM_OUT = 'src/main/resources/assets/hexalunar_calamity/animations/akm.animation.json'
BB_OUT = '模型/akm_geckolib.bbmodel'

# ------------------------------------------------------------------ 材质配色
MATS = {
    'receiver': dict(base=(132, 134, 138), hi=(186, 190, 194), lo=(74, 76, 82), kind='metal'),
    'dust':     dict(base=(144, 146, 150), hi=(198, 202, 206), lo=(82, 84, 90), kind='metal'),
    'steel':    dict(base=(104, 106, 112), hi=(160, 164, 172), lo=(52, 54, 60), kind='steel'),
    'blued':    dict(base=(84, 86, 92), hi=(130, 134, 142), lo=(40, 42, 48), kind='steel'),
    'wood':     dict(base=(208, 118, 44), hi=(242, 158, 78), lo=(140, 68, 20), kind='wood'),
    'wood_dark': dict(base=(124, 68, 30), hi=(164, 96, 48), lo=(74, 36, 14), kind='wood'),
    'poly':     dict(base=(72, 74, 80), hi=(108, 111, 118), lo=(36, 38, 44), kind='polymer',
                     border=0.0),
    'dark':     dict(base=(46, 47, 52), hi=(80, 82, 90), lo=(22, 23, 28), kind='metal'),
    'brass':    dict(base=(178, 142, 70), hi=(224, 190, 110), lo=(112, 86, 38), kind='metal'),
}

WIDEN = 1.34            # 厚度加宽系数（参考模型更剔透饱满，太薄会显得像纸片）

FACES = ['north', 'east', 'south', 'west', 'up', 'down']


def mag_cubes(n=5, start=(0.0, 1.50, -1.45), tilt0=5.0, tilt1=41.0,
              length=4.55, w=1.02, d=2.02, mat='poly'):
    """沿圆弧摆放弹匣：返回 [(名, origin, size, 材质, rot, pivot), ...]。"""
    tilt = [tilt0 + (tilt1 - tilt0) * i / (n - 1) for i in range(n)]
    seg = length / n
    p = list(start)
    out = []
    for i in range(n):
        a = math.radians((tilt[i] + (tilt[i - 1] if i else tilt[0])) / 2.0)
        c = tuple(p)                              # 该段的顶面中心
        dirv = (0.0, -math.cos(a), -math.sin(a))  # 向下 + 向前
        h = seg * 1.16
        center = (c[0], c[1] + dirv[1] * h / 2, c[2] + dirv[2] * h / 2)
        origin = (center[0] - w / 2, center[1] - h / 2, center[2] - d / 2)
        name = ['mag_top', 'mag_2', 'mag_3', 'mag_4', 'mag_low'][i] if n == 5 else 'mag_%d' % i
        out.append((name, origin, (w, h, d), mat, (tilt[i], 0, 0), center))
        p = [c[k] + dirv[k] * h for k in range(3)]
    base = p
    floor_origin = (base[0] - (w + 0.08) / 2, base[1] - 0.30, base[2] - (d + 0.06) / 2)
    out.append(('mag_floor', floor_origin, (w + 0.08, 0.32, d + 0.06), 'dark',
                (tilt1, 0, 0), (base[0], base[1], base[2])))
    return out

# ------------------------------------------------------------------ 骨骼与方块
# (骨骼名, 父骨骼, pivot, [(名字, origin, size, 材质, rot, pivot, inflate)])
BONES = [
    ('root', None, (0, 0, 0), []),
    ('body', 'root', (0, 3.0, 0), [
        # 机匣（冲压件）
        ('receiver', (-0.62, 2.55, -3.05), (1.24, 1.05, 5.45), 'receiver'),
        ('receiver_top', (-0.60, 3.34, -3.00), (1.20, 0.26, 5.35), 'receiver'),
        ('receiver_rear', (-0.66, 2.60, 2.30), (1.32, 1.30, 0.55), 'receiver'),
        ('trigger_housing', (-0.55, 2.15, 0.55), (1.10, 0.45, 2.10), 'receiver'),
        ('rivet_l', (-0.70, 2.85, -2.20), (0.10, 0.22, 0.22), 'blued'),
        ('rivet_r', (0.60, 2.85, -2.20), (0.10, 0.22, 0.22), 'blued'),
    ]),
    ('dust_cover', 'body', (0, 3.55, -0.2), [
        ('dust_main', (-0.58, 3.40, -2.85), (1.16, 0.32, 5.30), 'dust'),
        ('dust_ridge', (-0.44, 3.72, -2.70), (0.88, 0.14, 4.60), 'dust'),
        ('dust_rear_cap', (-0.54, 3.38, 2.35), (1.08, 0.36, 0.30), 'dust'),
    ]),
    ('rear_sight', 'body', (0, 3.8, -2.3), [
        ('rs_base', (-0.46, 3.74, -2.62), (0.92, 0.14, 0.95), 'blued'),
        ('rs_tangent', (-0.40, 3.86, -2.05), (0.80, 0.12, 0.75), 'blued'),
        ('rs_notch', (-0.28, 3.94, -2.55), (0.56, 0.12, 0.22), 'blued'),
    ]),
    ('bolt', 'body', (0.9, 3.05, 0.4), [
        ('bolt_carrier', (-0.30, 3.05, -2.70), (0.60, 0.40, 3.70), 'steel'),
        ('bolt_lug', (-0.24, 3.07, -2.95), (0.48, 0.34, 0.45), 'steel'),
        ('bolt_handle_arm', (0.30, 3.10, -1.05), (0.52, 0.26, 0.62), 'steel'),
        ('bolt_knob', (0.72, 3.05, -1.12), (0.34, 0.34, 0.76), 'steel'),
    ]),
    ('handguard', 'body', (0, 3.0, -4.6), [
        ('hg_lower', (-0.68, 2.58, -6.15), (1.36, 0.78, 3.35), 'wood'),
        ('hg_upper', (-0.58, 3.30, -6.05), (1.16, 0.38, 2.95), 'wood'),
        ('hg_ferrule', (-0.64, 2.52, -6.30), (1.28, 0.88, 0.36), 'blued'),
        ('hg_slat1', (-0.72, 2.72, -5.90), (1.44, 0.16, 0.30), 'wood_dark'),
        ('hg_slat2', (-0.72, 3.02, -5.90), (1.44, 0.16, 0.30), 'wood_dark'),
        ('gas_tube', (-0.40, 3.34, -6.20), (0.80, 0.40, 3.20), 'blued'),
    ]),
    ('barrel', 'body', (0, 3.0, -7.6), [
        ('barrel_main', (-0.30, 2.70, -8.05), (0.60, 0.60, 2.35), 'blued'),
        ('gas_block', (-0.40, 2.68, -6.60), (0.80, 0.78, 0.68), 'blued', (35, 0, 0), (0, 3.05, -6.6)),
        ('front_sight_base', (-0.38, 2.72, -7.85), (0.76, 0.70, 0.60), 'blued'),
        ('front_sight_post', (-0.13, 3.30, -7.80), (0.26, 0.48, 0.34), 'steel'),
        ('sight_hood_l', (-0.46, 3.20, -8.12), (0.20, 0.66, 0.66), 'blued'),
        ('sight_hood_r', (0.26, 3.20, -8.12), (0.20, 0.66, 0.66), 'blued'),
        ('sight_hood_top', (-0.46, 3.76, -8.12), (0.92, 0.16, 0.66), 'blued'),
        ('muzzle_brake', (-0.36, 2.64, -8.78), (0.72, 0.72, 0.74), 'steel'),
    ]),
    ('magazine', 'body', (0, 2.55, -1.3), mag_cubes(start=(0.0, 2.55, -1.45), length=2.45,
                                                    tilt1=37.0, w=1.02, d=2.02)),
    ('trigger', 'body', (0, 2.4, 1.6), [
        ('trigger_guard', (-0.28, 2.03, 1.10), (0.56, 0.13, 1.55), 'blued'),
        ('trigger_guard_front', (-0.28, 2.15, 0.95), (0.56, 0.38, 0.16), 'blued'),
        ('trigger_blade', (-0.13, 2.15, 1.55), (0.26, 0.52, 0.30), 'steel', (8, 0, 0), (0, 2.45, 1.70)),
        ('mag_release', (-0.16, 2.28, 0.95), (0.32, 0.44, 0.30), 'steel'),
        ('disconnector', (-0.10, 2.42, 1.90), (0.20, 0.22, 0.55), 'steel'),
    ]),
    ('grip', 'body', (0, 2.35, 2.9), [
        ('grip_main', (-0.58, 1.25, 2.45), (1.16, 1.35, 1.12), 'wood_dark', (12, 0, 0), (0, 2.35, 3.00)),
        ('grip_cap', (-0.62, 1.02, 2.35), (1.24, 0.22, 1.28), 'dark', (12, 0, 0), (0, 2.35, 3.00)),
        ('grip_screw', (0.56, 2.10, 2.95), (0.12, 0.22, 0.22), 'blued'),
    ]),
    ('stock', 'body', (0, 2.8, 5.0), [
        ('stock_main', (-0.60, 2.70, 3.25), (1.20, 1.00, 4.35), 'wood'),
        ('stock_comb', (-0.56, 3.52, 3.35), (1.12, 0.34, 2.85), 'wood'),
        ('stock_neck', (-0.62, 2.75, 2.55), (1.24, 1.18, 0.80), 'wood'),
        ('butt_plate', (-0.64, 2.62, 7.55), (1.28, 1.35, 0.45), 'dark'),
        ('sling_swivel', (-0.44, 2.28, 5.75), (0.88, 0.22, 0.45), 'blued'),
        ('stock_rib', (-0.62, 3.18, 4.60), (1.24, 0.12, 2.30), 'wood_dark'),
    ]),
    ('selector', 'body', (0.62, 2.6, 1.1), [
        ('sel_shaft', (0.60, 2.55, 0.95), (0.20, 0.80, 0.24), 'blued'),
        ('sel_lever', (0.80, 2.95, 0.20), (0.16, 1.10, 0.22), 'blued'),
        ('sel_detent', (0.70, 2.42, 0.85), (0.26, 0.22, 0.34), 'steel'),
    ]),
]


# ------------------------------------------------------------------ UV 打包（逐面 UV，像素矩形）
def face_size_units(face, size):
    sx, sy, sz = size
    return {'north': (sx, sy), 'south': (sx, sy), 'east': (sz, sy),
            'west': (sz, sy), 'up': (sx, sz), 'down': (sx, sz)}[face]


def pack_faces(bones, density=None):
    """给每个面分配像素矩形（货架打包 + 密度自动回退），返回 ({(bone,cube,face): rect}, density)。"""
    items = []
    for bname, _p, _piv, cubes in bones:
        for c in cubes:
            for f in FACES:
                fw, fh = face_size_units(f, c[2])
                items.append((bname, c[0], f, fw, fh))
    area = sum(fw * fh for _b, _c, _f, fw, fh in items)
    if density is None:
        density = min(24.0, max(6.0, (0.55 * TEX_W * TEX_H / max(area, 1e-6)) ** 0.5))

    def try_pack(dn):
        items2 = sorted(items, key=lambda it: -(it[4] * dn))
        x = y = row_h = 0
        out = {}
        for bname, cname, f, fw, fh in items2:
            w = max(4, int(round(fw * dn)))
            h = max(4, int(round(fh * dn)))
            if x + w + 2 > TEX_W:
                x, y, row_h = 0, y + row_h + 2, 0
            if y + h + 2 > TEX_H:
                return None
            out[(bname, cname, f)] = (x, y, w, h)
            x += w + 2
            row_h = max(row_h, h)
        return out

    while density > 4.0:
        res = try_pack(density)
        if res:
            return res, density
        density *= 0.92
    raise SystemExit('贴图放不下')


# ------------------------------------------------------------------ 画贴图
def paint_rect(img, rect, mat, face, seed, diag=False):
    x, y, w, h = rect
    m = MATS[mat]
    px = img.load()
    import random
    rnd = random.Random(seed)
    base = m['base']
    for j in range(h):
        # 顶亮底暗的竖向渐变
        t = j / max(h - 1, 1)
        f = 1.0 + 0.16 * (1 - 2 * t)
        for i in range(w):
            n = rnd.uniform(-8, 8)
            c = tuple(max(0, min(255, int(base[k] * f + n))) for k in range(3))
            px[x + i, y + j] = c
    d = ImageDraw.Draw(img)
    if diag:
        d = ImageDraw.Draw(img)
        d.rectangle([x, y, x + w - 1, y + max(2, h // 8)], fill=(220, 40, 40))
        s = max(3, min(w, h) // 4)
        d.rectangle([x, y, x + s - 1, y + s - 1], fill=(40, 220, 60))
        return
    # 面内 AO：上下压深、左右收窄，再加上高光边——块状模型靠这个才立体
    bd = max(1, int(min(w, h) * 0.11))
    if m.get('border', 1.0) <= 0.0:
        bd = 0
    for j in range(bd):
        f = 1.0 - 0.26 * (1 - j / bd)
        for i in range(w):
            c = px[x + i, y + j]
            px[x + i, y + j] = tuple(int(v * f) for v in c)
            c2 = px[x + i, y + h - 1 - j]
            px[x + i, y + h - 1 - j] = tuple(int(v * (f * 0.94)) for v in c2)
    for i in range(bd):
        f = 1.0 - 0.19 * (1 - i / bd)
        for j in range(h):
            c = px[x + i, y + j]
            px[x + i, y + j] = tuple(int(v * f) for v in c)
            c2 = px[x + w - 1 - i, y + j]
            px[x + w - 1 - i, y + j] = tuple(int(v * (f * 0.92)) for v in c2)
    d.line([(x + bd, y + 1), (x + w - bd - 1, y + 1)],
           fill=tuple(min(255, int(v * 1.34)) for v in m['hi']), width=1)
    d.line([(x + 2, y + bd), (x + 2, y + h - bd)],
           fill=tuple(min(255, int(v * 1.20)) for v in m['hi']), width=1)
    if m['kind'] == 'wood':
        for k in range(h // 5 + 1):
            yy = y + 2 + k * 5 + rnd.randint(-1, 1)
            col = tuple(int(v * 0.82) for v in m['lo'])
            d.line([(x + 1, yy), (x + w - 2, yy + rnd.randint(-1, 1))], fill=col, width=1)
        for k in range(w // 14 + 1):
            xx = x + 4 + k * 14 + rnd.randint(-2, 2)
            d.line([(xx, y + 1), (xx + rnd.randint(-1, 1), y + h - 2)],
                   fill=tuple(int(v * 0.88) for v in m['lo']), width=1)
    elif m['kind'] == 'metal':
        for k in range(max(2, w * h // 900)):
            sx = x + rnd.randrange(max(1, w))
            sy = y + rnd.randrange(max(1, h))
            ln = rnd.randint(2, 7)
            col = tuple(min(255, int(v * 1.18)) for v in m['hi'])
            d.line([(sx, sy), (sx + ln, sy + (1 if rnd.random() < 0.5 else 0))], fill=col, width=1)
        for k in range(max(2, w * h // 1600)):
            sx = x + rnd.randrange(max(1, w))
            sy = y + rnd.randrange(max(1, h))
            d.rectangle([sx, sy, sx + 1, sy + 1], fill=tuple(int(v * 0.7) for v in m['lo']))
    elif m['kind'] == 'polymer':
        step = 4
        for k in range(1, h // step):
            yy = y + k * step
            d.line([(x, yy), (x + w, yy)], fill=tuple(int(v * 0.86) for v in m['lo']), width=1)
    elif m['kind'] == 'steel':
        for k in range(h):
            t = k / max(h - 1, 1)
            col = tuple(int(m['lo'][c] + (m['hi'][c] - m['lo'][c]) * (1 - abs(2 * t - 1))) for c in range(3))
            d.line([(x, y + k), (x + w, y + k)], fill=col, width=1)
    # 边缘倒角：外圈压暗，内圈提亮
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=tuple(int(v * 0.62) for v in m['lo']))
    d.line([(x + 1, y + 1), (x + w - 2, y + 1)], fill=tuple(min(255, int(v * 1.22)) for v in m['hi']))
    d.line([(x + 1, y + 1), (x + 1, y + h - 2)], fill=tuple(min(255, int(v * 1.12)) for v in m['hi']))


def build_texture(bones, uv, diag=False):
    img = Image.new('RGB', (TEX_W, TEX_H), (26, 27, 30))
    seed = 1
    for bname, _p, _piv, cubes in bones:
        for c in cubes:
            mat = c[3]
            for f in FACES:
                r = uv.get((bname, c[0], f))
                if r:
                    paint_rect(img, r, mat, f, seed, diag=diag)
                    seed += 7
    if not diag:
        img = img.filter(ImageFilter.SMOOTH)
    return img


# ------------------------------------------------------------------ geo
def build_geo(bones, uv):
    out_bones = []
    for bname, parent, piv, cubes in bones:
        b = {'name': bname, 'pivot': list(piv)}
        if parent:
            b['parent'] = parent
        if cubes:
            cs = []
            for c in cubes:
                name, origin, size = c[0], c[1], c[2]
                fuv = {}
                for f in FACES:
                    x, y, w, h = uv[(bname, name, f)]
                    fuv[f] = {'uv': [x, y], 'uv_size': [w, h]}
                cu = {'origin': list(origin), 'size': list(size), 'uv': fuv}
                if len(c) > 4 and c[4]:
                    cu['rotation'] = list(c[4])
                if len(c) > 5 and c[5]:
                    cu['pivot'] = list(c[5])
                if len(c) > 6 and c[6]:
                    cu['inflate'] = c[6]
                cs.append(cu)
            b['cubes'] = cs
        out_bones.append(b)
    return {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.akm',
                'texture_width': TEX_W, 'texture_height': TEX_H,
                'visible_bounds_width': 3, 'visible_bounds_height': 3,
                'visible_bounds_offset': [0, 1.2, 0],
            },
            'bones': out_bones,
        }],
    }


# ------------------------------------------------------------------ 动画
def build_anims():
    """换弹 / 拉栓 / 待机。时间单位=秒；位移单位=单位（1/16 方块）。"""
    def bone(name, keys):
        out = {}
        for k, v in keys.items():
            if isinstance(v, list) and len(v) == 1 and isinstance(v[0], list):
                v = v[0]
            out[k] = {('vector' if k in ('position', 'scale') else 'post'): list(v)}
        return {name: out}

    anims = {}

    # ---- 拉栓：机柄后拉到底再推回（0.55s）
    pull = {}
    pull.update(bone('bolt', {
        '0.0': [[0, 0, 0]],
        '0.08': [[0, 0.1, 1.35]],
        '0.30': [[0, 0.1, 1.62]],
        '0.40': [[0, 0.1, 1.62]],
        '0.52': [[0, 0, 0.0]],
    }))
    pull.update(bone('trigger', {'0.0': [[0, 0, 0]], '0.30': [[0, 0, 0]]}))
    anims['bolt_pull'] = {'loop': False, 'animation_length': 0.55, 'bones': pull}

    # ---- 换弹：空仓挂机 → 退匣 → 新匣上膛 → 释放枪机
    rel = {}
    for b, keys in (
        ('bolt', {'0.00': [[0, 0, 0]], '0.30': [[0, 0.1, 1.62]], '0.95': [[0, 0.1, 1.62]],
                  '1.02': [[0, 0.02, 0.25]], '1.12': [[0, 0, 0]]}),
        ('magazine', {'0.00': [[0, 0, 0]], '0.08': [[0, -0.12, 0.05]],
                      '0.22': [[0, -0.9, 0.15]], '0.34': [[0, -3.4, 0.6]],
                      '0.52': [[0, -3.4, 0.6]], '0.66': [[0, -1.3, 0.25]],
                      '0.78': [[0, 0.10, 0]], '0.84': [[0, 0, 0]]}),
        ('body', {'0.00': [[0, 0, 0]], '0.30': [[0, -0.12, 0.08]], '0.68': [[0, -0.14, 0.1]],
                  '0.90': [[0, 0, 0]], '1.12': [[0, 0, 0]]}),
        ('selector', {'0.00': [[0, 0, 0]], '0.30': [[0, 0, 0]]}),
    ):
        rel.update(bone(b, keys))
    anims['reload'] = {'loop': False, 'animation_length': 1.2, 'bones': rel}

    # ---- 待机：轻微晃动
    idle = {}
    idle.update(bone('body', {'0.0': [[0, 0, 0]], '1.0': [[0, -0.03, 0]], '2.0': [[0, 0, 0]],
                              '3.0': [[0, 0.03, 0.02]], '4.0': [[0, 0, 0]]}))
    idle.update(bone('trigger', {'0.0': [[0, 0, 0]], '4.0': [[0, 0, 0]]}))
    anims['idle'] = {'loop': True, 'animation_length': 4.0, 'bones': idle}
    return {'format_version': '1.8.0', 'animations': anims}


# ------------------------------------------------------------------ bbmodel
# 每个面的 4 个角在「从外面看」的 左上/右上/右下/左下 顺序（UV 用）
def face_corners_2d(face, x0, y0, z0, x1, y1, z1):
    return {
        'north': [(x1, y1), (x0, y1), (x0, y0), (x1, y0)],
        'south': [(x0, y1), (x1, y1), (x1, y0), (x0, y0)],
        'east':  [(z1, y1), (z0, y1), (z0, y0), (z1, y0)],
        'west':  [(z0, y1), (z1, y1), (z1, y0), (z0, y0)],
        'up':    [(x0, z0), (x1, z0), (x1, z1), (x0, z1)],
        'down':  [(x0, z1), (x1, z1), (x1, z0), (x0, z0)],
    }[face]


def build_bbmodel(bones, uv, tex_path):
    import base64 as b64
    elements = []
    groups = []
    for bname, parent, piv, cubes in bones:
        el_ids = []
        for c in cubes:
            name, origin, size = c[0], c[1], c[2]
            x0, y0, z0 = origin
            x1, y1, z1 = x0 + size[0], y0 + size[1], z0 + size[2]
            faces = {}
            for f in FACES:
                u, v, w, h = uv[(bname, name, f)]
                corners = face_corners_2d(f, x0, y0, z0, x1, y1, z1)
                pts = []
                for (a, b) in corners:
                    if f in ('north', 'south'):
                        fx = (a - x0) / max(x1 - x0, 1e-6)
                        fy = (y1 - b) / max(y1 - y0, 1e-6)
                    elif f in ('east', 'west'):
                        fx = (a - z0) / max(z1 - z0, 1e-6)
                        fy = (y1 - b) / max(y1 - y0, 1e-6)
                    else:
                        fx = (a - x0) / max(x1 - x0, 1e-6)
                        fy = (b - z0) / max(z1 - z0, 1e-6)
                    pts.append([round(u + fx * w, 2), round(v + fy * h, 2)])
                faces[f] = {'uv': pts, 'texture': 0}
            el = {
                'name': name, 'box_uv': False, 'type': 'cube', 'uuid': _uuid(bname + c[0]),
                'origin': [round(origin[i] + 8, 4) for i in range(3)],
                'size': [round(x, 4) for x in size],
                'rotation': [0, 0, 0], 'color': 0, 'faces': faces,
                'visibility': True, 'export': True, 'locked': False,
                'shade': True, 'inflate': 0, 'nbt': {},
            }
            if len(c) > 4 and c[4]:
                el['rotation'] = [c[4][0], c[4][1], c[4][2]]
            if len(c) > 5 and c[5]:
                el['pivot'] = [round(c[5][i] + 8, 4) for i in range(3)]
            elements.append(el)
            el_ids.append(el['uuid'])
        groups.append({'name': bname, 'uuid': _uuid('g' + bname),
                       'origin': [round(piv[i] + 8, 4) for i in range(3)],
                       'rotation': [0, 0, 0], 'children': el_ids, 'visibility': True,
                       'autouv': 0, 'color': 0, 'export': True, 'locked': False,
                       'mirror_uv': False, 'isOpen': False, 'shade': True, 'nbt': {},
                       'parent': parent or 'root'})
    with open(tex_path, 'rb') as fh:
        data_url = 'data:image/png;base64,' + b64.b64encode(fh.read()).decode()
    return {
        'meta': {'format_version': '4.5', 'model_format': 'geckolib_model',
                 'box_uv': False},
        'name': 'akm_geckolib',
        'resolution': {'width': TEX_W, 'height': TEX_H},
        'elements': elements,
        'outliner': [g['uuid'] for g in groups],
        'groups': groups,
        'textures': [{'path': '', 'name': 'akm_geo.png', 'folder': 'block',
                      'namespace': '', 'id': '0', 'particle': False,
                      'render_mode': 'default', 'visible': True, 'mode': 'bitmap',
                      'saved': True, 'uuid': _uuid('tex0'), 'source': data_url}],
        'animations': [],
        'animation_controllers': [],
    }


def _uuid(s):
    import hashlib
    h = hashlib.md5(s.encode('utf-8')).hexdigest()
    return '%s-%s-%s-%s-%s' % (h[:8], h[8:12], h[12:16], h[16:20], h[20:32])


# ------------------------------------------------------------------ main
def widen(bones, k):
    """把宽度（X 轴）整体放大，让模型更饱满（所有 cube 的旋转都是绕 X，故不影响）。"""
    out = []
    for bname, parent, piv, cubes in bones:
        nc = []
        for c in cubes:
            name, origin, size = c[0], c[1], c[2]
            o = (origin[0] * k, origin[1], origin[2])
            s = (size[0] * k, size[1], size[2])
            rest = list(c[4:])
            if rest and rest[0]:
                rest[0] = (rest[0][0], rest[0][1], rest[0][2])
            if len(rest) > 1 and rest[1]:
                rest[1] = (rest[1][0] * k, rest[1][1], rest[1][2])
            nc.append(tuple([name, o, s, c[3]] + rest))
        out.append((bname, parent, (piv[0] * k, piv[1], piv[2]), nc))
    return out


def main(argv):
    bones = widen(BONES, WIDEN)
    diag = '--diag' in argv
    uv, density = pack_faces(bones)
    os.makedirs(os.path.dirname(TEX_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(ANIM_OUT), exist_ok=True)
    img = build_texture(bones, uv, diag=diag)
    img.save(TEX_OUT)
    print('贴图 -> %s  (%dx%d, %d 个面, 密度 %.1f 像素/单位%s)'
          % (TEX_OUT, TEX_W, TEX_H, len(uv), density, '，诊断模式' if diag else ''))
    geo = build_geo(bones, uv)
    with open(GEO_OUT, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, indent=1)
    ncube = sum(len(b[3]) for b in bones)
    print('模型 -> %s  (%d 骨骼, %d 方块)' % (GEO_OUT, len(bones), ncube))
    anim = build_anims()
    with open(ANIM_OUT, 'w', encoding='utf-8') as fh:
        json.dump(anim, fh, ensure_ascii=False, indent=1)
    print('动画 -> %s  (%s)' % (ANIM_OUT, ', '.join(anim['animations'])))
    if '--no-bbmodel' not in argv:
        bb = build_bbmodel(bones, uv, TEX_OUT)
        with open(BB_OUT, 'w', encoding='utf-8') as fh:
            json.dump(bb, fh, ensure_ascii=False)
        print('工程 -> %s  (%.1f MB)' % (BB_OUT, os.path.getsize(BB_OUT) / 1048576))
    if '--preview' in argv:
        os.system('python tools/geo_view.py "%s" "%s" build/akm_side.png --yaw -90 --pitch 0 --size 900 --zoom 1.02'
                  % (GEO_OUT, TEX_OUT))
        os.system('python tools/geo_view.py "%s" "%s" build/akm_iso.png --yaw -40 --pitch 18 --size 900 --zoom 1.02'
                  % (GEO_OUT, TEX_OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
