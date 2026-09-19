# -*- coding: utf-8 -*-
"""把 `模型/` 里用户提供的武器音频装进 mod 音效目录（ASCII 目标名）。

用法: python tools\install_awp_sounds.py
  awp枪声.ogg                  → sounds/weapon/awp_shot_1.ogg
  AWP狙击步枪换弹音效.ogg      → sounds/weapon/awp_reload_1.ogg
  拉栓上膛.ogg                 → sounds/weapon/bolt_1.ogg   （AKM 与 AWP 共用）
"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '模型')
DST = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'sounds', 'weapon')

JOBS = [
    ('awp枪声.ogg', 'awp_shot_1.ogg'),
    ('AWP狙击步枪换弹音效.ogg', 'awp_reload_1.ogg'),
    # 拉栓上膛：AKM 换弹后拉机柄 + AWP 每发后退壳上膛，两把枪共用一条（ModSounds.BOLT）
    ('拉栓上膛.ogg', 'bolt_1.ogg'),
]


def main():
    for src_name, dst_name in JOBS:
        src = os.path.join(SRC, src_name)
        if not os.path.exists(src):
            print('!! 缺音频 %s' % src)
            continue
        shutil.copy2(src, os.path.join(DST, dst_name))
        print('%-22s <- %-30s %.1f KB' % (dst_name, src_name,
                                          os.path.getsize(src) / 1024.0))


if __name__ == '__main__':
    main()
