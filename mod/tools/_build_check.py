#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""升版本 → 编译打包 → 汇总结果（避开 PowerShell 引号坑）。"""
import glob
import io
import json
import os
import re
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# 1) 升版本
ver = sys.argv[1] if len(sys.argv) > 1 else 'r34'
p = 'build.gradle'
s = io.open(p, encoding='utf-8').read()
s = re.sub(r"version = '1\.0\.0-r\d+'", "version = '1.0.0-%s'" % ver, s)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('版本 ->', re.search(r"version = '([^']+)'", s).group(1))

# 2) 编译
r = subprocess.run(['cmd', '/c', 'gradlew.bat', 'build', '--console=plain'],
                   capture_output=True, text=True, errors='replace')
log = (r.stdout or '') + (r.stderr or '')
io.open('build/_last_build.log', 'w', encoding='utf-8').write(log)
print('gradle 退出码 =', r.returncode)
for line in log.splitlines():
    if 'BUILD' in line or 'error:' in line or '错误:' in line:
        print('  ', line.strip()[:160])
errs = [l.strip() for l in log.splitlines() if '.java:' in l and 'error' in l.lower()]
if errs:
    print('--- Java 错误 ---')
    for e in errs[:15]:
        print('  ', e[:170])

# 3) 产物与资源核对
jars = sorted(glob.glob('build/libs/*.jar'), key=os.path.getmtime)
if jars:
    f = jars[-1]
    print('jar -> %s  %.1f MB' % (os.path.basename(f), os.path.getsize(f) / 1048576.0))
    z = zipfile.ZipFile(f)
    names = z.namelist()
    for want in ('geo/akm.geo.json', 'animations/akm.animation.json',
                 'textures/models/akm_geo.png', 'models/item/akm.json'):
        hit = [n for n in names if n.endswith(want)]
        print('   %-34s %s' % (want, 'OK' if hit else '缺失'))
    a = json.loads(z.read([n for n in names if n.endswith('animations/akm.animation.json')][0])
                   .decode('utf-8'))['animations']
    print('   动画键:', ', '.join(sorted(k.split('.')[-1] for k in a)))
    g = json.loads(z.read([n for n in names if n.endswith('geo/akm.geo.json')][0]).decode('utf-8'))
    bo = g['minecraft:geometry'][0]['bones']
    print('   骨骼 %d 根 / 方块 %d 个'
          % (len(bo), sum(len(b.get('cubes', [])) for b in bo)))
    item = json.loads(z.read([n for n in names
                             if n.endswith('models/item/akm.json')][0]).decode('utf-8'))
    print('   fp display:', json.dumps((item.get('display') or {})
                                       .get('firstperson_righthand'), ensure_ascii=False))
