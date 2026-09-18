"""把 tools/*_v2.py 生成的 geo+贴图装进 mod 资源目录（先备份旧文件）。

用法: python tools/install_models.py
"""
import hashlib
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
BACKUP = os.path.join(ROOT, 'build', 'backup_r38')

# (build 里的 geo, geo 目标名, 贴图目标名) —— geo 与贴图的命名后缀不一致，别猜
PAIRS = [
    ('akm_v3', 'akm.geo.json', 'akm_geo.png'),
    ('grenade_v3', 'mud.geo.json', 'mud_geo.png'),
    ('flashbang_v3', 'flashbang.geo.json', 'flashbang_geo.png'),
    ('bow_v3', 'compound_bow.geo.json', 'compound_bow_geo.png'),
    ('crossbow_v3', 'crossbow_geo.geo.json', 'crossbow_geo.png'),
]


def main():
    os.makedirs(BACKUP, exist_ok=True)
    for src_name, geo_name, tex_name in PAIRS:
        src_geo = os.path.join(ROOT, 'build', src_name + '.geo.json')
        src_tex = os.path.join(ROOT, 'build', src_name + '.png')
        dst_geo = os.path.join(ASSETS, 'geo', geo_name)
        dst_tex = os.path.join(ASSETS, 'textures', 'models', tex_name)
        for src, dst in ((src_geo, dst_geo), (src_tex, dst_tex)):
            if not os.path.exists(src):
                print('!! 缺文件 %s' % src)
                continue
            if os.path.exists(dst):
                shutil.copy2(dst, os.path.join(BACKUP, os.path.basename(dst)))
            shutil.copy2(src, dst)
            h = hashlib.md5(open(dst, 'rb').read()).hexdigest()[:8]
            print('%-30s <- %-22s md5=%s' % (os.path.basename(dst),
                                             os.path.basename(src), h))


if __name__ == '__main__':
    main()
