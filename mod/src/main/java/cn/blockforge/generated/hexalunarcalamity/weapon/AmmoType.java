package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import net.minecraft.world.item.Item;

import java.util.function.Supplier;

/** 三种互不混用的弹药类型 */
public enum AmmoType {
    BOLT("crossbow_bolt", ModItems.CROSSBOW_BOLT, 64, 0),
    ARROW("compound_arrow", ModItems.COMPOUND_ARROW, 96, 1),
    RIFLE("ammo_762", ModItems.AMMO_762, 300, 2);

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
