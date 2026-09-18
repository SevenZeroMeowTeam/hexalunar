#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""量参考模型 模型/akm.bbmodel 的比例：分组、每组的包围盒、元素数量。

用来在"手写 Blockbench 模型"时照抄真实比例（长/高/宽、各部件在枪身上的位置）。
"""
import io
import json
import os
from collections import OrderedDict

SRC = '模型/akm.bbmodel'

d = json.load(io.open(SRC, encoding='utf-8'))
print('name       =', d.get('name'))
print('model_fmt  =', d.get('model_format'), d.get('meta', {}).get('format_version'))
print('resolution =', d.get('resolution'))
texs = d.get('textures', [])
for t in texs:
    print('texture    =', t.get('name'), t.get('uuid'), 'src_len', len(t.get('source') or ''))

elems = d.get('elements', [])
print('elements   =', len(elems))

# 分组 -> 元素集合
groups = d.get('groups', [])
byname = {}
for g in groups:
    byname[g.get('uuid')] = g
    byname[g.get('name')] = g


def elems_of_group(g):
    out = []

    def walk(gg):
        for u in gg.get('children', []):
            c = byname.get(u)
            if c is None:
                continue
            if c.get('children') is not None and c.get('name') and c.get('origin') is not None \
                    and c.get('children'):
                walk(c)
            else:
                walk(c)
        return out
    # 直接遍历：children 里既有 group uuid 也有 element uuid
    stack = [g]
    seen = set()
    while stack:
        cur = stack.pop()
        for u in cur.get('children', []):
            if u in seen:
                continue
            seen.add(u)
            c = byname.get(u)
            if c is not None and 'children' in c:
                stack.append(c)
            else:
                out.append(u)
    return out


print('\n--- 顶层分组 ---')
for g in groups:
    if g.get('parent') in (None, 'root') or byname.get(g.get('parent')) is None:
        uuid2e = {e['uuid']: e for e in elems}
        uu = elems_of_group(g)
        es = [uuid2e[u] for u in uu if u in uuid2e]
        lo = [9e9] * 3
        hi = [-9e9] * 3
        for e in es:
            f = e.get('from')
            t = e.get('to')
            if f and t:
                for i in range(3):
                    lo[i] = min(lo[i], f[i])
                    hi[i] = max(hi[i], t[i])
        if es:
            print('  %-18s elems=%3d  X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f]  extent %.1fx%.1fx%.1f'
                  % (g.get('name'), len(es), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2],
                     hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
        else:
            print('  %-18s (无元素)  children=%d' % (g.get('name'), len(g.get('children', []))))

# 总面积
lo = [9e9] * 3
hi = [-9e9] * 3
for e in elems:
    f = e.get('from')
    t = e.get('to')
    if f and t:
        for i in range(3):
            lo[i] = min(lo[i], f[i])
            hi[i] = max(hi[i], t[i])
print('\n整体 bbox  min=%s max=%s' % ([round(v, 2) for v in lo], [round(v, 2) for v in hi]))
print('整体尺寸    %.2f x %.2f x %.2f  （X=左右 Y=上下 Z=前后）'
      % (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
print('=> 长轴是 %s 轴' % 'XYZ'[max(range(3), key=lambda i: hi[i] - lo[i])])

# 每个元素的类型分布
kinds = {}
for e in elems:
    k = e.get('type', 'cube')
    kinds[k] = kinds.get(k, 0) + 1
print('元素类型    ', kinds)

# 打印前若干个元素，看朝向（面朝向 + 尺寸）
print('\n--- 前 12 个元素 ---')
for e in elems[:12]:
    print('  %-22s type=%-6s from=%s to=%s rot=%s'
          % (str(e.get('name'))[:22], e.get('type'), e.get('from'), e.get('to'), e.get('rotation')))
print('\n--- 元素名（全部）---')
print(', '.join(str(e.get('name')) for e in elems[:80]))
