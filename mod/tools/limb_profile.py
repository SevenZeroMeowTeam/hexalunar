#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""量弓臂的走向：按 |X| 分箱统计网格（弓臂区域）的 Y / Z 分布。

用法: python tools/limb_profile.py <aligned.bbmodel> [...]
"""
import json
import sys

BINS = 12


def profile(path, xmin=1.6):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    vs = [v for el in data.get('elements', []) for v in el['vertices'].values()]
    sel = [v for v in vs if abs(v[0]) >= xmin]
    if not sel:
        print('%s: |X|>=%.1f 没有顶点' % (path, xmin))
        return
    print('%s  弓臂顶点 %d' % (path, len(sel)))
    xmax = max(abs(v[0]) for v in sel)
    step = (xmax - xmin) / BINS
    print('  %-14s %5s %8s %8s %8s %8s %8s %8s' % ('|X| 区间', '顶点', 'Ymin', 'Ymax', 'Y均', 'Zmin', 'Zmax', 'Z均'))
    for b in range(BINS):
        a0 = xmin + b * step
        a1 = a0 + step
        s = [v for v in sel if (a0 <= abs(v[0]) < a1) or (b == BINS - 1 and abs(v[0]) >= a1)]
        if not s:
            print('  %-14s %5d' % ('%.2f..%.2f' % (a0, a1), 0))
            continue
        print('  %-14s %5d %8.2f %8.2f %8.2f %8.2f %8.2f %8.2f' % (
            '%.2f..%.2f' % (a0, a1), len(s),
            min(v[1] for v in s), max(v[1] for v in s), sum(v[1] for v in s) / len(s),
            min(v[2] for v in s), max(v[2] for v in s), sum(v[2] for v in s) / len(s)))


if __name__ == '__main__':
    for p in sys.argv[1:]:
        profile(p)
