# -*- coding: utf-8 -*-
"""r116 的「明确清单」提交（据用户游戏截图：抛壳回右侧 + 倍镜去分叉）。

用法::  python tools/_commit_r116.py [--dry]
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
    'readme.md', 'mod/README.md', 'mod/build.gradle',
    J + '/weapon/WeaponMount.java',
    'mod/tools/awp_v2.py',
    R + '/geo/awp.geo.json',
    R + '/textures/models/awp_geo.png',
    R + '/textures/models/awp_geo_glowmask.png',
    Q + '/geo/awp.geo.json',
    Q + '/textures/models/awp_geo.png',
]

MSG = u"""fix(awp): r116 据游戏截图修两处 —— 抛壳回到枪身右侧 + 倍镜不再「分叉」

用户游戏内截图（第一人称，AWP）标注：
  「倍镜看起来有明显分叉」
  「所有武器自动抛壳为绿色箭头位置，抛壳方向应该为蓝色箭头位置」

【一、抛壳特效回到枪身右侧】
r115 把 WeaponMount.AWP_EJECT 的 x 从 0.90 压到 **0.30**（几乎回到枪身中线）——
本意是「与模型里那颗弹壳同源」，但屏幕上看着还是从枪身中间冒出来，用户再次反馈。
现在五把枪的抛壳点统一取「机匣半宽再往外一点」（模型 +X = 射手右侧，这条从 r107 起就对）：
  AKM 0.95（原值保持）/ AWP 0.30 → **0.78** / Kar98k 0.55 → **0.80** /
  莫辛 0.62 → **0.90** / M1 0.33 → **0.85**
模型内的空壳位置（r115 已挪到机匣右侧抛壳窗）保持不动。

【二、倍镜不再「分叉」】（tools/awp_v2.py）
镜筒原来有四段不同外径：物镜 SC_RO+0.05 / 变倍环 +0.03 / 目镜 +0.03 / **镜环 +0.07**
⇒ 四个台阶，从玩家那个「斜下看枪」的视角就是「筒上又叠了一层」（截图里那个分叉）。
现在整根筒的外径统一（最粗最细只差 0.02），镜环也几乎与筒齐平（只靠颜色区分）；
镜座从「两根细立柱」加宽成**整块座**（x ±0.30 / z 0.44）—— 筒与机匣之间是实在的座子。

【验证】
- 用 tools/geo_texview.py --yaw 345 --pitch 18（= 玩家第一人称那个斜下视角）逐轮出图核对：
  这个角度才看得见镜筒的层叠，侧视图看不出来；改完是干干净净一根等径筒。
- awp_v2.py 自检 0 失败；gradle build 通过；jar hexalunar_calamity-1.0.0-r116.jar 已部署。
"""


def run(args):
    p = subprocess.run(args, cwd=ROOT, capture_output=True)
    return (p.returncode,
            p.stdout.decode('utf-8', 'replace') + p.stderr.decode('utf-8', 'replace'))


def main():
    dry = '--dry' in sys.argv
    missing = [f for f in FILES if not os.path.exists(os.path.join(ROOT, f))]
    present = [f for f in FILES if f not in missing]
    msg_path = os.path.join(BUILD, '_commit_r116.txt')
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
