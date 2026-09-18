#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用 Blockbench 制作 / 保存 AKM 的 GeckoLib 工程。

流程（全部通过 Blockbench 的 MCP 驱动，模型与 UV 由 Blockbench 自己维护）：
  1. 用 bedrock 几何 codec 打开 geo/akm.geo.json（骨骼 + 方块 + 逐面 UV）
  2. 转成 GeckoLib Animated Model 格式（Project.convertFormat）
  3. 建 512x512 贴图并挂到所有面
  4. 存成 模型/akm_geckolib.bbmodel（Blockbench 工程，可继续手工编辑骨骼/动画）

用法:
  python tools/akm_bb.py build       # 导入 + 转换 + 挂贴图 + 存工程
  python tools/akm_bb.py read        # 把当前工程的方块/UV 导出来检查
  python tools/akm_bb.py shot        # 截一张图
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bbmcp import Mcp  # noqa: E402

ROOT = os.path.abspath('.')
GEO = 'src/main/resources/assets/hexalunar_calamity/geo/akm.geo.json'
TEX = 'src/main/resources/assets/hexalunar_calamity/textures/models/akm_geo.png'
BB = '模型/akm_geckolib.bbmodel'
DUMP = 'build/bb_akm_dump.json'
TEX_SIZE = 512


def p(path):
    return os.path.join(ROOT, path).replace('\\', '/')


def load_geo(mcp):
    code = ("const fs=require('fs');const p='%s';const o=JSON.parse(fs.readFileSync(p,'utf8'));"
            "Codecs.bedrock.parse(o,p).then(m=>{const mm=m||{};if(mm.load){mm.load(p);}"
            "Blockbench.showQuickMessage('geo loaded');}).catch(e=>Blockbench.showQuickMessage('ERR '+e.message));"
            "'importing geo'" % p(GEO))
    return mcp.call('risky_eval', {'code': code})


def convert(mcp, fmt='geckolib_model'):
    mcp.call('trigger_action', {'action': 'convert_project', 'confirmDialog': False})
    time.sleep(0.9)
    r = mcp.call('fill_dialog', {'values': json.dumps({'format': fmt}), 'confirm': True})
    time.sleep(1.6)
    return r


def make_texture(mcp):
    return mcp.call('create_texture', {'name': 'akm_geo', 'width': TEX_SIZE, 'height': TEX_SIZE,
                                       'data': p(TEX)})


def assign_texture(mcp):
    code = ("const t=(Texture.all[0]||null);"
            "let n=0;(Cube.all||[]).forEach(c=>Object.values(c.faces||{}).forEach(f=>{"
            "if(f){f.texture=(t?t.uuid:0);n++;}}));"
            "if(t&&Project){Project.textures=[t];}"
            "Canvas.updateAll&&Canvas.updateAll();'faces='+n+' textures='+Texture.all.length")
    return mcp.call('risky_eval', {'code': code})


def read_model(mcp):
    code = ("const fs=require('fs');"
            "const d={meta:(Project.meta||{}),name:Project.name,"
            "resolution:(Project.resolution||{}),"
            "elements:(Cube.all||[]).map(c=>({name:c.name,from:c.from,to:c.to,"
            "origin:c.origin,size:c.size,"
            "parent:(c.parent&&c.parent.name)||null,rotation:c.rotation||[0,0,0],"
            "faces:Object.fromEntries(Object.entries(c.faces||{}).filter(([k,v])=>v&&v.uv)"
            ".map(([k,v])=>[k,v.uv]))})),"
            "groups:(Group.all||[]).map(g=>({name:g.name,origin:g.origin,parent:(g.parent&&g.parent.name)||null,"
            "children:(g.children||[]).map(c=>c.name)})),"
            "format:Project.format.id};"
            "fs.writeFileSync('%s',JSON.stringify(d,null,1));"
            "'dumped '+d.elements.length+' elements'" % p(DUMP))
    return mcp.call('risky_eval', {'code': code})


def save_bbmodel(mcp):
    return mcp.call('export_model', {'codec_id': 'project', 'path': p(BB),
                                     'max_content_length': 0})


def reload_bbmodel(mcp):
    code = ("const fs=require('fs');const p='%s';const o=JSON.parse(fs.readFileSync(p,'utf8'));"
            "Codecs.project.parse(o,p).then(mm=>{const x=mm||{};if(x&&x.load){x.load(p);}"
            "Blockbench.showQuickMessage('akm reloaded');}).catch(e=>Blockbench.showQuickMessage('ERR '+e.message));"
            "'reloading ' + ((Project.animations||[]).length)" % p(BB))
    return mcp.call('risky_eval', {'code': code})


def main(argv):
    cmd = argv[1] if len(argv) > 1 else 'build'
    mcp = Mcp().connect()
    if cmd == 'reload':
        print(reload_bbmodel(mcp).get('text', '')[:120])
        time.sleep(3.5)
        info = mcp.call('get_project_info', {}).get('text', '')
        print(info[:200].replace('\n', ' '))
        anims = mcp.call('risky_eval', {'code': "(Project.animations||[]).map(a=>a.name).join(',')"}).get('text', '')
        print('工程里的动画:', anims[:200])
        print(mcp.call('capture_screenshot', {}).get('text', '')[:140])
        return 0
    if cmd == 'build':
        print('0) 建空白工程（MCP 的脚本编辑需要已打开的工程）…')
        print('   ', mcp.call('create_project', {'name': 'akm', 'format': 'geckolib_model'}).get('text', '')[:110])
        time.sleep(1.0)
        print('1) 导入 geo …')
        print('   ', load_geo(mcp).get('text', '')[:110])
        time.sleep(2.5)
        print('   工程:', mcp.call('get_project_info', {}).get('text', '')[:220].replace('\n', ' '))
        print('2) 转 GeckoLib 格式 …')
        print('   ', convert(mcp).get('text', '')[:120])
        print('   工程:', mcp.call('get_project_info', {}).get('text', '')[:200].replace('\n', ' '))
        print('3) 建 512 贴图 …')
        print('   ', make_texture(mcp).get('text', '')[:100])
        time.sleep(1.0)
        print('4) 挂到所有面 …')
        print('   ', assign_texture(mcp).get('text', '')[:120])
        print('5) 读回检查 …')
        print('   ', read_model(mcp).get('text', '')[:120])
        print('6) 存 Blockbench 工程 …')
        print('   ', save_bbmodel(mcp).get('text', '')[:160])
    elif cmd == 'read':
        print(read_model(mcp).get('text', ''))
    elif cmd == 'shot':
        r = mcp.call('capture_screenshot', {})
        print(r.get('text', '')[:200])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
