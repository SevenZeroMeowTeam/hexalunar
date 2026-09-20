package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem;
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
 * AWP 的 GeckoLib 模型定义 + 程序化骨骼细节。
 *
 * <h2>资源</h2>
 * <ul>
 *   <li>几何 {@code geo/awp.geo.json}：13 骨骼 / 58 方块 / 512² 逐面 UV</li>
 *   <li>贴图 {@code textures/models/awp_geo.png}（+ {@code _glowmask} 供流光层）</li>
 *   <li>动画 {@code animations/awp.animation.json}（控制器 {@code main}）</li>
 * </ul>
 *
 * <h2>骨骼</h2>
 * {@code root → move → body → barrel → bipod / scope → scope_adjust / scope_elev / scope_wind /
 * magazine / bolt / trigger / casing}。朝向：枪口 = -Z、上 = +Y、原点 = 机匣中心。
 *
 * <h2>为什么换弹/拉栓/抛壳要程序化推骨骼</h2>
 * 动画 JSON 是「固定秒数」，而实际时长由物品 NBT 的 {@code RELOAD_TICKS / BOLT_TICKS} 决定。
 * 按 NBT 进度推骨骼，读条和动作永远对得上；弹壳也就不用「计时槽」，
 * 直接由 {@code boltProgress} 算出「被枪机带出 → 边翻边抛向右上方」这条轨迹。
 */
