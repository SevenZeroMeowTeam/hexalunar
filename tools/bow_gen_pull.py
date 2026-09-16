"""生成复合弓的“拉弦”模型变体 + 弦贴图。

原理：
  - 原弓体网格不动（它自带的弦只有 ~0.005 单位厚，在游戏里等于看不见）
  - 在弓的两个梢之间生成一条新的弦（截面积 2 个交叉片，厚 ~0.07 单位 → 1080p 下约 8px）
  - 拉弦时弦的中点沿弓平面法线 p 后退：V 形分布（两端固定、中间位移最大）
  - 输出统一重排的 OBJ（v/vt 全部排在 f 之前，Forge 是顺序解析）

用法: python bow_gen_pull.py <源obj> <输出目录> [--pulls 0.8,1.9,3.0]
"""
import math
import os
import struct
import sys
import zlib

src = sys.argv[1]
outdir = sys.argv[2]
pulls = [0.8, 1.9, 3.0]
PULLS_ARE_FRACTIONS = '--frac' in sys.argv
if '--pulls' in sys.argv:
    pulls = [float(x) for x in sys.argv[sys.argv.index('--pulls') + 1].split(',')]
FORCE_SIGN = float(sys.argv[sys.argv.index('--sign') + 1]) if '--sign' in sys.argv else None
SKIP_TEX = '--no-tex' in sys.argv
PREFIX = sys.argv[sys.argv.index('--prefix') + 1] if '--prefix' in sys.argv else 'compound_bow'
PULL_AXIS = sys.argv[sys.argv.index('--pull-axis') + 1] if '--pull-axis' in sys.argv else 'p'   # p=面法线（弓），d=面内主轴（弩）
TEX_DIR = sys.argv[sys.argv.index('--tex-dir') + 1] if '--tex-dir' in sys.argv else os.path.join(outdir, 'textures')

head = []
verts = []
uvs = []
faces = []
with open(src, 'r', encoding='utf-8', errors='replace') as f:
    for line in f:
        p = line.split()
        if not p:
            continue
        k = p[0]
        if k == 'v':
            verts.append((float(p[1]), float(p[2]), float(p[3])))
        elif k == 'vt':
            uvs.append((float(p[1]), float(p[2])))
        elif k == 'f':
            faces.append(line.strip())
        elif k in ('mtllib', 'o', 'g', 's'):
            head.append(line.strip())

NV, NVT = len(verts), len(uvs)
print(f'读取 {src}: {NV} 顶点 / {NVT} UV / {len(faces)} 面')

# ---------- 弓平面（对 x,z 做 PCA）----------
mx = sum(v[0] for v in verts) / NV
mz = sum(v[2] for v in verts) / NV
sxx = syy = sxy = 0.0
for v in verts:
    a, b = v[0] - mx, v[2] - mz
    sxx += a * a
    syy += b * b
    sxy += a * b
th = 0.5 * math.atan2(2 * sxy, sxx - syy)
if PULL_AXIS == 'x':
    dx, dz = 1.0, 0.0
elif PULL_AXIS == 'z':
    dx, dz = 0.0, 1.0
else:
    dx, dz = math.cos(th), math.sin(th)
if PULL_AXIS in ('d', 'x', 'z'):
    # 弩：弦沿面内主轴后退（枪托方向），法线只用来给弦撑厚度
    px, pz = -dz, dx
    PULL_X, PULL_Z = dx, dz
else:
    px, pz = -dz, dx
    PULL_X, PULL_Z = px, pz
print(f'拉弦轴 = {PULL_AXIS}（方向 ({PULL_X:.3f},{PULL_Z:.3f})）')


def w(v):
    return (v[0] - mx) * px + (v[2] - mz) * pz


ys = [v[1] for v in verts]
ymin, ymax = min(ys), max(ys)
span = ymax - ymin

BAND = span * 0.032          # 弓楷带宽度（按模型高度取比例，与单位无关）
top = [v for v in verts if v[1] >= ymax - BAND]
bot = [v for v in verts if v[1] <= ymin + BAND]


def avg(pts):
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)


