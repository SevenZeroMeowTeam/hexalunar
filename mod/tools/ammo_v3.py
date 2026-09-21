# -*- coding: utf-8 -*-
"""弹药 3D 模型 v3：`.338` / `7.62×59` / `7.62×61` 三种子弹的原版 JSON 模型 + 贴图。

用户（2026-09-21）：「.338，7.62x59，7.62x61 子弹模型需要重新设计并建模」。

<h2>以前是什么样</h2>
三种弹药都是 `item/generated` 的**2D 平面图**（一张 16² png 画两发斜放的子弹），
拿在手里/扔在地上就是一张纸片 —— 这次改成**真正的 3D 物品模型**（原版 `elements`，
不需要 GeckoLib、也不需要动 Java）。

<h2>造型（照真弹的比例）</h2>
从下到上：**底缘（rim）→ 壳身（八棱柱）→ 壳肩（收口）→ 壳颈 → 弹头（阶梯锥）**。
弹壳用**八棱柱**（8 块绕 Y 轴旋转的薄板）—— 与项目里武器的八棱枪管/镜筒同一套审美；
弹头用 3 段递减的方块做出锥感（原版模型没有三角形，这也是 MC 物品模型的老办法）。

三种弹按真实口径比例区分（1 模型像素 ≈ 11 mm）：

| 弹种 | 真实 | 壳长 | 底径 | 颈径 | 头长 | 总长 |
| --- | --- | --- | --- | --- | --- | --- |
| `.338 Lapua` | 8.6×70 mm | 4.60 | 2.00 | 1.42 | 2.60 | 9.15 |
| `7.62×54R`（莫辛 / Kar98k） | 7.62×54 mm | 3.90 | 1.95 | 1.34 | 2.20 | 7.40 |
| `.30-06`（7.62×61，M1） | 7.62×63 mm | 4.30 | 1.80 | 1.28 | 2.35 | 8.00 |

⚠️ 7.62×54R 是**凸缘弹**（rim 比壳底粗一圈），所以它的底缘单独放大 0.55。

<h2>输出</h2>
`models/item/ammo_338.json`、`ammo_762_59.json`、`ammo_762_61.json`
`textures/item/ammo_338.png`（+ 另两种），贴图 64×64、逐面 UV。

用法::

    python tools/ammo_v3.py            # 生成 + 自检
    python tools/jsonmodel_view.py <json> <png> out.png    # 离线看三维效果
"""
import io
import json
import math
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity')
BUILD = os.path.join(ROOT, 'build')
TEX = 64

# ------------------------------------------------------------------ 三种弹的参数（模型像素）
#   rim=底缘 case=壳身 shoulder=壳肩 neck=壳颈 tip=弹头
SPECS = {
    'ammo_338': dict(
        label='.338 Lapua Magnum 8.6x70',
        rim_d=2.45, rim_h=0.45, case_d=2.00, case_h=4.60,
        shoulder_h=0.80, neck_d=1.42, neck_h=0.55, tip_h=2.60,
        brass=(198, 162, 86), brass_d=(150, 116, 54),
        copper=(186, 116, 68), copper_d=(140, 82, 44),
    ),
    'ammo_762_59': dict(
        label='7.62x54R (凸缘弹)',
        rim_d=2.60, rim_h=0.50, case_d=1.95, case_h=3.90,
        shoulder_h=0.85, neck_d=1.34, neck_h=0.55, tip_h=2.20,
        brass=(190, 154, 80), brass_d=(144, 110, 50),
        copper=(176, 110, 62), copper_d=(132, 78, 40),
    ),
    'ammo_762_61': dict(
        label='7.62x63 (.30-06)',
        rim_d=2.05, rim_h=0.40, case_d=1.80, case_h=4.30,
        shoulder_h=0.75, neck_d=1.28, neck_h=0.55, tip_h=2.35,
        brass=(202, 168, 96), brass_d=(154, 122, 60),
        copper=(192, 122, 72), copper_d=(146, 86, 44),
    ),
}

BOTTOM = 0.0                    # 弹底坐在 y = 0（物品栏里贴格子底部）


# ------------------------------------------------------------------ 面 / UV
FACES = ('north', 'east', 'south', 'west', 'up', 'down')


