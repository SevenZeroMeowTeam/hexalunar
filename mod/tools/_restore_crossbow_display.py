# -*- coding: utf-8 -*-
"""把十字弩的 display 还原成原来那套（之前那版 GUI/hand 都正常，不该动）。"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                 'models', 'item', 'crossbow.json')

ORIG = {
    'gui': {'rotation': [25, 215, 0], 'translation': [0, 1, 0], 'scale': [0.936, 0.936, 0.936]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [0.48, 0.48, 0.48]},
    'head': {'rotation': [0, 0, 0], 'translation': [0, 13, 0], 'scale': [0.78, 0.78, 0.78]},
    'fixed': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [0.72, 0.72, 0.72]},
    'thirdperson_righthand': {'rotation': [0, 0, 0], 'translation': [0, 0, 0],
                              'scale': [0.8, 0.8, 0.8]},
    'thirdperson_lefthand': {'rotation': [0, 0, 0], 'translation': [0, 0, 0],
                             'scale': [0.8, 0.8, 0.8]},
    'firstperson_righthand': {'rotation': [0, 0, 0], 'translation': [0, 0, 0],
                              'scale': [0.8, 0.8, 0.8]},
    'firstperson_lefthand': {'rotation': [0, 0, 0], 'translation': [0, 0, 0],
                             'scale': [0.8, 0.8, 0.8]},
}

d = json.load(io.open(P, encoding='utf-8'))
for k, v in ORIG.items():
    d['display'][k] = v
json.dump(d, io.open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('crossbow display restored; firstperson_righthand =',
      json.dumps(d['display']['firstperson_righthand'], ensure_ascii=False))
