#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 模型/akm.bbmodel（真枪外形的网格）转成 GeckoLib 真骨骼模型（poly_mesh）。

思路：外形直接用参考模型的网格（所以长得就像真枪），按区域把面切给不同骨骼
（枪身 / 弹匣 / 枪机 / 枪托 / 护木 / 枪管 / 握把），于是换弹、拉栓动画能驱动部件。
贴图从 2048 缩到 512，UV 同步缩放。

产出：
  geo/akm.geo.json             poly_mesh 骨骼模型
  textures/models/akm_geo.png  512x512 贴图（由参考贴图缩放而来）
  模型/akm_mesh.bbmodel        Blockbench 工程（网格 + 骨骼分组）

用法: python tools/akm_mesh_gen.py [--tex 512] [--no-bbmodel]
"""
import base64
import io
import json
import os
import sys

from PIL import Image

REF = '模型/akm.bbmodel'
GEO_OUT = 'src/main/resources/assets/hexalunar_calamity/geo/akm.geo.json'
TEX_OUT = 'src/main/resources/assets/hexalunar_calamity/textures/models/akm_geo.png'
BB_OUT = '模型/akm_mesh.bbmodel'

# 骨骼：名字 / 父 / pivot（与动画文件里的骨骼名一致）
BONES = [
    ('root', None, (0, 0, 0)),
    ('body', 'root', (0, 2.2, 0)),
    ('dust_cover', 'body', (0, 3.6, 0)),
    ('rear_sight', 'body', (0, 3.9, -2.4)),
    ('bolt', 'body', (1.0, 3.0, 0.4)),
    ('handguard', 'body', (0, 2.8, -4.6)),
    ('barrel', 'body', (0, 2.9, -7.2)),
    ('magazine', 'body', (0, 1.4, -1.3)),
    ('trigger', 'body', (0, 1.4, 1.8)),
    ('grip', 'body', (0, 1.4, 2.8)),
    ('stock', 'body', (0, 2.4, 5.2)),
    ('selector', 'body', (0.8, 2.2, 1.1)),
]


def _normal(p3):
    """三点法线（Newell），退化为 +Y。"""
    if len(p3) < 3:
        return (0.0, 1.0, 0.0)
    nx = ny = nz = 0.0
    for i in range(len(p3)):
        a, b = p3[i], p3[(i + 1) % len(p3)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    ln = (nx * nx + ny * ny + nz * nz) ** 0.5
    if ln < 1e-9:
        return (0.0, 1.0, 0.0)
    return (nx / ln, ny / ln, nz / ln)


def region_of(cx, cy, cz):
    """按面的中心点判断它属于哪根骨骼。"""
    if cy < 1.15 and -3.8 < cz < 0.9:
        return 'magazine'
    if cz > 3.0:
        return 'stock'
    if cz < -7.15:
        return 'barrel'
    if cz < -3.0:
        return 'handguard'
    if cy < 1.9 and cz > 1.3:
        return 'grip'
    if 1.0 < cy < 2.5 and 0.6 < cz < 3.2:
        return 'trigger'
    if cy > 3.25 and -3.2 < cz < 1.4:
        return 'dust_cover'
    if 2.4 < cy < 3.6 and -3.0 < cz < -1.0 and abs(cx) > 1.4:
        return 'selector'
    if cy > 3.2 and -3.4 < cz < -1.6:
        return 'rear_sight'
    if cy > 2.55 and -3.3 < cz < 1.6:
        return 'bolt'
    return 'body'


def main(argv):
    tex_size = 512
    if '--tex' in argv:
        tex_size = int(argv[argv.index('--tex') + 1])
    with open(REF, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    res = data.get('resolution') or {}
    uv_w = res.get('width', 2048) or 2048
    uv_h = res.get('height', 2048) or 2048
    el = data['elements'][0]
    verts = el['vertices']                       # {id: [x,y,z]}
    faces = el['faces']                          # {id: {vertices:[ids], uv:{id:[u,v]}}}
    print('参考网格: %d 顶点 / %d 面   UV 空间 %dx%d' % (len(verts), len(faces), uv_w, uv_h))

    # ---- 贴图：从内嵌的 base64 解出来，缩到 512 ----
    tex = None
    for t in data.get('textures', []):
        src = t.get('source') or ''
        if src.startswith('data:image'):
            tex = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGB')
            break
    if tex is None:
        raise SystemExit('参考工程里没有内嵌贴图')
    print('原贴图 %s -> %dx%d' % (str(tex.size), tex_size, tex_size))
    tex.resize((tex_size, tex_size), Image.LANCZOS).save(TEX_OUT)
    su, sv = tex_size / float(uv_w), tex_size / float(uv_h)

    # ---- 按骨骼分面 ----
    buckets = {b[0]: [] for b in BONES}
    for fid, f in faces.items():
        vs = [verts[k] for k in f['vertices'] if k in verts]
        if len(vs) < 3:
            continue
        cx = sum(v[0] for v in vs) / len(vs)
        cy = sum(v[1] for v in vs) / len(vs)
        cz = sum(v[2] for v in vs) / len(vs)
        buckets[region_of(cx, cy, cz)].append((f['vertices'], f.get('uv') or {}))
    for k, v in buckets.items():
        print('   %-12s %4d 面' % (k, len(v)))

    # ---- 生成 geo（poly_mesh）----
    out_bones = []
    for name, parent, piv in BONES:
        quad = buckets.get(name) or []
        b = {'name': name, 'pivot': list(piv)}
        if parent:
            b['parent'] = parent
        if quad:
            # 收集该骨骼用到的顶点，重建索引
            idx = {}
            pos, uv, normals, polys = [], [], [], []
            tmp = []
            for vids, uvmap in quad:
                poly = []
                for vid in vids:
                    if vid not in verts:
                        continue
                    if vid not in idx:
                        idx[vid] = len(pos)
                        pos.append([round(c, 4) for c in verts[vid]])
                        u = uvmap.get(vid) or [0.0, 0.0]
                        uv.append([round(u[0] * su, 3), round(u[1] * sv, 3)])
                    poly.append(idx[vid])
                if len(poly) >= 3:
                    tmp.append((poly, [verts[v] for v in vids if v in verts]))
            for poly, p3 in tmp:
                # 每个面一个法线（平直着色）
                n = _normal(p3)
                normals.append([round(n[0], 4), round(n[1], 4), round(n[2], 4)])
                ni = len(normals) - 1
                # GeckoLib 要求每个顶点写成 [位置索引, 法线索引, 缩放索引]
                polys.append([[pi, ni, 0] for pi in poly])
            b['poly_mesh'] = {
                'normalized_uvs': False,
                'positions': pos,
                'normals': normals,
                'uvs': uv,
                'polys': polys,
            }
        out_bones.append(b)

    geo = {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.akm',
                'texture_width': tex_size, 'texture_height': tex_size,
                'visible_bounds_width': 3, 'visible_bounds_height': 3,
                'visible_bounds_offset': [0, 1.2, 0],
            },
            'bones': out_bones,
        }],
    }
    os.makedirs(os.path.dirname(GEO_OUT), exist_ok=True)
    with open(GEO_OUT, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, indent=1)
    tot = sum(len(b.get('poly_mesh', {}).get('polys', [])) for b in out_bones)
    print('模型 -> %s （%d 骨骼 / %d 三角面）' % (GEO_OUT, len(out_bones), tot))

    # ---- Blockbench 工程（网格 + 分组，可在 Blockbench 里继续编辑）----
    if '--no-bbmodel' not in argv:
        elements, groups = [], []
        for name, parent, piv in BONES:
            quad = buckets.get(name) or []
            if not quad:
                continue
            vmap, vjson, fjson = {}, {}, {}
            for i, (vids, uvmap) in enumerate(quad):
                poly = []
                for vid in vids:
                    if vid not in verts:
                        continue
                    if vid not in vmap:
                        vmap[vid] = 'v%d' % len(vmap)
                        vjson[vmap[vid]] = [round(c, 4) for c in verts[vid]]
                    poly.append(vmap[vid])
                if len(poly) < 3:
                    continue
                uv = {}
                for vid in vids:
                    if vid in uvmap and vid in vmap:
                        uv[vmap[vid]] = [round(uvmap[vid][0] * su, 2), round(uvmap[vid][1] * sv, 2)]
                fjson['f%d' % i] = {'vertices': poly, 'uv': uv, 'texture': 0}
            elements.append({'name': name, 'type': 'mesh', 'uuid': _uuid(name),
                             'vertices': vjson, 'faces': fjson,
                             'origin': [0, 0, 0], 'rotation': [0, 0, 0],
                             'visibility': True, 'export': True, 'locked': False})
            groups.append({'name': name, 'uuid': _uuid('g' + name),
                           'origin': [round(p + 8, 4) for p in piv], 'rotation': [0, 0, 0],
                           'children': [_uuid(name)], 'visibility': True, 'autouv': 0,
                           'color': 0, 'export': True, 'locked': False, 'isOpen': False,
                           'parent': parent or 'root'})
        with open(TEX_OUT, 'rb') as fh:
            durl = 'data:image/png;base64,' + base64.b64encode(fh.read()).decode()
        bb = {
            'meta': {'format_version': '4.5', 'model_format': 'geckolib_model',
                     'box_uv': False},
            'name': 'akm_mesh',
            'resolution': {'width': tex_size, 'height': tex_size},
            'elements': elements,
            'outliner': [g['uuid'] for g in groups],
            'groups': groups,
            'textures': [{'path': '', 'name': 'akm_geo.png', 'folder': 'block',
                          'namespace': '', 'id': '0', 'particle': False,
                          'render_mode': 'default', 'visible': True, 'mode': 'bitmap',
                          'saved': True, 'uuid': _uuid('tex'), 'source': durl}],
            'animations': [],
            'animation_controllers': [],
        }
        with open(BB_OUT, 'w', encoding='utf-8') as fh:
            json.dump(bb, fh, ensure_ascii=False)
        print('工程 -> %s （%.1f MB）' % (BB_OUT, os.path.getsize(BB_OUT) / 1048576))
    return 0


def _uuid(s):
    import hashlib
    h = hashlib.md5(s.encode('utf-8')).hexdigest()
    return '%s-%s-%s-%s-%s' % (h[:8], h[8:12], h[12:16], h[16:20], h[20:32])


if __name__ == '__main__':
    sys.exit(main(sys.argv))
