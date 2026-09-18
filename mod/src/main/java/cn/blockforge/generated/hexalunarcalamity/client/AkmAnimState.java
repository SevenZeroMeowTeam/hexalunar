package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * AKM 的客户端动画状态（照复合弓 {@code BowAnimState} 那套做法）。
 *
 * <p>不走服务端 {@code triggerAnim}（物品动画那样触发易丢包、有延迟），改为客户端每 tick
 * 维护计时窗口，由 {@link AkmRifleItem} 的动画控制器读取后选动画：
 *
 * <ul>
 *   <li>打出一发（弹匣数下降）→ {@code fire}（枪机后坐复进 + 后座上跳）</li>
 *   <li>打空归零 / 换弹完成 → {@code bolt_pull}（拉机柄上膛）</li>
 *   <li>换弹中（物品 NBT {@code HlcReloadUntil}）→ {@code reload}（退匣 → 新匣 → 释放枪机）</li>
 *   <li>刚切到手上 → {@code safety}（拨一次保险/快慢机）</li>
 *   <li>冲刺 → {@code run} / {@code run_fast}；其余 → {@code idle}</li>
 * </ul>
 */
public final class AkmAnimState {

    /** fire 动画 0.30s ≈ 6 tick */
    private static final int FIRE_TICKS = 7;
    /** bolt_pull 动画 0.80s ≈ 16 tick */
    private static final int BOLT_TICKS = 17;
    /** safety 动画 0.55s ≈ 11 tick */
    private static final int SAFETY_TICKS = 12;

    private static int fireTicks;
    private static int boltTicks;
    private static int safetyTicks;
    private static int lastMag = -1;
    private static boolean wasHeld;

    /** 本地玩家主手拿着 AKM */
    public static boolean held() {
        Player player = player();
        return player != null && player.getMainHandItem().getItem() instanceof AkmRifleItem;
    }

    public static boolean firing() {
        return fireTicks > 0;
    }

    public static boolean bolting() {
        return boltTicks > 0;
    }

    public static boolean safety() {
        return safetyTicks > 0;
    }

    /** 拉栓动画进度 0..1；没在拉栓返回 -1 */
    public static float boltProgress() {
        if (boltTicks <= 0) return -1.0F;
        return 1.0F - boltTicks / (float) BOLT_TICKS;
    }

    /** 正在换弹（读物品 NBT，客户端可见） */
    public static boolean reloading() {
        Player player = player();
        if (player == null || player.level() == null) return false;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof AkmRifleItem)) return false;
        return AkmRifleItem.reloadProgress(stack, player.level().getGameTime()) >= 0.0F;
    }

    /** 冲刺中（跑动摆动） */
    public static boolean sprinting() {
        Player player = player();
        return player != null && held() && player.isSprinting() && player.onGround();
    }

    /** 本地玩家正按住右键举枪瞄准（正在 use 这把 AKM） */
    public static boolean aiming() {
        Player player = player();
        if (player == null || !player.isUsingItem()) return false;
        return player.getUseItem().getItem() instanceof AkmRifleItem;
    }

    /**
     * 有动作动画在跑（开火 / 拉栓 / 换弹 / 拨保险）。
     *
     * <p>只有这些动画允许推 camera 空骨骼；其余时候必须把它清零，
     * 否则 GeckoLib 会把上一段动作的最后一帧留在骨骼上，镜头就被永久歪掉了。
     */
    public static boolean action() {
        return fireTicks > 0 || boltTicks > 0 || safetyTicks > 0 || reloading();
    }

    /** 疾跑（摆动幅度更大） */
    public static boolean sprintFast() {
        Player player = player();
        return player != null && sprinting() && player.getFoodData().getFoodLevel() > 6;
    }

    /** 客户端每 tick：推进计时窗口，并识别开火 / 打空 / 换弹完成 / 切枪 */
    public static void tick() {
        if (fireTicks > 0) fireTicks--;
        if (boltTicks > 0) boltTicks--;
        if (safetyTicks > 0) safetyTicks--;

        Player player = player();
        ItemStack stack = player == null ? ItemStack.EMPTY : player.getMainHandItem();
        if (!(stack.getItem() instanceof AkmRifleItem)) {
            lastMag = -1;
            wasHeld = false;
            return;
        }
        int mag = AkmRifleItem.mag(stack);
        if (!wasHeld) {                     // 刚切到手上：拨一次保险
            wasHeld = true;
            lastMag = mag;
            safetyTicks = SAFETY_TICKS;
            return;
        }
        if (lastMag >= 0 && mag < lastMag) {          // 打出一发
            fireTicks = FIRE_TICKS;
            if (mag == 0) boltTicks = BOLT_TICKS;     // 打空自动拉栓
        } else if (lastMag >= 0 && mag > lastMag) {   // 换弹完成：上膛
            boltTicks = BOLT_TICKS;
        }
        lastMag = mag;
    }

    private static Player player() {
        return Minecraft.getInstance().player;
    }

    private AkmAnimState() {
    }
}
