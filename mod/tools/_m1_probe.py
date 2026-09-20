# -*- coding: utf-8 -*-
"""M1 加兰德专项放大核对：把某个模型点挪到原点后放大渲染，检查「枪口是不是空心圆管」
「觇孔环 / 镜片十字线」「弹夹盖张开后的样子」。

用法::

    python tools/_m1_probe.py <in.geo> <tex.png> <tag> [--focus x,y,z] [--zoom 4]
                              [--bones barrel,cover] [--views back,top,side,iso]
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = {'back': (180.0, 0.0), 'front': (0.0, 0.0), 'top': (0.0, 84.0),
         'side': (90.0, 0.0), 'iso': (215.0, 22.0), 'iso2': (-35.0, 20.0)}


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    geo_in, tex, tag = sys.argv[1], sys.argv[2], sys.argv[3]
    focus = [float(v) for v in arg('--focus', '0,0,0').split(',')]
    zoom = float(arg('--zoom', '4.0'))
    bones = [b for b in arg('--bones', '').split(',') if b]
    views = [v for v in arg('--views', 'back,top,iso').split(',') if v]
    size = int(arg('--size', '800'))

    g = json.load(open(os.path.join(ROOT, geo_in), encoding='utf-8'))
    gs = g['minecraft:geometry'][0]
    if bones:
        for b in gs['bones']:
            if b['name'] not in bones:
                b.pop('cubes', None)
    # --rot <bone>:<rx,ry,rz> 给某根骨骼加旋转（geo_texview 认骨骼 rotation）
    for i, a in enumerate(sys.argv):
        if a == '--rot':
            name, val = sys.argv[i + 1].split(':')
            r = [float(v) for v in val.split(',')]
            for b in gs['bones']:
                if b['name'] == name:
                    b['rotation'] = r
    # --move <bone>:<dx,dy,dz> 把某根骨骼（含子骨骼）的方块与 pivot 一起平移
    #   （geo_texview 没有骨骼位移通道，只能烘进方块 origin）
    for i, a in enumerate(sys.argv):
        if a == '--move':
            name, val = sys.argv[i + 1].split(':')
            d = [float(v) for v in val.split(',')]
            for b in gs['bones']:
                if b['name'] == name:
                    b['pivot'] = [b['pivot'][k] + d[k] for k in range(3)]
                    for c in b.get('cubes', []):
                        c['origin'] = [c['origin'][k] + d[k] for k in range(3)]
    # 把 focus 点挪到原点（方块与 pivot 一起挪）⇒ geo_texview 的 --zoom 就变成「对该点取景」
    for b in gs['bones']:
        b['pivot'] = [round(b['pivot'][i] - focus[i], 5) for i in range(3)]
        for c in b.get('cubes', []):
            c['origin'] = [round(c['origin'][i] - focus[i], 5) for i in range(3)]
            if 'pivot' in c:
                c['pivot'] = [round(c['pivot'][i] - focus[i], 5) for i in range(3)]
    sub = os.path.join(ROOT, 'build', '_m1p_%s.geo.json' % tag)
    json.dump(g, open(sub, 'w', encoding='utf-8'), ensure_ascii=False)

    for v in views:
        yaw, pitch = VIEWS[v]
        out = os.path.join(ROOT, 'build', '_m1p_%s_%s.png' % (tag, v))
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'geo_texview.py'),
                        os.path.relpath(sub, ROOT), tex, os.path.relpath(out, ROOT),
                        '--yaw', str(yaw), '--pitch', str(pitch),
                        '--size', str(size), '--zoom', str(zoom)],
                       check=True, stdout=subprocess.DEVNULL)
        print('wrote', os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main()
