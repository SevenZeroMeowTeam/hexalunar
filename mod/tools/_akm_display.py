#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""设定 AKM 物品模型的手持 display。

背景：GeckoLib 物品被手持时走原版路径，`display` 就是最终姿态。
identity（rot 0/trans 0）= 枪口正对视线方向 → 只能看到枪托截面（之前"一团"的原因）。
这里给一个"侧面 3/4 视角"的持枪姿势：
  第一人称 righthand：绕 Y 转 +32°（枪口指向左前），于是能看到机匣左侧 + 顶盖 + 弹匣。
"""
import io
import json

P = 'src/main/resources/assets/hexalunar_calamity/models/item/akm.json'
d = json.load(io.open(P, encoding='utf-8'))
disp = d.setdefault('display', {})

disp['firstperson_righthand'] = {'rotation': [0, 32, 0],
                                 'translation': [2.0, -1.2, -1.5],
                                 'scale': [0.9, 0.9, 0.9]}
disp['firstperson_lefthand'] = {'rotation': [0, 32, 0],
                                'translation': [-2.0, -1.2, -1.5],
                                'scale': [0.9, 0.9, 0.9]}
disp['thirdperson_righthand'] = {'rotation': [0, -22, 0],
                                 'translation': [0, 1.0, 0.5],
                                 'scale': [0.75, 0.75, 0.75]}
disp['thirdperson_lefthand'] = {'rotation': [0, -22, 0],
                                'translation': [0, 1.0, 0.5],
                                'scale': [0.75, 0.75, 0.75]}
disp['ground'] = {'rotation': [0, 0, 0], 'translation': [0, 2.0, 0],
                  'scale': [0.5, 0.5, 0.5]}
disp['fixed'] = {'rotation': [0, 0, 0], 'translation': [0, 0, 0],
                 'scale': [0.8, 0.8, 0.8]}
# GUI 图标：绕 Y 转 -90°（枪口朝右），再横滚 -14° 微抬，侧 3/4 视角
disp['gui'] = {'rotation': [0, -90, -14], 'translation': [0, 0, 0],
               'scale': [0.86, 0.86, 0.86]}
json.dump(d, io.open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('AKM display 已更新')
for k in ('firstperson_righthand', 'thirdperson_righthand', 'gui'):
    print('  %-22s %s' % (k, json.dumps(disp.get(k), ensure_ascii=False)))
