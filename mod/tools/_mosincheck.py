# -*- coding: utf-8 -*-
"""校验 r106 jar 内莫辛资源：列出条目 + 与 src 比对 md5（对照 7.62x59 图标/模型/动画）。"""
import hashlib
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBDIR = os.path.join(ROOT, 'build', 'libs')
ASSETS = 'assets/hexalunar_calamity/'


def newest_jar():
    """取 build/libs 里最新的那个 jar（版本号随轮次变，别写死）。"""
    jars = [os.path.join(LIBDIR, f) for f in os.listdir(LIBDIR)
            if f.endswith('.jar') and not f.endswith('-sources.jar')]
    return max(jars, key=os.path.getmtime)

PAIRS = [
    ('geo/mosin.geo.json', 'geo/mosin.geo.json'),
    ('textures/models/mosin_geo.png', 'textures/models/mosin_geo.png'),
    ('textures/models/mosin_geo_glowmask.png', 'textures/models/mosin_geo_glowmask.png'),
    ('animations/mosin.animation.json', 'animations/mosin.animation.json'),
    ('models/item/mosin_nagant.json', 'models/item/mosin_nagant.json'),
    ('models/item/ammo_762_59.json', 'models/item/ammo_762_59.json'),
    ('models/item/ammo_box_762_59.json', 'models/item/ammo_box_762_59.json'),
    ('textures/item/ammo_762_59.png', 'textures/item/ammo_762_59.png'),
    ('textures/item/ammo_box_762_59.png', 'textures/item/ammo_box_762_59.png'),
    ('lang/zh_cn.json', 'lang/zh_cn.json'),
    ('lang/en_us.json', 'lang/en_us.json'),
]


def main():
    JAR = newest_jar()
    if not os.path.exists(JAR):
        print('!! 找不到 jar（先 gradlew build）')
        return 1
    print('jar = %s' % os.path.basename(JAR))
    z = zipfile.ZipFile(JAR)
    names = set(z.namelist())
    bad = 0
    print('== jar 内的莫辛 / 7.62x59 条目 ==')
    for n in sorted(x for x in names if 'mosin' in x or '762_59' in x):
        print('   ', n)
    print('== 逐个 md5 对照（jar vs src）==')
    for rel, src_rel in PAIRS:
        entry = ASSETS + rel
        src = os.path.join(ROOT, 'src', 'main', 'resources', 'assets',
                           'hexalunar_calamity', src_rel)
        if entry not in names:
            print('!! 缺 jar 条目 %s' % entry)
            bad += 1
            continue
        if not os.path.exists(src):
            print('!! 缺 src 文件 %s' % src)
            bad += 1
            continue
        a = hashlib.md5(z.read(entry)).hexdigest()[:10]
        b = hashlib.md5(open(src, 'rb').read()).hexdigest()[:10]
        ok = 'MATCH' if a == b else '!! DIFF'
        if a != b:
            bad += 1
        print('%-46s %s  %s %s' % (rel, a, b, ok))
    for rel in ('data/hexalunar_calamity/recipes/ammo_762_59.json',
                'data/hexalunar_calamity/recipes/ammo_box_762_59.json',
                'data/hexalunar_calamity/loot_modifiers/weapon_cache_common.json'):
        print('%-46s %s' % (rel, 'OK' if 'data/hexalunar_calamity/' + rel.split('/')[-1] in names
                            else '??'))
    print('差异条目 %d 个 —— %s' % (bad, '全部一致 ✓' if bad == 0 else '需要检查'))
    z.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
