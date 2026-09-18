"""打印 GeckoLib 动画 JSON 概览：每个动画的骨骼 / 通道 / 关键帧数值。

用法: python tools/_animdump.py <animation.json>
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    path = argv[1]
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    d = json.load(open(path, encoding='utf-8'))
    for name, anim in d.get('animations', {}).items():
        print('== %s   loop=%s  len=%s' % (name, anim.get('loop'),
                                           anim.get('animation_length')))
        for bone, chans in anim.get('bones', {}).items():
            for chan, keys in chans.items():
                out = []
                for t, v in keys.items():
                    x = v.get('post') or v.get('vector') or v.get('pre')
                    out.append('%s=(%s)' % (t, ','.join('%.2f' % f for f in x))
                               if x else str(t))
                print('   %-12s %-9s %s' % (bone, chan, ' '.join(out)))
    print('骨骼总数 %d' % len({b for a in d.get('animations', {}).values()
                              for b in a.get('bones', {})}))


if __name__ == '__main__':
    main(sys.argv)
