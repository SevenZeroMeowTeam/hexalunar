package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.net.ModNetwork;
import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoUtil;
import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponAmmo;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.event.InputEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.lwjgl.glfw.GLFW;

/**
 * 枪械与投掷物键位。
 *
 * <p>武器：右键（原版 use）由各武器进入瞄准；左键在这里取消原版的挖掘/挥砍，
 * 并把点击、按住转换成开火请求包发给服务端。
 *
 * <p>手雷：右键被整个接管（不给原版 use 机会），只上报「按下 / 松开」；
 * 这一次按住是拔保险销、还是「潜行 + 右键」趁压杆还被手压着把销插回去，以及左键能不能丢出去，
 * 全部由服务端按手雷状态裁决。客户端本地只累计按住时长，用来画物品图标上的进度条。
 */
@Mod.EventBusSubscriber(modid = HexaLunarCalamity.MOD_ID, value = net.minecraftforge.api.distmarker.Dist.CLIENT)
public final class ClientWeaponInput {

    private static int cooldown = 0;
    private static boolean lastDown = false;

    /** 手雷：本次按住右键已持续多少 tick（只用于本地进度条） */
    private static int holdTicks = 0;
    private static boolean lastRmb = false;
    private static boolean holdReported = false;

    /** 左键按下：持枪取消挖掘/攻击改由开火接管；攥手雷取消挖掘并投掷 */
    @SubscribeEvent
    public static void onMouseButtonPre(InputEvent.MouseButton.Pre event) {
        if (event.getAction() == GLFW.GLFW_RELEASE) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.screen != null) return;

        if (event.getButton() == GLFW.GLFW_MOUSE_BUTTON_LEFT) {
            boolean grenade = GrenadeItem.heldGrenade(mc.player) != null;
            if (AmmoUtil.heldWeapon(mc.player) != null || grenade) {
                // 打断可能正在进行的方块挖掘（先挖着再切枪的情况）
                if (mc.gameMode != null) mc.gameMode.stopDestroyBlock();
                event.setCanceled(true);
            }
            if (grenade && GrenadeItem.isHeldPinOut(mc.player)) {
                ModNetwork.CHANNEL.sendToServer(
                        new ModNetwork.GrenadeAction(ModNetwork.GrenadeAction.THROW));
                GrenadeAnimState.onThrow();
                WeaponAnim.onThrow();
            }
            return;
        }

