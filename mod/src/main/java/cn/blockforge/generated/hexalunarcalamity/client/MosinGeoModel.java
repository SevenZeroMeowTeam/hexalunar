package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.weapon.MosinRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.Sights;
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
 * 莫辛-纳甘 M91/30 的 GeckoLib 模型定义 + 程序化骨骼细节（照 {@link Kar98kGeoModel} 那一套写）。
 *
 * <h2>资源</h2>
 * <ul>
 *   <li>几何 {@code geo/mosin.geo.json}（由 {@code tools/mosin_gen.py} 生成，14 骨骼 / 97 方块）</li>
 *   <li>贴图 {@code textures/models/mosin_geo.png}（+ {@code _glowmask} 供流光层）</li>
 *   <li>动画 {@code animations/mosin.animation.json}（六个状态都是「空动作」，姿态全部由本类程序化推）</li>
 * </ul>
 *
 * <h2>骨骼</h2>
 * {@code root → move → body → {barrel, handguard, bolt, magazine, trigger, scope →
 * scope_elev / scope_wind, casing, round_in, camera}}。朝向：枪口 = −Z、上 = +Y、原点 = 握把。
 *
 * <h2>三个「看得见」的动作</h2>
 * <ol>
 *   <li><b>拉栓循环（抽壳 → 抛壳 → 上膛）</b>：{@code bolt} 骨骼转 90° 抬起 + 后退 2.3，
 *       {@code casing}（黄铜弹壳）跟着枪机被抽出来，然后往 <b>+X（枪身右侧，抛壳口那一侧）</b>
 *       翻滚飞出；枪机推回闭锁时 {@code round_in}（弹仓里那一发）被顶进弹膛 —— 与
 *       {@code MosinRifleItem.finishBolt}（弹仓 −1、膛内 +1）是同一段时间轴。</li>
 *   <li><b>逐发压弹</b>：装填期间枪机保持敞开，每一发 {@code round_in} 从机匣上方落下压进弹仓
 *       （{@code LOAD_DROP}），**右手**从拉机柄移到机匣上方，跟着每一发往下按；**左手全程扶枪**。</li>
 *   <li><b>抛壳方向</b>：莫辛的抛壳口在机匣<b>右侧</b>（拉机柄同侧），所以弹壳往 +X 飞。</li>
 * </ol>
 */
