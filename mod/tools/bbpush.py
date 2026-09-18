#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 GeckoLib geo.json + 512² 贴图推进正在运行的 Blockbench（走 blockbench-mcp 的 risky_eval）。

用法: python tools/bbpush.py <geo.json> <texture.png> [项目名] [--format bedrock]

行为：清空当前工程 → 建贴图 → 建骨骼(Group) → 建方块(逐面 UV，含旋转/枢轴) → 刷新画布，
最后返回工程概况。之后可以用 capture_screenshot 截图核对。
"""
import base64
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def no_slash(s):
    """risky_eval 禁止源码里出现 '//'，base64 里可能恰好有，用 \\u002f 转义掉。"""
    return s.replace('/', '\\u002f')


def build_js(geo, tex_b64, name, size):
    g = geo['minecraft:geometry'][0]
    desc = g.get('description', {})
    tw = desc.get('texture_width', size)
    th = desc.get('texture_height', size)
    bones = g['bones']
    lines = []
    a = lines.append
    a('(function () {')
    a('  Project.name = %s;' % js_str(name))
    a('  Project.texture_width = %d; Project.texture_height = %d;' % (tw, th))
    a('  Outliner.root.slice().forEach(function (n) { if (n.remove) n.remove(); });')
    a('  Cube.all.slice().forEach(function (c) { if (c.remove) c.remove(); });')
    a('  Group.all.slice().forEach(function (gr) { if (gr.remove) gr.remove(); });')
    a('  Texture.all.slice().forEach(function (t) { if (t.remove) t.remove(false); });')
    a('  var TEXDATA = "data:image/png;base64,%s";' % no_slash(tex_b64))
    a('  var tex = new Texture({ name: %s, width: %d, height: %d });' % (js_str(name), tw, th))
    a('  tex.add();')
    a('  try { tex.fromDataURL(TEXDATA); } catch (e) { }')
    a('  tex.uv_width = %d; tex.uv_height = %d;' % (tw, th))
    a('  if (tex.setAsDefaultTexture) tex.setAsDefaultTexture();')
    a('  var TEXU = tex.uuid;')
    a('  var GROUPS = {};')
    a('  function bone(nm, origin, parent) {')
    a('    var gr = new Group({ name: nm, origin: origin });')
    a('    gr.init();')
    a('    var p = (parent && GROUPS[parent]) ? GROUPS[parent] : null;')
    a('    if (p) gr.addTo(p);')
    a('    GROUPS[nm] = gr; return gr;')
    a('  }')
    for b in bones:
        a('  bone(%s, %s, %s);' % (js_str(b['name']),
                                   json.dumps(b['pivot']),
                                   js_str(b.get('parent') or '')))
    a('  var created = 0;')
    for b in bones:
        for i, c in enumerate(b.get('cubes') or []):
            o = c['origin']
            s = c['size']
            frm = [o[0], o[1], o[2]]
            to = [o[0] + s[0], o[1] + s[1], o[2] + s[2]]
            a('  (function () {')
            a('    var cb = new Cube({ name: %s, from: %s, to: %s, box_uv: false, autouv: 0, texture: TEXU });'
              % (js_str('%s_%d' % (b['name'], i)), json.dumps(frm), json.dumps(to)))
            a('    cb.addTo(GROUPS[%s]); cb.init(); cb.box_uv = false;' % js_str(b['name']))
            if c.get('rotation'):
                a('    cb.rotation = %s; cb.origin = %s;'
                  % (json.dumps([float(v) for v in c['rotation']]),
                     json.dumps([float(v) for v in (c.get('pivot') or [0, 0, 0])])))
            uv = {}
            for face, spec in (c.get('uv') or {}).items():
                u0, v0 = float(spec['uv'][0]), float(spec['uv'][1])
                uw, uh = float(spec['uv_size'][0]), float(spec['uv_size'][1])
                uv[face] = [u0, v0, u0 + uw, v0 + uh]
            a('    var UV = %s;' % json.dumps(uv))
            a('    for (var fk in UV) { if (cb.faces[fk]) cb.faces[fk].uv = UV[fk]; }')
            a('    created++;')
            a('  })();')
    a('  Cube.all.slice().forEach(function (c) { c.texture = TEXU; c.color = 0;');
    a('    for (var f in c.faces) { c.faces[f].texture = TEXU; } });')
    a('  Canvas.updateAll();')
    a('  if (typeof updateUVEditor === "function") updateUVEditor();')
    a('  return JSON.stringify({cubes: created, groups: Group.all.length,')
    a('    size: [Project.texture_width, Project.texture_height],')
    a('    gallery: Texture.all.map(function (t) { return t.name + ":" + t.width + "x" + t.height; }),')
    a('    bones: Group.all.map(function (gr) { return gr.name + "(" + (gr.parent ? gr.parent.name : "-") + ")"; })}, null, 1);')
    a('})();')
    return '\n'.join(lines)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    geo_path, tex_path = args[0], args[1]
    name = args[2] if len(args) > 2 else os.path.splitext(os.path.basename(geo_path))[0]
    geo = json.load(open(geo_path, encoding='utf-8'))
    with open(tex_path, 'rb') as fh:
        b64 = base64.b64encode(fh.read()).decode('ascii')
    js = build_js(geo, b64, name, 512)
    out = os.path.join(ROOT, 'build', '_bbpush.js')
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(js)
    print('wrote %s (%d bytes)' % (out, len(js)))
    if '--write-only' in sys.argv:
        return 0
    import subprocess
    return subprocess.call([sys.executable, os.path.join(ROOT, 'tools', 'bbmcp.py'),
                            'js', out], cwd=ROOT)


if __name__ == '__main__':
    sys.exit(main())
