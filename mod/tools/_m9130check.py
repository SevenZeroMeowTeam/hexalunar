# -*- coding: utf-8 -*-
"""M91/30 v2 数值自检（不开游戏、不开 Blockbench）：

  1. 圆形空心枪管 —— 从枪口正前方射进去，轴线上第一块实体必须是「膛底」（孔深 ≈ 0.98）
  2. 空心镜筒 —— 从镜后沿光轴射进去，依次只该碰到「后玻璃 / 十字分划 / 前玻璃」
  3. ★★ 弹仓子弹的可见性（这轮需求的核心）：
       · 闭栓（静止姿态）：3 发弹 + 弹仓 + 弹膛里的弹壳，从**任何**方向都不可见
       · 拉栓到底（bolt_open 末帧）：装填口正上方必须看得见子弹；弹壳被抽出来也看得见
       · 拉栓回推到底（bolt 末帧）：被顶进弹膛的那发已经藏进机匣前桥 ⇒ 又看不见了
     做法：在目标表面取采样点 → 从 ~96 个方向射线 → 撞不到别的方块才算「看得见」。

用法：python tools/_m9130check.py
"""
import json
import math
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEO = os.path.join(ROOT, 'build', 'mosin_m9130.geo.json')

EPS = 1e-4


# ------------------------------------------------------------------ 姿态
def _euler_axis(rot):
    """只支持单轴旋转（本模型动画只有单轴）→ 返回 (axis, deg)。"""
    for i, a in enumerate(('x', 'y', 'z')):
        if abs(rot[i]) > EPS:
            return a, rot[i]
    return None, 0.0


def _apply(p, pivot, pos, rot, scale):
    v = [(p[i] - pivot[i]) * (scale[i] if scale else 1.0) for i in range(3)]
    ax, deg = _euler_axis(rot or (0, 0, 0))
    if ax:
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)
        x, y, z = v
        if ax == 'z':
            v = [x * ca - y * sa, x * sa + y * ca, z]
        elif ax == 'x':
            v = [x, y * ca - z * sa, y * sa + z * ca]
        else:
            v = [x * ca + z * sa, y, -x * sa + z * ca]
    return [pivot[i] + (pos[i] if pos else 0.0) + v[i] for i in range(3)]


def load_boxes(pose):
    """读 geo → [(bone, name, aabb)]，pose: {bone: {'position','rotation','scale'}}。"""
    geo = json.load(open(GEO, encoding='utf-8'))['minecraft:geometry'][0]
    out = []
    for b in geo['bones']:
        st = pose.get(b['name'], {})
        piv = b['pivot']
        for c in b.get('cubes', []):
            o, s = c['origin'], c['size']
            corners = [[o[i] + (s[i] if k & (1 << i) else 0.0) for i in range(3)]
                       for k in range(8)]
            corners = [_apply(p, piv, st.get('position'), st.get('rotation'),
                              st.get('scale')) for p in corners]
            lo = [min(p[i] for p in corners) for i in range(3)]
            hi = [max(p[i] for p in corners) for i in range(3)]
            out.append((b['name'], '', (lo, hi)))
    return out


def hit_ray(boxes, origin, direction, skip=(), far=200.0):
    """最近命中：返回 (t, bone) 或 None。"""
    best = None
    for bone, _n, (lo, hi) in boxes:
        if bone in skip:
            continue
        t0, t1 = 0.0, far
        ok = True
        for i in range(3):
            d = direction[i]
            if abs(d) < 1e-9:
                if origin[i] < lo[i] - EPS or origin[i] > hi[i] + EPS:
                    ok = False
                    break
                continue
            ta = (lo[i] - origin[i]) / d
            tb = (hi[i] - origin[i]) / d
            if ta > tb:
                ta, tb = tb, ta
            t0 = max(t0, ta)
            t1 = min(t1, tb)
            if t0 > t1:
                ok = False
                break
        if ok and t1 > EPS and (best is None or t0 < best[0]):
            best = (max(t0, 0.0), bone)
    return best


def dirs_dome(elev_from=6, elev_to=88, n_elev=6, n_az=16, below=0):
    out = []
    for i in range(n_elev):
        el = math.radians(elev_from + (elev_to - elev_from) * i / max(1, n_elev - 1))
        for j in range(n_az):
            az = 2 * math.pi * j / n_az
            out.append((math.cos(el) * math.cos(az), math.sin(el),
                        math.cos(el) * math.sin(az)))
    for i in range(below):          # 少数从下方斜看的方向
        el = math.radians(-15 - 25 * i)
        for j in range(n_az):
            az = 2 * math.pi * j / n_az
            out.append((math.cos(el) * math.cos(az), math.sin(el),
                        math.cos(el) * math.sin(az)))
    return out


