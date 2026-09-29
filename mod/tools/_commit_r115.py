# -*- coding: utf-8 -*-
"""r115 的「明确清单」提交：只 add 下面列表里的文件（不用 git add -A），
提交信息由本脚本写成 UTF-8 的 build/_commit_r115.txt 再 `git commit -F`。

用法::  python tools/_commit_r115.py [--dry]
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

J = 'mod/src/main/java/cn/blockforge/generated/hexalunarcalamity'
R = 'mod/src/main/resources/assets/hexalunar_calamity'
Q = 'mod/src/qresources/assets/hexalunar_calamity_q'

FILES = [
    # ---- 文档 / 构建
    'readme.md', 'mod/README.md', 'mod/build.gradle',
    # ---- Java（AWP 的世界抛壳口改到与模型同源的右侧抛壳窗）
    J + '/weapon/WeaponMount.java',
    # ---- 生成器（三把枪的空弹壳挪回右侧）
    'mod/tools/awp_v2.py',
    'mod/tools/m1_garand_v2.py',
    'mod/tools/mosin_m9130_v3.py',
    'mod/tools/_casing_probe.py',
    # ---- 重新生成的模型 / 贴图（主包）
    R + '/geo/awp.geo.json',
    R + '/geo/m1_garand.geo.json',
    R + '/geo/mosin.geo.json',
    R + '/textures/models/awp_geo.png',
    R + '/textures/models/awp_geo_glowmask.png',
    R + '/textures/models/m1_garand_geo.png',
    R + '/textures/models/m1_garand_geo_glowmask.png',
    R + '/textures/models/mosin_geo.png',
    R + '/textures/models/mosin_geo_glowmask.png',
    # ---- Q 弹版覆盖层（同步同样的模型与贴图）
    Q + '/geo/awp.geo.json',
    Q + '/geo/m1_garand.geo.json',
    Q + '/geo/mosin.geo.json',
    Q + '/textures/models/awp_geo.png',
    Q + '/textures/models/m1_garand_geo.png',
    Q + '/textures/models/mosin_geo.png',
]

MSG = u"""fix(casing): r115 修「抛壳位置跑到左侧」——AWP / M1 / 莫辛的空弹壳挪回机匣右侧抛壳窗

用户原话：「修复武器抛壳位置为右侧，不是左侧」

【根因】最近重建的三把枪（tools/awp_v2.py / tools/m1_garand_v2.py /
tools/mosin_m9130_v3.py）都把空弹壳（casing 骨骼的方块）放在**膛内中线 x=0**，
而更早的版本与 kar98k（casing pivot x = 0.30）都放在**机匣右侧的抛壳口**
—— 斜后上方看过去，弹壳就是从「枪身中间 / 偏左」冒出来的（用户看到的就是这个）。
上一次「抛壳改右侧」的修复（b39c2db）改的是**世界粒子方向**（删掉 ejectCasing 里
那句 .scale(-1)），当时提交信息还特意记录过「各枪 casing pivot 全在 +X
（awp 0.32 / kar98k 0.30 / m1 0.42 / mosin 0.62）」—— 这次是**模型端**又退回了中线。

【修法】三把枪统一：弹壳几何与骨骼 pivot 一起挪回右侧抛壳口
1. AWP（awp_v2.py）：机匣右壁在抛壳窗位置**留洞**（rcv_r 拆成 rcv_r_f / rcv_r_b，
   窗口 z 与顶部装填口一致 = −2.90…−2.10），空弹壳挪进右窗（CASE_X = 0.20、
   z −2.85…−2.25）；WeaponMount.AWP_EJECT 从 {0.90, 1.39, −0.60}（机匣右**外**侧、
   机匣**后**部，与模型里那颗弹壳对不上）改到与模型同源的 {0.30, 1.575, −2.50}
   ⇒ 世界里的黄铜壳也从右侧抛壳窗出来。
2. M1 加兰德（m1_garand_v2.py）：空弹壳挪到**右侧抛壳口**（x 0.10…0.30、
   z −1.65…−1.15，正对右壁缺口 z −1.75…−0.45）；M1_EJECT 本来就在右侧，不变。
3. 莫辛-纳甘（mosin_m9130_v3.py）：右壁同样开**抛壳窗**（rcv_r 拆两段，
   窗口 = 装填口 z −3.40…−2.25）＋ 空弹壳贴右内壁（x 0.00…0.26）；MOSIN_EJECT 不变。
4. 顺带修 awp_v2.py 自检的「悬空件」误报：touch() 先把每个轴按 [min, max] 归一化
   再比区间 —— 否则 (_sx*0.23, _sx*0.07) 这种**逆序**坐标在 _sx=−1 时会被当成空区间，
   mz_slotr0/r1、bp_foot_r 就被误报成「悬空的孤立方块」。AWP 自检现在 0 失败。
5. Q 弹版覆盖层的 awp / m1_garand / mosin 三套模型与贴图同步（否则 Q 版还是旧模型）。
6. 新工具 tools/_casing_probe.py：用**与游戏一致的第一人称变换链**把抛壳口 / 弹壳 /
   拉机柄投影到屏幕并打印像素 x —— 离线判定「左还是右」，不用开游戏
   （实测：模型 +X → 屏幕右侧；弹壳 bp=0.6 时屏幕 x≈1073，中心 731）。

验证：gradle build 通过（36s）；产物 hexalunar_calamity-1.0.0-r115.jar 已部署到
.minecraft/versions/1.20.1-Forge_47.4.23-2/mods。
"""


def run(args):
    p = subprocess.run(args, cwd=ROOT, capture_output=True)
    return (p.returncode,
            p.stdout.decode('utf-8', 'replace') + p.stderr.decode('utf-8', 'replace'))


def main():
    dry = '--dry' in sys.argv
    missing = [f for f in FILES if not os.path.exists(os.path.join(ROOT, f))]
    present = [f for f in FILES if f not in missing]
    msg_path = os.path.join(BUILD, '_commit_r115.txt')
    with io.open(msg_path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(MSG)

    log = ['FILES %d（缺 %d）' % (len(present), len(missing))]
    if missing:
        log.append('不存在：')
        log += ['  ' + m for m in missing]
    if dry:
        log.append('--dry：只检查清单，不 add / commit')
    else:
        rc, out = run(['git', 'add', '--'] + present)
        log.append('git add rc=%d\n%s' % (rc, out))
        rc, out = run(['git', 'commit', '-F', msg_path])
        log.append('git commit rc=%d\n%s' % (rc, out))
        rc, out = run(['git', '--no-pager', 'log', '--oneline', '-2'])
        log.append('log:\n' + out)

    text = '\n'.join(log)
    with io.open(os.path.join(BUILD, '_commit_out.txt'), 'w', encoding='utf-8',
                 newline='\n') as fh:
        fh.write(text + '\n')
    print('done（详见 build/_commit_out.txt）')


if __name__ == '__main__':
    main()
