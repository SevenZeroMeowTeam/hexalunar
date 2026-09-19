# -*- coding: utf-8 -*-
"""列出仓库里所有 .bbmodel（含大小）+ 报告 crossbow_v2.bbmodel 的内容结构。

用法: python tools\\_bbprobe2.py [name_substr]
"""
import io
import json
import os
import sys

ROOT = r'D:\做一个_Minecraft_1_20_1_的_F'


def main(argv):
    want = argv[1] if len(argv) > 1 else 'crossbow_v2'
    found = []
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'build', 'run', 'logs', 'node_modules')]
        for f in files:
            if f.lower().endswith('.bbmodel'):
                p = os.path.join(dirpath, f)
                found.append((os.path.getsize(p), p))
    found.sort()
    print('== %d 个 bbmodel ==' % len(found))
    for size, p in found:
        mark = ' <== 目标' if want.lower() in os.path.basename(p).lower() else ''
        print('%9d  %s%s' % (size, p, mark))
        if mark:
            report(p)


def report(path):
    data = json.loads(io.open(path, encoding='utf-8').read())
    print('  顶层键: %s' % sorted(data.keys()))
    print('  format=%s  model_format=%s  visible_box=%s' % (
        data.get('meta', {}).get('format_version'), data.get('model_format'),
        data.get('visible_box')))
    texs = data.get('textures', [])
    print('  贴图 %d 张: %s' % (len(texs), [t.get('name') for t in texs]))
    res = data.get('resolution', {})
    print('  resolution=%s' % res)
    elems = data.get('elements', [])
    kinds = {}
    cube_total = 0
    mesh_verts = 0
    for e in elems:
        t = e.get('type', 'cube')
        kinds[t] = kinds.get(t, 0) + 1
        if t == 'cube':
            cube_total += 1
        if 'vertices' in e:
            mesh_verts += len(e['vertices'])
    print('  elements=%d  类型统计=%s  网格顶点总数=%d' % (len(elems), kinds, mesh_verts))
    # 骨骼/分组
    def walk(items, depth):
        for it in items:
            if isinstance(it, str):
                print('    %s(裸 uuid) %s' % ('  ' * depth, it))
                continue
            n = it.get('name')
            origin = it.get('origin')
            children = it.get('children', [])
            print('    %s%s  origin=%s  children=%d' % ('  ' * depth, n, origin, len(children)))
            walk(children, depth + 1)
    print('  outliner:')
    walk(data.get('outliner', []), 1)


if __name__ == '__main__':
    main(sys.argv)
