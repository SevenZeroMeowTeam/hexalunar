# -*- coding: utf-8 -*-
"""r118：三种弹药的 3D 模型（.338 / 7.62x59 / 7.62x61）。用法: python tools/_commit_r118.py
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
ROOT = os.path.dirname(MOD)
BUILD = os.path.join(MOD, 'build')
R = 'mod/src/main/resources/assets/hexalunar_calamity'

FILES = [
    'readme.md', 'mod/README.md', 'mod/build.gradle',
    'mod/tools/ammo_v3.py',
    'mod/tools/jsonmodel_view.py',
    'mod/tools/_ammo_probe.py',
    R + '/models/item/ammo_338.json',
    R + '/models/item/ammo_762_59.json',
    R + '/models/item/ammo_762_61.json',
    R + '/textures/item/ammo_338.png',
    R + '/textures/item/ammo_762_59.png',
    R + '/textures/item/ammo_762_61.png',
]

MSG = u"""feat(ammo): r118 三种弹药的模型重新设计 —— 2D 图标换成 3D 立体子弹

用户原话：「.338，7.62x59，7.62x61 子弹模型需要重新设计并建模」

【以前】三种弹药都是 item/generated 的**平面图**（一张 16² png 里画两发斜放的子弹），
拿在手里 / 扔在地上 / 放进展示框都是**一张纸片**。

【现在】真正的 3D 物品模型 —— 用原版 `elements`（**不动 Java、不加 GeckoLib**）：
1. 生成器 tools/ammo_v3.py，造型从下往上：
   底缘（**八棱盘** + 底火圆点）→ 壳身（**八棱柱**，8 块绕 Y 轴旋转的薄板 ——
   与武器上的八棱枪管 / 镜筒同一套审美）→ 壳肩收口 → 弹头（三段递减 + 尖端）。
   共 20 个元素；**原点放在几何中心**（物品模型的 (0,0,0) 在物品栏里是格子中心，
   从 y=0 往上长的话子弹会吊在格子上半部 —— 第一版就踩了这个坑）。
2. 三种弹按**真实口径比例**区分（1 模型像素 ≈ 11 mm）：
   .338 Lapua（8.6×70）总高 9.00 / 7.62×54R（莫辛·Kar98k，**凸缘弹**，底缘单独放大）
   8.00 / .30-06（7.62×61，M1）7.80 —— 拿在手里一眼能分出型号。
3. 贴图各自 64×64、逐面 UV（脚本自己装箱）：黄铜壳身带柱面明暗、铜被甲弹头、
   底缘下表面的深色底火。

【新增工具】
tools/jsonmodel_view.py —— 离线渲染**原版 JSON 物品模型**（不用开游戏）：读 elements
（含绕 Y 轴旋转）→ 背面剔除 → **按元素**排序（按单个面排序会在小方块交错时画错层）
→ 正交投影 + **棱边描线**（不描线的「平均色填面」会把八棱柱糊成方柱，看不出形状）。
这个预览器是本轮能改对的关键。

【踩过的坑】
- 壳肩方块尺寸必须**小于八棱柱的内切圆**（case_d × 0.924）：用 case_d − 0.10 仍比
  内切圆宽 ⇒ 会从筒壁里凸出来。
- 收口别拆成六段小方块（sh0/sh1/neck/tip0/tip1/tip2）：等轴视角下每段顶面都是一片
  「斜片」，整体很碎；三段（肩 / 弹头主体 / 尖）就够。

【验证】gradle build 通过；jar hexalunar_calamity-1.0.0-r118.jar 已部署到 .minecraft/mods。
"""


def run(args):
    p = subprocess.run(args, cwd=ROOT, capture_output=True)
    return (p.returncode,
            p.stdout.decode('utf-8', 'replace') + p.stderr.decode('utf-8', 'replace'))


def main():
    missing = [f for f in FILES if not os.path.exists(os.path.join(ROOT, f))]
    present = [f for f in FILES if f not in missing]
    msg_path = os.path.join(BUILD, '_commit_r118.txt')
    with io.open(msg_path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(MSG)
    log = ['FILES %d（缺 %d）' % (len(present), len(missing))]
    if missing:
        log.append('不存在：' + str(missing))
    rc, out = run(['git', 'add', '--'] + present)
    log.append('git add rc=%d\n%s' % (rc, out))
    rc, out = run(['git', 'commit', '-F', msg_path])
    log.append('git commit rc=%d\n%s' % (rc, out))
    rc, out = run(['git', '--no-pager', 'log', '--oneline', '-2'])
    log.append('log:\n' + out)
    with io.open(os.path.join(BUILD, '_commit_out.txt'), 'w', encoding='utf-8',
                 newline='\n') as fh:
        fh.write('\n'.join(log) + '\n')
    print('done')


if __name__ == '__main__':
    main()
