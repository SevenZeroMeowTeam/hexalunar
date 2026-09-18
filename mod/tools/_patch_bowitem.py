#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 CompoundBowItem 的 GeckoLib 接线换成 SuperbWarfare BOCEK 式的三控制器谓词写法。"""
import io

P = ('src/main/java/cn/blockforge/generated/hexalunarcalamity/weapon/CompoundBowItem.java')
s = io.open(P, encoding='utf-8').read()
n = 0

# 1) 补 import
old = ('import software.bernie.geckolib.core.animation.AnimationController;\n'
       'import software.bernie.geckolib.core.animation.AnimatableManager;')
new = ('import software.bernie.geckolib.core.animation.AnimationController;\n'
       'import software.bernie.geckolib.core.animation.AnimationState;\n'
       'import software.bernie.geckolib.core.animation.AnimatableManager;')
if old in s:
    s = s.replace(old, new, 1)
    s = s.replace('import software.bernie.geckolib.core.animation.RawAnimation;',
                  'import software.bernie.geckolib.core.animation.RawAnimation;\n'
                  'import software.bernie.geckolib.core.object.PlayState;', 1)
    s = s.replace('import net.minecraft.server.level.ServerLevel;\n', '', 1)
    n += 1

# 2) 常量 + 控制器
old_ctrl = '''    /** GeckoLib 控制器：main = 待机循环，action = 换弹 / 拉弦 / 放箭 */
    public static final String GEO_CONTROLLER = "main";
    public static final String GEO_ACTION = "action";
'''
new_ctrl = '''    /** 动画名前缀与控制器名（规矩同 SuperbWarfare：animation.<id>.<state>） */
    public static final String ANIM_PREFIX = "animation.compound_bow.";
    public static final String C_IDLE = "idleController";
    public static final String C_FIRE = "fireController";
    public static final String C_RELOAD = "reloadController";
'''
if old_ctrl in s:
    s = s.replace(old_ctrl, new_ctrl, 1)
    n += 1

old_reg = '''        controllers.add(new AnimationController<>(this, GEO_CONTROLLER, 2,
                state -> state.setAndContinue(RawAnimation.begin().thenLoop("idle"))));
        controllers.add(new AnimationController<>(this, GEO_ACTION, 1,
                state -> state.setAndContinue(RawAnimation.begin().thenLoop("empty"))));
    }
'''
new_reg = '''        controllers.add(new AnimationController<>(this, C_IDLE, 3, this::idlePredicate));
        controllers.add(new AnimationController<>(this, C_FIRE, 0, this::firePredicate));
        controllers.add(new AnimationController<>(this, C_RELOAD, 0, this::reloadPredicate));
    }

    private static final String BOW_STATE =
            "cn.blockforge.generated.hexalunarcalamity.client.BowAnimState";

    /** 待机 / 拉弦 / 跑动；拉弦用 thenPlayAndHold，拉满后弦不会自己回弹 */
    private PlayState idlePredicate(AnimationState<CompoundBowItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (pulling()) {
            return event.setAndContinue(RawAnimation.begin().thenPlayAndHold(ANIM_PREFIX + "pull"));
        }
        if (sprinting()) {
            return event.setAndContinue(RawAnimation.begin().thenLoop(
                    ANIM_PREFIX + (sprintFast() ? "run_fast" : "run")));
        }
        return event.setAndContinue(RawAnimation.begin().thenLoop(ANIM_PREFIX + "idle"));
    }

    /** 放箭：单独一层，播完即停，不占用 idle 那层 */
    private PlayState firePredicate(AnimationState<CompoundBowItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (held() && firing()) {
            return event.setAndContinue(RawAnimation.begin().thenPlay(ANIM_PREFIX + "fire"));
        }
        return PlayState.STOP;
    }

    /** 搭箭（换弹） */
    private PlayState reloadPredicate(AnimationState<CompoundBowItem> event) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return PlayState.STOP;
        if (held() && reloading()) {
            return event.setAndContinue(RawAnimation.begin().thenPlay(ANIM_PREFIX + "reload"));
        }
        return PlayState.STOP;
    }

    // 客户端标志都在 client.BowAnimState（客户端类），这里只做布尔转发，
    // 免得把 Minecraft 引到通用侧（专用服务器会 NoClassDefFoundError）
    private static boolean held() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.held();
    }

    private static boolean pulling() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.pulling();
    }

    private static boolean sprinting() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.sprinting();
    }

    private static boolean sprintFast() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.sprintFast();
    }

    private static boolean firing() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.firing();
    }

    private static boolean reloading() {
        return cn.blockforge.generated.hexalunarcalamity.client.BowAnimState.reloading();
    }
'''
if old_reg in s:
    s = s.replace(old_reg, new_reg, 1)
    n += 1

# 3) use() 里的服务端触发去掉（改由客户端谓词驱动）
old_trig = '''        if (level instanceof ServerLevel serverLevel) {
            triggerAnim(player, GeoItem.getOrAssignId(stack, serverLevel), GEO_ACTION, "draw");
        }
'''
if old_trig in s:
    s = s.replace(old_trig, '', 1)
    n += 1

io.open(P, 'w', encoding='utf-8').write(s)
print('CompoundBowItem 补丁完成（%d 处）' % n)
for k in ['C_IDLE', 'idlePredicate', 'PlayState', 'triggerAnim', 'ServerLevel', 'BOW_STATE']:
    print('  %-14s %s' % (k, k in s))