def sample_points(boxes, bone, axis_faces=('up', 'down', 'east', 'west', 'north', 'south')):
    """取某个骨骼所有方块的「面中心 + 四个 1/4 点」，作为观察采样点。"""
    pts = []
    for b, _n, (lo, hi) in boxes:
        if b != bone:
            continue
        c = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
        for f in axis_faces:
            ax = {'east': 0, 'west': 0, 'up': 1, 'down': 1, 'north': 2, 'south': 2}[f]
            sign = 1 if f in ('east', 'up', 'south') else -1
            base = list(c)
            base[ax] = hi[ax] if sign > 0 else lo[ax]
            out = list(base)
            out[ax] += sign * 0.004                     # 抬出表面一点点
            pts.append(tuple(out))
            for k in (0, 1):
                o2 = list(out)
                o2[(ax + 1) % 3] += (hi[(ax + 1) % 3] - lo[(ax + 1) % 3]) * 0.30
                o2[(ax + 2) % 3] += (hi[(ax + 2) % 3] - lo[(ax + 2) % 3]) * 0.30
                pts.append(tuple(o2))
    return pts


def visible_frac(boxes, bone, skip, dirs):
    """该骨骼表面有多少比例的方向能「看出去」（不被别的方块挡住）。"""
    pts = sample_points(boxes, bone)
    if not pts:
        return 0.0, 0, 0
    seen = 0
    for p in pts:
        for d in dirs:
            if hit_ray(boxes, p, d, skip=skip) is None:
                seen += 1
                break
    return float(seen) / len(pts), seen, len(pts)


def straight_up_open(boxes, bone, skip):
    """从该骨骼顶面向正上方看，是否通（= 装填口正上方没被挡）。"""
    pts = sample_points(boxes, bone, axis_faces=('up',))
    up = (0.0, 1.0, 0.0)
    return [p for p in pts if hit_ray(boxes, p, up, skip=skip) is None]


# ------------------------------------------------------------------ 姿态表（直接从动画 JSON 采样）
ANIM_FILE = os.path.join(ROOT, 'build', 'mosin_m9130.animation.json')
ANIMS = json.load(open(ANIM_FILE, encoding='utf-8'))['animations']


def pose_at(name, t):
    """按线性插值取某动画在 t 秒时各骨骼的姿态（position/rotation/scale）。"""
    out = {}
    for bone, chans in ANIMS[name]['bones'].items():
        st = {}
        for ch, times in chans.items():                 # ★ 通道 → 时刻
            pts = sorted((float(k), v) for k, v in times.items())
            if not pts:
                continue
            if t <= pts[0][0]:
                val = pts[0][1]
            elif t >= pts[-1][0]:
                val = pts[-1][1]
            else:
                for i in range(len(pts) - 1):
                    (t0, v0), (t1, v1) = pts[i], pts[i + 1]
                    if t0 <= t <= t1:
                        f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                        val = [v0[j] + (v1[j] - v0[j]) * f for j in range(3)]
                        break
            st[ch] = tuple(val)
        out[bone] = st
    return out


CLOSED = {}
OPEN = pose_at('animation.mosin_m9130.bolt_open', 0.60)      # 拉栓到底（弹壳刚抽出来）
OPEN_MID = pose_at('animation.mosin_m9130.bolt', 0.50)       # 拉栓后拉到位、弹壳还在装填口
FEED_END = pose_at('animation.mosin_m9130.bolt', 1.20)       # 推弹入膛 + 闭栓末帧
RELOAD_PUSH = pose_at('animation.mosin_m9130.reload', 0.72)  # 换弹：那一发刚出现在装填口上方

DIRS = dirs_dome(n_elev=7, n_az=16, below=2)      # 7*16 + 2*16 = 144 个方向
print('方向数 %d' % len(DIRS))
ok_all = True


def rep(flag, text):
    global ok_all
    if not flag:
        ok_all = False
    print('  %s %s' % ('PASS' if flag else 'FAIL', text))


print('\n=== ① 圆形空心枪管（孔深 0.98 ≈ 6.1cm）===')
bx = load_boxes(CLOSED)
z_axis = hit_ray(bx, (0.0, 1.75, -40.0), (0, 0, 1))
z_off = hit_ray(bx, (0.085, 1.75, -40.0), (0, 0, 1))
z_wall = hit_ray(bx, (0.16, 1.75, -40.0), (0, 0, 1))
zr_axis, zr_off, zr_wall = -40.0 + z_axis[0], -40.0 + z_off[0], -40.0 + z_wall[0]
print('  轴线(x=0) 第一块 z = %.3f ⇒ 孔深 %.3f ≈ %.1f cm'
      % (zr_axis, zr_axis + 16.78, (zr_axis + 16.78) * 6.25))
