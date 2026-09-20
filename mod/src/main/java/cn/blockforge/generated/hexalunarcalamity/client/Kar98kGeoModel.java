package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.weapon.Kar98kItem;
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
 * Kar98k 的 GeckoLib 模型定义 + 程序化骨骼细节（照 {@link AwpGeoModel} 的那一套写）。
 *
 * <h2>资源</h2>
 * <ul>
 *   <li>几何 {@code geo/kar98k.geo.json}（由 {@code tools/kar98k_gen.py} 生成，11 骨骼 / 29 方块）</li>
 *   <li>贴图 {@code textures/models/kar98k_geo.png}（+ {@code _glowmask} 供流光层）</li>
 *   <li>动画：★ <b>直接复用 {@code animations/awp.animation.json}</b> ——
 *       Kar98k 的骨骼名与 AWP 基本一致（这正是 {@code kar98k_gen.py} docstring 的要求），
 *       所以 {@code idle / run / run_fast / fire / bolt / reload} 六段动画一条都不用重写；
 *       只多一根 {@code round_in}（压弹那一发），它由本类**程序化**驱动</li>
 * </ul>
 *
 * <h2>与 AWP 不同的三个数（都由 kar98k.geo.json 量出来）</h2>
 * <ol>
 *   <li><b>拉机柄抬升角 64°</b>（AWP 88°）：Kar98k 是**下弯柄**，柄头挂在 x≈1.25、y≈1.75，
 *       绕 bolt pivot（y=2.95）抬起来时柄头很快顶到 4 倍镜筒底面（y=3.95）。
 *       算下来 θ &gt; 71° 时柄身会从镜筒底面捅进去，取 64° 留 7° 余量。</li>
 *   <li><b>枪机后退 2.6 px</b>（AWP 4.2）：Kar98k 机匣短（z −2.4…1.2）、枪机本体 3.0 长，
 *       退 2.6 正好把枪机抽出机匣。</li>
 *   <li><b>右手握点</b>：下弯柄的柄头（{@code BOLT_GRIP_DX/DY}），抬柄时手跟着一起抬高。</li>
 * </ol>
 *
 * <h2>内置弹仓：一发一发压进去（★ r107）</h2>
 * Kar98k 没有可拆弹匣，弹仓底板（{@code magazine} 骨骼）**装填时不动**：控制器会播
 * {@code animation.awp.reload}（它只 key 了 {@code magazine} 一根骨骼，是「AWP 抽弹匣」的键帧），
 * 所以这里在装填期间把 {@code magazine} 骨骼**显式归零**压掉那段键帧。可见的动作全部程序化驱动：
 * <ul>
 *   <li><b>枪机</b>：装填全程敞开（{@link Kar98kItem#loadBoltTurn} / {@link Kar98kItem#loadBoltBack}
 *       ——开栓转上去、关栓转回来），与击发后的拉栓循环共用同一根 {@code bolt} 骨骼</li>
 *   <li><b>那一发弹</b>：{@code round_in} 从机匣上方（y≈3.4，正好在机匣顶与 4 倍镜筒之间）
 *       一发一发落进弹仓；关栓时再被枪机顶进弹膛</li>
 *   <li><b>双手</b>：右手全程握着拉机柄把枪机按住；左手从护木抬到机匣上方，
 *       跟着每一发往下按（{@code ARM_LOAD} + {@code ARM_PRESS}）</li>
 * </ul>
 */
public class Kar98kGeoModel extends GeoModel<Kar98kItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/kar98k.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/kar98k_geo.png");
    /** ★ 动画与 AWP 共用一份（骨骼名一致，见类注释） */
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/awp.animation.json");

    /**
     * 当前这一遍渲染是不是「拿在手上」（第一/第三人称；由 {@link Kar98kGeoRenderer} 设入）。
     * GeckoLib 的 {@code setCustomAnimations} 对 GUI 图标 / 掉落物 / 展示框一样会跑，
     * 不判断的话「举枪位移 + 后坐 + 抛壳」会跑到物品栏图标上。
     */
    static boolean handPass = false;

    /** {@code move} 骨骼 pivot（geo 里的值）—— 第一人称手臂靠它把骨骼位移换算成相机空间 */
    private static final float MOVE_PX = 0.0F;
    private static final float MOVE_PY = 1.75F;
    private static final float MOVE_PZ = 0.0F;

    /**
     * 当前这一帧的枪本体变换（给第一人称手臂用，见 {@link GunFrame} / {@link WeaponArms}）。
     * 手臂在 {@code RenderHandEvent} 里画、**比物品渲染早**，所以由 {@link #captureNow()} 主动算当前帧。
     */
    static final GunFrame frame = new GunFrame();

    /** move 姿态临时缓冲（骨骼与手臂共用；客户端渲染单线程，不会并发） */
    private static final float[] MOVE_POSE = new float[6];

    // ------------------------------------------------------------------ 拉栓
    /**
     * 拉机柄上抬角（度）：**64°** —— Kar98k 是下弯柄，柄头绕 bolt pivot 抬起时会顶到 4 倍镜筒
     * （镜筒底面 y=3.95、pivot y=2.95 ⇒ 柄头半径 1.25 时 θ&gt;71° 就穿模），64° 留 7° 余量。
     * 与 AWP 的 88° 不同是几何决定的，不是调参差异。
     */
    private static final float BOLT_LIFT = 64.0F;
    /** 拉栓：枪机后退量（模型像素）—— 机匣 z −2.4…1.2、枪机本体 3.0 长，退 2.6 正好抽出来 */
    private static final float BOLT_BACK = 2.6F;
    /** {@code bolt} 骨骼 pivot（geo 里的值）—— 拉机柄绕它抬起来 */
    private static final float BOLT_PX = 0.0F;
    private static final float BOLT_PY = 2.95F;
    private static final float BOLT_PZ = -1.9F;
    /** 拉机柄握点相对 pivot 的偏移（模型像素）：下弯柄的柄头（柄身方块 x[1.05,1.45]、y[1.6,2.9]） */
    private static final float BOLT_GRIP_DX = 1.25F;
    private static final float BOLT_GRIP_DY = -1.15F;
    /** 击发：扣扳机（绕顶部销轴向后转 11°，与 animation.awp.fire 一致） */
    private static final float TRIGGER_PULL = 11.0F;

    // ------------------------------------------------------------------ 抛壳轨迹
    /** 抛壳窗口在拉栓进度里的位置（抽壳结束才被抛壳挺顶出去） */
    private static final float CASE_T0 = 0.12F;
    private static final float CASE_T1 = 0.80F;
    /**
     * 被枪机抽出的距离 / 抛出的初速（模型像素）。
     *
     * <p>★ 与 AWP 的一处**有意不同**：AWP 的 {@code CASE_VX = -5.0}（弹壳往 −X 飞），
     * Kar98k 的抛壳口在机匣**右侧**（x≈+0.62，拉机柄也在右边），所以取 **+3.2**（往 +X 飞）——
     * 抛壳方向与拉机柄同侧才对。数值按本枪比例（枪身 20.8 px vs AWP 23.6 px）缩了一档。
     */
    private static final float CASE_BACK = 2.2F;
    private static final float CASE_VX = 3.2F;
    private static final float CASE_VY = 2.0F;
    private static final float CASE_G = 0.8F;
    /** 三轴翻滚（度） */
    private static final float CASE_SPIN_Z = 220.0F;
    private static final float CASE_SPIN_X = 140.0F;
    private static final float CASE_SPIN_Y = 90.0F;

    // ------------------------------------------------------------------ 逐发压弹（round_in）
    /**
     * 压弹时那一发被抬到机匣上方多高（模型像素）：`round_in` 静止位 y=1.70（机匣内部）⇒
     * 抬到 3.40 再落下去 —— 3.40 在**机匣顶 3.00 之上、4 倍镜筒底 3.95 之下**，那一发整发露得出来。
     */
    private static final float LOAD_DROP = 1.70F;
    /** 关栓上膛时那一发从弹仓被推进弹膛的量（+Y 抬进膛、−Z 往前）—— 在机匣内部，看不到 */
    private static final float FEED_UP = 0.45F;
    private static final float FEED_FWD = 1.10F;
    /** 关栓上膛在拉栓进度里的起点（枪机推回去的后半段把子弹顶进弹膛） */
    private static final float FEED_T0 = 0.55F;

    @Override
    public ResourceLocation getModelResource(Kar98kItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(Kar98kItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(Kar98kItem animatable) {
        return ANIMATION;
    }

    @Override
    public void setCustomAnimations(Kar98kItem animatable, long instanceId,
                                    AnimationState<Kar98kItem> state) {
        if (!handPass) {
            staticPose();
            return;
        }
        ItemStack stack = Kar98kAnimState.heldStack();
        long now = Kar98kAnimState.now();

        // ---------------------------------------------------------- 举枪（ADS）
        // ★ 与 AWP / AKM 完全同一套规则：举枪只做平移，枪管轴线始终平行于视线
        //   （举枪位移由 GunPose 在 pose 层施加，见 WeaponHandGrip.pushAds）
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

        // ---------------------------------------------------------- 枪机：拉栓循环 / 装填时敞开
        float bp = stack == null ? -1.0F : Kar98kItem.boltProgress(stack, now);
        float turn;
        float back;
        if (bp >= 0.0F) {
            turn = boltLiftAt(bp);
            back = boltBackAt(bp);
        } else if (stack != null) {
            turn = Kar98kItem.loadBoltTurn(stack, now);          // 逐发压弹：开栓 / 关栓
            back = Kar98kItem.loadBoltBack(stack, now);
        } else {
            turn = 0.0F;
            back = 0.0F;
        }
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            bolt.setRotX(0.0F);
            bolt.setRotY(0.0F);
            bolt.setRotZ(turn * BOLT_LIFT * Mth.DEG_TO_RAD);
            bolt.setPosX(0.0F);
            bolt.setPosY(0.0F);
            bolt.setPosZ(back * BOLT_BACK);
        }

        // ---------------------------------------------------------- 扣扳机
        // ★ 不能靠 animation.awp.fire：击发同一帧就开始拉栓，控制器优先拉栓（bolt > fire），
        //   那段 11° 的扣扳机键帧永远轮不到。改成按 fireWindow 推骨骼，一扣就有。
        CoreGeoBone trigger = getAnimationProcessor().getBone("trigger");
        if (trigger != null) {
            float fw = stack == null ? -1.0F : Kar98kItem.fireWindow(stack, now);
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
                casing.setPosZ(CASE_BACK * out - 1.0F * fly);
                casing.setRotZ(fly * CASE_SPIN_Z * Mth.DEG_TO_RAD);
                casing.setRotX(fly * CASE_SPIN_X * Mth.DEG_TO_RAD);
                casing.setRotY(fly * CASE_SPIN_Y * Mth.DEG_TO_RAD);
            }
        }

        // ---------------------------------------------------------- 逐发压弹 / 关栓上膛（round_in）
        CoreGeoBone roundIn = getAnimationProcessor().getBone("round_in");
        if (roundIn != null) {
            roundIn.setRotX(0.0F);
            roundIn.setRotY(0.0F);
            roundIn.setRotZ(0.0F);
            float lp = stack == null ? -1.0F : Kar98kItem.loadRoundProgress(stack, now);
            if (lp >= 0.0F) {
                // 压弹：那一发从机匣上方落进弹仓（越压越深，落底时与静止位重合）
                float p = ease(lp);
                roundIn.setHidden(false);
                roundIn.setPosX(0.0F);
                roundIn.setPosY(LOAD_DROP * (1.0F - p));
                roundIn.setPosZ(0.0F);
            } else if (bp >= FEED_T0) {
                // 关栓上膛：枪机把弹仓里那一发推进弹膛（在机匣内部，正常视角看不到）
                float p = Mth.clamp((bp - FEED_T0) / (1.0F - FEED_T0), 0.0F, 1.0F);
                roundIn.setHidden(p >= 0.98F);
                roundIn.setPosX(0.0F);
                roundIn.setPosY(FEED_UP * p);
                roundIn.setPosZ(-FEED_FWD * p);
            } else {
                roundIn.setHidden(true);
            }
        }

        // ---------------------------------------------------------- 内置弹仓：压掉 AWP 的抽弹匣键帧
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
     * move 骨骼当前帧的目标姿态 {@code {posX,posY,posZ,rotX,rotY,rotZ}}（模型像素 / 弧度）。
     *
     * <p>与 AKM / AWP 同一套持枪规则：★ 三个角度**恒为 0**（枪管轴线始终平行于视线），
     * 举枪位移与开火后坐都在 pose 层（{@link WeaponHandGrip#pushAds} / {@link GunPose}）。
     */
    static void computeMovePose(float[] out) {
        out[0] = 0.0F;
        out[1] = 0.0F;
        out[2] = 0.0F;
        out[3] = 0.0F;
        out[4] = 0.0F;
        out[5] = 0.0F;
    }

    /**
     * 手臂用：把**当前帧**的 move 姿态直接算进 {@link #frame}（手臂比物品先画，不能等捕获）。
     * 平移量用的是 {@link WeaponMount} 里那份与 {@code models/item/kar98k.json} 一致的 display。
     */
    static void captureNow() {
        computeMovePose(MOVE_POSE);
        Player local = Minecraft.getInstance().player;
        WeaponHandGrip.pushAds(WeaponAnim.Kind.KAR98K, local == null ? ItemStack.EMPTY
                : local.getMainHandItem(), local);
        frame.capture(WeaponMount.KAR98K_TX, WeaponMount.KAR98K_TY, WeaponMount.KAR98K_TZ, 1.0F,
                MOVE_PX, MOVE_PY, MOVE_PZ,
                MOVE_POSE[0], MOVE_POSE[1], MOVE_POSE[2],
                MOVE_POSE[3], MOVE_POSE[4], MOVE_POSE[5],
                Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.KAR98K).aim, 0.0F, 1.0F));
    }

    // ------------------------------------------------------------------ 左手动作（模型像素）
    /** 平时：托在护木下方（护木 z −8.6…−2.4，手放在中段） */
    private static final float[] ARM_SUPPORT = {0.0F, 1.15F, -5.90F};
    /**
     * 逐发压弹：左手抬到机匣**上方偏左**，把子弹一发一发按下去。
     *
     * <p>位置是量着几何挑的：y=3.60 在**机匣顶 3.00 之上、4 倍镜筒底 3.95 之下**（不穿模）；
     * z=−1.90 在桥夹槽（z −1.2…0.9）**之前**、前后两个镜环（−3.10…−2.50 / 0.60…1.20）之间；
     * x=−0.30 略偏左，让开正中间那一发弹。
     */
    private static final float[] ARM_LOAD = {-0.30F, 3.60F, -1.90F};
    /** 压弹时手跟着那一发往下按的量（按到 y≈3.05，正好压到机匣顶面上停住） */
    private static final float ARM_PRESS = 0.55F;
    private static final float[] TMP_C = new float[3];

    /**
     * 左手目标：
     * <ol>
     *   <li>平时托在护木下方</li>
     *   <li><b>开栓阶段</b>抬到机匣上方（{@link #ARM_LOAD}）</li>
     *   <li><b>压弹阶段</b>跟着那一发往下按（一发一次，按完抬起来拿下一发）</li>
     *   <li><b>关栓阶段</b>收回护木</li>
     * </ol>
     */
    static float[] leftHandPx(float[] out) {
        float rp = localReloadProgress();
        if (rp < 0.0F) return copy(ARM_SUPPORT, out);
        float lp = localRoundProgress();
        if (lp >= 0.0F) {
            // 压弹中：手跟着那一发一起往下，压到底就抬起来拿下一发
            float press = ARM_PRESS * ease(lp);
            TMP_C[0] = ARM_LOAD[0];
            TMP_C[1] = ARM_LOAD[1] - press;
            TMP_C[2] = ARM_LOAD[2];
            return copy(TMP_C, out);
        }
        // 开栓（<0.18）/ 关栓（>0.86）两头插值，中间整段保持在机匣上方
        if (rp < 0.18F) return lerp(ARM_SUPPORT, ARM_LOAD, ease(rp / 0.18F), out);
        if (rp < 0.86F) return copy(ARM_LOAD, out);
        return lerp(ARM_LOAD, ARM_SUPPORT, ease((rp - 0.86F) / 0.14F), out);
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
    /** 平时：握在握把上（握把方块 x ±0.52、y −0.10…1.30、z 1.30…2.60 的中心） */
    private static final float[] ARM_GRIP = {0.0F, 0.60F, 1.95F};
    private static final float[] TMP_B = new float[3];

    /**
     * 右手目标：平时握住握把（食指正在扳机上），拉栓时抬起来抓**下弯拉机柄**、
     * 跟着枪机一起抬起 / 后退，拉完再回到握把；
     * **逐发压弹的开栓与关栓阶段**同样去抓拉机柄（把枪机拉开、压完再推回去）。
     */
    static float[] rightHandPx(float[] out) {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return copy(ARM_GRIP, out);
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof Kar98kItem)) return copy(ARM_GRIP, out);
        long now = player.level().getGameTime();
        float bp = Kar98kItem.boltProgress(stack, now);
        float turn;
        float back;
        float phase;
        if (bp >= 0.0F) {                       // 击发后的拉栓循环
            turn = boltLiftAt(bp);
            back = boltBackAt(bp);
            phase = bp;
        } else {                                // 逐发压弹：开栓 / 关栓
            turn = Kar98kItem.loadBoltTurn(stack, now);
            back = Kar98kItem.loadBoltBack(stack, now);
            phase = Math.max(turn, back) > 0.0F ? 0.5F : -1.0F;
        }
        if (phase < 0.0F) return copy(ARM_GRIP, out);
        boltHandlePoint(turn, back, TMP_B);
        float a = Mth.clamp(Math.max(turn, back) / 0.45F, 0.0F, 1.0F);
        return lerp(ARM_GRIP, TMP_B, ease(a), out);
    }

    /** 拉机柄握点（模型空间的绝对点）：绕 bolt pivot 按 turn 抬起，再随枪机按 back 后退 */
    private static float[] boltHandlePoint(float turn, float back, float[] out) {
        float lift = turn * BOLT_LIFT * Mth.DEG_TO_RAD;
        float c = Mth.cos(lift);
        float s = Mth.sin(lift);
        out[0] = BOLT_PX + (BOLT_GRIP_DX * c - BOLT_GRIP_DY * s);
        out[1] = BOLT_PY + (BOLT_GRIP_DX * s + BOLT_GRIP_DY * c);
        out[2] = BOLT_PZ + back * BOLT_BACK;
        return out;
    }

    /** 本地玩家主手 Kar98k 的换弹（逐发压弹）总进度；没拿 / 没在装填返回 -1 */
    static float localReloadProgress() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return -1.0F;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof Kar98kItem)) return -1.0F;
        return Kar98kItem.reloadProgress(stack, player.level().getGameTime());
    }

    /** 本地玩家主手 Kar98k「正在压的那一发」的进度；不在压弹那一段返回 -1 */
    static float localRoundProgress() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return -1.0F;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof Kar98kItem)) return -1.0F;
        return Kar98kItem.loadRoundProgress(stack, player.level().getGameTime());
    }

    /**
     * GUI 图标 / 掉落物 / 展示框用的**静态姿态**：把一切动作归位
     * （举枪位移、后坐、拉栓、弹仓、抛壳全部清零并藏起弹壳）。
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
            casing.setHidden(true);                 // 静止时弹壳收在弹膛里，本来也看不见
        }
        CoreGeoBone roundIn = getAnimationProcessor().getBone("round_in");
        if (roundIn != null) {
            roundIn.setHidden(true);                // 压弹那一发：不在装填时收起
        }
    }
}
