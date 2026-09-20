# -*- coding: utf-8 -*-
"""打印 TaCZ `ai_awp` 各动画段的长度与关键骨骼的关键帧时间（"套用 TaCZ 持枪动画"取数用）。

用法::  python tools/_ai_awp_times.py [段名...]
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'build', 'ai_awp', 'ai_awp.animation.json')

WANT = ('root', 'bolt_group', 'bolt_rotate', 'magzine_and_bullet', 'mag_and_lefthand',
        'camera', 'bullet_shell', 'bullet_in_mag', 'striker')


def frames(ch):
    """通道 → [(时间, 值列表)]"""
    out = []
    if not isinstance(ch, dict):
        return out
    for k, v in ch.items():
        out.append((float(k), v if isinstance(v, list) else [v]))
    return sorted(out)


def main():
    d = json.load(io.open(SRC, encoding='utf-8'))
    anims = d['animations']
    want = sys.argv[1:] or list(anims.keys())
    for name in want:
        a = anims.get(name)
        if a is None:
            print('!! 没有 %s' % name)
            continue
        print('== %-18s len=%s loop=%s' % (name, a.get('animation_length'), a.get('loop')))
        for bone, ch in a.get('bones', {}).items():
            if bone not in WANT:
                continue
            for kind in ('rotation', 'position', 'scale'):
                if kind not in ch:
                    continue
                fs = frames(ch[kind])
                brief = ', '.join('%.2f:%s' % (t, [round(x, 2) for x in v]) for t, v in fs[:6])
                if len(fs) > 6:
                    brief += ' … (%d 帧)' % len(fs)
                print('   %-18s %-9s %s' % (bone, kind, brief))
        print()


if __name__ == '__main__':
    main()
