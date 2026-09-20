package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.MosinRifleItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * 莫辛-纳甘的客户端便捷查询（动画控制器 + {@link MosinGeoModel} 共用）。
 *
 * <p>与 {@link AwpAnimState} / {@link Kar98kAnimState} 同一套：动作进度**不在这里维护**，
 * 拉栓（{@code HlcBoltUntil}）、逐发压弹（{@code HlcLoadAt / HlcLoadNeed}）、
 * 击发窗口（{@code HlcFireAt}）全部读物品 NBT —— 服务端写、客户端读同一份，
 * 不会出现「动画演完了动作还没结束」的错位。这里只负责「谁拿着枪」这类本地状态。
 */
public final class MosinAnimState {

    private MosinAnimState() {
    }

    public static long now() {
        ClientLevel level = Minecraft.getInstance().level;
        return level == null ? 0L : level.getGameTime();
    }

    /** 本地玩家主手的莫辛（不是它返回 null） */
    public static ItemStack heldStack() {
        Player player = Minecraft.getInstance().player;
        if (player == null) return null;
        ItemStack stack = player.getMainHandItem();
        return stack.getItem() instanceof MosinRifleItem ? stack : null;
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

    /** 正按住右键抵肩瞄准（正在 use 这把莫辛） */
    public static boolean aiming() {
        Player player = Minecraft.getInstance().player;
        if (player == null || !player.isUsingItem()) return false;
        return player.getUseItem().getItem() instanceof MosinRifleItem;
    }
}
