# -*- coding: utf-8 -*-
"""r117：修「倍镜与枪身之间的间隙」（莫辛 + AWP 的镜座补长）。用法: python tools/_commit_r117.py
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
Q = 'mod/src/qresources/assets/hexalunar_calamity_q'

FILES = [
    'readme.md', 'mod/README.md', 'mod/build.gradle',
    'mod/tools/awp_v2.py',
    'mod/tools/mosin_m9130_v3.py',
    R + '/geo/awp.geo.json',
    R + '/geo/mosin.geo.json',
    R + '/textures/models/awp_geo.png',
    R + '/textures/models/awp_geo_glowmask.png',
    R + '/textures/models/mosin_geo.png',
    R + '/textures/models/mosin_geo_glowmask.png',
    Q + '/geo/awp.geo.json',
    Q + '/geo/mosin.geo.json',
    Q + '/textures/models/awp_geo.png',
    Q + '/textures/models/mosin_geo.png',
]

MSG = u"""fix(scope): r117 修「倍镜有明显间隙」——莫辛 / AWP 的镜座补到镜筒全长

用户游戏截图（莫辛-纳甘 M91/30，第一人称）标注：「倍镜有明显间隙修复它」

【根因】莫辛 v3 的镜座（sc_mnt）**只在装填口之后**（PORT_Z1…RCV_Z1）有一块，
镜筒在**机匣前半**那一大段下面是空的 —— 那里只留了一条矮导轨 sc_rail_f（顶到 2.34），
而镜筒底在 SCOPE_Y − SC_RO = 2.96 ⇒ 中间 0.62 的缝在玩家那个斜下视角里
**能穿过枪身看到背景**，就是用户圈出来的「明显间隙」。

【修法】
1. 莫辛（tools/mosin_m9130_v3.py）：补一段与机匣同宽的支架 sc_mnt_f
   （在装填口**之前**，从 RCV_TOP 一直托到镜筒底），原来那条矮导轨被它取代；
   装填口（PORT_Z0…PORT_Z1）上方**仍然开敞** —— 压弹那一发要从那儿垂直落进弹仓，不能堵。
2. AWP（tools/awp_v2.py）：镜座从「两个 0.44 宽的窄环座」改成**两段长座**
   （sc_mnt_f / sc_mnt_b，装填口前后各一段，x ±0.30、从导轨顶连到镜筒底）；
   顺带去掉「镜环」—— 镜筒现在是一根干净的等径筒 + 两段座（面数 1086 → 990）。
   装填口那段留空：弹匣里那一发要从那儿看得见，而机匣右壁的抛壳窗也在同一段 z 上。

【验证】
用 geo_texview.py --yaw 345 --pitch 18（玩家那个斜下视角）出图核对 —— 这个角度才看得见
「镜筒与枪身之间的缝」，侧视图看不出来；改完缝已经被支架填上。
两个生成器自检 0 失败；gradle build 通过；jar hexalunar_calamity-1.0.0-r117.jar 已部署。
"""


def run(args):
    p = subprocess.run(args, cwd=ROOT, capture_output=True)
    return (p.returncode,
            p.stdout.decode('utf-8', 'replace') + p.stderr.decode('utf-8', 'replace'))


def main():
    missing = [f for f in FILES if not os.path.exists(os.path.join(ROOT, f))]
    present = [f for f in FILES if f not in missing]
    msg_path = os.path.join(BUILD, '_commit_r117.txt')
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
