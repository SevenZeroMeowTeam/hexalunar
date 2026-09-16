"""通用「拉弦变体」生成器（可按任意主轴）。

用法:
  python weapon_string.py <源obj> <输出目录> --prefix crossbow --span z --pull d --sign -1 \
      --pulls 0.2,0.5,0.8 --frac --thick 0.009 --tex-dir <贴图目录>

参数:
  --span  x|y|z    弦的两个挂点所在的轴（弩用 z，竖直的弓用 y）
  --pull  d|p      拉弦方向：d=面内主轴（弩/枪托方向），p=面法线（竖直弓）
  --sign  ±1       方向取反
  --pulls 列表     拉弦幅度；加 --frac 则按弦长比例
  --thick 数值     弦粗细（按弦长比例，默认 0.009）
"""
import math
import os
import struct
import sys
import zlib

a = sys.argv
src, outdir = a[1], a[2]


def opt(name, default=None):
    return a[a.index(name) + 1] if name in a else default


prefix = opt('--prefix', 'weapon')
span_ax = opt('--span', 'y')
pull_ax = opt('--pull', 'p')
sign = float(opt('--sign', '-1'))
pulls = [float(x) for x in opt('--pulls', '0.2,0.5,0.8').split(',')]
frac = '--frac' in a
thick_rel = float(opt('--thick', '0.009'))
tex_dir = opt('--tex-dir')
seg = int(opt('--seg', '10'))

AX = {'x': 0, 'y': 1, 'z': 2}
S = AX[span_ax]
O1, O2 = [i for i in (0, 1, 2) if i != S]

head, verts, uvs, faces = [], [], [], []
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
print(f'读取 {os.path.basename(src)}: {NV} 顶点 / {NVT} UV / {len(faces)} 面')

# 弦挂点：沿 span 轴的两个极值点
vals = [v[S] for v in verts]
vmin, vmax = min(vals), max(vals)
span = vmax - vmin
band = span * 0.032
top = [v for v in verts if v[S] >= vmax - band]
bot = [v for v in verts if v[S] <= vmin + band]


def avg(pts):
    n = len(pts)
    return tuple(sum(p[i] for p in pts) / n for i in range(3))


T, B = avg(top), avg(bot)
print(f'{span_ax} 轴跨度 {span:.4f}｜挂点1 {tuple(round(c,3) for c in T)}（{len(top)}）'
      f'｜挂点2 {tuple(round(c,3) for c in B)}（{len(bot)}）')

# 垂直平面内 PCA：d = 主轴（面内），p = 法线
m1 = sum(v[O1] for v in verts) / NV
m2 = sum(v[O2] for v in verts) / NV
s11 = s22 = s12 = 0.0
for v in verts:
    x1, x2 = v[O1] - m1, v[O2] - m2
    s11 += x1 * x1
    s22 += x2 * x2
    s12 += x1 * x2
th = 0.5 * math.atan2(2 * s12, s11 - s22)
d1, d2 = math.cos(th), math.sin(th)
p1, p2 = -d2, d1
if pull_ax == 'd':
    q1, q2 = d1, d2
else:
    q1, q2 = p1, p2
print(f'面内主轴 d=({d1:.3f},{d2:.3f})｜法线 p=({p1:.3f},{p2:.3f})｜拉弦用 {pull_ax}=({q1:.3f},{q2:.3f})')


def vec(along_s, c1, c2):
    v = [0.0, 0.0, 0.0]
    v[S] = along_s
    v[O1] = c1
    v[O2] = c2
    return tuple(v)


thick = span * thick_rel
print(f'弦粗细 = {thick:.5f}（弦长的 {thick_rel*100:.2f}%）')


def lerp(A, Bv, t):
    return tuple(A[i] + (Bv[i] - A[i]) * t for i in range(3))


def gen(dist):
    N = lerp(T, B, 0.5)
    off = [0.0, 0.0, 0.0]
    off[O1] = q1 * dist * sign
    off[O2] = q2 * dist * sign
    N = tuple(N[i] + off[i] for i in range(3))
    pts = []
    for i in range(seg + 1):
        t = i / seg
        pts.append(lerp(T, N, t * 2) if t <= 0.5 else lerp(N, B, (t - 0.5) * 2))
    quads = []
    for axis1, axis2 in ((d1, d2), (p1, p2)):
        o = [0.0, 0.0, 0.0]
        o[O1] = axis1 * thick / 2
        o[O2] = axis2 * thick / 2
        for i in range(seg):
            P, Q = pts[i], pts[i + 1]
            quads.append((
                tuple(P[j] - o[j] for j in range(3)),
                tuple(P[j] + o[j] for j in range(3)),
                tuple(Q[j] + o[j] for j in range(3)),
                tuple(Q[j] - o[j] for j in range(3)),
            ))
    return quads, N


def write_png(path, size, rows):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    buf = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    buf += chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(buf)


if tex_dir:
    SZ = 16
    rows = [[0] * (SZ * 3) for _ in range(SZ)]
    for y in range(SZ):
        for x in range(SZ):
            base = 208 + (12 if (x + y) % 4 == 0 else 0)
            rows[y][x * 3:x * 3 + 3] = [base, base, min(255, base + 8)]
    os.makedirs(tex_dir, exist_ok=True)
    write_png(os.path.join(tex_dir, 'bow_string.png'), SZ, rows)
    print(f'弦贴图 → {os.path.join(tex_dir, "bow_string.png")}')

for i, dv in enumerate(pulls):
    dist = dv * span if frac else dv
    quads, N = gen(dist)
    path = os.path.join(outdir, f'{prefix}_pulling_{i}.obj')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'# {prefix} 拉弦变体（tools/weapon_string.py 生成）\n')
        for line in head:
            f.write(line + '\n')
        for v in verts:
            f.write(f'v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n')
        for q in quads:
            for p in q:
                f.write(f'v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n')
        for u, vv in uvs:
            f.write(f'vt {u:.4f} {vv:.4f}\n')
        for _ in quads:
            for u, vv in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)):
                f.write(f'vt {u:.4f} {vv:.4f}\n')
        f.write('usemtl mat\n')
        for line in faces:
            f.write(line + '\n')
        f.write('usemtl str\n')
        for qi in range(len(quads)):
            vb, tb = NV + qi * 4 + 1, NVT + qi * 4 + 1
            f.write(f'f {vb}/{tb} {vb + 1}/{tb + 1} {vb + 2}/{tb + 2} {vb + 3}/{tb + 3}\n')
    print(f'写出 {os.path.basename(path)}（拉弦 {dist:.4f}，弦点 {tuple(round(c, 3) for c in N)}）')
