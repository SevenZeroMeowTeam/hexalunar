#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把我的 geo 模型与 模型/akm.bbmodel（参考）并排渲染，便于找差距。

用法: python tools/akm_vs_ref.py
输出: build/vs_ref.png
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_view as gv  # noqa: E402
import render_mesh as rm  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

GEO = 'src/main/resources/assets/hexalunar_calamity/geo/akm.geo.json'
TEX = 'src/main/resources/assets/hexalunar_calamity/textures/models/akm_geo.png'
REF = '模型/akm.bbmodel'
SIZE = 900


def main():
    gv.render(GEO, TEX, 'build/_mine_side.png', yaw=-90, pitch=0, size=SIZE, zoom=1.0)
    gv.render(GEO, TEX, 'build/_mine_iso.png', yaw=-40, pitch=16, size=SIZE, zoom=1.0)
    data = json.load(open(REF, encoding='utf-8'))
    rm.render(data, 'side', 'build/_ref_side.png', size=SIZE, margin=30)
    rm.render(data, 'top', 'build/_ref_top.png', size=SIZE, margin=30)

    ims = [('我的模型 · 侧视', Image.open('build/_mine_side.png').convert('RGB')),
           ('参考模型 · 侧视', Image.open('build/_ref_side.png').convert('RGB')),
           ('我的模型 · 等轴', Image.open('build/_mine_iso.png').convert('RGB')),
           ('参考模型 · 俯视', Image.open('build/_ref_top.png').convert('RGB'))]
    w = max(i.width for _, i in ims)
    canvas = Image.new('RGB', (w * 2 + 10, ims[0][1].height * 2 + 60), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    for i, (tag, im) in enumerate(ims):
        x = (i % 2) * (w + 10)
        y = (i // 2) * (im.height + 30)
        canvas.paste(im, (x, y + 24))
        d.text((x + 6, y + 6), tag, fill=(0, 0, 0))
    canvas = canvas.resize((canvas.width // 2, canvas.height // 2))
    canvas.save('build/vs_ref.png')
    print('wrote build/vs_ref.png')


if __name__ == '__main__':
    main()
