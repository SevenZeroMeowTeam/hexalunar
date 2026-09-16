"""放大枪械模型：只改 display 里的 scale（GUI 图标 + 第一人称手持）。

用法: python scale_weapons.py <models/item 目录> [--gui 0.72] [--fp-akm 0.55] [--fp-other 0.5]
"""
import json
import os
import sys

d = sys.argv[1]


def opt(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


gui_scale = opt('--gui', 0.72)
fp_akm = opt('--fp-akm', 0.55)
fp_other = opt('--fp-other', 0.5)

changed = 0
for name in sorted(os.listdir(d)):
    if not name.endswith('.json'):
        continue
    if name.startswith('akm'):
        fp = fp_akm
    elif name.startswith('crossbow') or name.startswith('compound_bow'):
        fp = fp_other
    else:
        continue
    path = os.path.join(d, name)
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    disp = data.get('display')
    if not disp:
        continue
    if 'gui' in disp:
        disp['gui']['scale'] = [gui_scale] * 3
    for key in ('firstperson_righthand', 'firstperson_lefthand'):
        if key in disp:
            disp[key]['scale'] = [fp] * 3
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    changed += 1
    print(f'{name}: gui={gui_scale}  第一人称 scale={fp}')
print(f'共修改 {changed} 个模型 JSON')
