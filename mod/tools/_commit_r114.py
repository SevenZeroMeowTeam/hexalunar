# -*- coding: utf-8 -*-
"""r114 的「明确清单」提交：只 add 下面列表里的文件（不用 git add -A），
提交信息由本脚本写成 UTF-8 的 build/_commit_r114.txt 再 `git commit -F`。
（PowerShell 直接传中文给 git 会按 GBK 存成乱码，终端里中文输出也会乱码 ⇒ 一律落文件。）

用法::  python tools/_commit_r114.py [--dry]
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
    'readme.md', 'mod/README.md', 'mod/build.gradle', 'Agent.md', 'mod/Agent.md',
    # ---- Java
    J + '/client/AkmGeoModel.java',
    J + '/client/AwpGeoModel.java',
    J + '/client/ClientWeaponInput.java',
    J + '/client/M1GarandGeoModel.java',
    J + '/client/ModClient.java',
    J + '/client/QChibi.java',
    J + '/client/QChibiSkeletonRenderer.java',
    J + '/client/QChibiZombieModel.java',
    J + '/client/QChibiZombieRenderer.java',
    J + '/registry/ModItems.java',
    J + '/weapon/M1GarandItem.java',
    J + '/weapon/WeaponMount.java',
    # ---- 资源（主包）
    R + '/animations/awp.animation.json',
    R + '/animations/m1_garand.animation.json',
    R + '/animations/mosin.animation.json',
    R + '/geo/awp.geo.json',
    R + '/geo/m1_garand.geo.json',
    R + '/geo/mosin.geo.json',
    R + '/lang/en_us.json',
    R + '/lang/zh_cn.json',
    R + '/textures/models/awp_geo.png',
    R + '/textures/models/awp_geo_glowmask.png',
    R + '/textures/models/m1_garand_geo.png',
    R + '/textures/models/m1_garand_geo_glowmask.png',
    R + '/textures/models/mosin_geo.png',
    R + '/textures/models/mosin_geo_glowmask.png',
    # ---- Q 弹版覆盖层
    Q + '/geo/akm.geo.json',
    Q + '/geo/awp.geo.json',
    Q + '/geo/compound_bow.geo.json',
    Q + '/geo/crossbow_geo.geo.json',
    Q + '/geo/flashbang.geo.json',
    Q + '/geo/kar98k.geo.json',
    Q + '/geo/m1_garand.geo.json',
    Q + '/geo/mosin.geo.json',
    Q + '/geo/mud.geo.json',
    Q + '/textures/entity/q_chibi_skeleton.png',
    Q + '/textures/models/awp_geo.png',
    Q + '/textures/models/awp_geo_glowmask.png',
    Q + '/textures/models/compound_bow_geo.png',
    Q + '/textures/models/crossbow_geo.png',
    Q + '/textures/models/flashbang_geo.png',
    Q + '/textures/models/kar98k_geo.png',
    Q + '/textures/models/m1_garand_geo.png',
    Q + '/textures/models/mosin_geo.png',
    Q + '/textures/models/mud_geo.png',
    # ---- 生成器 / 校核脚本（readme 里点名的那些）
    'mod/tools/awp_v2.py',
    'mod/tools/m1_garand_gen.py',
    'mod/tools/m1_garand_v2.py',
    'mod/tools/mosin_m9130_gen.py',
    'mod/tools/mosin_m9130_v2.py',
    'mod/tools/mosin_m9130_v3.py',
    'mod/tools/q_akm_gen.py',
    'mod/tools/qgen.py',
    'mod/tools/qjar_check.py',
    'mod/tools/q_chibi_skeleton_tex.py',
    'mod/tools/geo2bbmodel.py',
    'mod/tools/bbanim.py',
    'mod/tools/_ads_check.py',
    'mod/tools/_awp2check.py',
    'mod/tools/_awpviews.py',
    'mod/tools/_awpshot_fix.py',
    'mod/tools/_ai_awp_times.py',
    'mod/tools/_m1check.py',
    'mod/tools/_m1_probe.py',
    'mod/tools/_m9130check.py',
    'mod/tools/_mos3check.py',
    'mod/tools/_mosviews.py',
    'mod/tools/_mosshot_eye.py',
    'mod/tools/_mosshot_tg.py',
    'mod/tools/_zoomshot.py',
    'mod/tools/_tacz_anim.py',
    'mod/tools/_tacz_animlist.py',
    'mod/tools/_tacz_cat.py',
    'mod/tools/_tacz_find.py',
    'mod/tools/_tacz_probe2.py',
    # ---- 自产 Blockbench 工程文件（参考包 / 源音频不提交）
    'mod/模型/hexalunar_m1_garand.bbmodel',
    'mod/模型/hexalunar_m1_garand-1.bbmodel',
    'mod/模型/hexalunar_m1_garand-2.bbmodel',
    'mod/模型/hexalunar_mosin_m9130.bbmodel',
]

MSG = u"""feat(awp): r114 AWP 整体重建（模型 v2）+ 拉栓/持枪照 TaCZ 精密国际 ai_awp

