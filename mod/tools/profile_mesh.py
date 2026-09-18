#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""沿长轴分箱统计 mesh 的剖面尺寸，用来确定机身/弓臂/握把/枪托的实际范围。"""
import json
import sys


def main(path, axis=0, bins=16):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    verts = list(data['elements'][0]['vertices'].values())
    names = ['X', 'Y', 'Z']
    vals = [v[axis] for v in verts]
    lo, hi = min(vals), max(vals)
    print('axis %s range %.2f .. %.2f' % (names[axis], lo, hi))
    step = (hi - lo) / bins
    other = [i for i in range(3) if i != axis]
    print('%-6s %-8s %8s %10s %10s %10s %10s %8s' % (
        'bin', 'range', 'verts', '%s min' % names[other[0]], '%s max' % names[other[0]],
        '%s min' % names[other[1]], '%s max' % names[other[1]], 'thick'))
    for b in range(bins):
        a = lo + b * step
        z = lo + (b + 1) * step
        sel = [v for v in verts if a <= v[axis] < z or (b == bins - 1 and v[axis] == hi)]
        if not sel:
            print('%-6d %-8s %8d' % (b, '%.2f..%.2f' % (a, z), 0))
            continue
        o0 = [v[other[0]] for v in sel]
        o1 = [v[other[1]] for v in sel]
        print('%-6d %-8s %8d %10.2f %10.2f %10.2f %10.2f %8.2f' % (
            b, '%.2f..%.2f' % (a, z), len(sel), min(o0), max(o0), min(o1), max(o1),
            max(o1) - min(o1)))


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
