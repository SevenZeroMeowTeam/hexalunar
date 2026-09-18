#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""渲染单个 mesh 型 bbmodel 的 side/top/front 视图。

用法: python tools/render_one.py <model.bbmodel> <out_prefix> [yaw]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_mesh as rm  # noqa: E402


def main(path, prefix, yaw=0.0):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    if abs(yaw) > 1e-6:
        import math
        a = math.radians(-yaw)
        ca, sa = math.cos(a), math.sin(a)
        for el in data['elements']:
            el['vertices'] = {k: [v[0] * ca + v[2] * sa, v[1], -v[0] * sa + v[2] * ca]
                              for k, v in el['vertices'].items()}
    os.makedirs(os.path.dirname(prefix) or '.', exist_ok=True)
    tex = rm.load_texture(data)
    if tex:
        tex.convert('RGB').save(prefix + '_tex.png')
    for view in rm.VIEWS:
        rm.render(data, view, '%s_%s.png' % (prefix, view))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.0)