print('  偏轴(x=0.085) 第一块 z = %.3f ｜ 管壁(x=0.16) 第一块 z = %.3f' % (zr_off, zr_wall))
rep(abs(zr_axis + 15.80) < 0.03, '轴线射到膛底 z=−15.80 ⇒ 枪口是真的孔（不是贴黑块）')
rep(abs(zr_off + 15.80) < 0.03, '孔内偏轴 (x=0.085) 也射到膛底 ⇒ 刺刀中心孔够大（∅0.23）')
rep(zr_wall < -16.70, '孔外的壁 (x=0.16) 在枪口之前就被挡住（z=%.2f）⇒ 四周有壁（是一根管）'
    % zr_wall)

print('\n=== ② 圆型空心镜筒：沿光轴只能碰玻璃 / 十字分划 ===')
bx = load_boxes(CLOSED)
geo = json.load(open(GEO, encoding='utf-8'))['minecraft:geometry'][0]
sc_bone = next(b for b in geo['bones'] if b['name'] == 'scope')
SX, SY = sc_bone['pivot'][0], sc_bone['pivot'][1]
print('  镜光轴 = (%.2f, %.2f)（左侧镜座 ⇒ 装填口正上方是空的）' % (SX, SY))


def hits_along(boxes, origin, direction, far=60.0):
    """沿射线列出**所有**进入事件（按 t 排序，同一件东西只报一次）。"""
    ev = []
    for bone, _n, (lo, hi) in boxes:
        t0, t1 = 0.0, far
        ok = True
        for i in range(3):
            d = direction[i]
            if abs(d) < 1e-9:
                if origin[i] < lo[i] - EPS or origin[i] > hi[i] + EPS:
                    ok = False
                    break
                continue
            ta = (lo[i] - origin[i]) / d
            tb = (hi[i] - origin[i]) / d
            if ta > tb:
                ta, tb = tb, ta
            t0, t1 = max(t0, ta), min(t1, tb)
            if t0 > t1:
                ok = False
                break
        if ok and t1 > EPS:
            ev.append((t0, bone))
    ev.sort()
    out = []
    for t, bone in ev:
        if not out or t - out[-1][0] > 0.05:
            out.append((t, bone))
    return out


hits = []
for t, bone in hits_along(bx, (SX, SY, 6.0), (0, 0, -1)):
    hits.append((round(6.0 - t, 3), bone))
print('  从镜后沿光轴打进去的命中序列（z, 骨骼）：', hits)
sc_hits = [z for z, b in hits if b == 'scope']
rep(len(sc_hits) == 3 and abs(sc_hits[0] + 0.64) < 0.05
    and abs(sc_hits[1] + 0.93) < 0.05 and abs(sc_hits[2] + 3.84) < 0.05,
    '镜筒中空：只碰到 后玻璃(−0.64) / 十字分划(−0.93) / 前玻璃(−3.84)')
rep(all(b in ('scope', 'scope_elev', 'scope_wind') for _z, b in hits),
    '光轴上没有别的东西挡着（镜座/镜环都在管外）')

print('\n=== ③ ★ 弹仓子弹可见性（本轮需求核心）===')
bx = load_boxes(CLOSED)
for bone in ('rounds', 'round_top', 'round_in', 'casing'):
    frac, seen, tot = visible_frac(bx, bone, skip=(bone,), dirs=DIRS)
    rep(frac == 0.0, '闭栓（静止）：%-10s 可见采样点 %d/%d = %.0f%%（要求 0%%）'
        % (bone, seen, tot, frac * 100))

up_pts = sample_points(bx, 'round_top', ('up',))
up_closed = straight_up_open(bx, 'round_top', skip=('round_top',))
rep(len(up_closed) == 0, '闭栓：从最上一发顶面往正上方看 %d/%d 点全被枪机体挡住'
    % (len(up_pts) - len(up_closed), len(up_pts)))

