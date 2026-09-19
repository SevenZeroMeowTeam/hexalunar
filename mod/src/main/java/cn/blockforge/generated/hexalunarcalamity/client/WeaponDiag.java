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
 */
public final class WeaponDiag {

    private static final Logger LOGGER = LoggerFactory.getLogger(HexaLunarCalamity.MOD_ID);
    /** 每秒最多一行（20 tick） */
    private static final int PERIOD = 20;

    /** 这一帧 {@code WeaponHandGrip.apply} 有没有被调用（= 我们的手持变换真的生效了） */
    public static volatile boolean applyCalled;
    /** 这一帧 {@code WeaponArms.renderAkm/renderCrossbow/renderAwp} 有没有被调用 */
    public static volatile boolean armsCalled;
    /** 最近一次 {@code GunFrame} 捕获到的举枪进度 */
    public static volatile float frameAim = -1.0F;

    private static int ticks;
    private static boolean warnedDisplay;

    private WeaponDiag() {
    }

    /** 每客户端 tick 调用（{@code ClientEvents#onClientTick} 末尾） */
    public static void tick(Minecraft mc) {
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
                "t=%d held=%s off=%s sight=%d | using=%s useItem=%s useAnim=%s | aim=%.2f frameAim=%.2f"
                        + " equip=%.2f attack=%.2f swinging=%s | ads=(%.2f,%.2f,%.2f) roll=%.1f"
                        + " | modelDisp=%s expect=%s MISMATCH=%s"
                        + " | apply=%s arms=%s | fovSetting=%d mainHand=%s",
                mc.level.getGameTime(),
                shown.getItem(),
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
                disp == null ? "null" : String.format(Locale.ROOT, "(%.3f,%.3f,%.3f)", disp.x, disp.y, disp.z),
                expectPx == null ? "null"
                        : String.format(Locale.ROOT, "(%.3f,%.3f,%.3f)",
                                expectPx[0] / 16.0F, expectPx[1] / 16.0F, expectPx[2] / 16.0F),
                dispMismatch,
                applyCalled, armsCalled,
                mc.options.fov().get(), mc.player.getMainArm());

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
        try (FileWriter w = new FileWriter(file, true)) {
            w.write(line);
            w.write(System.lineSeparator());
        } catch (IOException ignored) {
            // 诊断文件写不出来就算了（日志里还有一份）
        }
    }
}
