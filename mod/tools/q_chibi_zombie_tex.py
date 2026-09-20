#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Q 弹版僵尸皮肤（64×64）—— 严格按 `client/QChibiZombieModel` 的 UV 表绘制。

Q 版模型把方块尺寸改了（头 12³、身 6×6×5、臂 4×8×4、腿 4×5×4），
所以**不能**沿用原版僵尸贴图（原版头只有 32×16 的展开区）——这张皮是给 Q 版几何专用的。

UV 表（与 `QChibiZombieModel.createBodyLayer()` 必须一致；MC 的展开规则：
`w×h×d` 的方块在 `texOffs(u,v)` 处占 `2(w+d) × (d+h)`，**正面**在 `(u+d, v+d)` 大小 `w×h`）

    =========  ========  ============  ==================
    部位        尺寸@uv    展开区          正面（画脸/衣裤）
    =========  ========  ============  ==================
    head       12³ @ 0,0  48×24         (12,12) 12×12
    body        6×6×5@0,26 22×11        (5,31)   6×6
    right_arm   4×8×4@0,38 16×12        (4,42)   4×8
    left_arm    4×8×4@18,38 16×12       (22,42)  4×8
    right_leg   4×5×4@0,51 16×9         (4,55)   4×5
    left_leg    4×5×4@18,51 16×9        (22,55)  4×5
    =========  ========  ============  ==================

用法: python tools/q_chibi_zombie_tex.py
产出: src/qresources/assets/hexalunar_calamity_q/textures/entity/q_chibi_zombie.png
"""
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'src', 'qresources', 'assets', 'hexalunar_calamity_q',
                   'textures', 'entity', 'q_chibi_zombie.png')
PREVIEW = os.path.join(ROOT, 'build', '_q_chibi_zombie_x8.png')

# ---- 配色（Q 版：亮、干净、饱和）----
SKIN = (104, 150, 92)
SKIN_D = (78, 118, 70)
SKIN_HI = (126, 176, 110)
HAIR = (54, 74, 52)
STITCH = (40, 52, 40)
EYE_W = (248, 250, 245)
EYE_B = (34, 38, 46)
BLUSH = (222, 126, 126)
SHIRT = (62, 72, 100)
SHIRT_HI = (84, 96, 128)
SHIRT_D = (44, 52, 74)
PANTS = (48, 54, 70)
PANTS_HI = (66, 74, 94)
BELT = (36, 34, 40)
BLOOD = (108, 132, 92)


def px(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c + (255,))


def rect(img, x0, y0, x1, y1, c):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            px(img, x, y, c)


def main():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))

    # ---------------- 头：12³ @ (0,0)，展开 48×24 ----------------
    rect(img, 0, 0, 47, 23, SKIN)                 # 整块铺皮肤
    rect(img, 0, 0, 47, 11, SKIN)                 # 上半条 = 顶/底面 + 侧面顶部
    rect(img, 12, 0, 23, 11, HAIR)                # 头顶（up 面）→ 头发
    rect(img, 12, 12, 23, 13, HAIR)               # 额头刘海
    rect(img, 0, 12, 11, 23, SKIN_D)              # 右脸/左脸侧面暗一档
    rect(img, 24, 12, 35, 23, SKIN_D)
    rect(img, 36, 12, 47, 23, SKIN)               # 后脑勺
    # 大眼睛（左 14..17 / 右 19..22，y 15..18）
    rect(img, 14, 15, 17, 18, EYE_W)
    rect(img, 15, 16, 16, 17, EYE_B)
    rect(img, 19, 15, 22, 18, EYE_W)
    rect(img, 20, 16, 21, 17, EYE_B)
    # 腮红 + 缝合嘴
    rect(img, 13, 19, 14, 20, BLUSH)
    rect(img, 22, 19, 23, 20, BLUSH)
    for x in range(16, 21):
        px(img, x, 21, STITCH)
    px(img, 16, 20, STITCH)
    px(img, 20, 20, STITCH)
    rect(img, 18, 21, 18, 22, STITCH)             # 中间一针竖着，像缝过
    # 头顶高光一点，别死板
    px(img, 14, 2, SKIN_HI)
    px(img, 20, 4, SKIN_HI)

    # ---------------- 身子 6×6×5 @ (0,26)，展开 22×11 ----------------
    rect(img, 0, 26, 21, 36, SHIRT)
    rect(img, 0, 26, 21, 30, SHIRT_D)             # 上半（肩/背）暗一档
    rect(img, 5, 31, 10, 36, SHIRT)               # 正面
    rect(img, 5, 31, 10, 31, SHIRT_HI)            # 衣领
    rect(img, 7, 33, 8, 36, BLOOD)                # 撕开一道口子，露出灰绿皮肤
    rect(img, 5, 36, 10, 36, BELT)                # 腰带
    px(img, 6, 35, SHIRT_HI)

    # ---------------- 手臂 4×8×4（两条）----------------
    for u in (0, 18):
        rect(img, u, 38, u + 15, 49, SKIN)
        rect(img, u + 4, 38, u + 7, 41, SHIRT)    # 破袖子（顶面）
        rect(img, u + 4, 42, u + 7, 43, SHIRT)    # 正面袖子
        rect(img, u + 4, 44, u + 7, 49, SKIN)     # 小臂露出来
        px(img, u + 5, 46, SKIN_D)                # 一点脏污
        px(img, u + 6, 48, SKIN_HI)

    # ---------------- 腿 4×5×4（两条）----------------
    for u in (0, 18):
        rect(img, u, 51, u + 15, 59, PANTS)
        rect(img, u + 4, 55, u + 7, 59, PANTS)    # 正面
        rect(img, u + 4, 55, u + 5, 56, PANTS_HI)
        rect(img, u + 6, 58, u + 7, 59, STITCH)   # 裤脚磨破

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    img.resize((img.width * 8, img.height * 8), Image.NEAREST).save(PREVIEW)

    # 自检：UV 区域必须落在 64×64 内
    regions = [('head', 0, 0, 48, 24), ('body', 0, 26, 22, 11),
               ('right_arm', 0, 38, 16, 12), ('left_arm', 18, 38, 16, 12),
               ('right_leg', 0, 51, 16, 9), ('left_leg', 18, 51, 16, 9)]
    bad = 0
    for name, x, y, w, h in regions:
        ok = x + w <= 64 and y + h <= 64
        bad += 0 if ok else 1
        print('  %-10s uv=(%2d,%2d) 展开 %2dx%-2d  %s' % (name, x, y, w, h, 'OK' if ok else '*** 越界 ***'))
    print('wrote %s  (%dx%d)  预览 build\\_q_chibi_zombie_x8.png'
          % (os.path.relpath(OUT, ROOT), img.width, img.height))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
