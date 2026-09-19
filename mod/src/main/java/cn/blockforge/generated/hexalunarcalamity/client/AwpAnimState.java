package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * AWP 的客户端便捷查询（骨骼动画控制器 + {@link AwpGeoModel} 共用）。
 *
 * <p>动作进度**不在这里维护**：换弹 / 拉栓 / 击发的窗口全部读物品 NBT
 * （{@code HlcReloadUntil} / {@code HlcBoltUntil} / {@code HlcFireAt}），
 * 服务端写、客户端读同一份，永远不会出现「动画演完了动作还没结束」的错位。
 * 这里只负责「谁拿着枪」这类本地状态。
 */
public final class AwpAnimState {

    private AwpAnimState() {
    }

    public static long now() {
        ClientLevel level = Minecraft.getInstance().level;
        return level == null ? 0L : level.getGameTime();
    }

    /** 本地玩家主手的 AWP（不是 AWP 返回 null） */
    public static ItemStack heldStack() {
        Player player = Minecraft.getInstance().player;
        if (player == null) return null;
        ItemStack stack = player.getMainHandItem();
        return stack.getItem() instanceof AwpRifleItem ? stack : null;
    }

    public static boolean held() {
        return heldStack() != null;
    }

    /** 冲刺中（跑动摆动） */
    public static boolean sprinting() {
        Player player = Minecraft.getInstance().player;
        return player != null && held() && player.isSprinting() && player.onGround();
    }

    /** 疾跑（摆动更大） */
    public static boolean sprintFast() {
        Player player = Minecraft.getInstance().player;
        return player != null && sprinting() && player.getFoodData().getFoodLevel() > 6;
    }

    /** 正按住右键抵肩瞄准（正在 use 这把 AWP） */
    public static boolean aiming() {
        Player player = Minecraft.getInstance().player;
        if (player == null || !player.isUsingItem()) return false;
        return player.getUseItem().getItem() instanceof AwpRifleItem;
    }
}
