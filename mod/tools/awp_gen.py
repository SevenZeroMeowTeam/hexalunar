# -*- coding: utf-8 -*-
"""把 `模型/AWP_Printstream_Minecraft` 的基岩版几何转成 GeckoLib 用的 geo + 贴图。

参考包（`使用说明.md`）的约定与本项目相反：它是 **X = 枪口朝前、Z = 横向**，
本项目一律 **枪口 = -Z（北）、上 = +Y、横向 = X**。所以这里做四件事：

1. **把旋转烘进几何**（`R_y(+90°)`: (x,y,z) → (z, y, -x)），**不加**一根转 90° 的根骨骼 ——
   父骨骼一旦带旋转，子骨骼的位移就落在父级的局部系里：`move` 骨骼沿 Z 推会变成往侧面推。
   逐面 UV 跟着换名：new east ← old south、new west ← old north、
   new north ← old east、new south ← old west（up/down 原地不动）。
   ★ 代价：up/down 面在新系里的边长是旧的 (d, w) 转置 —— 面片本身是斜纹/纯色，
   90° 内旋转看起来只是条纹角度变化，肉眼几乎看不出（要完全消除得重新装箱整张图集）。
2. **整体缩放 K = 0.75**：参考模型 28 像素（=1.75 格）太长，收到 21 像素（≈1.31 格，
   真枪 1.18m）。烘进几何而不是用 display scale —— 这样 Java 侧只有一套数（S=1），
   子弹、枪口焰、手臂全用同一份模型像素坐标。
3. **贴图重画到 512²**（微调 2 改）：不再简单 ×4 放大，而是把所有面**重新装箱**到 512²
   （密度 ~= 22 像素/单位，比原来 4 像素/单位细 5 倍）——每个面拿到一块专属矩形，
   内容从参考图对应块 LANCZOS 重采样后逐面增强（白底黑纹拉对比变硬朗 / 不锈钢拉丝 /
   磷化黑颗粒），再叠逐面倒角与 AO。UV 写进输出 geo，与几何尺寸无关（避免拉伸）。
4. 补 `root` / `move` 两根骨骼（`move` = Java 侧推「举枪位移 + 后坐」的骨骼，
   与 AKM 同一套约定）。

微调（r79，在原参考包基础上按需求补）：
5. **8 倍镜可调节**拆成三根独立骨骼：`scope_adjust`（变倍环，绕镜筒轴自转）、
   `scope_elev`（顶部高低钮）、`scope_wind`（右侧风偏钮）—— 各自绕自己的轴转即「拧调节环/钮」。
6. 新增 **`casing`（弹壳）骨骼**：弹壳静止时收在机匣内（被「抛壳口盖板」遮住看不见），
   拉栓时由枪机带出 → 边翻边抛向枪身右侧 —— 见 `awp_v1.animation.json` 里的
   `animation.awp.bolt` / `animation.awp.reload`。
7. 补写实细节件：抛壳口盖板、导轨齿 ×4、机匣螺钉 ×4、弹匣加强筋 ×2；
微调 2（r80，按用户反馈「太臃肿 / 枪身在长一点 / 扳机和弹匣应该有距离」）：
8. **瘦身**：机匣 3→2.4 高、2→1.6 宽；枪托/护木等 Z 向收 0.8~0.9（`BONE_SLIM_Z`）。
9. **机匣加长**：8 → 9.5 单位（往前伸到 x=5.5），顶部导轨同步加长、随顶面下移 0.6。
10. **下半部重排**（真实 AWP 顺序：枪托 → 握把 → 扳机护圈 → ←留空→ 弹匣 → 枪管）：
    握把后移到 x -1.9~-0.7、扳机/护圈跟着后移、弹匣（连同底板）前移到 x 1.5~3.9，
    弹匣后缘与护圈前缘之间留 1.15 单位（≈5.4 cm）的空档。
11. **扳机独立成骨**（`trigger`，父 = `body`，pivot = 顶部销轴）—— 可以单独扣动，
    动画 `animation.awp.fire`（绕销轴后转 11°）；护圈仍留在家骨上。   新面的材质（不锈钢 / 磷化黑 / 黄铜）画在**图集空闲区**，脚本会自检不与旧面撞格。

用法: python tools\awp_gen.py    → build/awp_v1.geo.json + awp_v1.png + awp_v1.animation.json
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '模型', 'AWP_Printstream_Minecraft')
SRC_GEO = os.path.join(SRC, 'bedrock', 'geometry.awp_printstream.json')
SRC_TEX = os.path.join(SRC, 'awp_printstream.png')
OUT_GEO = os.path.join(ROOT, 'build', 'awp_v1.geo.json')
OUT_TEX = os.path.join(ROOT, 'build', 'awp_v1.png')
OUT_ANIM = os.path.join(ROOT, 'build', 'awp_v1.animation.json')   # 微调新增：拉栓抛壳 / 换弹 / 镜调节
OUT_GLOW = os.path.join(ROOT, 'build', 'awp_v1_glowmask.png')     # 流光遮罩（自产）

IDENT = 'geometry.awp'
TEX_SCALE = 4                 # 贴图放大倍数（UV 同步 ×4）
K = 0.75                      # 几何缩放（把 28 像素的枪收到 21 像素）

# 源骨骼名 → 目标骨骼名；顺序 = 父级先出
BONE_MAP = [
    ('bone_body', 'body', 'move'),
    ('bone_barrel', 'barrel', 'body'),
    ('bone_bipod', 'bipod', 'barrel'),
    ('bone_scope', 'scope', 'body'),
    ('bone_scope_adjust', 'scope_adjust', 'scope'),
    ('bone_magazine', 'magazine', 'body'),
    ('bone_bolt', 'bolt', 'body'),
]

# 旋转是绕 Y 轴 ±90°，只换名字不换尺寸（up/down 的转置见文件头说明）
FACE_REMAP = {'up': 'up', 'down': 'down',
              'south': 'east', 'north': 'west', 'east': 'north', 'west': 'south'}

# ================================================================== 微调（r79）
# 1) 「8 倍镜可调节」拆三根骨骼：scope_adjust = 变倍环 / scope_elev = 高低钮 / scope_wind = 风偏钮
# 2) casing = 弹壳骨骼（拉栓抛壳）；3) 补写实细节件
EXTRA_BONES = [
    # (骨骼名, 父级, 源坐标 pivot)
    ('scope_elev', 'scope', (0.20, 4.80, 0.00)),   # 顶部高低调节钮（绕自身竖轴自转）
    ('scope_wind', 'scope', (0.20, 4.25, 0.54)),   # 右侧风偏调节钮（绕自身横轴自转）
    ('casing', 'body', (0.90, 1.80, 0.425)),       # 弹壳（pivot = 弹壳中心，便于翻滚）
    ('trigger', 'body', (-0.21, -0.20, 0.0)),      # 扳机（pivot = 顶部销轴，扣扳机绕它转）
]

# 源骨骼里的方块搬到新骨骼：键 = (源骨骼名, 源 origin 取 3 位小数)
CUBE_MOVE = {
    ('bone_scope', (-0.2, 5.4, -0.4)): 'scope_elev',
    ('bone_scope_adjust', (-0.2, 4.5, 0.6)): 'scope_wind',
    ('bone_body', (0.9, -1.2, -0.15)): 'trigger',   # 扳机不再跟机匣共骨
}

# ---- 微调 2：比例 / 布局 ----
# 骨骼整体按 Z（宽度）瘦身：z *= k（绕 z=0 收）
BONE_SLIM_Z = {'body': 0.80, 'bolt': 0.85, 'barrel': 0.90,
               'scope': 0.90, 'scope_adjust': 0.90, 'scope_elev': 0.90, 'scope_wind': 0.90}
# 骨骼整体平移（镜子隨导轨下移 0.6；枪机贴回收窄后的机匣侧面）
BONE_SHIFT = {'scope': (0, -0.6, 0), 'scope_adjust': (0, -0.6, 0),
              'scope_elev': (0, -0.6, 0), 'scope_wind': (0, -0.6, 0),
              'bolt': (0, 0, -0.2)}
# 逐方块改形：键 = (源骨骼, 原 origin) → (新 origin, 新 size)
# 布局顺序（X 向前）：枪托 → 握把 → 扳机护圈/扳机 → ←留空→ 弹匣 → 机匣前端 → 枪管
RESHAPE = {
    ('bone_body', (-4.0, 0.0, -1.0)): ((-4.0, 0.0, -0.8), (9.5, 2.4, 1.6)),        # 机匣：加长/压低/收窄
    ('bone_body', (-3.5, 3.0, -0.5)): ((-3.5, 2.4, -0.4), (8.0, 0.4, 0.8)),        # 顶部导轨
    ('bone_body', (1.6, -3.2, -0.7)): ((-1.9, -3.0, -0.6), (1.2, 3.0, 1.2)),       # 握把后移
    # 扳机/护圈已改由 REPLACE 重画（见下表），这里不再列
    ('bone_magazine', (-2.2, -3.0, -0.8)): ((1.90, -1.70, -0.58), (1.6, 1.9, 1.16)),   # 短弹匣（AWP 式，几乎贴底）
    ('bone_magazine', (-2.4, -3.4, -0.9)): ((1.72, -2.02, -0.70), (1.9, 0.32, 1.40)),  # 弹匣底板
    # 枪管加长（微调 4）：中段 10.5 → 13.7 单位，枪口组（前准座 + 制退器）整体前移 3.5
    ('bone_barrel', (5.5, 1.6, -0.5)): ((5.5, 1.6, -0.45), (13.7, 1.0, 0.90)),
    ('bone_barrel', (15.6, 1.2, -0.9)): ((19.1, 1.2, -0.81), (1.0, 1.8, 1.62)),
    ('bone_barrel', (16.6, 1.35, -0.75)): ((20.1, 1.35, -0.675), (1.6, 1.5, 1.35)),
}

# 逐方块旋转（源坐标系，只支持绕 Z 轴）：键 = (源骨骼, 原 origin)
#   值 = (旋转角度, 旋转中心)。源系绕 Z 转 = 项目系绕 X 转（角度同号）。
#   握把必须**绕顶端向后倾**（真实步枪的握把都不是垂直的）；source rot_z 为**负**
#   ⇒ 下端向 -X（后方）倒（与 AKM 的 rot=(-14,0,0) 同一约定）。
CUBE_ROT = {
    ('bone_body', (1.6, -3.2, -0.7)): (-17.0, (-1.30, 0.0, 0.0)),     # 握把后倾 17°
}

# 逐方块**替换**（微调 5「倍镜圆一点」、微调 6「重画扳机」）：
#   键 = (源骨骼, 原 origin) → [(origin, size[, rot_z, pivot]), ...]
#   · 两个交错小盒（十字双盒）叠出近似八边形截面；新盒沿用原方块**逐面 UV**（图案/贴图不丢）
#   · 作者值是**未瘦身/未平移**的源坐标，生成时与其它方块走同一套 slim/shift
#   · 截面 (a, b) → A:(a, 0.78b) + B:(0.78a, b)，两盒同心（_OCT）
_OCT = 0.78
REPLACE = {
    # 镜筒（绕 X 轴的圆管）
    ('bone_scope', (-2.0, 4.2, -0.6)): [((-2.0, 4.33, -0.60), (4.5, 1.2 * _OCT, 1.2)),
                                        ((-2.0, 4.20, -0.47), (4.5, 1.2, 1.2 * _OCT))],
    # 物镜筒（前喇叭）
    ('bone_scope', (2.5, 4.0, -0.9)): [((2.5, 4.175, -0.90), (1.4, 1.6 * _OCT, 1.8)),
                                       ((2.5, 4.000, -0.70), (1.4, 1.6, 1.8 * _OCT))],
    # 物镜圈（薄环）
    ('bone_scope', (3.9, 4.15, -0.75)): [((3.9, 4.290, -0.75), (0.15, 1.3 * _OCT, 1.5)),
                                         ((3.9, 4.150, -0.59), (0.15, 1.3, 1.5 * _OCT))],
    # 目镜筒
    ('bone_scope', (-3.0, 4.05, -0.75)): [((-3.0, 4.215, -0.75), (1.0, 1.5 * _OCT, 1.5)),
                                          ((-3.0, 4.050, -0.59), (1.0, 1.5, 1.5 * _OCT))],
    # 目镜圈（薄环）
    ('bone_scope', (-3.15, 4.2, -0.6)): [((-3.15, 4.330, -0.60), (0.15, 1.2 * _OCT, 1.2)),
                                         ((-3.15, 4.200, -0.47), (0.15, 1.2, 1.2 * _OCT))],
    # 两个镜环（环抱镜筒的夹箍）
    ('bone_scope', (1.5, 3.4, -0.4)): [((1.5, 3.500, -0.40), (1.0, 0.9 * _OCT, 0.8)),
                                       ((1.5, 3.400, -0.31), (1.0, 0.9, 0.8 * _OCT))],
    ('bone_scope', (-1.5, 3.4, -0.4)): [((-1.5, 3.500, -0.40), (1.0, 0.9 * _OCT, 0.8)),
                                        ((-1.5, 3.400, -0.31), (1.0, 0.9, 0.8 * _OCT))],
    # 变倍环（绕镜筒轴自转的那个）
    ('bone_scope_adjust', (1.0, 4.05, -0.75)): [((1.0, 4.215, -0.75), (0.6, 1.5 * _OCT, 1.5)),
                                                ((1.0, 4.050, -0.59), (0.6, 1.5, 1.5 * _OCT))],
    # 顶部高低钮（轴 = Y，截面在 XZ 面）
    ('bone_scope', (-0.2, 5.4, -0.4)): [((-0.20, 5.4, -0.31), (0.8, 0.7, 0.8 * _OCT)),
                                        ((-0.11, 5.4, -0.40), (0.8 * _OCT, 0.7, 0.8))],
    # 右侧风偏钮（轴 = Z，截面在 XY 面）
    ('bone_scope_adjust', (-0.2, 4.5, 0.6)): [((-0.20, 4.575, 0.6), (0.8, 0.7 * _OCT, 0.45)),
                                              ((-0.11, 4.500, 0.6), (0.8 * _OCT, 0.7, 0.45))],
    # ---- 扳机重画（微调 6）：不再是单根方棍，而是「上座 + 扳机片 + 指托」三件，略向后倾 ----
    # 旋转中心 = 各自顶端（−10° ⇒ 下端往后）
    ('bone_body', (0.9, -1.2, -0.15)): [
        ((-0.32, -0.50, -0.11), (0.22, 0.30, 0.22)),                       # 上座（从销轴伸出）
        ((-0.36, -1.02, -0.09), (0.18, 0.56, 0.18), -10.0, (-0.27, -0.48, 0.0)),   # 扳机片
        ((-0.42, -1.20, -0.11), (0.24, 0.22, 0.22), -10.0, (-0.27, -1.00, 0.0)),   # 指托
    ],
    # ---- 护圈改成真正的**环形框**（原来是个实心块，把扳机埋在里头）----
    # 开口 x −1.0~0.35 / y −1.25~−0.25（1.35×1.0 单位 ≈ 6.3×4.7 cm）；z 值写成未瘦身值（body 还要 ×0.8）
    ('bone_body', (0.2, -1.4, -0.4)): [
        ((-1.00, -0.25, -0.44), (1.60, 0.25, 0.88)),                        # 上横梁（贴机匣底）
        ((0.35, -1.50, -0.44), (0.25, 1.25, 0.88)),                         # 前立柱
        ((-1.00, -1.50, -0.44), (1.35, 0.25, 0.88)),                        # 下横梁
    ],
}

# 逐方块**材质覆盖**：键 = (源骨骼, 原 origin) → 材质名（改用程序生成的材质，不用参考图那块）
#   参考图里枪口制退器那块是浅灰条纹，而真枪/参考照里制退器是黑的 ⇒ 覆盖成 DARK
CUBE_MAT = {
    ('bone_barrel', (16.6, 1.35, -0.75)): 'DARK',      # 枪口制退器
}

# 新增方块（源坐标系：X 枪口向前 / Y 上 / Z 横向），材质名决定贴图内容
DETAILS = [
    # ★ 贴在别的面上的小件都往内缩 0.02（与基面错开，避免共面 z-fighting）
    ('body', (-1.60, 1.35, 0.78), (3.20, 1.00, 0.10), 'DARK'),       # 抛壳口盖板（弹壳出口）
    ('body', (-3.40, 2.78, -0.36), (0.50, 0.20, 0.72), 'STEEL'),     # 导轨齿 ×4
    ('body', (-2.40, 2.78, -0.36), (0.50, 0.20, 0.72), 'STEEL'),
    ('body', (0.00, 2.78, -0.36), (0.50, 0.20, 0.72), 'STEEL'),
    ('body', (1.00, 2.78, -0.36), (0.50, 0.20, 0.72), 'STEEL'),
    ('body', (-3.20, 0.70, 0.78), (0.36, 0.36, 0.16), 'DARK'),       # 机匣螺钉 ×4
    ('body', (2.60, 0.70, 0.78), (0.36, 0.36, 0.16), 'DARK'),
    ('body', (-3.20, 0.70, -0.94), (0.36, 0.36, 0.16), 'DARK'),
    ('body', (2.60, 0.70, -0.94), (0.36, 0.36, 0.16), 'DARK'),
    ('magazine', (1.95, -1.25, 0.55), (1.42, 0.22, 0.15), 'DARK'),   # 弹匣加强筋 ×2
    ('magazine', (1.95, -1.25, -0.70), (1.42, 0.22, 0.15), 'DARK'),
    ('casing', (-0.40, 1.45, 0.10), (2.60, 0.70, 0.65), 'BRASS'),    # 弹壳体（静止时在机匣内）
    ('casing', (-0.58, 1.39, 0.06), (0.18, 0.82, 0.72), 'BRASS'),    # 弹壳底缘
]


def box_uv(u0, v0, w, h, d):
    """基岩版 box UV → 逐面矩形 (u, v, w, h)，单位：源贴图像素（V 向下、左上为原点）。

    与 Blockbench / 基岩版一致（`east` 在盒子左脚、`west` 在中间）——
    注意参考包自己的生成脚本把 east/west 写反了，但**每个方块的整块 UV 都落在同一个色区里**，
    左右互换只会让斜纹镜像，肉眼看不出来，这里按标准公式写。
    """
    return {
        'up': (u0 + d, v0, w, d),
        'down': (u0 + d + w, v0, w, d),
        'east': (u0, v0 + d, d, h),
        'north': (u0 + d, v0 + d, w, h),
        'west': (u0 + d + w, v0 + d, d, h),
        'south': (u0 + d + w + d, v0 + d, w, h),
    }


def rot(p):
    """参考系 → 本项目系：绕 Y 转 +90°（+X 枪口 → -Z 前方），再整体缩放 K。"""
    return [p[2] * K, p[1] * K, -p[0] * K]


def key(p):
    """方块 origin 的比对键（源坐标，取 3 位小数，躲开 0.19999999999999996 这类浮点）。"""
    return (round(p[0], 3), round(p[1], 3), round(p[2], 3))


def face_layout(size):
    """每个面在贴图上的**几何尺寸**（宽, 高）——与 box_uv 的排布一一对应。

    ★ 面尺寸 = 该面的真实边长（单位 = 源像素 = 1/16 格），所以“按几何尺寸装箱”
      等于全程保持等向纹素密度，不会把图案拉变形。
    """
    sx, sy, sz = size
    return {'up': (sx, sz), 'down': (sx, sz), 'east': (sz, sy),
            'north': (sx, sy), 'west': (sz, sy), 'south': (sx, sy)}


def pack(faces, size=512, gutter=2):
    """货架装箱：密度从高往低试，就地写回 'px/py/pw/ph/den'。返回最终密度。"""
    for den in range(26, 5, -1):
        x = y = shelf = 0
        ok = True
        for f in sorted(faces, key=lambda f: -f['h']):
            pw = max(2, int(round(f['w'] * den)))
            ph = max(2, int(round(f['h'] * den)))
            if x + pw + gutter > size:
                x, y, shelf = 0, y + shelf + gutter, 0
            if y + ph + gutter > size:
                ok = False
                break
            f.update(px=x, py=y, pw=pw, ph=ph, den=den)
            x += pw + gutter
            shelf = max(shelf, ph)
        if ok:
            return den
    raise SystemExit('贴图装箱失败：面太大，装不进 %d²' % size)


def classify(tile):
    """参考图切片 → 材质类别（用来决定怎么增强）。"""
    g = np.asarray(tile.convert('L'), dtype=np.float32)
    m, sd = float(g.mean()), float(g.std())
    if m > 138 and sd > 26:
        return 'pattern'          # 白底黑纹（Printstream 网格）
    if m > 138:
        return 'steel'            # 不锈钢 / 银灰
    if m > 70:
        return 'gray'
    return 'dark'                 # 磷化黑


def draw_material(mat, w, h):
    """新方块的面：在 512 分辨率下重新画（不是放大小色块）。"""
    a = np.zeros((h, w, 4), dtype=np.float32)
    gy = np.linspace(0.0, 1.0, h)[:, None]
    gx = np.linspace(0.0, 1.0, w)[None, :]
    wide = w >= h                                    # 长边方向 = u（长方面横着放）
    t = np.broadcast_to(gy if wide else gx, (h, w))  # 沿短边 → 圆柱/拉丝方向
    if mat == 'BRASS':                               # 黄铜：圆柱明暗 + 高光带
        base = np.array([206.0, 158.0, 80.0], dtype=np.float32)
        f = 1.16 - 0.40 * t + 0.10 * np.exp(-((t - 0.22) ** 2) / 0.02)
        a[:, :, :3] = base[None, None, :] * f[:, :, None]
    elif mat == 'STEEL':                             # 不锈钢：细拉丝
        n = w if wide else h
        brush = 1.0 + 0.035 * np.cos(np.arange(n) * 0.9)
        b = np.broadcast_to(brush[None, :] if wide else brush[:, None], (h, w))
        a[:, :, :3] = np.array([199.0, 202.0, 208.0], dtype=np.float32)[None, None, :] * b[:, :, None]
        a[:, :, :3] *= (1.06 - 0.16 * t)[:, :, None]
    else:                                            # DARK 磷化黑：极细颗粒
        rng = np.random.RandomState(11)
        a[:, :, :3] = 46.0 + rng.randint(-1, 2, (h, w, 1))
        a[:, :, :3] *= (0.92 + 0.12 * (1.0 - t))[:, :, None]
    a[:, :, 3] = 255
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def enhance(tile, kind):
    """逐面增强：参考图内容重采样后按材质类别加细节（512 才有的信息量）。

    ★ 参考图的图案是**横跨整个面的大斜带**（2 单位宽的 45° 黑带，间距 ~11.5 单位），
      放大后边缘会发虚 → pattern 类用陡峭的 S 曲线把过渡带压到 2~3 像素（硬边但抗锯）。
    """
    a = np.asarray(tile, dtype=np.float32).copy()
    h, w = a.shape[:2]
    k = {'pattern': 7.0, 'steel': 3.0, 'gray': 3.0}.get(kind, 2.0)
    m = a[:, :, :3].mean(axis=2, keepdims=True)
    a[:, :, :3] = np.clip(a[:, :, :3] + (np.clip((m - 126.0) * k + 126.0, 0, 255) - m), 0, 255)
    if kind == 'steel':
        col = 1.0 + 0.03 * np.cos((np.arange(w) * 1.7).reshape(1, w, 1)) if w >= h \
            else 1.0 + 0.03 * np.cos((np.arange(h) * 1.7).reshape(h, 1, 1))
        a[:, :, :3] = np.clip(a[:, :, :3] * col, 0, 255)
    elif kind == 'dark':
        rng = np.random.RandomState(5)
        a[:, :, :3] = np.clip(a[:, :, :3] + rng.randint(-1, 2, (h, w, 1)), 0, 255)
    return Image.fromarray(a.astype(np.uint8))


def make_tile(src, f, psize):
    """一个面的贴图：新方块按材质重画，参考方块从原图对应块重采样 + 增强。"""
    w, h = max(2, int(psize[0])), max(2, int(psize[1]))
    if f['mat']:
        return draw_material(f['mat'], w, h)
    x0, y0 = int(math.floor(f['sx'])), int(math.floor(f['sy']))
    x1 = max(int(math.ceil(f['sx'] + f['sw'])), x0 + 1)
    y1 = max(int(math.ceil(f['sy'] + f['sh'])), y0 + 1)
    tile = src.crop((x0, y0, x1, y1))
    kind = classify(tile)
    return enhance(tile.resize((w, h), Image.LANCZOS), kind)


def shade_faces(canvas, faces):
    """逐面倒角/AO（左/上提亮、右/下压暗）—— 512 分辨率下才有意义的细节。

    顺便产出**流光遮罩**：参考图有大面积纯白，`gen_glowmask.py` 的亮度分位法在这里会失效
    （阈值直接顶到 255），所以自己画遮罩 —— 倒角高光带 + 金属面的反光带。
    返回 alpha = 遮罩强度的 mask（0..1）。
    """
    a = np.asarray(canvas, dtype=np.float32)
    mask = np.zeros(a.shape[:2], dtype=np.float32)
    for f in faces:
        x, y, w, h = f['px'], f['py'], f['pw'], f['ph']
        if w < 6 or h < 6:
            continue
        b = max(1, int(round(min(w, h) * 0.09)))
        a[y:y + b, x:x + w, :3] *= 1.10
        a[y:y + h, x:x + b, :3] *= 1.07
        a[y + h - b:y + h, x:x + w, :3] *= 0.87
        a[y:y + h, x + w - b:x + w, :3] *= 0.90
        mask[y:y + b, x:x + w] = np.maximum(mask[y:y + b, x:x + w], 0.80)
        mask[y:y + h, x:x + b] = np.maximum(mask[y:y + h, x:x + b], 0.65)
        if f['mat'] in ('STEEL', 'BRASS'):                 # 金属：只留一条中线反光
            mask[y:y + h, x + w // 2:x + w // 2 + 1] = 1.0
    np.clip(a, 0, 255, out=a)
    canvas.paste(Image.fromarray(a.astype(np.uint8)))
    p = np.pad(mask, 1, mode='edge')                       # 膨胀 1 像素，细高光才看得见
    hh, ww = mask.shape
    for dy in range(3):
        for dx in range(3):
            mask = np.maximum(mask, p[dy:dy + hh, dx:dx + ww])
    return mask


def paint_faces(src_path, faces, size=512):
    src = Image.open(src_path).convert('RGBA')
    canvas = Image.new('RGBA', (size, size), (32, 32, 36, 255))
    for f in faces:
        canvas.paste(make_tile(src, f, (f['pw'], f['ph'])), (f['px'], f['py']))
    return canvas, shade_faces(canvas, faces)


def model_cube(origin, size, uv, rot=None, pivot=None):
    """源坐标系方块 → 输出坐标系方块（绕 Y +90° 再缩放 K，与整体变换一致）。

    rot = 源系旋转（仅支持绕 Z 轴，转成项目系的绕 X），pivot = 旋转中心（源坐标）。
    """
    x0, y0, z0 = origin
    sx, sy, sz = size
    o = [z0 * K, y0 * K, -(x0 + sx) * K]
    s = [sz * K, sy * K, sx * K]
    cube = {'origin': [round(v, 4) for v in o],
            'size': [round(v, 4) for v in s],
            'inflate': 0,
            'uv': uv}
    if rot is not None:
        rz = rot if isinstance(rot, (int, float)) else rot[2]
        cube['rotation'] = [round(float(rz), 4), 0.0, 0.0]   # 源 +Z → 项目 +X
        cube['pivot'] = [round(v, 4) for v in rot_point(pivot or origin)]
    return cube


def rot_point(p):
    """源系的一个点 → 项目系（不取逆、不加尺寸）。"""
    return [p[2] * K, p[1] * K, -p[0] * K]


def xform(origin, size, target):
    """按目标骨骼做「宽度瘦身 + 整体平移」（REPLACE 的路：作者值 = 未瘦身/未平移的源值）。"""
    kz = BONE_SLIM_Z.get(target, 1.0)
    if kz != 1.0:
        origin = (origin[0], origin[1], origin[2] * kz)
        size = (size[0], size[1], size[2] * kz)
    sh = BONE_SHIFT.get(target)
    if sh:
        origin = tuple(origin[i] + sh[i] for i in range(3))
    return origin, size


def mat_pixel(mat, i, j):
    """（已被 draw_material 取代，保留只为兼容旧调用）"""
    raise NotImplementedError('mat_pixel 已废弃，改用 draw_material')


def anim_json():
    """GeckoLib / 基岩版动画（写进 build/awp_v1.animation.json）。

    ★ 坐标已换到本项目系：**+Z = 向射手（后退）**、**+X = 枪的右侧（抛壳方向）**、Y = 上；
      位移单位 = 模型像素（= 已经乘过 K 的最终几何单位）。
    ★ 拉栓抛壳分三段：枪机带出 → 边翻边抛向右上方 → 旋转消失（“翻转抛出”）。
      `casing` 用 scale 0/1 当“看不见/看得见”（基岩版没有隐藏通道）。
    """
    BOLT_BACK = 1.90          # 枪机后退量（源坐标 2.5 × K）
    LIFT = 62.0               # 拉机柄上抬角（绕枪管轴 = Z 轴，+ = 向上抬）

    # 拉机柄 + 枪机（时间基准）
    bolt_ch = {
        'rotation': {'0.00': [0, 0, 0], '0.15': [0, 0, LIFT],
                     '0.70': [0, 0, LIFT], '0.95': [0, 0, 0]},
        'position': {'0.00': [0, 0, 0], '0.15': [0, 0, 0], '0.45': [0, 0, BOLT_BACK],
                     '0.70': [0, 0, BOLT_BACK], '0.95': [0, 0, 0]},
    }
    # 弹壳：抽壳 → 抛壳 → 翻滚（被枪机带出 1.25，再从抛壳口翻出）
    EXTRACT = 1.25            # 被枪机抽出的距离（模型像素）
    cs_pos = {
        '0.00': [0, 0, 0], '0.40': [0, 0, 0], '0.52': [0, 0.05, EXTRACT],
        '0.64': [0.85, 0.55, EXTRACT + 0.10], '0.88': [2.60, 1.45, EXTRACT - 0.60],
        '1.20': [4.90, 1.55, EXTRACT - 2.10], '1.60': [7.00, 0.60, EXTRACT - 3.60],
    }
    cs_rot = {
        '0.40': [0, 0, 0], '0.64': [35, 120, 200], '0.88': [330, 300, 470],
        '1.20': [700, 540, 780], '1.60': [1080, 800, 1140],
    }
    cs_scl = {'0.00': [0, 0, 0], '0.40': [1, 1, 1], '1.42': [1, 1, 1], '1.60': [0, 0, 0]}
    casing_ch = {'position': cs_pos, 'rotation': cs_rot, 'scale': cs_scl}

    def shift(channels, dt):
        return {ch: {'%0.2f' % (float(t) + dt): list(v) for t, v in keys.items()}
                for ch, keys in channels.items()}

    return {'format_version': '1.10.0', 'animations': {
        # 待机 / 跑动 / 疾跑：**故意保持静止**（枪在手里不允许晃，位移/角度一律清零，
        # 只留一条全零通道让 GeckoLib 能解析）
        'animation.awp.idle': {
            'loop': True, 'animation_length': 2.00,
            'bones': {'root': {'rotation': {'0.0': [0, 0, 0], '2.0': [0, 0, 0]}}},
        },
        'animation.awp.run': {
            'loop': True, 'animation_length': 1.00,
            'bones': {'root': {'rotation': {'0.0': [0, 0, 0], '1.0': [0, 0, 0]}}},
        },
        'animation.awp.run_fast': {
            'loop': True, 'animation_length': 1.00,
            'bones': {'root': {'rotation': {'0.0': [0, 0, 0], '1.0': [0, 0, 0]}}},
        },
        # 单独拉栓抛壳（单发循环动作）：上抬拉机柄 → 后退抽壳 → 弹壳翻滚抛出 → 推回闭锁
        'animation.awp.bolt': {
            'loop': False, 'animation_length': 1.60,
            'bones': {'bolt': bolt_ch, 'casing': casing_ch},
        },
        # 换弹：弹匣脱落 → 新弹匣装入 → 拉栓抛壳（bolt/casing 整体后移 0.90s）
        'animation.awp.reload': {
            'loop': False, 'animation_length': 2.60,
            'bones': {
                'magazine': {
                    'rotation': {'0.00': [0, 0, 0], '0.30': [14, 0, 0],
                                 '1.00': [14, 0, 0], '1.40': [0, 0, 0], '2.60': [0, 0, 0]},
                    'position': {'0.00': [0, 0, 0], '0.30': [0, -1.35, -0.45],
                                 '1.00': [0, -1.35, -0.45], '1.40': [0, 0, 0], '2.60': [0, 0, 0]},
                },
                'bolt': shift(bolt_ch, 0.90),
                'casing': shift(casing_ch, 0.90),
            },
        },
        # 8 倍镜调节（可循环）：变倍环绕镜筒轴转 720°、高低钮绕竖轴、风偏钮绕横轴
        'animation.awp.scope_adjust': {
            'loop': True, 'animation_length': 2.00,
            'bones': {
                'scope_adjust': {'rotation': {'0.0': [0, 0, 0], '2.0': [0, 0, 720]}},
                'scope_elev': {'rotation': {'0.0': [0, 0, 0], '2.0': [0, 360, 0]}},
                'scope_wind': {'rotation': {'0.0': [0, 0, 0], '2.0': [360, 0, 0]}},
            },
        },
        # 击发：扣扳机（绕顶部销轴向后转 11°）→ 回弹
        'animation.awp.fire': {
            'loop': False, 'animation_length': 0.35,
            'bones': {'trigger': {
                'rotation': {'0.00': [0, 0, 0], '0.05': [-11, 0, 0],
                             '0.12': [-11, 0, 0], '0.30': [0, 0, 0]},
            }},
        },
        # 开镜：镜身下沉 + 小幅俯仰
        'animation.awp.scope_ads': {
            'loop': False, 'animation_length': 0.35,
            'bones': {'scope': {
                'position': {'0.0': [0, 0, 0], '0.35': [0, -0.25, 0.35]},
                'rotation': {'0.0': [0, 0, 0], '0.35': [-2, 0, 0]},
            }},
        },
    }}


def main():
    geo = json.load(open(SRC_GEO, encoding='utf-8'))['minecraft:geometry'][0]
    src_bones = {b['name']: b for b in geo['bones']}

    nodes = {}
    order = []

    def add_bone(name, parent, pivot):
        if name in nodes:
            return
        p = [float(pivot[0]), float(pivot[1]), float(pivot[2])]
        p[2] *= BONE_SLIM_Z.get(name, 1.0)               # 微调 2：瘦身时 pivot 一起收
        sh = BONE_SHIFT.get(name)
        if sh:
            p = [p[i] + sh[i] for i in range(3)]
        node = {'name': name, 'pivot': [round(v, 4) for v in rot(p)]}
        if parent:
            node['parent'] = parent
        nodes[name] = node
        order.append(name)

    # root / move：本项目统一的「根 + 动作骨骼」；move 的 pivot = 握把（微调 2 后握把在 -1.3）
    add_bone('root', None, (0.0, 0.0, 0.0))
    add_bone('move', 'root', (-1.74, -1.43, 0.0))
    for src_name, name, parent in BONE_MAP:
        add_bone(name, parent, src_bones[src_name]['pivot'])
    for name, parent, pivot in EXTRA_BONES:              # 微调：可调镜 / 弹壳骨骼
        add_bone(name, parent, pivot)

    jobs = []
    cubes = 0
    faces = 0

    def add_cube(bone_name, origin, size, src_rects, mat=None, rot=None, pivot=None):
        """src_rects = 源贴图上的逐面矩形（None = 新方块，内容程序生成）"""
        uv = {}
        nodes[bone_name].setdefault('cubes', []).append(
            model_cube(origin, size, uv, rot, pivot))
        layout = face_layout(size)
        for old_face, new_face in FACE_REMAP.items():
            gw, gh = layout[old_face]
            job = {'cube': uv, 'face': new_face, 'w': gw, 'h': gh, 'mat': mat, 'sx': None}
            if src_rects is not None:
                u, v, w, h = src_rects[old_face]
                job.update(sx=u, sy=v, sw=w, sh=h)
            jobs.append(job)
            uv[new_face] = None                          # 装箱后回填
        return uv

    for src_name, name, parent in BONE_MAP:
        for c in src_bones[src_name].get('cubes', []):
            target = CUBE_MOVE.get((src_name, key(c['origin'])), name)   # 微调：拆部件到新骨骼
            origin = tuple(float(v) for v in c['origin'])
            size = tuple(float(v) for v in c['size'])
            old_size = size
            rp = REPLACE.get((src_name, key(c['origin'])))               # 微调 5：换几何（倍镜拟圆 / 重画扳机）
            if rp:
                rects = box_uv(c['uv'][0], c['uv'][1], *old_size)
                for ent in rp:
                    ro, rsz = ent[0], ent[1]
                    rr = ent[2] if len(ent) > 2 else None
                    rpiv = ent[3] if len(ent) > 3 else None
                    o2, s2 = xform(ro, rsz, target)
                    if rpiv:
                        rpiv = xform(rpiv, (0.0, 0.0, 0.0), target)[0]
                    add_cube(target, o2, s2, None if CUBE_MAT.get((src_name, key(c['origin']))) else rects,
                             mat=CUBE_MAT.get((src_name, key(c['origin']))), rot=rr, pivot=rpiv)
                    cubes += 1
                    faces += 6
                continue
            kz = BONE_SLIM_Z.get(target, 1.0)                            # 微调 2：宽度瘦身
            if kz != 1.0:
                origin = (origin[0], origin[1], origin[2] * kz)
                size = (size[0], size[1], size[2] * kz)
            rs = RESHAPE.get((src_name, key(c['origin'])))               # 微调 2：改形/移位
            if rs:
                origin = tuple(float(v) for v in rs[0])
                size = tuple(float(v) for v in rs[1])
            sh = BONE_SHIFT.get(target)                                  # 微调 2：整体平移
            if sh:
                origin = tuple(origin[i] + sh[i] for i in range(3))
            cr = CUBE_ROT.get((src_name, key(c['origin'])))              # 微调 3：方块旋转（握把后倾）
            mt = CUBE_MAT.get((src_name, key(c['origin'])))              # 材质覆盖
            add_cube(target, origin, size,
                     None if mt else box_uv(c['uv'][0], c['uv'][1], *old_size),
                     mat=mt, rot=cr[0] if cr else None, pivot=cr[1] if cr else None)
            cubes += 1
            faces += 6

    for bone_name, origin, size, mat in DETAILS:         # 微调：细节件 + 弹壳
        add_cube(bone_name, origin, size, None, mat)
        cubes += 1
        faces += 6

    den = pack(jobs)                                     # 贴图重新装箱 → 密度（像素/单位）
    for f in jobs:
        f['cube'][f['face']] = {'uv': [f['px'], f['py']], 'uv_size': [f['pw'], f['ph']]}

    out_bones = [nodes[n] for n in order]

    out = {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': IDENT,
                        'texture_width': geo['description']['texture_width'] * TEX_SCALE,
                        'texture_height': geo['description']['texture_height'] * TEX_SCALE,
                        'visible_bounds_width': 4, 'visible_bounds_height': 2.5,
                        'visible_bounds_offset': [0, 0.6, 0]},
        'bones': out_bones}]}
    os.makedirs(os.path.dirname(OUT_GEO), exist_ok=True)
    with open(OUT_GEO, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))

    img, glow = paint_faces(SRC_TEX, jobs)               # 逐面重绘（在 512 分辨率下重新画）
    img.save(OUT_TEX)
    # 流光遮罩：格式与 gen_glowmask.py 一致（RGB = 贴图 ×1.08，alpha = 遮罩）
    ga = np.asarray(img).astype(np.float32)
    ga[..., :3] = np.clip(ga[..., :3] * 1.08, 0, 255)
    ga[..., 3] = np.clip(glow * 255.0, 0, 255)
    Image.fromarray(ga.astype(np.uint8)).save(OUT_GLOW)

    with open(OUT_ANIM, 'w', encoding='utf-8') as fh:
        json.dump(anim_json(), fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------ 自检
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for b in out_bones:
        for c in b.get('cubes', []):
            for i in range(3):
                lo[i] = min(lo[i], c['origin'][i])
                hi[i] = max(hi[i], c['origin'][i] + c['size'][i])
    print('骨骼 %d / 方块 %d / 面 %d' % (len(out_bones), cubes, faces))
    for b in out_bones:
        n = len(b.get('cubes', []))
        print('  %-14s parent=%-12s pivot=%s  cubes=%d'
              % (b['name'], b.get('parent') or '-', b['pivot'], n))
    print('包围盒 X %.3f..%.3f  Y %.3f..%.3f  Z %.3f..%.3f'
          % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    print('长度 %.2f 格 / 高 %.2f 格 / 宽 %.2f 格'
          % ((hi[2] - lo[2]) / 16.0, (hi[1] - lo[1]) / 16.0, (hi[0] - lo[0]) / 16.0))
    print('贴图 %dx%d  装箱 %d 个面（%d 方块）/ 密度 %.0f 像素每单位（旧方案 4）'
          % (img.width, img.height, len(jobs), cubes, den))
    seen = set()
    dup = 0
    for f in jobs:
        for yy in range(f['py'], f['py'] + f['ph']):
            for xx in range(f['px'], f['px'] + f['pw']):
                dup += 1 if (xx, yy) in seen else 0
                seen.add((xx, yy))
    print('自检：逐面 UV 重叠像素 = %d %s' % (dup, 'OK' if not dup else '✗ 装箱有重叠'))
    print('wrote', os.path.relpath(OUT_GEO, ROOT))
    print('wrote', os.path.relpath(OUT_TEX, ROOT))
    print('wrote', os.path.relpath(OUT_ANIM, ROOT))
    print('wrote', os.path.relpath(OUT_GLOW, ROOT),
          '（发光像素 %d）' % int((glow > 0.15).sum()))

    # ------------------------------------------------------------------ Java 侧要用的关键点（模型像素，已缩放）
    def pt(x, y, z, tag):
        p = rot([x, y, z])
        print('  %-12s [%8.3f, %8.3f, %8.3f]' % (tag, p[0], p[1], p[2]))

    print('关键点（模型像素，喂给 WeaponMount / GeoModel）:')
    pt(21.7, 2.10, 0.0, 'MUZZLE')          # 枪口端面中心（微调 4：枪管加长后前伸到这里）
    pt(0.30, 1.85, 0.83, 'EJECT_PORT')     # 抛壳口中心（弹壳从这儿飞出）
    pt(-1.74, -1.43, 0.0, 'GRIP')          # 握把中心（右手指位，= move pivot；后倾 17°）
    pt(9.50, 0.90, 0.0, 'FORE')            # 护木/枪管下方（左手托位）
    pt(-0.50, 2.00, 1.67, 'BOLT_HANDLE')   # 枪机拉柄外端（左手拉栓终点）
    pt(2.70, -2.02, 0.0, 'MAG_BOTTOM')     # 弹匣底（微调 3：短弹匣，前 x 1.9~3.5）
    pt(0.0, 4.20, 0.0, 'SCOPE_AXIS')       # 8 倍镜光轴（变倍环/调节钮都绕它自转）
    pt(0.90, 1.80, 0.425, 'CASING_PIVOT')  # 弹壳骨骼枢轴
    return 0


if __name__ == '__main__':
    sys.exit(main())
