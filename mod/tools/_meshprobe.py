# -*- coding: utf-8 -*-
"""体检一个 Blockbench **mesh** 模型（v2 十字弩）：每个网格的名字/顶点数/包围盒 + 贴图导出。

用法: python tools\\_meshprobe.py <bbmodel> [out_dir]
"""
import base64
import io
import json
import os
import re
import sys


def main(argv):
    path = argv[1]
    outdir = argv[2] if len(argv) > 2 else r'D:\做一个_Minecraft_1_20_1_的_F\mod\build\v2mesh'
    os.makedirs(outdir, exist_ok=True)
    data = json.loads(io.open(path, encoding='utf-8').read())
    print('文件: %s  (%d 字节)' % (path, os.path.getsize(path)))
    print('format=%s  resolution=%s' % (data.get('meta', {}).get('format_version'),
                                        data.get('resolution')))

    # 贴图
    for i, t in enumerate(data.get('textures', [])):
        src = t.get('source', '')
        m = re.match(r'data:image/(\w+);base64,(.*)$', src, re.S)
        name = t.get('name') or ('tex%d' % i)
        if m:
            raw = base64.b64decode(m.group(2))
            out = os.path.join(outdir, '%s.png' % name)
            with open(out, 'wb') as f:
                f.write(raw)
            print('贴图[%d] %s  %s  -> %s (%d 字节)' % (i, name, t.get('uv_width'), out, len(raw)))
        else:
            print('贴图[%d] %s  source=%.40s...' % (i, name, src))

    elems = {e['uuid']: e for e in data.get('elements', [])}
    print('元素 %d 个' % len(elems))

    # 每个元素：顶点包围盒
    total_verts = 0
    gmin = [1e9] * 3
    gmax = [-1e9] * 3
    info = []
    for uuid, e in elems.items():
        verts = e.get('vertices', {})
        pts = list(verts.values())
        total_verts += len(pts)
        if not pts:
            continue
        mn = [min(p[i] for p in pts) for i in range(3)]
        mx = [max(p[i] for p in pts) for i in range(3)]
        for i in range(3):
            gmin[i] = min(gmin[i], mn[i])
            gmax[i] = max(gmax[i], mx[i])
        info.append((e.get('name'), len(pts), mn, mx, uuid, e.get('origin'), e.get('rotation')))
    print('顶点总数 %d' % total_verts)
    print('整体包围盒 min=%s max=%s  尺寸=%s' % (
        [round(v, 2) for v in gmin], [round(v, 2) for v in gmax],
        [round(gmax[i] - gmin[i], 2) for i in range(3)]))
    print()
    print('%-22s %5s  %-26s %-26s %s' % ('名字', '顶点', 'min', 'max', 'origin/rotation'))
    for name, n, mn, mx, _uuid, origin, rot in sorted(info, key=lambda t: (t[2][2], t[0] or '')):
        print('%-22s %5d  %-26s %-26s %s / %s' % (
            name, n, [round(v, 2) for v in mn], [round(v, 2) for v in mx],
            [round(v, 2) for v in origin] if origin else None,
            [round(v, 1) for v in rot] if rot else None))

    print()
    print('outliner:', json.dumps(data.get('outliner', []), ensure_ascii=False)[:600])


if __name__ == '__main__':
    main(sys.argv)
