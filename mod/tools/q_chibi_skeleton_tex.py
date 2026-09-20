#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Q 版骷髅皮肤（64×64）—— 与 `q_chibi_zombie.png` **同一张 UV 表**，只是画成骨头。

写进 Q 版覆盖层：`src/qresources/assets/hexalunar_calamity_q/textures/entity/q_chibi_skeleton.png`

UV 表（与 `client/QChibiZombieModel` 的几何一一对应，改模型必须同步改这里）：
    head     12×12×12 @ (0, 0)    → 展开 48×24，正面 (12,12) 12×12
    body      6× 6× 5 @ (0, 26)   → 展开 22×11，正面 (5,31)   6×6
    right_arm 4× 8× 4 @ (0, 38)   → 展开 16×12，正面 (4,42)
    left_arm  4× 8× 4 @ (18, 38)
    right_leg 4× 5× 4 @ (0, 51)   → 展开 16×9， 正面 (4,56)
    left_leg  4× 5× 4 @ (18, 51)

（Bedrock/vanilla 的盒子展开规则：给定 (w,h,d) 与 texOffs(u,v)，
  右面 (u, v+d, d, h)、正面 (u+d, v+d, w, h)、左面 (u+d+w, v+d, d, h)、
  背面 (u+d+w+d, v+d, w, h)、顶面 (u+d, v, w, d)、底面 (u+d+w, v, w, d)。）
"""
import io
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'src', 'qresources', 'assets', 'hexalunar_calamity_q',
                   'textures', 'entity', 'q_chibi_skeleton.png')
TEX = 64

BONE = (232, 232, 222)
BONE_D = (198, 198, 188)      # 侧面/顶面暗一档
BONE_DD = (168, 168, 158)     # 关节/阴影
SOCKET = (46, 42, 40)         # 眼窝
TOOTH = (246, 246, 240)


def box(d, u, v, w, h, dep, front=BONE, side=BONE_D, top=BONE_D):
    """按 vanilla 展开规则画一个盒子的六个面（只画需要的，够用就行）"""
    d.rectangle([u, v + dep, u + dep - 1, v + dep + h - 1], fill=side)                  # 右
    d.rectangle([u + dep, v + dep, u + dep + w - 1, v + dep + h - 1], fill=front)       # 前
    d.rectangle([u + dep + w, v + dep, u + dep + w + dep - 1, v + dep + h - 1], fill=side)   # 左
    d.rectangle([u + dep + w + dep, v + dep, u + dep + w + dep + w - 1, v + dep + h - 1], fill=side)  # 后
    d.rectangle([u + dep, v, u + dep + w - 1, v + dep - 1], fill=top)                   # 顶
    d.rectangle([u + dep + w, v, u + dep + w + w - 1, v + dep - 1], fill=top)           # 底
    return (u + dep, v + dep, w, h)          # 正面矩形（供继续画细节）


def main():
    img = Image.new('RGBA', (TEX, TEX), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # ---------------- 头：骷髅脸（正面 12×12 @ (12,12)） ----------------
    fx, fy, fw, fh = box(d, 0, 0, 12, 12, 12, front=BONE, side=BONE_D, top=BONE_D)
    # 眼窝（两个大方黑框，Q 版的"大眼"就是它）
    d.rectangle([fx + 2, fy + 3, fx + 4, fy + 6], fill=SOCKET)
    d.rectangle([fx + 7, fy + 3, fx + 9, fy + 6], fill=SOCKET)
    # 鼻腔
    d.rectangle([fx + 5, fy + 7, fx + 6, fy + 8], fill=BONE_DD)
    # 牙：一排竖直分隔线
    d.rectangle([fx + 2, fy + 9, fx + 9, fy + 10], fill=BONE_DD)
    for tx in range(fx + 3, fx + 9, 2):
        d.rectangle([tx, fy + 9, tx, fy + 10], fill=TOOTH)
    # 后脑的骨缝
    d.rectangle([fx + 4, fy - 8, fx + 7, fy - 6], fill=BONE_DD)

    # ---------------- 身子：肋骨（正面 6×6 @ (5,31)） ----------------
    bx, by, bw, bh = box(d, 0, 26, 6, 6, 5, front=BONE, side=BONE_D, top=BONE_D)
    for ry in range(by + 1, by + 5, 2):
        d.rectangle([bx, ry, bx + bw - 1, ry], fill=BONE_DD)          # 肋骨横线
    d.rectangle([bx + 2, by + 1, bx + 3, by + 4], fill=BONE_DD)        # 脊柱

    # ---------------- 四肢：骨头 + 关节暗环 ----------------
    for (u, v) in ((0, 38), (18, 38)):        # 手臂 4×8×4
        ax, ay, aw, ah = box(d, u, v, 4, 8, 4, front=BONE, side=BONE_D, top=BONE_D)
        d.rectangle([ax, ay + 3, ax + aw - 1, ay + 4], fill=BONE_DD)
        d.rectangle([ax + 1, ay + 6, ax + 2, ay + 7], fill=BONE_DD)
    for (u, v) in ((0, 51), (18, 51)):        # 腿 4×5×4
        lx, ly, lw, lh = box(d, u, v, 4, 5, 4, front=BONE, side=BONE_D, top=BONE_D)
        d.rectangle([lx, ly + 2, lx + lw - 1, ly + 3], fill=BONE_DD)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print('wrote', os.path.relpath(OUT, ROOT), img.size)
    # 顺手把几个关键色块打印出来，方便肉眼核对没画歪
    print('  head front  =', img.getpixel((fx + 0, fy + 0)), '→ 眼睛', img.getpixel((fx + 3, fy + 4)))
    print('  body front  =', img.getpixel((bx, by)), '→ 肋骨', img.getpixel((bx + 1, by + 1)))


if __name__ == '__main__':
    main()
