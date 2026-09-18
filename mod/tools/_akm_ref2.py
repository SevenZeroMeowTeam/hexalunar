#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""量 模型/akm.bbmodel（free 格式 mesh）：顶点 bbox、朝向、三视图渲染、UV 结构。

输出：
  build/akmref_axes.png   三视图（三角面填充，用于肉眼读枪型）
  控制台：bbox、长轴、面数、UV 取值方式、沿长轴的高度/宽度剖面
"""
import io
import json

from PIL import Image, ImageDraw

SRC = '模型/akm.bbmodel'

d = json.load(io.open(SRC, encoding='utf-8'))
res = d.get('resolution') or {}
TW = res.get('width', 16)
TH = res.get('height', 16)
el = d['elements'][0]
verts = el.get('vertices') or {}
faces = el.get('faces') or {}
print('resolution(uv) = %s x %s' % (TW, TH))
print('mesh vertices  = %d   faces = %d' % (len(verts), len(faces)))

pts = [tuple(v) for v in verts.values()]
lo = [min(p[i] for p in pts) for i in range(3)]
hi = [max(p[i] for p in pts) for i in range(3)]
print('bbox  min=%s  max=%s' % ([round(v, 2) for v in lo], [round(v, 2) for v in hi]))
ext = [hi[i] - lo[i] for i in range(3)]
print('extent  X=%.2f  Y=%.2f  Z=%.2f' % tuple(ext))
print('=> 最长 %s 轴 / 次之 %s 轴 / 最薄 %s 轴'
      % tuple('XYZ'[i] for i in sorted(range(3), key=lambda i: -ext[i])))

k0 = list(faces)[0]
f0 = faces[k0]
print('\n第一个面: %s' % json.dumps(f0, ensure_ascii=False)[:300])
uvs = []
for f in faces.values():
    uv = f.get('uv') or {}
    for v in uv.values():
        try:
            uvs.append((float(v[0]), float(v[1])))
        except Exception:
            pass
if uvs:
    umax = max(u for u, _ in uvs)
    vmax = max(v for _, v in uvs)
    print('UV 范围  u:[%.3f,%.3f] v:[%.3f,%.3f] => %s'
          % (min(u for u, _ in uvs), umax, min(v for _, v in uvs), vmax,
             '归一化 0..1' if umax <= 1.001 and vmax <= 1.001 else '像素'))

tris = []
for f in faces.values():
    vs = f.get('vertices') or []
    p = [verts[v] for v in vs if v in verts]
    if len(p) >= 3:
        tris.append(p)

W = 300
for ax, ay, key in ((0, 1, 'XY'), (2, 1, 'ZY'), (0, 2, 'XZ')):
    span = max(hi[ax] - lo[ax], hi[ay] - lo[ay], 1e-6)
    sc = (W - 16) / span
    im = Image.new('RGB', (W, W), (250, 250, 252))
    dr = ImageDraw.Draw(im)

    def P(p, ax=ax, ay=ay, sc=sc):
        return (8 + (p[ax] - lo[ax]) * sc, 8 + (hi[ay] - p[ay]) * sc)
    for p in tris:
        dr.polygon([P(q) for q in p], fill=(150, 170, 190), outline=(90, 110, 130))
    dr.text((6, 4), '%s : %s(right) / %s(up)' % (key, 'XYZ'[ax], 'XYZ'[ay]), fill=(200, 30, 30))
    im.save('build/akmref_%s.png' % key)

ims = [Image.open('build/akmref_%s.png' % k) for k in ('XY', 'ZY', 'XZ')]
sheet = Image.new('RGB', (W * 3, W), (255, 255, 255))
for i, im in enumerate(ims):
    sheet.paste(im, (i * W, 0))
sheet.save('build/akmref_axes.png')
print('\n三视图 -> build/akmref_axes.png')

lx = max(range(3), key=lambda i: ext[i])
ah = 1
aw = [i for i in range(3) if i not in (lx, ah)][0]
print('\n沿长轴 %s 每 1 单位分段的 高度(%s)/宽度(%s) 范围：'
      % ('XYZ'[lx], 'XYZ'[ah], 'XYZ'[aw]))
n = int(ext[lx]) + 1
buck = [[] for _ in range(n)]
for p in tris:
    for q in p:
        i = min(n - 1, max(0, int(q[lx] - lo[lx])))
        buck[i].append(q)
for i, b in enumerate(buck):
    if not b:
        continue
    print('  %s=%6.1f~%-6.1f  H[%6.2f,%6.2f]  W[%6.2f,%6.2f]  n=%d'
          % ('XYZ'[lx], lo[lx] + i, lo[lx] + i + 1,
             min(q[ah] for q in b), max(q[ah] for q in b),
             min(q[aw] for q in b), max(q[aw] for q in b), len(b)))
