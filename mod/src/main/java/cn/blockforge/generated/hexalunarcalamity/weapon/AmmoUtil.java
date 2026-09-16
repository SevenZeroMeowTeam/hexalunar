package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.item.AmmoBoxItem;
import cn.blockforge.generated.hexalunarcalamity.item.CreativeAmmoBoxItem;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

/**
 * 弹药供给：优先副手/主手弹药盒（创造盒无限），其次背包。
 * 三种武器只消耗各自弹药，不混装。
 */
public final class AmmoUtil {

    public static int count(Player player, AmmoType type) {
        int n = countInventory(player, type.get());
        for (ItemStack hand : new ItemStack[]{player.getMainHandItem(), player.getOffhandItem()}) {
            if (hand.getItem() instanceof CreativeAmmoBoxItem) {
                AmmoType mode = CreativeAmmoBoxItem.modeFor(player);
                if (mode == type) return Integer.MAX_VALUE;
            } else if (hand.getItem() instanceof AmmoBoxItem box && box.type == type) {
                n += AmmoBoxItem.stored(hand);
            }
        }
        return n;
    }

    private static int countInventory(Player player, Item item) {
        int n = 0;
        for (ItemStack stack : player.getInventory().items) {
            if (stack.is(item)) n += stack.getCount();
        }
        return n;
    }

    /** 消耗 n 发弹药，成功返回 true */
    public static boolean consume(Player player, AmmoType type, int n) {
        if (player.isCreative()) return true;
        if (count(player, type) < n) return false;
        for (int i = 0; i < n; i++) consumeOne(player, type);
        return true;
    }

    private static void consumeOne(Player player, AmmoType type) {
        // 1. 创造盒无限
        for (ItemStack hand : new ItemStack[]{player.getOffhandItem(), player.getMainHandItem()}) {
            if (hand.getItem() instanceof CreativeAmmoBoxItem
                    && CreativeAmmoBoxItem.modeFor(player) == type) {
                return;
            }
        }
        // 2. 生存弹药盒内部库存（空时自动从背包补满）
        for (ItemStack hand : new ItemStack[]{player.getOffhandItem(), player.getMainHandItem()}) {
            if (hand.getItem() instanceof AmmoBoxItem box && box.type == type) {
                if (AmmoBoxItem.stored(hand) == 0) {
                    refillBox(player, hand, box);
                }
                if (AmmoBoxItem.stored(hand) > 0) {
                    AmmoBoxItem.take(hand, 1);
                    return;
                }
            }
        }
        // 3. 背包
        takeFromInventory(player, type.get(), 1);
    }

    private static void refillBox(Player player, ItemStack boxStack, AmmoBoxItem box) {
        int want = box.type.boxCapacity;
        int have = takeFromInventory(player, box.type.get(), want);
        AmmoBoxItem.put(boxStack, have);
    }

    /** 从手持弹药盒取弹（创造盒无限返回 want），返回实际取出数量 */
    public static int takeFromBox(Player player, AmmoType type, int want) {
        for (ItemStack hand : new ItemStack[]{player.getOffhandItem(), player.getMainHandItem()}) {
            if (hand.getItem() instanceof CreativeAmmoBoxItem
                    && CreativeAmmoBoxItem.modeFor(player) == type) {
                return want;
            }
            if (hand.getItem() instanceof AmmoBoxItem box && box.type == type) {
                return AmmoBoxItem.take(hand, want);
            }
        }
        return 0;
    }

    public static int takeFromInventory(Player player, Item item, int max) {
        int taken = 0;
        var slots = player.getInventory().items;
        for (int i = 0; i < slots.size() && taken < max; i++) {
            ItemStack stack = slots.get(i);
            if (!stack.is(item)) continue;
            int move = Math.min(stack.getCount(), max - taken);
            stack.shrink(move);
            taken += move;
            if (stack.isEmpty()) slots.set(i, ItemStack.EMPTY);
        }
        return taken;
    }

    /** 找出玩家手上武器对应的弹药类型 */
    @Nullable
    public static AmmoType weaponAmmoType(ItemStack weapon) {
        if (weapon.getItem() instanceof WeaponAmmo ammo) return ammo.ammoType();
        return null;
    }

    /** 玩家当前持有的模组武器（主手优先） */
    @Nullable
    public static ItemStack heldWeapon(Player player) {
        ItemStack main = player.getMainHandItem();
        if (main.getItem() instanceof WeaponAmmo) return main;
        ItemStack off = player.getOffhandItem();
        if (off.getItem() instanceof WeaponAmmo) return off;
        return null;
    }

    private AmmoUtil() {}
}
