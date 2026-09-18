#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""看 .bbmodel 里元素的结构细节（mesh 顶点 / 面 / 贴图）。"""
import json
import sys


def main(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    for i, e in enumerate(data.get('elements', [])):
        print('=== element %d ===' % i)
        print('keys:', sorted(e.keys()))
        print('type:', e.get('type'), 'name:', e.get('name'))
        print('uuid:', e.get('uuid'))
        for k, v in e.items():
            if k in ('vertices', 'faces'):
                print('%s: (dict) len=%d' % (k, len(v) if hasattr(v, '__len__') else -1))
            else:
                print('%s: %s' % (k, json.dumps(v, ensure_ascii=False)[:200]))
        verts = e.get('vertices') or {}
        sample = list(verts.items())[:5]
        for k, v in sample:
            print('   v %s -> %s' % (k, json.dumps(v)))
        faces = e.get('faces') or {}
        fsample = list(faces.items())[:3]
        for k, v in fsample:
            print('   f %s -> %s' % (k, json.dumps(v)[:300]))
        # bbox
        if verts:
            xs = [v[0] for v in verts.values()]
            ys = [v[1] for v in verts.values()]
            zs = [v[2] for v in verts.values()]
            print('   bbox X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f' % (
                min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
        print('   faces count:', len(faces))
        print('   texture:', e.get('texture'))
        print('   visibility:', e.get('visibility'))


if __name__ == '__main__':
    main(sys.argv[1])
