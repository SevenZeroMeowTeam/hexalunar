package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.weapon.M1GarandItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponMount;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import software.bernie.geckolib.core.animatable.model.CoreGeoBone;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;

/**
 * M1 加兰德的 GeckoLib 模型定义 + 程序化骨骼细节（照 {@link Kar98kGeoModel} 那一套写）。
 *
 * <h2>资源</h2>
 * <ul>
 *   <li>几何 {@code geo/m1_garand.geo.json}（{@code tools/m1_garand_v2.py} 生成，
 *       12 骨骼 / 67 方块）—— 空心圆管枪管 / 八棱觇孔 + 透明镜片十字线 /
 *       与机匣顶齐平的弹夹盖 / 8 发可见子弹的漏夹；★ **没有露在外面的弹匣、拉机柄与导气杆**
 *       （用户三次标注要求：机匣下方空无一物、侧边只有木材与枪管）</li>
 *   <li>贴图 {@code textures/models/m1_garand_geo.png}（+ {@code _glowmask} 供流光层）</li>
 *   <li>动画：★ {@code animations/m1_garand.animation.json}（{@code tools/m1_garand_v2.py} 一并生成）——
 *       {@code idle / run / run_fast / fire / bolt / reload}；
 *       ★★ 六段**全是空动作**（只挂一条恒为 0 的 root 通道）：枪机 / 弹夹盖 / 漏夹 / 抛壳 /
 *       举枪 / 持枪姿态统统由本类程序化驱动，这样就不会再踩
 *       「动画关键帧盖掉 setCustomAnimations 里写的值」那个老坑（AKM 换弹下沉就是它）</li>
 * </ul>
 *
 * <h2>★ 持枪动画 = TaCZ 的「通用步枪」{@code rifle_default}</h2>
 * 用户要求「套用 TaCZ 步枪的持枪动画」，而 TaCZ 里没有 M1（连 M1 原型都没有）。
 * TaCZ 的 {@code assets/tacz/animations/rifle_default.animation.json} 就是**所有没自带动画的步枪**
 * 用的那一套（idle / run / walk_aiming / ADS_up / ADS_down / draw …），所以直接取它：
 * <ul>
 *   <li>{@code idle}（7.27s 循环）：呼吸微摆 rotX ±0.8° / rotZ ±1.4° / 位移 ±0.17 单位</li>
 *   <li>{@code run}（0.8s 循环）：**枪压低并转到右侧** rotX −35.6° / rotY −44.6° / rotZ +31.4°、
 *       位置 (−1.3, −5.5, −0.6) TaCZ 单位（已按枪长 38 → 21 折算 ×0.55）</li>
 *   <li>{@code walk_aiming}：极轻的摆动（0.7° / 0.11 单位）</li>
 * </ul>
 * 这几个数写在 {@link WeaponMount#m1HoldPose}：**骨骼渲染与弹道共用同一份**
 * （不然跑动时枪口与枪身会脱开），由本类的 {@link #computeMovePose} 取用。
 *
 * <h2>四件程序化的事</h2>
 * <ol>
 *   <li><b>气动枪机循环</b>（每发一次）：导气杆自己后退 {@link #BOLT_BACK} px 把空弹壳带出来再复进闭锁
 *       —— 玩家不用拉栓（加兰德**根本没有要拉的栓**）。空仓时枪机**停在后位**。</li>
 *   <li><b>★ 弹夹盖</b>（{@code cover}）：**整体平行抬起**（不转任何角度）＝ 打开，
 *       装填时抬着、压完自动落回合上，**每打一发抬起一下把空弹壳放出去**，
 *       **打空不合上**（空仓挂机）。合上时与机匣顶齐平、盖住漏夹口 ⇒ 从上面看不见里面的子弹。</li>
 *   <li><b>★ 漏夹</b>（{@code clip_in} + {@code clip_rounds}）：**只在装填时可见** ——
 *       8 发黄铜子弹只在漏夹被抬到机匣上方这段时间看得见，压进去/合上后
 *       （连盖子一起）全部隐藏，这就是用户要的「弹匣可以看见子弹，合起来看不见」。</li>
 *   <li><b>双手</b>：平时右手握托颈 / 左手托前托；换弹时**右手**抬起漏夹压下去
 *       （左手始终托着枪 —— 加兰德换弹就是单手压漏夹）。</li>
 * </ol>
 */
