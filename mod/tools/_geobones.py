"""列出 geo 里每根骨骼的 pivot / 父级 / 方块数与包围盒，用于判断「动哪根骨骼最省事」。

用法: python tools\_geobones.py <geo.json> [骨骼名]     # 给了骨骼名就逐个方块列出来
"""
import io
import json
import sys


def main(argv):
    with io.open(argv[1], encoding='utf-8') as fh:
        geo = json.load(fh)
    g = geo['minecraft:geometry'][0]
    only = argv[2] if len(argv) > 2 else None
    print('format=%s  texture=%s' % (g.get('description', {}).get('identifier'), g.get('description', {}).get('texture_size')))
    tot = 0
    for b in g['bones']:
        cubes = b.get('cubes') or []
        tot += len(cubes)
        if cubes:
            ox = [min(c['origin'][i] for c in cubes) for i in range(3)]
            ex = [max(c['origin'][i] + c['size'][i] for c in cubes) for i in range(3)]
            box = ' 盒 %s .. %s' % ([round(v, 2) for v in ox], [round(v, 2) for v in ex])
        else:
            box = ''
        extra = ' '.join(k for k in ('rotation', 'position', 'inflate') if k in b)
        print('%-14s parent=%-14s pivot=%-22s cubes=%3d%s %s' % (
            b['name'], b.get('parent', '-'), [round(v, 2) for v in b['pivot']], len(cubes), box, extra))
        if only and b['name'] == only:
            for i, c in enumerate(cubes):
                o, s = c['origin'], c['size']
                print('    [%2d] X %6.2f..%6.2f  Y %6.2f..%6.2f  Z %6.2f..%6.2f  rot=%s'
                      % (i, o[0], o[0] + s[0], o[1], o[1] + s[1], o[2], o[2] + s[2],
                         c.get('rotation')))
    print('合计 %d 方块' % tot)


if __name__ == '__main__':
    main(sys.argv)
