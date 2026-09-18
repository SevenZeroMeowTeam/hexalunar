#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把复合弓的 display 槽位改成新朝向/更大比例后的值。

模型已经：①根骨骼 +90° 转到物品平面（否则第一人称看到侧边一条细棍）
        ②几何整体 ×1.30、原点在握把中心
所以 display 只需负责「手持姿态」：旋转保持原来的 -34° 侧摆（正对镜头），
平移把弓摆到握把位置，缩放从 0.62 提到 0.95（合计比原来大约 1.3 倍）。
"""
import io
import json

P = 'src/main/resources/assets/hexalunar_calamity/models/item/compound_bow.json'
ROT = [-180.0, -34.232, -180.0]

SLOTS = {
    # 第一人称：往下/左一点，别顶到准心
    'firstperson_righthand': (ROT, [0.5, 2.1, 6.5], 0.95),
    'firstperson_lefthand': (ROT, [0.5, 2.1, 6.5], 0.95),
    # 第三人称：手里拿着，整体放大 1.4 倍
    'thirdperson_righthand': (ROT, [4.8, -0.8, 4.7], 0.85),
    'thirdperson_lefthand': (ROT, [4.8, -0.8, 4.7], 0.85),
    'gui': ([-155.0, -69.232, -180.0], [0, 1, 0], 0.95),
    'ground': ([0.0, -55.768, 0.0], [0, 4, 0], 0.42),
    'fixed': ([0.0, -55.768, 0.0], [0, 0, 0], 0.7),
    'head': ([0.0, 34.232, 0.0], [0, 13, 0], 0.85),
}

d = json.load(io.open(P, encoding='utf-8'))
d.setdefault('display', {})
for slot, (rot, trans, sc) in SLOTS.items():
    d['display'][slot] = {'rotation': rot, 'translation': trans, 'scale': [sc, sc, sc]}
with io.open(P, 'w', encoding='utf-8') as fh:
    json.dump(d, fh, ensure_ascii=False, indent=1)
for k, v in sorted(d['display'].items()):
    print('%-24s rot=%-28s trans=%-20s scale=%s' % (k, v['rotation'], v['translation'], v['scale']))
