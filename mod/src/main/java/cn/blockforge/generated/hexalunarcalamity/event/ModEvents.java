package cn.blockforge.generated.hexalunarcalamity.event;

import cn.blockforge.generated.hexalunarcalamity.moon.MoonManager;
import cn.blockforge.generated.hexalunarcalamity.moon.MoonPhase;
import cn.blockforge.generated.hexalunarcalamity.net.ModNetwork;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** 命中反馈与登录月相同步 */
@Mod.EventBusSubscriber(modid = cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity.MOD_ID)
public final class ModEvents {

    /** 玩家攻击命中：白色命中标记 */
    @SubscribeEvent
    public static void onAttack(LivingAttackEvent event) {
        if (event.getSource().getEntity() instanceof ServerPlayer player
                && event.getEntity() != player && !(event.getEntity() instanceof Player)) {
            ModNetwork.hitMarker(player, false);
        }
    }

    /** 玩家造成击杀：红色标记 */
    @SubscribeEvent
    public static void onDeath(LivingDeathEvent event) {
        if (event.getSource().getEntity() instanceof ServerPlayer player
                && !(event.getEntity() instanceof Player)) {
            ModNetwork.hitMarker(player, true);
        }
    }

    /** 重进世界时把当前月相推给客户端 */
    @SubscribeEvent
    public static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer sp && sp.level() instanceof ServerLevel server) {
            MoonPhase phase = MoonManager.current(server);
            ModNetwork.syncToPlayer(sp, MoonPhase.indexOf(phase), MoonManager.get(server).nightCount);
        }
    }

    /** 死亡不掉落月相进度，但重生时同步一次 */
    @SubscribeEvent
    public static void onRespawn(PlayerEvent.PlayerRespawnEvent event) {
        if (event.getEntity() instanceof ServerPlayer sp && sp.level() instanceof ServerLevel server) {
            MoonPhase phase = MoonManager.current(server);
            ModNetwork.syncToPlayer(sp, MoonPhase.indexOf(phase), MoonManager.get(server).nightCount);
        }
    }

    /** 手雷：拔销进度、引信倒计时、离开手掌自动插回保险销（只在服务端结算） */
    @SubscribeEvent
    public static void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase != TickEvent.Phase.END
                || event.side != net.minecraftforge.fml.LogicalSide.SERVER) return;
        if (!(event.player instanceof ServerPlayer player) || player.isRemoved()) return;
        cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem.serverTick(player);
    }

    private static boolean alive(LivingEntity e) {
        return e.isAlive();
    }

    private ModEvents() {}
}
