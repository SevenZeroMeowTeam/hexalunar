# -*- coding: utf-8 -*-
"""检查 install_models 是否意外改动了别的模型：备份 vs 当前文件的 md5。"""
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
BACKUP = os.path.join(ROOT, 'build', 'backup_r38')


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()[:10]


for name, cur in (('geo', os.path.join(ASSETS, 'geo')),
                  ('tex', os.path.join(ASSETS, 'textures', 'models'))):
    for f in sorted(os.listdir(cur)):
        if not f.endswith(('.json', '.png')):
            continue
        old = os.path.join(BACKUP, f)
        if not os.path.exists(old):
            continue
        a, b = md5(old), md5(os.path.join(cur, f))
        if name == 'tex' and not f.endswith('.png'):
            continue
        print('%-28s %s %s %s' % (f, 'same' if a == b else '*** CHANGED', a, b))