class Packer:
    """把每张面按 [宽,高] 排进 64×64 的贴图（简单的货架式装箱）。"""

    def __init__(self, size=TEX):
        self.size = size
        self.x = 0
        self.y = 0
        self.row_h = 0
        self.used = []

    def take(self, w, h):
        w, h = max(1, int(math.ceil(w))), max(1, int(math.ceil(h)))
        if self.x + w > self.size:
            self.x = 0
            self.y += self.row_h + 1
            self.row_h = 0
        if self.y + h > self.size:
            raise RuntimeError('贴图放不下：加尺寸或减少细节')
        rect = (self.x, self.y, self.x + w, self.y + h)
        self.x += w + 1
        self.row_h = max(self.row_h, h)
        self.used.append(rect)
        return rect


def faces_for(box, packer, w, h, d):
    """给一个方块生成 6 面 UV（尺寸 w/h/d 单位像素，取整后装箱）"""
    wi, hi, di = max(1, round(w)), max(1, round(h)), max(1, round(d))
    layout = {
        'north': (wi, hi), 'south': (wi, hi),
        'east': (di, hi), 'west': (di, hi),
        'up': (wi, di), 'down': (wi, di),
    }
    out = {}
    for f in FACES:
        fw, fh = layout[f]
        x0, y0, x1, y1 = packer.take(fw, fh)
        out[f] = {'uv': [x0, y0, x1, y1], 'texture': '#0'}
    return out


def add_box(elems, packer, name, x0, y0, z0, x1, y1, z1, rot=None):
    w, h, d = x1 - x0, y1 - y0, z1 - z0
    e = {
        'name': name,
        'from': [round(x0, 4), round(y0, 4), round(z0, 4)],
        'to': [round(x1, 4), round(y1, 4), round(z1, 4)],
    }
    e['faces'] = faces_for(e, packer, w, h, d)
    if rot is not None:
        origin, angle = rot
        e['rotation'] = {'origin': [round(v, 4) for v in origin], 'axis': 'y',
                         'angle': round(angle, 4), 'rescale': False}
    elems.append(e)
    return e


def oct_prism(elems, packer, name, y0, y1, dia):
    """八棱柱（正八边形，绕 Y 轴）：8 块薄板分别摆在八条边上。

    ★★ r119b 重大修正（踩坑记录）：MC 的 BlockElement rotation **只接受
    -45 / -22.5 / 0 / 22.5 / 45 五个角度值**（BlockElement$Deserializer
    直接抛 JsonParseException: Invalid rotation 90.0 found），而早期版本用
    `angle = i * 45` 生成 0/45/90/135/… ⇒ **整个模型 JSON 解析失败**。
    游戏日志里的表现非常误导人：
        Failed to load model hexalunar_calamity:models/item/ammo_338.json
        Unable to load model … FileNotFoundException: …ammo_338.json
    看着像「文件没打进 jar」（其实在），真因在两条日志之间的堆栈里。

    所以不能靠旋转 90/135/… 把板"转"到圆周上，改法：
      · 法线朝 ±Z 的边 → 板"薄在 Z"，不旋转
      · 法线朝 ±X 的边 → 板"薄在 X"，不旋转（靠 from/to 换轴向，而不是转 90°）
      · 斜边 → 板薄在 Z，绕**板自身中心**转 ±45°（135° 与 -45° 形状等价）
    """
    r = dia / 2.0
    r_in = r * math.cos(math.radians(22.5))                 # 边心距（内切圆半径）
    side = 2.0 * r * math.sin(math.radians(22.5)) + 0.10    # 板宽（略重叠，防缝）
    thick = max(0.16, dia * 0.11)
    yc = (y0 + y1) / 2.0
    # (外法线角°, 薄在哪轴, rotation 角度)
    plan = [
        (0, 'z', 0.0), (45, 'z', 45.0), (90, 'x', 0.0), (135, 'z', -45.0),
        (180, 'z', 0.0), (225, 'z', 45.0), (270, 'x', 0.0), (315, 'z', -45.0),
    ]
    for k, (theta, thin, ang) in enumerate(plan):
        rad = math.radians(theta)
        cx = math.sin(rad) * r_in
        cz = math.cos(rad) * r_in
        if thin == 'z':
            x0, x1 = cx - side / 2.0, cx + side / 2.0
            z0, z1 = cz - thick / 2.0, cz + thick / 2.0
            fw, fd = side, thick
        else:
            x0, x1 = cx - thick / 2.0, cx + thick / 2.0
            z0, z1 = cz - side / 2.0, cz + side / 2.0
            fw, fd = thick, side
        e = {
            'name': '%s_%d' % (name, k),
            'from': [round(x0, 4), round(y0, 4), round(z0, 4)],
            'to': [round(x1, 4), round(y1, 4), round(z1, 4)],
            'faces': faces_for(None, packer, fw, y1 - y0, fd),
        }
        if ang != 0.0:
            # ★ origin 取**板自身中心**：旋转只改朝向、不移动板（位置已由 from/to 摆好）
            e['rotation'] = {'origin': [round(cx, 4), round(yc, 4), round(cz, 4)],
                             'axis': 'y', 'angle': ang, 'rescale': False}
        elems.append(e)


