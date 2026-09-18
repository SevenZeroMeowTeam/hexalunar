#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""十字弩（crossbow / 参考 模型/十字弩.bbmodel）重建 GeckoLib 真骨骼方块模型。

参考网格是薄壳 mesh（4649 面，x ±6.54 / y 0~4.65 / z ±7.84），按实测比例手工重建：
  机匣导轨（长条）、枪托+托底、握把+扳机、顶部瞄准镜、左右弓臂（伸向 ±x）、
  弓弦两段（从弓臂梢到弦心）+ 弦心、弩箭（沿导轨，未装填时隐藏）、脚踏。

朝向：弩箭飞出方向 = **-Z（北）**（参考是 +z 朝前，所以整体 Ry180°）。
原点：握把上方（手持位置对）。
拉弦：与复合弓同一套算法 —— 弦长取拉满所需 L，绕弓臂梢转 φ，两端正好在弦心重合；
      拉弦与装弹由 GeoModel 按 CrossbowWeaponItem.reloadProgress 程序化驱动（连续、跟手）。

动画（BOCEK 规范）：animation.crossbow.idle / run / run_fast[loop]、fire[play_once]。

产出：geo/crossbow_geo.geo.json、textures/models/crossbow_geo.png、
      animations/crossbow.animation.json、模型/十字弩_geo.bbmodel

