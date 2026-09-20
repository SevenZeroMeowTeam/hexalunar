# -*- coding: utf-8 -*-
"""TaCZ 参考配置探针：读 build/tacz_kar98/ 下导出的 json，打印骨骼 / 定位组 / 配件标签。

用法:
  python tools\\_tacz_probe.py bones build\\tacz_kar98\\kar98_geo.json [过滤词]
  python tools\\_tacz_probe.py tags  build\\tacz_kar98\\kar98_allow.json
  python tools\\_tacz_probe.py pivot build\\tacz_kar98\\kar98_geo.json idle_view iron_view
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path_of(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def load(p):
    return json.load(open(path_of(p), encoding='utf-8'))


def geo_of(g):
    geo = g.get('minecraft:geometry')
    if isinstance(geo, dict):
        return list(geo.values())[0]
    return geo[0]


def bones(g, want):
    gg = geo_of(g)
    out = []
    for b in gg.get('bones', []):
        name = b.get('name')
        if want and want not in (name or ''):
            continue
        piv = b.get('pivot')
        n = len(b.get('cubes', []) or [])
        parent = b.get('parent')
        out.append((name, parent, piv, n))
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    cmd, src = argv[1], argv[2]
    g = load(src)
    if cmd == 'bones':
        want = argv[3] if len(argv) > 3 else ''
        rows = bones(g, want)
        print('%-26s %-26s %-28s %s' % ('bone', 'parent', 'pivot', 'cubes'))
        for name, parent, piv, n in rows:
            print('%-26s %-26s %-28s %d' % (name, parent or '-',
                                            ','.join('%.4f' % v for v in piv) if piv else '-', n))
        print('共 %d 根（过滤 %r）' % (len(rows), want))
    elif cmd == 'pivot':
        names = set(argv[3:])
        for name, parent, piv, n in bones(g, ''):
            if name in names:
                print('%-26s pivot = %s' % (name, piv))
    elif cmd == 'tags':
        for k, v in g.items():
            print('%-28s %s' % (k, json.dumps(v, ensure_ascii=False)[:200]))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