def box_centered(elems, packer, name, y0, y1, dia):
    """居中的方柱（用于底缘 / 壳颈 / 弹头这类小尺寸件）"""
    h = dia / 2.0
    return add_box(elems, packer, name, -h, y0, -h, h, y1, h)


# ------------------------------------------------------------------ 生成一颗子弹
def build(spec):
    elems = []
    packer = Packer()

    # ★★ 原点必须落在**几何中心**：物品模型的 (0,0,0) 在物品栏里就是格子中心，
    #   如果从 y=0 往上长，整颗子弹会吊在格子的上半部。
    total = spec['rim_h'] + spec['case_h'] + spec['shoulder_h'] + spec['tip_h']
    y = -total / 2.0
    # 1) 底缘（rim）—— 比壳身粗一圈，**也做成八棱盘**（方块底缘从上往下看是"方的"，很出戏）
    oct_prism(elems, packer, 'rim', y, y + spec['rim_h'], spec['rim_d'])
    #    八棱柱是空心的 ⇒ 底下补一块封盘（也是底火所在的那一面）
    box_centered(elems, packer, 'rim_floor', y, y + 0.07, spec['rim_d'] * 0.94)
    y += spec['rim_h']
    # 2) 壳身（八棱柱，主体 —— 全枪最"圆"的那一段）
    oct_prism(elems, packer, 'case', y, y + spec['case_h'], spec['case_d'])
    y += spec['case_h']
    # 3) 壳肩（**一段**收口）
    #   ★ 别再拆成两段：拆成 sh0/sh1/neck/tip0/tip1/tip2 六段小方块时，等轴视角下
    #     每段的顶面都变成一片"斜片"，整体看着很碎（离线预览里最明显）。三段就够。
    #   尺寸必须**小于八棱柱的内切圆**（case_d × 0.924），否则会从筒壁里凸出来。
    box_centered(elems, packer, 'shoulder', y, y + spec['shoulder_h'],
                 min(spec['neck_d'] + 0.30, spec['case_d'] * 0.90))
    y += spec['shoulder_h']
    # 4) 弹头（三段递减：主体 → 收窄 → 尖）
    th = spec['tip_h']
    box_centered(elems, packer, 'tip0', y, y + th * 0.60, spec['neck_d'])
    box_centered(elems, packer, 'tip1', y + th * 0.60, y + th * 0.85, spec['neck_d'] * 0.62)
    box_centered(elems, packer, 'tip2', y + th * 0.85, y + th, spec['neck_d'] * 0.30)
    y += th
    return elems, packer, y


