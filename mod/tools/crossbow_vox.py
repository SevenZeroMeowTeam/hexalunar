#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""十字弩 v4：把**参考网格**（`模型/十字弩_v2.bbmodel`，11 个 mesh 部件）体素化成 GeckoLib 方块模型。

做法沿用 `akm_voxel_gen.py`：
  · 参考工程是「单层壳」网格 → 射线沿 +X 穿越，按「穿入/穿出」成对填充；薄壁（<0.5 格）吸到最近一格；
  · 每个体素从**入射面**采样贴图；与 AKM 的区别是这里会记住体素来自哪个 mesh → 直接映射到骨骼。
  · 体素的 UV 大小按**该三角面的 UV 密度**算（`sqrt(uv面积 / 3D面积)`，像素/单位），
    这样贴图在体素上的缩放与原始网格一致（AKM 那份是写死的，这里必须算）。

★ 骨骼名与 pivot 必须保持 `CrossbowGeoModel` 依赖的那套：
    root → move → body → {stock, grip, scope, prod_left, prod_right, string_left, string_right, nock, bolt}
  Java 会推：`string_left/right`(rotY 拉弦)、`cam_left/right`(rotY 凸轮)、`nock`(posZ/posY)、`bolt`(posY/posZ)。
  弦两段必须是「从弓臂梢枢轴指向弦心」的直杆，**长度 = hypot(TIP_X, DRAW_DZ)** ——
  绕 Y 转 ∓atan2(DRAW_DZ, TIP_X) 后内端正好落到弦心后退 DRAW_DZ 的位置（脚本末尾有自检）。

