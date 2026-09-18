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
            // ★ r78 紧急投掷：手里攚着一颗已拔销 / 引信在烧的手雷时，R 不再是换弹，而是立刻丢出去
            if (player != null && mc.screen == null && !mc.isPaused() && !player.isDeadOrDying()
                    && throwLiveGrenade(player)) {
                continue;
            }
            if (holding) {
                if (weapon != null && weapon.getItem() instanceof cn.blockforge.generated
                        .hexalunarcalamity.weapon.CompoundBowItem) {
                    BowAnimState.triggerReload();
                }
                ModNetwork.sendReload();
            }
        }
    }

    /**
     * ★ r78：按 R 紧急投掷 —— 只要手上（主手或副手）有一颗已拔销 / 引信在烧的手雷就丢它。
     *
     * <p>专门解决「拔完销正好碰到敌对生物、主手还举着枪」的处境：不用先切回雷，按 R 就行。
     */
    private static boolean throwLiveGrenade(Player player) {
        ItemStack stack = cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem
                .grenadeInEitherHand(player);
        if (stack == null || !cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem
                .isPinOut(stack)) {
            return false;
        }
        ModNetwork.CHANNEL.sendToServer(
                new ModNetwork.GrenadeAction(ModNetwork.GrenadeAction.THROW));
        GrenadeAnimState.onThrow();
        WeaponAnim.onThrow();
        return true;
    }

    private ClientGunController() {}
}
