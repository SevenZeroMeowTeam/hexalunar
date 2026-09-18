"""生成开镜遮罩贴图 scope_glare.png：镜筒暗角 + 角落镜头眩光。

★ 上一版是"中心一大团白光"（中心 alpha 0.62），进游戏等于蒙了层白布，看不清生物。
  现在：
    r < 0.80  ：alpha = 0  —— 准星与目标区**完全透明**，一点都不挡
    0.80 ~ 1.12：冷蓝黑暗角柔和渐入（最外 alpha 约 110，很轻）
    内缘 r≈0.82 处加一道极淡的亮环（镜片边缘反光）
    左上角一块低强度暖色柔光（镜头眩光，峰值 alpha 约 48，且远离准星）
  客户端按「拉满整屏」贴（blit 到 0,0,w,h），16:9 下暗角自然落在屏幕外圈。

产出: src/main/resources/assets/hexalunar_calamity/textures/gui/scope_glare.png
"""
import math
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                   'textures', 'gui', 'scope_glare.png')
N = 256

CLEAR_R = 0.80        # 这个半径内完全不挡（准星区）
VIG_A = 110.0         # 暗角最外圈 alpha（轻）
RIM_A = 26.0          # 内缘亮环 alpha
RIM_R = 0.82
FLARE_A = 48.0        # 角落眩光峰值 alpha
FLARE_X, FLARE_Y = 0.26, 0.24   # 眩光中心（左上，归一化）
FLARE_R = 0.40


def main():
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    px = img.load()
    c = (N - 1) / 2.0
    for y in range(N):
        for x in range(N):
            dx, dy = (x - c) / c, (y - c) / c
            r = math.hypot(dx, dy)

            # 暗角（冷蓝黑）
            va = 0.0
            if r > CLEAR_R:
                t = min(1.0, (r - CLEAR_R) / (1.12 - CLEAR_R))
                va = VIG_A * (t ** 1.7)
            vr, vg, vb = 10.0, 12.0, 17.0

            # 内缘亮环（很淡）
            rim = max(0.0, 1.0 - abs(r - RIM_R) / 0.05)
            if rim > 0.0:
                ra = RIM_A * rim * rim
                if ra > va:
                    va, vr, vg, vb = ra, 150.0, 175.0, 195.0

            # 角落眩光（暖白）
            fd = math.hypot((x / float(N) - FLARE_X), (y / float(N) - FLARE_Y)) / FLARE_R
            fa = FLARE_A * max(0.0, 1.0 - fd) ** 2.4

            a = max(va, fa)
            if a <= 0.5:
                continue
            w = fa / (va + fa) if (va + fa) > 1e-6 else 0.0
            rr = vr * (1.0 - w) + 255.0 * w
            gg = vg * (1.0 - w) + 250.0 * w
            bb = vb * (1.0 - w) + 236.0 * w
            px[x, y] = (int(rr), int(gg), int(bb), int(min(255.0, a)))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print('wrote %s  %dx%d（中心 r<%.2f 全透明）' % (OUT, N, N, CLEAR_R))


if __name__ == '__main__':
    main()
