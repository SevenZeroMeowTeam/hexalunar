#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""倍镜遮罩离线预览：把 ClientEvents.drawScopeOverlay 的绘制数学复刻一遍，出 PNG。

调十字分划（长度/透明度/中心留白）时不用进游戏，直接看图对比：
    python tools/scope_preview.py                 # 出「当前样式」与「旧样式」两张对比图
    python tools/scope_preview.py --out dir       # 指定输出目录

复刻的 GUI 尺寸取 428x240（约等于 1080p + GUI scale 3），比例和游戏一致。
"""
import argparse
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def write_png(path, w, h, pix):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += pix[y * w * 4:(y + 1) * w * 4]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


class Canvas:
    """等价于 GuiGraphics：blit(color, x1, y1, x2, y2) 对应 fill 的 [x1,x2) × [y1,y2)"""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.pix = bytearray(w * h * 4)

    def blit(self, color, x1, y1, x2, y2):
        a = (color >> 24) & 0xFF
        r, g, b = (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF
        for y in range(max(0, y1), min(self.h, y2)):
            row = y * self.w
            for x in range(max(0, x1), min(self.w, x2)):
                i = (row + x) * 4
                if a >= 255:
                    self.pix[i:i + 4] = bytes((r, g, b, 255))
                else:
                    inv = 255 - a
                    self.pix[i] = (r * a + self.pix[i] * inv) // 255
                    self.pix[i + 1] = (g * a + self.pix[i + 1] * inv) // 255
                    self.pix[i + 2] = (b * a + self.pix[i + 2] * inv) // 255
                    self.pix[i + 3] = 255


def background(c):
    """假地形 + 中间一个人形目标，方便判断遮挡"""
    for y in range(c.h):
        t = y / c.h
        base = (60 + int(50 * t), 90 + int(70 * t), 150 + int(80 * t))
        c.blit(0xFF000000 | (base[0] << 16) | (base[1] << 8) | base[2], 0, y, c.w, y + 1)
    horizon = c.h // 2 + 18
    c.blit(0xFF6E5A3C, 0, horizon, c.w, c.h)
    cx, cy = c.w // 2, c.h // 2
    c.blit(0xFF23282E, cx - 7, cy - 26, cx + 7, cy + 30)
    c.blit(0xFF23282E, cx - 11, cy - 24, cx + 11, cy - 8)


def overlay(c, style):
    w, h = c.w, c.h
    cx, cy = w // 2, h // 2
    r = min(w, h) * 42 // 100

    # 圆形黑边
    ring = (0xDD << 24) | 0x0A0A0A
    for y in range(h):
        dy = y - cy
        dx2 = r * r - dy * dy
        if dx2 <= 0:
            c.blit(ring, 0, y, w, y + 1)
            continue
        dx = int(dx2 ** 0.5)
        c.blit(ring, 0, y, cx - dx, y + 1)
        c.blit(ring, cx + dx, y, w, y + 1)

    # 镜筒边缘细环
    edge = 0x66 << 24
    for y in range(h):
        dy = y - cy
        dx2 = (r + 2) ** 2 - dy * dy
        dxr = (r - 1) ** 2 - dy * dy
        if dx2 > 0:
            outer = int(dx2 ** 0.5)
            inner = int(dxr ** 0.5) if dxr > 0 else 0
            if outer > inner:
                c.blit(edge, cx - outer, y, cx - inner, y + 1)
                c.blit(edge, cx + inner, y, cx + outer, y + 1)

    if style == "old":
        line = 0xB0FFFFFF
        c.blit(line, cx - 1, cy - r // 2, cx, cy - 6)
        c.blit(line, cx - 1, cy + 6, cx, cy + r // 2)
        c.blit(line, cx - r // 2, cy - 1, cx - 6, cy)
        c.blit(line, cx + 6, cy - 1, cx + r // 2, cy)
        c.blit(0xE0FFFFFF, cx - 1, cy - 1, cx + 1, cy + 1)
    else:
        gap = 9
        length = max(16, min(r // 3, 52))
        tick = max(6, length // 3)
        near, far = 0x74FFFFFF, 0x3CFFFFFF
        c.blit(near, cx - 1, cy - gap - tick, cx, cy - gap)
        c.blit(far, cx - 1, cy - gap - length, cx, cy - gap - tick)
        c.blit(near, cx - 1, cy + gap, cx, cy + gap + tick)
        c.blit(far, cx - 1, cy + gap + tick, cx, cy + gap + length)
        c.blit(near, cx - gap - tick, cy - 1, cx - gap, cy)
        c.blit(far, cx - gap - length, cy - 1, cx - gap - tick, cy)
        c.blit(near, cx + gap, cy - 1, cx + gap + tick, cy)
        c.blit(far, cx + gap + tick, cy - 1, cx + gap + length, cy)
        c.blit(0x9CFFFFFF, cx - 1, cy - 1, cx, cy)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "scope_preview"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for style in ("old", "new"):
        canvas = Canvas(428, 240)
        background(canvas)
        overlay(canvas, style)
        path = os.path.join(args.out, f"scope-{style}.png")
        write_png(path, canvas.w, canvas.h, canvas.pix)
        print("written:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
