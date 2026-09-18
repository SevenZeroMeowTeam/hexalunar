"""从武器贴图生成发光遮罩 `<name>_glowmask.png`。

思路：**把"抛光高光"那部分像素标成发光**（按亮度取高分位阈值），
于是"光滑反光"的部位在暗处也会亮，并由 `GlossGlintLayer` 让它随时间脉动 = 流光。

用法:
  python tools/gen_glowmask.py                 # 处理 assets 里全部武器贴图
  python tools/gen_glowmask.py <base.png> [<out.png>] [--pct 96.5]
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXDIR = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                      'textures', 'models')
BASES = ['akm_geo.png', 'mud_geo.png', 'flashbang_geo.png', 'compound_bow_geo.png',
         'crossbow_geo.png']


def dilate(m, k=1):
    """把遮罩膨胀 k 像素：原来只有 1 像素宽的倒角高光太细，膨胀后流光才看得出来。"""
    if k <= 0:
        return m
    p = np.pad(m, k, mode='edge')
    out = m.copy()
    h, w = m.shape
    for dy in range(0, 2 * k + 1):
        for dx in range(0, 2 * k + 1):
            out = np.maximum(out, p[dy:dy + h, dx:dx + w])
    return out


def make(base_path, out_path, pct=94.5, dil=1):
    img = Image.open(base_path).convert('RGBA')
    a = np.asarray(img).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3]
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    valid = (alpha > 8.0) & (luma > 40.0)
    if not valid.any():
        print('!! %s 没有有效像素' % os.path.basename(base_path))
        return None
    thr = float(np.percentile(luma[valid], pct))
    # 软过渡：阈值往上 26 级亮度内渐入，超过就是纯发光
    m = np.clip((luma - thr) / 26.0, 0.0, 1.0) ** 0.8
    m[~valid] = 0.0
    m = dilate(m, dil)
    m[~valid] = 0.0
    out_rgb = np.clip(rgb * 1.08, 0.0, 255.0)
    out = np.concatenate([out_rgb, (m * 255.0)[..., None]], axis=-1)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(out_path)
    n = int((m > 0.15).sum())
    print('%-30s 阈值 %5.1f  发光像素 %6d (%.2f%%)' % (os.path.basename(out_path), thr, n,
                                                     100.0 * n / max(1, int(valid.sum()))))
    return out_path


def main(argv):
    args = [x for x in argv[1:] if not x.startswith('--')]
    pct = 94.5
    dil = 1
    for i, x in enumerate(argv):
        if x == '--pct':
            pct = float(argv[i + 1])
        if x == '--dilate':
            dil = int(argv[i + 1])
    if args:
        base = args[0]
        out = args[1] if len(args) > 1 else os.path.splitext(base)[0] + '_glowmask.png'
        make(base, out, pct, dil)
        return
    for name in BASES:
        base = os.path.join(TEXDIR, name)
        if not os.path.exists(base):
            print('!! 缺 %s' % base)
            continue
        make(base, os.path.join(TEXDIR, os.path.splitext(name)[0] + '_glowmask.png'), pct, dil)


if __name__ == '__main__':
    main(sys.argv)
