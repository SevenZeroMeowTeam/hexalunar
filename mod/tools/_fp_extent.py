#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""打印 geo 里每个骨骼（以及整体）的模型像素包围盒，用来判断「眼睛该站在哪儿」。

用法: python tools\\_fp_extent.py <geo.json> [--tz 1.8 --dz 1.4]
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main(argv):
    geo = argv[1]
    def val(name, default):
        return float(argv[argv.index(name) + 1]) if name in argv else default

    tz = val('--tz', 0.0)
    dz = val('--dz', 0.0)
    data = json.load(open(geo, encoding='utf-8'))
    g = data['minecraft:geometry'][0]
    lo = [1e9] * 3
    hi = [-1e9] * 3
    print('%-14s %-24s %-24s %s' % ('bone', 'x[min..max]', 'y[min..max]', 'z[min..max]'))
    for b in g['bones']:
        o = b.get('origin', [0, 0, 0])
        bl = [1e9] * 3
        bh = [-1e9] * 3
        for e in b.get('cubes', []):
            for i in range(3):
                a, c = o[i] + e['origin'][i], o[i] + e['origin'][i] + e['size'][i]
                bl[i] = min(bl[i], a, c)
                bh[i] = max(bh[i], a, c)
                lo[i] = min(lo[i], a, c)
                hi[i] = max(hi[i], a, c)
        if bl[0] > bh[0]:
            print('%-14s (无方块)' % b['name'])
            continue
        print('%-14s %7.2f..%7.2f        %7.2f..%7.2f        %7.2f..%7.2f'
              % (b['name'], bl[0], bh[0], bl[1], bh[1], bl[2], bh[2]))
    print('--- 整体 x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f（模型像素）'
          % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    # 眼睛在相机 z=0，模型点 p 的深度 = 0.72 − (tz + dz + p.z)/16
    print('--- 眼睛深度（格，正 = 在眼睛前方）: 最前端 z=%.2f → %.3f 格；最后端 z=%.2f → %.3f 格'
          % (lo[2], 0.72 - (tz + dz + lo[2]) / 16.0, hi[2], 0.72 - (tz + dz + hi[2]) / 16.0))


if __name__ == '__main__':
    main(sys.argv)
