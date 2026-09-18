package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;

/**
 * 复合弓的客户端动画状态。
 *
 * <p>参照 SuperbWarfare（BOCEK 复合弓）的做法：动画不靠服务端触发，
 * 而是客户端每 tick 维护一组标志（它那边是 {@code ClientEventHandler.bowPull}），
 * 由物品的三个动画控制器读取后选动画：
 *
 * <ul>
 *   <li>拉弦 {@code pulling} → {@code thenPlayAndHold(animation.compound_bow.pull)}（拉满保持）</li>
 *   <li>放箭 {@code firing}（松开右键后的一小段窗口）→ {@code thenPlay(...fire)}</li>
 *   <li>搭箭 {@code reloading}（按 R 后的一小段窗口）→ {@code thenPlay(...reload)}</li>
 *   <li>冲刺 {@code sprinting} → {@code loop(...run / ...run_fast)}</li>
 *   <li>其余 → {@code loop(...idle)}</li>
 * </ul>
 *
 * <p>只在<b>第一人称、主手持弓</b>时才算“手持”，否则一律 idle ——
 * 避免背包里其它弓跟着一起动（GeckoLib 的物品动画是按物品种类共享的）。
 */
public final class BowAnimState {

    /** fire 动画 0.4s ≈ 8 tick */
    private static final int FIRE_TICKS = 8;
    /** reload 动画 0.35s ≈ 7 tick */
    private static final int RELOAD_TICKS = 7;

    private static int fireTicks;
    private static int reloadTicks;
    private static boolean wasPulling;

    /** 本地玩家主手拿着复合弓 */
    public static boolean held() {
        Player player = player();
        return player != null && player.getMainHandItem().getItem() instanceof CompoundBowItem;
    }

    /** 正拉弦（第一人称按住右键） */
    public static boolean pulling() {
        Player player = player();
        if (player == null || !held()) return false;
        if (!player.isUsingItem() || !(player.getUseItem().getItem() instanceof CompoundBowItem)) {
            return false;
        }
        return Minecraft.getInstance().options.getCameraType().isFirstPerson();
    }

    /** 冲刺中（跑动摆动） */
    public static boolean sprinting() {
        Player player = player();
        return player != null && held() && player.isSprinting() && player.onGround();
    }

    /** 疾跑（跑得更快时摆动幅度更大） */
    public static boolean sprintFast() {
        Player player = player();
        return player != null && player.isSprinting() && player.getFoodData().getFoodLevel() > 6;
    }

    public static boolean firing() {
        return fireTicks > 0;
    }

    public static boolean reloading() {
        return reloadTicks > 0;
    }

    /** R 键换箭时调用（客户端） */
    public static void triggerReload() {
        reloadTicks = RELOAD_TICKS;
    }

    /** 客户端每 tick：推进计时器，并把「松开右键」识别成一次放箭 */
    public static void tick() {
        if (fireTicks > 0) fireTicks--;
        if (reloadTicks > 0) reloadTicks--;
        boolean now = pulling();
        if (wasPulling && !now) {
            fireTicks = FIRE_TICKS;
        }
        wasPulling = now;
    }

    private static Player player() {
        return Minecraft.getInstance().player;
    }

    private BowAnimState() {
    }
}
