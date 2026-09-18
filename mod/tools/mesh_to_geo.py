#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把任意参考 .bbmodel 的网格转成 poly_mesh geo（单骨骼），用于离线渲染看图。

注意：GeckoLib 4.8.4 只解析 poly_mesh、不渲染它，所以这个 geo **不能**直接用于游戏，
它只是给 tools/geo_view.py 渲染参考形状用的。

用法: python tools/mesh_to_geo.py <model.bbmodel> <out.geo.json> <tex.png> [tex_size]
"""
import base64
import io
import json
import os
import sys

from PIL import Image

sys.path.insert(0, 'tools')
from akm_voxel_gen import load_ref


def _normal(p3):
    if len(p3) < 3:
        return (0.0, 1.0, 0.0)
    nx = ny = nz = 0.0
    for i in range(len(p3)):
        a, b = p3[i], p3[(i + 1) % len(p3)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    ln = (nx * nx + ny * ny + nz * nz) ** 0.5
    return (0.0, 1.0, 0.0) if ln < 1e-9 else (nx / ln, ny / ln, nz / ln)


def main(argv):
    if len(argv) < 4:
        raise SystemExit(__doc__)
    src, geo_out, tex_out = argv[1], argv[2], argv[3]
    tex_size = int(argv[4]) if len(argv) > 4 else 1024
    _v, tris, tex, uv_w, uv_h = load_ref(src)
    if tex is None:
        raise SystemExit('参考工程没有内嵌贴图')
    os.makedirs(os.path.dirname(tex_out), exist_ok=True)
    tex.resize((tex_size, tex_size), Image.LANCZOS).save(tex_out)
    su = sv = tex_size / float(uv_w)

    pos, uvs, normals, polys, idx = [], [], [], [], {}
    for t in tris:
        poly = []
        for k in range(3):
            key = tuple(round(c, 4) for c in t[k])
            if key not in idx:
                idx[key] = len(pos)
                pos.append(list(key))
                uvs.append([round(t[3 + k][0] * su, 3), round(t[3 + k][1] * sv, 3)])
            poly.append(idx[key])
        n = _normal((t[0], t[1], t[2]))
        normals.append([round(n[0], 4), round(n[1], 4), round(n[2], 4)])
        ni = len(normals) - 1
        polys.append([[pi, ni, 0] for pi in poly])

    geo = {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {'identifier': 'geometry.ref_mesh',
                            'texture_width': tex_size, 'texture_height': tex_size},
            'bones': [{'name': 'root', 'pivot': [0, 0, 0],
                       'poly_mesh': {'normalized_uvs': False, 'positions': pos,
                                     'normals': normals, 'uvs': uvs, 'polys': polys}}],
        }],
    }
    with open(geo_out, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False)
    print('%s -> %s（%d 顶点 / %d 面）  贴图 %s' % (src, geo_out, len(pos), len(polys), tex_out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
