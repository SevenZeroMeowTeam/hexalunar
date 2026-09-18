#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""震爆弹压把沿 -X 侧竖直，弹开要绕 Z 轴（手雷是沿 +Z 背面、绕 X 轴，别照抄）。"""
import io
import json

p = 'src/main/java/cn/blockforge/generated/hexalunarcalamity/client/FlashbangGeoModel.java'
s = io.open(p, encoding='utf-8').read()
old = "            spoon.setRotX(-spoonOpen * SPOON_OPEN_DEG * Mth.DEG_TO_RAD);"
new = "            // 压把在 -X 侧竖直，绕 Z 轴向外弹开（手雷那种在 +Z 背面、绕 X）\n" \
      "            spoon.setRotZ(-spoonOpen * SPOON_OPEN_DEG * Mth.DEG_TO_RAD);"
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('改成绕 Z:', 'spoon.setRotZ(-spoonOpen' in s)

pose = 'build/fb_pose_armed.json'
d = {'pin': {'pos': [0, 0, -1.15]}, 'spoon': {'rot': [0, 0, -42.0]}}
json.dump(d, io.open(pose, 'w', encoding='utf-8'), indent=1)
print('pose 写好')