        // 右键：只要手上攥着手雷就整段接管，避免原版对着方块 / 生物使用物品
        if (event.getButton() == GLFW.GLFW_MOUSE_BUTTON_RIGHT
                && GrenadeItem.heldGrenade(mc.player) != null) {
            event.setCanceled(true);
        }
    }

    /** 每 tick 轮询按键：武器按节奏发开火包，手雷跟踪右键按下 / 松开 */
    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) return;

        // 物品图标上的进度条要按世界时间算剩余引信，这里把客户端时间交给 common 代码
        GrenadeItem.clientGameTime = mc.level.getGameTime();

        if (mc.screen != null || mc.player.isSpectator()) {
            cooldown = 0;
            lastDown = false;
            releaseGrenadeHold();
            return;
        }

        tickGrenadeHold(mc);

        ItemStack weapon = AmmoUtil.heldWeapon(mc.player);
        if (weapon == null || !(weapon.getItem() instanceof WeaponAmmo)) {
            cooldown = 0;
            lastDown = false;
            return;
        }

        int interval;
        boolean auto;
        if (weapon.getItem() instanceof AkmRifleItem) {
            interval = AkmRifleItem.FIRE_INTERVAL; // 全自动
            auto = true;
        } else if (weapon.getItem() instanceof CrossbowWeaponItem) {
            interval = CrossbowWeaponItem.FIRE_INTERVAL; // 按住连发
            auto = true;
        } else if (weapon.getItem() instanceof CompoundBowItem) {
            interval = CompoundBowItem.FIRE_INTERVAL; // 半自动：一击一发
            auto = false;
        } else {
            cooldown = 0; lastDown = false; return;
        }

        boolean down = GLFW.glfwGetMouseButton(mc.getWindow().getWindow(),
                GLFW.GLFW_MOUSE_BUTTON_LEFT) == GLFW.GLFW_PRESS;
        if (cooldown > 0) cooldown--;

        if (down && cooldown == 0 && (auto || !lastDown)) {
            ModNetwork.CHANNEL.sendToServer(new ModNetwork.WeaponFire());
            // 手持动作：开火后坐（客户端先自己演，不必等服务端回包）
            WeaponAnim.onFire(weapon, mc.player.isUsingItem() && mc.player.getUseItem() == weapon);
            cooldown = interval;
        }
        lastDown = down;
    }

    /** 手雷右键：上报按下 / 松开，并累计本地按住时长供进度条使用 */
    private static void tickGrenadeHold(Minecraft mc) {
        ItemStack stack = GrenadeItem.heldGrenade(mc.player);
        if (stack == null) {
            releaseGrenadeHold();
            return;
        }
        boolean rmb = GLFW.glfwGetMouseButton(mc.getWindow().getWindow(),
                GLFW.GLFW_MOUSE_BUTTON_RIGHT) == GLFW.GLFW_PRESS;
        int state = GrenadeItem.state(stack);

        if (rmb && !lastRmb) {
            // 一次全新的按下：插着销就是拔销；销已拔出时**潜行 + 右键**才是把销插回去
            holdTicks = 0;
            holdReported = true;
            GrenadeItem.clientPullProgress = state == GrenadeItem.STATE_SAFE ? 0.0F : -1.0F;
            boolean pinOut = state == GrenadeItem.STATE_PRIMED || state == GrenadeItem.STATE_ARMED;
            GrenadeItem.clientReinsertProgress =
                    pinOut && mc.player.isShiftKeyDown() ? 0.0F : -1.0F;
            ModNetwork.CHANNEL.sendToServer(
                    new ModNetwork.GrenadeAction(ModNetwork.GrenadeAction.RMB_DOWN));
        } else if (!rmb && lastRmb) {
            sendRelease();
            holdTicks = 0;
            GrenadeItem.clientPullProgress = -1.0F;
            GrenadeItem.clientReinsertProgress = -1.0F;
        }

        if (rmb && holdReported) {
            holdTicks++;
            float p = Math.min(1.0F, holdTicks / (float) GrenadeItem.PIN_TICKS);
            if (GrenadeItem.clientPullProgress >= 0.0F) GrenadeItem.clientPullProgress = p;
            if (GrenadeItem.clientReinsertProgress >= 0.0F) GrenadeItem.clientReinsertProgress = p;
        }
        // 销已拔出、压杆还被手压着：销一直保持拉出样子，别让模型把它插回去
        if (state == GrenadeItem.STATE_PRIMED && GrenadeItem.clientReinsertProgress < 0.0F) {
            GrenadeItem.clientPullProgress = 1.0F;
        }
        lastRmb = rmb;
    }

    /** 切走手雷 / 打开界面 / 旁观：收尾按住状态，别让服务端挂着拔销中 */
    private static void releaseGrenadeHold() {
        sendRelease();
        holdTicks = 0;
        lastRmb = false;
        GrenadeItem.clientPullProgress = -1.0F;
        GrenadeItem.clientReinsertProgress = -1.0F;
    }

    private static void sendRelease() {
        if (!holdReported) return;
        holdReported = false;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) return;
        ModNetwork.CHANNEL.sendToServer(
                new ModNetwork.GrenadeAction(ModNetwork.GrenadeAction.RMB_UP));
    }

    /** R 键的装填请求由 {@link ClientGunController} 统一发送，本类只管开火与手雷 */
    private ClientWeaponInput() {}
}
