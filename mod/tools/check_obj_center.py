#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""核对 bbmodel 与游戏内 .obj 的坐标对应：OBJ 顶点 = bbmodel 顶点/16 + 0.5 ？

用法: python tools/check_obj_center.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb_north as bn  # noqa: E402

ITEM = 'src/main/resources/assets/hexalunar_calamity/models/item'
PAIRS = [
    ('akm', '模型/akm.bbmodel', 'akm.obj'),
    ('compound_bow', '模型/复合弓.bbmodel', 'compound_bow.obj'),
    ('compound_bow_p0', '模型/复合弓.bbmodel', 'compound_bow_pulling_0.obj'),
    ('bolt', '模型/弩箭.bbmodel', 'bolt.obj'),
    ('mtx', '模型/mtx.bbmodel', 'mtx.obj'),
    ('mud', '模型/mud.bbmodel', 'mud.obj'),
    ('crossbow_v2', '模型/十字弩_v2.bbmodel', 'crossbow.obj'),
]


def bb_bbox(path):
    data = bn.load(path)
    pts = [bn.elem_local_to_world(el, tuple(v)) for el, v in bn.world_verts(data)]
    return bbox(pts)


def obj_verts(path):
    pts = []
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if line.startswith('v '):
                p = line.split()
                pts.append((float(p[1]), float(p[2]), float(p[3])))
    return pts


def bbox(pts):
    return (min(p[0] for p in pts), max(p[0] for p in pts),
            min(p[1] for p in pts), max(p[1] for p in pts),
            min(p[2] for p in pts), max(p[2] for p in pts))


def main():
    print('%-16s %-34s %-34s %s' % ('model', 'bbmodel bbox (units)', 'obj bbox (block)', 'bb center -> obj center 差'))
    for name, bb, obj in PAIRS:
        bp, op = bb, os.path.join(ITEM, obj)
        if not (os.path.exists(bp) and os.path.exists(op)):
            print('%-16s 缺文件' % name)
            continue
        b = bb_bbox(bp)
        o = bbox(obj_verts(op))
        bc = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)
        oc = ((o[0] + o[1]) / 2, (o[2] + o[3]) / 2, (o[4] + o[5]) / 2)
        ext_b = ((b[1] - b[0]), (b[3] - b[2]), (b[5] - b[4]))
        ext_o = ((o[1] - o[0]), (o[3] - o[2]), (o[5] - o[4]))
        # 若 obj = (bb - c)/16 + 0.5 则 c = bb_center - 16*(obj_center - 0.5)
        c = tuple(bc[i] - 16 * (oc[i] - 0.5) for i in range(3))
        # 尺寸比看是否 16 倍
        ratio = tuple(round(ext_b[i] / ext_o[i], 3) if ext_o[i] else 0 for i in range(3))
        print('%-16s ctr(%.2f,%.2f,%.2f) ext(%.2f,%.2f,%.2f)  ctr(%.3f,%.3f,%.3f) ext(%.3f,%.3f,%.3f)  c=(%.2f,%.2f,%.2f) 比=%s'
              % (name, bc[0], bc[1], bc[2], ext_b[0], ext_b[1], ext_b[2],
                 oc[0], oc[1], oc[2], ext_o[0], ext_o[1], ext_o[2], c[0], c[1], c[2], ratio))


if __name__ == '__main__':
    main()
