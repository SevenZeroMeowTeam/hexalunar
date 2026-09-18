package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * 手雷的客户端动画状态（同复合弓的 BowAnimState / SuperbWarfare 的 ClientEventHandler）。
 *
 * <p>拔销、压把弹开这两个是**连续动作**，直接读 {@link GrenadeItem} 已经算好的
 * {@code clientPullProgress} / {@code clientReinsertProgress}，
 * 由 {@link GrenadeGeoModel} 每帧程序化设置保险销与压把的骨骼（照 SuperbWarfare
 * BocekItemModel 用 bowPullPos 推骨骼的做法）。这里只维护投掷窗口与跑动判定。
 */
public final class GrenadeAnimState {

    /** throw 动画 0.3s ≈ 6 tick */
    private static final int THROW_TICKS = 6;

    private static int throwTicks;

    /** 本地玩家主手拿着手雷 */
    public static boolean held() {
        Player player = Minecraft.getInstance().player;
        return player != null && player.getMainHandItem().getItem() instanceof GrenadeItem;
    }

    /**
     * 压杆已脱落（= 引信点燃）。手里攥着时永远是 false：拔销只是把销抽出来，
     * 压杆仍被手压着，所以模型上压把不会弹开；只有出手那一瞬（{@link #throwing()}）才弹。
     */
    public static boolean armed() {
        Player player = Minecraft.getInstance().player;
        if (player == null) return false;
        ItemStack stack = player.getMainHandItem();
        return stack.getItem() instanceof GrenadeItem && GrenadeItem.isArmed(stack);
    }

    /** 拔销进度 0..1（按住右键），没在拔返回 -1 */
    public static float pullProgress() {
        return GrenadeItem.clientPullProgress;
    }

    /** 插回销进度 0..1，没在插返回 -1 */
    public static float reinsertProgress() {
        return GrenadeItem.clientReinsertProgress;
    }

    public static boolean throwing() {
        return throwTicks > 0;
    }

    public static boolean sprinting() {
        Player player = Minecraft.getInstance().player;
        return player != null && held() && player.isSprinting() && player.onGround();
    }

    public static boolean sprintFast() {
        Player player = Minecraft.getInstance().player;
        return player != null && player.isSprinting() && player.getFoodData().getFoodLevel() > 6;
    }

    /** 左键出手那一瞬（由 {@link ClientWeaponInput} 调用）：压杆脱手、甩臂扔出去 */
    public static void onThrow() {
        throwTicks = THROW_TICKS;
    }

    /** 客户端每 tick：推进投掷动作窗口 */
    public static void tick() {
        if (throwTicks > 0) throwTicks--;
    }

    private GrenadeAnimState() {
    }
}
