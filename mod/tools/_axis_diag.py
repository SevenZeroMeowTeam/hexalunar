#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""量 AKM 几何的真实朝向：长轴是哪个轴、原点在哪、各骨骼 pivot。

判据：MC 物品模型的"正确姿势"是
  - 前向（枪口）沿 -Z
  - 上方 +Y
  - 左右厚度沿 X
  - 原点(0,0,0)在握把处（否则整把枪会从相机中心往外伸，一半在脑后）
"""
import glob
import io
import json
import os

from PIL import Image, ImageDraw

BASE = 'src/main/resources/assets/hexalunar_calamity'
TARGETS = ['akm', 'crossbow', 'compound_bow', 'frag_grenade', 'flashbang']

for name in TARGETS:
    print('=' * 78)
    print('### %s' % name)
    ip = '%s/models/item/%s.json' % (BASE, name)
    if os.path.exists(ip):
        ij = json.load(io.open(ip, encoding='utf-8'))
        fp = (ij.get('display') or {}).get('firstperson_righthand')
        print('item json fp: %s' % json.dumps(fp, ensure_ascii=False))
    geos = [p for p in glob.glob('%s/geo/*.json' % BASE) if name.split('_')[0] in os.path.basename(p)]
    if not geos:
        print('  (找不到 geo)')
        continue
    for gp in geos:
        try:
            g = json.load(io.open(gp, encoding='utf-8'))
        except Exception as e:
            print('  %s 解析失败 %s' % (gp, e))
            continue
        geo = g.get('minecraft:geometry', [g])
        geo = geo[0] if isinstance(geo, list) else geo
        desc = geo.get('description', {})
        print('-- %s  tex %s x %s' % (os.path.basename(gp), desc.get('texture_width'), desc.get('texture_height')))
        bones = geo.get('bones', [])
        cubes = [c for b in bones for c in b.get('cubes', [])]
        lo = [9e9] * 3
        hi = [-9e9] * 3
        for c in cubes:
            o = c['origin']
            s = c['size']
            for i in range(3):
                lo[i] = min(lo[i], o[i])
                hi[i] = max(hi[i], o[i] + s[i])
        print('   bones=%d cubes=%d' % (len(bones), len(cubes)))
        print('   bounds  X[%.2f,%.2f]  Y[%.2f,%.2f]  Z[%.2f,%.2f]' %
              (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
        print('   extent  X=%.2f  Y=%.2f  Z=%.2f   <-- 最大者=长轴' %
              (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
        rts = [b for b in bones if b.get('rotation')]
        print('   带 rotation 的骨骼: %s' %
              [(b['name'], b['rotation']) for b in rts][:6])
        print('   骨骼: %s' % [(b['name'], b.get('parent'), b.get('pivot')) for b in bones][:14])

        # 画三视图轮廓，看形状
        W = 190
        imgs = []
        for ax, ay, lab in ((0, 1, 'X-Y (物品平面)'), (2, 1, 'Z-Y (侧视)'), (0, 2, 'X-Z (俯视)')):
            span = max(hi[ax] - lo[ax], hi[ay] - lo[ay], 1e-3)
            sc = (W - 20) / span
            im = Image.new('RGB', (W, W), (18, 18, 24))
            d = ImageDraw.Draw(im)
            for c in cubes:
                x0 = 10 + (c['origin'][ax] - lo[ax]) * sc
                y0 = 10 + (hi[ay] - c['origin'][ay] - c['size'][ay]) * sc
                x1 = x0 + c['size'][ax] * sc
                y1 = y0 + c['size'][ay] * sc
                d.rectangle([x0, y0, max(x1, x0 + 1), max(y1, y0 + 1)],
                            outline=(120, 200, 255), fill=(60, 110, 150))
            d.text((4, 2), lab, fill=(255, 220, 120))
            imgs.append(im)
        sheet = Image.new('RGB', (W * 3, W), (0, 0, 0))
        for i, im in enumerate(imgs):
            sheet.paste(im, (i * W, 0))
        out = 'build/diag_%s_axes.png' % name
        sheet.save(out)
        print('   三视图 -> %s' % out)
