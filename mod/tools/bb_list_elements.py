#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""列出 bbmodel 每个元素的名称、包围盒、顶点/面数。"""
import json
import sys

with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    data = json.load(fh)
lo_all = [1e9] * 3
hi_all = [-1e9] * 3
print('file:', sys.argv[1], ' elements:', len(data.get('elements', [])))
for el in data.get('elements', []):
    vs = list(el['vertices'].values())
    lo = [min(v[i] for v in vs) for i in range(3)]
    hi = [max(v[i] for v in vs) for i in range(3)]
    for i in range(3):
        lo_all[i] = min(lo_all[i], lo[i])
        hi_all[i] = max(hi_all[i], hi[i])
    print('  %-10s verts=%4d faces=%4d  X[%7.2f..%7.2f] Y[%6.2f..%6.2f] Z[%7.2f..%7.2f]' % (
        el['name'], len(vs), len(el['faces']), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
print('  TOTAL      X[%.2f..%.2f] Y[%.2f..%.2f] Z[%.2f..%.2f]  size=%.2f x %.2f x %.2f' % (
    lo_all[0], hi_all[0], lo_all[1], hi_all[1], lo_all[2], hi_all[2],
    hi_all[0] - lo_all[0], hi_all[1] - lo_all[1], hi_all[2] - lo_all[2]))
