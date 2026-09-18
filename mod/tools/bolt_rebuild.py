# -*- coding: utf-8 -*-
"""重建十字弩的弩箭（crossbow.geo.json 的 bolt 骨骼）+ 补画贴图。

参考 模型/弩箭.bbmodel：细长箭杆 + 锥形箭头 + 三片尾羽。
沿用原 bolt 骨骼的枢轴/朝向（箭尖 = -Z，箭身躺在弩身导轨上沿 Y=1.35）。
新增的近/远面 UV 从 crossbow_geo.png 里挑空闲的 8px 格并重绘。
"""
import json
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'geo', 'crossbow.geo.json')
TEX = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'textures', 'models', 'crossbow_geo.png')
CELL = 8

geo = json.load(open(GEO, encoding='utf-8'))
g = geo['minecraft:geometry'][0]

# ---- 1. 统计已占用的 UV 格 ----
used = set()
for b in g['bones']:
    for c in b.get('cubes', []):
        for spec in (c.get('uv') or {}).values():
            u, v = spec['uv']
            w, h = spec['uv_size']
            for yy in range(int(v) // CELL, (int(v + h) + CELL - 1) // CELL):
                for xx in range(int(u) // CELL, (int(u + w) + CELL - 1) // CELL):
                    used.add((xx, yy))
print('occupied cells:', len(used))

free = []
for yy in range(64):
    for xx in range(64):
        if (xx, yy) not in used:
            free.append((xx, yy))
print('free cells:', len(free))

img = Image.open(TEX).convert('RGBA')
dr = ImageDraw.Draw(img)
alloc = {}


def take(name):
    if len(free) == 0:
        raise RuntimeError('no free uv cell')
    c = free.pop(0)
    alloc[name] = (c[0] * CELL, c[1] * CELL)
    return alloc[name]


def paint(name, rgb, kind='flat'):
    x, y = alloc[name]
    for j in range(CELL):
        for i in range(CELL):
            f = 1.0 - 0.10 * (abs(i - 3.5) / 3.5) - 0.06 * (abs(j - 3.5) / 3.5)
            c = (int(rgb[0] * f), int(rgb[1] * f), int(rgb[2] * f), 255)
            img.putpixel((x + i, y + j), c)
    if kind == 'steel':
        for i in range(CELL):
            dr.line([(x, y + i), (x + CELL - 1, y + i)], fill=(int(rgb[0] * 1.12), int(rgb[1] * 1.12),
                                                               int(rgb[2] * 1.12), 255))
    elif kind == 'vane':
        for i in range(1, CELL - 1):
            dr.line([(x + i, y + 1), (x + i, y + CELL - 2)],
                    fill=(int(rgb[0] * 0.80), int(rgb[1] * 0.80), int(rgb[2] * 0.80), 255))
        dr.line([(x, y), (x + CELL - 1, y)], fill=(255, 255, 255, 255))


CARBON = (38, 40, 43)
STEELP = (150, 153, 158)
VANE = (222, 96, 44)
NOCK = (60, 62, 66)

for nm, col, kd in (('shaft', CARBON, 'flat'), ('point', STEELP, 'steel'),
                    ('vane', VANE, 'vane'), ('nock', NOCK, 'flat')):
    take(nm)
    paint(nm, col, kd)

for b in g['bones']:
    if b['name'] == 'bolt':
        print('old bolt cubes:', len(b['cubes']))
        break


def cube(origin, size, tile):
    u, v = alloc[tile]
    face = {'uv': [u, v], 'uv_size': [CELL, CELL]}
    return {'origin': [round(origin[0], 3), round(origin[1], 3), round(origin[2], 3)],
            'size': [round(size[0], 3), round(size[1], 3), round(size[2], 3)],
            'uv': {k: dict(face) for k in ('north', 'south', 'east', 'west', 'up', 'down')}}


cubes = [
    # 箭杆（碳素）
    cube((-0.20, 1.38, -8.10), (0.40, 0.40, 9.10), 'shaft'),
    # 锥形箭头（三段收尖）
    cube((-0.30, 1.28, -8.70), (0.60, 0.60, 0.60), 'point'),
    cube((-0.21, 1.37, -9.05), (0.42, 0.42, 0.35), 'point'),
    cube((-0.10, 1.48, -9.35), (0.20, 0.20, 0.30), 'point'),
    # 尾端箭尾（卡弦）
    cube((-0.17, 1.41, 1.00), (0.34, 0.34, 0.30), 'nock'),
    # 三片尾羽（绕 Z 轴 120° 均布）
    {'origin': [0.20, 1.52, -0.95], 'size': [0.62, 0.12, 1.90],
     'rotation': [0.0, 0.0, 0.0], 'pivot': [0.0, 1.58, 0.0],
     'uv': {k: {'uv': list(alloc['vane']), 'uv_size': [CELL, CELL]} for k in
            ('north', 'south', 'east', 'west', 'up', 'down')}},
    {'origin': [0.20, 1.52, -0.95], 'size': [0.62, 0.12, 1.90],
     'rotation': [0.0, 0.0, 120.0], 'pivot': [0.0, 1.58, 0.0],
     'uv': {k: {'uv': list(alloc['vane']), 'uv_size': [CELL, CELL]} for k in
            ('north', 'south', 'east', 'west', 'up', 'down')}},
    {'origin': [0.20, 1.52, -0.95], 'size': [0.62, 0.12, 1.90],
     'rotation': [0.0, 0.0, 240.0], 'pivot': [0.0, 1.58, 0.0],
     'uv': {k: {'uv': list(alloc['vane']), 'uv_size': [CELL, CELL]} for k in
            ('north', 'south', 'east', 'west', 'up', 'down')}},
]

for b in g['bones']:
    if b['name'] == 'bolt':
        b['cubes'] = cubes

with open(GEO, 'w', encoding='utf-8') as fh:
    json.dump(geo, fh, ensure_ascii=False, separators=(',', ':'))
img.save(TEX)
print('new bolt cubes:', len(cubes))
print('wrote', GEO, os.path.getsize(GEO))
print('wrote', TEX, os.path.getsize(TEX))
print('alloc', alloc)
