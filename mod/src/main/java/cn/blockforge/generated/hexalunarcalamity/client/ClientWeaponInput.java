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
 *
 * <h2>★★ r90：按键状态只信「真实的鼠标事件」，不再信 GLFW 的缓存</h2>
 *
 * <p>用户反馈两个症状，其实是同一个根因：
 * <ol>
 *   <li>「游戏中断点 / alt-tab 之后回到游戏，左键不发射」——半自动武器再也等不到一次
 *       「新的按下」；</li>
 *   <li>「按住右键进不了机瞄（抵肩）」——{@code isUsingItem()} 卡在 true，原版
 *       {@code LivingEntity#startUsingItem} 里有一句 {@code if (... && !this.isUsingItem())}
 *       ⇒ <b>只要卡着，后面任何一次右键都进不去</b>。</li>
 * </ol>
 *
 * <p>原因都在 {@code GLFW.glfwGetMouseButton}：它给的是 GLFW 自己缓存的按钮状态。
 * 调试器断点 / alt-tab / 点到别的窗口时，鼠标松开事件落在别的窗口上 ⇒ 这个缓存**永远停在按下**。
 * 于是：
 * <ul>
 *   <li>轮询出来的 {@code down} 恒为 true ⇒ 半自动武器的 {@code lastDown} 再也回不到 false；</li>
 *   <li>右键那一路也一样，并且原版的 use 状态没人去释放 ⇒ {@code isUsingItem()} 卡死。</li>
 * </ul>
 *
 * <p>现在的做法：
 * <ul>
 *   <li>按下 / 松开**只**由 {@link InputEvent.MouseButton} 事件维护（{@link #attackPressed} /
 *       {@link #usePressed}）。GLFW 缓存只在「已经收到过真实按下」时才允许参与，避免幻影输入。</li>
 *   <li>窗口重新获得焦点时把状态整个复位，并主动释放卡住的 use（见 {@link #clearStuckUse}）。</li>
 *   <li>每 tick 兜底：右键没按住、手上武器又不在换弹/上弦，就直接释放 use —— 这样
 *       「右键进不了机瞄」不会因为一次丢事件而永久坏掉。</li>
 * </ul>
 */
@Mod.EventBusSubscriber(modid = HexaLunarCalamity.MOD_ID, value = net.minecraftforge.api.distmarker.Dist.CLIENT)
public final class ClientWeaponInput {

    private static int cooldown = 0;
    private static boolean lastDown = false;

    /**
     * 左键「按住」状态：**只**由真实的鼠标事件维护。
     *
     * <p>失焦 / 断点会丢掉松开事件，这个值是唯一可靠的口径；{@code GLFW.glfwGetMouseButton}
     * 会永久停在按下（见类注释）。
     */
    private static boolean attackPressed = false;
    /** 右键「按住」状态（同上）。机瞄 / 拉弦 / 手雷都用它，不再直接读 GLFW 缓存。 */
    private static boolean usePressed = false;
    /** 上一 tick 窗口是否活跃（失而复得时把所有输入状态复位） */
    private static boolean wasWindowActive = true;

    /** 手雷：本次按住右键已持续多少 tick（只用于本地进度条） */
    private static int holdTicks = 0;
    private static boolean holdReported = false;

    /** 左键按下：持枪取消挖掘/攻击改由开火接管；攥手雷取消挖掘并投掷 */
    @SubscribeEvent
    public static void onMouseButtonPre(InputEvent.MouseButton.Pre event) {
        Minecraft mc = Minecraft.getInstance();
        boolean release = event.getAction() == GLFW.GLFW_RELEASE;

        // ★ 松开永远要处理（哪怕界面开着 / 手上没武器）：否则状态会一直停在「按住」，
        //   就是用户报的「左键不发射 / 右键进不了机瞄」。
        if (event.getButton() == GLFW.GLFW_MOUSE_BUTTON_LEFT) {
            if (release) {
                attackPressed = false;
                lastDown = false;
            } else if (mc.player != null && mc.screen == null) {
                attackPressed = true;
            }
        } else if (event.getButton() == GLFW.GLFW_MOUSE_BUTTON_RIGHT) {
            usePressed = !release;
        }

        if (release) return;
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

        // ★★ r90：右键只在「手上真攥着手雷」时才整段接管 —— {@code heldGrenade} 已经保证
        //    「主手是枪械时副手的雷不参与按键」，所以举着 AKM 时右键一定轮得到瞄准。
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

        // ★ 窗口失而复得（alt-tab / 调试器断点 / 点了别处再回来）—— 把输入状态整个复位：
        //   · 松开事件可能在失焦期间丢掉了 ⇒ 状态要清，等一次真实按下再开火（避免“幻影射击”）
        //   · 右键的 use 可能卡着不清，把玩家锁在 isUsingItem() 里（右键再也进不了机瞄）
        boolean windowActive = mc.isWindowActive();
        if (windowActive && !wasWindowActive) {
            cooldown = 0;
            lastDown = false;
            attackPressed = false;
            usePressed = false;
            releaseGrenadeHold();
            clearStuckUse(mc);
        }
        wasWindowActive = windowActive;

        if (mc.screen != null || mc.player.isSpectator()) {
            cooldown = 0;
            lastDown = false;
            attackPressed = false;
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

        // ★ r90 兜底：右键明明没按着、武器也不在换弹/上弦，却还卡在 isUsingItem ⇒ 释放。
        //   不释放的话原版 startUsingItem 里的 `!isUsingItem()` 判断会让**之后每一次右键都失效**
        //   （用户：「按住右键进不了机瞄」）。
        if (!usePressed && !weaponBusy(weapon, mc)) {
            clearStuckUse(mc);
        }

        int interval;
        boolean auto;
        if (weapon.getItem() instanceof AkmRifleItem) {
            interval = AkmRifleItem.FIRE_INTERVAL; // 全自动
            auto = true;
        } else if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AwpRifleItem) {
            interval = cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem
                    .CYCLE_TICKS / 2;              // 栓动：击发 + 拉栓整个循环，按住也不会连发
            auto = false;
        } else if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .Kar98kItem) {
            // ★ r105 Kar98k：同样是栓动（与 AWP 一条调校），按住左键不会连发
            interval = cn.blockforge.generated.hexalunarcalamity.weapon.Kar98kItem
                    .CYCLE_TICKS / 2;
            auto = false;
        } else if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .MosinRifleItem) {
            // ★ r106 莫辛：同样是栓动（击发 + 拉栓整个循环），按住左键不会连发
            interval = cn.blockforge.generated.hexalunarcalamity.weapon.MosinRifleItem
                    .CYCLE_TICKS / 2;
            auto = false;
        } else if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .M1GarandItem) {
            // ★ r108 M1 加兰德：**连射**（半自动）—— 按住左键按 FIRE_INTERVAL 的节奏一发一发打，
            //   枪机由导气杆自动循环，不需要玩家拉栓
            interval = cn.blockforge.generated.hexalunarcalamity.weapon.M1GarandItem.FIRE_INTERVAL;
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

        boolean down = attackDown(mc);
        if (cooldown > 0) cooldown--;

        if (down && cooldown == 0 && (auto || !lastDown)) {
            // ★ r72：十字弩未上弦时不「扫射」—— 只在按下的那一下发一次请求
            //   （服务端会空响 + 提示右键上弦），按住不会每 5 tick 刷一次提示。
            boolean dryCrossbow = weapon.getItem() instanceof CrossbowWeaponItem
                    && !CrossbowWeaponItem.cocked(weapon);
            if (!dryCrossbow) {
                ModNetwork.CHANNEL.sendToServer(new ModNetwork.WeaponFire());
                // 手持动作：开火后坐（客户端先自己演，不必等服务端回包）
                WeaponAnim.onFire(weapon, mc.player.isUsingItem() && mc.player.getUseItem() == weapon);
            } else if (!lastDown) {
                ModNetwork.CHANNEL.sendToServer(new ModNetwork.WeaponFire());
            }
            cooldown = interval;
        }
        lastDown = down;
    }

    /**
     * 左键是否真的按着：真实事件优先，GLFW 缓存只在「已经见过一次真实按下」时才参与兜底
     * （那个缓存失焦后会永久停在按下，是这次两个 bug 的根因）。
     */
    private static boolean attackDown(Minecraft mc) {
        if (attackPressed) return true;
        return false;
    }

    /** 手上这把武器是不是「正在换弹 / 正在上弦」——这种情况下的 use 状态是正当的，不能释放 */
    private static boolean weaponBusy(ItemStack weapon, Minecraft mc) {
        if (mc.level == null) return false;
        long now = mc.level.getGameTime();
        if (weapon.getItem() instanceof AkmRifleItem) return AkmRifleItem.reloading(weapon, now);
        if (weapon.getItem() instanceof CrossbowWeaponItem) {
            return CrossbowWeaponItem.reloadProgress(weapon, now) >= 0.0F;
        }
        if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AwpRifleItem) {
            return cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem
                    .reloading(weapon, now)
                    || cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem
                    .bolting(weapon, now);
        }
        if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .Kar98kItem) {
            // ★ r105/r107 Kar98k：逐发压弹 / 拉栓期间 use 状态是正当的，不能释放
            return cn.blockforge.generated.hexalunarcalamity.weapon.Kar98kItem
                    .loading(weapon, now)
                    || cn.blockforge.generated.hexalunarcalamity.weapon.Kar98kItem
                    .bolting(weapon, now);
        }
        if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .MosinRifleItem) {
            // ★ r106 莫辛：逐发压弹 / 拉栓期间 use 状态是正当的，不能释放
            return cn.blockforge.generated.hexalunarcalamity.weapon.MosinRifleItem
                    .loading(weapon, now)
                    || cn.blockforge.generated.hexalunarcalamity.weapon.MosinRifleItem
                    .bolting(weapon, now);
        }
        if (weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .M1GarandItem) {
            // ★ r108 M1：压漏夹 / 枪机自动循环期间 use 状态是正当的，不能释放
            return cn.blockforge.generated.hexalunarcalamity.weapon.M1GarandItem
                    .loading(weapon, now)
                    || cn.blockforge.generated.hexalunarcalamity.weapon.M1GarandItem
                    .bolting(weapon, now);
        }
        // 复合弓：举弓蓄力本来就要一直按着右键，交给上面的 usePressed 判断
        return false;
    }

    /** 主动释放「卡住的 use」——原版 startUsingItem 里那句 !isUsingItem() 会让卡住之后右键永久失效 */
    private static void clearStuckUse(Minecraft mc) {
        if (mc.player == null || mc.gameMode == null) return;
        if (mc.player.isUsingItem()) {
            mc.gameMode.releaseUsingItem(mc.player);
        }
    }

    /** 手雷右键：上报按下 / 松开，并累计本地按住时长供进度条使用 */
    private static void tickGrenadeHold(Minecraft mc) {
        ItemStack stack = GrenadeItem.heldGrenade(mc.player);
        if (stack == null) {
            releaseGrenadeHold();
            return;
        }
        boolean rmb = usePressed;
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

    private static boolean lastRmb = false;

    /** 切走手雷 / 打开界面 / 旁观：收尾按住状态（手还抓着，所以不当作「松手」） */
    private static void releaseGrenadeHold() {
        sendHoldCancel();
        holdTicks = 0;
        lastRmb = false;
        GrenadeItem.clientPullProgress = -1.0F;
        GrenadeItem.clientReinsertProgress = -1.0F;
    }

    /**
     * 真的松开了右键 —— 这才会触发「压杆脱手 ⇒ 撞针击发」的逻辑（服务端决定）。
     */
    private static void sendRelease() {
        sendHoldEnd(ModNetwork.GrenadeAction.RMB_UP);
    }

    /** 按住状态被动中止（开界面 / 切手持物 / 旁观）：手还抓着，不算松手，不让引信点燃 */
    private static void sendHoldCancel() {
        sendHoldEnd(ModNetwork.GrenadeAction.HOLD_CANCEL);
    }

    private static void sendHoldEnd(int action) {
        if (!holdReported) return;
        holdReported = false;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) return;
        ModNetwork.CHANNEL.sendToServer(new ModNetwork.GrenadeAction(action));
    }

    /** R 键的装填请求由 {@link ClientGunController} 统一发送，本类只管开火与手雷 */
    private ClientWeaponInput() {}
}