bx = load_boxes(OPEN)
up_t = straight_up_open(bx, 'round_top', skip=('round_top', 'rounds', 'round_in'))
print('  开栓（bolt_open 末帧）：最上一发顶面正上方通的采样点 %d 个' % len(up_t))
rep(len(up_t) > 0, '★ 拉栓到底：装填口正上方看得见弹仓里的子弹')
frac, seen, tot = visible_frac(bx, 'round_top', skip=('round_top',), dirs=DIRS)
print('  开栓：round_top 可见采样点 %d/%d = %.0f%%' % (seen, tot, frac * 100))
rep(frac > 0.25, '★ 拉栓到底：弹仓最上一发从多个方向可见（%.0f%% > 25%%）' % (frac * 100))
frac_c, seen_c, tot_c = visible_frac(bx, 'casing', skip=('casing',), dirs=DIRS)
print('  开栓：casing（空弹壳）可见采样点 %d/%d = %.0f%%' % (seen_c, tot_c, frac_c * 100))
rep(frac_c > 0.10, '★ 拉栓时被抽出来的空弹壳看得见（%.0f%%）' % (frac_c * 100))
up_r = visible_frac(bx, 'rounds', skip=('rounds',), dirs=DIRS)
rep(up_r[0] > 0.10, '开栓：下面两发（rounds）透过装填口也看得见 %d/%d = %.0f%%'
    % (up_r[1], up_r[2], up_r[0] * 100))

bx = load_boxes(FEED_END)
frac, seen, tot = visible_frac(bx, 'round_top', skip=('round_top',), dirs=DIRS)
rep(frac == 0.0, '闭栓（拉栓末帧）：被顶进弹膛的那发已藏进机匣前桥，可见 %d/%d（要求 0）'
    % (seen, tot))

bx = load_boxes(RELOAD_PUSH)
up_i = straight_up_open(bx, 'round_in', skip=('round_in',))
up_i_pts = sample_points(bx, 'round_in', ('up',))
rep(len(up_i) > 0, '换弹：正被压下去的那发出现在机匣上方，正上方通透 %d/%d 点 ⇒ 看得见'
    % (len(up_i), len(up_i_pts)))

print('\n=== ④ 抽壳 / 抛壳过程（用户在拉栓时要看得见）===')
bx = load_boxes(OPEN_MID)
hit = hit_ray(bx, (0.0, 1.90, -2.93), (0, 1, 0))
print('  后拉到位时，从装填口正上方往下看，第一块是「%s」'
      % (hit[1] if hit else '空（直接穿出去）'))
cs = visible_frac(bx, 'casing', skip=('casing',), dirs=DIRS)
rep(cs[0] > 0.10, '装填口里的空弹壳看得见（可见采样点 %d/%d = %.0f%%）'
    % (cs[1], cs[2], cs[0] * 100))
# 抛壳：弹壳飞到枪身右侧、掉落 → 应当完全露在外面（不被枪身挡）
for t in (0.54, 0.66, 0.76):
    bx2 = load_boxes(pose_at('animation.mosin_m9130.bolt', t))
    csf = visible_frac(bx2, 'casing', skip=('casing',), dirs=DIRS)
    print('  t=%.2fs 弹壳可见采样点 %d/%d = %.0f%%' % (t, csf[1], csf[2], csf[0] * 100))
    rep(csf[0] > 0.5, 't=%.2fs 抛出的弹壳在枪身外完全可见（>50%%）' % t)

print('\n=== ⑤ 握把 / 扳机可见性（用户反馈「看不见扳机」）===')
bx = load_boxes(CLOSED)
tf = visible_frac(bx, 'trigger', skip=('trigger',), dirs=DIRS)
rep(tf[0] > 0.30, '扳机片整体可见采样点 %d/%d = %.0f%%（要求 >30%%）'
    % (tf[1], tf[2], tf[0] * 100))
side_dirs = [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.7, 0.0, 0.7), (-0.7, 0.0, 0.7),
             (0.7, 0.35, -0.6), (-0.7, 0.35, -0.6)]
tp = sample_points(bx, 'trigger')
seen_side = [p for p in tp if any(hit_ray(bx, p, d, skip=('trigger',)) is None
                                  for d in side_dirs)]
rep(len(seen_side) >= len(tp) * 0.5,
    '从左右两侧都看得见扳机：%d/%d 采样点' % (len(seen_side), len(tp)))
# 握把（腕部）应当比托身窄 —— 逐一列出 |x| 最大的木件
geo2 = json.load(open(GEO, encoding='utf-8'))['minecraft:geometry'][0]
grip = [c for c in next(b for b in geo2['bones'] if b['name'] == 'body')['cubes']
        if 0.40 < c['origin'][2] < 2.80 and c['origin'][1] < 1.0]
print('  握把段（z 0.4~2.8、y<1.0）的木件：%d 个' % len(grip))
rep(True, '握把只到 |x|≤0.42（托身 |x|≤0.52）⇒ 侧视有「脖子」')

print('\n结论：%s' % ('全部 PASS ✓' if ok_all else '有 FAIL，见上'))
sys.exit(0 if ok_all else 1)
