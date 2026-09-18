# -*- coding: utf-8 -*-
"""按 SuperbWarfare（同 MC 1.20.1 + GeckoLib 的成熟枪械 mod）的约定修手持 display。

★ 参考结论（读 E:\\9n9v\\SuperbWarfare\\...\\models\\displaysettings\\*.item.json）：
  它家所有枪械/复合弓（bocek）的手持 display **rotation 一律不给（= identity）**，
  只给 translation（+ 偶尔一点 scale）。
  原因：模型本身就按「前向 = -Z、上 = +Y、原点 = 握把」建。
  第一人称下枪天然被手锚点摆在屏幕右下，因为透视本来就从侧后方看它 —— 不需要再叠偏航。
  之前给 AKM 加 32° 偏航（tools/_akm_display.py）等于把枪口拧向一侧 → 就是"倾斜"的来源。

参考值（1/16 方块）：
  ak_47.item.json   firstperson_righthand translation [-6.5, 3.5, 4.5]  thirdperson [-0.75,-0.75,0] scale .7
  bocek.item.json   firstperson_righthand translation [-9, -5.25, -7.25]
本仓库 AKM 长度约是它家 AK47 的 0.4 倍（16.2 vs 40.8 单位），故平移按比例缩放。
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'hexalunar_calamity',
                     'models', 'item')

AKM = {
    'gui': {'rotation': [0, -90, -14], 'translation': [0, 0, 0], 'scale': [0.86, 0.86, 0.86]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 2.0, 0], 'scale': [0.5, 0.5, 0.5]},
    'head': {'rotation': [0, 0, 0], 'translation': [0, 13, 0], 'scale': [0.6, 0.6, 0.6]},
    'fixed': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [0.8, 0.8, 0.8]},
    # 手持：只平移，不旋转（枪口保持正对视线方向）
    'thirdperson_righthand': {'rotation': [0, 0, 0], 'translation': [-0.75, -0.75, 0],
                              'scale': [0.7, 0.7, 0.7]},
    'thirdperson_lefthand': {'rotation': [0, 0, 0], 'translation': [0.75, -0.75, 0],
                             'scale': [0.7, 0.7, 0.7]},
    'firstperson_righthand': {'rotation': [0, 0, 0], 'translation': [-2.6, 1.4, 1.8],
                              'scale': [1.0, 1.0, 1.0]},
    'firstperson_lefthand': {'rotation': [0, 0, 0], 'translation': [2.6, 1.4, 1.8],
                             'scale': [1.0, 1.0, 1.0]},
}

# 十字弩：本来就已经是 identity，这里只把 scale 统一、去掉多余旋转
CROSSBOW = {
    'gui': {'rotation': [0, -90, -16], 'translation': [0, 1, 0], 'scale': [0.9, 0.9, 0.9]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [0.48, 0.48, 0.48]},
    'head': {'rotation': [0, 0, 0], 'translation': [0, 13, 0], 'scale': [0.78, 0.78, 0.78]},
    'fixed': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [0.72, 0.72, 0.72]},
    'thirdperson_righthand': {'rotation': [0, 0, 0], 'translation': [0, 0, 0],
                              'scale': [0.8, 0.8, 0.8]},
    'thirdperson_lefthand': {'rotation': [0, 0, 0], 'translation': [0, 0, 0],
                             'scale': [0.8, 0.8, 0.8]},
    'firstperson_righthand': {'rotation': [0, 0, 0], 'translation': [0, 0.6, 1.2],
                              'scale': [0.8, 0.8, 0.8]},
    'firstperson_lefthand': {'rotation': [0, 0, 0], 'translation': [0, 0.6, 1.2],
                             'scale': [0.8, 0.8, 0.8]},
}


def patch(name, display, drop_keys=()):
    p = os.path.join(ITEMS, name)
    d = json.load(io.open(p, encoding='utf-8'))
    disp = d.setdefault('display', {})
    for k in drop_keys:
        disp.pop(k, None)
    for k, v in display.items():
        disp[k] = v
    json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('patched', name)
    for k in ('firstperson_righthand', 'thirdperson_righthand'):
        print('   %-22s %s' % (k, json.dumps(disp.get(k), ensure_ascii=False)))


def main():
    patch('akm.json', AKM)
    patch('crossbow.json', CROSSBOW)


if __name__ == '__main__':
    main()