输出：build/crossbow_v4.geo.json / build/crossbow_v4.png，再由 install_models.py 装进 assets。
"""
import base64
import io
import json
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, '模型', '十字弩_v2.bbmodel')
OUT_DIR = os.path.join(ROOT, 'build')
GEO_OUT = os.path.join(OUT_DIR, 'crossbow_v4.geo.json')
TEX_OUT = os.path.join(OUT_DIR, 'crossbow_v4.png')

FACES = ('north', 'east', 'south', 'west', 'up', 'down')

# ------------------------------------------------------------------ 参数
# 参考模型 grip 网格的包围盒中心 → 现有模型握把中心（CB_RIGHT / display 都是照这个调的）
GRIP_TARGET = (0.0, -0.95, 0.66)
# 拉弦行程（模型像素）：弦心从 NOCK_Z0 再往 +Z（射手方向）退这么多
DRAW_DZ = 1.80
# 体素大小（模型像素）：0.45 -> ~820 方块（0.35 要 1400+，太贵；0.5 -> ~690）
STEP = 0.45
# ★ 弓臂放大（r65）：用户要求「弓臂明显探出机身」（参照 模型/十字弩.bbmodel 那个宽弓臂）。
#   参考 v2 的弓臂只到 |x| 3.2、而机身带（riser）就到 1.9 ⇒ 弓臂只比机身探出 1.3 像素，看着就像贴在弩身上。
#   X 拉长会让体素变成 0.45×0.77 的长条，所以厚度（Y/Z）另外再放一点，观感上更像参考的宽弓臂。
#   ★ limb / cables / string 三个分件必须**一起**放（弦锚点在弓臂梢上），锚点取各自的内端，否则会和 riser 脱开。
LIMB_SX = 1.7
LIMB_SY = 1.25
# 弓臂（单侧分件，绕自己的内端缩放，内端不动 ⇒ 不会跟 riser 脱开）
LIMB_X_MESHES = ('limb_L', 'limb_R')
# 横跨两侧的分件（弦 / 线缆）必须绕 x=0 缩放，否则整个模型会变成一边长一边短
LIMB_MID_MESHES = ('string', 'cables')
LIMB_THICK_MESHES = ('limb_L', 'limb_R')
# 贴图：v2 贴图缩到 480²，右下角留 32px 宽带子放「弦/弦心/弩箭」纯色块
TEX_SIZE = 512
PATCH = 480
PAT_STRING = (480, 0, 32, 10)
PAT_NOCK = (480, 16, 32, 10)
PAT_BOLT_SH = (480, 32, 32, 10)
PAT_BOLT_HD = (480, 48, 32, 10)
PAT_VANE = (480, 64, 32, 10)
COL_STRING = (210, 203, 182)
COL_NOCK = (38, 38, 40)
COL_BOLT_SH = (58, 60, 64)
COL_BOLT_HD = (168, 172, 178)
COL_VANE = (214, 90, 44)

MESH_BONE = {
    'riser': 'body', 'rail': 'body', 'housing': 'body', 'detail': 'body', 'cables': 'body',
    'scope': 'scope', 'grip': 'grip', 'stock': 'stock',
    'limb_L': 'prod_right', 'limb_R': 'prod_left',
    'string': 'body',                      # 弦另外用方块画（要能绕弓臂梢转）
}

BONES = [
    ('root', None), ('move', 'root'), ('body', 'move'), ('stock', 'body'), ('grip', 'body'),
    ('scope', 'body'), ('prod_left', 'body'), ('prod_right', 'body'),
    ('cam_left', 'body'), ('cam_right', 'body'),
    ('string_left', 'body'), ('string_right', 'body'), ('nock', 'body'), ('bolt', 'body'),
]


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def ray_tri(orig, d, a, b, c):
    e1, e2 = sub(b, a), sub(c, a)
    p = cross(d, e2)
    det = dot(e1, p)
    if abs(det) < 1e-9:
        return None
    inv = 1.0 / det
    t1 = sub(orig, a)
    u = dot(t1, p) * inv
    if u < -1e-6 or u > 1.0 + 1e-6:
        return None
    q = cross(t1, e1)
    v = dot(d, q) * inv
    if v < -1e-6 or u + v > 1.0 + 1e-6:
        return None
    t = dot(e2, q) * inv
    return None if t <= 1e-6 else (t, u, v)


def load_ref(path=REF):
    data = json.loads(io.open(path, encoding='utf-8').read())
    tris, meshes = [], {}
    raw_uv_max = 0.0
    for el in data.get('elements', []):
        verts = {k: tuple(v) for k, v in el['vertices'].items()}
        name = el.get('name') or 'unnamed'
        xs = [p[0] for p in verts.values()]
        ys = [p[1] for p in verts.values()]
        zs = [p[2] for p in verts.values()]
        meshes[name] = ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))
        seen = set()
        for f in el['faces'].values():
            vids = [v for v in (f.get('vertices') or []) if v in verts]
            if len(vids) < 3:
                continue
            uvmap = f.get('uv') or {}
            raw_uv_max = max(raw_uv_max, max((abs(v) for uv in uvmap.values() for v in uv),
                                             default=0.0))
            for i in range(1, len(vids) - 1):
                a, b, c = verts[vids[0]], verts[vids[i]], verts[vids[i + 1]]
                key = tuple(sorted(tuple(round(k, 3) for k in v) for v in (a, b, c)))
                if key in seen:
                    continue
                seen.add(key)
                tris.append((a, b, c, tuple(uvmap.get(vids[0], (0, 0))),
                             tuple(uvmap.get(vids[i], (0, 0))),
                             tuple(uvmap.get(vids[i + 1], (0, 0))), name))
    tex = None
    for t in data.get('textures') or []:
        src = t.get('source') or ''
        if src.startswith('data:image'):
            tex = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGB')
            break
    res = data.get('resolution') or {}
    return meshes, tris, tex, float(res.get('width') or 16), raw_uv_max


def limb_anchor_x(xs):
    """分件所在的 ±X 侧以及它的内端 x（弓臂放大时以它为锚点，内端不动 ⇒ 不会跟 riser 脱开）"""
    sign = 1.0 if (min(xs) + max(xs)) > 0 else -1.0
    return sign * min(abs(v) for v in xs)


def scale_limbs(tris, meshes):
    """把弓臂（+ 线缆 / 弦）按 LIMB_SX / LIMB_SY 放大，并回写这些分件的包围盒。"""
    if LIMB_SX == 1.0 and LIMB_SY == 1.0:
        return tris, meshes
    cy = 0.0
    n = 0
    for name in LIMB_THICK_MESHES:
        (_, y0, _), (_, y1, _) = meshes[name]
        cy += (y0 + y1) / 2.0
        n += 1
    cy = cy / n
    # ★ 锚点必须取**整个分件**的内端 x（按三角形算的话，梢部那几片会以自己的最小 x 为轴 ⇒ 几乎不动）
    anchors = {}
    for name in LIMB_X_MESHES:
        (x0, _, _), (x1, _, _) = meshes[name]
        anchors[name] = limb_anchor_x([x0, x1])
    for name in LIMB_MID_MESHES:
        anchors[name] = 0.0
    out = []
    for t in tris:
        name = t[6]
        if name not in anchors:
            out.append(t)
            continue
        ax = anchors[name]
        pts = []
        for p in t[:3]:
            nx = ax + LIMB_SX * (p[0] - ax)
            if name in LIMB_THICK_MESHES:
                pts.append((nx, cy + LIMB_SY * (p[1] - cy), p[2]))
            else:
                pts.append((nx, p[1], p[2]))
        out.append(tuple(pts) + t[3:])
    for name in LIMB_X_MESHES + LIMB_MID_MESHES:
        pts = [p for t in out if t[6] == name for p in t[:3]]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        zs = [p[2] for p in pts]
        meshes[name] = ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))
    return out, meshes


def uv_space(tex_w, res_w, raw_uv_max):
    """判断 mesh 的 UV 存在哪个空间：归一化 / 分辨率单位 / 已经是像素。"""
    if raw_uv_max <= 1.0001:
        return tex_w / 1.0, '归一化 0..1'
    if raw_uv_max <= res_w * 1.05 and tex_w > res_w * 1.5:
        return tex_w / res_w, '分辨率单位 0..%.0f' % res_w
    return 1.0, '像素 0..%d' % tex_w


def voxelize(tris, step, uv_scale):
    """**表面**体素化：沿每个三角面密采样，采样点落在哪格就标记哪格（一格的壳）。

    为什么不用 AKM 那份「射线穿入/穿出成对填充」：v2 是 11 个**互相重叠**的壳体部件
    （导轨里还有槽、镜筒是空管），成对填充会把内部空隙一起填掉、薄壁还会被吸成大块，
    渲染出来是一坨乱方块。表面壳既贴合轮廓、方块数也少得多，视觉上完全一样（里面看不见）。
    返回 {(ix,iy,iz): (u_px, v_px, mesh)}，UV 取该格第一个采样点的贴图坐标。
    """
    cells = {}
    xs = [t[i][0] for t in tris for i in range(3)]
    ys = [t[i][1] for t in tris for i in range(3)]
    zs = [t[i][2] for t in tris for i in range(3)]
    lo = (min(xs), min(ys), min(zs))
    hi = (max(xs), max(ys), max(zs))
    for tri in tris:
        p0, p1, p2 = tri[0], tri[1], tri[2]
        q0 = (tri[3][0] * uv_scale, tri[3][1] * uv_scale)
        q1 = (tri[4][0] * uv_scale, tri[4][1] * uv_scale)
        q2 = (tri[5][0] * uv_scale, tri[5][1] * uv_scale)
        span = max(abs(p1[0] - p0[0]) + abs(p2[0] - p0[0]),
                   abs(p1[1] - p0[1]) + abs(p2[1] - p0[1]),
                   abs(p1[2] - p0[2]) + abs(p2[2] - p0[2]))
        n = max(2, int(math.ceil(span / (step * 0.5))) + 1)
        for i in range(n + 1):
            for j in range(n + 1 - i):
                w0 = 1.0 - (i + j) / float(n)
                w1 = i / float(n)
                w2 = j / float(n)
                px = w0 * p0[0] + w1 * p1[0] + w2 * p2[0]
                py = w0 * p0[1] + w1 * p1[1] + w2 * p2[1]
                pz = w0 * p0[2] + w1 * p1[2] + w2 * p2[2]
                key = (int(math.floor((px - lo[0]) / step)),
                       int(math.floor((py - lo[1]) / step)),
                       int(math.floor((pz - lo[2]) / step)))
                if key not in cells:
                    cells[key] = (w0 * q0[0] + w1 * q1[0] + w2 * q2[0],
                                  w0 * q0[1] + w1 * q1[1] + w2 * q2[1],
                                  tri[6])
    return cells, lo, hi


def build_texture(tex):
    img = Image.new('RGB', (TEX_SIZE, TEX_SIZE), (26, 27, 29))
    img.paste(tex.resize((PATCH, PATCH), Image.LANCZOS), (0, 0))
    for (x, y, w, h), col in ((PAT_STRING, COL_STRING), (PAT_NOCK, COL_NOCK),
                              (PAT_BOLT_SH, COL_BOLT_SH), (PAT_BOLT_HD, COL_BOLT_HD),
                              (PAT_VANE, COL_VANE)):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                img.putpixel((xx, yy), col)
    return img


def main(argv):
    step = STEP
    if '--step' in argv:
        step = float(argv[argv.index('--step') + 1])
    uvmul = 1.0
    if '--uvmul' in argv:
        uvmul = float(argv[argv.index('--uvmul') + 1])

    meshes, tris, tex, res_w, raw_max = load_ref()
    if tex is None:
        raise SystemExit('参考工程里没有内嵌贴图')
    uv_scale, kind = uv_space(tex.size[0], res_w, raw_max)
    print('参考网格: %d 个部件 / %d 三角面  贴图 %s  分辨率 %.0f  UV 最大 %.3f'
          % (len(meshes), len(tris), tex.size, res_w, raw_max))
    print('UV 空间判定: %s  ->  x%.1f' % (kind, uv_scale))

    if LIMB_SX != 1.0 or LIMB_SY != 1.0:
        lmin0, lmax0 = meshes['limb_L']
        tris, meshes = scale_limbs(tris, meshes)
        lmin1, lmax1 = meshes['limb_L']
        print('弓臂放大: X x%.2f 厚度(Y) x%.2f   弓臂外端 X %.2f -> %.2f（内端不动）'
              % (LIMB_SX, LIMB_SY, lmax0[0], lmax1[0]))

    gmin, gmax = meshes['grip']
    gc = [(gmin[i] + gmax[i]) / 2 for i in range(3)]
    delta = tuple(GRIP_TARGET[i] - gc[i] for i in range(3))
    print('grip 中心 %s -> %s  -> 平移 %.3f, %.3f, %.3f'
          % ([round(v, 2) for v in gc], list(GRIP_TARGET), *delta))
    tris = [tuple((p[0] + delta[0], p[1] + delta[1], p[2] + delta[2]) for p in t[:3]) + t[3:]
            for t in tris]

    cells, lo, hi = voxelize(tris, step, uv_scale)
    print('体素 %.2fpx -> %d 个方块   包围盒 x %.2f~%.2f  y %.2f~%.2f  z %.2f~%.2f'
          % (step, len(cells), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))

    buckets = {b[0]: [] for b in BONES}
    # 体素面的 UV 尺寸：用标称密度（1 单位 = 贴图/分辨率 像素）——同 AKM 那份，实测观感最好
    wu = step * (TEX_SIZE / res_w) * uvmul
    for (ix, iy, iz), (u, v, mesh) in cells.items():
        face = {'uv': [round(u - wu / 2, 3), round(v - wu / 2, 3)],
                'uv_size': [round(wu, 3), round(wu, 3)]}
        buckets[MESH_BONE.get(mesh, 'body')].append({
            'origin': [round(lo[0] + ix * step, 4), round(lo[1] + iy * step, 4),
                       round(lo[2] + iz * step, 4)],
            'size': [round(step, 4)] * 3,
            'uv': {f: dict(face) for f in FACES},
        })

    # ---- 弦 / 弦心 / 弩箭（方块画，UV 走右下角纯色带）----
    smin, smax = meshes['string']
    tip_x = max(abs(smin[0]), abs(smax[0]))
    nock_z = (smin[2] + smax[2]) / 2 + delta[2]
    str_y = (smin[1] + smax[1]) / 2 + delta[1]
    half = math.hypot(tip_x, DRAW_DZ)

    def rect(pat):
        x, y, w, h = pat
        return {'uv': [x, y], 'uv_size': [w, h]}

    def box(x0, x1, y0, y1, z0, z1, pat):
        return {'origin': [round(min(x0, x1), 4), round(min(y0, y1), 4), round(min(z0, z1), 4)],
                'size': [round(abs(x1 - x0), 4), round(abs(y1 - y0), 4), round(abs(z1 - z0), 4)],
                'uv': {f: dict(rect(pat)) for f in FACES}}

    th = 0.075
    buckets['string_left'].append(box(-tip_x, -tip_x + half, str_y - th, str_y + th,
                                      nock_z - th, nock_z + th, PAT_STRING))
    buckets['string_right'].append(box(tip_x - half, tip_x, str_y - th, str_y + th,
                                       nock_z - th, nock_z + th, PAT_STRING))
    buckets['nock'].append(box(-0.60, 0.60, str_y - 0.26, str_y + 0.26,
                               nock_z - 0.26, nock_z + 0.26, PAT_NOCK))

    rmin, rmax = meshes['rail']
    rail_front, rail_top = rmin[2] + delta[2], rmax[1] + delta[1]
    bolt_y = rail_top + 0.16
    bolt_rear, bolt_tip = nock_z + 0.55, rail_front - 2.90
    buckets['bolt'].append(box(-0.20, 0.20, bolt_y - 0.18, bolt_y + 0.18,
                               bolt_tip + 0.6, bolt_rear - 0.6, PAT_BOLT_SH))
    buckets['bolt'].append(box(-0.26, 0.26, bolt_y - 0.26, bolt_y + 0.26,
                               bolt_tip, bolt_tip + 0.62, PAT_BOLT_HD))
    for zz in (bolt_rear - 0.45, bolt_rear - 0.95):
        buckets['bolt'].append(box(-0.36, 0.36, bolt_y - 0.30, bolt_y + 0.30,
                                   zz - 0.24, zz + 0.24, PAT_VANE))

    # ---- geo ----
    out_bones = []
    for name, parent in BONES:
        cubes = buckets.get(name) or []
        if name in ('string_left', 'string_right', 'cam_left', 'cam_right', 'nock'):
            sign = -1.0 if name.endswith('_left') else (1.0 if name.endswith('_right') else 0.0)
            piv = [round(sign * tip_x, 4), round(str_y, 4), round(nock_z, 4)]
        elif cubes:
            n = len(cubes)
            piv = [round(sum(c['origin'][i] + c['size'][i] / 2 for c in cubes) / n, 4)
                   for i in range(3)]
        else:
            piv = [0.0, 0.0, 0.0]
        b = {'name': name, 'pivot': list(piv)}
        if parent:
            b['parent'] = parent
        if cubes:
            b['cubes'] = cubes
        out_bones.append(b)

    os.makedirs(OUT_DIR, exist_ok=True)
    build_texture(tex).save(TEX_OUT)
    geo = {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {
                'identifier': 'geometry.crossbow_geo',
                'texture_width': TEX_SIZE, 'texture_height': TEX_SIZE,
                'visible_bounds_width': 3, 'visible_bounds_height': 3,
                'visible_bounds_offset': [0, 1.2, 0],
            },
            'bones': out_bones,
        }],
    }
    with io.open(GEO_OUT, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, indent=1)
    print('模型 -> %s （%d 骨骼 / %d 方块）' % (GEO_OUT, len(out_bones), len(cells)))
    print('贴图 -> %s' % TEX_OUT)
    for name, _p in BONES:
        n = len(buckets.get(name) or [])
        if n:
            print('   %-13s %4d' % (name, n))

    print()
    print('---- Java 常数（CrossbowGeoModel）----')
    print('TIP_X   = %.3f  （弦半跨 = 弓臂梢 X）' % tip_x)
    print('DRAW_DZ = %.3f  （本脚本设定）' % DRAW_DZ)
    print('NOCK_Z0 = %.3f  （弦面 Z）' % nock_z)
    print('弦面 Y  = %.3f  弦半长 = %.3f  PHI = %.2f°'
          % (str_y, half, math.degrees(math.atan2(DRAW_DZ, tip_x))))
    print('导轨前端 z=%.3f 顶面 y=%.3f   弩箭 尾 z=%.3f 尖 z=%.3f y=%.3f'
          % (rail_front, rail_top, bolt_rear, bolt_tip, bolt_y))
    lmin, lzmax = meshes['limb_L'][0], meshes['limb_L'][1]
    print('FLEX_PX = %.3f  FLEX_PZ = %.3f  （弓臂内端最前角 = 弓臂弯折支点，模型像素）'
          % (lmin[0] + delta[0] + step / 2.0, lmin[2] + delta[2]))
    lminx = min(abs(meshes['limb_L'][0][0]), abs(meshes['limb_R'][1][0]))
    lmaxx = max(abs(meshes['limb_L'][1][0]), abs(meshes['limb_R'][0][0]))
    print('弓臂 X 范围 %.3f ~ %.3f（模型像素）  跨度 %.2f'
          % (lminx + delta[0], lmaxx + delta[0], (lmaxx + delta[0]) * 2))

    phi = math.atan2(DRAW_DZ, tip_x)
    ok = True
    for sign, label in ((-1, 'left'), (1, 'right')):
        ex = sign * tip_x - sign * half * math.cos(phi)
        ez = nock_z + half * math.sin(phi)
        good = abs(ex) < 1e-9 and abs(ez - (nock_z + DRAW_DZ)) < 1e-9
        ok = ok and good
        print('弦%-5s 拉满内端 -> X %.4f  Z %.4f（目标 0.0000 / %.4f）%s'
              % (label, ex, ez, nock_z + DRAW_DZ, 'OK' if good else '*** 不对'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