T, B = avg(top), avg(bot)
print(f'弓高 {span:.2f}｜上梢 {tuple(round(c, 2) for c in T)}（{len(top)} 顶点）'
      f'｜下梢 {tuple(round(c, 2) for c in B)}（{len(bot)} 顶点）')
print(f'平面主轴 d=({dx:.3f},{dz:.3f})｜法线 p=({px:.3f},{pz:.3f})')

w_tip = (w(T) + w(B)) / 2
W_WIN = span * 0.2
lo = sum(1 for v in verts if w_tip - W_WIN <= w(v) <= w_tip - span * 0.02)
hi = sum(1 for v in verts if w_tip + span * 0.02 <= w(v) <= w_tip + W_WIN)
sign = -1.0 if lo < hi else 1.0
if FORCE_SIGN is not None:
    sign = FORCE_SIGN
print(f'弦挂点 w={w_tip:.3f}｜两侧几何量 低侧 {lo} / 高侧 {hi} → 拉弦方向 {sign:+.0f}p')

SEG = 10
THICK = span * 0.0089   # 弦粗细：约为弓高的 0.9%（1080p 下约 7px）


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def gen_string(dist):
    N = lerp(T, B, 0.5)
    N = (N[0] + PULL_X * dist * sign, N[1], N[2] + PULL_Z * dist * sign)
    pts = []
    for i in range(SEG + 1):
        t = i / SEG
        pts.append(lerp(T, N, t * 2) if t <= 0.5 else lerp(N, B, (t - 0.5) * 2))
    quads = []
    for axis in ((dx, 0.0, dz), (px, 0.0, pz)):
        off = tuple(c * THICK / 2 for c in axis)
        for i in range(SEG):
            a, b = pts[i], pts[i + 1]
            quads.append((
                (a[0] - off[0], a[1] - off[1], a[2] - off[2]),
                (a[0] + off[0], a[1] + off[1], a[2] + off[2]),
                (b[0] + off[0], b[1] + off[1], b[2] + off[2]),
                (b[0] - off[0], b[1] - off[1], b[2] - off[2]),
            ))
    return quads, N


def write_png(path, size, rgb_rows):
    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw_data = b''.join(b'\x00' + bytes(r) for r in rgb_rows)
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(raw_data, 9))
    out += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(out)


SZ = 16
rows = [[0] * (SZ * 3) for _ in range(SZ)]
for y in range(SZ):
    for x in range(SZ):
        base = 208 + (12 if (x + y) % 4 == 0 else 0)
        rows[y][x * 3:x * 3 + 3] = [base, base, min(255, base + 8)]
os.makedirs(TEX_DIR, exist_ok=True)
if not SKIP_TEX:
    write_png(os.path.join(TEX_DIR, 'bow_string.png'), SZ, rows)
    print(f'写出弦贴图 {os.path.join(TEX_DIR, "bow_string.png")} ({SZ}x{SZ})')

for i, dist_in in enumerate(pulls):
    dist = dist_in * span if PULLS_ARE_FRACTIONS else dist_in
    quads, N = gen_string(dist)
    path = os.path.join(outdir, f'{PREFIX}_pulling_{i}.obj')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# compound_bow 拉弦变体（由 tools/bow_gen_pull.py 生成）\n')
        for line in head:
            f.write(line + '\n')
        for v in verts:
            f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
        for q in quads:
            for p in q:
                f.write(f'v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n')
        for u, vv in uvs:
            f.write(f'vt {u:.4f} {vv:.4f}\n')
        for _ in quads:
            for u, vv in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)):
                f.write(f'vt {u:.4f} {vv:.4f}\n')        f.write('usemtl mat\n')
        for line in faces:
            f.write(line + '\n')
        f.write('usemtl str\n')
        for qi in range(len(quads)):
            vb = NV + qi * 4 + 1
            tb = NVT + qi * 4 + 1
            f.write(f'f {vb}/{tb} {vb + 1}/{tb + 1} {vb + 2}/{tb + 2} {vb + 3}/{tb + 3}\n')
    print(f'写出 {os.path.basename(path)}（拉弦 {dist:.2f} 单位，弦点 N={tuple(round(c, 2) for c in N)}）')