用户原话：「根据图片用blockbench建模，枪管为圆形空洞枪管，弹匣可以看见子弹，
拉完栓看不见弹匣里面子弹，瞄准镜也为圆型空心内部透明玻璃和十字线构成，枪身
可以使用方块构建或其他结构使其看起来更真实，有明显的换弹，图片为awp，栓动
狙击枪，打一下拉一下栓把空弹壳带出抛出，带入新的子弹推入发射，做完替换原有
的awp，awp有弹夹，套用tacz步枪的持枪动画，注：tacz中没有awp，套用tacz的
精密国际awm的手持动画」

AWP（r114，模型 v2）
- 新生成器 tools/awp_v2.py → 18 骨骼 / 180 方块 / 512² 逐面 UV
  · 枪管 = 一整根八棱空洞壁（外径全程 0.250 / 内孔 0.125 + 内壁 8 段膛线 +
    膛底黑堵头 + 八棱制退器两道泄气槽）：枪口正视是一圈管壁 + 一个黑洞
  · 瞄准镜 = 空心镜筒（一根直筒 + 变倍环 + 两宽镜环）+ 前后整片透明圆镜片
    （背景 alpha = 0、方角直接丢弃 ⇒ 是圆玻璃不是方块），目镜刻十字分划 +
    中心红点；镜座改成坐在机匣后桥上的一整块实心块
  · 弹匣里 5 发看得见的子弹：round_in（最上一发）+ mag_r1..mag_r4
  · 自检（tools/_awp2check.py → build/_awp2check.txt）：枪口↔膛底整条轴线是
    空的 / 镜筒内通 + 镜片整片透明含十字线 / 5 发都在匣内不穿底 / 闭锁被枪机
    体盖住抛壳口、后拉 1.90 后让开 → 全 OK
- Java 适配（client/AwpGeoModel）：旧的 magazine_rounds（一根骨骼 3 个方块）
  作废，改成按 NBT 余弹逐根控 round_in / mag_r1..mag_r4 ——
  闭锁时全藏（枪机体盖住装填口，外面本来就看不见）→ 拉栓时露出来（托弹板把
  最上一发顶到弹匣口）→ 枪机回位把它推进膛、推到底就从弹匣里消失 ⇒ 正好是
  用户要的「弹匣可以看见子弹 / 拉完栓看不见」；打一发少一发跟着 HlcMag 走
- 动作数值照 TaCZ 的精密国际 ai_awp（TaCZ 没有单独的 awp；它的
  ai_awp_display.json 写着 use_default_animation: "rifle"）：
  拉机柄 62°（TaCZ bolt_rotate 60°）、整枪向右侧倾 11.9° + 微抬 4.6° + 微沉
  0.40（TaCZ bolt 的 root）、枪机后退 1.90（新几何自检扫出）、换弹弹匣 45°
  翻转脱出（TaCZ 到 −131°）、后坐俯仰 6.0（TaCZ shoot 7.94°）
- 持枪动画 = TaCZ 通用步枪 rifle_default：新增 WeaponMount.awpHoldPose（与
  m1HoldPose 同一份数值）——idle 呼吸 / 走路轻摆 / 冲刺时枪压低并转到射手右侧；
  抵肩时全部收掉；枪口与抛壳点的世界坐标走同一份姿态（awpHoldPoint），
  跑动时枪口焰与弹道不会与枪身脱开
- Q 弹版覆盖层同步（qresources 的 awp geo / 贴图 / glowmask）

同批入库（r109~r113 一直未提交的部分）
- M1 加兰德整体重建（tools/m1_garand_v2.py：空心圆管枪管 + 空心觇孔环 +
  8 发可见漏夹、弹夹盖平行抬起、抛壳走盖板让出的口子）
- 新武器：Kar98k 栓动步枪、莫辛-纳甘 M91/30（tools/mosin_m9130_gen.py 系列）
- Q 弹版：QChibi 骨骼僵尸（QChibi / QChibiSkeletonRenderer / qgen /
  q_chibi_skeleton_tex + qresources 覆盖层）
- 文档：readme.md / mod/README.md（AWP r114 段 + 更新日志）、版本号 1.0.0-r114
- 新工具：tools/_ai_awp_times.py（看 TaCZ ai_awp 某段动画的关键帧/长度）、
  tools/_awpviews.py（五视图出图）、tools/_awp2check.py（生成器一键自检）
"""


def run(args):
    p = subprocess.run(args, cwd=ROOT, capture_output=True)
    return (p.returncode,
            p.stdout.decode('utf-8', 'replace') + p.stderr.decode('utf-8', 'replace'))


def main():
    dry = '--dry' in sys.argv
    missing = [f for f in FILES if not os.path.exists(os.path.join(ROOT, f))]
    present = [f for f in FILES if f not in missing]
    msg_path = os.path.join(BUILD, '_commit_r114.txt')
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
        rc, out = run(['git', '--no-pager', 'log', '--oneline', '-3'])
        log.append('log:\n' + out)

    text = '\n'.join(log)
    with io.open(os.path.join(BUILD, '_commit_out.txt'), 'w', encoding='utf-8',
                 newline='\n') as fh:
        fh.write(text + '\n')
    print('done（详见 build/_commit_out.txt）')


if __name__ == '__main__':
    main()
