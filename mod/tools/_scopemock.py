"""离线模拟十字弩开镜画面：截一张游戏截图当背景 → 4 倍放大 → 按 ClientEvents.drawScopeOverlay
的同一套数学画遮罩/暗角/分划，用来在不开游戏的情况下检查开镜视野是否干净、分划是否居中。

用法: python tools/_scopemock.py <背景png> <输出png> [GUI倍率]
"""
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    src = argv[1]
    if not os.path.isabs(src):
        src = os.path.join(ROOT, src)
    out = os.path.join(ROOT, argv[2] if len(argv) > 2 else 'build/_scopemock.png')
    scale = float(argv[3]) if len(argv) > 3 else 2.0
    bg = Image.open(src).convert('RGB')
    W, H = bg.size
    # 4 倍镜：把画面中心 1/4 放大回来（= FOV 缩到 1/4）
    cw, ch = W // 4, H // 4
    zoom = bg.crop((W // 2 - cw // 2, H // 2 - ch // 2, W // 2 + cw // 2, H // 2 + ch // 2))
    zoom = zoom.resize((W, H), Image.NEAREST)

    gw, gh = int(W / scale), int(H / scale)      # 等效 GUI 尺寸
    ov = Image.new('RGBA', (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cx, cy = gw // 2, gh // 2
    r = int(min(gw, gh) * 0.44)
    mask = (10, 10, 12, 0xF0)
    # 镜筒外近黑
    for y in range(gh):
        dy = y - cy
        dx2 = r * r - dy * dy
        if dx2 <= 0:
            d.line([(0, y), (gw, y)], fill=mask)
            continue
        dx = int(dx2 ** 0.5)
        d.line([(0, y), (cx - dx, y)], fill=mask)
        d.line([(cx + dx, y), (gw, y)], fill=mask)
    # 镜缘单圈暗角（最外 7%）+ 玻璃细环
    band = max(3, r * 7 // 100)
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        outer = int(max(0, r * r - dy * dy) ** 0.5)
        inner = int(max(0, (r - band) * (r - band) - dy * dy) ** 0.5)
        if outer > inner:
            d.line([(cx - outer, y), (cx - inner, y)], fill=(0, 0, 0, 0x1C))
            d.line([(cx + inner, y), (cx + outer, y)], fill=(0, 0, 0, 0x1C))
        d.line([(cx - outer, y), (cx - outer + 2 * int(scale), y)], fill=(255, 255, 255, 0x33))
        d.line([(cx + outer - 2 * int(scale), y), (cx + outer, y)], fill=(255, 255, 255, 0x33))
    # 分划（对称，粗细 1 GUI 像素）
    gap, ln = 10, max(14, min(r // 4, 40))
    tick = max(5, ln // 2)
    t = 1
    near, far = (255, 255, 255, 0x8C), (255, 255, 255, 0x3A)
    d.rectangle([cx - t, cy - gap - tick, cx, cy - gap], fill=near)
    d.rectangle([cx - t, cy - gap - ln, cx, cy - gap - tick], fill=far)
    d.rectangle([cx - t, cy + gap, cx, cy + gap + tick], fill=near)
    d.rectangle([cx - t, cy + gap + tick, cx, cy + gap + ln], fill=far)
    d.rectangle([cx - gap - tick, cy - t, cx - gap, cy], fill=near)
    d.rectangle([cx - gap - ln, cy - t, cx - gap - tick, cy], fill=far)
    d.rectangle([cx + gap, cy - t, cx + gap + tick, cy], fill=near)
    d.rectangle([cx + gap + tick, cy - t, cx + gap + ln, cy], fill=far)
    d.rectangle([cx - t, cy - t, cx, cy], fill=(255, 255, 255, 0x9C))

    ov = ov.resize((W, H), Image.NEAREST)
    out_img = Image.alpha_composite(zoom.convert('RGBA'), ov).convert('RGB')
    out_img.save(out)
    print('wrote %s  (GUI %dx%d, r=%d)' % (os.path.relpath(out, ROOT), gw, gh, r))


if __name__ == '__main__':
    main(sys.argv)
