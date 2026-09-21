"""扫描 models/item/*.json：找出所有「带 elements 的 3D 物品模型」，
并检查它们是否会踩 r118 的两个坑（parent 触发 ItemModelGenerator / rotation 角度非法）。

用法：python tools/_ammo_audit.py
"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
ITEM = os.path.join(ROOT, '..', 'src', 'main', 'resources', 'assets',
                    'hexalunar_calamity', 'models', 'item')
LEGAL = (-45.0, -22.5, 0.0, 22.5, 45.0)
GEN_ROOTS = ('builtin/generated', 'item/generated', 'item/handheld')

found = 0
for p in sorted(glob.glob(os.path.join(ITEM, '*.json'))):
    try:
        m = json.load(open(p, encoding='utf-8'))
    except Exception as ex:
        print('!! JSON 解析失败 %s: %s' % (os.path.basename(p), ex))
        continue
    if 'elements' not in m:
        continue
    found += 1
    name = os.path.basename(p)
    parent = m.get('parent', '(none)')
    angles = sorted(set(float(e['rotation']['angle'])
                        for e in m['elements'] if 'rotation' in e))
    bad_ang = [a for a in angles if a not in LEGAL]
    bad_axis = sorted(set(e['rotation'].get('axis')
                          for e in m['elements'] if 'rotation' in e
                          and e['rotation'].get('axis') != 'y'))
    warn = []
    if parent.endswith(GEN_ROOTS):
        warn.append('parent=%s 会触发 ItemModelGenerator（吃掉 elements）' % parent)
    if bad_ang:
        warn.append('非法角度 %s（原版只允许 %s）' % (bad_ang, LEGAL))
    if bad_axis:
        warn.append('非 Y 轴旋转 %s' % bad_axis)
    print('%-22s elements=%-3d parent=%-42s angles=%s  %s'
          % (name, len(m['elements']), parent, angles,
             ('*** ' + '；'.join(warn)) if warn else 'OK'))

print('\n共 %d 个带 elements 的物品模型' % found)
