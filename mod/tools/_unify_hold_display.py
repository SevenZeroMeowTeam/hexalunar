#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""统一手持 display：以「投掷物」为基准（identity 旋转 + 平移 0 + 合理缩放）。

背景：手雷/震爆弹的 display 是 identity，用户确认手持正常；而 AKM/复合弓/十字弩
沿用旧 OBJ 那套大角度旋转（[-90,0,0]、[-180,-34,-180] 等），叠上 GeckoLib 几何后
出现了「只有一条细线 / 位置偏 / 大小不对」。

同时撤掉复合弓上的 root +90°（那是为了"平面朝向"加的 hack，反而把箭转向了 ±X）。
"""
import io
import json

# 统一的手持姿态：不旋转，缩放略小于 1（模型自身已是手持尺寸）
SCALES = {'akm': 0.80, 'compound_bow': 0.75, 'crossbow': 0.80}
SLOTS = ('firstperson_righthand', 'firstperson_lefthand',
         'thirdperson_righthand', 'thirdperson_lefthand')

for name, sc in SCALES.items():
    p = 'src/main/resources/assets/hexalunar_calamity/models/item/%s.json' % name
    d = json.load(io.open(p, encoding='utf-8'))
    disp = d.setdefault('display', {})
    for slot in SLOTS:
        disp[slot] = {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [sc, sc, sc]}
    # 掉落物/展示框也顺手统一（原本是别的旧值）
    disp['ground'] = {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [sc * 0.6] * 3}
    disp['fixed'] = {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [sc * 0.9] * 3}
    json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%s: 手持 -> identity, scale=%.2f' % (name, sc))

# 撤掉复合弓 root 的 +90° 旋转
g = 'tools/bow_gen.py'
s = io.open(g, encoding='utf-8').read()
old = """        else:
            # 根骨骼：整把弓绕 Y 转到 MC 物品平面（X-Y），
            # 否则第一人称/GUI 会正对着弓的侧边（看到一条细棍）
            b['rotation'] = [0, root_yaw, 0]
"""
new = """        # 根骨骼不再做朝向旋转：统一让几何自己保持「箭向 -Z、上为 +Y」，
        # 手持姿态交给 model json 的 display（与投掷物同一套，已验证正常）
"""
if old in s:
    s = s.replace(old, new, 1)
    io.open(g, 'w', encoding='utf-8', newline='').write(s)
    print('bow_gen.py: 已撤掉 root Y 旋转')
else:
    print('bow_gen.py: 锚点未匹配（可能已改过），需手工确认')
