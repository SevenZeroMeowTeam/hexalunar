#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""压把铰点移到最顶端、开合角降到 45°，避免弹开时看着整块脱开。"""
import io
import json

p = 'tools/grenade_gen.py'
s = io.open(p, encoding='utf-8').read()
old = "('spoon', 'fuze', (0.0, 13.6, 8.4)),      # 铰点：引信顶、压把根部"
new = "('spoon', 'fuze', (0.0, 14.35, 8.6)),    # 铰点取压把最顶端，开合时不会看着脱开"
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('铰点改动:', new in s)

p2 = 'src/main/java/cn/blockforge/generated/hexalunarcalamity/client/GrenadeGeoModel.java'
t = io.open(p2, encoding='utf-8').read()
t = t.replace('SPOON_OPEN_DEG = 62.0F', 'SPOON_OPEN_DEG = 45.0F')
io.open(p2, 'w', encoding='utf-8', newline='').write(t)
print('开合角 45:', 'SPOON_OPEN_DEG = 45.0F' in t)

pose = 'build/gren_pose_armed.json'
d = json.load(io.open(pose, encoding='utf-8'))
d['spoon']['rot'] = [-45.0, 0, 0]
json.dump(d, io.open(pose, 'w', encoding='utf-8'), indent=1)
print('pose 改为 45 度')
