#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把一个 mesh 型 bbmodel 绕 Y 轴转正（长轴对齐 Z），居中 X/Z、Y 抬到 0，另存新 bbmodel。

用法: python tools/bb_align.py <in.bbmodel> <yaw_deg> <out.bbmodel>
"""
import json
import math
import sys


def main(src, yaw, dst):
    with open(src, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    a = math.radians(-float(yaw))
    ca, sa = math.cos(a), math.sin(a)
    rot = {}
    for el in data['elements']:
        out = {}
        for k, v in el['vertices'].items():
            out[k] = [v[0] * ca + v[2] * sa, v[1], -v[0] * sa + v[2] * ca]
        rot[el['name']] = out
    xs = [v[0] for o in rot.values() for v in o.values()]
    ys = [v[1] for o in rot.values() for v in o.values()]
    zs = [v[2] for o in rot.values() for v in o.values()]
    cx = (min(xs) + max(xs)) / 2
    cz = (min(zs) + max(zs)) / 2
    y0 = min(ys)
    for el in data['elements']:
        el['vertices'] = {k: [round(v[0] - cx, 4), round(v[1] - y0, 4), round(v[2] - cz, 4)]
                          for k, v in rot[el['name']].items()}
    data['name'] = data.get('name', 'model') + '_aligned'
    with open(dst, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False)
    xs = [v[0] for el in data['elements'] for v in el['vertices'].values()]
    ys = [v[1] for el in data['elements'] for v in el['vertices'].values()]
    zs = [v[2] for el in data['elements'] for v in el['vertices'].values()]
    print('aligned -> %s  X[%.2f..%.2f]=%.2f  Y[%.2f..%.2f]=%.2f  Z[%.2f..%.2f]=%.2f' % (
        dst, min(xs), max(xs), max(xs) - min(xs),
        min(ys), max(ys), max(ys) - min(ys),
        min(zs), max(zs), max(zs) - min(zs)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
