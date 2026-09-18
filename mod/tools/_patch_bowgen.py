#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一次性脚本：把 bow_gen.py 的 write_anims 换成 SuperbWarfare BOCEK 规范版本。

动画名统一 animation.compound_bow.<state>，播放类型用 Bedrock 的 loop 语义：
  idle / run / run_fast -> true
  pull                  -> "hold_on_last_frame"（拉满保持，Java 侧用 thenPlayAndHold）
  fire / reload         -> false（play_once）
并加 move（跑动摆动，包住弓身）与 camera（无方块空骨骼，抖第一人称视角）。
"""
import io

P = 'tools/bow_gen.py'
NEW = '''def write_anims(_delta):
    """动画配置照 SuperbWarfare 的 BOCEK 复合弓规范（同名同播放类型）：
      animation.compound_bow.idle / run / run_fast  loop
      animation.compound_bow.pull                   hold_on_last_frame（拉满保持）
      animation.compound_bow.fire / reload          play_once
    结构必须是 骨骼 → rotation|position → 时间 → post|vector（GeckoLib 按通道名取）。
    """
    P = 'animation.compound_bow.'
    idle = {'loop': True, 'animation_length': 1.8667, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.93, [0.35, 0, 0.25]), (1.87, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (0.93, [-0.3, 0, -0.2]), (1.87, [0, 0, 0])])},
        'arrow': {'position': _kfv([(0.0, [0, -40, 0])])},
    }}
    run = {'loop': True, 'animation_length': 0.8333, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.21, [2.6, 0, -0.8]), (0.42, [0, 0, 0]),
                                  (0.63, [-2.2, 0, 0.6]), (0.83, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.21, [0, -0.5, 0]), (0.42, [0, 0, 0]),
                                   (0.63, [0, 0.5, 0]), (0.83, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (0.42, [1.2, 0, 1.6]), (0.83, [0, 0, 0])])},
        'arrow': {'position': _kfv([(0.0, [0, -40, 0])])},
    }}
    run_fast = {'loop': True, 'animation_length': 0.6, 'bones': {
        'move': {'rotation': _kf([(0.0, [0, 0, 0]), (0.15, [4.0, 0, -1.4]), (0.30, [0, 0, 0]),
                                  (0.45, [-3.4, 0, 1.0]), (0.60, [0, 0, 0])]),
                 'position': _kfv([(0.0, [0, 0, 0]), (0.15, [0, -0.9, 0]), (0.30, [0, 0, 0]),
                                   (0.45, [0, 0.9, 0]), (0.60, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (0.30, [1.8, 0, 2.4]), (0.60, [0, 0, 0])])},
        'arrow': {'position': _kfv([(0.0, [0, -40, 0])])},
    }}
    pull = {'loop': 'hold_on_last_frame', 'animation_length': 1.0, 'bones': {
        'string_upper': {'rotation': _kf([(0.0, [0, 0, 0]), (0.25, [2.0, 0, 0]), (1.0, [-PHI, 0, 0])])},
        'string_lower': {'rotation': _kf([(0.0, [0, 0, 0]), (0.25, [-2.0, 0, 0]), (1.0, [PHI, 0, 0])])},
        'nock': {'position': _kfv([(0.0, [0, 0, 0]), (1.0, [0, 0, DRAW_DZ])])},
        'arrow': {'position': _kfv([(0.0, [0, -40, 0]), (0.22, [0, 0, 0]), (1.0, [0, 0, DRAW_DZ])])},
        'cam_upper': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [-38, 0, 0])])},
        'cam_lower': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [-38, 0, 0])])},
        'upper_limb': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [-2.6, 0, 0])])},
        'lower_limb': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [2.6, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [0.8, 0, 0])])},
        'move': {'position': _kfv([(0.0, [0, 0, 0]), (1.0, [0, 0, -0.6])])},
        'camera': {'rotation': _kf([(0.0, [0, 0, 0]), (1.0, [-1.6, 0.8, 0])])},
    }}
    fire = {'loop': False, 'animation_length': 0.4, 'bones': {
        'string_upper': {'rotation': _kf([(0.0, [-PHI, 0, 0]), (0.12, [4.2, 0, 0]), (0.4, [0, 0, 0])])},
        'string_lower': {'rotation': _kf([(0.0, [PHI, 0, 0]), (0.12, [-4.2, 0, 0]), (0.4, [0, 0, 0])])},
        'nock': {'position': _kfv([(0.0, [0, 0, DRAW_DZ]), (0.12, [0, 0, -0.6]), (0.4, [0, 0, 0])])},
        'arrow': {'position': _kfv([(0.0, [0, 0, DRAW_DZ]), (0.1, [0, 0, -10]), (0.4, [0, -40, 0])])},
        'cam_upper': {'rotation': _kf([(0.0, [-38, 0, 0]), (0.4, [0, 0, 0])])},
        'cam_lower': {'rotation': _kf([(0.0, [-38, 0, 0]), (0.4, [0, 0, 0])])},
        'upper_limb': {'rotation': _kf([(0.0, [-2.6, 0, 0]), (0.16, [1.6, 0, 0]), (0.4, [0, 0, 0])])},
        'lower_limb': {'rotation': _kf([(0.0, [2.6, 0, 0]), (0.16, [-1.6, 0, 0]), (0.4, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0.8, 0, 0]), (0.1, [-1.4, 0, 0]), (0.4, [0, 0, 0])])},
        'move': {'position': _kfv([(0.0, [0, 0, -0.6]), (0.1, [0, 0, 0.9]), (0.4, [0, 0, 0])])},
        'camera': {'rotation': _kf([(0.0, [-1.6, 0.8, 0]), (0.1, [-4.2, -0.6, 0]), (0.4, [0, 0, 0])])},
    }}
    reload_ = {'loop': False, 'animation_length': 0.35, 'bones': {
        'arrow': {'position': _kfv([(0.0, [0, -40, 7]), (0.18, [0, 0, 7]), (0.28, [0, 0, 0]),
                                    (0.35, [0, 0, 0])])},
        'body': {'rotation': _kf([(0.0, [0, 0, 0]), (0.18, [0, 0, -2.2]), (0.35, [0, 0, 0])])},
        'string_upper': {'rotation': _kf([(0.0, [0, 0, 0]), (0.22, [3.4, 0, 0]), (0.35, [0, 0, 0])])},
        'string_lower': {'rotation': _kf([(0.0, [0, 0, 0]), (0.22, [-3.4, 0, 0]), (0.35, [0, 0, 0])])},
        'nock': {'position': _kfv([(0.0, [0, 0, 0]), (0.22, [0, 0, 0.8]), (0.35, [0, 0, 0])])},
    }}
    anims = {'format_version': '1.8.0', 'animations': {
        P + 'idle': idle, P + 'run': run, P + 'run_fast': run_fast,
        P + 'pull': pull, P + 'fire': fire, P + 'reload': reload_}}
    os.makedirs(os.path.dirname(ANIM_OUT), exist_ok=True)
    with open(ANIM_OUT, 'w', encoding='utf-8') as fh:
        json.dump(anims, fh, ensure_ascii=False, indent=1)
    print('动画 -> %s（BOCEK 规范：idle/run/run_fast[loop]、pull[hold_on_last_frame]、'
          'fire/reload[play_once]；φ=%.2f° 弦长 %.2f）' % (ANIM_OUT, PHI, SEG_LEN))
    return 0


'''

s = io.open(P, encoding='utf-8').read()
i = s.index('def write_anims')
j = s.index('def write_bbmodel')
io.open(P, 'w', encoding='utf-8').write(s[:i] + NEW + s[j:])
print('write_anims 已替换为 BOCEK 规范版本')
