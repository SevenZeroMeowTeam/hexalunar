#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把若干 bbmodel 的 top / side 视图拼成一张网格图，方便一眼看朝向。

用法: python tools/views_grid.py <out.png> <top|side|front> <model.bbmodel> [...]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw  # noqa: E402
import render_mesh as rm  # noqa: E402


def bake(data):
    """把元素自身的 rotation 烘进顶点（渲染器只看原始顶点）。"""
    import bb_north as bn
    for el in data.get('elements', []):
        if any(abs(x) > 1e-9 for x in (el.get('rotation') or [0, 0, 0])):
            o = tuple(el.get('origin') or [0, 0, 0])
            for k, v in list(el['vertices'].items()):
                el['vertices'][k] = list(bn.elem_local_to_world(el, tuple(v)))
            el['rotation'] = [0, 0, 0]
            el['origin'] = [0, 0, 0]
    return data


def main(out, view, paths):
    panels = []
    for p in paths:
        with open(p, 'r', encoding='utf-8') as fh:
            data = bake(json.load(fh))
        tmp = 'build/views/_tmp.png'
        os.makedirs('build/views', exist_ok=True)
        rm.render(data, view, tmp, size=520, margin=24)
        im = Image.open(tmp).convert('RGB')
        panels.append((os.path.basename(p).replace('.bbmodel', ''), im))
    w = max(im.width for _, im in panels)
    h = max(im.height for _, im in panels)
    cols = min(3, len(panels))
    rows = (len(panels) + cols - 1) // cols
    canvas = Image.new('RGB', (w * cols + 10 * (cols - 1), h * rows + 30 * rows), (235, 235, 230))
    d = ImageDraw.Draw(canvas)
    for i, (name, im) in enumerate(panels):
        cx = (i % cols) * (w + 10)
        cy = (i // cols) * (h + 30)
        canvas.paste(im, (cx, cy + 22))
        d.text((cx + 6, cy + 6), '%s  [%s]' % (name, view), fill=(0, 0, 0))
    canvas.save(out)
    print('wrote %s  (%d panels, %dx%d)' % (out, len(panels), canvas.width, canvas.height))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
