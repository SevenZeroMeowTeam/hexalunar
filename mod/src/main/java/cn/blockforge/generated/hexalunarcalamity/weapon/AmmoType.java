package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import net.minecraft.world.item.Item;

import java.util.function.Supplier;

/** 三种互不混用的弹药类型 */
public enum AmmoType {
    BOLT("crossbow_bolt", ModItems.CROSSBOW_BOLT, 64, 0),
    ARROW("compound_arrow", ModItems.COMPOUND_ARROW, 96, 1),
    RIFLE("ammo_762", ModItems.AMMO_762, 300, 2),
    /** .338 拉普阿马格努姆：AWP 专用，与 7.62 不通用 */
    SNIPER("ammo_338", ModItems.AMMO_338, 120, 3),
    /** 7.62x59 步枪弹（★ r106）：莫辛-纳甘 / Kar98k 共用，与 AKM 的 7.62x39、AWP 的 .338 都不通用 */
    MOSIN("ammo_762_59", ModItems.AMMO_762_59, 150, 4),
    /** ★ r108 7.62x61 步枪弹：M1 加兰德专用（与 7.62x59 / 7.62x39 / .338 都不通用） */
    GARAND("ammo_762_61", ModItems.AMMO_762_61, 128, 5);

    /**
     * ★ r107：7.62x59 的**别名**（不是新的枚举常量 ⇒ {@code values()}、HUD 格位、弹药盒都不受影响）——
     * 这发弹按**口径**称呼更准确：它同时供莫辛-纳甘与 Kar98k 使用，而 {@link #MOSIN} 是按先落地的那把枪
     * 命名的。Kar98k 的代码一律写 {@code AmmoType.RIFLE_762_59}，指的就是同一发弹。
     */
    public static final AmmoType RIFLE_762_59 = MOSIN;

    /** ★ r108：7.62x61 的别名（同上一行的道理）——M1 加兰德的代码写 {@code AmmoType.RIFLE_762_61} */
    public static final AmmoType RIFLE_762_61 = GARAND;

    public final String id;
    public final Supplier<Item> item;
    public final int boxCapacity;
    /** hud_icons.png 中的图标格（每格 16px，横向编号） */
    public final int hudCell;

    AmmoType(String id, Supplier<Item> item, int boxCapacity, int hudCell) {
        this.id = id;
        this.item = item;
        this.boxCapacity = boxCapacity;
        this.hudCell = hudCell;
    }

    public Item get() {
        return item.get();
    }
}
