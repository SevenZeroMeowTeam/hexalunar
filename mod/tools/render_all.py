#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量渲染 模型/*.bbmodel 的 side/top/front 视图到 build/renders/。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_mesh as rm  # noqa: E402

SRC = '模型'
OUT = os.path.join('build', 'renders')


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(f for f in os.listdir(SRC) if f.endswith('.bbmodel'))
    for f in files:
        path = os.path.join(SRC, f)
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        base = os.path.splitext(f)[0]
        if not data.get('elements'):
            print('skip %s: no elements' % f)
            continue
        tex = rm.load_texture(data)
        if tex:
            tex.convert('RGB').save(os.path.join(OUT, base + '_tex.png'))
        for view in rm.VIEWS:
            rm.render(data, view, os.path.join(OUT, '%s_%s.png' % (base, view)))


if __name__ == '__main__':
    main()
