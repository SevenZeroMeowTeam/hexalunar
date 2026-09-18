package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import software.bernie.geckolib.core.animatable.model.CoreGeoBone;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;

/**
 * 十字弩的 GeckoLib 模型（体素，824 方块 / 14 骨骼）。
 *
 * <p>模型由 {@code tools/crossbow_vox.py} 把参考网格 {@code 模型/十字弩_v2.bbmodel}
 * （11 个 mesh 部件的「现代复合弩」：窄弓臂 + 高导轨 + 枪式握把 + 镜筒 + 线缆）**表面体素化**而来，
 * 逐格从原贴图采样 UV；弦 / 弦心 / 弩箭用方块单独画（要能绕弓臂梢转）。
 * 坐标系：以握把中心为原点、弩头朝 −Z，与旧模型同一套（{@code WeaponArms} 的握点不用改）。
 *
 * <p><b>拉弦装弹</b>是连续动作（按住/R 键共 {@code RELOAD_TICKS}=30 tick），所以按
 * {@code CrossbowWeaponItem.reloadProgress} 程序化推骨骼：
 * 弦两段绕弓臂梢（<b>Y 轴</b>）转 φ、弦心后退 DRAW_DZ，弩箭在后半段滑上弦。
 * 弦长取拉满所需（hypot(2.62, 1.80)=3.18），未拉时两段在中点重叠、被弦心缠绳盖住。
 * ★ TIP_X / DRAW_DZ / NOCK_Z0 必须与 {@code tools/crossbow_vox.py} 的同名常数一致
 *   （生成器末尾会打印并自检「拉满时两段弦的内端正好落在弦心」）。
 * ★ 上弦完成（cocked）后弦**不往后拉**（贴回两弓臂之间）——拉回去的弦心离镜头更近，
 *   透视下会像一根浮在弩上方的「∧」。
 *
 * <p><b>弓臂内收（r63）</b>：拉弦时两弓臂绕「贴导轨的内端」向内转（拉满 9°），外端因此
 * **向内 + 向后**走 —— 看上去就是「弓臂向内收缩」；松开 / 击发后回到参考网格（图片）那个张开姿态。
 * 弦与凸轮盘的 pivot 就在弓臂梢上，所以它们跟着弓臂平移同样的位移，不会脱开。
 * ★ FLEX_DEG / FLEX_PX / FLEX_PZ 必须与 {@code tools/_cb_flex.py} 的同名常数一致
 *   （那个脚本会打印收进量、弦内端偏差，并能烘焙姿态出图）。
 */
