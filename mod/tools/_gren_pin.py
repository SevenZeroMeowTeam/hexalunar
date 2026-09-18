# -*- coding: utf-8 -*-
"""手雷 / 震爆弹「保险销 + 压杆」行为离线自检（r75）。

只做两件事：
1. 读源码核对关键规则（尤其是「手里攥着绝不能点燃引信」这条硬保证）；
2. 把状态机可读地打出来，方便对着用户描述逐条核对。

用法： cd mod; python tools/_gren_pin.py
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEM = os.path.join(ROOT, "src", "main", "java", "cn", "blockforge", "generated",
                    "hexalunarcalamity", "item", "GrenadeItem.java")
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "hexalunar_calamity", "lang")

ok = True


def check(label, cond, detail=u""):
    global ok
    ok = ok and bool(cond)
    print(u"  [%s] %s%s" % (u"OK " if cond else u"FAIL", label,
                            (u"  -> " + detail) if detail else u""))


def read(path):
    """按 UTF-8 读文件（源码与语言文件都是 UTF-8）"""
    with io.open(path, encoding=u"utf-8") as fh:
        return fh.read()


with io.open(ITEM, encoding="utf-8") as fh:
    src = fh.read()

print(u"== 1. 写实规则：松手就击发、手里/身上照样烧 ==")
check(u"有 lightFuse（撞针击发 = 点燃引信）", u"private static void lightFuse(" in src)
check(u"serverEndHold：PRIMED 松手 ⇒ lightFuse",
      re.search(r"STATE_PRIMED\)\s*\{\s*\n\s*lightFuse\(stack, now\);", src) is not None)
check(u"手里烧：serverTick 的 ARMED 走 burnInHand",
      u"case STATE_ARMED -> burnInHand(player, stack, g, now);" in src)
check(u"掌心起爆：burnInHand 调 detonateInHand",
      re.search(r"burnInHand[\s\S]{0,500}detonateInHand", src) is not None)
check(u"背包 / 护甲里的雷也照烧（tickStored ⇒ detonateInHand）",
      re.search(r"tickStored[\s\S]{0,500}detonateInHand", src) is not None)
check(u"引信点燃后插不回销（ARMED ⇒ fuse_no_pin_back）",
      u'"message.hexalunar_calamity.fuse_no_pin_back"' in src)
check(u"副手 + 主手枪械 = 被胳臂夹着（避免必死局面）", u"clampedUnderArm" in src)
check(u"r75 的「自动插销」已删除",
      u"AUTO_BACK_TICKS" not in src and u"primedAt" not in src)

print(u"== 2. 松手 / 被动中止 / 插销 ==")
check(u"拔销没拔完松手 → SAFE（销弹回）", u'"message.hexalunar_calamity.pin_slipped"' in src)
check(u"松手击发有提示 fuse_lit", u'"message.hexalunar_calamity.fuse_lit"' in src)
check(u"插销中松手 → 回到 PRIMED（销还没进去）",
      re.search(r"STATE_REINSERTING\)\s*\{[^}]*setPrimed\(stack, now\)", src, re.S) is not None)
check(u"被动中止（开界面 / 切手持物）不点火：serverCancelHold 只在 PULLING 时复位",
      re.search(r"serverCancelHold\(Player player\)[\s\S]{0,400}STATE_PULLING", src) is not None)

jfile = lambda *p: read(os.path.join(ROOT, u"src", u"main", u"java", u"cn", u"blockforge",
                                    u"generated", u"hexalunarcalamity", *p))
net = jfile(u"net", u"ModNetwork.java")
cli = jfile(u"client", u"ClientWeaponInput.java")
check(u"网络包有 HOLD_CANCEL", u"HOLD_CANCEL" in net)
check(u"客户端区分：真松手 RMB_UP、被动中止 HOLD_CANCEL",
      u"RMB_UP" in cli and u"HOLD_CANCEL" in cli)
check(u"服务端处理 HOLD_CANCEL", u"case HOLD_CANCEL -> GrenadeItem.serverCancelHold(player);" in net)

print(u"== 3. 语言文件 ==")
for name in ("zh_cn.json", "en_us.json"):
    with io.open(os.path.join(LANG, name), encoding="utf-8") as fh:
        text = fh.read()
    for key in (u"pin_slipped", u"fuse_lit", u"fuse_no_pin_back", u"pin_back",
                u"pin_pulled", u"pin_reinsert_hint", u"need_pin"):
        full = u"message.hexalunar_calamity." + key
        check(u"%s 有 %s" % (name, key), u'"%s"' % full in text)
    check(u"%s 已删掉 pin_autoback" % name,
          u'"message.hexalunar_calamity.pin_autoback"' not in text)

print(u"== 4. 状态机（对着需求逐条核对） ==")
rows = [
    (u"SAFE", u"按住右键 1 秒", u"PRIMED", u"销拔出，压杆仍被手压着（引信未点）"),
    (u"SAFE", u"拔销中途松手（<1 秒）", u"SAFE", u"销自己弹回去（pin_slipped）"),
    (u"PRIMED", u"★ 一松手（没及时按住 / 手滑）", u"ARMED", u"撞针击发、引信点燃（满 5 秒）"),
    (u"PRIMED", u"潜行 + 右键 1 秒", u"SAFE", u"手动插回保险销"),
    (u"PRIMED", u"左键", u"抛射体", u"压杆在出手瞬间脱落，引信从这一刻开始烧"),
    (u"REINSERTING", u"中途松手", u"PRIMED", u"销没进去，回到待投态"),
    (u"ARMED", u"左键及时丢出去", u"抛射体", u"接着剩下的时间烧（至少 5 tick）"),
    (u"ARMED", u"5 秒内没丢出去", u"掌心起爆", u"detonateInHand，自己吃满伤害"),
    (u"ARMED", u"收回背包 / 换到别的格子", u"继续烧", u"引信不会自己灭，到点爆在身上"),
    (u"ARMED", u"右键（想插销）", u"ARMED", u"来不及了 —— fuse_no_pin_back"),
    (u"任意", u"开界面 / 切手持物（被动中止）", u"不变", u"手还抓着，不算松手，不点火"),
    (u"任意", u"副手 + 主手是枪械", u"SAFE", u"被胳臂夹着，且丢不出去 ⇒ 不给必死局面"),
]
print(u"  %-12s %-28s %-8s %s" % (u"起态", u"事件", u"到态", u"说明"))
for a, b, c, d in rows:
    print(u"  %-12s %-28s %-8s %s" % (a, b, c, d))

print(u"")
print(u"结果：" + (u"全部通过" if ok else u"有 FAIL，需要修"))
sys.exit(0 if ok else 1)
