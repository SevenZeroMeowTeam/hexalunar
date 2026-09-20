# -*- coding: utf-8 -*-
"""校验本轮改动的 JSON 是否合法（lang / 物品模型 / 配方 / 战利品 / 动画 / geo）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
D = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'hexalunar_calamity')

FILES = [
    os.path.join(A, 'lang', 'zh_cn.json'),
    os.path.join(A, 'lang', 'en_us.json'),
    os.path.join(A, 'geo', 'mosin.geo.json'),
    os.path.join(A, 'animations', 'mosin.animation.json'),
    os.path.join(A, 'models', 'item', 'mosin_nagant.json'),
    os.path.join(A, 'models', 'item', 'ammo_762_59.json'),
    os.path.join(A, 'models', 'item', 'ammo_box_762_59.json'),
    os.path.join(D, 'recipes', 'ammo_762_59.json'),
    os.path.join(D, 'recipes', 'ammo_box_762_59.json'),
    os.path.join(D, 'loot_modifiers', 'weapon_cache_common.json'),
    os.path.join(D, 'loot_modifiers', 'weapon_cache_rare.json'),
]


def main():
    bad = 0
    for p in FILES:
        rel = os.path.relpath(p, ROOT)
        try:
            with open(p, encoding='utf-8') as fh:
                json.load(fh)
            print('OK       %s' % rel)
        except Exception as e:                                   # noqa: BLE001
            bad += 1
            print('!! 坏文件 %s -> %s' % (rel, e))
    # 关键 lang 键存在性
    zh = json.load(open(os.path.join(A, 'lang', 'zh_cn.json'), encoding='utf-8'))
    en = json.load(open(os.path.join(A, 'lang', 'en_us.json'), encoding='utf-8'))
    need = ['item.hexalunar_calamity.mosin_nagant', 'item.hexalunar_calamity.ammo_762_59',
            'item.hexalunar_calamity.ammo_box_762_59',
            'tooltip.hexalunar_calamity.mosin_controls',
            'tooltip.hexalunar_calamity.mosin_ammo',
            'tooltip.hexalunar_calamity.mosin_sight']
    for k in need:
        ok = k in zh and k in en
        if not ok:
            bad += 1
        print('%-52s %s' % (k, 'OK' if ok else '!! 缺'))
    print('问题数 %d —— %s' % (bad, '全部通过 ✓' if bad == 0 else '需修'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
