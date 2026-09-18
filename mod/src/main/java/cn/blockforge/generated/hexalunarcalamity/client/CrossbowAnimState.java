package cn.blockforge.generated.hexalunarcalamity.client;

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
