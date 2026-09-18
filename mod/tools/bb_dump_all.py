#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把一个 bbmodel 压成紧凑摘要文本（去掉贴图 base64），方便读比例。

用法: python tools/bb_dump_all.py <model.bbmodel> [out.txt]
"""
import json
import sys
import os


def num(v):
    if isinstance(v, (int, float)):
        f = float(v)
        return ('%g' % f)
    return str(v)


def vec(v):
    if not v:
        return '-'
    return '[' + ','.join(num(x) for x in v) + ']'


def main(path, out=None):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    elems = {}
    for e in data.get('elements', []):
        elems[e.get('uuid')] = e
    lines = []
    lines.append('FILE %s  size=%d bytes' % (os.path.basename(path), os.path.getsize(path)))
    lines.append('name=%s  format=%s  res=%s  tex_w/h=%s/%s  box_uv=%s' % (
        data.get('name'),
        (data.get('meta') or {}).get('format_version') or data.get('model_format'),
        data.get('resolution'),
        data.get('texture_width'), data.get('texture_height'), data.get('box_uv')))
    lines.append('elements=%d  outliner_roots=%d  animations=%s' % (
        len(data.get('elements', [])), len(data.get('outliner', [])),
        [a.get('name') for a in data.get('animations', [])]))
    ds = data.get('display_settings') or {}
    lines.append('display_slots=%s' % (sorted(ds.keys()) if isinstance(ds, dict) else ds))
    for tex in data.get('textures', []):
        src = tex.get('source') or ''
        lines.append('  tex %s  uv=%sx%s  src_bytes=%d' % (
            tex.get('name'), tex.get('uv_width'), tex.get('uv_height'), len(src)))
    lines.append('--- hierarchy ---')

    def walk(node, depth):
        pad = '  ' * depth
        if isinstance(node, str):
            e = elems.get(node)
            if e is None:
                lines.append('%s??? %s' % (pad, node))
                return
            f, t = e.get('from'), e.get('to')
            size = None
            if f and t:
                size = [abs(t[i] - f[i]) for i in range(3)]
            rot = e.get('rotation')
            lines.append('%s cube "%s" from=%s to=%s size=%s rot=%s origin=%s inflate=%s' % (
                pad, e.get('name'), vec(f), vec(t),
                '[' + ','.join(num(s) for s in size) + ']' if size else '-',
                vec(rot) if rot else '-', vec(e.get('origin')), e.get('inflate', 0)))
            return
        name = node.get('name')
        lines.append('%s GROUP "%s" origin=%s rot=%s' % (
            pad, name, vec(node.get('origin')), vec(node.get('rotation')) if node.get('rotation') else '-'))
        for k in node.get('children') or []:
            walk(k, depth + 1)

    for node in data.get('outliner', []):
        walk(node, 1)

    # 未挂到 outliner 的 cube
    used = set()

    def collect(node):
        if isinstance(node, str):
            used.add(node)
        else:
            for k in node.get('children') or []:
                collect(k)
    for node in data.get('outliner', []):
        collect(node)
    leftovers = [e for e in data.get('elements', []) if e.get('uuid') not in used]
    if leftovers:
        lines.append('--- unparented cubes (%d) ---' % len(leftovers))
        for e in leftovers:
            lines.append('  cube "%s" from=%s to=%s' % (e.get('name'), vec(e.get('from')), vec(e.get('to'))))

    # 总体包围盒
    mins = [1e9] * 3
    maxs = [-1e9] * 3
    for e in data.get('elements', []):
        f, t = e.get('from'), e.get('to')
        if not f or not t:
            continue
        for i in range(3):
            mins[i] = min(mins[i], f[i], t[i])
            maxs[i] = max(maxs[i], f[i], t[i])
    if mins[0] < 1e8:
        lines.append('--- bounds ---')
        lines.append('  min=%s max=%s size=%s' % (
            vec(mins), vec(maxs), vec([maxs[i] - mins[i] for i in range(3)])))

    text = '\n'.join(lines)
    if out:
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(text)
        print('wrote', out, len(text), 'chars')
    else:
        print(text)


if __name__ == '__main__':
    o = sys.argv[2] if len(sys.argv) > 2 else None
    main(sys.argv[1], o)
