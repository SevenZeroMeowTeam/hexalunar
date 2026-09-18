package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * 枪械瞄具（可装在 AKM 顶部导轨上）。用物品 NBT 记录装了哪个。
 *
 * <p>三种状态：
 * <ul>
 *   <li>{@link #IRON} 机械瞄具（默认）：照门顶—准星顶那条线在 Y=3.44</li>
 *   <li>{@link #DOT} 红点：红点圆心 Y=3.79 —— 举枪时把<b>红点</b>顶到准星上，
 *       而且还能看到枪本体（只在屏幕中心画一个红点）</li>
 *   <li>{@link #SCOPE} 4 倍镜：光轴 Y=4.00 —— 和十字弩一样整屏开镜（视野 1/4 + 圆形镜筒）</li>
 * </ul>
 *
 * <p>装配方式：<b>潜行 + 右键</b>，副手拿瞄具 = 装上（消耗一个）；空手 = 拆下（还给你）。
 * 平时右键仍然是举枪瞄准。
 */
public final class Sights {

    public static final int IRON = 0;
    public static final int DOT = 1;
    public static final int SCOPE = 2;

    /** 物品 NBT 键 */
    public static final String TAG = "HlcSight";

    public static int sight(ItemStack stack) {
        CompoundTag tag = stack == null ? null : stack.getTag();
        if (tag == null || !tag.contains(TAG)) return IRON;
        int v = tag.getInt(TAG);
        return v < IRON || v > SCOPE ? IRON : v;
    }

    public static void set(ItemStack stack, int value) {
        if (stack == null || stack.isEmpty()) return;
        if (value <= IRON) {
            CompoundTag tag = stack.getTag();
            if (tag != null) tag.remove(TAG);
            return;
        }
        stack.getOrCreateTag().putInt(TAG, value);
    }

    /** 手上的物品是哪一档瞄具（不是瞄具返回 IRON） */
    public static int fromItem(Item item) {
        if (item == ModItems.RED_DOT_SIGHT.get()) return DOT;
        if (item == ModItems.SCOPE_4X.get()) return SCOPE;
        return IRON;
    }

    /** 拆下来时还给玩家的那个物品 */
    public static ItemStack itemOf(int sight) {
        return switch (sight) {
            case DOT -> new ItemStack(ModItems.RED_DOT_SIGHT.get());
            case SCOPE -> new ItemStack(ModItems.SCOPE_4X.get());
            default -> ItemStack.EMPTY;
        };
    }

    public static String key(int sight) {
        return switch (sight) {
            case DOT -> "tooltip.hexalunar_calamity.sight_dot";
            case SCOPE -> "tooltip.hexalunar_calamity.sight_scope";
            default -> "tooltip.hexalunar_calamity.sight_iron";
        };
    }

    private Sights() {
    }
}
