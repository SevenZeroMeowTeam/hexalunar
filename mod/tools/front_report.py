#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""汇总物品 JSON 的 display 与对应 bbmodel 的对齐角，判断模型网格里「前方(枪口)」在哪一端。

用法: python tools/front_report.py
"""
import json
import math
import os

ITEM = 'src/main/resources/assets/hexalunar_calamity/models/item'
MODELS = {'akm': 'akm', 'crossbow': '十字弩_v2', 'crossbow_legacy': '十字弩',
          'compound_bow': '复合弓', 'bolt': '弩箭', 'mtx': 'mtx', 'mud': 'mud'}


def load_verts(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    vs = []
    for el in data.get('elements', []):
        vs += [tuple(v) for v in el['vertices'].values()]
    return vs


def rot(pts, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(x * ca + z * sa, y, -x * sa + z * ca) for (x, y, z) in pts]


def align_angle(pts):
    best = None
    for i in range(0, 3600):
        ang = -180 + i * 0.1
        rp = rot(pts, ang)
        sz = max(v[2] for v in rp) - min(v[2] for v in rp)
        if best is None or sz > best[0]:
            best = (sz, ang)
    return best[1]


def main():
    print('%-16s %-28s %s' % ('item', 'mesh 对齐角 / 长轴跨度', 'display 旋转 (thirdperson | firstperson | gui)'))
    for item, model in MODELS.items():
        jp = os.path.join(ITEM, item + '.json')
        bp = os.path.join('模型', model + '.bbmodel')
        disp = '-'
        if os.path.exists(jp):
            with open(jp, 'r', encoding='utf-8') as fh:
                d = json.load(fh).get('display', {})
            parts = []
            for slot in ('thirdperson_righthand', 'firstperson_righthand', 'gui'):
                v = d.get(slot, {})
                parts.append('%s%s' % (slot[:2], v.get('rotation')))
            disp = ' | '.join(parts)
        info = 'missing'
        if os.path.exists(bp):
            pts = load_verts(bp)
            a = align_angle(pts)
            rp = rot(pts, a)
            sz = max(v[2] for v in rp) - min(v[2] for v in rp)
            sx = max(v[0] for v in rp) - min(v[0] for v in rp)
            sy = max(v[1] for v in rp) - min(v[1] for v in rp)
            info = 'A=%7.2f  X=%.2f Y=%.2f Z=%.2f' % (a, sx, sy, sz)
        print('%-16s %-28s %s' % (item, info, disp))


if __name__ == '__main__':
    main()
