#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""打印 bbmodel 里 element 的几何信息（mesh 顶点/面/包围盒）。"""
import json
import sys
import os


def bbox(verts):
    if not verts:
        return None
    if isinstance(verts, dict):
        verts = list(verts.values())
    if not verts:
        return None
    dim = len(verts[0]) if isinstance(verts[0], (list, tuple)) else 3
    mins = [1e18] * dim
    maxs = [-1e18] * dim
    for v in verts:
        for i in range(dim):
            mins[i] = min(mins[i], v[i])
            maxs[i] = max(maxs[i], v[i])
    return mins, maxs


def main(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    print('==', os.path.basename(path), os.path.getsize(path), 'bytes')
    print('format_version:', (data.get('meta') or {}).get('format_version'),
          ' model_format:', data.get('model_format'),
          ' name:', data.get('name'))
    for key in sorted(data.keys()):
        if key in ('elements', 'textures', 'outliner'):
            continue
        v = data[key]
        s = json.dumps(v, ensure_ascii=False)
        print('  key %-22s = %s' % (key, s[:160]))
    for e in data.get('elements', []):
        print('  ELEMENT type=%s name=%s' % (e.get('type'), e.get('name')))
        for k, v in e.items():
            if k in ('vertices', 'faces', 'uv'):
                continue
            print('     %-14s = %s' % (k, json.dumps(v, ensure_ascii=False)[:200]))
        verts = e.get('vertices') or []
        faces = e.get('faces') or {}
        print('     vertices=%d  faces=%d' % (len(verts), len(faces)))
        bb = bbox(verts)
        if bb:
            mins, maxs = bb
            print('     bbox min=%s max=%s size=%s' % (
                [round(x, 4) for x in mins], [round(x, 4) for x in maxs],
                [round(maxs[i] - mins[i], 4) for i in range(len(mins))]))
        # uv 抽样
        for fid, f in list(faces.items())[:3]:
            print('     face', fid, json.dumps(f, ensure_ascii=False)[:220])
    for t in data.get('textures', []):
        print('  TEX name=%s uv=%sx%s uv_size=%s source_len=%d' % (
            t.get('name'), t.get('uv_width'), t.get('uv_height'),
            (t.get('uv_width'), t.get('uv_height')), len(t.get('source') or '')))


if __name__ == '__main__':
    for p in sys.argv[1:]:
        main(p)
