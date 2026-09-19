# -*- coding: utf-8 -*-
"""确认 r61 jar 里装的是新体素弩（crossbow geo 的方块数）与贴图 md5。"""
import glob
import hashlib
import os
import zipfile

JARS = sorted(glob.glob(r'D:\做一个_Minecraft_1_20_1_的_F\mod\build\libs\*.jar'))
latest = [j for j in JARS if 'r61' in j] or JARS[-1:]
for p in latest:
    z = zipfile.ZipFile(p)
    geo = z.read('assets/hexalunar_calamity/geo/crossbow_geo.geo.json').decode('utf-8')
    tex = z.read('assets/hexalunar_calamity/textures/models/crossbow_geo.png')
    print('%s  %.2f MB' % (os.path.basename(p), os.path.getsize(p) / 1048576.0))
    print('   crossbow geo cubes = %d   贴图 md5=%s'
          % (geo.count('"origin"'), hashlib.md5(tex).hexdigest()[:10]))
