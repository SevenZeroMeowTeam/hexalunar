package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoUtil;
import cn.blockforge.generated.hexalunarcalamity.weapon.Sights;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponMount;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;
import org.joml.Vector3f;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Locale;

/**
 * 第一人称武器「枪 / 手臂」错位的现场记录器（诊断用，正常玩可以无视）。
 *
 * <p>为什么需要它：用户反馈「枪飘在手右上方、和手臂分离」，但离线把 {@code WeaponMount} /
 * {@code GunFrame} / {@code WeaponArms} 的那条链子重算一遍，**枪的握把点与手的落点是同一个点**
 * ——说明现成代码里有一条链路在用户机器上不成立（模型 display、动画、原版挥砍位移、
 * 或者 {@code isUsingItem} 卡住）。这些值只有在游戏里才拿得到，所以这里每秒写一行现场数据：
 * <ul>
 *   <li>手上是什么、有没有装瞄具；{@code isUsingItem} / {@code getUseAnimation}（右键进不了机瞄看这里）；</li>
 *   <li>{@code aim}（举枪过渡）、{@code equip}、{@code attackAnim} / {@code swinging}
 *       （原版挥砍位移会把枪整个转 45°，一眼就能看出来）；</li>
 *   <li>举枪位移（{@link cn.blockforge.generated.hexalunarcalamity.weapon.GunPose#ADS}）；</li>
 *   <li><b>模型里实际的 display 平移</b>（从烘焙好的 item model 读）对比
 *       {@link WeaponMount} 里写死的常数 —— 这两个不一致，枪和手就必然错开；</li>
 *   <li>这一帧 {@code applyForgeHandTransform} / 补画手臂有没有真的被调用。</li>
 * </ul>
 *
 * <p>输出落在 <b>游戏目录下的 {@code hexalunar_diag.txt}</b>（同时进日志 INFO）。
 *
 * <p>★★ r110：<b>默认关闭</b>。以前这里是无条件常开的，于是每秒往 {@code latest.log}
 * 和游戏目录的 {@code hexalunar_diag.txt} 各写一行 —— 日志被 {@code [HLCDIAG]} 刷满
 * （一次启动上万行），而且每秒一次的文件写入落在渲染线程上。现场数据只在排查
 * 「枪 / 手臂错位」时才需要，所以改成显式开关：
 *
 * <pre>启动参数加 -Dhexalunar.diag=true</pre>
 *
 * 不开这个开关时 {@link #tick} 直接返回，不写日志也不碰文件。
 */
public final class WeaponDiag {

    private static final Logger LOGGER = LoggerFactory.getLogger(HexaLunarCalamity.MOD_ID);
    /** 每秒最多一行（20 tick） */
    private static final int PERIOD = 20;

    /**
     * 是否记录现场数据。默认 <b>false</b>（见类注释）：用 {@code -Dhexalunar.diag=true} 打开。
     */
    public static final boolean ENABLED = Boolean.getBoolean("hexalunar.diag");

    /** 本次会话是否已经清空过诊断文件（避免它跨启动无限增长） */
    private static boolean truncated;

    /** 这一帧 {@code WeaponHandGrip.apply} 有没有被调用（= 我们的手持变换真的生效了） */
    public static volatile boolean applyCalled;
    /** 这一帧 {@code WeaponArms.renderAkm/renderCrossbow/renderAwp} 有没有被调用 */
    public static volatile boolean armsCalled;
    /** 最近一次 {@code GunFrame} 捕获到的举枪进度 */
    public static volatile float frameAim = -1.0F;
    /**
     * ★ r96：**渲染那一刻**手上是哪个物品。
     *
     * <p>以前只用 tick 时刻的 {@code heldWeapon} 打日志，而 {@code applyCalled/armsCalled} 是过去一秒里
     * 累积的 ⇒「held=akm 但 arms=false」这种组合可能只是换枪过程中的时间窗错位，白读一轮。
     * 现在渲染侧直接把自己的物品记下来，两边同一时刻。
     */
    public static volatile net.minecraft.world.item.Item renderedItem;

    private static int ticks;
    private static boolean warnedDisplay;

    private WeaponDiag() {
    }