def paint(spec, packer, elems):
    """按元素名画贴图：底缘/壳身/壳肩/壳颈 = 黄铜（柱面明暗），弹头 = 铜被甲。"""
    img = Image.new('RGBA', (TEX, TEX), (0, 0, 0, 0))
    px = img.load()
    brass, brass_d = spec['brass'], spec['brass_d']
    copper, copper_d = spec['copper'], spec['copper_d']

    def mix(c1, c2, t):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    for e in elems:
        kind = 'copper' if e['name'].startswith('tip') else 'brass'
        base, dark = (copper, copper_d) if kind == 'copper' else (brass, brass_d)
        for f, fd in e['faces'].items():
            x0, y0, x1, y1 = fd['uv']
            w, h = x1 - x0, y1 - y0
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    if f in ('up', 'down'):
                        # 端面：径向明暗（中间亮、边缘暗）
                        t = 0.25
                    else:
                        # 侧面：横向柱面明暗（左暗 → 中亮 → 右暗）
                        u = (xx - x0 + 0.5) / w
                        t = math.sin(u * math.pi) ** 0.6
                    c = mix(dark, base, t)
                    px[xx, yy] = (c[0], c[1], c[2], 255)
    # 底火（rim_floor 的下表面中心一个深色圆点 —— 底缘改成八棱盘后，弹底就是这块封盘）
    for e in elems:
        if e['name'] == 'rim_floor':
            fd = e['faces']['down']
            x0, y0, x1, y1 = fd['uv']
            cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            r = min(x1 - x0, y1 - y0) * 0.26
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    if (xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= r * r:
                        px[xx, yy] = (96, 98, 104, 255)
            break
    return img


# ------------------------------------------------------------------ 输出
# ★★ 原版只允许这 5 个角度（BlockElement$Deserializer，违反就是整个模型加载失败）
LEGAL_ANGLES = (-45.0, -22.5, 0.0, 22.5, 45.0)


def check_rotations(model):
    """自检：elements 里的 rotation.angle 必须是原版允许的 5 个值之一。

    ★ 这个坑（r118）在游戏里表现成「模型打不进 jar」，实际是 JSON 解析失败 ——
      一定要在生成器里拦下来，别让它在游戏日志里变成误导人的 FileNotFoundException。
    """
    for e in model.get('elements', []):
        rot = e.get('rotation')
        if rot is None:
            continue
        ang = float(rot['angle'])
        if ang not in LEGAL_ANGLES:
            raise RuntimeError('%s：rotation 角度 %s 非法，只允许 %s'
                               % (e.get('name'), ang, LEGAL_ANGLES))
        if rot.get('axis') != 'y':
            raise RuntimeError('%s：本生成器只实现了绕 Y 轴旋转' % e.get('name'))


def write_model(name, elems):
    model = {
        # ★★ r119b：**绝不能用 item/generated** —— 它的根模型是 builtin/generated，
        #   ModelBakery 会因此调 ItemModelGenerator 重新生成 elements；而那个生成器
        #   只认 #layer0..#layer4 纹理，我们的面引用的是 #0 ⇒ 它把所有面都跳过，
        #   产出一个 elements 为空的模型 ⇒ 游戏里就是一团品红/黑。
        #   改成自定义的 ammo_3d_base（parent = block/block + 自己写 display）。
        'parent': 'hexalunar_calamity:item/ammo_3d_base',
        'textures': {
            '0': 'hexalunar_calamity:item/%s' % name,
            'particle': 'hexalunar_calamity:item/%s' % name,
        },
        'elements': elems,
    }
    check_rotations(model)                       # ★ 自检：rotation 角度是否合法
    dst = os.path.join(RES, 'models', 'item', name + '.json')
    with io.open(dst, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(model, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    return dst


def main():
    os.makedirs(os.path.join(RES, 'models', 'item'), exist_ok=True)
    os.makedirs(os.path.join(RES, 'textures', 'item'), exist_ok=True)
    for name, spec in SPECS.items():
        elems, packer, top = build(spec)
        img = paint(spec, packer, elems)
        tex = os.path.join(RES, 'textures', 'item', name + '.png')
        img.save(tex)
        dst = write_model(name, elems)
        print('%-14s %-26s 元素 %2d  总高 %.2f 单位（%.1f%% 格子）  -> %s'
              % (name, spec['label'], len(elems), top, top / 16.0 * 100.0,
                 os.path.relpath(dst, ROOT)))
        # 自检
        bad = []
        for e in elems:
            for f, fd in e['faces'].items():
                x0, y0, x1, y1 = fd['uv']
                if not (0 <= x0 < x1 <= TEX and 0 <= y0 < y1 <= TEX):
                    bad.append('%s.%s UV 越界 %s' % (e['name'], f, fd['uv']))
        used = packer.y + packer.row_h
        print('   贴图：%d×%d，占用高度 %d px  %s' % (TEX, TEX, used,
                                                   'UV OK' if not bad else '!! ' + '; '.join(bad[:3])))
    print('\n→ 用 `python tools/jsonmodel_view.py <json> <png> out.png` 看三维效果')


if __name__ == '__main__':
    main()
