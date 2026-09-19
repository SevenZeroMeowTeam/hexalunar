# -*- coding: utf-8 -*-
"""AWP 参考贴图占用分析：找出被 geo UV 引用的像素，并统计空闲区块。

用法: python tools\_awpfree.py
输出：占用图（每格 8x8 源像素）+ 可用的空闲矩形（>= 8x8）。
"""
import json
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '模型', 'AWP_Printstream_Minecraft')
GEO = json.load(open(os.path.join(SRC, 'bedrock', 'geometry.awp_printstream.json'),
                     encoding='utf-8'))['minecraft:geometry'][0]
TEX = Image.open(os.path.join(SRC, 'awp_printstream.png')).convert('RGBA')
W, H = TEX.size
print('texture %dx%d' % (W, H))

used = [[False] * W for _ in range(H)]


def box_uv(u0, v0, w, h, d):
    return [(u0 + d, v0, w, d), (u0 + d + w, v0, w, d),
            (u0, v0 + d, d, h), (u0 + d, v0 + d, w, h),
            (u0 + d + w, v0 + d, d, h), (u0 + d + w + d, v0 + d, w, h)]


total = 0
for b in GEO['bones']:
    for c in b.get('cubes', []):
        sx, sy, sz = c['size']
        for (u, v, w, h) in box_uv(c['uv'][0], c['uv'][1], sx, sy, sz):
            for yy in range(int(round(v)), int(round(v + h))):
                for xx in range(int(round(u)), int(round(u + w))):
                    if 0 <= xx < W and 0 <= yy < H:
                        used[yy][xx] = True
        total += 1
print('cubes =', total)

CELL = 8
rows = H // CELL
cols = W // CELL
print('\n占用图（%dx%d 格，每格 %d 像素；# = 有引用，. = 空闲）' % (cols, rows, CELL))
print('    ' + ''.join('%d' % (i % 10) for i in range(cols)))
for r in range(rows):
    line = ''
    for cidx in range(cols):
        cnt = 0
        for yy in range(r * CELL, (r + 1) * CELL):
            for xx in range(cidx * CELL, (cidx + 1) * CELL):
                if used[yy][xx]:
                    cnt += 1
        line += '#' if cnt > CELL * CELL * 0.5 else (':' if cnt else '.')
    print('%3d %s' % (r * CELL, line))

# 找整块空闲的 8x8 cell（用于新增材质色块）
print('\n完全空闲的 %dx%d 区块一维索引（左→右，上→下）:' % (CELL, CELL))
free = []
for r in range(rows):
    for cidx in range(cols):
        cnt = 0
        for yy in range(r * CELL, (r + 1) * CELL):
            for xx in range(cidx * CELL, (cidx + 1) * CELL):
                if used[yy][xx]:
                    cnt += 1
        if cnt == 0:
            free.append((cidx * CELL, r * CELL))
print('共 %d 个：%s' % (len(free), free[:80]))

print('\n各 8x8 区块平均色（前若干空闲块，用于确认可用）:')
for (x, y) in free[:16]:
    px = [TEX.getpixel((xx, yy)) for yy in range(y, y + CELL) for xx in range(x, x + CELL)]
    r = sum(p[0] for p in px) // len(px)
    g = sum(p[1] for p in px) // len(px)
    b = sum(p[2] for p in px) // len(px)
    a = sum(p[3] for p in px) // len(px)
    print('  (%3d,%3d) mean=(%3d,%3d,%3d,%3d)' % (x, y, r, g, b, a))
