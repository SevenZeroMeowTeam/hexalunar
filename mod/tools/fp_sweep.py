#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""扫描 display 平移，拼成对比图，用来定第一人称手持位置。"""
import io
import json
import os
import subprocess
import sys

from PIL import Image

GEO = 'src/main/resources/assets/hexalunar_calamity/geo/compound_bow.geo.json'
TEX = 'src/main/resources/assets/hexalunar_calamity/textures/models/compound_bow_geo.png'
MODEL = 'src/main/resources/assets/hexalunar_calamity/models/item/compound_bow.json'
TMP = 'build/_sweep_item.json'

ROT = [-180.0, -34.232, -180.0]
CANDS = [
    ('s0.68 t(2,2.1)', ROT, [2.0, 2.1, 6.5], 0.68),
    ('s0.68 t(5,2.1)', ROT, [5.0, 2.1, 6.5], 0.68),
    ('s0.68 t(2,-1.0)', ROT, [2.0, -1.0, 6.5], 0.68),
    ('s0.68 t(5,-1.0)', ROT, [5.0, -1.0, 6.5], 0.68),
    ('s0.55 t(2,2.1)', ROT, [2.0, 2.1, 6.5], 0.55),
    ('s0.80 t(2,2.1)', ROT, [2.0, 2.1, 6.5], 0.80),
]

base = json.load(io.open(MODEL, encoding='utf-8'))
tiles = []
for label, rot, trans, sc in CANDS:
    d = json.load(io.open(MODEL, encoding='utf-8'))
    for slot in ('firstperson_righthand', 'firstperson_lefthand'):
        d['display'][slot] = {'rotation': rot, 'translation': trans, 'scale': [sc] * 3}
    with io.open(TMP, 'w', encoding='utf-8') as fh:
        json.dump(d, fh)
    out = 'build/_sweep_%d.png' % len(tiles)
    subprocess.run([sys.executable, 'tools/geo_item_view.py', GEO, TEX, out,
                    '--cam', 'fp', '--display', TMP], check=True,
                   stdout=subprocess.DEVNULL)
    tiles.append((label, out))

S = 390
sheet = Image.new('RGB', (S * 3, S * 2), (255, 255, 255))
from PIL import ImageDraw
dr = ImageDraw.Draw(sheet)
for i, (label, path) in enumerate(tiles):
    im = Image.open(path).convert('RGB').resize((S, S))
    x, y = (i % 3) * S, (i // 3) * S
    sheet.paste(im, (x, y))
    dr.rectangle([x, y, x + S - 1, y + 18], fill=(0, 0, 0))
    dr.text((x + 4, y + 4), label, fill=(255, 255, 255))
sheet.save('build/fp_sweep.png')
os.remove(TMP)
print('written build/fp_sweep.png')
