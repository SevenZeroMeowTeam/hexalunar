#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""震爆弹（flashbang / 参考 模型/mtx.bbmodel）重建 GeckoLib 真骨骼方块模型。

参考网格是薄壳 mesh（10386 面），按实测比例手工重建：
  弹体   圆柱（半径 ~4.8）：每层用「十字双盒」拟八边形截面
  底部   略宽的底盖（参考半径 5.9）
  头     顶部引信头（半径 4.4）+ 上盖
  环带   弹体中段一圈蓝色带（参考贴图里就是蓝的）
  压把   沿侧面竖直的扁平杆，铰点在头顶
  保险销 穿过引信头的横销（轴沿 Z）+ 外端拉环；**拔销方向 = -Z（北）**

朝向：保险销拉出方向 / 模型正面 = -Z（北）。原点=弹体中心（握在手里）。
动画命名与播放类型照 SuperbWarfare BOCEK 规范；拔销/压把弹开由 GeoModel 程序化驱动。

产出：geo/flashbang.geo.json、textures/models/flashbang_geo.png、
      animations/flashbang.animation.json、模型/震爆弹_geo.bbmodel

用法: python tools/flashbang_gen.py [--tex 512] [--no-bbmodel]
"""
import base64
import io
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
from akm_voxel_gen import load_ref

REF = '模型/mtx.bbmodel'
GEO_OUT = 'src/main/resources/assets/hexalunar_calamity/geo/flashbang.geo.json'
TEX_OUT = 'src/main/resources/assets/hexalunar_calamity/textures/models/flashbang_geo.png'
ANIM_OUT = 'src/main/resources/assets/hexalunar_calamity/animations/flashbang.animation.json'
BB_OUT = '模型/震爆弹_geo.bbmodel'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')

SCALE = 0.34                       # 参考 18.4px -> 手持约 6.2px
BODY_R, BODY_Y0, BODY_Y1 = 4.80, -3.60, 11.00
CAP_R, CAP_Y = 5.70, -4.80
HEAD_R, HEAD_Y0, HEAD_Y1 = 4.40, 11.00, 13.00
ORG = (0.0, 3.6, 1.6)              # 参考模型的偏置中心，减掉它让原点落在弹体中心

# 骨骼：(名字, 父, pivot)  —— 缩放前的参考坐标
BONES = [
    ('root', None, (0.0, 0.0, 0.0)),
    ('move', 'root', ORG),
    ('body', 'move', ORG),
    ('fuze', 'body', (0.0, 11.0, 1.6)),
    ('spoon', 'fuze', (0.0, 13.4, 1.2)),      # 铰点：头顶、压把根部
    ('pin', 'fuze', (0.0, 12.2, 1.6)),
]

SAMPLES = {
    'body': (-4.7, 3.9, -1.0, 10.0, -1.0, 4.5),
    'band': (-4.7, 3.9, 5.5, 9.0, -0.5, 4.5),
    'cap': (-4.0, 3.0, -5.0, -1.5, -1.0, 5.6),
    'head': (-3.5, 3.5, 11.0, 13.6, -1.5, 4.0),
    'spoon': (-4.6, -2.4, 6.0, 13.0, -2.6, 1.0),
    'pin': (-4.0, -1.4, 11.0, 13.4, -2.6, 0.4),
}
# 参考贴图偏暗，用「目标材质色 × 采样亮度」着色
MATERIAL = {'body': (74, 78, 68),      # 军绿弹体
            'band': (44, 88, 142),     # 蓝色环带
            'cap': (58, 60, 56),       # 深灰底盖
            'head': (50, 52, 50),      # 深灰引信头
            'spoon': (44, 46, 46),     # 黑色压把
            'pin': (168, 170, 172)}    # 银灰保险销/拉环


def shade(patch, base):
    px = list(patch.getdata())
    lums = sorted(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2] for c in px)
    mid = lums[len(lums) // 2] or 1.0
    out = Image.new('RGB', patch.size)
    data = []
    for c in px:
        lum = (0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / mid
        k = max(0.70, min(1.30, 0.50 + 0.55 * lum))
        data.append(tuple(max(0, min(255, int(v * k))) for v in base))
    out.putdata(data)
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


def cylinder_slabs(y0, y1, r, n=7):
    """圆柱：每层用两个正交的盒子拼出八边形截面。"""
    out = []
    h = (y1 - y0) / n
    for i in range(n):
        ya, yb = y0 + i * h, y0 + (i + 1) * h
        w = r
        s = r * 0.62
        out.append((-w, w, ya, yb, -s, s))
        out.append((-s, s, ya, yb, -w, w))
    return out


def main(argv):
    tex_size = 512
    if '--tex' in argv:
        tex_size = int(argv[argv.index('--tex') + 1])
    _v, tris, tex, uv_w, uv_h = load_ref(REF)
    if tex is None:
        raise SystemExit('参考工程没有内嵌贴图')
    atlas, slots = build_texture(sample_patches(tris, tex, uv_w, uv_h), tex_size)
    os.makedirs(os.path.dirname(TEX_OUT), exist_ok=True)
    atlas.save(TEX_OUT)

    cubes = {b[0]: [] for b in BONES}

    def add(bone, x0, x1, y0, y1, z0, z1, mat):
        u, v = slots[mat]
        face = {'uv': [u + 9.0, v + 9.0], 'uv_size': [46.0, 46.0]}
        cubes[bone].append({
            'origin': [round(x0 - ORG[0], 3), round(y0 - ORG[1], 3), round(z0 - ORG[2], 3)],
            'size': [round(x1 - x0, 3), round(y1 - y0, 3), round(z1 - z0, 3)],
            'uv': {f: dict(face) for f in FACES},
        })

    # 弹体：圆柱 + 中段蓝环带（环带做成略外凸的两层）
    for (x0, x1, y0, y1, z0, z1) in cylinder_slabs(BODY_Y0, BODY_Y1, BODY_R, 7):
        add('body', x0, x1, y0, y1, z0, z1, 'body')
    for (x0, x1, y0, y1, z0, z1) in cylinder_slabs(6.0, 8.4, BODY_R + 0.25, 2):
        add('body', x0, x1, y0, y1, z0, z1, 'band')
    # 底盖（略宽）
    for (x0, x1, y0, y1, z0, z1) in cylinder_slabs(CAP_Y, BODY_Y0, CAP_R, 2):
        add('body', x0, x1, y0, y1, z0, z1, 'cap')
    # 引信头 + 上盖
    for (x0, x1, y0, y1, z0, z1) in cylinder_slabs(HEAD_Y0, HEAD_Y1, HEAD_R, 2):
        add('fuze', x0, x1, y0, y1, z0, z1, 'head')
    add('fuze', -1.5, 1.5, HEAD_Y1, HEAD_Y1 + 0.9, 0.1, 3.1, 'head')
    # 压把：沿 -x 侧竖直（铰点在头顶），顶端一段塞进引信头里避免露缝
    add('spoon', -5.30, -3.90, 12.3, 13.6, -0.5, 3.6, 'spoon')
    add('spoon', -5.20, -3.80, 8.0, 12.3, -0.4, 1.6, 'spoon')
    add('spoon', -5.20, -3.80, 5.0, 8.0, -0.2, 1.4, 'spoon')
    # 保险销：横销穿过引信头 + 外端拉环挂在头外侧（拉出方向 -Z）
    add('pin', -0.34, 0.34, 11.85, 12.55, -4.60, 4.20, 'pin')
    ring_c, ring_r = (0.0, 11.6, -5.85), 1.15
    for i in range(8):
        a = math.radians(i * 45.0)
        cy = ring_c[1] + ring_r * math.cos(a)
        cz = ring_c[2] + ring_r * math.sin(a)
        add('pin', -0.20, 0.20, cy - 0.32, cy + 0.32, cz - 0.32, cz + 0.32, 'pin')

    for name in cubes:
        for c in cubes[name]:
            c['origin'] = [round(v * SCALE, 3) for v in c['origin']]
            c['size'] = [round(v * SCALE, 3) for v in c['size']]

    out_bones = []
    for name, parent, piv in BONES:
        b = {'name': name,
             'pivot': [round((piv[i] - ORG[i]) * SCALE, 4) for i in range(3)]}
        if parent:
            b['parent'] = parent
        if cubes.get(name):
            b['cubes'] = cubes[name]
        out_bones.append(b)

    total = sum(len(cubes[b[0]]) for b in BONES)
    geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': 'geometry.flashbang', 'texture_width': tex_size,
                        'texture_height': tex_size, 'visible_bounds_width': 1,
                        'visible_bounds_height': 1, 'visible_bounds_offset': [0, 0, 0]},
        'bones': out_bones}]}
    with open(GEO_OUT, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, indent=1)
    print('模型 -> %s（%d 骨骼 / %d 方块，缩放 %.2f）' % (GEO_OUT, len(out_bones), total, SCALE))

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
    P = 'animation.flashbang.'
    idle = {'loop': True, 'animation_length': 1.7, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.85, [0.6, 0, 0.4]), (1.7, [0, 0, 0])])},
    }}
    run = {'loop': True, 'animation_length': 0.8333, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.21, [3.2, 0, -1.2]), (0.42, [0, 0, 0]),
                                  (0.63, [-2.8, 0, 1.0]), (0.83, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.21, [0, -0.6, 0]), (0.42, [0, 0, 0]),
                                   (0.63, [0, 0.6, 0]), (0.83, [0, 0, 0])])},
    }}
    run_fast = {'loop': True, 'animation_length': 0.6, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.15, [5.0, 0, -1.8]), (0.30, [0, 0, 0]),
                                  (0.45, [-4.2, 0, 1.4]), (0.60, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.15, [0, -1.1, 0]), (0.30, [0, 0, 0]),
                                   (0.45, [0, 1.1, 0]), (0.60, [0, 0, 0])])},
    }}
    throw = {'loop': False, 'animation_length': 0.3, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.12, [-26, 0, 0]), (0.3, [-40, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.12, [0, 1.2, -1.6]), (0.3, [0, 2.0, -3.0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (0.12, [-16, 0, 0]), (0.3, [-28, 0, 0])])},
        'spoon': {'rotation': _kf([(0.0, [0, 0, 0]), (0.1, [7, 0, 0]), (0.3, [-6, 0, 0])])},
    }}
    anims = {'format_version': '1.8.0', 'animations': {
        P + 'idle': idle, P + 'run': run, P + 'run_fast': run_fast, P + 'throw': throw}}
    os.makedirs(os.path.dirname(ANIM_OUT), exist_ok=True)
    with open(ANIM_OUT, 'w', encoding='utf-8') as fh:
        json.dump(anims, fh, ensure_ascii=False, indent=1)
    print('动画 -> %s（idle/run/run_fast[loop]、throw[play_once]）' % ANIM_OUT)


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
          'name': 'flashbang_geo', 'resolution': {'width': tex_size, 'height': tex_size},
          'elements': elements, 'outliner': [g['uuid'] for g in groups], 'groups': groups,
          'textures': [{'path': '', 'name': 'flashbang_geo.png', 'folder': 'block',
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
    sys.exit(main(sys.argv))
