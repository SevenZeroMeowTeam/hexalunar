# -*- coding: utf-8 -*-
"""看一眼 `模型/ammo.bbmodel`（Blockbench 工程）里都有些什么：元素尺寸 / 贴图 / 分辨率。

用法::  python tools/_ammo_probe.py [路径]
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MOD, '模型', 'ammo.bbmodel')
    d = json.load(io.open(path, encoding='utf-8'))
    print('model_format=%s  name=%s' % (d.get('model_format'), d.get('name')))
    res = d.get('resolution') or {}
    print('resolution: %s' % res)
    texs = d.get('textures') or []
    print('textures: %s' % [t.get('name') for t in texs])
    out = []
    def walk(elems, depth, out):
        for e in elems:
            if e.get('type') == 'cube' and e.get('visibility', True):
                f, t = e.get('from', [0, 0, 0]), e.get('to', [0, 0, 0])
                size = [round(t[i] - f[i], 2) for i in range(3)]
                out.append('%s%-14s from=%s size=%s' %
                           ('  ' * depth, e.get('name', '?'),
                            [round(v, 2) for v in f], size))
            if e.get('children'):
                walk(e['children'], depth + 1, out)
    walk(d.get('elements') or [], 0, out)
    print('cubes=%d' % len(out))
    for ln in out[:40]:
        print(ln)


if __name__ == '__main__':
    main()
