# -*- coding: utf-8 -*-
"""r58 文档更新：版本号 r57→r58、修一行乱码、补 JOML 坑与手臂离线验算工具。

用脚本而不是手工编辑的原因：根 readme.md 里有一行早先写坏的字（不可逆的替换字符），
按行号/前缀定位比字符串精确匹配可靠。
"""
import io
import os
import re

ROOT = r'D:\做一个_Minecraft_1_20_1_的_F'
ROOT_README = os.path.join(ROOT, 'readme.md')
MOD_README = os.path.join(ROOT, 'mod', 'README.md')

ARM_BULLET = (
    '- 手臂摆放：手臂方块在 pose 坐标里是 **原点端=肩、局部 +0.75 格端=手**，'
    '所以「把手放到 H」= 原点平移 `H − R·(方块局部 x 中心, 0.75·s, 0)`；\n'
    '  只沿长度方向拉伸（`pose.scale(1,s,1)`），粗细保持原版。'
    '注意右臂方块局部 x 中心是 **−0.375**、左臂（mirror）是 **+0.375**，不补偿手就偏半个方块\n'
)

PITFALL = """14. **JOML 的 `Matrix3f` 9 参数构造是「列优先命名」**
    `new Matrix3f(m00, m01, m02, m10, …)` 里的 `m01` 是**第 0 列第 1 行**。照 `(x, y, z)` 的顺序
    把三个基向量写进去，拿到的是**转置矩阵**（= 反向旋转）。第一人称手臂用它就会整条翻到相机后面去、
    被近平面切一刀 → 屏幕上一大片皮肤色（r57 的 bug）。建正交基要**一列一列地填**：
    `new Matrix3f().setColumn(0, x).setColumn(1, y).setColumn(2, z).getNormalizedRotation(q)`。
    离线自查：`mod/tools/_joml_probe/`（`JomlProbe` 验 JOML 约定、`ArmSim` 算手臂方块落点）。

"""

TOOL_ROW = ("| `_joml_probe/`（Java） | 第一人称手臂离线验算：`JomlProbe` 验 JOML 旋转约定（"
            "`Matrix3f` 构造顺序 / `rotateAxis` 语义），`ArmSim` 按 `WeaponArms` 同一套数学算出"
            "双臂方块 8 个角在相机空间的位置并投影到屏幕，顺带告警「是否越过相机平面」（越过了就是糊屏） |\n")

CHANGELOG_R58 = ("- **r58** — 修第一人称手臂「糊屏」：JOML 的 `Matrix3f` 9 参数构造是列优先命名，"
                 "照 `(x,y,z)` 写基向量得到的是**转置矩阵**（反向旋转），两条手臂被翻到相机后面、"
                 "近平面切一刀，屏幕上是一大片皮肤色。改成 `setColumn` 逐列建基，"
                 "并把肩点前移（`z −0.20 → −0.42`，手臂根部不再贴着相机）、"
                 "补上左臂 mirror 造成的 x 中心偏移（右 −0.375 / 左 +0.375）、"
                 "距离异常时干脆不画\n")


def read_lines(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read().splitlines(True)


def write_lines(path, lines):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.writelines(lines)


def fix_root():
    lines = read_lines(ROOT_README)
    out = []
    done = {'arm': False, 'pit': False, 'tool': False}
    for ln in lines:
        if '1.0.0-r57' in ln:
            ln = ln.replace('1.0.0-r57', '1.0.0-r58')
        if ln.startswith('- 手臂摆放：'):
            out.append(ARM_BULLET)
            done['arm'] = True
            continue
        if ln.startswith('13. **模型共面会 z-fighting'):
            # 13 这条是多行，等它的正文（含缩进的续行）走完再插 14
            out.append(ln)
            continue
        if ln.strip() == '---' and done['arm'] and not done['pit'] and any(
                x.startswith('13. **模型共面') for x in out):
            out.append('\n' + PITFALL)
            done['pit'] = True
        if ln.startswith('| `_ads_check.py`') and not done['tool']:
            out.append(ln)
            out.append(TOOL_ROW)
            done['tool'] = True
            continue
        out.append(ln)
    write_lines(ROOT_README, out)
    print('root readme: 手臂行=%s 坑14=%s 工具行=%s' % (done['arm'], done['pit'], done['tool']))


def fix_mod():
    lines = read_lines(MOD_README)
    out = []
    done = False
    for ln in lines:
        ln = ln.replace('1.0.0-r57', '1.0.0-r58')
        if ln.startswith('- **r57** —') and not done:
            out.append(CHANGELOG_R58)
            done = True
        out.append(ln)
    write_lines(MOD_README, out)
    print('mod readme: r58 条目=%s' % done)


def check():
    for p in (ROOT_README, MOD_README):
        txt = io.open(p, encoding='utf-8').read()
        print('%s: r58 x%d / r57 x%d / U+FFFD x%d' % (
            os.path.basename(os.path.dirname(p)) + '/' + os.path.basename(p),
            txt.count('r58'), txt.count('r57'), txt.count('\ufffd')))


if __name__ == '__main__':
    fix_root()
    fix_mod()
    check()
