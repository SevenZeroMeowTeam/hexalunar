#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""给 CrossbowWeaponItem 接上 GeckoLib：GeoItem + 两个控制器 + 客户端扩展。"""
import io
import json

P = 'src/main/java/cn/blockforge/generated/hexalunarcalamity/weapon/CrossbowWeaponItem.java'
s = io.open(P, encoding='utf-8').read()
n = 0

imp_anchor = 'import net.minecraft.world.level.Level;'
imp_add = ('import net.minecraft.world.level.Level;\n'
           'import software.bernie.geckolib.animatable.GeoItem;\n'
           'import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;\n'
           'import software.bernie.geckolib.core.animation.AnimationController;\n'
           'import software.bernie.geckolib.core.animation.AnimationState;\n'
           'import software.bernie.geckolib.core.animation.AnimatableManager;\n'
           'import software.bernie.geckolib.core.animation.RawAnimation;\n'
           'import software.bernie.geckolib.core.object.PlayState;\n'
           'import software.bernie.geckolib.util.GeckoLibUtil;')
if imp_anchor in s and 'GeoItem' not in s:
    s = s.replace(imp_anchor, imp_add, 1)
    n += 1

old_cls = 'public class CrossbowWeaponItem extends Item implements WeaponAmmo {'
new_cls = '''public class CrossbowWeaponItem extends Item implements WeaponAmmo, GeoItem {

    /** 动画名前缀与控制器名（照 SuperbWarfare BOCEK 规范：animation.<id>.<state>） */
    public static final String ANIM_PREFIX = "animation.crossbow.";
    public static final String C_MOVE = "moveController";
    public static final String C_FIRE = "fireController";

    private final AnimatableInstanceCache geoCache = GeckoLibUtil.createInstanceCache(this);

    // ------------------------------------------------------------ GeckoLib
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, C_MOVE, 3, this::movePredicate));
        controllers.add(new AnimationController<>(this, C_FIRE, 0, this::firePredicate));
    }

    /** 待机 / 跑动摆动（拉弦装弹是连续的，在 CrossbowGeoModel 里按 reloadProgress 程序化驱动） */
    private PlayState movePredicate(AnimationState<CrossbowWeaponItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (sprintIng()) {
            return event.setAndContinue(RawAnimation.begin().thenLoop(
                    ANIM_PREFIX + (sprintFastNow() ? "run_fast" : "run")));
        }
        return event.setAndContinue(RawAnimation.begin().thenLoop(ANIM_PREFIX + "idle"));
    }

    /** 放箭：单独一层，播完即停 */
    private PlayState firePredicate(AnimationState<CrossbowWeaponItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (cn.blockforge.generated.hexalunarcalamity.client.CrossbowAnimState.firing()) {
            return event.setAndContinue(RawAnimation.begin().thenPlay(ANIM_PREFIX + "fire"));
        }
        return PlayState.STOP;
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return geoCache;
    }

    private static boolean sprintIng() {
        return cn.blockforge.generated.hexalunarcalamity.client.CrossbowAnimState.sprinting();
    }

    private static boolean sprintFastNow() {
        return cn.blockforge.generated.hexalunarcalamity.client.CrossbowAnimState.sprintFast();
    }'''
if old_cls in s:
    s = s.replace(old_cls, new_cls, 1)
    n += 1

old_ic = ('        consumer.accept(cn.blockforge.generated.hexalunarcalamity.client.'
          'WeaponArmPose.CROSSBOW);')
new_ic = ('        consumer.accept(cn.blockforge.generated.hexalunarcalamity.client.'
          'CrossbowItemClientExtensions.INSTANCE);')
if old_ic in s:
    s = s.replace(old_ic, new_ic, 1)
    n += 1

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('CrossbowWeaponItem 补丁 %d 处；GeoItem=%s 控制器=%s 扩展=%s'
      % (n, 'implements WeaponAmmo, GeoItem' in s, 'C_MOVE' in s,
         'CrossbowItemClientExtensions.INSTANCE' in s))

