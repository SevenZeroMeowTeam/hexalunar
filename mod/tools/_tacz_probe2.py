# -*- coding: utf-8 -*-
"""把 TaCZ 的某段动画抽出来看骨骼通道（用来「套用 TaCZ 的持枪动画」）。

用法::

    python tools/_tacz_probe2.py ai_awp                 # 列出 ai_awp 的所有动画段
    python tools/_tacz_probe2.py ai_awp idle            # 只看 idle：每根骨骼的 rot/pos 极值
    python tools/_tacz_probe2.py ai_awp idle run walk   # 看多段

抽出来的 json 落在 `build/tacz_<名>/<名>.animation.json`（方便再细看）。
"""
import json
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
JAR = r'D:\mcmod\src\main\libs\tacz-1.20.1-1.1.8-hotfix.jar'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def extract(key):
    with zipfile.ZipFile(JAR) as z:
        hit = [n for n in z.namelist() if n.endswith(key)]
        if not hit:
            raise SystemExit('jar 里没有 %s' % key)
        raw = z.read(hit[0])
    dst = os.path.join(ROOT, 'build', key.replace('.animation.json', ''))
    os.makedirs(dst, exist_ok=True)
    path = os.path.join(dst, key)
    with open(path, 'wb') as fh:
        fh.write(raw)
    return path, json.loads(raw.decode('utf-8'))


def _frames(ch):
    """把某个通道的 keyframe 统一成 {时间: [x,y,z]}（TaCZ 里有 {t:[x,y,z]} 和 {t:{post:[..]}} 两种，
    偶尔整条通道直接写成 list ⇒ 直接跳过）。"""
    if not isinstance(ch, dict):
        return {}
    out = {}
    for t, v in ch.items():
        if isinstance(v, dict):
            v = v.get('post') or v.get('pre') or v.get('vector') or [0, 0, 0]
        try:
            out[float(t)] = [float(x) for x in v]
        except (TypeError, ValueError):
            continue
    return out


def main():
    key = (sys.argv[1] if len(sys.argv) > 1 else 'ai_awp') + '.animation.json'
    want = sys.argv[2:]
    path, d = extract(key)
    print('抽到 %s' % os.path.relpath(path, ROOT))
    anims = d.get('animations', d)
    names = [k for k in anims if not want or any(w in k for w in want)]
    print('动画段 %d 个（过滤 %r）' % (len(anims), want))
    for name in sorted(anims):
        a = anims[name]
        if name not in names:
            print('  %-42s loop=%-20s %.2fs' % (name, a.get('loop'), a.get('length', 0)))
            continue
        print('== %s   loop=%s  len=%s  keys=%s'
              % (name, a.get('loop'), a.get('length'), list(a.keys())))
        for bone, chans in a.get('bones', {}).items():
            bits = []
            for chan, tag in (('rotation', 'rot'), ('position', 'pos'), ('scale', 'scl')):
                if chan not in chans:
                    continue
                raw = chans[chan]
                if not isinstance(raw, dict):
                    # ★ TaCZ 的 static_xxx 常常直接把通道写成常数数组（[x,y,z]）—— 就是「静态持枪姿态」
                    if isinstance(raw, (list, tuple)) and len(raw) == 3:
                        bits.append('%s(常量) %s' % (tag, ['%.2f' % float(v) for v in raw]))
                    continue
                fr = _frames(raw)
                if not fr:
                    continue
                xs = [v[0] for v in fr.values()]
                ys = [v[1] for v in fr.values()]
                zs = [v[2] for v in fr.values()]
                bits.append('%s X %7.2f..%7.2f Y %7.2f..%7.2f Z %7.2f..%7.2f'
                            % (tag, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
            if bits:
                print('   %-16s %s' % (bone, '   |   '.join(bits)))


if __name__ == '__main__':
    main()
