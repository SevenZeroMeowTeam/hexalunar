# -*- coding: utf-8 -*-
"""修复合弓「准星在箭上方」。

根因：ClientEvents.applyBowCamera 每帧把模型里 camera 空骨骼的角度叠到视角上：
    event.setPitch(pitch - bone.getRotX())   event.setYaw(yaw + bone.getRotY())
而放箭走的是玩家原始朝向（CompoundBowItem.shoot -> shootFromRotation(player, xRot, yRot)）。
于是在 pull 动画里 camera 骨骼的 **稳定** 偏移 [-1.6, 0.8, 0] 会让准星与弹道永久差
1.6° 俯仰 + 0.8° 偏航 —— 25 格外就偏 ~0.7 格，正是"准星在箭上方"。

修法：稳定态只保留 **绕视线轴的横滚**（roll 不改变正前方，所以准星仍精确指向弹道，
同时保留"拉弦时镜头被拧一下"的手感）；pitch/yaw 只在放箭瞬间的后坐里给。

（同理 AKM 的 idle 只有 0.3° 摆动、fire/bolt/reload 都是一次性后坐，不影响瞄准，不动。）
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                 'animations', 'compound_bow.animation.json')

d = json.load(io.open(P, encoding='utf-8'))
anim = d['animations']

# pull：满弦稳定态只给横滚
pull = anim['animation.compound_bow.pull']['bones']
pull['camera'] = {'rotation': {'0': {'post': [0, 0, 0]},
                               '1': {'post': [0, 0, 1.5]}}}

# fire：从横滚 1.5 起步，后坐瞬间给一点俯仰（此时箭已经出膛，不影响弹道）
fire = anim['animation.compound_bow.fire']['bones']
fire['camera'] = {'rotation': {'0': {'post': [0, 0, 1.5]},
                               '0.1': {'post': [-4.2, -0.6, 1.5]},
                               '0.4': {'post': [0, 0, 0]}}}

json.dump(d, io.open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('patched', os.path.relpath(P, ROOT))
print('  pull.camera ->', json.dumps(pull['camera'], ensure_ascii=False))
print('  fire.camera ->', json.dumps(fire['camera'], ensure_ascii=False))
