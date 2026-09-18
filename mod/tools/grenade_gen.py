#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""手雷（frag_grenade / 参考 模型/mud.bbmodel）重建 GeckoLib 真骨骼方块模型。

参考网格是薄壳 mesh（3349 顶点 / 6719 面），按实测比例手工重建方块：
  弹体   半径 5.4 的菠萝球（参考 x ±5.43、y -0.4~10.4）
  引信颈 y 10.0~12.6 / 引信帽 y 12.6~14.6（参考 y 13~15 时 x ±1.94）
  压把   沿弹体背面（+z）竖直，铰点在引信顶 —— 保险销拔出后会弹开
  保险销 穿过引信的横销（轴沿 Z）+ 外端拉环；**拔销方向 = -Z（北）**

朝向：保险销拉出方向 / 模型正面 = -Z（北）。
动画命名与播放类型照 SuperbWarfare BOCEK 的规范：animation.<id>.<state>；
拔销与压把弹开是**连续动作**，所以用模型类里的程序化骨骼变换驱动（同它家 BocekItemModel），
动画只负责 idle / run / run_fast / throw。

产出：
  geo/mud.geo.json
  textures/models/mud_geo.png
  animations/mud.animation.json
  模型/手雷_geo.bbmodel

用法: python tools/grenade_gen.py [--tex 512] [--no-bbmodel]
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
from akm_voxel_gen import load_ref

REF = '模型/mud.bbmodel'
GEO_OUT = 'src/main/resources/assets/hexalunar_calamity/geo/mud.geo.json'
TEX_OUT = 'src/main/resources/assets/hexalunar_calamity/textures/models/mud_geo.png'
ANIM_OUT = 'src/main/resources/assets/hexalunar_calamity/animations/mud.animation.json'
BB_OUT = '模型/手雷_geo.bbmodel'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')

# 参考是 16px 大小的手雷，缩到手持合理大小（约 5.7px）
SCALE = 0.38
BODY_R = 5.4
BODY_CY, BODY_CZ = 5.0, 5.4

# 骨骼：(名字, 父, pivot)  —— 都在缩放前的参考坐标系里
BONES = [
    ('root', None, (0.0, 0.0, 0.0)),
    ('move', 'root', (0.0, 5.0, 5.4)),
    ('body', 'move', (0.0, 5.0, 5.4)),
    ('fuze', 'body', (0.0, 10.6, 5.4)),
    ('spoon', 'fuze', (0.0, 14.35, 8.6)),    # 铰点取压把最顶端，开合时不会看着脱开
    ('pin', 'fuze', (0.0, 12.2, 5.4)),        # 保险销轴心
]

# 从参考贴图采样的部件区域：(x0,x1, y0,y1, z0,z1)
SAMPLES = {
    'body': (-5.6, 5.6, 1.0, 9.2, 0.6, 9.4),
    'fuze': (-2.2, 2.2, 10.2, 14.8, 3.0, 7.6),
    'spoon': (-1.0, 1.0, 5.0, 13.2, 9.3, 11.6),
    'pin': (-2.6, 2.6, 10.8, 13.6, 0.8, 3.4),
}
FALLBACK = {'body': (86, 98, 58), 'fuze': (58, 60, 56),
            'spoon': (44, 46, 46), 'pin': (150, 152, 155)}
# 参考贴图偏暗且发奇，直接拿来做贴图进游戏是一团黑/一田灰。
# 做法：保留采样块的**亮度细节**（菠萝纹、金属光泽），颜色对准现实材质色
MATERIAL = {'body': (96, 110, 66),      # 军绿弹体
            'fuze': (62, 64, 62),        # 深灰引信
            'spoon': (46, 48, 48),       # 黑色压把
            'pin': (168, 170, 172)}      # 银灰保险销/拉环


