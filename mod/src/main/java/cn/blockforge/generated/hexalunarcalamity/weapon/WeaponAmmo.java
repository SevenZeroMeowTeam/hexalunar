package cn.blockforge.generated.hexalunarcalamity.weapon;

import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/** 可被弹药盒识别的武器接口 */
public interface WeaponAmmo {
    AmmoType ammoType();

    /**
     * 左键攻击（开火）的服务端入口：客户端左键按下 / 按住连发时通过
     * WeaponFire 包触发，在这里做真正的耗弹与射击。
     */
    default void serverFire(Player player, ItemStack stack, InteractionHand hand) {
    }

    /**
     * R 键手动装填的服务端入口：客户端按下装填键时通过 WeaponReload 包触发。
     * 默认无装填概念（弩/弓直接消耗背包弹药），步枪类按需覆写。
     */
    default void serverReload(Player player, ItemStack stack, InteractionHand hand) {
    }
}
