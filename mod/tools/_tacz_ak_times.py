# -*- coding: utf-8 -*-
"""打印 TaCZ `ak47` 的动画清单 + 关键骨骼关键帧（"套用 TaCZ 动画"取数用）。

数据来源：`build/_tacz_ak/custom__tacz_default_gun__animations__ak47.animation.json`
（由 `build/_tacz_ak_list.py` 从 TaCZ jar 导出）。

用法::

    python tools/_tacz_ak_times.py                # 清单 + 关键骨骼总览
    python tools/_tacz_ak_times.py reload_empty   # 只看某段
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = os.path.join(ROOT, 'build', '_tacz_ak')
ANIM = os.path.join(D, 'custom__tacz_default_gun__animations__ak47.animation.json')
GEO = os.path.join(D, 'custom__tacz_default_gun__geo_models__gun__ak47_geo.json')

# 关心的骨骼（AK 是自动/半自动：没有手动拉栓段，但有 bolt 后坐 + 换弹 + 抛壳）
INTEREST = re.compile(r'bolt|mag|hand|shell|bullet|root|camera|constraint|striker|trigger', re.I)


def frames(ch):
    out = []
    if isinstance(ch, dict):
        for k, v in ch.items():
            if isinstance(v, dict):                     # {"pre": [...], "post": [...]} 贝塞尔帧
                v = v.get('post', v.get('pre'))
            out.append((float(k), v if isinstance(v, list) else [v]))
    return sorted(out, key=lambda t: t[0])


def main(argv):
    d = json.load(io.open(ANIM, encoding='utf-8'))
    anims = d.get('animations', {})

    if os.path.exists(GEO):
        g = json.load(io.open(GEO, encoding='utf-8'))
        bones = [b['name'] for b in g['minecraft:geometry'][0]['bones']]
        print('ak47_geo 骨骼（%d）：' % len(bones))
        print('   ' + ', '.join(bones))
        print()

    print('动画清单（%d 段）：' % len(anims))
    for name, a in sorted(anims.items()):
        print('   %-26s len=%-6s loop=%-6s bones=%d' %
              (name, a.get('animation_length'), a.get('loop'), len(a.get('bones', {}))))
    print()

    want = [a for a in argv if not a.startswith('-')] or ['shoot', 'reload_tactical', 'reload_empty']
    for name in want:
        a = anims.get(name)
        if a is None:
            cand = [k for k in anims if name in k]
            print('!! 没有 %s（近似：%s）' % (name, cand))
            continue
        print('== %-24s len=%s loop=%s' % (name, a.get('animation_length'), a.get('loop')))
        for bone, ch in a.get('bones', {}).items():
            if not INTEREST.search(bone):
                continue
            for kind in ('rotation', 'position', 'scale'):
                if kind not in ch:
                    continue
                fs = frames(ch[kind])
                brief = ', '.join('%.2f:%s' % (t, [round(x, 2) for x in v]) for t, v in fs[:7])
                if len(fs) > 7:
                    brief += ' … 共 %d 帧' % len(fs)
                print('   %-22s %-9s %s' % (bone, kind, brief))
        print()


if __name__ == '__main__':
    # 自己写 UTF-8 报告（PowerShell 的 `>` 重定向会写成 UTF-16，读不了）
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main(sys.argv[1:])
    text = buf.getvalue()
    sys.__stdout__.write(text)
    with io.open(os.path.join(ROOT, 'build', '_tacz_ak_overview.txt'), 'w', encoding='utf-8') as f:
        f.write(text)