用法: python tools/crossbow_gen.py [--tex 512] [--no-bbmodel]
"""
import base64
import io
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
from akm_voxel_gen import load_ref, rotate_tris

REF = '模型/十字弩.bbmodel'
GEO_OUT = 'src/main/resources/assets/hexalunar_calamity/geo/crossbow_geo.geo.json'
TEX_OUT = 'src/main/resources/assets/hexalunar_calamity/textures/models/crossbow_geo.png'
ANIM_OUT = 'src/main/resources/assets/hexalunar_calamity/animations/crossbow.animation.json'
BB_OUT = '模型/十字弩_geo.bbmodel'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')

SCALE = 1.0
STRING_Y = 2.60
TIP_X, TIP_Z = 6.00, -2.20      # 弓臂梢（左右对称）
DRAW_DZ = 2.60                  # 拉满时弦心后退距离
SEG_LEN = math.sqrt(TIP_X ** 2 + DRAW_DZ ** 2)
PHI = math.degrees(math.atan2(DRAW_DZ, TIP_X))
GRIP = (0.0, 2.60, 3.60)        # 原点（握把上方）

# 骨骼：(名字, 父, pivot)
BONES = [
    ('root', None, (0.0, 0.0, 0.0)),
    ('move', 'root', GRIP),
    ('body', 'move', GRIP),
    ('stock', 'body', (0.0, 1.60, 5.20)),
    ('grip', 'body', (0.0, 2.20, 4.00)),
    ('scope', 'body', (0.0, 4.40, 1.60)),
    ('prod_left', 'body', (-1.20, STRING_Y, -1.40)),
    ('prod_right', 'body', (1.20, STRING_Y, -1.40)),
    ('string_left', 'body', (-TIP_X, STRING_Y, TIP_Z)),
    ('string_right', 'body', (TIP_X, STRING_Y, TIP_Z)),
    ('nock', 'body', (0.0, STRING_Y, TIP_Z)),
    ('bolt', 'body', (0.0, STRING_Y, TIP_Z)),
]

SAMPLES = {
    'rail': (-1.5, 1.5, 2.0, 3.4, -3.0, 3.0),
    'stock': (2.0, 5.0, 0.4, 3.0, -7.6, -3.0),
    'scope': (0.6, 2.8, 3.2, 4.6, -1.4, 3.4),
    'limb': (-6.5, -2.4, 2.0, 3.2, 1.9, 6.0),
    'string': (-3.0, 3.0, 2.4, 3.0, 5.3, 7.8),
    'bolt': (-0.6, 0.6, 2.2, 3.2, -2.0, 2.0),
    'dark': (-1.2, 1.2, 0.8, 2.4, 2.6, 5.4),
}
MATERIAL = {'rail': (46, 48, 50), 'stock': (52, 52, 50), 'scope': (38, 40, 42),
            'limb': (58, 58, 56), 'string': (176, 178, 180), 'bolt': (150, 142, 126),
            'dark': (34, 36, 36)}


def shade(patch, base):
    px = list(patch.getdata())
    lums = sorted(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2] for c in px)
    mid = lums[len(lums) // 2] or 1.0
    out = Image.new('RGB', patch.size)
    out.putdata([tuple(max(0, min(255, int(v * max(0.70, min(1.30,
                    0.50 + 0.55 * ((0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / mid))))))
                 for v in base) for c in px])
    return out


def sample_patches(tris, tex, uv_w, uv_h, size=48):
    cw, ch = tex.size
    out = {}
    for mat, (x0, x1, y0, y1, z0, z1) in SAMPLES.items():
        pts = []
        for t in tris:
            cx = sum(p[0] for p in t[:3]) / 3.0
            cy = sum(p[1] for p in t[:3]) / 3.0
            cz = sum(p[2] for p in t[:3]) / 3.0
            if not (x0 <= cx <= x1 and y0 <= cy <= y1 and z0 <= cz <= z1):
                continue
            for k in range(3):
                u, v = t[3 + k]
                pts.append((u * cw / float(uv_w), v * ch / float(uv_h)))
        if not pts:
            out[mat] = shade(Image.new('RGB', (size, size), MATERIAL[mat]), MATERIAL[mat])
            continue
        mu = sorted(p[0] for p in pts)[len(pts) // 2]
        mv = sorted(p[1] for p in pts)[len(pts) // 2]
        h = size // 2
        box = (int(mu) - h, int(mv) - h, int(mu) + h, int(mv) + h)
        patch = Image.new('RGB', (size, size), MATERIAL[mat])
        clip = (max(box[0], 0), max(box[1], 0), min(box[2], cw), min(box[3], ch))
        if clip[2] > clip[0] and clip[3] > clip[1]:
            patch.paste(tex.crop(clip).convert('RGB'), (clip[0] - box[0], clip[1] - box[1]))
        out[mat] = shade(patch, MATERIAL[mat])
    return out


def build_texture(patches, tex_size):
    im = Image.new('RGB', (tex_size, tex_size), (24, 24, 26))
    slots = {}
    for i, mat in enumerate(sorted(SAMPLES)):
        ox, oy = (i % 8) * 64, (i // 8) * 64
        slots[mat] = (ox, oy)
        im.paste(patches[mat].resize((48, 48), Image.LANCZOS), (ox + 8, oy + 8))
        dr = ImageDraw.Draw(im)
        for x in range(64):
            for xx in (ox, ox + 63):
                dr.point((xx, oy + x), fill=(32, 34, 32))
        for y in range(64):
            for yy in (oy, oy + 63):
                dr.point((ox + y, yy), fill=(32, 34, 32))
    return im, slots


def build(argv):
    tex_size = 512
    if '--tex' in argv:
        tex_size = int(argv[argv.index('--tex') + 1])
    _v, tris, tex, uv_w, uv_h = load_ref(REF)
    tris = rotate_tris(tris, 180.0)          # 箭飞向 -Z（北）
    atlas, slots = build_texture(sample_patches(tris, tex, uv_w, uv_h), tex_size)
    os.makedirs(os.path.dirname(TEX_OUT), exist_ok=True)
    atlas.save(TEX_OUT)

    cubes = {b[0]: [] for b in BONES}

    def add(bone, x0, x1, y0, y1, z0, z1, mat):
        u, v = slots[mat]
        face = {'uv': [u + 9.0, v + 9.0], 'uv_size': [46.0, 46.0]}
        cubes[bone].append({
            'origin': [round((x0 - GRIP[0]) * SCALE, 3), round((y0 - GRIP[1]) * SCALE, 3),
                       round((z0 - GRIP[2]) * SCALE, 3)],
            'size': [round((x1 - x0) * SCALE, 3), round((y1 - y0) * SCALE, 3),
                     round((z1 - z0) * SCALE, 3)],
            'uv': {f: dict(face) for f in FACES},
        })

    # 机匣导轨 + 弩臂座
    add('body', -0.90, 0.90, 2.05, 3.15, -3.00, 5.40, 'rail')
    add('body', -1.35, 1.35, 2.10, 3.10, -3.20, -1.40, 'rail')
    # 枪托（含托底/贴腮）
    add('stock', -1.00, 1.00, 1.55, 3.00, 3.60, 6.60, 'stock')
    add('stock', -1.10, 1.10, 0.90, 3.20, 6.60, 7.80, 'stock')
    add('stock', -0.75, 0.75, 2.90, 3.55, 4.40, 6.40, 'stock')
    # 握把 + 扳机
    add('grip', -0.75, 0.75, 1.10, 2.30, 3.40, 4.60, 'dark')
    add('grip', -0.22, 0.22, 1.60, 2.35, 4.35, 4.75, 'dark')
    # 瞄准镜：主管 + 前后镜座
    add('scope', -0.55, 0.55, 3.55, 4.45, 0.00, 3.30, 'scope')
    add('scope', -0.72, 0.72, 3.42, 4.58, 0.30, 0.90, 'scope')
    add('scope', -0.68, 0.68, 3.45, 4.55, 2.60, 3.25, 'scope')
    add('scope', -0.30, 0.30, 3.15, 3.60, 0.60, 1.30, 'scope')
    add('scope', -0.30, 0.30, 3.15, 3.60, 2.20, 2.90, 'scope')
    # 左右弓臂：从弩臂座伸向 ±x，带一点前倾
    for sgn, bone in ((-1, 'prod_left'), (1, 'prod_right')):
        add(bone, min(sgn * 1.10, sgn * 2.60), max(sgn * 1.10, sgn * 2.60), 2.25, 2.95, -2.10, -1.10, 'limb')
        add(bone, min(sgn * 2.60, sgn * 4.30), max(sgn * 2.60, sgn * 4.30), 2.35, 2.90, -2.40, -1.20, 'limb')
        add(bone, min(sgn * 4.30, sgn * 5.40), max(sgn * 4.30, sgn * 5.40), 2.45, 2.85, -2.60, -1.40, 'limb')
        add(bone, min(sgn * 5.40, sgn * TIP_X), max(sgn * 5.40, sgn * TIP_X), 2.50, 2.80, -2.70, -1.70, 'limb')
    # 弦两段：沿 X 从弓臂梢横向伸到弦心，长度取拉满所需（未拉时在中点重叠，被弦心盖住）
    add('string_left', -TIP_X, -TIP_X + SEG_LEN, STRING_Y - 0.08, STRING_Y + 0.08,
        TIP_Z - 0.08, TIP_Z + 0.08, 'string')
    add('string_right', TIP_X - SEG_LEN, TIP_X, STRING_Y - 0.08, STRING_Y + 0.08,
        TIP_Z - 0.08, TIP_Z + 0.08, 'string')
    # 弦心（缠绳）+ 弩箭
    add('nock', -0.42, 0.42, STRING_Y - 0.85, STRING_Y + 0.85, TIP_Z - 0.30, TIP_Z + 0.30, 'string')
    add('bolt', -0.26, 0.26, STRING_Y - 0.22, STRING_Y + 0.22, -6.20, TIP_Z + 0.10, 'bolt')
    add('bolt', -0.40, 0.40, STRING_Y - 0.32, STRING_Y + 0.32, -7.00, -6.20, 'bolt')
    add('bolt', -0.52, -0.30, STRING_Y - 0.28, STRING_Y + 0.28, TIP_Z - 1.60, TIP_Z - 0.20, 'dark')
    add('bolt', 0.30, 0.52, STRING_Y - 0.28, STRING_Y + 0.28, TIP_Z - 1.60, TIP_Z - 0.20, 'dark')

    out_bones = []
    for name, parent, piv in BONES:
        b = {'name': name,
             'pivot': [round((piv[i] - GRIP[i]) * SCALE, 4) for i in range(3)]}
        if parent:
            b['parent'] = parent
        if cubes.get(name):
            b['cubes'] = cubes[name]
        out_bones.append(b)

    total = sum(len(cubes[b[0]]) for b in BONES)
    geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': 'geometry.crossbow_geo', 'texture_width': tex_size,
                        'texture_height': tex_size, 'visible_bounds_width': 2,
                        'visible_bounds_height': 2, 'visible_bounds_offset': [0, 0, 0]},
        'bones': out_bones}]}
    with open(GEO_OUT, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, indent=1)
    print('模型 -> %s（%d 骨骼 / %d 方块；弦长 %.2f φ=%.2f°）' % (
        GEO_OUT, len(out_bones), total, SEG_LEN, PHI))
    write_anims()
    if '--no-bbmodel' not in argv:
        write_bbmodel(out_bones, cubes, tex_size)
    return 0


def _kf(pairs):
    return dict((('%g' % t), {'post': [round(v, 3) for v in val]}) for t, val in pairs)


def _kfv(pairs):
    return dict((('%g' % t), {'vector': [round(v * SCALE, 3) for v in val]})
                for t, val in pairs)


def write_anims():
    P = 'animation.crossbow.'
    idle = {'loop': True, 'animation_length': 1.9, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.95, [0.4, 0, 0.3]), (1.9, [0, 0, 0])])},
        'bolt': {'position': _kfv([(0.0, [0, -40, 0])])},
    }}
    run = {'loop': True, 'animation_length': 0.8333, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.21, [2.4, 0, -0.9]), (0.42, [0, 0, 0]),
                                  (0.63, [-2.0, 0, 0.7]), (0.83, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.21, [0, -0.4, 0]), (0.42, [0, 0, 0]),
                                   (0.63, [0, 0.4, 0]), (0.83, [0, 0, 0])])},
        'bolt': {'position': _kfv([(0.0, [0, -40, 0])])},
    }}
    run_fast = {'loop': True, 'animation_length': 0.6, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.15, [3.8, 0, -1.5]), (0.30, [0, 0, 0]),
                                  (0.45, [-3.2, 0, 1.1]), (0.60, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.15, [0, -0.8, 0]), (0.30, [0, 0, 0]),
                                   (0.45, [0, 0.8, 0]), (0.60, [0, 0, 0])])},
        'bolt': {'position': _kfv([(0.0, [0, -40, 0])])},
    }}
    # 放箭：弦回弹过冲 + 弩箭飞出 + 机体后坐
    fire = {'loop': False, 'animation_length': 0.32, 'bones': {
        'string_left': {'rotation': _kf([(0.0, [0, 0, 0]), (0.1, [0, 3.5, 0]), (0.32, [0, 0, 0])])},
        'string_right': {'rotation': _kf([(0.0, [0, 0, 0]), (0.1, [0, -3.5, 0]), (0.32, [0, 0, 0])])},
        'nock': {'position': _kfv([(0.0, [0, 0, DRAW_DZ]), (0.1, [0, 0, -0.4]), (0.32, [0, 0, 0])])},
        'bolt': {'position': _kfv([(0.0, [0, 0, DRAW_DZ]), (0.08, [0, 0, -14]), (0.32, [0, -40, 0])])},
        'move': {'rotation': _kf([(0.0, [-1.2, 0, 0]), (0.08, [2.4, 0, 0]), (0.32, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.08, [0, 0, 1.1]), (0.32, [0, 0, 0])])},
    }}
    anims = {'format_version': '1.8.0', 'animations': {
        P + 'idle': idle, P + 'run': run, P + 'run_fast': run_fast, P + 'fire': fire}}
    os.makedirs(os.path.dirname(ANIM_OUT), exist_ok=True)
    with open(ANIM_OUT, 'w', encoding='utf-8') as fh:
        json.dump(anims, fh, ensure_ascii=False, indent=1)
    print('动画 -> %s（idle/run/run_fast[loop]、fire[play_once]；拉弦/装弹由 GeoModel 程序化驱动）' % ANIM_OUT)


def write_bbmodel(out_bones, cubes, tex_size):
    elements, groups = [], []
    pivots = dict((b['name'], b['pivot']) for b in out_bones)
    for name, parent, _piv in BONES:
        cs = cubes.get(name) or []
        if not cs:
            continue
        for i, c in enumerate(cs):
            elements.append({'name': '%s_%d' % (name, i), 'type': 'cube',
                             'uuid': _uuid('%s_%d' % (name, i)), 'origin': c['origin'],
                             'size': c['size'], 'inflate': 0, 'uv': c['uv'],
                             'visibility': True, 'export': True, 'locked': False})
        groups.append({'name': name, 'uuid': _uuid(name), 'origin': pivots[name],
                       'rotation': [0, 0, 0],
                       'children': [_uuid('%s_%d' % (name, i)) for i in range(len(cs))],
                       'visibility': True, 'autouv': 0, 'color': 0, 'export': True,
                       'locked': False, 'isOpen': False, 'parent': parent or 'root'})
    with open(TEX_OUT, 'rb') as fh:
        durl = 'data:image/png;base64,' + base64.b64encode(fh.read()).decode()
    bb = {'meta': {'format_version': '4.5', 'model_format': 'geckolib_model', 'box_uv': False},
          'name': 'crossbow_geo', 'resolution': {'width': tex_size, 'height': tex_size},
          'elements': elements, 'outliner': [g['uuid'] for g in groups], 'groups': groups,
          'textures': [{'path': '', 'name': 'crossbow_geo.png', 'folder': 'block',
                        'namespace': '', 'id': '0', 'particle': False,
                        'render_mode': 'default', 'visible': True, 'mode': 'bitmap',
                        'saved': True, 'uuid': _uuid('tex'), 'source': durl}],
          'animations': [], 'animation_controllers': []}
    with open(BB_OUT, 'w', encoding='utf-8') as fh:
        json.dump(bb, fh, ensure_ascii=False)
    print('工程 -> %s（%.2f MB）' % (BB_OUT, os.path.getsize(BB_OUT) / 1048576))


def _uuid(s):
    import hashlib
    h = hashlib.md5(s.encode('utf-8')).hexdigest()
    return '%s-%s-%s-%s-%s' % (h[:8], h[8:12], h[12:16], h[16:20], h[20:32])


if __name__ == '__main__':
    sys.exit(build(sys.argv))
