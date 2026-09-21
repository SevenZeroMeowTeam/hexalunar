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
 * 十字弩的 GeckoLib 模型（体素，953 方块 / 15 骨骼）。
 *
 * <p>模型由 {@code tools/crossbow_vox.py} 把参考网格 {@code 模型/十字弩_v2.bbmodel}
 * （11 个 mesh 部件的「现代复合弩」：窄弓臂 + 高导轨 + 枪式握把 + 镜筒 + 线缆）**表面体素化**而来，
 * 逐格从原贴图采样 UV；弦 / 弦心 / 弩箭用方块单独画（要能绕弓臂梢转）。
 * 坐标系：以握把中心为原点、弩头朝 −Z，与旧模型同一套（{@code WeaponArms} 的握点不用改）。
 *
 * <p><b>拉弦装弹</b>是连续动作（按住/R 键共 {@code RELOAD_TICKS}=30 tick），所以按
 * {@code CrossbowWeaponItem.reloadProgress} 程序化推骨骼：
 * 弦两段绕弓臂梢（<b>Y 轴</b>）转 φ、弦心后退 {@code draw·DRAW_DZ}、弩箭跟着左手滑上箭槽。
 *
 * <p><b>★ r119 弦改成「一条平行直线 + 拉弦成 V」</b>（用户：「弦恢复平行线，弓臂向外扩展，
 * 有拉弦动画，拉弦弓臂向内收缩，左手上箭，对照图 5 设计」）：
 * <br>· <b>弓臂向外扩展</b>：生成器的 {@code LIMB_SX} 2.05 → 2.40（跨度 10.32 → 11.61 像素），
 *   {@code TIP_X} 随之 5.371 → 5.805（取弓臂网格外缘 ⇒ 弦端点正好落在弓臂梢上）；
 * <br>· <b>弦恢复平行线</b>：每段弦的几何长**改成正好 = TIP_X**（旧版固定 6.221 > 半跨 ⇒
 *   静止时两段在中线重叠交叉，看上去是「两条斜线」）。静止时两段共线 ⇒ 一条笔直的弦；
 * <br>· <b>拉弦</b>：{@link #stringPhi} 解出转角、{@link #stringStretch} 同步给骨骼 scaleX
 *   （弦长 = {@code hypot(x, DRAW_DZ)}）⇒ 弦心精确落在两段内端，形成干净的**内 V**；
 * <br>· <b>拉弦时弓臂向内收缩</b>：{@link #flexLimb} 绕「贴导轨的内端」内转 {@link #FLEX_DEG}°
 *   并整体后滑 {@link #FLEX_BACK}（已上膛则保持内敛，击发才弹回）；
 * <br>· <b>左手上箭</b>：p ∈ (0.70, 0.84) 时弩箭骨骼**跟着左手位移**从导轨下方升到箭槽
 *   （旧版要等到 p > 0.84 才在导轨上凭空出现）。
 *
 * ★ TIP_X / DRAW_DZ / NOCK_Z0 / FLEX_PX / FLEX_PZ 必须与 {@code tools/crossbow_vox.py} 打印的
 *   同名常数一致（生成器末尾会自检「拉满时两段弦的内端落在弦心」「静止时两段共线」）。
 * ★ 上弦完成（cocked）后弦**不往后拉**（贴回两弓臂之间）——拉回去的弦心离镜头更近，
 *   透视下会像一根浮在弩上方的「∧」。
 *
 * <p><b>弓臂内收（r63）</b>：拉弦时两弓臂绕「贴导轨的内端」向内转，外端因此
 * **向内 + 向后**走 —— 看上去就是「弓臂向内收缩」；松开 / 击发后回到参考网格（图片）那个张开姿态。
 * 弦与凸轮盘的 pivot 就在弓臂梢上，所以它们跟着弓臂平移同样的位移，不会脱开。
 */
public class CrossbowGeoModel extends GeoModel<CrossbowWeaponItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/crossbow_geo.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/crossbow_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/crossbow.animation.json");

    /**
     * 弓臂梢到弦心的横向距离（生成器 TIP_X）—— **同时也是每一段弦的几何长度**。
     * ★ r119 弓臂向外扩展（缩放 2.05 → 2.40）后 = **5.805**（生成器现在取**弓臂网格的 X 外缘**，
     * 而不是参考网格里那条比弓臂长 0.85 的 string 网格 ⇒ 弦端点正好搭在弓臂梢 / 凸轮上，
     * 未拉弦时两段各占一半，正好铺满跨度）。
     *
     * <p>★★ r119（用户：「弦恢复平行线 … 有拉弦动画」）—— 弦的**几何长度恒等于 {@link #TIP_X}**，
     * 运行时靠**骨骼 scaleX** 改成实际需要的长度：
     * <br>· 静止（draw = 0）：锚点到弦心的水平距离就是 TIP_X ⇒ 长度 = TIP_X ⇒ {@code scaleX = 1}，
     * 两段共线 ⇒ **渲染出来就是一条笔直的弦**。
     * <br>· 拉满（draw = 1）：锚点被弓臂内收带进来（{@code x = TIP_X + δx}）、弦心后退 DRAW_DZ
     * ⇒ 需要的长度 = {@code hypot(x, DRAW_DZ)} ⇒ {@code scaleX = 该值 / TIP_X}（≈ 0.90）。
     *
     * <p>★ 历史踩坑（r89 / r97）：那时弦的**几何尺寸**被固定写成 6.221（前身是 r71 的「线缆」，
     * 长度刻意做成 {@code tip_x + 0.85}「越过中线形成交叉」），而半跨只有 5.371 ⇒
     * **未拉弦时两段就在中线附近重叠交叉**，看上去是「两条斜线」而不是一条弦 ——
     * 这正是用户 r119 说的「弦不是平行线」。现在几何长度 = 半跨，静止必共线；
     * 而「拉满时长度不够」由 scaleX 补上（真弓里对应凸轮放线）。
     * <p>（旧的 {@code STRING_LEN = 6.221} 与 {@code PHI_RAD} 两个常量已随本次改动删除：
     * 弦长不再固定，转角 φ 与伸缩量都由 {@link #stringPhi}/{@link #stringStretch} 每帧解析求出。）
     */
    private static final float TIP_X = 5.805F;
    /** 拉满时弦心相对**弓臂锚点平面**的净后退距离（生成器 DRAW_DZ） */
    private static final float DRAW_DZ = 1.80F;
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
    /**
     * ★ r85：拉满时两弓臂绕「贴导轨的内端」向内转的角度。
     *
     * <p>从 8° 加到 **13°**：弓臂内收得更多，锚点往里走 ⇒ 固定长度的弦能把弦心拉得更深
     * （用户拿图指的「弦应该是深 V」）。内收量由 {@code tools/_cb_flex.py} 离线验算（它带数值自检）。
     */
    private static final float FLEX_DEG = 13.0F;
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
    /** 上一帧的弓臂内收程度（上膛后钉在 1）—— 弦心/弩箭/左手的位移都要跟它一致 */
    private static float lastFlex = 0.0F;

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
        // ★ r73（用户要求）：上弦完成后**弦保持 V 字形**（拉着）—— 以前上膛后弦会贴回两弓臂之间
        //   （draw = 0），看着就像“没上弦”。现在 cocked 时 draw 钉在 1：弦成 V、弦心/弩箭都在后位，
        //   击发那一刻才弹回（并触发弦震动）。
        float draw = cocked ? 1.0F : Mth.clamp(p / 0.65F, 0.0F, 1.0F);
        float load = cocked ? 1.0F : Mth.clamp((p - 0.55F) / 0.45F, 0.0F, 1.0F);
        // ★ r69：把「弓臂向内收多少」与「弦被拉多深」分成两个量：
        //   · 拉弦时弓臂内收 = 拉的进度（0→1）
        //   · **上完膛保持内敛**（cocked 时钉在 1，不弹回去），击发后才回到张开姿态
        //   r73 起弦在上膛后也保持拉着（draw = 1）⇒ V 字形，只有击发才弹回。
        float flexAmt = cocked ? 1.0F : draw;

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

        // ★ r119：弦两段绕弓臂梢（Y 轴）转 φ —— 左 -φ、右 +φ，内端精确落在弦心；
        //   同时把**骨骼 scaleX** 设成「实际需要的长度 / 几何长度（= TIP_X）」：
        //   静止时它正好是 1（两段共线 ⇒ 一条笔直的平行弦），拉满时锚点内移 ⇒ 略缩（≈0.90）。
        float phi = stringPhi(flexAmt, draw);
        float stretch = stringStretch(flexAmt, draw);
        CoreGeoBone left = getAnimationProcessor().getBone("string_left");
        CoreGeoBone right = getAnimationProcessor().getBone("string_right");
        if (left != null) {
            left.setRotY(-draw * phi + tw);
            left.setScaleX(stretch);
        }
        if (right != null) {
            right.setRotY(draw * phi - tw);
            right.setScaleX(stretch);
        }

        // ★ 弓臂内收（r63/r64/r65）：拉弦时两弓臂绕「贴导轨的内端」向内转 + 整体往射手方向滑 ——
        //   外端**向内约 0.5 + 向后约 0.7**（用户选的「又向内又向后」），松开/击发后回到
        //   参考网格（图片）那个张开姿态。弦与凸轮盘挂在弓臂梢上，跟着走。
        //   ★ 弦锚点因此产生的位移要用到弦心/弩箭/左手上（见 nockTravel），三者必须严格一致，
        //   否则弦会落在弦心后面（拉满时差 0.36 像素，肉眼就是“弦没贴住弦心”）。
        float flex = flexAmt * FLEX_DEG * Mth.DEG_TO_RAD;
        float back = flexAmt * FLEX_BACK;
        flexLimb("prod_right", "cam_right", "string_right", 1, -flex, back);
        flexLimb("prod_left", "cam_left", "string_left", -1, flex, back);

        // 复合十字弩：拉弦时两个凸轮盘跟着转（弦从凸轮上放/收）
        CoreGeoBone camL = getAnimationProcessor().getBone("cam_left");
        CoreGeoBone camR = getAnimationProcessor().getBone("cam_right");
        if (camL != null) camL.setRotY(-draw * CAM_SPIN);
        if (camR != null) camR.setRotY(draw * CAM_SPIN);

        // 弦心（缠绳）随拉弦后退：行程 = 弦绷直所需（弦段长度固定 ⇒ 锚点内移后能拉得更深）+ 弓臂后滑量；
        // 震动时跟着弦心一起前后抖（弦在 X 上的半投影 = TIP_X）
        float travel = nockTravel(flexAmt, draw);
        CoreGeoBone nock = getAnimationProcessor().getBone("nock");
        if (nock != null) {
            nock.setPosZ(travel - TIP_X * tw);
            nock.setPosY(0.0F);
        }

        // 弩箭：没装填时挪到看不见；装填时滑到弦心（拉满后停在弦上）
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            // ★★ r119（用户：「左手上箭」）：箭**跟着左手一起从下面升上来**，而不是等到
            //   p > 0.84 才在导轨上凭空出现。手在 p = 0.70 落到最低点（ARM_FETCH，相当于
            //   「从箭袋取箭」），所以箭从那时起出现、并贴着手的位移一起升到箭槽；
            //   p >= 0.84 手把箭推到箭槽，箭归位到导轨（之后弦一放就把箭射出去）。
            if (cocked || p >= 0.84F) {
                bolt.setPosY(0.0F);
                bolt.setPosZ(travel);
            } else if (p > 0.70F) {
                leftHandPx(p, TMP_BOLT);
                bolt.setPosY(TMP_BOLT[1] - BOLT_GRIP_Y + BOLT_HAND_LIFT);
                bolt.setPosZ(TMP_BOLT[2] - BOLT_GRIP_Z);
            } else {
                bolt.setPosY(BOLT_HIDE_Y);
                bolt.setPosZ(0.0F);
            }
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
        lastFlex = flexAmt;

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
        WeaponHandGrip.pushAds(WeaponAnim.Kind.CROSSBOW, ItemStack.EMPTY, null);   // 弩不叠举枪位移
        frame.capture(0.0F, 0.0F, 0.0F, CB_SCALE, MOVE_PX, MOVE_PY, MOVE_PZ,
                0.0F, 0.0F, KICK_BACK * WeaponAnim.of(WeaponAnim.Kind.CROSSBOW).recoil,
                0.0F, 0.0F, 0.0F,
                Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.CROSSBOW).aim, 0.0F, 1.0F));  // 持枪姿态（GunPose）
    }

    // ------------------------------------------------------------------ 左手动作（模型像素）
    /** 十字弩 display 的缩放（models/item/crossbow.json） */
    private static final float CB_SCALE = 0.8F;
    /** 托护木（平时：导轨前段下方）—— 导轨底面 y 0.33 / 前端 z −8.64 */
    private static final float[] ARM_SUPPORT = {0.0F, -0.65F, -6.30F};
    /** 去下面取箭时的位置（在导轨下方、前面） */
    private static final float[] ARM_FETCH = {0.20F, -1.30F, -7.20F};
    /**
     * ★ r119「左手上箭」：弩箭在模型里的**手持抓点** —— 箭身中心的 y / 手抓的 z
     * （z 与 {@link #boltPoint} 一致，y 取导轨顶面 + 0.16）。
     */
    private static final float BOLT_GRIP_Y = 1.76F;
    private static final float BOLT_GRIP_Z = -5.80F;
    /** 箭压在掌心上方一点（否则箭会跟手方块重叠） */
    private static final float BOLT_HAND_LIFT = 0.22F;
    private static final float[] TMP_A = new float[3];
    private static final float[] TMP_B = new float[3];
    /** 画「左手上的箭」用的临时缓冲（不能跟 TMP_A/TMP_B 共用） */
    private static final float[] TMP_BOLT = new float[3];

    /**
     * 左手在模型像素空间的目标：护木 → 抓住弦 → 往后拉 → 松手去取箭 → 把箭推上箭槽 → 回护木。
     */
    static float[] leftHandPx(float[] out) {
        return leftHandPx(lastProgress, out);
    }

    /**
     * 左手在模型像素空间的目标（**指定进度版本**）。
     *
     * <p>★ r119「左手上箭」：{@link #setCustomAnimations} 画「左手上的箭」时要用**当前帧**的 p
     * （{@link #leftHandPx(float[])} 读的是上一帧的 {@code lastProgress}）——
     * 否则箭会比手晚一帧，看上去就是「手到了、箭还在下面」。
     */
    static float[] leftHandPx(float p, float[] out) {
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
        if (p < 0.92F) return boltPoint(out);            // 扶着箭，等上弦完成
        // ★ r84：回护木用更长的窗口（0.92~1.00，约 3~4 tick）—— 原先最后 3% 里从箭槽甩回护木，
        //   看着就是「上弦完成手臂向下晃一下」；现在平滑滑回。
        boltPoint(TMP_B);                                // 回护木
        return lerp(TMP_B, ARM_SUPPORT, ease((p - 0.92F) / 0.08F), out);
    }

    /** 弦心上的握点（弦心 z = NOCK_Z0 + nockTravel(lastFlex, draw)，手抓在它后面一点、弦面下方） */
    private static float[] stringPoint(float draw, float[] out) {
        out[0] = 0.26F;
        out[1] = 1.30F;
        out[2] = NOCK_Z0 + nockTravel(lastFlex, draw) + 0.30F;
        return out;
    }

    /** 弩箭上的握点（箭尾在弦心上，所以跟着 nockTravel 走） */
    private static float[] boltPoint(float[] out) {
        out[0] = 0.20F;
        out[1] = 1.41F;
        out[2] = -5.80F + nockTravel(lastFlex, lastDraw);
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

    /**
     * 拉弦时弦两段绕锚点的转角（弧度）：**由几何解出来**，不再是固定的 {@link #PHI_RAD}。
     *
     * <p>弦段长度 {@link #STRING_LEN} 是固定的，而弓臂内收后锚点横向距离变成
     * {@code x = TIP_X + δx} ⇒ 弦能拉到的最深处（弦心相对锚点平面）就是
     * {@code depth = √(L² − x²)}，转角 {@code φ = atan2(depth, x)}。
     * 把它代回「弦心后退量」与弦骨骼转角，弦的两段内端依旧精确交在弦心上（不会拉过头/拉不够）。
     */
    private static float stringPhi(float flexAmt, float draw) {
        return (float) Math.atan2(draw * DRAW_DZ, anchorX(flexAmt));
    }

    /**
     * ★ r119：弦骨需要的 **scaleX** = 实际需要的长度 / 几何长度（= {@link #TIP_X}）。
     *
     * <p>静止 draw = 0 时锚点到弦心的水平距离就是 TIP_X ⇒ 返回 1（两段共线，一条笔直的弦）；
     * 拉满时锚点被弓臂带进来（x = TIP_X + δx）、弦心后退 DRAW_DZ ⇒
     * 返回 {@code hypot(x, DRAW_DZ) / TIP_X}（≈ 0.90，弦略缩 —— 视觉上弦只会短 10%，看不出来）。
     */
    private static float stringStretch(float flexAmt, float draw) {
        float x = anchorX(flexAmt);
        float pull = draw * DRAW_DZ;
        return Mth.sqrt(x * x + pull * pull) / TIP_X;
    }

    /** 弓臂内收后弦锚点（弓臂梢）的横向位置：TIP_X + δx */
    private static float anchorX(float flexAmt) {
        float[] sh = anchorShift(1, flexTheta(flexAmt), flexAmt * FLEX_BACK, TMP_SHIFT);
        return TIP_X + sh[0];
    }

    /** 弓臂内收后弦锚点平面的 z 位移（含弓臂整体后滑 back） */
    private static float anchorDz(float flexAmt) {
        float[] sh = anchorShift(1, flexTheta(flexAmt), flexAmt * FLEX_BACK, TMP_SHIFT);
        return sh[1];
    }

    /** 右弓臂内收角（弧度，负 = 外端向内 + 向后） */
    private static float flexTheta(float draw) {
        return -draw * FLEX_DEG * Mth.DEG_TO_RAD;
    }

    /**
     * 弦心相对初始位置的后退量 —— **弦 / 弩箭 / 左手共用的唯一一份**。
     *
     * <p>= 弦锚点被弓臂带走的 z 位移（弓臂内收 flexAmt） + 弦绷直所需的后退
     * （弦段长度固定为 STRING_LEN，锚点往内移之后，同样的弦能把弦心拉得更靠后）：
     * 第二项即 {@code L·sin(draw·φ)}，φ 用 {@link #stringPhi}（**随弓臂内收变**）。
     */
    private static float nockTravel(float flexAmt, float draw) {
        // ★ r119：弦心 = 两段弦的内端交汇处 ⇒ z 就是「锚点平面的位移 + 弦心净后退量」。
        //   净后退量 = draw·DRAW_DZ（弦长由骨骼 scaleX 保证），不再需要反解 φ
        //   —— 旧版用「固定弦长 6.221」反解，实际拉深到 3.12 px，远超设计的 1.80。
        return anchorDz(flexAmt) + draw * DRAW_DZ;
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
     * GUI 图标 / 掉落物 / 展示框用的**静态姿态**：按 {@link #cockedNow} 摆成「未上弦」或「已上弦」：
     *
     * <p>· 未上弦：弓臂张开（未内收）、弦贴回两弓臂之间（一条直线平行于导轨顶面）、看不到弩箭
     * <br>· 已上弦：弓臂内敛（缩小的 U）、**弦拉成 V 字形**、弩箭在箭槽里
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
            // ★ r119：弦的伸缩也归位（否则掠过一帧拉满的图标之后，弦会一直缩着）
            bone.setScaleX(1.0F);
            bone.setScaleY(1.0F);
            bone.setScaleZ(1.0F);
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
        // ★ r73：已上弦的图标要跟手持时一个样子 —— 弦成 V、弓臂内敛、弩箭（弦心）在后位
        if (!cockedNow) return;
        float flex = FLEX_DEG * Mth.DEG_TO_RAD;
        flexLimb("prod_right", "cam_right", "string_right", 1, -flex, FLEX_BACK);
        flexLimb("prod_left", "cam_left", "string_left", -1, flex, FLEX_BACK);
        CoreGeoBone left = getAnimationProcessor().getBone("string_left");
        CoreGeoBone right = getAnimationProcessor().getBone("string_right");
        float phiC = stringPhi(1.0F, 1.0F);
        float stretchC = stringStretch(1.0F, 1.0F);
        if (left != null) {
            left.setRotY(-phiC);
            left.setScaleX(stretchC);
        }
        if (right != null) {
            right.setRotY(phiC);
            right.setScaleX(stretchC);
        }
        float travel = nockTravel(1.0F, 1.0F);
        CoreGeoBone nock = getAnimationProcessor().getBone("nock");
        if (nock != null) {
            nock.setPosZ(travel);
            nock.setPosY(0.0F);
        }
        if (bolt != null) bolt.setPosZ(travel);
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
