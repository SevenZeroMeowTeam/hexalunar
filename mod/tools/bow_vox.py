#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""复合弓：把参考网格体素化成 GeckoLib 方块模型（弓身部分），弦/箭另做。

测试用：先看体素化效果，scripts/bow_gen.py 再补齐弦、箭、骨骼与动画。

用法: python tools/bow_vox.py [step] [tex] [out_geo] [out_tex]
"""
import io
import json
import os
import sys

from PIL import Image

sys.path.insert(0, 'tools')
from akm_voxel_gen import load_ref, voxelize, rotate_tris, yaw_slope

REF = '模型/复合弓.bbmodel'
FACES = ('north', 'south', 'east', 'west', 'up', 'down')


def main(argv):
    step = float(argv[1]) if len(argv) > 1 else 0.4
    tex_size = int(argv[2]) if len(argv) > 2 else 512
    geo_out = argv[3] if len(argv) > 3 else 'build/bow_vox.geo.json'
    tex_out = argv[4] if len(argv) > 4 else 'build/bow_vox.png'

    verts, tris, tex, uv_w, uv_h = load_ref(REF)
    tris = rotate_tris(tris, 180.0)     # 让箭飞向 -Z（北）
    tex.resize((tex_size, tex_size), Image.LANCZOS).save(tex_out)
    su = sv = tex_size / float(uv_w)

    cells, lo, hi = voxelize(tris, step, uv_w, uv_h)
    print('体素 %d  包围盒 x %.2f~%.2f y %.2f~%.2f z %.2f~%.2f' % (
        len(cells), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))

    # 把所有体素归到一个骨骼里，先看形状
    cubes = []
    for (ix, iy, iz), (u, v) in cells.items():
        cubes.append({
            'origin': [round(lo[0] + ix * step, 4), round(lo[1] + iy * step, 4),
                       round(lo[2] + iz * step, 4)],
            'size': [round(step, 4)] * 3,
            'uv': {f: {'uv': [round(u - step * su / 2, 3), round(v - step * sv / 2, 3)],
                       'uv_size': [round(step * su, 3), round(step * sv, 3)]} for f in FACES},
        })
    geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': 'geometry.bow', 'texture_width': tex_size,
                        'texture_height': tex_size},
        'bones': [{'name': 'root', 'pivot': [0, 0, 0], 'cubes': cubes}]}]}
    os.makedirs(os.path.dirname(geo_out), exist_ok=True)
    with open(geo_out, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False)
    print('-> %s （%d 方块）' % (geo_out, len(cubes)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
