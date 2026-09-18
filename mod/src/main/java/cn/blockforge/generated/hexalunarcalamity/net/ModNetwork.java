package cn.blockforge.generated.hexalunarcalamity.net;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.client.ClientGrenadeState;
import cn.blockforge.generated.hexalunarcalamity.client.ClientMoonState;
import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import net.minecraft.client.Minecraft;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.simple.SimpleChannel;

import java.util.function.Supplier;

/** 模组网络通道：月相同步、命中反馈、武器与手雷操作 */
public final class ModNetwork {
    private static final String PROTOCOL = "1";
    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            ResourceLocation.fromNamespaceAndPath(HexaLunarCalamity.MOD_ID, "main"),
            () -> PROTOCOL, PROTOCOL::equals, PROTOCOL::equals);

    private static int index = 0;

    public static void init() {
        CHANNEL.registerMessage(index++, MoonPhaseSync.class,
                MoonPhaseSync::encode, MoonPhaseSync::decode, MoonPhaseSync::handle);
        CHANNEL.registerMessage(index++, HitMarker.class,
                HitMarker::encode, HitMarker::decode, HitMarker::handle);
        CHANNEL.registerMessage(index++, WeaponFire.class,
                WeaponFire::encode, WeaponFire::decode, WeaponFire::handle);
        CHANNEL.registerMessage(index++, WeaponReload.class,
                WeaponReload::encode, WeaponReload::decode, WeaponReload::handle);
        CHANNEL.registerMessage(index++, GrenadeAction.class,
                GrenadeAction::encode, GrenadeAction::decode, GrenadeAction::handle);
        CHANNEL.registerMessage(index++, FlashBang.class,
                FlashBang::encode, FlashBang::decode, FlashBang::handle);
    }

    public static void syncToPlayer(ServerPlayer player, int phaseIndex, long night) {
        CHANNEL.send(PacketDistributor.PLAYER.with(() -> player), new MoonPhaseSync(phaseIndex, night));
    }

    public static void syncToAll(int phaseIndex, long night) {
        CHANNEL.send(PacketDistributor.ALL.noArg(), new MoonPhaseSync(phaseIndex, night));
    }

    public static void hitMarker(ServerPlayer player, boolean kill) {
        CHANNEL.send(PacketDistributor.PLAYER.with(() -> player), new HitMarker(kill));
    }

    /** 客户端 → 服务端：请求装填（R 键） */
    public static void sendReload() {
        CHANNEL.sendToServer(new WeaponReload());
    }

    /** 震爆弹打到谁就只发给谁：白光强度 0..1（越近越强，隔墙更弱） */
    public static void flash(Player player, float strength) {
        if (player instanceof ServerPlayer sp) {
            CHANNEL.send(PacketDistributor.PLAYER.with(() -> sp), new FlashBang(strength));
        }
    }

    /** 月相变化同步包 */
    public record MoonPhaseSync(int phaseIndex, long night) {
        public static void encode(MoonPhaseSync msg, FriendlyByteBuf buf) {
            buf.writeVarInt(msg.phaseIndex + 1);
            buf.writeVarLong(msg.night);
        }

        public static MoonPhaseSync decode(FriendlyByteBuf buf) {
            return new MoonPhaseSync(buf.readVarInt() - 1, buf.readVarLong());
        }

        public static void handle(MoonPhaseSync msg, Supplier<NetworkEvent.Context> ctx) {
            NetworkEvent.Context context = ctx.get();
            context.enqueueWork(() -> DistExecutor.unsafeRunWhenOn(net.minecraftforge.api.distmarker.Dist.CLIENT,
                    () -> () -> ClientMoonState.apply(msg.phaseIndex(), msg.night(), Minecraft.getInstance())));
            context.setPacketHandled(true);
        }
    }

    /** 命中/击杀反馈包 */
    public record HitMarker(boolean kill) {
        public static void encode(HitMarker msg, FriendlyByteBuf buf) {
            buf.writeBoolean(msg.kill);
        }

        public static HitMarker decode(FriendlyByteBuf buf) {
            return new HitMarker(buf.readBoolean());
        }

        public static void handle(HitMarker msg, Supplier<NetworkEvent.Context> ctx) {
            NetworkEvent.Context context = ctx.get();
            context.enqueueWork(() -> DistExecutor.unsafeRunWhenOn(net.minecraftforge.api.distmarker.Dist.CLIENT,
                    () -> () -> ClientMoonState.showHitMarker(msg.kill())));
            context.setPacketHandled(true);
        }
    }

    /** 左键开火请求包（客户端 → 服务端） */
    public record WeaponFire() {
        public static void encode(WeaponFire msg, FriendlyByteBuf buf) {
        }

        public static WeaponFire decode(FriendlyByteBuf buf) {
            return new WeaponFire();
        }

        public static void handle(WeaponFire msg, Supplier<NetworkEvent.Context> ctx) {
            NetworkEvent.Context context = ctx.get();
            context.enqueueWork(() -> {
                ServerPlayer player = context.getSender();
                if (player == null) return;
                net.minecraft.world.item.ItemStack weapon =
                        cn.blockforge.generated.hexalunarcalamity.weapon.AmmoUtil.heldWeapon(player);
                // 客户端与服务器可能错开一帧（点完枪立刻切手），这里必须判空
                if (weapon == null) return;
                if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon.WeaponAmmo ammo) {
                    net.minecraft.world.InteractionHand hand =
                            weapon == player.getMainHandItem()
                                    ? net.minecraft.world.InteractionHand.MAIN_HAND
                                    : net.minecraft.world.InteractionHand.OFF_HAND;
                    ammo.serverFire(player, weapon, hand);
                }
            });
            context.setPacketHandled(true);
        }
    }

    /** R 键手动装填请求包（客户端 → 服务端） */
    public record WeaponReload() {
        public static void encode(WeaponReload msg, FriendlyByteBuf buf) {
        }

        public static WeaponReload decode(FriendlyByteBuf buf) {
            return new WeaponReload();
        }

        public static void handle(WeaponReload msg, Supplier<NetworkEvent.Context> ctx) {
            NetworkEvent.Context context = ctx.get();
            context.enqueueWork(() -> {
                ServerPlayer player = context.getSender();
                if (player == null) return;
                net.minecraft.world.item.ItemStack weapon =
                        cn.blockforge.generated.hexalunarcalamity.weapon.AmmoUtil.heldWeapon(player);
                if (weapon == null) return;
                if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon.WeaponAmmo ammo) {
                    net.minecraft.world.InteractionHand hand =
                            weapon == player.getMainHandItem()
                                    ? net.minecraft.world.InteractionHand.MAIN_HAND
                                    : net.minecraft.world.InteractionHand.OFF_HAND;
                    ammo.serverReload(player, weapon, hand);
                }
            });
            context.setPacketHandled(true);
        }
    }

    /**
     * 手雷操作包（客户端 → 服务端）。
     *
     * <p>客户端只上报按键，「这次按住右键是拔销还是把销插回去」「左键能不能丢出去」
     * 都由服务端按手雷当前状态裁决，作弊客户端改不了状态机。
     */
    public record GrenadeAction(int action) {
        /** 右键按下 */
        public static final int RMB_DOWN = 0;
        /** 右键松开 */
        public static final int RMB_UP = 1;
        /** 左键出手投掷 */
        public static final int THROW = 2;
        /** 按住被被动中止（开界面 / 切手持物 / 旁观）—— 手还抓着，不当作松手 */
        public static final int HOLD_CANCEL = 3;

        public static void encode(GrenadeAction msg, FriendlyByteBuf buf) {
            buf.writeVarInt(msg.action);
        }

        public static GrenadeAction decode(FriendlyByteBuf buf) {
            return new GrenadeAction(buf.readVarInt());
        }

        public static void handle(GrenadeAction msg, Supplier<NetworkEvent.Context> ctx) {
            NetworkEvent.Context context = ctx.get();
            context.enqueueWork(() -> {
                ServerPlayer player = context.getSender();
                if (player == null) return;
                switch (msg.action) {
                    case RMB_DOWN -> GrenadeItem.serverBeginHold(player);
                    case RMB_UP -> GrenadeItem.serverEndHold(player);
                    case HOLD_CANCEL -> GrenadeItem.serverCancelHold(player);
                    case THROW -> GrenadeItem.serverThrow(player);
                    default -> {
                    }
                }
            });
            context.setPacketHandled(true);
        }
    }

    /** 震爆弹命中反馈包（服务端 → 客户端）：只发给被震到的那个人 */
    public record FlashBang(float strength) {
        public static void encode(FlashBang msg, FriendlyByteBuf buf) {
            buf.writeFloat(msg.strength);
        }

        public static FlashBang decode(FriendlyByteBuf buf) {
            return new FlashBang(buf.readFloat());
        }

        public static void handle(FlashBang msg, Supplier<NetworkEvent.Context> ctx) {
            NetworkEvent.Context context = ctx.get();
            context.enqueueWork(() -> DistExecutor.unsafeRunWhenOn(net.minecraftforge.api.distmarker.Dist.CLIENT,
                    () -> () -> ClientGrenadeState.onFlash(msg.strength())));
            context.setPacketHandled(true);
        }
    }

    private ModNetwork() {}
}
