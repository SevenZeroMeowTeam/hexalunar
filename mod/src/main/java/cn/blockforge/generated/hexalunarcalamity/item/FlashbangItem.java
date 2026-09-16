package cn.blockforge.generated.hexalunarcalamity.item;

import net.minecraft.world.item.Item;

/**
 * 震爆弹：拔销 1 秒、引信 5 秒，爆点不炸方块不破片，
 * 靠强光和巨响让范围内生物眩晕（几乎无法移动）并致盲。
 */
public class FlashbangItem extends GrenadeItem {

    public FlashbangItem(Properties properties) {
        super(properties, Kind.FLASH, 1.25F);
    }
}
