package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.net.ModNetwork;
import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoUtil;
import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * 弹药与换弹按键：<b>R 键＝换弹</b>（手持 AKM 时）。
 *
 * <p>左键开火由 {@link ClientWeaponInput} 统一处理，右键瞄准由各武器自身的 use() 进入，
 * 这里只负责把换弹请求发给服务端。
 */
@Mod.EventBusSubscriber(modid = HexaLunarCalamity.MOD_ID, value = Dist.CLIENT)
public final class ClientGunController {


    /** R 键＝装填（手持 AKM / 十字弩 / 复合弓时；复合弓是“搭箭”动画） */
    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        Player player = mc.player;
        ItemStack weapon = player == null ? null : AmmoUtil.heldWeapon(player);
        boolean holding = player != null && weapon != null && mc.screen == null && !mc.isPaused()
                && !player.isDeadOrDying()
                && (weapon.getItem() instanceof AkmRifleItem
                    || weapon.getItem() instanceof CrossbowWeaponItem
                    || weapon.getItem() instanceof cn.blockforge.generated
                            .hexalunarcalamity.weapon.CompoundBowItem);
        while (ModKeys.RELOAD.consumeClick()) {
            if (holding) {
                if (weapon != null && weapon.getItem() instanceof cn.blockforge.generated
                        .hexalunarcalamity.weapon.CompoundBowItem) {
                    BowAnimState.triggerReload();
                }
                ModNetwork.sendReload();
            }
        }
    }

    private ClientGunController() {}
}
