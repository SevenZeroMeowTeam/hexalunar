"""把 OBJ 顶点从「16 单位/方块」缩放到「方块」单位（除以 16）。

Forge 的 ObjLoader 把 OBJ 坐标直接当【方块】用（BakedQuad 位置=方块），
Blockbench 导出的 0..16 坐标必须先除以 16，否则在游戏里大 16 倍。

用法: python obj_normalize.py <obj> [<obj> ...] [--div 16] [--force]

防呆：模型坐标已经都在 1.5 以内（即已是方块单位）时会跳过，避免重复除 16 把模型弄坏；
确实需要再除一次时加 --force。
"""
import os
import shutil
import sys

div = 16.0
if '--div' in sys.argv:
    div = float(sys.argv[sys.argv.index('--div') + 1])
files = [a for a in sys.argv[1:] if not a.startswith('--') and a != str(div)]
force = '--force' in sys.argv


def max_coord(obj_path):
    biggest = 0.0
    with open(obj_path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if line.startswith('v '):
                p = line.split()
                biggest = max(biggest, abs(float(p[1])), abs(float(p[2])), abs(float(p[3])))
    return biggest


for path in files:
    biggest = max_coord(path)
    if not force and biggest <= 1.5:
        print(f'{os.path.basename(path)}: 最大坐标 {biggest:.3f}，看起来已经是方块单位 → 跳过'
              f'（确实要再除一次请加 --force）')
        continue
    out = []
    nv = 0
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            p = line.split()
            if p and p[0] == 'v':
                x, y, z = (float(p[1]) / div, float(p[2]) / div, float(p[3]) / div)
                out.append(f'v {x:.6f} {y:.6f} {z:.6f}\n')
                nv += 1
            else:
                out.append(line if line.endswith('\n') else line + '\n')
    bak = path + '.unit16bak'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(out)
    print(f'{os.path.basename(path)}: {nv} 个顶点 ÷{div:g} → 方块单位（备份 {os.path.basename(bak)}）')