    /** 每客户端 tick 调用（{@code ClientEvents#onClientTick} 末尾） */
    public static void tick(Minecraft mc) {
        if (!ENABLED) {
            // ★ r110 诊断关闭时也要把这一秒累积的现场量清掉：
            //   WeaponArms 用 Math.max 累加 externalPoseDelta，没人复位就会一路涨到 Float.MAX。
            applyCalled = false;
            armsCalled = false;
            WeaponArms.externalPoseDelta = 0.0F;
            return;
        }
        if (mc.player == null || mc.level == null) return;
        if (++ticks < PERIOD) return;
        ticks = 0;
        try {
            report(mc);
        } catch (Throwable t) {
            LOGGER.warn("hexalunar 诊断写出错", t);
        }
    }

    private static void report(Minecraft mc) {
        ItemStack held = mc.player.getMainHandItem();
        ItemStack weapon = AmmoUtil.heldWeapon(mc.player);
        if (weapon == null && !(held.getItem() instanceof cn.blockforge.generated
                .hexalunarcalamity.item.GrenadeItem)) {
            return;                                  // 没拿我们的东西就不刷屏
        }
        WeaponAnim.State st = WeaponAnim.heldKind(mc.player) == null
                ? null : WeaponAnim.of(WeaponAnim.heldKind(mc.player));
        ItemStack shown = weapon == null ? held : weapon;
        Vector3f disp = firstPersonTranslation(mc, shown);
        // ★ r95 修：单位对齐 —— 模型里读到的 display 平移是**格**（已经是 模型像素/16），
        //   而 WeaponMount 那三个常数是**模型像素**。以前拿「格」比「像素」，于是永远 MISMATCH
        //   （日志里 held=awp/akm 全都误报），把现场数据也带歪了。
        float[] expectPx = expectedDisplayPx(shown);
        boolean dispMismatch = false;
        if (disp != null && expectPx != null) {
            dispMismatch = Math.abs(disp.x - expectPx[0] / 16.0F) > 0.006F
                    || Math.abs(disp.y - expectPx[1] / 16.0F) > 0.006F
                    || Math.abs(disp.z - expectPx[2] / 16.0F) > 0.006F;
        }

        String line = String.format(Locale.ROOT,
                "t=%d held=%s render=%s off=%s sight=%d | using=%s useItem=%s useAnim=%s"
                        + " | aim=%.2f frameAim=%.2f equip=%.2f attack=%.2f swinging=%s"
                        + " | ads=(%.2f,%.2f,%.2f) roll=%.1f poseDelta=%.3f"
                        + " | modelDisp=%s expect=%s MISMATCH=%s"
                        + " | apply=%s arms=%s | fovSetting=%d mainHand=%s",
                mc.level.getGameTime(),
                shown.getItem(),
                renderedItem == null ? "null" : renderedItem,
                mc.player.getOffhandItem().getItem(),
                weapon == null ? -1 : Sights.sight(weapon),
                mc.player.isUsingItem(), mc.player.getUseItem().getItem(),
                mc.player.getUseItem().getItem().getUseAnimation(mc.player.getUseItem()),
                st == null ? -1.0F : st.aim, frameAim,
                WeaponHandGrip.equipNow, mc.player.getAttackAnim(1.0F), mc.player.swinging,
                cn.blockforge.generated.hexalunarcalamity.weapon.GunPose.ADS[0],
                cn.blockforge.generated.hexalunarcalamity.weapon.GunPose.ADS[1],
                cn.blockforge.generated.hexalunarcalamity.weapon.GunPose.ADS[2],
                cn.blockforge.generated.hexalunarcalamity.weapon.GunPose.ADS[4],
                WeaponArms.externalPoseDelta,
                disp == null ? "null" : String.format(Locale.ROOT, "(%.3f,%.3f,%.3f)", disp.x, disp.y, disp.z),
                expectPx == null ? "null"
                        : String.format(Locale.ROOT, "(%.3f,%.3f,%.3f)",
                                expectPx[0] / 16.0F, expectPx[1] / 16.0F, expectPx[2] / 16.0F),
                dispMismatch,
                applyCalled, armsCalled,
                mc.options.fov().get(), mc.player.getMainArm());

        // ★ r96：外部手持渲染留下的篡改量 —— 非 0 就说明有别的模组改了事件里的 PoseStack
        if (WeaponArms.externalPoseDelta > 0.001F) {
            LOGGER.info("[HLCDIAG] ★ 检测到外部手持渲染篡改 PoseStack：poseDelta={}（已用干净基准覆盖回去）",
                    String.format(Locale.ROOT, "%.4f", WeaponArms.externalPoseDelta));
        }

        // 模型里的 display 与 WeaponMount 常数不一致 = 枪/手必然错开的硬证据（只警告一次）
        if (dispMismatch && !warnedDisplay) {
            warnedDisplay = true;
            LOGGER.warn("★ 枪械 display 平移与 WeaponMount 常数不一致：model={} 期望=(格){}"
                            + " —— 手臂与弹道都按常数算，枪按模型画，两者会错开",
                    disp, expectPx == null ? "null" : String.format(Locale.ROOT, "(%.3f,%.3f,%.3f)",
                            expectPx[0] / 16.0F, expectPx[1] / 16.0F, expectPx[2] / 16.0F));
        }
        LOGGER.info("[HLCDIAG] {}", line);
        append(mc, line);
        applyCalled = false;
        armsCalled = false;
        WeaponArms.externalPoseDelta = 0.0F;              // ★ r96：篡改量按报告周期复位
    }

