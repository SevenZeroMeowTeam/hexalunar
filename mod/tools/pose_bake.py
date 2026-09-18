# -*- coding: utf-8 -*-
"""把 geo 按「拉弦程序化姿态」烘焙一份出来，用于离线检查弦/压把不会跑偏。

用法: python tools/pose_bake.py <in.geo.json> <out.geo.json> <kind>
      kind = crossbow  -> 按 CrossbowGeoModel 的 draw=1 姿态
      kind = bow       -> 按 compound_bow 动画 JSON 的 pull 满帧姿态
"""
import json
import math
import sys


def load(p):
    return json.load(open(p, encoding='utf-8'))


def rot_y(deg):
    a = math.radians(deg)
    return [[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]]


def rot_x(deg):
    a = math.radians(deg)
    return [[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]]


def apply(mat, v):
    return [sum(mat[i][j] * v[j] for j in range(3)) for i in range(3)]


def pose(geo, fn):
    """fn(bone_name) -> (rot_mat_3x3 or None, translate[3]) ；绕骨骼 pivot 施加"""
    g = geo['minecraft:geometry'][0]
    for b in g['bones']:
        r, t = fn(b['name'])
        piv = b.get('pivot', [0, 0, 0])
        for c in b.get('cubes', []):
            o = c['origin']
            s = c['size']
            new = []
            for corner in ((0, 0, 0), (s[0], 0, 0), (0, s[1], 0), (0, 0, s[2]),
                           (s[0], s[1], 0), (s[0], 0, s[2]), (0, s[1], s[2]),
                           (s[0], s[1], s[2])):
                p = [o[i] + corner[i] - piv[i] for i in range(3)]
                if r:
                    p = apply(r, p)
                p = [p[i] + piv[i] + t[i] for i in range(3)]
                new.append(p)
            lo = [min(n[i] for n in new) for i in range(3)]
            hi = [max(n[i] for n in new) for i in range(3)]
            c['origin'] = [round(lo[i], 4) for i in range(3)]
            c['size'] = [round(hi[i] - lo[i], 4) for i in range(3)]
            c.pop('rotation', None)
            c.pop('pivot', None)
    return geo


def crossbow(name):
    tip_x, dz, nz = 6.0, 2.60, -5.80
    phi = math.degrees(math.atan2(dz, tip_x))
    if name == 'string_left':
        return rot_y(-phi), [0, 0, 0]
    if name == 'string_right':
        return rot_y(phi), [0, 0, 0]
    if name == 'nock':
        return None, [0, 0, dz]
    if name == 'bolt':
        return None, [0, 0, dz]
    return None, [0, 0, 0]


def bow(name):
    if name == 'string_upper':
        return rot_x(-20.785), [0, 0, 0]
    if name == 'string_lower':
        return rot_x(20.785), [0, 0, 0]
    if name == 'nock':
        return None, [0, 0, 3.38]
    if name == 'arrow':
        return None, [0, 0, 3.38]
    return None, [0, 0, 0]


def main():
    src, dst, kind = sys.argv[1], sys.argv[2], sys.argv[3]
    geo = load(src)
    pose(geo, crossbow if kind == 'crossbow' else bow)
    with open(dst, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, separators=(',', ':'))
    print('wrote', dst)


if __name__ == '__main__':
    main()
