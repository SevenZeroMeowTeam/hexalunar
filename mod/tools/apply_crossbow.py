#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 build/crossbow_v2/ 里生成的新十字弩装进 mod 资源（先备份旧文件）。

用法: python tools/apply_crossbow.py [--revert]
"""
import os
import shutil
import sys

MOD = 'src/main/resources/assets/hexalunar_calamity'
ITEM = os.path.join(MOD, 'models', 'item')
TEX = os.path.join(MOD, 'textures', 'models')
SRC = os.path.join('build', 'crossbow_v2')
BAK = os.path.join('build', 'backup_crossbow_old')

COPY = [
    (os.path.join(SRC, 'crossbow.obj'), os.path.join(ITEM, 'crossbow.obj')),
    (os.path.join(SRC, 'crossbow.mtl'), os.path.join(ITEM, 'crossbow.mtl')),
    (os.path.join(SRC, 'crossbow_pulling_0.obj'), os.path.join(ITEM, 'crossbow_pulling_0.obj')),
    (os.path.join(SRC, 'crossbow_pulling_1.obj'), os.path.join(ITEM, 'crossbow_pulling_1.obj')),
    (os.path.join(SRC, 'crossbow_pulling_2.obj'), os.path.join(ITEM, 'crossbow_pulling_2.obj')),
    (os.path.join(SRC, 'crossbow_bolt_part.obj'), os.path.join(ITEM, 'crossbow_bolt_part.obj')),
    (os.path.join(SRC, 'crossbow_bolt_part.json'), os.path.join(ITEM, 'crossbow_bolt_part.json')),
    (os.path.join(SRC, 'crossbow_hand_part.obj'), os.path.join(ITEM, 'crossbow_hand_part.obj')),
    (os.path.join(SRC, 'crossbow_hand_part.json'), os.path.join(ITEM, 'crossbow_hand_part.json')),
    (os.path.join(SRC, 'crossbow_v2.png'), os.path.join(TEX, 'crossbow.png')),
    (os.path.join(SRC, '十字弩_v2.bbmodel'), os.path.join('模型', '十字弩_v2.bbmodel')),
]


def backup():
    os.makedirs(BAK, exist_ok=True)
    for src, dst in COPY:
        if os.path.exists(dst):
            name = dst.replace('\\', '/').split('/')[-1]
            if not os.path.exists(os.path.join(BAK, name)):
                shutil.copy2(dst, os.path.join(BAK, name))
                print('backup  %s -> %s' % (dst, os.path.join(BAK, name)))
            else:
                print('backup  %s 已存在，跳过' % name)
    shutil.copytree(BAK, BAK) if False else None


def revert():
    n = 0
    for _, dst in COPY:
        name = dst.replace('\\', '/').split('/')[-1]
        b = os.path.join(BAK, name)
        if os.path.exists(b):
            shutil.copy2(b, dst)
            print('restore %s' % dst)
            n += 1
    print('已还原 %d 个文件' % n)


def apply():
    backup()
    for src, dst in COPY:
        if not os.path.exists(src):
            print('!! 缺少 %s' % src)
            continue
        shutil.copy2(src, dst)
        print('install %s (%d bytes)' % (dst, os.path.getsize(dst)))


if __name__ == '__main__':
    if '--revert' in sys.argv:
        revert()
    else:
        apply()