public class AwpGeoModel extends GeoModel<AwpRifleItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/awp.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/awp_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/awp.animation.json");

    /**
     * 当前这一遍渲染是不是「拿在手上」（第一/第三人称；由 {@link AwpGeoRenderer} 设入）。
     * GeckoLib 的 {@code setCustomAnimations} 对 GUI 图标 / 掉落物 / 展示框一样会跑，
     * 不判断的话「举枪位移 + 后坐 + 抛壳」会跑到物品栏图标上。
     */
    static boolean handPass = false;

    /** 开火后坐：**r84 起不再推枪**（改成只推镜头，见 ClientEvents.applyRecoilKick） */
    private static final float KICK_BACK_UNUSED = 1.9F;

    /** move 骨骼 pivot（geo 里的值）—— 第一人称手臂靠它把骨骼位移换算成相机空间 */
    private static final float MOVE_PX = 0.0F;
    private static final float MOVE_PY = -1.0725F;
    private static final float MOVE_PZ = 1.305F;

    /**
     * 当前这一帧的枪本体变换（给第一人称手臂用，见 {@link GunFrame} / {@link WeaponArms}）。
     *
     * <p>手臂在 {@code RenderHandEvent} 里画，**比物品渲染早**，靠「渲染时捕获」只能拿到上一帧的值
     * —— 开火那一瞬枪和手会差一帧。所以这里由 {@link #captureNow()} 主动算当前帧。
     */
    static final GunFrame frame = new GunFrame();

    /** move 姿态临时缓冲（骨骼与手臂共用；客户端渲染单线程，不会并发） */
    private static final float[] MOVE_POSE = new float[6];

    /**
     * 拉栓：拉机柄上抬角（度）—— r84 由 62° 提到 **88°**（几乎竖直），抡柄的动作一眼能看见；
     * 88° 时柄头到 Y≈2.14，仍在 8 倍镜筒（底面 2.75）之下，不会穿模。
     * 与 {@code animation.awp.bolt}、{@code tools/_awp_arms.py} 里的值保持一致。
     */
    private static final float BOLT_LIFT = 88.0F;
    /** 拉栓：枪机后退量（模型像素）—— r87 由 3.4 提到 **4.2**（≈26cm，比真实栓动略长但看得清抽壳行程） */
    private static final float BOLT_BACK = 4.2F;
    /** {@code bolt} 骨骼 pivot（geo 里的值）—— 拉机柄绕它抬起来 */
    private static final float BOLT_PX = 0.615F;
    private static final float BOLT_PY = 1.50F;
    private static final float BOLT_PZ = 0.375F;
    /** 拉机柄握点相对 pivot 的偏移（模型像素）：柄头 x[0.87,1.2525]，手再往外一点正好包住 */
    private static final float BOLT_GRIP_DX = 0.685F;
    private static final float BOLT_GRIP_DY = -0.05F;
    /**
     * 右手「从握把摸到拉机柄」（{@code BOLT_HAND_IN} 之前）与「拉完立即回握把」的区间。
     * r84：枪机一拉到底（0.60）就松手，在 {@code BOLT_HAND_SNAP}（约 1.8 tick）里**快速**回到握把，
     * 不再一路跟着枪机慢慢滑回去。
     */
    private static final float BOLT_HAND_IN = 0.18F;
    private static final float BOLT_HAND_OUT = 0.60F;
    /** 回握把用多少进度（r84：0.08 → 0.18，约 4 tick；太快就是「手向下甩一下」） */
    private static final float BOLT_HAND_SNAP = 0.18F;
    /** 击发：扣扳机（绕顶部销轴向后转 11°，与 animation.awp.fire 一致） */
    private static final float TRIGGER_PULL = 11.0F;

    /** 换弹：弹匣掉落距离 / 前倾角 */
    private static final float MAG_DROP = 2.6F;
    private static final float MAG_TILT = 26.0F;

    // ------------------------------------------------------------------ 抛壳轨迹
    /** 抛壳窗口在拉栓进度里的位置：抽壳结束才被抛壳挺顶出去（r84 窗口延长到 0.80，飞行看得更清楚） */
    private static final float CASE_T0 = 0.12F;
    private static final float CASE_T1 = 0.80F;
    /**
     * 被枪机抽出的距离 / 抛出的初速（模型像素）—— r84 整条弧线加大：
     * 抽出 1.5 → **3.0**（跟得上 3.4 的枪机行程），抛向 +X 3.4 → **5.0**、向上初速 1.7 → 2.2，
     * 让弹壳从抛壳口翻出去时**离开枪身与右臂**，能看清它三轴翻滚地飞走。
     */
    private static final float CASE_BACK = 3.0F;
    private static final float CASE_VX = 5.0F;    // ★ r107：右抛壳（+X），原来是 -5 往左飞
    private static final float CASE_VY = 2.2F;
    private static final float CASE_G = 0.8F;
    /** 三轴翻滚（度） */
    private static final float CASE_SPIN_Z = -240.0F;   // ★ r107：自转方向跟着镜像
    private static final float CASE_SPIN_X = 150.0F;
    private static final float CASE_SPIN_Y = 90.0F;

    @Override
    public ResourceLocation getModelResource(AwpRifleItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(AwpRifleItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(AwpRifleItem animatable) {
        return ANIMATION;
    }

    @Override
    public void setCustomAnimations(AwpRifleItem animatable, long instanceId,
                                    AnimationState<AwpRifleItem> state) {
        if (!handPass) {
            staticPose();
            return;
        }
        ItemStack stack = AwpAnimState.heldStack();
        long now = AwpAnimState.now();

        // ---------------------------------------------------------- 举枪（ADS）
        // ★ 举枪只做平移：叠任何角度都会让「8 倍镜光轴」离开屏幕中心。
        //   腰射同样不给任何角度 —— 与 AKM 完全同一套持枪规则（见 computeMovePose）
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

        // ---------------------------------------------------------- 拉栓
        float bp = stack == null ? -1.0F : AwpRifleItem.boltProgress(stack, now);
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            bolt.setRotX(0.0F);
            bolt.setRotY(0.0F);
            bolt.setRotZ(boltLiftAt(bp) * BOLT_LIFT * Mth.DEG_TO_RAD);
            bolt.setPosX(0.0F);
            bolt.setPosY(0.0F);
            bolt.setPosZ(boltBackAt(bp) * BOLT_BACK);
        }

        // ---------------------------------------------------------- 扣扳机
        // ★ 不能靠 animation.awp.fire：击发同一帧就开始拉栓，控制器优先拉栓（bolt > fire），
        //   那段 11° 的扣扳机键帧永远轮不到。改成按 fireWindow 推骨骼，一扣就有。
        CoreGeoBone trigger = getAnimationProcessor().getBone("trigger");
        if (trigger != null) {
            float fw = stack == null ? -1.0F : AwpRifleItem.fireWindow(stack, now);
            trigger.setRotX(-TRIGGER_PULL * triggerPullAt(fw) * Mth.DEG_TO_RAD);
        }

        // ---------------------------------------------------------- 抛壳（跟着拉栓进度）
        CoreGeoBone casing = getAnimationProcessor().getBone("casing");
        if (casing != null) {
            if (bp < CASE_T0 || bp > CASE_T1) {
                casing.setHidden(true);
            } else {
                casing.setHidden(false);
                float c = (bp - CASE_T0) / (CASE_T1 - CASE_T0);      // 窗口内 0..1
                float out = Mth.clamp((c / 0.22F), 0.0F, 1.0F);      // 先跟枪机抽出来
                float fly = Mth.clamp((c - 0.22F) / 0.78F, 0.0F, 1.0F);   // 再被顶出去
                casing.setPosX(CASE_VX * fly);
                casing.setPosY(CASE_VY * fly - CASE_G * fly * fly);
                casing.setPosZ(CASE_BACK * out - 1.2F * fly);
                casing.setRotZ(fly * CASE_SPIN_Z * Mth.DEG_TO_RAD);
                casing.setRotX(fly * CASE_SPIN_X * Mth.DEG_TO_RAD);
                casing.setRotY(fly * CASE_SPIN_Y * Mth.DEG_TO_RAD);
            }
        }

        // ---------------------------------------------------------- 换弹（弹匣）
        float rp = stack == null ? -1.0F : AwpRifleItem.reloadProgress(stack, now);
        CoreGeoBone mag = getAnimationProcessor().getBone("magazine");
        if (mag != null) {
            mag.setHidden(rp >= 0.0F && magHidden(rp));   // 旧匣掉出去的那段直接藏
            float drop = rp < 0.0F ? 0.0F : magDropAt(rp);
            mag.setPosX(0.0F);
            mag.setPosY(-MAG_DROP * drop);
            mag.setPosZ(-0.5F * drop);
            mag.setRotX(MAG_TILT * drop * Mth.DEG_TO_RAD);
        }
    }

    /**
     * move 骨骼当前帧的目标姿态 {@code {posX,posY,posZ,rotX,rotY,rotZ}}（模型像素 / 弧度）。
     *
     * <p>骨骼与手臂**共用这一份**：{@link #captureNow()} 也调它，所以枪和手不会差一帧。
     * 举枪只做平移（叠角度会把 8 倍镜光轴推离屏幕中心）；后坐只沿枪管后拖。
     *
     * <p>★ 三个角度**恒为 0** —— 与 AKM 完全同一套持枪规则：枪管轴线始终平行于视线。
     * r82 曾给过第一人称 −14° 的腰射下压角，那等于让枪在世界里真的朝下 14°（看着就是「枪口下垂」），
     * 已按用户要求去掉。将来若还要调屏幕上的倾斜感，请改 display 旋转并同步 {@link WeaponMount}。
     */
    static void computeMovePose(float[] out) {
        // ★★ r85：举枪位移**不再推 move 骨骼**（改由 GunPose 在 pose 层施加，见
        //   {@link WeaponHandGrip#pushAds}）；骨骼一律零位移、零角度：
        //   · 举枪（ADS）：pose 层平移 —— 把眼睛贴到目镜上、镜筒光轴顶到屏幕中心
        //   · 开火后坐（★ r93）：pose 层的 **firePitch 绕手俯仰** —— 枪管微抬 + 枪托微沉
        //     （以前是整枪 lift 平抬，枪托会跟着往上走，不符合「枪托下沉」的手感）
        //   · 后坐：同时推镜头（{@code ClientEvents.applyRecoilKick}）
        out[0] = 0.0F;
        out[1] = 0.0F;
        out[2] = 0.0F;
        out[3] = 0.0F;
        out[4] = 0.0F;
        out[5] = 0.0F;
    }

    /**
     * 手臂用：把**当前帧**的 move 姿态直接算进 {@link #frame}。
     *
     * <p>平移量用的是 {@link WeaponMount} 里那份与 {@code models/item/awp.json} 一致的 display，
     * 所以手臂拿到的手位和物品渲染出来位置完全一致。
     */
    static void captureNow() {
        computeMovePose(MOVE_POSE);
        // 举枪位移/开火上抬（相机空间、格）写进 GunPose：手臂与枪共用同一份
        Player local = Minecraft.getInstance().player;
        WeaponHandGrip.pushAds(WeaponAnim.Kind.AWP, local == null ? ItemStack.EMPTY
                : local.getMainHandItem(), local);
        frame.capture(WeaponMount.AWP_TX, WeaponMount.AWP_TY, WeaponMount.AWP_TZ, 1.0F,
                MOVE_PX, MOVE_PY, MOVE_PZ,
                MOVE_POSE[0], MOVE_POSE[1], MOVE_POSE[2],
                MOVE_POSE[3], MOVE_POSE[4], MOVE_POSE[5],
                Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.AWP).aim, 0.0F, 1.0F));   // 持枪姿态（GunPose）
    }

    // ------------------------------------------------------------------ 左手动作（模型像素）
    // 手臂本体在 WeaponArms 里画；这里只回答「左手这一刻该在枪的哪个位置」。
    /** 平时：托在护木下方（狙击手的支撑手一直在这里；再往前就是折叠的两脚架了） */
    private static final float[] ARM_SUPPORT = {0.0F, -0.55F, -3.30F};
    /** 换弹：弹匣握点 */
    private static final float[] ARM_MAG = {0.0F, -0.95F, -1.95F};
    /** magazine 骨骼 pivot（geo 里的值） */
    private static final float MAG_PY = 0.0F;
    private static final float MAG_PZ = 0.90F;
    private static final float[] TMP_A = new float[3];

    /** 左手目标：换弹时伸手去抓弹匣（跟着它一起下坠），其余时间托在枪管下方 */
    static float[] leftHandPx(float[] out) {
        float rp = localReloadProgress();
        if (rp < 0.0F) {
            copy(ARM_SUPPORT, out);
        } else {
            magPoint(rp, TMP_A);
            if (rp < 0.12F) lerp(ARM_SUPPORT, TMP_A, ease(rp / 0.12F), out);
            else if (rp < 0.82F) copy(TMP_A, out);
            else lerp(TMP_A, ARM_SUPPORT, ease((rp - 0.82F) / 0.18F), out);
        }
        return out;      // 开火微抬改由 GunPose 的 lift（枪+双手一起抬），这里不再自己加
    }

    /** 弹匣上的握点（跟着弹匣下移 + 前倾） */
    private static float[] magPoint(float p, float[] out) {
        float drop = magDropAt(p);
        float tilt = MAG_TILT * drop * Mth.DEG_TO_RAD;
        float dy = ARM_MAG[1] - MAG_PY;
        float dz = ARM_MAG[2] - MAG_PZ;
        float c = Mth.cos(tilt);
        float s = Mth.sin(tilt);
        out[0] = ARM_MAG[0];
        out[1] = MAG_PY + (dy * c - dz * s) - MAG_DROP * drop;
        out[2] = MAG_PZ + (dy * s + dz * c);
        return out;
    }

    /**
     * 换弹时弹匣的「退出程度」0..1（0 = 就位，1 = 完全退出）—— 骨骼与手臂同一份。
     *
     * <p>★ r84：旧匣退到底后**继续往下掉**（>1 的部分），到 1.30 倍行程时已经被
     * {@link #magHidden} 藏起来（= 掉在地上）；新匣再从 1.30 倍处升上来卡回井里。
     * 一根骨骼演完「退旧匣 + 插新匣」两个动作，不带世界实体（TaCZ 也是这个做法）。
     */
    private static float magDropAt(float p) {
        if (p < 0.0F) return 0.0F;
        if (p < 0.28F) return ease(p / 0.28F);
        if (p < 0.46F) return 1.0F + 0.30F * ease((p - 0.28F) / 0.18F);         // 旧匣继续往下掉
        if (p < 0.58F) return 1.30F;                                            // 空窗（匣已经掉出去了）
        if (p < 0.80F) return 1.30F * (1.0F - ease((p - 0.58F) / 0.22F));        // 新匣从下面顶上来
        return 0.0F;                                                            // 到位
    }

    /** 旧匣掉出去了、新匣还没上来的那段：藏起来（否则会看成「滑下去又滑回来」） */
    private static boolean magHidden(float p) {
        return p >= 0.38F && p < 0.58F;
    }

    private static float ease(float t) {
        float x = Mth.clamp(t, 0.0F, 1.0F);
        return x * x * (3.0F - 2.0F * x);
    }

    private static float[] copy(float[] src, float[] out) {
        System.arraycopy(src, 0, out, 0, 3);
        return out;
    }

    private static float[] lerp(float[] a, float[] b, float t, float[] out) {
        for (int i = 0; i < 3; i++) out[i] = a[i] + (b[i] - a[i]) * t;
        return out;
    }

    /**
     * 拉机柄抬高量 0..1（骨骼与右手共用同一份 —— 手才跟得住枪机）：
     * 抬起 → 保持 → 末端压回。
     */
    private static float boltLiftAt(float bp) {
        if (bp < 0.0F) return 0.0F;
        if (bp < 0.20F) return bp / 0.20F;
        if (bp > 0.85F) return Mth.clamp((1.0F - bp) / 0.15F, 0.0F, 1.0F);
        return 1.0F;
    }

    /** 枪机后退量 0..1：后退 → 保持 → 推回（同样骨骼 / 手共用） */
    private static float boltBackAt(float bp) {
        if (bp < 0.0F) return 0.0F;
        return Mth.clamp((bp - 0.20F) / 0.35F, 0.0F, 1.0F)
                * (1.0F - Mth.clamp((bp - 0.62F) / 0.32F, 0.0F, 1.0F));
    }

    /** 扣扳机的压下量 0..1：快扣 → 慢放（-1 = 不在击发窗口里） */
    private static float triggerPullAt(float fw) {
        if (fw < 0.0F) return 0.0F;
        if (fw < 0.25F) return ease(fw / 0.25F);
        return ease(Mth.clamp((1.0F - fw) / 0.75F, 0.0F, 1.0F));
    }

    // ------------------------------------------------------------------ 右手动作（模型像素）
    /** 平时：握把（= move 骨骼 pivot，枪就画在这只手上） */
    private static final float[] ARM_GRIP = {0.0F, -1.07F, 1.31F};
    private static final float[] TMP_B = new float[3];

    /**
     * 右手目标：平时握住握把（食指正在扳机上），拉栓时抬起来抓拉机柄、
     * 跟着枪机一起抬起 / 后退，拉完再回到握把。换弹不动右手（换弹匣是左手的活）。
     */
    static float[] rightHandPx(float[] out) {
        float bp = localBoltProgress();
        if (bp < 0.0F) {
            copy(ARM_GRIP, out);
        } else {
            boltHandlePoint(bp, TMP_B);
            if (bp < BOLT_HAND_IN) {
                lerp(ARM_GRIP, TMP_B, ease(bp / BOLT_HAND_IN), out);
            } else if (bp < BOLT_HAND_OUT) {
                copy(TMP_B, out);
            } else {
                lerp(TMP_B, ARM_GRIP,
                        ease(Mth.clamp((bp - BOLT_HAND_OUT) / BOLT_HAND_SNAP, 0.0F, 1.0F)), out);
            }
        }
        return out;      // ★ r85：开火微抬改由 GunPose 的 lift —— 整把枪与双手一起抬
    }

    /** 拉机柄握点（模型空间的绝对点）：绕 bolt pivot 抬起 LIFT 角，再随枪机后退 */
    private static float[] boltHandlePoint(float bp, float[] out) {
        float lift = boltLiftAt(bp) * BOLT_LIFT * Mth.DEG_TO_RAD;
        float c = Mth.cos(lift);
        float s = Mth.sin(lift);
        out[0] = BOLT_PX + (BOLT_GRIP_DX * c - BOLT_GRIP_DY * s);
        out[1] = BOLT_PY + (BOLT_GRIP_DX * s + BOLT_GRIP_DY * c);
        out[2] = BOLT_PZ + boltBackAt(bp) * BOLT_BACK;
        return out;
    }

    /** 本地玩家主手 AWP 的拉栓进度；没拿 / 没拉栓（含击发后那几帧停顿）返回 -1 */
    static float localBoltProgress() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return -1.0F;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof AwpRifleItem)) return -1.0F;
        return AwpRifleItem.boltProgress(stack, player.level().getGameTime());
    }

    /** 本地玩家主手 AWP 的换弹进度；没拿 / 没换弹返回 -1 */
    static float localReloadProgress() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return -1.0F;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof AwpRifleItem)) return -1.0F;
        return AwpRifleItem.reloadProgress(stack, player.level().getGameTime());
    }

    /**
     * GUI 图标 / 掉落物 / 展示框用的**静态姿态**：把一切动作归位（举枪位移、后坐、拉栓、
     * 换弹的弹匣、抛壳全部清零并藏起弹壳）。
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
            casing.setHidden(true);                 // 静止时弹壳收在机匣里，本来也看不见
        }
    }
}
