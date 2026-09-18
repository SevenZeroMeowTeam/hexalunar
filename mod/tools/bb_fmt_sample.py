#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""打印 bbmodel 里 mesh 元素与面/UV 的确切结构（用于复刻格式）。"""
import json
import sys

src = sys.argv[1]
with open(src, 'r', encoding='utf-8') as fh:
    data = json.load(fh)
el = data['elements'][0]
out = {}
out['element_keys'] = list(el.keys())
out['element_head'] = {k: v for k, v in el.items() if k not in ('vertices', 'faces')}
vk = list(el['vertices'].keys())[:3]
out['vertices_sample'] = {k: el['vertices'][k] for k in vk}
fk = list(el['faces'].keys())[:3]
out['faces_sample'] = {k: el['faces'][k] for k in fk}
out['textures'] = [{k: (v if k != 'source' else ('<%d bytes>' % len(v or '')))
                    for k, v in t.items()} for t in data.get('textures', [])]
out['top_level_keys'] = list(data.keys())
out['meta'] = data.get('meta')
out['visible_box'] = data.get('visible_box')
with open('build/bb_format_sample.json', 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print('ok')
