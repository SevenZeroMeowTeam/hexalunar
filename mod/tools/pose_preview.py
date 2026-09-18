#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 geo 按某个姿态（旋转/平移）变换后另存一个 geo，用于离线预览骨骼动画效果。

只支持绕骨骼 pivot 的 XYZ 欧拉旋转 + 平移（够验证拉弦/换弹这类动作）。

用法: python tools/pose_preview.py <in.geo.json> <out.geo.json> '<pose.json>'
pose.json 形如 {"string_upper": {"rot": [-20.78, 0, 0]}, "nock": {"pos": [0, 0, 2.6]}}
"""
import io
import os
import json
import math
import sys


def rot(p, pivot, deg):
    x, y, z = (p[0] - pivot[0], p[1] - pivot[1], p[2] - pivot[2])
    rx, ry, rz = (math.radians(d) for d in deg)
    # Z
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    # Y
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    # X
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    return (x + pivot[0], y + pivot[1], z + pivot[2])


def main(argv):
    geo_in, geo_out = argv[1], argv[2]
    arg = argv[3]
    if os.path.exists(arg):
        with io.open(arg, encoding='utf-8') as fh:
            pose = json.load(fh)
    else:
        pose = json.loads(arg)
    with io.open(geo_in, encoding='utf-8') as fh:
        geo = json.load(fh)
    bones = geo['minecraft:geometry'][0]['bones']
    piv = dict((b['name'], b['pivot']) for b in bones)
    order = [b['name'] for b in bones]
    cubes = []
    for b in bones:
        tr = pose.get(b['name']) or {}
        rotv = tr.get('rot') or [0, 0, 0]
        posv = tr.get('pos') or [0, 0, 0]
        # 父骨骼的变换要叠加（body 动了子骨骼跟着动）
        chain = []
        cur = b['name']
        chain.append(cur)
        p = None
        for bb in bones:
            if bb['name'] == cur:
                p = bb.get('parent')
        while p and p in piv:
            chain.append(p)
            nxt = None
            for bb in bones:
                if bb['name'] == p:
                    nxt = bb.get('parent')
            p = nxt
        chain.reverse()
        for c in b.get('cubes') or []:
            o = list(c['origin'])
            s = list(c['size'])
            for bone_name in chain:
                t = pose.get(bone_name) or {}
                o = list(rot(o, piv[bone_name], t.get('rot') or [0, 0, 0]))
                if t.get('pos'):
                    o = [o[i] + t['pos'][i] for i in range(3)]
            cubes.append({'origin': [round(v, 3) for v in o], 'size': s, 'uv': c['uv']})
    geo['minecraft:geometry'][0]['bones'] = [{'name': 'root', 'pivot': [0, 0, 0], 'cubes': cubes}]
    for b in geo['minecraft:geometry'][0]['bones']:
        for c in b['cubes']:
            for f in c['uv'].values():
                f['uv'] = [round(v, 3) for v in f['uv']]
                f['uv_size'] = [round(v, 3) for v in f['uv_size']]
    with io.open(geo_out, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False)
    print('%s -> %s（%d 方块）' % (geo_in, geo_out, len(cubes)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
