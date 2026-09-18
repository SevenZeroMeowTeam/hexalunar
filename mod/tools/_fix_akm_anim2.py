import json
import os

p = os.path.join('src', 'main', 'resources', 'assets', 'hexalunar_calamity', 'animations',
                 'akm.animation.json')
a = json.load(open(p, encoding='utf-8'))
anim = a['animations']

# 换弹期间 magazine / bolt 由 AkmGeoModel.setCustomAnimations 按真实读条程序化驱动
rel = anim['animation.akm.reload']['bones']
rel.pop('magazine', None)
rel.pop('bolt', None)

# 拉机柄行程按真实 AK（约 10cm）收敛
anim['animation.akm.fire']['bones']['bolt']['position'] = {
    '0': {'vector': [0, 0, 0]},
    '0.07': {'vector': [0, 0, 1.9]},
    '0.17': {'vector': [0, 0, 0]},
    '0.3': {'vector': [0, 0, 0]},
}
anim['animation.akm.bolt_pull']['bones']['bolt']['position'] = {
    '0': {'vector': [0, 0, 0]},
    '0.24': {'vector': [0, 0, 2.9]},
    '0.36': {'vector': [0, 0, 2.9]},
    '0.52': {'vector': [0, 0, -0.25]},
    '0.66': {'vector': [0, 0, 0]},
    '0.8': {'vector': [0, 0, 0]},
}

with open(p, 'w', encoding='utf-8') as fh:
    json.dump(a, fh, ensure_ascii=False, indent=1)
print('reload bones now:', list(anim['animation.akm.reload']['bones'].keys()))
print('animations:', list(anim.keys()))
print('written', p, os.path.getsize(p))
