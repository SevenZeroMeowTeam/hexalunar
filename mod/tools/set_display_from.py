#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把某个物品模型的 display 对齐到「参考武器」（默认 AKM）的姿态。

因为我们的新模型都是「枪口朝 -Z」的轴对齐模型，和 AKM 同一套坐标系，
所以直接套用 AKM 的 rotation / translation，再按 --scale 放大 scale 即可。

用法:
  python tools/set_display_from.py --ref <参考.json> --scale 1.3 <目标.json> [...]
  python tools/set_display_from.py --ref ... --rot-only <目标.json>   # 只改 rotation
"""
import json
import os
import shutil
import sys

ITEM = 'src/main/resources/assets/hexalunar_calamity/models/item'


def main():
    args = sys.argv[1:]
    ref = args[args.index('--ref') + 1]
    scale = float(args[args.index('--scale') + 1]) if '--scale' in args else 1.0
    rot_only = '--rot-only' in args
    targets = [a for a in args if not a.startswith('--') and a not in (ref,)
               and not a.replace('.', '').replace('-', '').isdigit()]
    targets = [t for t in targets if t.endswith('.json')]
    with open(ref, 'r', encoding='utf-8') as fh:
        ref_disp = json.load(fh).get('display') or {}
    for path in targets:
        with open(path, 'r', encoding='utf-8') as fh:
            spec = json.load(fh)
        disp = spec.get('display') or {}
        for slot, rv in ref_disp.items():
            if slot not in disp:
                disp[slot] = json.loads(json.dumps(rv))
                continue
            disp[slot]['rotation'] = list(rv.get('rotation') or [0, 0, 0])
            if not rot_only:
                disp[slot]['translation'] = list(rv.get('translation') or [0, 0, 0])
                sc = disp[slot].get('scale') or [1, 1, 1]
                base = rv.get('scale') or [1, 1, 1]
                disp[slot]['scale'] = [round(base[0] * scale, 4)] * 3
        spec['display'] = disp
        if not os.path.exists(path + '.dispbak'):
            shutil.copy2(path, path + '.dispbak')
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(spec, fh, indent=1, ensure_ascii=False)
            fh.write('\n')
        print('%s: display 已对齐 %s（scale x%.2f%s）' % (
            os.path.basename(path), os.path.basename(ref), scale,
            '，只改 rotation' if rot_only else ''))
        for slot in ('gui', 'ground', 'head', 'fixed',
                     'thirdperson_righthand', 'firstperson_righthand'):
            if slot in disp:
                print('   %-22s rot=%s t=%s s=%s' % (
                    slot, disp[slot]['rotation'], disp[slot]['translation'],
                    disp[slot].get('scale')))


if __name__ == '__main__':
    main()
