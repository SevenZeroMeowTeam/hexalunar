#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 bbmodel 的绝对 UV 反推每个元素用到的贴图块索引，并抽样该块的颜色。"""
import base64
import io
import json
import sys

from PIL import Image

with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    data = json.load(fh)
res = float((data.get('resolution') or {}).get('width') or 16)
tex = None
for t in data.get('textures', []):
    src = t.get('source') or ''
    if src.startswith('data:image'):
        tex = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGB')
        break
print('texture', tex.size if tex else None, 'resolution', res)
for el in data.get('elements', []):
    tiles = {}
    for f in el['faces'].values():
        for k, uv in (f.get('uv') or {}).items():
            col = int(uv[0] // 1)
            row = int(uv[1] // 1)
            tiles[(col, row)] = tiles.get((col, row), 0) + 1
    items = []
    for (col, row), n in sorted(tiles.items()):
        if tex:
            cx = int((col + 0.5) * res / 16 * tex.size[0] / res * 1)
            px = min(tex.size[0] - 1, int((col + 0.5) * tex.size[0] / 16))
            py = min(tex.size[1] - 1, int((row + 0.5) * tex.size[1] / 16))
            c = tex.getpixel((px, py))
        else:
            c = None
        items.append('r%dc%d:%s(x%d)' % (row, col, c, n))
    print('  %-10s %s' % (el['name'], ' '.join(items)))
