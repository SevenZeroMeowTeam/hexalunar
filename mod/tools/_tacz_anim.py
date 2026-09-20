# -*- coding: utf-8 -*-
"""把 TaCZ jar 里的某个动画文件打印成「骨骼 / 通道 / 时间范围 / 各轴极值」的紧凑表。

用法::

    python tools/_tacz_anim.py rifle_default            # 通用步枪持枪动画
    python tools/_tacz_anim.py springfield1873 idle ADS_up
"""
import io
import json
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JAR = r'D:\mcmod\src\main\libs\tacz-1.20.1-1.1.8-hotfix.jar'


def load(name):
    z = zipfile.ZipFile(JAR)
    for p in ('assets/tacz/animations/%s.animation.json' % name,
              'assets/tacz/custom/tacz_default_gun/assets/tacz/animations/%s.animation.json' % name):
        if p in z.namelist():
            return json.loads(z.read(p))['animations']
    raise SystemExit('not found: %s' % name)


def _flat(v):
    """关键帧值可以是 [x,y,z] 或 {'post':[..]} / {'vector':[..]}（TaCZ 用 post）"""
    if isinstance(v, dict):
        for k in ('post', 'vector', 'pre'):
            if k in v:
                return _flat(v[k])
        return [0.0]
    return v if isinstance(v, list) else [float(v)]


def summarize(anim):
    for bone, chans in anim.get('bones', {}).items():
        for chan, keys in chans.items():
            if not isinstance(keys, dict):
                continue
            pairs = sorted(((float(t), v) for t, v in keys.items()), key=lambda kv: kv[0])
            ts = [p[0] for p in pairs]
            vals = [_flat(p[1]) for p in pairs]
            n = max(len(v) for v in vals)
            rng = []
            for i in range(n):
                col = [v[i] for v in vals]
                rng.append('%.3f..%.3f' % (min(col), max(col)))
            print('  %-14s %-9s n=%-3d t=%.2f..%.2f  %s'
                  % (bone, chan, len(ts), ts[0], ts[-1], '  '.join(rng)))


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'rifle_default'
    want = sys.argv[2:]
    a = load(name)
    for k, v in a.items():
        if want and k not in want:
            continue
        print('== %s   loop=%s  len=%s  tacz_loop=%s'
              % (k, v.get('loop'), v.get('animation_length'), v.get('loop_delay', '-')))
        summarize(v)
    if not want:
        print()
        print('names:', ', '.join(a.keys()))


if __name__ == '__main__':
    main()