def shade(patch, base):
    """把采样块变成「目标材质色 × 自身亮度」：保留纹理，去掉偏色。"""
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
    """按区域从参考贴图取一小块真实纹理当材质（保留菠萝纹/金属质感）。"""
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
            out[mat] = None
            continue
        mu = sorted(p[0] for p in pts)[len(pts) // 2]
        mv = sorted(p[1] for p in pts)[len(pts) // 2]
        h = size // 2
        box = (int(mu) - h, int(mv) - h, int(mu) + h, int(mv) + h)
        patch = Image.new('RGB', (size, size), FALLBACK[mat])
        clip = (max(box[0], 0), max(box[1], 0), min(box[2], cw), min(box[3], ch))
        if clip[2] > clip[0] and clip[3] > clip[1]:
            sub = tex.crop(clip).convert('RGB')
            patch.paste(sub, (clip[0] - box[0], clip[1] - box[1]))
        # 把影调向“该区域实际采样到的中值色”拉回一半：
        # 参考贴图那块常常落在暗部，直接用会整块发褐，这样既保留纹理又不会偏色
        cols = []
        for t in tris:
            cx = sum(q[0] for q in t[:3]) / 3.0
            cy = sum(q[1] for q in t[:3]) / 3.0
            cz = sum(q[2] for q in t[:3]) / 3.0
            if not (x0 <= cx <= x1 and y0 <= cy <= y1 and z0 <= cz <= z1):
                continue
            for k in range(3):
                u, v = t[3 + k]
                cols.append(tex.getpixel((int(u * cw / float(uv_w)) % cw,
                                          int(v * ch / float(uv_h)) % ch))[:3])
        if cols:
            cols.sort(key=lambda c: c[0] * 3 + c[1] * 6 + c[2])
            base = cols[len(cols) // 2]
            patch = Image.blend(patch, Image.new('RGB', (size, size), base), 0.35)
        out[mat] = shade(patch, MATERIAL[mat])
    return out


def build_texture(patches, tex_size):
    im = Image.new('RGB', (tex_size, tex_size), (24, 24, 26))
    slots = {}
    for i, mat in enumerate(sorted(SAMPLES)):
        ox, oy = (i % 8) * 64, (i // 8) * 64
        slots[mat] = (ox, oy)
        p = patches.get(mat)
        if p is None:
            p = Image.new('RGB', (48, 48), FALLBACK[mat])
        p = p.resize((48, 48), Image.LANCZOS)
        im.paste(p, (ox + 8, oy + 8))
        # 边缘沿用中值色，避免采样到透明像素出现黑边
        dr = ImageDraw.Draw(im)
        for x in range(64):
            for xx in (ox, ox + 63):
                dr.point((xx, oy + x), fill=(32, 34, 32))
        for y in range(64):
            for yy in (oy, oy + 63):
                dr.point((ox + y, yy), fill=(32, 34, 32))
    return im, slots


def sphere_slabs():
    """把菠萝球切成 8 层方板（像素球）。"""
    out = []
    n = 8
    h = 2 * BODY_R / n
    for i in range(n):
        y0 = BODY_CY - BODY_R + i * h
        y1 = y0 + h
        ym = (y0 + y1) / 2.0
        half = math.sqrt(max(0.0, BODY_R * BODY_R - (ym - BODY_CY) ** 2))
        # 取整到 0.2px，看起来更“方块化”
        half = math.floor(half / 0.2) * 0.2
        if half <= 0.2:
            continue
        out.append((-half, half, y0, y1, BODY_CZ - half, BODY_CZ + half))
    return out


def main(argv):
    tex_size = 512
    if '--tex' in argv:
        tex_size = int(argv[argv.index('--tex') + 1])
    _v, tris, tex, uv_w, uv_h = load_ref(REF)
    if tex is None:
        raise SystemExit('参考工程没有内嵌贴图')
    patches = sample_patches(tris, tex, uv_w, uv_h)
    atlas, slots = build_texture(patches, tex_size)
    os.makedirs(os.path.dirname(TEX_OUT), exist_ok=True)
    atlas.save(TEX_OUT)

    cubes = {b[0]: [] for b in BONES}

    def add(bone, x0, x1, y0, y1, z0, z1, mat):
        u, v = slots[mat]
        face = {'uv': [u + 9.0, v + 9.0], 'uv_size': [46.0, 46.0]}
        cubes[bone].append({
            'origin': [round(x0, 3), round(y0, 3), round(z0, 3)],
            'size': [round(x1 - x0, 3), round(y1 - y0, 3), round(z1 - z0, 3)],
            'uv': {f: dict(face) for f in FACES},
        })

    # 弹体：像素球 + 一点腰部收窄
    for (x0, x1, y0, y1, z0, z1) in sphere_slabs():
        add('body', x0, x1, y0, y1, z0, z1, 'body')

    # 引信颈 / 帽
    add('fuze', -1.6, 1.6, 10.0, 12.6, 3.8, 7.0, 'fuze')
    add('fuze', -1.9, 1.9, 12.6, 14.6, 3.4, 7.2, 'fuze')
    add('fuze', -0.9, 0.9, 14.6, 15.0, 4.4, 6.4, 'fuze')

    # 压把：沿背面竖直的扁平杆（铰点在顶部）
    # 顶端一段插进引信里（z 与引信重叠），这样绕顶点铰开时不会露出缝
    add('spoon', -0.70, 0.70, 13.0, 14.6, 6.9, 9.8, 'spoon')
    add('spoon', -0.60, 0.60, 8.6, 13.0, 9.0, 10.3, 'spoon')
    add('spoon', -0.60, 0.60, 4.6, 8.6, 9.6, 10.9, 'spoon')
    add('spoon', -0.60, 0.60, 3.2, 4.6, 8.6, 10.2, 'spoon')

    # 保险销：横销 + 外端拉环（拉出方向 -Z）
    add('pin', -0.34, 0.34, 11.85, 12.55, 4.6, 8.6, 'pin')
    ring_c, ring_r = (0.0, 11.6, 3.1), 1.15
    for i in range(8):
        a = math.radians(i * 45.0)
        cy = ring_c[1] + ring_r * math.cos(a)
        cz = ring_c[2] + ring_r * math.sin(a)
        add('pin', -0.20, 0.20, cy - 0.32, cy + 0.32, cz - 0.32, cz + 0.32, 'pin')

    # 原点：弹体中心（手持时握在手里），再整体缩放
    org = (0.0, BODY_CY, BODY_CZ)
    for name in cubes:
        for c in cubes[name]:
            c['origin'] = [round((c['origin'][i] - org[i]) * SCALE, 3) for i in range(3)]
            c['size'] = [round(v * SCALE, 3) for v in c['size']]

    out_bones = []
    for name, parent, piv in BONES:
        b = {'name': name,
             'pivot': [round((piv[i] - org[i]) * SCALE, 4) for i in range(3)]}
        if parent:
            b['parent'] = parent
        if cubes.get(name):
            b['cubes'] = cubes[name]
        out_bones.append(b)

    total = sum(len(cubes[b[0]]) for b in BONES)
    geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': 'geometry.mud', 'texture_width': tex_size,
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
    """照 BOCEK 规范：animation.<id>.<state>，loop 用 true / hold_on_last_frame / false。

    拔销与压把弹开是连续动作（跟 GrenadeItem 的按住进度走），
    放在 GeoModel 里程序化驱动，这里只做 idle / run / run_fast / throw。
    """
    P = 'animation.mud.'
    idle = {'loop': True, 'animation_length': 1.6, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.8, [0.6, 0, 0.4]), (1.6, [0, 0, 0])])},
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
    # 投掷：手雷从手里甩出去那一下（身体前倾 + 压把甩开）
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
    print('动画 -> %s（BOCEK 规范：idle/run/run_fast[loop]、throw[play_once]；'
          '拔销/压把由 GeoModel 程序化驱动）' % ANIM_OUT)
    return 0


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
          'name': 'grenade_geo', 'resolution': {'width': tex_size, 'height': tex_size},
          'elements': elements, 'outliner': [g['uuid'] for g in groups], 'groups': groups,
          'textures': [{'path': '', 'name': 'mud_geo.png', 'folder': 'block', 'namespace': '',
                        'id': '0', 'particle': False, 'render_mode': 'default', 'visible': True,
                        'mode': 'bitmap', 'saved': True, 'uuid': _uuid('tex'), 'source': durl}],
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
