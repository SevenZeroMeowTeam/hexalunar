"""用 (x,z) 投影 + y 跨度定位弓弦：弦在 (x,z) 上是几乎一个点，但 y 跨度接近整弓高。

用法: python bow_find_string.py <obj> [--dump 输出obj]
"""
import sys
from collections import defaultdict

path = sys.argv[1]
out = None
if '--dump' in sys.argv:
    out = sys.argv[sys.argv.index('--dump') + 1]

raw = []
verts = []
faces = []
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    for line in f:
        raw.append(line)
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            verts.append((float(p[1]), float(p[2]), float(p[3])))
        elif p[0] == 'f':
            faces.append([int(t.split('/')[0]) - 1 for t in p[1:]])

ys = [v[1] for v in verts]
ymin, ymax = min(ys), max(ys)
height = ymax - ymin
print(f'弓高 y {ymin:.2f}..{ymax:.2f} = {height:.2f}')

CELL = 0.5
cells = defaultdict(list)
for i, (x, y, z) in enumerate(verts):
    cells[(round(x / CELL), round(z / CELL))].append(i)

rows = []
for key, idxs in cells.items():
    yy = [verts[i][1] for i in idxs]
    span = max(yy) - min(yy)
    if len(idxs) >= 4:
        rows.append((span, len(idxs), key, idxs))
rows.sort(reverse=True)

print('\n=== y 跨度最大的 (x,z) 格子（弦候选）===')
for span, n, key, idxs in rows[:12]:
    xs = [verts[i][0] for i in idxs]
    zs = [verts[i][2] for i in idxs]
    yy = [verts[i][1] for i in idxs]
    cov = span / height
    print(f'  ({key[0]*CELL:5.2f},{key[1]*CELL:5.2f})  顶点 {n:3d}  y {min(yy):6.2f}..{max(yy):6.2f}  '
          f'跨度 {span:5.2f} = 弓高 {cov*100:4.0f}%  实际 x {min(xs):.2f}..{max(xs):.2f}  z {min(zs):.2f}..{max(zs):.2f}')

# 弦柱：把高跨度格子合并成一条竖直“柱子”
best = rows[0] if rows else None
if best:
    span, n, key, idxs = best
    xs = [verts[i][0] for i in idxs]
    zs = [verts[i][2] for i in idxs]
    cx, cz = sum(xs) / len(xs), sum(zs) / len(zs)
    print(f'\n最佳弦柱中心 ≈ x={cx:.3f}  z={cz:.3f}')
    # 收集弦柱附近所有顶点
    R = 0.55
    col = [i for i, (x, y, z) in enumerate(verts) if abs(x - cx) <= R and abs(z - cz) <= R]
    cy = [verts[i][1] for i in col]
    print(f'半径 {R} 内顶点 {len(col)}，y {min(cy):.2f}..{max(cy):.2f}（弓高占比 {(max(cy)-min(cy))/height*100:.0f}%）')
    # 柱子外最近的顶点有多远？判断柱子是否“孤立”
    others = [(x, y, z) for i, (x, y, z) in enumerate(verts) if i not in set(col)]
    d = sorted(((x - cx) ** 2 + (z - cz) ** 2) ** 0.5 for x, y, z in others)[:8]
    print(f'柱子外最近 8 个顶点的 (x,z) 距离: ' + ', '.join(f'{v:.2f}' for v in d))
    print(f'→ 弦若孤立，这些距离应明显大于 {R}')
