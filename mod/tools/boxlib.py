#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""方块模型公共库：512² 逐面 UV 图集 + 材质画法 + geo.json 生成。

约定：16 u = 1 方块；UV 用像素坐标（geo.json 的 uv/uv_size 就是像素）。
每个「面」单独分配一块贴图矩形 → 比例正确、可以做逐面 AO/倒角。
"""
import json
import math

from PIL import Image, ImageDraw

SIZE = 512
S = 11.0          # 每模型单位分配的贴图像素数（贴图密度）
UVCAP = 120       # 单个面 UV 矩形的最大边长（长条部件拉伸而不是撑爆图集）
FACE_SEED = {'north': 11, 'south': 29, 'east': 47, 'west': 71, 'up': 89, 'down': 103}
FACE_ALL = ('north', 'south', 'east', 'west', 'up', 'down')


class Pack(object):
    """货架式装箱。

    `plan()` 先按高度降序排一遍再分配 —— 长条部件（弓片/弦/导杆）的侧面又高又窄，
    不排序的话货架会浪费掉大量空间直接溢出。
    """

    def __init__(self, size=SIZE):
        self.size = size
        self.x, self.y, self.rowh = 1, 1, 0
        self.boxes = {}

    def plan(self, items):
        for key, w, h in sorted(items, key=lambda t: -t[2]):
            self.alloc(key, w, h)

    def alloc(self, key, w, h):
        w = max(2, int(math.ceil(w)))
        h = max(2, int(math.ceil(h)))
        if self.x + w > self.size - 1:
            self.x, self.y, self.rowh = 1, self.y + self.rowh + 1, 0
        if self.y + h > self.size - 1:
            raise RuntimeError('atlas overflow at %s (%d,%d)' % (key, w, h))
        r = (self.x, self.y, w, h)
        self.x += w + 1
        self.rowh = max(self.rowh, h)
        self.boxes[key] = r
        return r


class LC(object):
    """确定性 LCG，保证每次生成的贴图一致。"""

    def __init__(self, seed):
        self.s = (int(seed) * 1103515245 + 12345) & 0x7FFFFFFF or 1

    def f(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s / float(0x7FFFFFFF)

    def r(self, a, b):
        return a + (b - a) * self.f()

    def ri(self, a, b):
        return int(self.r(a, b + 0.999))


def cl(v):
    return int(max(0, min(255, v)))


def sh(c, f, add=0):
    return (cl(c[0] * f + add), cl(c[1] * f + add), cl(c[2] * f + add))


# ------------------------------------------------------------------ 材质画法
def _metal(img, rect, rn, base, horiz):
    x, y, w, h = rect
    px = img.load()
    for j in range(h):
        rowf = 1.0 + rn.r(-0.045, 0.045)
        for i in range(w):
            c = sh(base, rowf * rn.r(0.955, 1.045))
            px[x + i, y + j] = (c[0], c[1], c[2], 255)
    for _ in range(int(w * h / 45) + 1):
        bx, by = rn.ri(0, w - 1), rn.ri(0, h - 1)
        f = rn.r(0.80, 0.90) if rn.f() < 0.6 else rn.r(1.06, 1.14)
        n = rn.ri(1, max(1, (w if horiz else h) // 4))
        for k in range(n):
            xx = min(w - 1, bx + k) if horiz else bx
            yy = by if horiz else min(h - 1, by + k)
            c = px[x + xx, y + yy]
            px[x + xx, y + yy] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)


def _brushed(img, rect, rn, base, seed):
    x, y, w, h = rect
    px = img.load()
    for j in range(h):
        for i in range(w):
            f = 0.94 + 0.10 * math.sin(i * 0.8 + seed) + rn.r(-0.035, 0.035)
            c = sh(base, f)
            px[x + i, y + j] = (c[0], c[1], c[2], 255)


def _wood(img, rect, rn, base, seed):
    x, y, w, h = rect
    px = img.load()
    for j in range(h):
        grain = math.sin(j * rn.r(0.55, 0.95) + seed) * 0.5 + 0.5
        f = 0.90 + 0.16 * grain + rn.r(-0.05, 0.05)
        band = 0.72 if any((j + k * 7) % 11 == 0 for k in range(3)) else 1.0
        for i in range(w):
            c = sh(base, f * band * (1.0 - 0.06 * abs(i / max(w - 1, 1) - 0.5) * 2))
            px[x + i, y + j] = (c[0], c[1], c[2], 255)
    for j in range(h):
        if rn.f() < 0.22:
            f = rn.r(1.14, 1.24)
            for i in range(w):
                c = px[x + i, y + j]
                px[x + i, y + j] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)


def _checker(img, rect, rn, base):
    x, y, w, h = rect
    px = img.load()
    for j in range(h):
        for i in range(w):
            f = 0.86 if ((i // 2 + j // 2) % 2 == 0) else 1.06
            c = sh(base, f * rn.r(0.94, 1.06))
            px[x + i, y + j] = (c[0], c[1], c[2], 255)


def _ribs(img, rect, rn, base):
    x, y, w, h = rect
    px = img.load()
    for j in range(h):
        f = 0.86 if (j % 4 in (0, 1)) else 1.05
        for i in range(w):
            c = sh(base, f * rn.r(0.95, 1.05))
            px[x + i, y + j] = (c[0], c[1], c[2], 255)
        px[x + w - 1, y + j] = sh(base, 0.70)


def _flat_col(img, rect, rn, base, horiz=None):
    x, y, w, h = rect
    px = img.load()
    for j in range(h):
        for i in range(w):
            c = sh(base, rn.r(0.97, 1.03))
            px[x + i, y + j] = (c[0], c[1], c[2], 255)


def _plastic(img, rect, rn, base, horiz=None):
    x, y, w, h = rect
    px = img.load()
    for j in range(h):
        for i in range(w):
            c = sh(base, rn.r(0.94, 1.05))
            px[x + i, y + j] = (c[0], c[1], c[2], 255)
    for _ in range(int(w * h / 30) + 1):
        i, j = rn.ri(0, w - 1), rn.ri(0, h - 1)
        f = rn.r(1.05, 1.12)
        c = px[x + i, y + j]
        px[x + i, y + j] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)


def _cloth(img, rect, rn, base, horiz=None):
    """手套/布料：斜织纹细噪点（无金属拉丝、无镜面高光）。"""
    x, y, w, h = rect
    px = img.load()
    for j in range(h):
        rowf = 1.0 + rn.r(-0.02, 0.02)
        for i in range(w):
            wv = 1.035 if (i + j) % 3 == 0 else 0.985
            c = sh(base, rowf * wv * rn.r(0.98, 1.02))
            px[x + i, y + j] = (c[0], c[1], c[2], 255)


KINDS = {'metal': _metal, 'brushed': _brushed, 'wood': _wood, 'checker': _checker,
         'ribs': _ribs, 'flat': _flat_col, 'plastic': _plastic, 'cloth': _cloth}

# 抛光强度：0 = 关（回到旧的纯 AO 边缘），1 = 默认。脚本可改这个值调各模型的光泽。
GLOSS = 1.0

# 曲率阴影用的光方向（模型坐标，已归一化）：上方 + 略偏玩家一侧
LIGHT = (0.40, 0.84, 0.36)
CURV_AMBIENT = 0.56
CURV_DIFFUSE = 0.78

_FACE_N = {'north': (0.0, 0.0, -1.0), 'south': (0.0, 0.0, 1.0),
           'east': (1.0, 0.0, 0.0), 'west': (-1.0, 0.0, 0.0),
           'up': (0.0, 1.0, 0.0), 'down': (0.0, -1.0, 0.0)}


def _norm3(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / n, v[1] / n, v[2] / n) if n > 1e-9 else (0.0, 1.0, 0.0)


def curv_shade(curv, fc):
    """按面的中心点算曲率阴影系数（球/柱体不再只有 6 级面朝向明暗）。

    curv = ('sphere', (cx, cy, cz)) 或 ('cyl', 'x'|'y'|'z', (a, b))。
    """
    if not curv:
        return None
    kind = curv[0]
    if kind == 'sphere':
        c = curv[1]
        n = _norm3((fc[0] - c[0], fc[1] - c[1], fc[2] - c[2]))
    elif kind == 'cyl':
        axis, (a, b) = curv[1], curv[2]
        if axis == 'x':
            n = _norm3((0.0, fc[1] - a, fc[2] - b))
        elif axis == 'y':
            n = _norm3((fc[0] - a, 0.0, fc[2] - b))
        else:
            n = _norm3((fc[0] - a, fc[1] - b, 0.0))
    else:
        return None
    d = max(0.0, n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2])
    return CURV_AMBIENT + CURV_DIFFUSE * d


def paint(img, rect, kind, face, tag, seed, base, detail=None, ao=0.20, ao_b=None,
          gloss=None, tint=None):
    """画一个面：材质底 + 细节 + tint（曲率阴影）+ 抛光（光泽/倒角/高光斑）+ 边缘 AO。"""
    rn = LC(seed)
    x, y, w, h = rect
    horiz = w >= h
    fn = KINDS.get(kind, _metal)
    if kind in ('brushed', 'wood'):
        fn(img, rect, rn, base, seed)
    else:
        fn(img, rect, rn, base, horiz)
    if detail:
        detail(img, rect, face, seed)
    px = img.load()
    if tint is not None and abs(tint - 1.0) > 1e-4:
        for j in range(h):
            for i in range(w):
                c = px[x + i, y + j]
                px[x + i, y + j] = (cl(c[0] * tint), cl(c[1] * tint),
                                    cl(c[2] * tint), 255)
    g = (GLOSS if gloss is None else gloss)
    b = ao_b if ao_b is not None else (1 if min(w, h) <= 10 else 2)

    # ---- 抛光 1：竖向光泽渐变（上半部亮、下半部收暗，像曲面把天光反到上缘）
    if g > 0.0:
        for j in range(h):
            t = j / float(max(h - 1, 1))
            f = 1.0 + 0.085 * g * (1.0 - t) ** 1.6
            for i in range(w):
                c = px[x + i, y + j]
                px[x + i, y + j] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)

    # ---- 抛光 2：倒角。上沿给高光带（不是 AO 暗边），下沿给反光暗带
    hi = (1.28, 1.13)
    lo = (0.72, 0.87)
    for i in range(w):
        for k in range(b):
            if g > 0.0:
                f = 1.0 + (hi[k] - 1.0) * g
                c = px[x + i, y + k]
                px[x + i, y + k] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)
                f = 1.0 + (lo[k] - 1.0) * g
                c = px[x + i, y + h - 1 - k]
                px[x + i, y + h - 1 - k] = (cl(c[0] * f), cl(c[1] * f),
                                            cl(c[2] * f), 255)
            else:
                f = 1.0 - ao * (1.0 - k / float(b))
                for yy in (y + k, y + h - 1 - k):
                    c = px[x + i, yy]
                    px[x + i, yy] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)
    # 左右边缘仍旧轻微收暗，保留体积感
    for j in range(h):
        for k in range(b):
            f = 1.0 - ao * 0.75 * (1.0 - k / float(b))
            for xx in (x + k, x + w - 1 - k):
                c = px[xx, y + j]
                px[xx, y + j] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)

    # ---- 抛光 3：镜面高光斑（上半部几道短亮线，像抛光金属的反光痕）
    if g > 0.0 and min(w, h) >= 6 and kind not in ('wood', 'ribs', 'checker', 'cloth'):
        for _ in range(int(w * h / 300.0) + 1):
            bx, by = rn.ri(0, max(0, w - 1)), rn.ri(0, max(0, max(0, h // 3)))
            ln = rn.ri(1, max(1, w // 3))
            fl = 1.0 + (rn.r(1.20, 1.42) - 1.0) * g
            for kk in range(ln):
                xx = min(w - 1, bx + kk)
                c = px[x + xx, y + by]
                px[x + xx, y + by] = (cl(c[0] * fl), cl(c[1] * fl), cl(c[2] * fl), 255)

    if face == 'up':
        for i in range(w):
            for k in range(b + 1):
                c = px[x + i, y + k]
                px[x + i, y + k] = (cl(c[0] * 1.10), cl(c[1] * 1.10), cl(c[2] * 1.10), 255)
    if face == 'down':
        for i in range(w):
            for k in range(b + 1):
                c = px[x + i, y + h - 1 - k]
                px[x + i, y + h - 1 - k] = (cl(c[0] * 0.86), cl(c[1] * 0.86),
                                            cl(c[2] * 0.86), 255)


# ------------------------------------------------------------------ 几何 & 输出
def cube(bone, name, x, y, z, mat, rot=None, piv=None, tag=None, kind=None, curv=None):
    """mat=(r,g,b) 基色；kind 指定材质画法；tag 给逐面细节用；
    curv=('sphere',(cx,cy,cz)) 或 ('cyl','x'|'y'|'z',(a,b)) 给曲面烘连续明暗。"""
    return {'bone': bone, 'name': name, 'x': x, 'y': y, 'z': z, 'mat': mat,
            'rot': rot, 'piv': piv, 'tag': tag, 'kind': kind or 'metal', 'curv': curv}


def build(bones, cubes, identifier, size=SIZE, details=None, density=S, cap=UVCAP):
    """生成 (geo_dict, PIL.Image)。details: {tag: fn(img, rect, face, seed)}"""
    img = Image.new('RGBA', (size, size), (12, 12, 12, 255))
    pack = Pack(size)
    out_bones = {b[0]: {'name': b[0], 'pivot': list(b[2])} for b in bones}
    for name, parent, _p in bones:
        if parent:
            out_bones[name]['parent'] = parent
        out_bones[name]['cubes'] = []
    details = details or {}

    # 第一遍：算每个面的 UV 矩形尺寸，按高度降序装箱
    faces_of = []
    plan = []
    for n, cb in enumerate(cubes, start=1):
        x0, x1 = cb['x']
        y0, y1 = cb['y']
        z0, z1 = cb['z']
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        sizes = {'north': (sx, sy), 'south': (sx, sy), 'east': (sz, sy),
                 'west': (sz, sy), 'up': (sx, sz), 'down': (sx, sz)}
        for face, (fw, fh) in sizes.items():
            pw = min(cap, max(2, fw * density))
            ph = min(cap, max(2, fh * density))
            key = '%s/%s/%s' % (cb['bone'], cb['name'], face)
            plan.append((key, pw, ph))
        faces_of.append((n, cb, sizes))
    pack.plan(plan)

    for n, cb, sizes in faces_of:
        x0, x1 = cb['x']
        y0, y1 = cb['y']
        z0, z1 = cb['z']
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        cd = {'origin': [round(x0, 4), round(y0, 4), round(z0, 4)],
              'size': [round(sx, 4), round(sy, 4), round(sz, 4)]}
        if cb['rot']:
            cd['rotation'] = [float(v) for v in cb['rot']]
            cd['pivot'] = [float(v) for v in (cb['piv'] or (0, 0, 0))]
        uv = {}
        for face in ('north', 'south', 'east', 'west', 'up', 'down'):
            tag = cb['tag'] or ''
            detail = details.get(tag)
            rect = pack.boxes['%s/%s/%s' % (cb['bone'], cb['name'], face)]
            # 曲面件：按该面中心点的法线方向烘连续明暗，并关掉 AO/倒角（否则一颗球会变成马赛克）
            fc = ((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5)
            shade = curv_shade(cb.get('curv'), fc)
            if shade is None:
                paint(img, rect, cb['kind'], face, tag, n * 977 + FACE_SEED[face],
                      cb['mat'], detail)
            else:
                paint(img, rect, cb['kind'], face, tag, n * 977 + FACE_SEED[face],
                      cb['mat'], detail, ao=0.0, gloss=0.18, tint=shade)
            uv[face] = {'uv': [float(rect[0]), float(rect[1])],
                        'uv_size': [float(rect[2]), float(rect[3])]}
        cd['uv'] = uv
        out_bones[cb['bone']]['cubes'].append(cd)
    blist = []
    for name, parent, pivot in bones:
        b = out_bones[name]
        if not b['cubes']:
            b.pop('cubes')
        blist.append(b)
    geo = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': identifier, 'texture_width': size,
                        'texture_height': size, 'visible_bounds_width': 3,
                        'visible_bounds_height': 3, 'visible_bounds_offset': [0, 0, 0]},
        'bones': blist}]}
    return geo, img


def write(geo, img, geo_path, tex_path, quiet=False):
    with open(geo_path, 'w', encoding='utf-8') as fh:
        json.dump(geo, fh, ensure_ascii=False, separators=(',', ':'))
    img.save(tex_path)
    n = sum(len(b.get('cubes', [])) for b in geo['minecraft:geometry'][0]['bones'])
    if not quiet:
        print('bones %d  cubes %d' % (len(geo['minecraft:geometry'][0]['bones']), n))
        print('wrote', geo_path)
        print('wrote', tex_path)
    return n


def sphere_slabs(radius, cy, n, k=0.414, shrink=0.965):
    """把半径为 radius、球心高度 cy 的球沿 Y 切成 n 层，返回 [(y0,y1,r), ...]。

    每层用「十字双盒」拟八边形截面 —— 比单个方盒圆得多。r 取该层正中的球半径，
    于是纵向也形成方形像素圆的阶梯。
    """
    out = []
    step = 2.0 * radius / n
    for i in range(n):
        y0 = cy - radius + i * step
        y1 = y0 + step
        yc = (y0 + y1) / 2.0
        t = abs(yc - cy) / radius
        r = radius * math.sqrt(max(0.0, 1.0 - t * t)) if t < 1.0 else 0.0
        out.append((y0, y1, max(r, radius * 0.20) * shrink))
    return out


def bolt(bone, prefix, cx, cy, cz, r, h, mat, axis='x', tag=None, kind='metal',
         dark=None):
    """螺钉 / 铆钉：一个凸出的小方台 +（可选）一道更暗的一字槽。

    (cx, cy, cz) 是**贴合面上的中心点**，axis 是拧入方向，h = 凸出高度（可为负，表示往
    反向凸，用于左侧零件），r = 半径。
    """
    def rng(a, b):
        return (a, b) if a <= b else (b, a)

    if axis == 'x':
        head = (rng(cx, cx + h), (cy - r, cy + r), (cz - r, cz + r))
        top = max(cx, cx + h)
        slot = (rng(top - 0.028, top + 0.028), (cy - r * 0.78, cy + r * 0.78),
                (cz - r * 0.16, cz + r * 0.16))
    elif axis == 'y':
        head = ((cx - r, cx + r), rng(cy, cy + h), (cz - r, cz + r))
        top = max(cy, cy + h)
        slot = ((cx - r * 0.78, cx + r * 0.78), rng(top - 0.028, top + 0.028),
                (cz - r * 0.16, cz + r * 0.16))
    else:
        head = ((cx - r, cx + r), (cy - r, cy + r), rng(cz, cz + h))
        top = max(cz, cz + h)
        slot = ((cx - r * 0.78, cx + r * 0.78), (cy - r * 0.16, cy + r * 0.16),
                rng(top - 0.028, top + 0.028))
    out = [cube(bone, prefix + '_head', head[0], head[1], head[2], mat, tag=tag, kind=kind)]
    if dark is not None:
        out.append(cube(bone, prefix + '_slot', slot[0], slot[1], slot[2], dark, tag=tag,
                        kind='flat'))
    return out


def vents(bone, prefix, region, n, mat, along='y', tag=None, kind='flat', fill=0.42):
    """成排的凹槽 / 散热槽：在 region 里沿 along 方向均分 n 条（用暗色小盒表示凹进去）。

    region = (x0, x1, y0, y1, z0, z1)，是**槽所在的那一层**外包盒。
    """
    x0, x1, y0, y1, z0, z1 = region
    out = []
    for i in range(n):
        t = (i + 0.5) / n
        if along == 'y':
            c, half = y0 + (y1 - y0) * t, (y1 - y0) / n * fill
            box = ((x0, x1), (c - half, c + half), (z0, z1))
        elif along == 'z':
            c, half = z0 + (z1 - z0) * t, (z1 - z0) / n * fill
            box = ((x0, x1), (y0, y1), (c - half, c + half))
        else:
            c, half = x0 + (x1 - x0) * t, (x1 - x0) / n * fill
            box = ((c - half, c + half), (y0, y1), (z0, z1))
        out.append(cube(bone, '%s_%d' % (prefix, i), box[0], box[1], box[2], mat,
                        tag=tag, kind=kind))
    return out


def cross_boxes(bone, prefix, y0, y1, r, cx, cz, mat, kind, tag=None, k=0.414, curv=None):
    """用两个正交盒子拼出八边形截面的柱体。

    默认给曲率阴影（按 'y' 轴圆柱）—— 这样八边形柱看起来是圆的；
    做球面时传 curv=('sphere',(cx, cy, cz)) 才能纵向也连续。
    """
    if curv is None:
        curv = ('cyl', 'y', (cx, cz))
    a = k * r
    return [
        cube(bone, prefix + '_a', (cx - r, cx + r), (y0, y1), (cz - a, cz + a), mat,
             tag=tag, kind=kind, curv=curv),
        cube(bone, prefix + '_b', (cx - a, cx + a), (y0, y1), (cz - r, cz + r), mat,
             tag=tag, kind=kind, curv=curv),
    ]


def ring(bone, prefix, cx, cy, cz, r, tube, mat, kind, axis='x', seg=8):
    """八边形圆环（axis = 环的法线轴：'x' → 环在 Y-Z 平面）。

    每段是一个「弦」小盒：局部 Z 指向切线、局部 Y 指向径向、局部 X 为环厚。
    """
    out = []
    L = 2.0 * r * math.sin(math.pi / seg) * 1.15
    for i in range(seg):
        ang = 2 * math.pi * i / seg
        ca, sa = math.cos(ang), math.sin(ang)
        for off in (0.0,):
            a = ang + off
            ca, sa = math.cos(a), math.sin(a)
            if axis == 'x':
                cyy, czz = cy + r * ca, cz + r * sa
                box = ((cx - tube / 2, cx + tube / 2), (cyy - tube / 2, cyy + tube / 2),
                       (czz - L / 2, czz + L / 2))
                rot, piv = (math.degrees(a), 0, 0), (cx, cyy, czz)
            elif axis == 'y':
                cxx, czz = cx + r * ca, cz + r * sa
                box = ((cxx - tube / 2, cxx + tube / 2), (cy - tube / 2, cy + tube / 2),
                       (czz - L / 2, czz + L / 2))
                rot, piv = (0, math.degrees(a), 0), (cxx, cy, czz)
            else:
                cxx, cyy = cx + r * ca, cy + r * sa
                box = ((cxx - tube / 2, cxx + tube / 2), (cyy - tube / 2, cyy + tube / 2),
                       (cz - L / 2, cz + L / 2))
                rot, piv = (0, 0, math.degrees(a)), (cxx, cyy, cz)
            out.append(cube(bone, '%s_%d' % (prefix, i), box[0], box[1], box[2], mat,
                            rot=rot, piv=piv, kind=kind))
    return out


def arc_boxes(bone, prefix, pts, thick, half_w, mat, kind, tag=None, plane='xy',
              offset=0.0):
    """沿折线放一串旋转小盒（压把/杆件）。

    plane='xy'：折线在 X-Y 平面，盒子的宽沿 Z，绕 Z 轴转；
    plane='yz'：折线在 Y-Z 平面，盒子的宽沿 X，绕 X 轴转。
    """
    out = []
    for i, p in enumerate(pts):
        if i == 0:
            d = (pts[1][0] - p[0], pts[1][1] - p[1])
            seg = math.hypot(d[0], d[1])
        elif i == len(pts) - 1:
            d = (p[0] - pts[i - 1][0], p[1] - pts[i - 1][1])
            seg = math.hypot(d[0], d[1])
        else:
            d = (pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1])
            seg = (math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
                   + math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])) / 2.0
        if plane == 'xy':
            ang = math.degrees(math.atan2(d[1], d[0]))
        else:
            # 局部 +Z 绕 X 转 θ 后指向 (0, -sinθ, cosθ)，要它对准 (dy,dz)
            ang = math.degrees(math.atan2(-d[0], d[1]))
        h = seg * 0.62
        if plane == 'xy':
            box = ((p[0] - h, p[0] + h), (p[1] - thick / 2, p[1] + thick / 2),
                   (-half_w + offset, half_w + offset))
            out.append(cube(bone, '%s_%d' % (prefix, i), box[0], box[1], box[2], mat,
                            rot=(0, 0, ang), piv=(p[0], p[1], offset), kind=kind, tag=tag))
        else:
            box = ((-half_w + offset, half_w + offset),
                   (p[0] - thick / 2, p[0] + thick / 2),
                   (p[1] - h, p[1] + h))
            out.append(cube(bone, '%s_%d' % (prefix, i), box[0], box[1], box[2], mat,
                            rot=(ang, 0, 0), piv=(offset, p[0], p[1]), kind=kind, tag=tag))
    return out


# ------------------------------------------------------------------ 3x5 点阵字（钢印/铭文）
GLYPH = {
    'A': ('010', '101', '111', '101', '101'),
    'B': ('111', '101', '110', '101', '111'),
    'C': ('111', '100', '100', '100', '111'),
    'D': ('110', '101', '101', '101', '110'),
    'E': ('111', '100', '111', '100', '111'),
    'F': ('111', '100', '111', '100', '100'),
    'G': ('111', '100', '101', '101', '111'),
    'H': ('101', '101', '111', '101', '101'),
    'I': ('111', '010', '010', '010', '111'),
    'J': ('001', '001', '001', '101', '111'),
    'K': ('101', '101', '110', '101', '101'),
    'L': ('100', '100', '100', '100', '111'),
    'M': ('101', '111', '111', '111', '101'),
    'N': ('101', '111', '111', '101', '101'),
    'O': ('111', '101', '101', '101', '111'),
    'P': ('111', '101', '111', '100', '100'),
    'Q': ('111', '101', '101', '111', '001'),
    'R': ('111', '101', '111', '110', '101'),
    'S': ('111', '100', '111', '001', '111'),
    'T': ('111', '010', '010', '010', '010'),
    'U': ('101', '101', '101', '101', '111'),
    'V': ('101', '101', '101', '101', '010'),
    'W': ('101', '101', '111', '111', '101'),
    'X': ('101', '101', '010', '101', '101'),
    'Y': ('101', '101', '010', '010', '010'),
    'Z': ('111', '001', '010', '100', '111'),
    '0': ('111', '101', '101', '101', '111'),
    '1': ('010', '110', '010', '010', '111'),
    '2': ('111', '001', '111', '100', '111'),
    '3': ('111', '001', '111', '001', '111'),
    '4': ('101', '101', '111', '001', '001'),
    '5': ('111', '100', '111', '001', '111'),
    '6': ('111', '100', '111', '101', '111'),
    '7': ('111', '001', '010', '010', '010'),
    '8': ('111', '101', '111', '101', '111'),
    '9': ('111', '101', '111', '001', '111'),
    ' ': ('000', '000', '000', '000', '000'),
    ',': ('000', '000', '010', '010', '100'),
    '.': ('000', '000', '000', '000', '010'),
    '-': ('000', '000', '111', '000', '000'),
    '/': ('001', '001', '010', '100', '100'),
    '+': ('000', '010', '111', '010', '000'),
    ':': ('000', '010', '000', '010', '000'),
}


def text_w(s, adv=4):
    """一行点阵字的宽度（像素）。"""
    return len(s) * adv - 1


def text(d, x, y, s, color, adv=4, ytop=None, ybot=None):
    """画 3x5 点阵字（ImageDraw）。

    y 可为小数；ytop/ybot 裁剪行区间 —— 把一行字拆到相邻两个面上拼出来时必须用，
    否则字会溢出到隔壁元件自己的贴图矩形里。
    """
    ox = float(x)
    for ch in s:
        g = GLYPH.get(ch)
        if g:
            for r, row in enumerate(g):
                py = int(y) + r
                if (ytop is not None and py < ytop) or (ybot is not None and py >= ybot):
                    continue
                for c, bit in enumerate(row):
                    if bit == '1':
                        d.point((int(ox) + c, py), fill=color)
        ox += adv


def edge(img, rect, top=1.10, bot=0.86):
    """上下沿提亮/压暗。用原像素乘系数 —— 颜色跟随材质，不写死基色。"""
    x, y, w, h = rect
    px = img.load()
    for i in range(x, x + w):
        for k, f in ((y, top), (y + h - 1, bot)):
            c = px[i, k]
            px[i, k] = (cl(c[0] * f), cl(c[1] * f), cl(c[2] * f), 255)
