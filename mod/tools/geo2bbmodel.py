"""把 build/<name>_v2.geo.json + 贴图 转成 Blockbench 工程（模型/<name>_v3.bbmodel）。

用法: python tools/geo2bbmodel.py            # 全部
      python tools/geo2bbmodel.py akm_v2     # 指定

结构按 Blockbench 的 bedrock/geckolib 工程格式：
  - 元素用 origin/size（Bedrock 风格，与 geo 一致），带旋转的方块连 rotation/pivot 一起带过去
  - outliner 用现代嵌套树（组里挂元素 uuid 和子组）
  - textures 里内嵌 data URL，打开即带 512² 贴图
"""
import base64
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT, '模型')
JOBS = [
    ('akm_v3', 'hexalunar_akm'),
    ('grenade_v3', 'hexalunar_mud'),
    ('flashbang_v3', 'hexalunar_flashbang'),
    ('bow_v3', 'hexalunar_compound_bow'),
    ('crossbow_v3', 'hexalunar_crossbow'),
    ('awp_v1', 'hexalunar_awp'),
    ('mosin_v1', 'hexalunar_mosin_nagant'),
]


def _uuid(s):
    h = hashlib.md5(s.encode('utf-8')).hexdigest()
    return '%s-%s-%s-%s-%s' % (h[:8], h[8:12], h[12:16], h[16:20], h[20:32])


def convert(geo_name, out_name):
    geo_path = os.path.join(ROOT, 'build', geo_name + '.geo.json')
    tex_path = os.path.join(ROOT, 'build', geo_name + '.png')
    out_path = os.path.join(MODELS_DIR, out_name + '.bbmodel')
    g = json.load(open(geo_path, encoding='utf-8'))['minecraft:geometry'][0]
    tw = g['description'].get('texture_width', 512)
    th = g['description'].get('texture_height', 512)

    elements = []
    nodes = {}
    order = []
    for b in g['bones']:
        bname = b['name']
        kids = []
        for i, c in enumerate(b.get('cubes', [])):
            ename = '%s_%s' % (bname, c.get('name') or i)
            eu = _uuid(geo_name + '/el/' + ename)
            # ★ 逐面 UV 必须写成 faces[face].uv = [x1,y1,x2,y2]（像素坐标）。
            # 写成顶层 "uv": {face: {uv, uv_size}} 是无效结构 —— Blockbench 会忽略它，
            # 全部面退化成默认的 [0,0,1,1]（贴图左上角 1 像素），模型在视口里整个发黑。
            faces = {}
            for face, spec in (c.get('uv') or {}).items():
                u0, v0 = float(spec['uv'][0]), float(spec['uv'][1])
                uw, uh = float(spec['uv_size'][0]), float(spec['uv_size'][1])
                faces[face] = {'uv': [u0, v0, u0 + uw, v0 + uh], 'texture': 0}
            el = {'name': ename, 'type': 'cube', 'uuid': eu, 'origin': c['origin'],
                  'size': c['size'], 'inflate': c.get('inflate', 0), 'faces': faces,
                  'visibility': True, 'export': True, 'locked': False, 'box_uv': False}
            if c.get('rotation'):
                el['rotation'] = c['rotation']
                el['pivot'] = c.get('pivot') or c['origin']
            elements.append(el)
            kids.append(eu)
        nodes[bname] = {'name': bname, 'uuid': _uuid(geo_name + '/grp/' + bname),
                        'origin': b['pivot'], 'rotation': b.get('rotation') or [0, 0, 0],
                        'children': kids, 'visibility': True, 'autouv': 0, 'color': 0,
                        'export': True, 'locked': False, 'isOpen': True,
                        '_parent': b.get('parent')}
        order.append(bname)

    # 按 parent 把组挂成树（现代 outliner）
    for bname in order:
        par = nodes[bname].pop('_parent')
        if par and par in nodes:
            nodes[par]['children'].append(nodes[bname])
    roots = [nodes[b['name']] for b in g['bones']
             if not b.get('parent') or b['parent'] not in nodes]

    durl = 'data:image/png;base64,' + base64.b64encode(open(tex_path, 'rb').read()).decode()
    bb = {'meta': {'format_version': '4.5', 'model_format': 'geckolib_model',
                   'box_uv': False},
          'name': out_name,
          'model_identifier': g['description'].get('identifier', ''),
          'resolution': {'width': tw, 'height': th},
          'elements': elements,
          'outliner': roots,
          'textures': [{'path': '', 'name': out_name + '.png', 'folder': 'block',
                        'namespace': '', 'id': '0', 'particle': False,
                        'render_mode': 'default', 'visible': True, 'mode': 'bitmap',
                        'saved': False, 'uuid': _uuid(geo_name + '/tex'), 'source': durl}],
          'animations': [], 'animation_controllers': []}
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(bb, fh, ensure_ascii=False)
    print('%-28s 元素 %3d  组 %2d  %.2f MB' % (os.path.basename(out_path), len(elements),
                                               len(order), os.path.getsize(out_path) / 1048576))


def main(argv):
    want = argv[1:] if len(argv) > 1 else None
    done = 0
    for geo_name, out_name in JOBS:
        if want and geo_name not in want:
            continue
        convert(geo_name, out_name)
        done += 1
    if done == 0:
        print('没有匹配的模型；可选: %s' % ', '.join(j[0] for j in JOBS))


if __name__ == '__main__':
    main(sys.argv)