public class M1GarandGeoModel extends GeoModel<M1GarandItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/m1_garand.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/m1_garand_geo.png");
    /** 动画文件（与 Kar98k / 莫辛同一套骨骼名，但**没有拉栓动作**：气动半自动） */
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/m1_garand.animation.json");

    /** 当前这一遍是不是「拿在手上」（由 {@link M1GarandGeoRenderer} 设入） */
    static boolean handPass = false;

    /** {@code move} 骨骼 pivot（geo 里的值） */
    private static final float MOVE_PX = 0.0F;
    private static final float MOVE_PY = 1.30F;
    private static final float MOVE_PZ = 1.60F;

    /** 当前这一帧的枪本体变换（给第一人称手臂用，见 {@link GunFrame} / {@link WeaponArms}） */
    static final GunFrame frame = new GunFrame();

    private static final float[] MOVE_POSE = new float[6];

    // ------------------------------------------------------------------ 枪机（气动循环）
    /** {@code bolt} 骨骼 pivot（geo 里的值） */
    private static final float BOLT_PX = 0.0F;
    private static final float BOLT_PY = 2.80F;
    private static final float BOLT_PZ = -1.60F;
    /** 气动枪机循环的后退量（模型像素）：导气杆跟着一起走 */
    private static final float BOLT_BACK = 2.40F;
    /** 击发：扣扳机（绕顶部销轴向后转 11°，与 animation.m1_garand.fire 一致） */
    private static final float TRIGGER_PULL = 11.0F;

    // ------------------------------------------------------------------ ★ 弹夹盖（cover）
    /**
     * ★ 盖板打开 = **沿 Y 平行抬起** {@code COVER_LIFT} 像素，**三个角度恒为 0**
     * —— 用户要求「漏匣上盖是平行的」「打开时也保持平行（打开时也保持平行）」。
     *
     * <p>模块里的盖板 pivot = {@code (0, 2.94, −0.78)}，但它只用于取骨骼；
     * 因为只做平移，pivot 取在哪里都不影响外观。
     *
     * <p>抬 0.40 后盖板落在 y 3.28…3.40，与机匣顶（3.00）之间留出 0.28 的缝 ⇒
     * 空壳（直径 0.20）正是从这条缝里抛出去的（用户「抛壳也如此」：抛壳走的也是这条被盖板让出的口，
     * 盖板全程保持平行）。与 tools/m1_garand_v2.py 的 {@code COVER_LIFT} 必须一致。
     */
    private static final float COVER_LIFT = 0.40F;
    /** 枪机后退到多少（比例）时盖子已完全抬起 —— 之后就是等枪机复进把盖子带回来 */
    private static final float COVER_OPEN_AT = 0.26F;

    // ------------------------------------------------------------------ 漏夹（clip_in + clip_rounds）
    /**
     * 压漏夹时它被抬到机匣上方多高：整只漏夹压在机匣内部（底 1.88 / 顶 2.574）⇒
     * 抬 1.75 后落在 3.63…4.32，**整只都在机匣顶（3.04）之上**，装填时看得见 8 发子弹。
     */
    private static final float CLIP_DROP = 1.75F;

    // ------------------------------------------------------------------ 抛壳（半自动，每发一次）
    /** 抛壳窗口在枪机循环里的位置（★ 先让盖板抬起来：0.14 之前壳不出现） */
    private static final float CASE_T0 = 0.14F;
    private static final float CASE_T1 = 0.72F;
    /** 抽出距离 / 抛出的初速（模型像素）：弹壳从机匣右侧（+X）翻出去 */
    private static final float CASE_BACK = 1.50F;
    private static final float CASE_VX = 3.00F;
    private static final float CASE_VY = 1.80F;
    private static final float CASE_G = 0.80F;
    private static final float CASE_SPIN_Z = 200.0F;
    private static final float CASE_SPIN_X = 130.0F;
    private static final float CASE_SPIN_Y = 90.0F;

    @Override
    public ResourceLocation getModelResource(M1GarandItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(M1GarandItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(M1GarandItem animatable) {
        return ANIMATION;
    }

    @Override
    public void setCustomAnimations(M1GarandItem animatable, long instanceId,
                                    AnimationState<M1GarandItem> state) {
        if (!handPass) {
            staticPose();
            return;
        }
        ItemStack stack = M1GarandAnimState.heldStack();
        long now = M1GarandAnimState.now();

        // ---------------------------------------------------------- 举枪（ADS）：只做平移
        computeMovePose(MOVE_POSE);
        CoreGeoBone move = getAnimationProcessor().getBone("move");
        if (move != null) {
            move.setRotX(MOVE_POSE[3]);
            move.setRotY(MOVE_POSE[4]);
            move.setRotZ(MOVE_POSE[5]);
            move.setPosX(MOVE_POSE[0]);
            move.setPosY(MOVE_POSE[1]);
            move.setPosZ(MOVE_POSE[2]);
        }

        // ---------------------------------------------------------- 枪机
        float bp = stack == null ? -1.0F : M1GarandItem.boltProgress(stack, now);
        float back;
        if (bp >= 0.0F) {
            back = Mth.sin(bp * (float) Math.PI);                  // 半自动：后退 → 复进
        } else if (stack != null && M1GarandItem.loading(stack, now)) {
            float release = M1GarandItem.boltReleaseProgress(stack, now);
            back = release < 0.0F ? 1.0F : 1.0F - ease(release);    // 压漏夹全程挂机，随后复进
        } else if (stack != null && M1GarandItem.boltHoldOpen(stack, now)) {
            back = 1.0F;                                            // 空仓挂机（M1 打空的样子）
        } else {
            back = 0.0F;
        }
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            bolt.setRotX(0.0F);
            bolt.setRotY(0.0F);
            bolt.setRotZ(0.0F);                                     // 导气杆只平移、不转
            bolt.setPosX(0.0F);
            bolt.setPosY(0.0F);
            bolt.setPosZ(back * BOLT_BACK);
        }

        // ---------------------------------------------------------- 扣扳机
        CoreGeoBone trigger = getAnimationProcessor().getBone("trigger");
        if (trigger != null) {
            float fw = stack == null ? -1.0F : M1GarandItem.fireWindow(stack, now);
            trigger.setRotX(-TRIGGER_PULL * triggerPullAt(fw) * Mth.DEG_TO_RAD);
        }

        // ---------------------------------------------------------- 抛壳
        CoreGeoBone casing = getAnimationProcessor().getBone("casing");
        if (casing != null) {
            if (bp < CASE_T0 || bp > CASE_T1) {
                casing.setHidden(true);
            } else {
                casing.setHidden(false);
                float c = (bp - CASE_T0) / (CASE_T1 - CASE_T0);
                float out = Mth.clamp(c / 0.22F, 0.0F, 1.0F);       // 先跟枪机抽出来
                float fly = Mth.clamp((c - 0.22F) / 0.78F, 0.0F, 1.0F);
                casing.setPosX(CASE_VX * fly);
                casing.setPosY(CASE_VY * fly - CASE_G * fly * fly);
                casing.setPosZ(CASE_BACK * out - 0.6F * fly);
                casing.setRotZ(fly * CASE_SPIN_Z * Mth.DEG_TO_RAD);
                casing.setRotX(fly * CASE_SPIN_X * Mth.DEG_TO_RAD);
                casing.setRotY(fly * CASE_SPIN_Y * Mth.DEG_TO_RAD);
            }
        }

        // ---------------------------------------------------------- ★ 弹夹盖：平行抬起（不旋转）
        CoreGeoBone cover = getAnimationProcessor().getBone("cover");
        if (cover != null) {
            cover.setRotX(0.0F);                                    // ★ 三个角度恒为 0：盖板永远平行
            cover.setRotY(0.0F);
            cover.setRotZ(0.0F);
            cover.setPosX(0.0F);
            cover.setPosY(coverOpenAt(bp, stack, now) * COVER_LIFT); // 打开 = 整体竖直抬起
            cover.setPosZ(0.0F);
        }

        // ---------------------------------------------------------- ★ 漏夹：只在装填时看得见（含 8 发子弹）
        boolean loading = stack != null && M1GarandItem.loading(stack, now);
        CoreGeoBone clipIn = getAnimationProcessor().getBone("clip_in");
        if (clipIn != null) {
            float clip = stack == null ? -1.0F : M1GarandItem.clipProgress(stack, now);
            clipIn.setHidden(!loading);                             // 合上/打空后：整只漏夹都不画
            clipIn.setPosY(clip >= 0.0F ? CLIP_DROP * (1.0F - ease(clip)) : 0.0F);
        }
        CoreGeoBone clipRounds = getAnimationProcessor().getBone("clip_rounds");
        if (clipRounds != null) {
            clipRounds.setHidden(!loading);                         // 8 发子弹跟着漏夹一起显隐
        }

        // ---------------------------------------------------------- 弹仓底板：漏夹供弹，一切归零
        CoreGeoBone mag = getAnimationProcessor().getBone("magazine");
        if (mag != null) {
            mag.setHidden(false);
            mag.setRotX(0.0F);
            mag.setPosX(0.0F);
            mag.setPosY(0.0F);
            mag.setPosZ(0.0F);
        }
    }

    /**
     * ★ 弹夹盖的打开量 0..1（Java 侧乘上 {@link #COVER_LIFT} 得到抬起高度）。
     *
     * <ul>
     *   <li><b>击发</b>：跟着气动枪机循环 —— 后退时抬起（把空弹壳放出去）、复进时落下；</li>
     *   <li><b>装填</b>：压漏夹全程抬着，枪机复进闭锁那一段（{@link M1GarandItem#boltReleaseProgress}）
     *       缓缓落回 ⇒ 「装填完成自动合上弹夹盖」；</li>
     *   <li><b>打空</b>：{@link M1GarandItem#boltHoldOpen} 时恒为 1 ⇒ 「打空弹夹不合上」，
     *       要重新压弹（R 键）才会合上。</li>
     * </ul>
     *
     * <p>★ 本方法的返回值**不再当角度用** —— 盖板是平移打开的（用户「打开时也保持平行」）。
     */
    private static float coverOpenAt(float bp, ItemStack stack, long now) {
        if (bp >= 0.0F) {
            // 每发：先快开（到 COVER_OPEN_AT 就全开），再慢慢合上
            float f = bp < COVER_OPEN_AT ? bp / COVER_OPEN_AT
                    : 1.0F - (bp - COVER_OPEN_AT) / (1.0F - COVER_OPEN_AT);
            return ease(Mth.clamp(f, 0.0F, 1.0F));
        }
        if (stack == null) return 0.0F;
        if (M1GarandItem.loading(stack, now)) {
            float release = M1GarandItem.boltReleaseProgress(stack, now);
            return release < 0.0F ? 1.0F : 1.0F - ease(release);
        }
        return M1GarandItem.boltHoldOpen(stack, now) ? 1.0F : 0.0F;
    }

    /**
     * move 骨骼当前帧的目标姿态（与 AKM / AWP / Kar98k / 莫辛同一套规则）。
     *
     * <p>★ 角度基准恒为 0：**举枪位移与开火后坐都在 pose 层**（{@link WeaponHandGrip#pushAds}），
     * 一旦在骨骼上留角度，瞄准线就会离开屏幕中心。
     *
     * <p>★ r111 起多了一层「持枪动画」：呼吸微摆 + 冲刺时把枪压低转到身侧 ——
     * 系数与换算全部在 {@link WeaponMount#m1HoldPose}（TaCZ 通用步枪 {@code rifle_default}），
     * **骨骼渲染与弹道取的是同一份数**，所以跑动时枪口焰/弹道不会与枪身脱开。
     */
    static void computeMovePose(float[] out) {
        Player player = Minecraft.getInstance().player;
        WeaponMount.m1HoldPose(player, aimNow(), holdRun(player), out);
    }

    /** 当前举枪比例（举枪时持枪姿态全部收掉：瞄准线必须精确） */
    private static float aimNow() {
        return Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.M1_GARAND).aim, 0.0F, 1.0F);
    }

    /** 上一游戏刻的编号 + 平滑后的冲刺量（同一刻只推进一步：渲染一帧可能调好几次） */
    private static long holdTick = Long.MIN_VALUE;
    private static float holdRun = 0.0F;

    /** 冲刺量的平滑（0 → 1 大约 6 tick），台阶式切换会让「枪压下去」是一下子跳过去 */
    private static float holdRun(Player player) {
        Minecraft mc = Minecraft.getInstance();
        long now = mc.level == null ? 0L : mc.level.getGameTime();
        if (now != holdTick) {
            holdTick = now;
            float target = player != null && player.isSprinting() && player.onGround() ? 1.0F : 0.0F;
            holdRun += Mth.clamp(target - holdRun, -0.18F, 0.18F);
        }
        return holdRun;
    }

    /** 手臂用：把**当前帧**的 move 姿态直接算进 {@link #frame}（手臂比物品先画，不能等捕获） */
    static void captureNow() {
        computeMovePose(MOVE_POSE);
        Player local = Minecraft.getInstance().player;
        WeaponHandGrip.pushAds(WeaponAnim.Kind.M1_GARAND, local == null ? ItemStack.EMPTY
                : local.getMainHandItem(), local);
        frame.capture(WeaponMount.M1_TX, WeaponMount.M1_TY, WeaponMount.M1_TZ, 1.0F,
                MOVE_PX, MOVE_PY, MOVE_PZ,
                MOVE_POSE[0], MOVE_POSE[1], MOVE_POSE[2],
                MOVE_POSE[3], MOVE_POSE[4], MOVE_POSE[5],
                Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.M1_GARAND).aim, 0.0F, 1.0F));
    }

    // ------------------------------------------------------------------ 右手（模型像素）
    /**
     * 平时：握在**托颈**上（M1 没有独立握把 —— 托颈就是握把，与枪托是一整块木头）。
     * 模型里托颈的木头占 y 1.35…2.70、z 2.10…3.60，所以手落在它的前下角。
     */
    private static final float[] ARM_GRIP = {0.0F, 1.45F, 2.55F};
    /**
     * 换弹：右手把 8 发漏夹从机匣**上方**压下去。
     * y=4.06 是漏夹被抬到最高的位置（静止位顶 2.574 + CLIP_DROP 1.75 ≈ 4.32），
     * z=−1.40 正对机匣的压弹口（**盖板开口 z −1.98…−0.78 的正中心**，照门座在 z −0.70…0.06
     * 一带、手在它前面，不穿模）。
     */
    private static final float[] ARM_CLIP = {0.0F, 4.06F, -1.40F};
    /** 压到底时手往下走的量（漏夹继续进机匣，手停在机匣顶面上方） */
    private static final float ARM_PRESS = 1.00F;
    private static final float[] TMP_C = new float[3];

    /**
     * 右手目标：
     * <ol>
     *   <li>平时握着托颈（食指在扳机上）—— 半自动射击时**手不跟着枪机跑**（枪机是导气杆自己动的）</li>
     *   <li><b>压漏夹</b>：抬手到机匣上方，跟着漏夹一起往下按</li>
     * </ol>
     * ★ 漏夹到位后枪机是**自己**复进闭锁的（复进簧 + 导气）—— 右手**不再去抓拉机柄**：
     *   加兰德没有要拉的栓，用户明确要求「无需拉栓」。
     */
    static float[] rightHandPx(float[] out) {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return copy(ARM_GRIP, out);
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof M1GarandItem)) return copy(ARM_GRIP, out);
        long now = player.level().getGameTime();

        float clip = M1GarandItem.clipProgress(stack, now);
        if (clip >= 0.0F) {                                          // 压漏夹
            float press = ARM_PRESS * ease(clip);
            TMP_C[0] = ARM_CLIP[0];
            TMP_C[1] = ARM_CLIP[1] - press;
            TMP_C[2] = ARM_CLIP[2];
            return copy(TMP_C, out);
        }
        return copy(ARM_GRIP, out);
    }

    // ------------------------------------------------------------------ 左手（模型像素）
    /**
     * 左手：一直托在前托下方（加兰德换弹是**单手压漏夹** —— 右手干活，左手把枪端住，
     * 所以左手在换弹期间也不动）。
     */
    private static final float[] ARM_SUPPORT = {0.0F, 1.40F, -6.20F};

    static float[] leftHandPx(float[] out) {
        return copy(ARM_SUPPORT, out);
    }

    private static float ease(float t) {
        float x = Mth.clamp(t, 0.0F, 1.0F);
        return x * x * (3.0F - 2.0F * x);
    }

    private static float[] copy(float[] src, float[] out) {
        System.arraycopy(src, 0, out, 0, 3);
        return out;
    }

    /** 扣扳机的压下量 0..1：快扣 → 慢放（-1 = 不在击发窗口里） */
    private static float triggerPullAt(float fw) {
        if (fw < 0.0F) return 0.0F;
        if (fw < 0.25F) return ease(fw / 0.25F);
        return ease(Mth.clamp((1.0F - fw) / 0.75F, 0.0F, 1.0F));
    }

    /**
     * GUI 图标 / 掉落物 / 展示框用的**静态姿态**：举枪位移、枪机、弹夹盖、抛壳、漏夹全部归位
     * （枪机在闭锁位、**弹夹盖合上**、弹壳与 8 发子弹都藏起来）。
     */
    private void staticPose() {
        CoreGeoBone move = getAnimationProcessor().getBone("move");
        if (move != null) {
            move.setRotX(0.0F);
            move.setRotY(0.0F);
            move.setRotZ(0.0F);
            move.setPosX(0.0F);
            move.setPosY(0.0F);
            move.setPosZ(0.0F);
        }
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            bolt.setRotX(0.0F);
            bolt.setRotY(0.0F);
            bolt.setRotZ(0.0F);
            bolt.setPosX(0.0F);
            bolt.setPosY(0.0F);
            bolt.setPosZ(0.0F);
        }
        CoreGeoBone mag = getAnimationProcessor().getBone("magazine");
        if (mag != null) {
            mag.setHidden(false);
            mag.setRotX(0.0F);
            mag.setPosX(0.0F);
            mag.setPosY(0.0F);
            mag.setPosZ(0.0F);
        }
        CoreGeoBone trigger = getAnimationProcessor().getBone("trigger");
        if (trigger != null) {
            trigger.setRotX(0.0F);
        }
        CoreGeoBone casing = getAnimationProcessor().getBone("casing");
        if (casing != null) {
            casing.setHidden(true);                 // 静止时弹壳收在弹膛里
        }
        CoreGeoBone cover = getAnimationProcessor().getBone("cover");
        if (cover != null) {
            cover.setRotX(0.0F);                    // 图标里弹夹盖是合上的（三个角度都为 0）
            cover.setRotY(0.0F);
            cover.setRotZ(0.0F);
            cover.setPosX(0.0F);
            cover.setPosY(0.0F);                    // 抬起量为 0 ⇒ 与机匣顶齐平
            cover.setPosZ(0.0F);
        }
        CoreGeoBone clipIn = getAnimationProcessor().getBone("clip_in");
        if (clipIn != null) {
            clipIn.setHidden(true);                 // 图标里不画漏夹（合上后本来就看不见）
            clipIn.setPosY(0.0F);
        }
        CoreGeoBone clipRounds = getAnimationProcessor().getBone("clip_rounds");
        if (clipRounds != null) {
            clipRounds.setHidden(true);             // 8 发子弹也一起藏起来
        }
    }
}