    /**
     * 这把枪在 {@code models/item/*.json} 里写死的 firstperson display 平移（**模型像素**），
     * 用来和从烘焙模型读到的那份（**格**）做对照。单位别搞混 —— r95 之前就是「格比像素」，
     * 于是一路误报 MISMATCH。
     */
    private static float[] expectedDisplayPx(ItemStack stack) {
        if (stack.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AkmRifleItem) {
            return new float[]{WeaponMount.AKM_TX, WeaponMount.AKM_TY, WeaponMount.AKM_TZ};
        }
        if (stack.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AwpRifleItem) {
            return new float[]{WeaponMount.AWP_TX, WeaponMount.AWP_TY, WeaponMount.AWP_TZ};
        }
        if (stack.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .Kar98kItem) {
            // ★ r105：Kar98k 的 display 常数（models/item/kar98k.json 与 WeaponMount 必须是同一组）
            return new float[]{WeaponMount.KAR98K_TX, WeaponMount.KAR98K_TY, WeaponMount.KAR98K_TZ};
        }
        if (stack.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .MosinRifleItem) {
            // ★ r106：莫辛的 display 常数（models/item/mosin_nagant.json 与 WeaponMount 必须同一组）
            return new float[]{WeaponMount.MOSIN_TX, WeaponMount.MOSIN_TY, WeaponMount.MOSIN_TZ};
        }
        if (stack.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .M1GarandItem) {
            // ★ r108：M1 加兰德的 display 常数（models/item/m1_garand.json 与 WeaponMount 必须同一组）
            return new float[]{WeaponMount.M1_TX, WeaponMount.M1_TY, WeaponMount.M1_TZ};
        }
        if (stack.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .CrossbowWeaponItem) {
            return new float[]{0.0F, 0.0F, 0.0F};            // crossbow.json：平移 0 / scale 0.8
        }
        return null;
    }

    /**
     * 从烘焙好的物品模型上读「第一人称右手」的 display 平移（单位：模型像素 = 1/16 格）。
     * 这就是原版 {@code handleCameraTransforms} 真正会用的那一份数据。
     */
    private static Vector3f firstPersonTranslation(Minecraft mc, ItemStack stack) {
        try {
            var model = mc.getItemRenderer().getModel(stack, mc.level, mc.player, 0);
            var transform = model.getTransforms()
                    .getTransform(net.minecraft.world.item.ItemDisplayContext.FIRST_PERSON_RIGHT_HAND);
            return transform.translation;
        } catch (Throwable t) {
            return null;
        }
    }

    private static void append(Minecraft mc, String line) {
        File file = new File(mc.gameDirectory, "hexalunar_diag.txt");
        // ★ r110：本次会话第一次写之前先清空，否则这个文件会跨启动无限增长
        boolean appendMode = truncated;
        truncated = true;
        try (FileWriter w = new FileWriter(file, appendMode)) {
            w.write(line);
            w.write(System.lineSeparator());
        } catch (IOException ignored) {
            // 诊断文件写不出来就算了（日志里还有一份）
        }
    }
}
