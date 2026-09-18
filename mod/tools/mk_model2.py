#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 tools/bb_model_v3.js —— 按 模型/十字弩.bbmodel 的比例重做（宽扁弓弧 + 短机身）。

实测原模型（去掉 -30 度偏航后的真实比例）：
  弓臂展开 ≈ 16.8，机身自弓平面向后 ≈ 8.3（总长 ≈ 16.5），总高 ≈ 4.65
  即 span : length : height ≈ 1 : 0.98 : 0.277
本模型取 span 22.8 / length 18.1 / height 7.2（比例 1 : 0.79 : 0.316），
机身比原模型略长一点，方便放弹匣与倍镜。
"""
import json
import os

CUBES = []


def cube(name, bone, f, t, mat, fx=None, rot=None, pivot=None, mirror=False):
    rec = {'n': name, 'b': bone, 'f': [round(v, 2) for v in f], 't': [round(v, 2) for v in t], 'm': mat}
    if fx:
        rec['fx'] = fx
    if rot:
        rec['r'] = rot
        rec['p'] = pivot
    CUBES.append(rec)
    if mirror:
        mrec = {'n': name + '_r', 'b': bone.replace('_l', '_r'),
                'f': [-t[0], f[1], f[2]], 't': [-f[0], t[1], t[2]], 'm': mat}
        if fx:
            mrec['fx'] = fx
        if rot:
            mrec['r'] = [rot[0], -rot[1], -rot[2]]
            mrec['p'] = [-pivot[0], pivot[1], pivot[2]]
        CUBES.append(mrec)


def teeth(name, bone, x0, x1, y0, y1, z0, z1, pitch, width, mat):
    z, i = z0, 0
    while z + width <= z1:
        cube('%s_%d' % (name, i), bone, [x0, y0, z], [x1, y1, z + width], mat)
        z += pitch
        i += 1


def build():
    B = 'body'

    cube('receiver', B, [-1.5, -0.4, -0.6], [1.5, 1.3, 6.2], 'body_main', {'east': 'panel', 'west': 'panel', 'up': 'receiverTop'})
    cube('recv_side_l', B, [-1.65, 0.1, 0.4], [-1.5, 1.05, 5.6], 'body_hi', mirror=True)
    cube('recv_bottom', B, [-1.35, -0.7, 0.2], [1.35, -0.4, 5.9], 'body_dark')
    cube('recv_bevel', B, [-0.95, 1.3, -0.4], [0.95, 1.52, 6.0], 'body_hi')
    cube('bolt_channel', B, [-0.7, 1.3, -3.0], [0.7, 1.42, 6.0], 'body_dark')

    cube('rail_l', B, [-1.28, 1.42, -2.6], [-0.74, 1.72, 6.0], 'metal', {'up': 'railTop'}, mirror=True)
    teeth('rail_t', B, -1.26, -0.76, 1.72, 1.88, -2.5, 5.9, 1.4, 0.9, 'metal')
    teeth('rail_tr', B, 0.76, 1.26, 1.72, 1.88, -2.5, 5.9, 1.4, 0.9, 'metal')

    cube('eject_port', B, [-1.52, 0.35, 1.9], [1.52, 1.15, 4.0], 'body_dark')
    cube('charge_handle', B, [1.51, 0.4, 1.6], [2.0, 1.05, 2.6], 'metal')
    cube('charge_knob', B, [2.0, 0.5, 1.7], [2.4, 0.95, 2.5], 'steel')

    cube('riser', B, [-1.9, -0.5, -3.1], [1.9, 1.8, -0.6], 'body_main', {'east': 'riser', 'west': 'riser', 'north': 'riserN'})
    cube('riser_bevel', B, [-1.5, 1.8, -2.85], [1.5, 2.2, -0.8], 'body_hi')
    cube('riser_side_l', B, [-2.05, 0.1, -2.85], [-1.9, 1.6, -0.9], 'body_hi', mirror=True)
    cube('limb_pocket_l', B, [1.4, 0.7, -3.0], [2.4, 2.5, -0.7], 'metal', mirror=True)
    cube('limb_cap_l', B, [1.65, 1.1, -3.3], [2.2, 2.2, -3.0], 'steel', mirror=True)
    cube('front_grip', B, [-1.15, -1.7, -1.4], [1.15, 0.2, 0.4], 'rubber')
    cube('fg_stop', B, [-1.25, -2.1, -1.5], [1.25, -1.5, 0.5], 'body_dark')

    cube('scope_mount_l', B, [-1.35, 1.42, 0.2], [-0.85, 2.4, 1.4], 'metal', mirror=True)
    cube('scope_mount2_l', B, [-1.35, 1.42, 4.2], [-0.85, 2.4, 5.4], 'metal', mirror=True)
    cube('scope_ring_f', 'scope', [-1.4, 2.15, -0.2], [1.4, 3.45, 1.6], 'metal')
    cube('scope_ring_r', 'scope', [-1.4, 2.15, 4.0], [1.4, 3.45, 5.8], 'metal')
    cube('scope_tube', 'scope', [-1.15, 2.35, 0.0], [1.15, 3.25, 5.6], 'scope_body', {'east': 'tube', 'west': 'tube'})
    cube('scope_obj', 'scope', [-1.55, 2.0, 5.6], [1.55, 3.6, 6.6], 'metal')
    cube('scope_glass', 'scope', [-1.3, 2.25, 6.6], [1.3, 3.35, 6.85], 'glass', {'north': 'glassFx'})
    cube('scope_eye', 'scope', [-1.45, 2.1, -1.0], [1.45, 3.5, -0.2], 'metal')
    cube('scope_eye_glass', 'scope', [-1.2, 2.3, -1.25], [1.2, 3.3, -1.05], 'glass_dk')
    cube('turret_up', 'scope', [-0.5, 3.45, 2.3], [0.5, 4.05, 3.4], 'metal')
    cube('turret_up_cap', 'scope', [-0.32, 4.05, 2.45], [0.32, 4.25, 3.25], 'steel')
    cube('turret_side', 'scope', [1.15, 2.45, 2.3], [1.85, 3.1, 3.4], 'metal')

    cube('stock_tube', 'stock', [-1.3, 0.2, 6.2], [1.3, 1.6, 9.0], 'body_main', {'east': 'stock', 'west': 'stock'})
    cube('stock_tube_l', 'stock', [-1.45, 0.55, 6.3], [-1.3, 1.35, 8.9], 'body_hi', mirror=True)
    cube('stock_upper', 'stock', [-1.1, 1.6, 6.3], [1.1, 2.3, 9.2], 'body_main', rot=[-3, 0, 0], pivot=[0, 1.6, 6.3])
    cube('stock_cheek', 'stock', [-0.85, 2.3, 6.8], [0.85, 2.72, 9.3], 'rubber', rot=[-3, 0, 0], pivot=[0, 1.6, 6.3])
    cube('stock_lower', 'stock', [-1.05, -0.5, 6.4], [1.05, 0.45, 9.1], 'body_dark', rot=[-2, 0, 0], pivot=[0, 0.45, 6.4])
    cube('stock_strut', 'stock', [-0.95, 0.35, 8.4], [0.95, 1.15, 9.1], 'body_dark')
    cube('buttpad', 'stock', [-1.2, -1.2, 9.1], [1.2, 3.0, 10.0], 'rubber', rot=[-4, 0, 0], pivot=[0, 0.45, 9.1])
    cube('buttpad_l', 'stock', [-1.35, -1.05, 9.2], [-1.2, 2.85, 9.9], 'body_dark', rot=[-4, 0, 0], pivot=[0, 0.45, 9.1], mirror=True)
    cube('sling_loop', 'stock', [-0.28, -1.5, 7.4], [0.28, -1.05, 8.4], 'metal')

    cube('grip_core', 'grip', [-1.1, -2.5, 4.6], [1.1, -0.5, 6.2], 'rubber', {'east': 'grip', 'west': 'grip'},
         rot=[16, 0, 0], pivot=[0, -0.5, 5.6])
    cube('grip_face', 'grip', [-0.88, -2.1, 4.2], [0.88, -1.0, 4.6], 'body_dark', rot=[16, 0, 0], pivot=[0, -0.5, 5.6])
    cube('grip_heel', 'grip', [-1.15, -0.5, 6.0], [1.15, 0.35, 6.7], 'body_main')
    cube('grip_base', 'grip', [-1.25, -2.9, 4.5], [1.25, -2.3, 5.9], 'rubber', rot=[16, 0, 0], pivot=[0, -0.5, 5.6])

    cube('guard_front', 'body', [-0.9, -2.2, 2.9], [0.9, -1.7, 3.4], 'body_dark')
    cube('guard_bottom', 'body', [-0.9, -2.2, 2.9], [0.9, -1.9, 5.2], 'body_dark')

    cube('trigger_blade', 'trigger', [-0.28, -2.0, 3.9], [0.28, -0.7, 4.4], 'metal')
    cube('trigger_pin', 'trigger', [-0.45, -0.8, 4.5], [0.45, -0.45, 5.2], 'steel')

    cube('mag_body', 'mag', [-1.1, -2.2, 0.6], [1.1, -0.4, 3.0], 'body_dark',
         {'east': 'mag', 'west': 'mag', 'north': 'magN'}, rot=[-7, 0, 0], pivot=[0, -0.4, 3.0])
    cube('mag_rib0', 'mag', [-1.2, -1.6, 0.45], [1.2, -1.3, 2.9], 'body_hi', rot=[-7, 0, 0], pivot=[0, -0.4, 3.0])
    cube('mag_rib1', 'mag', [-1.2, -1.0, 0.55], [1.2, -0.7, 2.9], 'body_hi', rot=[-7, 0, 0], pivot=[0, -0.4, 3.0])
    cube('mag_floor', 'mag', [-1.2, -2.5, 0.25], [1.2, -2.1, 2.7], 'metal', rot=[-7, 0, 0], pivot=[0, -0.4, 3.0])
    cube('mag_release', 'mag', [-0.45, -2.3, 2.7], [0.45, -1.9, 3.3], 'steel', rot=[-7, 0, 0], pivot=[0, -0.4, 3.0])

    cube('bolt_shaft', 'bolt', [-0.26, 1.32, -5.6], [0.26, 1.68, 1.4], 'bolt', {'east': 'bolt', 'west': 'bolt'})
    cube('bolt_nock', 'bolt', [-0.4, 1.32, 1.4], [0.4, 1.68, 2.0], 'accent')
    cube('bolt_head', 'bolt', [-0.48, 1.24, -7.0], [0.48, 1.76, -5.6], 'steel')
    cube('bolt_fletch_l', 'bolt', [-1.15, 1.18, -0.4], [0.0, 1.82, 1.3], 'bolt', mirror=True)
    cube('bolt_fletch_u', 'bolt', [-0.22, 1.68, -0.4], [0.22, 2.44, 1.3], 'bolt')

    L = 'limb_l'
    cube('limb_root', L, [1.7, 1.15, -2.9], [3.4, 2.55, -0.9], 'limb_hi', {'north': 'limb', 'south': 'limb'}, mirror=True)
    cube('limb_seg1', L, [3.2, 1.3, -2.75], [6.6, 2.38, -1.05], 'limb', {'north': 'limb', 'south': 'limb'},
         rot=[0, -9, 0], pivot=[2.2, 1.9, -1.9], mirror=True)
    cube('limb_seg2', L, [6.3, 1.44, -2.5], [9.0, 2.28, -1.05], 'limb', {'north': 'limb', 'south': 'limb'},
         rot=[0, -18, 0], pivot=[2.2, 1.9, -1.9], mirror=True)
    cube('limb_tip', L, [8.7, 1.56, -2.2], [10.2, 2.2, -1.15], 'limb_hi',
         rot=[0, -26, 0], pivot=[2.2, 1.9, -1.9], mirror=True)
    cube('limb_ridge', L, [3.4, 2.35, -2.5], [8.8, 2.62, -1.4], 'limb_hi',
         rot=[0, -14, 0], pivot=[2.2, 1.9, -1.9], mirror=True)
    cube('limb_web_l', L, [4.0, 1.55, -2.15], [7.2, 2.2, -1.5], 'body_dark',
         rot=[0, -12, 0], pivot=[2.2, 1.9, -1.9], mirror=True)

    for i in range(5):
        y0 = 0.95 + i * 0.38
        yc = y0 + 0.19
        dy = abs(yc - 1.9)
        half = (max(1.05 * 1.05 - dy * dy, 0.05)) ** 0.5
        cube('cam_%d' % i, L, [10.3 - half, y0, -2.4], [10.3 + half, y0 + 0.38, -0.6], 'cam',
             {'east': 'cam', 'west': 'cam'}, rot=[0, -26, 0], pivot=[2.2, 1.9, -1.9], mirror=True)
    cube('cam_hub', L, [9.8, 1.68, -2.5], [10.8, 2.12, -0.5], 'steel',
         rot=[0, -26, 0], pivot=[2.2, 1.9, -1.9], mirror=True)
    cube('cam_guide', L, [10.1, 0.95, -0.7], [11.1, 2.85, -0.15], 'metal',
         rot=[0, -26, 0], pivot=[2.2, 1.9, -1.9], mirror=True)

    cube('string_l', 'string_l', [0, 1.76, -1.0], [10.8, 2.04, -0.6], 'string', mirror=True)
    cube('string_l_c', 'string_l', [0, 1.0, -0.95], [10.8, 1.15, -0.65], 'string', mirror=True)

    BOW = ('limb_l', 'limb_r', 'string_l', 'string_r')
    DY = -0.26
    for rec in CUBES:
        if rec['b'] in BOW:
            rec['f'][1] = round(rec['f'][1] + DY, 2)
            rec['t'][1] = round(rec['t'][1] + DY, 2)
            if 'p' in rec:
                rec['p'][1] = round(rec['p'][1] + DY, 2)

    with open(os.path.join('tools', 'bb_model_v3.js'), 'w', encoding='utf-8') as fh:
        fh.write(JS % json.dumps(CUBES, ensure_ascii=False))
    print('cubes:', len(CUBES))


JS = """(function () {
var CUBES = %s;
var out = { made: 0, failed: [] };
Outliner.root.slice().forEach(function (n) { if (n.remove) n.remove(); });
Cube.all.slice().forEach(function (c) { if (c.remove) c.remove(); });
Group.all.slice().forEach(function (g) { if (g.remove) g.remove(); });
Project.texture_width = 64;
Project.texture_height = 64;
Project.name = '十字弩';
Project.geckolib_modid = 'hexalunar_calamity';
var GROUPS = {};
function bone(name, origin, parent) {
  var g = new Group({ name: name, origin: origin });
  g.init();
  if (parent && GROUPS[parent]) g.addTo(GROUPS[parent]);
  GROUPS[name] = g;
}
bone('body', [0, 0, 0], null);
bone('scope', [0, 2.95, 2.4], 'body');
bone('stock', [0, 0.6, 8.0], 'body');
bone('grip', [0, -0.5, 5.6], 'body');
bone('trigger', [0, -0.5, 4.4], 'body');
bone('mag', [0, -0.4, 3.0], 'body');
bone('limb_l', [2.2, 1.64, -1.9], 'body');
bone('limb_r', [-2.2, 1.64, -1.9], 'body');
bone('string_l', [10.8, 1.64, -0.8], 'limb_l');
bone('string_r', [-10.8, 1.64, -0.8], 'limb_r');
bone('bolt', [0, 1.5, -2.0], 'body');
bone('bolt', [0, 1.76, -2.0], 'body');
var MAT = {
  body_main: [4, 4, 1, 1], body_hi: [12, 4, 1, 1], body_dark: [20, 4, 1, 1], metal: [28, 4, 1, 1],
  rubber: [36, 4, 1, 1], string: [44, 4, 1, 1], glass: [52, 4, 1, 1], steel: [60, 4, 1, 1],
  limb: [4, 12, 1, 1], cam: [12, 12, 1, 1], limb_hi: [20, 12, 1, 1], accent: [28, 12, 1, 1],
  scope_body: [36, 12, 1, 1], bolt: [44, 12, 1, 1], glass_dk: [52, 12, 1, 1], white: [60, 12, 1, 1]
};
var FACE = {
  panel: [0, 16, 11, 5], riser: [12, 16, 5, 5], riserN: [18, 16, 5, 5],
  railTop: [24, 16, 2, 11], mag: [28, 16, 4, 5], magN: [33, 16, 4, 2],
  grip: [38, 16, 3, 6], tube: [42, 16, 7, 2], cam: [50, 16, 3, 3],
  limb: [54, 16, 9, 2], bolt: [0, 22, 14, 1], stock: [16, 22, 4, 3],
  receiverTop: [21, 22, 4, 11], glassFx: [52, 20, 3, 2]
};
var FACES = ['north', 'south', 'east', 'west', 'up', 'down'];
CUBES.forEach(function (spec) {
  var g = GROUPS[spec.b];
  if (!g) { out.failed.push(spec.n); return; }
  var c = new Cube({ name: spec.n, from: spec.f, to: spec.t, box_uv: false, autouv: 0, texture: 0 });
  if (spec.r) { c.rotation = spec.r; c.origin = spec.p; }
  c.addTo(g); c.init(); c.box_uv = false;
  var uv = {};
  FACES.forEach(function (f) {
    var r = (spec.fx && spec.fx[f] && FACE[spec.fx[f]]) || MAT[spec.m];
    uv[f] = { uv: [r[0], r[1]], uv_size: [r[2], r[3]] };
  });
  c.uv = uv;
  out.made++;
});
Canvas.updateAll();
if (typeof updateUVEditor === 'function') updateUVEditor();
out.cubes = Cube.all.length;
return JSON.stringify(out, null, 1);
})();
"""

if __name__ == '__main__':
    build()
