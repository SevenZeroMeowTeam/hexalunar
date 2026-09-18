# -*- coding: utf-8 -*-
"""查 GeckoLib jar 里和「网格（poly_mesh）」有关的类，判断 4.8.4 到底渲不渲染 mesh。

用法: python tools\\_glmesh.py
"""
import zipfile

JAR = (r'C:\Users\Administrator\.gradle\caches\modules-2\files-2.1\software.bernie.geckolib'
       r'\geckolib-forge-1.20.1\4.8.4\35153b92ee86becebbf3b0b2559e2bc9ee8d16fb'
       r'\geckolib-forge-1.20.1-4.8.4.jar')


def main():
    names = zipfile.ZipFile(JAR).namelist()
    for key in ('Poly', 'Mesh', 'mesh', 'Tri', 'Vertex'):
        hits = [n for n in names if key in n.split('/')[-1]]
        print('--- 含 %r 的类/资源: %d' % (key, len(hits)))
        for n in hits:
            print('    ' + n)


if __name__ == '__main__':
    main()
