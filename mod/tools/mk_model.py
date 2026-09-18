#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 tools/bb_model_v2.js —— 在 Blockbench 里重建十字弩（GeckoLib 真骨骼）。

设计目标（对齐 模型/十字弩.bbmodel 的原始造型 + 参考照片）：
  * 长度轴 -Z 向前（弓臂在 -Z 端），+Y 向上，原点在握把处（GeckoLib 物品模型约定）
  * 用倒角小件、斜面（cube rotation）、锥形弓臂、圆形凸轮替代"大方块"，
    让模型在 1/16 方块尺度下更像真实器械

产物：tools/bb_model_v2.js
"""
import json
import os

CUBES = []
MIRROR = []


def cube(name, bone, f, t, mat, fx=None, rot=None, pivot=None, mirror=False):
    rec = {
        'n': name, 'b': bone, 'f': [round(v, 3) for v in f], 't': [round(v, 3) for v in t], 'm': mat,
    }
    if fx:
        rec['fx'] = fx
    if rot:
        rec['r'] = rot
        rec['p'] = pivot
    CUBES.append(rec)
    if mirror:
        mf = [-t[0], f[1], f[2]]
        mt = [-f[0], t[1], t[2]]
        mrec = {'n': name + '_r', 'b': bone.replace('_l', '_r'), 'f': mf, 't': mt, 'm': mat}
        if fx:
            mrec['fx'] = fx
        if rot:
            mrec['r'] = [rot[0], -rot[1], -rot[2]]
            mrec['p'] = [-pivot[0], pivot[1], pivot[2]]
        CUBES.append(mrec)


def disc_yz_x(name, bone, cx, cy, cz, r, depth, mat, segments=5):
    """在 XY 平面上近似出一个圆盘（凸轮），沿 Z 方向有厚度。"""
    step = 2.0 * r / segments
    for i in range(segments):
        y0 = cy - r + i * step
        yc = y0 + step / 2.0
        dy = abs(yc - cy)
        half = (max(r * r - dy * dy, 0.04)) ** 0.5
        cube('%s_%d' % (name, i), bone, [cx - half, y0, cz - depth / 2.0], [cx + half, y0 + step, cz + depth / 2.0], mat)


def teeth(name, bone, x0, x1, y0, y1, z0, z1, pitch, width, mat):
    z = z0
    i = 0
    while z + width <= z1:
        cube('%s_%d' % (name, i), bone, [x0, y0, z], [x1, y1, z + width], mat)
        z += pitch
        i += 1


def build():
    B = 'body'

    cube('lower_recv', B, [-1.9, -2.0, -2.6], [1.9, 1.5, 8.6], 'body_main', {'east': 'panel', 'west': 'panel'})
    cube('lower_bevel_l', B, [-2.05, -1.6, 0.4], [-1.9, 0.9, 7.4], 'body_hi', mirror=True)

    cube('upper_recv', B, [-1.7, 1.5, -3.2], [1.7, 3.9, 7.3], 'body_main', {'east': 'panel', 'west': 'panel'})
    cube('upper_bevel_l', B, [-1.85, 2.1, -2.9], [-1.7, 3.6, 7.1], 'body_hi', mirror=True)
    cube('brass_deflector', B, [-1.55, 2.9, 0.5], [1.55, 3.75, 3.3], 'body_hi')

    cube('eject_port', B, [-1.72, 2.55, 3.6], [1.72, 3.7, 6.9], 'body_dark')
    cube('charge_handle', B, [-0.45, 2.5, -3.9], [0.45, 3.3, -2.9], 'metal')
    cube('charge_knob', B, [-0.8, 2.35, -4.5], [0.8, 3.45, -3.9], 'metal')

    cube('mag_release', B, [-0.6, -2.05, 2.6], [0.6, -1.5, 3.9], 'metal')
    cube('selector_l', B, [-2.35, -0.9, 3.6], [-1.9, -0.15, 4.7], 'metal', mirror=True)
    cube('bolt_lock', B, [-2.25, 0.1, 6.2], [-1.9, 0.75, 7.1], 'metal', mirror=True)

    cube('rail_front_l', B, [-1.3, 3.9, -9.8], [-0.75, 4.2, -3.2], 'metal', {'up': 'railTop'}, mirror=True)
    teeth('rail_front_t', B, -1.28, -0.77, 4.2, 4.4, -9.6, -3.3, 1.5, 0.95, 'metal')
    teeth('rail_front_tr', B, 0.77, 1.28, 4.2, 4.4, -9.6, -3.3, 1.5, 0.95, 'metal')
    cube('rail_rear_l', B, [-1.3, 3.9, 0.0], [-0.75, 4.2, 7.2], 'metal', {'up': 'railTop'}, mirror=True)
    teeth('rail_rear_t', B, -1.28, -0.77, 4.2, 4.4, 0.1, 7.1, 1.5, 0.95, 'metal')
    teeth('rail_rear_tr', B, 0.77, 1.28, 4.2, 4.4, 0.1, 7.1, 1.5, 0.95, 'metal')
    cube('bolt_groove', B, [-0.72, 3.86, -10.0], [0.72, 3.98, 3.0], 'body_dark')

    cube('guard_front', B, [-1.05, -4.4, 1.5], [1.05, -3.3, 2.1], 'body_dark')
    cube('guard_bottom', B, [-1.05, -4.4, 1.5], [1.05, -3.8, 4.3], 'body_dark')
    cube('guard_rear', B, [-1.05, -4.4, 3.9], [1.05, -1.4, 4.5], 'body_dark')

    cube('handguard', B, [-1.5, 0.5, -9.6], [1.5, 3.65, -3.2], 'body_main', {'east': 'riser', 'west': 'riser'})
    cube('hg_bevel_l', B, [-1.65, 1.1, -9.3], [-1.5, 3.2, -3.5], 'body_hi', mirror=True)
    for i, z in enumerate([-8.9, -7.6, -6.3, -5.0]):
        cube('hg_slot_%d' % i, B, [-1.52, 1.6, z], [-1.35, 2.1, z + 0.85], 'body_dark', mirror=True)
        cube('hg_slot_b_%d' % i, B, [-1.52, 0.95, z], [-1.35, 1.4, z + 0.85], 'body_dark', mirror=True)

    cube('riser', B, [-2.3, -0.2, -11.5], [2.3, 4.25, -9.5], 'body_main', {'east': 'riser', 'west': 'riser', 'north': 'riserN'})
    cube('riser_top', B, [-1.7, 3.4, -10.9], [1.7, 4.7, -9.6], 'body_hi')
    cube('riser_bevel_l', B, [-2.45, 0.6, -11.2], [-2.3, 3.6, -9.8], 'body_hi', mirror=True)
    cube('limb_pocket_l', B, [2.0, 1.4, -11.3], [2.9, 4.0, -9.6], 'metal', mirror=True)
    cube('limb_pocket_cap_l', B, [2.3, 1.8, -11.6], [2.7, 3.6, -11.3], 'steel', mirror=True)

    cube('scope_mount_fl', B, [-1.35, 4.2, -8.8], [-0.7, 5.3, -7.4], 'metal', mirror=True)
    cube('scope_mount_rl', B, [-1.35, 4.2, -2.6], [-0.7, 5.3, -1.2], 'metal', mirror=True)
    cube('scope_ring_f', B, [-1.6, 4.9, -9.2], [1.6, 6.3, -7.0], 'metal')
    cube('scope_ring_r', B, [-1.6, 4.9, -3.0], [1.6, 6.3, -0.8], 'metal')

    cube('scope_tube', 'scope', [-1.35, 5.05, -9.0], [1.35, 6.15, -0.9], 'scope_body', {'east': 'tube', 'west': 'tube'})
    cube('scope_obj', 'scope', [-1.8, 4.65, -10.3], [1.8, 6.55, -9.0], 'metal')
    cube('scope_glass', 'scope', [-1.5, 4.9, -10.6], [1.5, 6.3, -10.3], 'glass', {'north': 'glassFx'})
    cube('scope_eye', 'scope', [-1.7, 4.8, -0.9], [1.7, 6.4, 0.4], 'metal')
    cube('scope_turret_v', 'scope', [-0.55, 6.55, -6.4], [0.55, 7.5, -5.3], 'metal')
    cube('scope_turret_vc', 'scope', [-0.35, 7.5, -6.2], [0.35, 7.8, -5.5], 'steel')
    cube('scope_turret_h', 'scope', [1.35, 5.25, -6.4], [2.15, 6.0, -5.3], 'metal')
    cube('scope_eye_lens', 'scope', [-1.45, 5.0, 0.4], [1.45, 6.2, 0.6], 'glass_dk')

    cube('magwell', B, [-1.7, 3.9, 1.3], [1.7, 5.1, 6.4], 'body_dark')
    cube('magwell_lip', B, [-1.85, 5.1, 1.2], [1.85, 5.5, 6.5], 'metal')

    cube('stock_tube', 'stock', [-1.45, 1.4, 7.3], [1.45, 3.5, 10.4], 'body_main', {'east': 'stock', 'west': 'stock'})
    cube('stock_tube_l', 'stock', [-1.6, 1.9, 7.4], [-1.45, 3.1, 10.3], 'body_hi', mirror=True)
    cube('stock_top', 'stock', [-1.35, 3.5, 7.5], [1.35, 4.2, 10.6], 'body_main', rot=[-4, 0, 0], pivot=[0, 3.5, 10.6])
    cube('stock_riser', 'stock', [-0.95, 4.2, 8.2], [0.95, 5.0, 10.9], 'rubber')
    cube('stock_bridge', 'stock', [-1.05, -0.9, 8.0], [1.05, 1.5, 10.6], 'body_dark', rot=[-3, 0, 0], pivot=[0, 1.5, 8.0])
    cube('stock_bridge2', 'stock', [-1.05, -2.2, 8.5], [1.05, -0.9, 10.3], 'body_dark', rot=[-2, 0, 0], pivot=[0, -0.9, 8.5])
    cube('buttpad', 'stock', [-1.5, -3.2, 10.6], [1.5, 4.9, 11.6], 'rubber', rot=[-6, 0, 0], pivot=[0, 0, 10.6])
    cube('buttpad_l', 'stock', [-1.65, -3.0, 10.7], [-1.5, 4.7, 11.5], 'body_dark', rot=[-6, 0, 0], pivot=[0, 0, 10.6], mirror=True)
    cube('sling_loop', 'stock', [-0.35, -3.4, 9.4], [0.35, -2.6, 10.6], 'metal')

    cube('grip_core', 'grip', [-1.3, -7.4, 4.0], [1.3, -2.0, 6.0], 'rubber', {'east': 'grip', 'west': 'grip'},
         rot=[14, 0, 0], pivot=[0, -2.0, 5.0])
    cube('grip_face', 'grip', [-1.05, -6.4, 3.5], [1.05, -3.4, 3.95], 'body_dark', rot=[14, 0, 0], pivot=[0, -2.0, 5.0])
    cube('grip_base', 'grip', [-1.45, -8.3, 3.2], [1.45, -7.0, 5.8], 'rubber', rot=[14, 0, 0], pivot=[0, -2.0, 5.0])
    cube('grip_heel', 'grip', [-1.35, -2.6, 6.0], [1.35, -1.0, 6.7], 'body_main')

    cube('trigger_blade', 'trigger', [-0.32, -3.9, 2.6], [0.32, -2.2, 3.2], 'metal')
    cube('trigger_pin', 'trigger', [-0.55, -2.3, 3.5], [0.55, -1.9, 4.3], 'steel')

    cube('mag_body', 'mag', [-1.35, 5.1, 1.5], [1.35, 9.2, 5.6], 'body_dark', {'east': 'mag', 'west': 'mag', 'north': 'magN'},
         rot=[-5, 0, 0], pivot=[0, 5.1, 5.6])
    cube('mag_rib_0', 'mag', [-1.45, 6.0, 1.35], [1.45, 6.5, 5.5], 'body_hi', rot=[-5, 0, 0], pivot=[0, 5.1, 5.6])
    cube('mag_rib_1', 'mag', [-1.45, 7.2, 1.55], [1.45, 7.7, 5.5], 'body_hi', rot=[-5, 0, 0], pivot=[0, 5.1, 5.6])
    cube('mag_rib_2', 'mag', [-1.45, 8.4, 1.75], [1.45, 8.9, 5.5], 'body_hi', rot=[-5, 0, 0], pivot=[0, 5.1, 5.6])
    cube('mag_floor', 'mag', [-1.5, 9.2, 1.0], [1.5, 9.9, 5.4], 'metal', rot=[-5, 0, 0], pivot=[0, 5.1, 5.6])
    cube('mag_witness', 'mag', [-0.45, 5.6, 1.35], [0.45, 6.6, 1.5], 'steel', rot=[-5, 0, 0], pivot=[0, 5.1, 5.6])

    cube('bolt_shaft', 'bolt', [-0.28, 4.0, -12.6], [0.28, 4.42, 2.2], 'bolt', {'east': 'bolt', 'west': 'bolt'})
    cube('bolt_nock', 'bolt', [-0.42, 4.0, 2.2], [0.42, 4.42, 2.9], 'accent')
    cube('bolt_head', 'bolt', [-0.5, 3.9, -14.3], [0.5, 4.52, -12.6], 'steel')
    cube('bolt_fletch_l', 'bolt', [-1.25, 3.85, 0.3], [0.0, 4.57, 2.2], 'bolt', mirror=True)
    cube('bolt_fletch_u', 'bolt', [-0.25, 4.42, 0.3], [0.25, 5.3, 2.2], 'bolt')

    L = 'limb_l'
    cube('limb_base', L, [1.7, 3.0, -10.6], [3.6, 5.4, -8.4], 'limb_hi', {'north': 'limb', 'south': 'limb'}, mirror=True)
    cube('limb_seg1', L, [3.4, 3.35, -10.35], [6.6, 5.05, -8.65], 'limb', {'north': 'limb', 'south': 'limb'},
         rot=[0, -6, 0], pivot=[2.6, 4.2, -9.5], mirror=True)
    cube('limb_seg2', L, [6.4, 3.6, -10.0], [9.2, 4.8, -8.5], 'limb', {'north': 'limb', 'south': 'limb'},
         rot=[0, -11, 0], pivot=[2.6, 4.2, -9.5], mirror=True)
    cube('limb_tip', L, [9.0, 3.85, -9.6], [10.6, 4.55, -8.4], 'limb_hi',
         rot=[0, -15, 0], pivot=[2.6, 4.2, -9.5], mirror=True)
    cube('limb_ridge', L, [3.5, 4.55, -10.1], [9.1, 5.0, -8.9], 'limb_hi', rot=[0, -9, 0], pivot=[2.6, 4.2, -9.5], mirror=True)

    for i in range(5):
        y0 = 2.9 + i * 0.55
        yc = y0 + 0.275
        dy = abs(yc - 4.2)
        half = (max(1.35 * 1.35 - dy * dy, 0.05)) ** 0.5
        cube('cam_%d' % i, L, [10.6 - half, y0, -10.3], [10.6 + half, y0 + 0.55, -7.9], 'cam',
             {'east': 'cam', 'west': 'cam'}, rot=[0, -16, 0], pivot=[2.6, 4.2, -9.5], mirror=True)
    cube('cam_hub', L, [10.0, 3.85, -10.5], [11.2, 4.55, -7.7], 'steel', rot=[0, -16, 0], pivot=[2.6, 4.2, -9.5], mirror=True)
    cube('cam_guide', L, [10.4, 2.7, -7.9], [11.6, 5.7, -7.4], 'metal', rot=[0, -16, 0], pivot=[2.6, 4.2, -9.5], mirror=True)

    cube('string_l', 'string_l', [0, 4.06, -8.0], [11.0, 4.34, -7.6], 'string', mirror=True)
    cube('string_l_c', 'string_l', [0, 2.95, -7.9], [11.0, 3.1, -7.7], 'string', mirror=True)

    with open(os.path.join('tools', 'bb_model_v2.js'), 'w', encoding='utf-8') as fh:
        fh.write(JS_CUBES % json.dumps(CUBES, ensure_ascii=False))
    print('cubes:', len(CUBES), '->', 'tools/bb_model_v2.js')


JS_CUBES = """(function () {
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
bone('scope', [0, 5.6, -5], 'body');
bone('stock', [0, 2.4, 8], 'body');
bone('grip', [0, -2.6, 5.0], 'body');
bone('trigger', [0, -2.6, 3.4], 'body');
bone('mag', [0, 5.1, 5.6], 'body');
bone('limb_l', [2.6, 4.2, -9.5], 'body');
bone('limb_r', [-2.6, 4.2, -9.5], 'body');
bone('string_l', [11.0, 4.2, -7.8], 'limb_l');
bone('string_r', [-11.0, 4.2, -7.8], 'limb_r');
bone('bolt', [0, 4.2, -4], 'body');

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
  if (spec.r) {
    c.rotation = spec.r;
    c.origin = spec.p;
  }
  c.addTo(g);
  c.init();
  c.box_uv = false;
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
out.groups = Group.all.map(function (g) { return g.name + '<' + (g.parent ? g.parent.name : 'root') + '>'; });
return JSON.stringify(out, null, 1);
})();
"""

if __name__ == '__main__':
    build()
