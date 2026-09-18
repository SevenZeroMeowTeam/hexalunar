#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""解析 .bbmodel，打印结构概要（格式 / 分辨率 / 骨骼树 / 立方体统计 / 贴图）。"""
import json
import sys
import base64


def walk(node, groups, cubes, depth=0, lines=None):
    if lines is None:
        lines = []
    if isinstance(node, str):
        return
    if isinstance(node, dict):
        kids = node.get('children') or []
        name = node.get('name', '?')
        origin = node.get('origin')
        rot = node.get('rotation')
        lines.append('%s%s  pivot=%s rot=%s  cubes=%d' % (
            '  ' * depth, name, origin, rot, len(kids) and 0 or 0))
        for k in kids:
            if isinstance(k, str):
                cubes.append(k)
            else:
                walk(k, groups, cubes, depth + 1, lines)
        groups.append(name)
    return lines


def main(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    meta = data.get('meta', {})
    print('file      :', path)
    print('name      :', data.get('name'))
    print('meta      :', json.dumps(meta, ensure_ascii=False))
    print('resolution:', data.get('resolution'))
    print('texture_w/h:', data.get('texture_width'), data.get('texture_height'))
    print('elements  :', len(data.get('elements', [])))
    outliner = data.get('outliner', [])
    print('outliner roots:', len(outliner))
    print('animations:', [a.get('name') for a in data.get('animations', [])])
    print('controllers:', [
        (a.get('name'), len(a.get('animators', [])))
        for a in data.get('animation_controllers', [])
    ] if data.get('animation_controllers') else None)
    print('display_settings keys:', list((data.get('display_settings') or {}).keys()))
    print('--- outliner tree ---')
    for node in outliner:
        if isinstance(node, str):
            cube = next((e for e in data.get('elements', []) if e.get('uuid') == node), None)
            print('  [cube] %s' % (cube.get('name') if cube else node))
        else:
            walk(node, [], [])
            for line in []:
                pass
    print('--- textures ---')
    for tex in data.get('textures', []):
        src = tex.get('source', '') or ''
        size = len(src)
        head = src[:32]
        print('  %s  %sx%s  bytes=%d  head=%s' % (
            tex.get('name'), tex.get('uv_width'), tex.get('uv_height'), size, head))
    print('--- elements sample ---')
    for e in data.get('elements', [])[:8]:
        print('  %s from=%s to=%s rot=%s' % (
            e.get('name'), e.get('from'), e.get('to'), e.get('rotation')))


if __name__ == '__main__':
    main(sys.argv[1])