public class CrossbowGeoModel extends GeoModel<CrossbowWeaponItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/crossbow_geo.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/crossbow_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/crossbow.animation.json");

    /** 弓臂梢到弦心的横向距离（生成器 TIP_X）；★ r65 弓臂放大 1.7 倍后 = 4.454 */
    private static final float TIP_X = 4.454F;
    /** 拉满时弦心后退距离（生成器 DRAW_DZ） */
    private static final float DRAW_DZ = 1.80F;
    /** 弦段长度（生成器按 hypot(TIP_X, DRAW_DZ) 生成） */
    private static final float STRING_LEN = 4.804F;
    /** 弦段转角 φ = atan(DRAW_DZ / TIP_X) */
    private static final float PHI_RAD = (float) Math.atan2(DRAW_DZ, TIP_X);
    /** 弦面中心的 z（生成器 NOCK_Z0；已含「以握把为原点」的平移） */
    private static final float NOCK_Z0 = -5.20F;
    /** 弩箭收起时挪走的高度（挪到看不见） */
    private static final float BOLT_HIDE_Y = -40.0F;
    /** 击发后弦震动持续 tick 数 */
    private static final int TWANG_TICKS = 9;
    /**
     * 当前这一遍渲染是不是「拿在手上」（第一/第三人称；由 {@link CrossbowGeoRenderer} 设入）。
     * GeckoLib 的 {@code setCustomAnimations} 对 GUI 图标 / 掉落物 / 展示框一样会跑。
     */
    static boolean handPass = false;

    /**
     * 击发后坐（模型像素，乘 WeaponAnim 的后坐冲量）：**只沿弩身方向后拖**（+Z 朝射手）。
     *
     * <p>【不给上下、不给俯仰】：用户要求「只前后动不是上下动」。弩比枪轻，幅度取小一半。
     */
    private static final float KICK_BACK = 0.95F;
    /** 拉满时凸轮盘转过的角度（视觉：弦从凸轮上放开）；随 DRAW_DZ 等比放大 */
    private static final float CAM_SPIN = (float) Math.toRadians(60.0);

    // ------------------------------------------------------------------ 弓臂内收（r63）
    /** ★ 拉满时弓臂内收角（度）：绕「贴导轨的内端」转，外端向内 + 向后 ⇒「弓臂向内收缩」 */
    private static final float FLEX_DEG = 8.0F;
    /** ★ 拉满时两弓臂整体**向后（射手方向）**滑的量（模型像素）—— 只靠转的话外端主要只往内走 */
    private static final float FLEX_BACK = 0.35F;
    /** 弓臂弯折支点（模型像素）：贴导轨那一端（最前端）—— 由 tools/crossbow_vox.py 打印 */
    private static final float FLEX_PX = 1.599F;
    private static final float FLEX_PZ = -8.697F;
    /** cam / 弦锚点所在平面的 z（= 这两个骨骼 pivot 的 z） */
    private static final float CAM_Z = -5.20F;

    /**
     * 这一遍渲染的弩是不是「已上弦」（由 {@link CrossbowGeoRenderer} 从被渲染的 ItemStack 读）。
     * 图标 / 展示框里要按这个决定看不看得到弩箭（换弹状态是**本地玩家**的，不能拿来画图标）。
     */
    static boolean cockedNow = false;

    /** 弦震动计时（客户端静态字段，跨帧保留） */
    private static long twangUntil = 0L;
    /** 上一帧是否已上弦（用来捕捉「击发」这个边沿） */
    private static boolean wasCocked = false;
    /** 当前这一遍渲染是不是 GUI 图标（由 {@link CrossbowGeoRenderer} 每帧设置） */
    /**
     * 当前这一帧的弩本体变换（给第一人称手臂用，见 {@link GunFrame}）。
     * 十字弩的 display 是「平移 0 / scale 0.8」，与 {@code models/item/crossbow.json} 一致。
     */
    static final GunFrame frame = new GunFrame();
    /** move 骨骼 pivot（geo 里的值） */
    private static final float MOVE_PX = 0.0F;
    private static final float MOVE_PY = 0.0F;
    private static final float MOVE_PZ = 0.0F;
    /** 上一帧的换弹进度 / 拉弦量（左手动作要用；-1 = 没在换弹） */
    private static float lastProgress = -1.0F;
    private static float lastDraw = 0.0F;

    @Override
    public ResourceLocation getModelResource(CrossbowWeaponItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(CrossbowWeaponItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(CrossbowWeaponItem animatable) {
        return ANIMATION;
    }

    @Override
    public void setCustomAnimations(CrossbowWeaponItem animatable, long instanceId,
                                    AnimationState<CrossbowWeaponItem> animationState) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) return;
        ItemStack stack = mc.player.getMainHandItem();
        if (!(stack.getItem() instanceof CrossbowWeaponItem)) {
            stack = mc.player.getOffhandItem();
            if (!(stack.getItem() instanceof CrossbowWeaponItem)) return;
        }

        // ★ GUI 图标 / 掉落物 / 展示框：画一帧**静态姿态**就走。
        //   那些语境里「开火中 / 换弹进度」同样是真的（都是本地玩家的全局状态），
        //   不归位的话物品栏图标会在开火时往后拖、上弦时弦还会被拉走（用户反馈过）。
        //   同时**不捕获 frame** —— 第一人称手臂在 RenderHandEvent 里比物品先画，
        //   读的是上一帧的捕获值，被图标那一遍覆盖掉就会「弩动、手不动」。
        if (!handPass) {
            staticPose();
            return;
        }

        long now = mc.level.getGameTime();
        boolean cocked = CrossbowWeaponItem.cocked(stack);
        float progress = CrossbowWeaponItem.reloadProgress(stack, now);   // 0..1，-1 表示没在装
        float p = progress < 0.0F ? 0.0F : Mth.clamp(progress, 0.0F, 1.0F);

        // 前 65% 拉弦，后 35% 把箭推上弦
        // ★ 上弦完成（cocked）后弦**不再往后拉**，直接贴回两弓臂之间（draw = 0）：
        //   拉回去的弦心离镜头近 0.17 格，透视下会像一根浮在弩上方的「∧」（用户要求看不到）。
        //   拉弦动作本身照旧（装填期间 draw 从 0 拉到 1），一上弦就弹回弓臂前面。
        float draw = cocked ? 0.0F : Mth.clamp(p / 0.65F, 0.0F, 1.0F);
        float load = cocked ? 1.0F : Mth.clamp((p - 0.55F) / 0.45F, 0.0F, 1.0F);

        // 击发那一瞬（已上弦 → 未上弦）触发弦震动：两段同相摆动，弦心跟着前后抖
        if (wasCocked && !cocked) {
            twangUntil = now + TWANG_TICKS;
        }
        wasCocked = cocked;
        float tw = 0.0F;
        int twLeft = (int) (twangUntil - now);
        if (twLeft > 0) {
            float decay = twLeft / (float) TWANG_TICKS;                 // 1 → 0
            tw = (float) Math.sin((TWANG_TICKS - twLeft) * 2.1F) * 0.17F * decay * decay;
        }

        // 弦两段：绕弓臂梢的 Y 轴转（左 -φ、右 +φ），两端正好在弦心重合
        CoreGeoBone left = getAnimationProcessor().getBone("string_left");
        CoreGeoBone right = getAnimationProcessor().getBone("string_right");
        if (left != null) left.setRotY(-draw * PHI_RAD + tw);
        if (right != null) right.setRotY(draw * PHI_RAD - tw);

        // ★ 弓臂内收（r63/r64/r65）：拉弦时两弓臂绕「贴导轨的内端」向内转 + 整体往射手方向滑 ——
        //   外端**向内约 0.5 + 向后约 0.7**（用户选的「又向内又向后」），松开/击发后回到
        //   参考网格（图片）那个张开姿态。弦与凸轮盘挂在弓臂梢上，跟着走。
        //   ★ 弦锚点因此产生的位移要用到弦心/弩箭/左手上（见 nockTravel），三者必须严格一致，
        //   否则弦会落在弦心后面（拉满时差 0.36 像素，肉眼就是“弦没贴住弦心”）。
        float flex = draw * FLEX_DEG * Mth.DEG_TO_RAD;
        float back = draw * FLEX_BACK;
        flexLimb("prod_right", "cam_right", "string_right", 1, -flex, back);
        flexLimb("prod_left", "cam_left", "string_left", -1, flex, back);

        // 复合十字弩：拉弦时两个凸轮盘跟着转（弦从凸轮上放/收）
        CoreGeoBone camL = getAnimationProcessor().getBone("cam_left");
        CoreGeoBone camR = getAnimationProcessor().getBone("cam_right");
        if (camL != null) camL.setRotY(-draw * CAM_SPIN);
        if (camR != null) camR.setRotY(draw * CAM_SPIN);

        // 弦心（缠绳）随拉弦后退：行程 = 弦绷直所需（弦段长度固定 ⇒ 锚点内移后能拉得更深）+ 弓臂后滑量；
        // 震动时跟着弦心一起前后抖（弦在 X 上的半投影 = TIP_X）
        float travel = nockTravel(draw);
        CoreGeoBone nock = getAnimationProcessor().getBone("nock");
        if (nock != null) {
            nock.setPosZ(travel - TIP_X * tw);
            nock.setPosY(0.0F);
        }

        // 弩箭：没装填时挪到看不见；装填时滑到弦心（拉满后停在弦上）
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            // ★ 左手（WeaponArms）在 p≈0.84 才把箭送到箭槽，所以箭也那时候出现，
            //   否则箭会先凭空出现在导轨上、手再慢吞吞地过去「假装」放箭。
            boolean hasBolt = cocked || p > 0.84F;
            bolt.setPosY(hasBolt ? 0.0F : BOLT_HIDE_Y);
            bolt.setPosZ(travel);
        }
        // ★ 「只前后动，不上下动」（同 AKM）：角度一律清零，X/Y 一律清零，Z 只由后坐冲量驱动。
        //   以前在开火时给动画的 Z 放行 —— 那是阶跃值，每发都让弩顿一下（「多一帧」）。
        CoreGeoBone move = getAnimationProcessor().getBone("move");
        if (move != null) {
            move.setRotX(0.0F);
            move.setRotY(0.0F);
            move.setRotZ(0.0F);
            move.setPosX(0.0F);
            move.setPosY(0.0F);
            // 后坐：只沿弩身后拖（走 move 骨骼，第一人称手臂读的就是它 ⇒ 手会跟着一起前后动）
            move.setPosZ(KICK_BACK * WeaponAnim.of(WeaponAnim.Kind.CROSSBOW).recoil);
        }

        // 左手动作要用（手臂在 RenderHandEvent 里先画，所以读上一帧的值就够）
        lastProgress = progress;
        lastDraw = draw;

        // ★ 拉弦/装填全靠上面这些**弩自身的动作**表现（弦两段往后转、弦心后退、凸轮盘转、
        //   弩箭滑上弦），再加上 animation.json 里 move 的摆动（低头/后拖/顿挫），
        //   以及第一人称的手臂（左手拉弦 / 递箭）；不做实体手方块。
    }

    /**
     * 手臂（第一人称补画的双臂）用：把**当前帧**的 move 状态直接算进 {@link #frame}。
     *
     * <p>为什么不能等渲染时捕获：手臂在 {@code RenderHandEvent} 里画，**比物品渲染早**，
     * 等物品渲染再捕获就只能拿到上一帧的值 —— 开枪那一瞬间弩和弩手差一帧（「多一帧上下晃」）。
     * 现在 {@link #frame} 只有这一个写入点。
     */
    static void captureNow() {
        frame.capture(0.0F, 0.0F, 0.0F, CB_SCALE, MOVE_PX, MOVE_PY, MOVE_PZ,
                0.0F, 0.0F, KICK_BACK * WeaponAnim.of(WeaponAnim.Kind.CROSSBOW).recoil,
                0.0F, 0.0F, 0.0F);
    }

    // ------------------------------------------------------------------ 左手动作（模型像素）
    /** 十字弩 display 的缩放（models/item/crossbow.json） */
    private static final float CB_SCALE = 0.8F;
    /** 托护木（平时：导轨前段下方）—— 导轨底面 y 0.33 / 前端 z −8.64 */
    private static final float[] ARM_SUPPORT = {0.0F, -0.65F, -6.30F};
    /** 去下面取箭时的位置（在导轨下方、前面） */
    private static final float[] ARM_FETCH = {0.20F, -1.30F, -7.20F};
    private static final float[] TMP_A = new float[3];
    private static final float[] TMP_B = new float[3];

    /**
     * 左手在模型像素空间的目标：护木 → 抓住弦 → 往后拉 → 松手去取箭 → 把箭推上箭槽 → 回护木。
     */
    static float[] leftHandPx(float[] out) {
        float p = lastProgress;
        if (p < 0.0F) return copy(ARM_SUPPORT, out);
        if (p < 0.05F) return copy(ARM_SUPPORT, out);
        if (p < 0.15F) {                                 // 伸手去抓弦
            stringPoint(0.0F, TMP_A);
            return lerp(ARM_SUPPORT, TMP_A, ease((p - 0.05F) / 0.10F), out);
        }
        if (p < 0.62F) return stringPoint(lastDraw, out); // 跟着弦往后拉
        if (p < 0.70F) {                                 // 松手，下去取箭
            stringPoint(1.0F, TMP_A);
            return lerp(TMP_A, ARM_FETCH, ease((p - 0.62F) / 0.08F), out);
        }
        if (p < 0.84F) {                                 // 把箭送到箭槽
            boltPoint(TMP_A);
            return lerp(ARM_FETCH, TMP_A, ease((p - 0.70F) / 0.14F), out);
        }
        if (p < 0.97F) return boltPoint(out);            // 扶着箭，等上弦完成
        boltPoint(TMP_B);                                // 回护木
        return lerp(TMP_B, ARM_SUPPORT, ease((p - 0.97F) / 0.03F), out);
    }

    /** 弦心上的握点（弦心 z = NOCK_Z0 + nockTravel(draw)，手抓在它后面一点、弦面下方） */
    private static float[] stringPoint(float draw, float[] out) {
        out[0] = 0.26F;
        out[1] = 1.30F;
        out[2] = NOCK_Z0 + nockTravel(draw) + 0.30F;
        return out;
    }

    /** 弩箭上的握点（箭尾在弦心上，所以跟着 nockTravel 走） */
    private static float[] boltPoint(float[] out) {
        out[0] = 0.20F;
        out[1] = 1.41F;
        out[2] = -5.80F + nockTravel(lastDraw);
        return out;
    }

    /**
     * 弦锚点（cam / 弦骨骼的 pivot，它在弓臂梢上）在「弓臂绕内端转 θ + 整体后滑 back」后的位移。
     *
     * <p>δ = R(θ)·(A − P) + P − A + (0, 0, back)，其中 A = (side·TIP_X, CAM_Z)、P = (side·FLEX_PX, FLEX_PZ)。
     */
    private static float[] anchorShift(int side, float theta, float back, float[] out) {
        float fpx = side * FLEX_PX;
        float ax = side * TIP_X;
        float adx = ax - fpx;
        float adz = CAM_Z - FLEX_PZ;
        float c = Mth.cos(theta);
        float s = Mth.sin(theta);
        out[0] = (adx * c + adz * s + fpx) - ax;
        out[1] = (-adx * s + adz * c + FLEX_PZ) - CAM_Z + back;
        return out;
    }

    /** 右弓臂内收角（弧度，负 = 外端向内 + 向后） */
    private static float flexTheta(float draw) {
        return -draw * FLEX_DEG * Mth.DEG_TO_RAD;
    }

    /**
     * 弦心相对初始位置的后退量 —— **弦 / 弩箭 / 左手共用的唯一一份**。
     *
     * <p>= 弦锚点被弓臂带走的 z 位移 + 弦绷直所需的后退（弦段长度固定为 Stringlen，
     * 锚点往内移之后，同样的弦能把弦心拉得更靠后），第二项即 L·sin(draw·φ)。
     */
    private static float nockTravel(float draw) {
        float[] sh = anchorShift(1, flexTheta(draw), draw * FLEX_BACK, TMP_SHIFT);
        return sh[1] + STRING_LEN * Mth.sin(draw * PHI_RAD);
    }

    /** nockTravel 用的临时缓冲（渲染单线程） */
    private static final float[] TMP_SHIFT = new float[2];

    /**
     * 弓臂内收：绕「贴导轨的内端」（{@link #FLEX_PX}/{@link #FLEX_PZ}）转 θ、再整体后滑 back，
     * 外端因此**向内 + 向后**走 —— 就是「拉弦时弓臂向内收缩」。
     *
     * <p>GeckoLib 的骨骼变换是 {@code pivot + pos + R(rot)·(p − pivot)}，绕任意点 A 转
     * 等价于「原旋转 + pos 补偿 {@code (A − pivot) − R·(A − pivot)}」
     * 再加一个整体后滑 {@code back}（同一份数学的离线验算在 {@code tools/_cb_flex.py}，带数值自检与出图）。
     * 弦 / 凸轮盘的 pivot 就落在弓臂梢上，所以它们要跟着弓臂**平移**同样的位移，
     * 否则弦会跟弓臂脱开。
     */
    private void flexLimb(String limbName, String camName, String stringName, int side,
                          float theta, float back) {
        CoreGeoBone limb = getAnimationProcessor().getBone(limbName);
        if (limb == null) return;
        float fpx = side * FLEX_PX;
        float dx = fpx - limb.getPivotX();
        float dz = FLEX_PZ - limb.getPivotZ();
        float c = Mth.cos(theta);
        float s = Mth.sin(theta);
        limb.setRotY(theta);
        limb.setPosX(dx - (dx * c + dz * s));
        limb.setPosZ(dz - (-dx * s + dz * c) + back);

        // 弦锚点随弓臂走：δ = R(θ)·(A − P) + P − A，再加弓臂整体后滑的 back
        float[] sh = anchorShift(side, theta, back, new float[2]);
        shift(camName, sh[0], sh[1]);
        shift(stringName, sh[0], sh[1]);
    }

    /** 整段平移骨骼（只挪 pos，不动旋转） */
    private void shift(String boneName, float dx, float dz) {
        CoreGeoBone bone = getAnimationProcessor().getBone(boneName);
        if (bone == null) return;
        bone.setPosX(bone.getPosX() + dx);
        bone.setPosZ(bone.getPosZ() + dz);
    }

    /**
     * GUI 图标 / 掉落物 / 展示框用的**静态姿态**：弦、凸轮盘、弓臂、弩箭全部归位，
     * 弩箭按被渲染那把弩的 {@link #cockedNow} 决定看不看得到（换弹进度是本地玩家的，画图标不能看它）。
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
        for (String name : new String[]{"cam_left", "cam_right", "string_left", "string_right",
                "nock"}) {
            CoreGeoBone bone = getAnimationProcessor().getBone(name);
            if (bone == null) continue;
            bone.setRotX(0.0F);
            bone.setRotY(0.0F);
            bone.setRotZ(0.0F);
            bone.setPosX(0.0F);
            bone.setPosY(0.0F);
            bone.setPosZ(0.0F);
        }
        for (String name : new String[]{"prod_left", "prod_right"}) {
            CoreGeoBone bone = getAnimationProcessor().getBone(name);
            if (bone == null) continue;
            bone.setRotY(0.0F);
            bone.setPosX(0.0F);
            bone.setPosZ(0.0F);
        }
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            bolt.setPosY(cockedNow ? 0.0F : BOLT_HIDE_Y);
            bolt.setPosZ(0.0F);
        }
    }

    private static float[] copy(float[] src, float[] out) {
        System.arraycopy(src, 0, out, 0, 3);
        return out;
    }

    private static float[] lerp(float[] a, float[] b, float t, float[] out) {
        for (int i = 0; i < 3; i++) out[i] = a[i] + (b[i] - a[i]) * t;
        return out;
    }

    /** 平滑（smoothstep） */
    private static float ease(float t) {
        float x = Mth.clamp(t, 0.0F, 1.0F);
        return x * x * (3.0F - 2.0F * x);
    }
}
