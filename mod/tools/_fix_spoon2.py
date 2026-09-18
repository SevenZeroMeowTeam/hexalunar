#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""压把顶端一段塞进引信内部、开角降到 38°，弹开时不会出现缝隙。"""
import io

p = 'tools/grenade_gen.py'
s = io.open(p, encoding='utf-8').read()
old = "    add('spoon', -0.70, 0.70, 13.0, 14.4, 8.2, 9.6, 'spoon')"
new = ("    # 顶端一段插进引信里（z 与引信重叠），这样绕顶点铰开时不会露出缝\n"
       "    add('spoon', -0.70, 0.70, 13.0, 14.6, 6.9, 9.8, 'spoon')")
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('压把顶端已改:', new.splitlines()[-1].strip() in s)

p2 = 'src/main/java/cn/blockforge/generated/hexalunarcalamity/client/GrenadeGeoModel.java'
t = io.open(p2, encoding='utf-8').read()
t = t.replace('SPOON_OPEN_DEG = 45.0F', 'SPOON_OPEN_DEG = 38.0F')
io.open(p2, 'w', encoding='utf-8', newline='').write(t)
print('开角 38:', 'SPOON_OPEN_DEG = 38.0F' in t)