public class MosinGeoModel extends GeoModel<MosinRifleItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/mosin.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/mosin_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/mosin.animation.json");

    /**
     * 当前这一遍渲染是不是「拿在手上」（第一/第三人称；由 {@link MosinGeoRenderer} 设入）。
     * GeckoLib 的 {@code setCustomAnimations} 对 GUI 图标 / 掉落物 / 展示框一样会跑，
     * 不判断的话「举枪位移 + 后坐 + 抛壳」会跑到物品栏图标上。
     */
    static boolean handPass = false;

    /** 这一遍渲染的瞄具档位（由 {@link MosinGeoRenderer} 按物品 NBT 设入）：不是 4 倍镜就藏掉镜筒 */
    static int sightNow = Sights.SCOPE;

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
     * 拉机柄上抬角（度）：**90°**。莫辛是下弯柄，柄头绕枪管轴抬起后最高 Y≈2.77，
     * 而 4 倍镜筒底面在 Y=3.08（{@code mosin_gen.py} 自检会打印这个余量）⇒ 90° 也碰不到镜子。
     */
    private static final float BOLT_LIFT = 90.0F;
    /** 拉栓：枪机后退量（模型像素）—— 机匣 z −4.58…−0.62、枪机本体 2.7 长，退 2.3 正好把弹壳抽出弹膛 */
    private static final float BOLT_BACK = 2.3F;
    /** {@code bolt} 骨骼 pivot（geo 里的值）—— 拉机柄绕它抬起来 */
    private static final float BOLT_PX = 0.0F;
    private static final float BOLT_PY = 1.75F;
    private static final float BOLT_PZ = -1.85F;
    /** 拉机柄握点相对 pivot 的偏移（模型像素）：下弯柄的柄头（方块 x 0.72…1.10、y 1.02…1.34） */
    private static final float BOLT_GRIP_DX = 0.95F;
    private static final float BOLT_GRIP_DY = -0.60F;
    /** 右手「摸到拉机柄」（{@code BOLT_HAND_IN} 之前）与「拉完立即回握把」的区间 */
    private static final float BOLT_HAND_IN = 0.18F;
    private static final float BOLT_HAND_OUT = 0.60F;
    private static final float BOLT_HAND_SNAP = 0.18F;
    /** 击发：扣扳机（绕顶部销轴向后转 11°） */
    private static final float TRIGGER_PULL = 11.0F;

    // ------------------------------------------------------------------ 抛壳轨迹（抽壳 → 抛出）
    /** 抛壳窗口在拉栓进度里的位置：枪机后退到 40% 时弹壳被抽出来，之后被抛壳挺顶出去 */
    private static final float CASE_T0 = 0.30F;
    private static final float CASE_T1 = 0.86F;
    /** 跟着枪机被抽出的距离 / 抛出的初速（模型像素）：往 +X（右侧抛壳口）飞 */
    private static final float CASE_BACK = 2.3F;
    private static final float CASE_VX = 4.6F;
    private static final float CASE_VY = 1.9F;
    private static final float CASE_G = 0.75F;
    /** 三轴翻滚（度） */
    private static final float CASE_SPIN_Z = 240.0F;
    private static final float CASE_SPIN_X = 150.0F;
    private static final float CASE_SPIN_Y = 100.0F;

    // ------------------------------------------------------------------ 逐发压弹（round_in）
    /** 压弹时那一发在机匣上方多高（模型像素）：弹仓内定位 Y≈0.86 ⇒ 抬到 3.16 再落下去 */
    private static final float LOAD_DROP = 2.30F;
    /** 关栓上膛时那一发从弹仓被推到弹膛的量（+Y 进膛、−Z 往前）—— 在机匣内部，正常视角看不到 */
    private static final float FEED_UP = 0.89F;
    private static final float FEED_FWD = 0.60F;

    @Override
    public ResourceLocation getModelResource(MosinRifleItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(MosinRifleItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(MosinRifleItem animatable) {
        return ANIMATION;
    }

    @Override
    public void setCustomAnimations(MosinRifleItem animatable, long instanceId,
                                    AnimationState<MosinRifleItem> state) {
        if (!handPass) {
            staticPose();
            return;
        }
        ItemStack stack = MosinAnimState.heldStack();
        long now = MosinAnimState.now();

        // ---------------------------------------------------------- 举枪（ADS）
        // ★ 与 AKM / AWP / Kar98k 完全同一套规则：举枪只做平移，枪管轴线始终平行于视线
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

        // ---------------------------------------------------------- 4 倍镜（按瞄具档位显隐）
        setSightVisible(getAnimationProcessor().getBone("scope"),
                getAnimationProcessor().getBone("scope_elev"),
                getAnimationProcessor().getBone("scope_wind"), sightNow);

        // ---------------------------------------------------------- 枪机：拉栓动画 / 装填时敞开
        float bp = stack == null ? -1.0F : MosinRifleItem.boltProgress(stack, now);
        float turn;
        float back;
        if (bp >= 0.0F) {
            turn = boltLiftAt(bp);
            back = boltBackAt(bp);
        } else if (stack != null) {
            turn = MosinRifleItem.loadBoltTurn(stack, now);          // 逐发压弹：开栓 / 关栓
            back = MosinRifleItem.loadBoltBack(stack, now);
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
        // 不能靠动画：击发同一帧就开始拉栓，控制器优先拉栓（bolt > fire），那段键帧永远轮不到。
        CoreGeoBone trigger = getAnimationProcessor().getBone("trigger");
        if (trigger != null) {
            float fw = stack == null ? -1.0F : MosinRifleItem.fireWindow(stack, now);
            trigger.setRotX(-TRIGGER_PULL * triggerPullAt(fw) * Mth.DEG_TO_RAD);
        }

        // ---------------------------------------------------------- 抛壳（跟着拉栓进度：抽壳 → 抛出）
        CoreGeoBone casing = getAnimationProcessor().getBone("casing");
        if (casing != null) {
            if (bp < CASE_T0 || bp > CASE_T1) {
                casing.setHidden(true);
            } else {
                casing.setHidden(false);
                float c = (bp - CASE_T0) / (CASE_T1 - CASE_T0);      // 窗口内 0..1
                float out = Mth.clamp(c / 0.20F, 0.0F, 1.0F);        // 先跟枪机抽出来
                float fly = Mth.clamp((c - 0.20F) / 0.80F, 0.0F, 1.0F);   // 再被顶出机匣
                casing.setPosX(CASE_VX * fly);
                casing.setPosY(CASE_VY * fly - CASE_G * fly * fly);
                casing.setPosZ(CASE_BACK * back - 0.9F * fly);
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
            float lp = stack == null ? -1.0F : MosinRifleItem.loadRoundProgress(stack, now);
            if (lp >= 0.0F) {
                // 压弹：从机匣上方落进弹仓（越压越深，落底时与静止位重合）
                float p = ease(lp);
                roundIn.setHidden(false);
                roundIn.setPosX(0.0F);
                roundIn.setPosY(LOAD_DROP * (1.0F - p));
                roundIn.setPosZ(0.0F);
            } else if (bp >= FEED_T0) {
                // 关栓上膛：枪机把弹仓里那一发推进弹膛（在机匣内部，看不到，但与 HUD 计数一致）
                float p = Mth.clamp((bp - FEED_T0) / (1.0F - FEED_T0), 0.0F, 1.0F);
                roundIn.setHidden(p >= 0.98F);
                roundIn.setPosX(0.0F);
                roundIn.setPosY(FEED_UP * p);
                roundIn.setPosZ(-FEED_FWD * p);
            } else {
                roundIn.setHidden(true);
            }
        }

        // ---------------------------------------------------------- 弹仓：莫辛是固定弹仓，一切归零
        CoreGeoBone mag = getAnimationProcessor().getBone("magazine");
        if (mag != null) {
            mag.setHidden(false);
            mag.setRotX(0.0F);
            mag.setPosX(0.0F);
            mag.setPosY(0.0F);
            mag.setPosZ(0.0F);
        }
    }

    /** 关栓上膛在拉栓进度里的起点（枪机推回去的后半段把子弹顶进弹膛） */
    private static final float FEED_T0 = 0.55F;

    /** 4 倍镜三根骨骼按瞄具档位显隐（只有装了 4 倍镜才显示） */
    static void setSightVisible(CoreGeoBone scope, CoreGeoBone elev, CoreGeoBone wind, int sight) {
        boolean show = sight == Sights.SCOPE;
        if (scope != null) scope.setHidden(!show);
        if (elev != null) elev.setHidden(!show);
        if (wind != null) wind.setHidden(!show);
    }

    /**
     * move 骨骼当前帧的目标姿态 {@code {posX,posY,posZ,rotX,rotY,rotZ}}（模型像素 / 弧度）。
     *
     * <p>与 AKM / AWP / Kar98k 同一套持枪规则：★ 三个角度**恒为 0**（枪管轴线始终平行于视线），
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
     * 平移量用的是 {@link WeaponMount} 里那份与 {@code models/item/mosin_nagant.json} 一致的 display。
     */
    static void captureNow() {
        computeMovePose(MOVE_POSE);
        Player local = Minecraft.getInstance().player;
        WeaponHandGrip.pushAds(WeaponAnim.Kind.MOSIN, local == null ? ItemStack.EMPTY
                : local.getMainHandItem(), local);
        frame.capture(WeaponMount.MOSIN_TX, WeaponMount.MOSIN_TY, WeaponMount.MOSIN_TZ, 1.0F,
                MOVE_PX, MOVE_PY, MOVE_PZ,
                MOVE_POSE[0], MOVE_POSE[1], MOVE_POSE[2],
                MOVE_POSE[3], MOVE_POSE[4], MOVE_POSE[5],
                Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.MOSIN).aim, 0.0F, 1.0F));
    }

    // ------------------------------------------------------------------ 左手：全程扶枪（模型像素）
    /** 左手扶枪的支撑点：托在前托下方（前托 z −13.56…−0.58、托底 Y≈0.98） */
    private static final float[] ARM_SUPPORT = {0.0F, 0.95F, -8.00F};

    /**
     * 左手目标：**全程托在前托下方扶枪**（用户要求）。
     *
     * <p>莫辛的操作分工是「**左手扶枪、右手干活**」：开栓 / 逐发压弹 / 关栓全在右手
     * （见 {@link #rightHandPx}），左手只负责把枪端稳 —— 所以这里恒为支撑点，不参与装填动作。
     */
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

    private static float[] lerp(float[] a, float[] b, float t, float[] out) {
        for (int i = 0; i < 3; i++) out[i] = a[i] + (b[i] - a[i]) * t;
        return out;
    }

    /** 拉机柄抬高量 0..1：抬起 → 保持 → 末端压回 */
    private static float boltLiftAt(float bp) {
        if (bp < 0.0F) return 0.0F;
        if (bp < 0.20F) return bp / 0.20F;
        if (bp > 0.85F) return Mth.clamp((1.0F - bp) / 0.15F, 0.0F, 1.0F);
        return 1.0F;
    }

    /** 枪机后退量 0..1：后退 → 保持 → 推回（骨骼 / 手共用） */
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

    // ------------------------------------------------------------------ 右手：握把 / 拉栓 / ★逐发压弹
    /** 平时：握住腕部（握把/原点附近，枪就端在这只手上） */
    private static final float[] ARM_GRIP = {0.0F, 1.35F, -0.05F};
    /**
     * 逐发压弹：**右手**抬到机匣上方，把子弹一发一发按下去（用户要求：压弹是右手的活）。
     *
     * <p>★ 取 x = **+0.50** 是故意偏到镜筒右侧 —— 4 倍镜筒占 x ±0.36、正上方那条线被镜子占着，
     * 手伸到 x=0 会穿模；偏右一点正好是「右手拇指按压弹仓口」的位置。
     */
    private static final float[] ARM_LOAD_R = {0.50F, 3.10F, -2.95F};
    /** 每一发按下去的深度（模型像素） */
    private static final float PRESS_DEPTH = 0.55F;
    private static final float[] TMP_C = new float[3];
    private static final float[] TMP_B = new float[3];

    /**
     * 右手目标 —— 莫辛的活全在这只手上：
     * <ol>
     *   <li><b>击发后的拉栓循环</b>：整段抓着拉机柄（抬起 → 跟着枪机后退抛壳 → 推回闭锁）</li>
     *   <li><b>装填的开栓 / 关栓阶段</b>：同样抓拉机柄</li>
     *   <li><b>★ 逐发压弹阶段</b>：手抬到机匣上方（{@link #ARM_LOAD_R}），每一发
     *       「前 35% 抬手取下一发 → 后 65% 按进弹仓」 —— 首尾与上一发的压到底位置自然接上，
     *       不会跳位；第一发额外用 30% 的时间把手从拉机柄挪过来</li>
     *   <li>其余时间握住腕部</li>
     * </ol>
     */
    static float[] rightHandPx(float[] out) {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return copy(ARM_GRIP, out);
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof MosinRifleItem)) return copy(ARM_GRIP, out);
        long now = player.level().getGameTime();

        // ---- 1) 击发后的拉栓循环：整段抓着拉机柄 ----
        float bp = MosinRifleItem.boltProgress(stack, now);
        if (bp >= 0.0F) {
            float turn = boltLiftAt(bp);
            float back = boltBackAt(bp);
            boltHandlePoint(turn, back, TMP_B);
            return lerp(ARM_GRIP, TMP_B, ease(Math.max(turn, back) / 0.45F), out);
        }

        if (!MosinRifleItem.loading(stack, now)) return copy(ARM_GRIP, out);

        float turn = MosinRifleItem.loadBoltTurn(stack, now);
        float back = MosinRifleItem.loadBoltBack(stack, now);
        float lp = MosinRifleItem.loadRoundProgress(stack, now);

        // ---- 2) 逐发压弹：抬到机匣上方，一发一发往下按 ----
        if (lp >= 0.0F) {
            float press = lp < 0.35F
                    ? PRESS_DEPTH * (1.0F - ease(lp / 0.35F))       // 抬手取下一发
                    : PRESS_DEPTH * ease((lp - 0.35F) / 0.65F);     // 压进弹仓
            TMP_C[0] = ARM_LOAD_R[0];
            TMP_C[1] = ARM_LOAD_R[1] - press;
            TMP_C[2] = ARM_LOAD_R[2];
            if (MosinRifleItem.loadRoundIndex(stack, now) == 0 && lp < 0.30F) {
                // 第一发：先把手从拉机柄挪过来（否则会突然跳位）
                boltHandlePoint(turn, back, TMP_B);
                return lerp(TMP_B, TMP_C, ease(lp / 0.30F), out);
            }
            return copy(TMP_C, out);
        }

        // ---- 3) 开栓 / 关栓：抓拉机柄（turn/back 从 0 涨到 1 的途中自然滑过去）----
        boltHandlePoint(turn, back, TMP_B);
        return lerp(ARM_GRIP, TMP_B, ease(Math.max(turn, back) / 0.45F), out);
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

    /**
     * GUI 图标 / 掉落物 / 展示框用的**静态姿态**：把一切动作归位
     * （举枪位移、后坐、枪机、弹壳、压弹那一发全部清零并藏起），
     * 4 倍镜按 {@link #sightNow} 显隐（图标里也能看出装没装镜）。
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
            casing.setHidden(true);                 // 静止时弹壳收在机匣里，本来也看不见
        }
        CoreGeoBone roundIn = getAnimationProcessor().getBone("round_in");
        if (roundIn != null) {
            roundIn.setHidden(true);                // 压弹那一发：不在装填时收起
        }
        setSightVisible(getAnimationProcessor().getBone("scope"),
                getAnimationProcessor().getBone("scope_elev"),
                getAnimationProcessor().getBone("scope_wind"), sightNow);
    }
}