# 客户端状态（放箭窗口 + 跑动判定）
C = 'src/main/java/cn/blockforge/generated/hexalunarcalamity/client/CrossbowAnimState.java'
io.open(C, 'w', encoding='utf-8', newline='').write('''package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * 十字弩的客户端动画状态（同复合弓 BowAnimState / 手雷 GrenadeAnimState 的写法）。
 *
 * <p>拉弦装弹是连续动作，由 CrossbowGeoModel 按 reloadProgress 程序化驱动，
 * 这里只维护「放箭」的一小段窗口与跑动判定。
 */
public final class CrossbowAnimState {

    /** fire 动画 0.32s ≈ 7 tick */
    private static final int FIRE_TICKS = 7;

    private static int fireTicks;
    private static boolean wasCocked;

    public static boolean held() {
        Player player = Minecraft.getInstance().player;
        if (player == null) return false;
        return player.getMainHandItem().getItem() instanceof CrossbowWeaponItem
                || player.getOffhandItem().getItem() instanceof CrossbowWeaponItem;
    }

    public static boolean firing() {
        return fireTicks > 0;
    }

    public static boolean sprinting() {
        Player player = Minecraft.getInstance().player;
        return player != null && held() && player.isSprinting() && player.onGround();
    }

    public static boolean sprintFast() {
        Player player = Minecraft.getInstance().player;
        return player != null && player.isSprinting() && player.getFoodData().getFoodLevel() > 6;
    }

    /** 每客户端 tick：从「已上弦」变成「未上弦」＝ 放箭了 */
    public static void tick() {
        if (fireTicks > 0) fireTicks--;
        Player player = Minecraft.getInstance().player;
        boolean cocked = false;
        if (player != null) {
            ItemStack stack = player.getMainHandItem();
            if (!(stack.getItem() instanceof CrossbowWeaponItem)) {
                stack = player.getOffhandItem();
            }
            cocked = stack.getItem() instanceof CrossbowWeaponItem
                    && CrossbowWeaponItem.cocked(stack);
        }
        if (wasCocked && !cocked) {
            fireTicks = FIRE_TICKS;
        }
        wasCocked = cocked;
    }

    private CrossbowAnimState() {
    }
}
''')
print('CrossbowAnimState 已写')

# 客户端 tick 里推进
E = 'src/main/java/cn/blockforge/generated/hexalunarcalamity/client/ClientEvents.java'
t = io.open(E, encoding='utf-8').read()
if 'CrossbowAnimState.tick();' not in t:
    t = t.replace('        GrenadeAnimState.tick();',
                  '        GrenadeAnimState.tick();\n        CrossbowAnimState.tick();', 1)
    io.open(E, 'w', encoding='utf-8', newline='').write(t)
    print('ClientEvents 已加 CrossbowAnimState.tick()')
else:
    print('ClientEvents 已有')

# 物品模型改 builtin/entity
M = 'src/main/resources/assets/hexalunar_calamity/models/item/crossbow.json'
m = json.load(io.open(M, encoding='utf-8'))
display = m.get('display') or {}
out = {'parent': 'builtin/entity', 'gui_light': 'front', 'display': display}
json.dump(out, io.open(M, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('crossbow.json -> builtin/entity（保留 display）')

# 注册点排除 OBJ 动画包装
D = 'src/main/java/cn/blockforge/generated/hexalunarcalamity/client/ModClient.java'
d = io.open(D, encoding='utf-8').read()
old_k = '''        if (path.startsWith("crossbow") || path.contains("crossbow_pulling")) {
            return WeaponAnim.Kind.CROSSBOW;
        }'''
new_k = '''        // 十字弩也改 GeckoLib 骨骼渲染（CrossbowGeoRenderer + geo/crossbow_geo.geo.json），
        // 拉弦装弹由 CrossbowGeoModel 程序化驱动，不再走 OBJ 分件/display 包装
        if (path.startsWith("crossbow") || path.contains("crossbow_pulling")) return null;'''
if old_k in d:
    d = d.replace(old_k, new_k, 1)
    io.open(D, 'w', encoding='utf-8', newline='').write(d)
    print('ModClient 已排除 crossbow')
else:
    print('ModClient 锚点未匹配，需手工检查')
