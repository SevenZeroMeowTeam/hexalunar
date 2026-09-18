#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修正 GeckoLib 动画文件结构：把 骨骼 → 时间 → post/vector 包一层通道名。

GeckoLib 的 BakedAnimationsAdapter 是按通道名取的（scale / position / rotation），
缺了这一层整段动画就静默不生效（akm.animation.json 原来就是这个问题）。

用法: python tools/fix_anim_channels.py <动画.json> [更多.json ...]
"""
import io
import json
import sys

CH = {'post': 'rotation', 'pre': 'rotation', 'vector': 'position', 'scale': 'scale'}


def fix_bone(bone):
    """返回 (是否需要改, 新 bone)。已经是正确结构则原样返回。"""
    if any(k in ('rotation', 'position', 'scale') for k in bone):
        return False, bone
    out = {}
    changed = False
    for t, val in bone.items():
        if not isinstance(val, dict):
            return False, bone
        ch = None
        for k in val:
            if k in CH:
                ch = CH[k]
                break
        if ch is None:
            return False, bone
        out.setdefault(ch, {})[t] = val
        changed = True
    return changed, (out if changed else bone)


def main(argv):
    for path in argv[1:]:
        with io.open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        n = 0
        for _name, anim in (data.get('animations') or {}).items():
            bones = anim.get('bones') or {}
            for bname in list(bones):
                ok, new = fix_bone(bones[bname])
                if ok:
                    bones[bname] = new
                    n += 1
        with io.open(path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        print('%s: 修正 %d 条骨骼通道' % (path, n))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
