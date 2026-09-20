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
 *   <li>几何 {@code geo/m1_garand.geo.json}（{@code tools/m1_garand_gen.py} 生成，10 骨骼 / 29 方块）</li>
 *   <li>贴图 {@code textures/models/m1_garand_geo.png}（+ {@code _glowmask} 供流光层）</li>
 *   <li>动画：★ <b>复用 {@code animations/awp.animation.json}</b> ——
 *       M1 的骨骼名与 AWP / Kar98k 那一套一致（{@code root/move/body/barrel/bolt/casing/
 *       magazine/trigger} + 自己的 {@code handguard} / {@code clip_in}），
 *       {@code idle / run / run_fast / fire / bolt / reload} 六段直接可用；
 *       真正要动的部分全部由本类程序化驱动</li>
 * </ul>
 *
 * <h2>三件程序化的事</h2>
 * <ol>
 *   <li><b>自动枪机循环（半自动）</b>：每发之后导气杆自己后退 {@link #BOLT_BACK} px 把空弹壳带出来
 *       再复进闭锁 —— 玩家不用拉栓（「拉一次栓即可」指的就是换弹最后那一下）。
 *       空仓时枪机**停在后位**（M1 的标志样子）。</li>
 *   <li><b>漏夹</b>（{@code clip_in}）：换弹时右手把 8 发漏夹从机匣上方
 *       {@link #CLIP_DROP} px 压进去；**打空后整只漏夹弹出来**（隐藏）。</li>
 *   <li><b>双手</b>：平时右手握把 / 左手托前托；换弹时**右手**抬起漏夹压下去、
 *       再抓住拉机柄跟着枪机复进（左手始终托着枪 —— 加兰德换弹就是单手压漏夹）。</li>
 * </ol>
 */
public class M1GarandGeoModel extends GeoModel<M1GarandItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/m1_garand.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/m1_garand_geo.png");
    /** 动画与 AWP / Kar98k / 莫辛共用一份（骨骼名一致，见类注释） */
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/awp.animation.json");

    /** 当前这一遍是不是「拿在手上」（由 {@link M1GarandGeoRenderer} 设入） */
    static boolean handPass = false;

    /** {@code move} 骨骼 pivot（geo 里的值） */
    private static final float MOVE_PX = 0.0F;
    private static final float MOVE_PY = 1.30F;
    private static final float MOVE_PZ = 1.60F;

    /** 当前这一帧的枪本体变换（给第一人称手臂用，见 {@link GunFrame} / {@link WeaponArms}） */
    static final GunFrame frame = new GunFrame();

    private static final float[] MOVE_POSE = new float[6];

    // ------------------------------------------------------------------ 枪机（自动循环）
    /** {@code bolt} 骨骼 pivot（geo 里的值） */
    private static final float BOLT_PX = 0.0F;
    private static final float BOLT_PY = 2.80F;
    private static final float BOLT_PZ = -1.60F;
    /** 自动枪机循环的后退量（模型像素）：导气杆跟着一起走 */
    private static final float BOLT_BACK = 2.40F;
    /** 拉机柄（导气杆手柄）相对 pivot 的偏移：方块中心 x0.95 / y2.35 / z−1.05 */
    private static final float BOLT_GRIP_DX = 0.95F;
    private static final float BOLT_GRIP_DY = -0.45F;
    private static final float BOLT_GRIP_DZ = 0.55F;
    /** 击发：扣扳机（绕顶部销轴向后转 11°，与 animation.awp.fire 一致） */
    private static final float TRIGGER_PULL = 11.0F;

    // ------------------------------------------------------------------ 漏夹（clip_in）
    /** 压漏夹时它被抬到机匣上方多高：静止位顶 2.06 ⇒ 抬到 4.31（机匣顶 3.00 之上，看得见） */
    private static final float CLIP_DROP = 2.25F;

    // ------------------------------------------------------------------ 抛壳（半自动，每发一次）
    /** 抛壳窗口在枪机循环里的位置 */
    private static final float CASE_T0 = 0.10F;
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

        // ---------------------------------------------------------- 漏夹：压进去 / 打空弹出
        CoreGeoBone clipIn = getAnimationProcessor().getBone("clip_in");
        if (clipIn != null) {
            float clip = stack == null ? -1.0F : M1GarandItem.clipProgress(stack, now);
            if (clip >= 0.0F) {
                clipIn.setHidden(false);                            // 压漏夹：跟着手往下
                clipIn.setPosY(CLIP_DROP * (1.0F - ease(clip)));
            } else if (stack != null && !M1GarandItem.loading(stack, now)
                    && M1GarandItem.empty(stack)) {
                clipIn.setHidden(true);                             // 漏夹已经打空弹出来了
                clipIn.setPosY(0.0F);
            } else {
                clipIn.setHidden(false);                            // 压到位 / 还有弹：在机匣里
                clipIn.setPosY(0.0F);
            }
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
     * move 骨骼当前帧的目标姿态（与 AKM / AWP / Kar98k / 莫辛同一套规则）：
     * ★ 三个角度**恒为 0**（枪管轴线始终平行于视线），举枪位移与开火后坐都在 pose 层。
     */
    static void computeMovePose(float[] out) {
        out[0] = 0.0F;
        out[1] = 0.0F;
        out[2] = 0.0F;
        out[3] = 0.0F;
        out[4] = 0.0F;
        out[5] = 0.0F;
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
    /** 平时：握在托颈（wrist）上 */
    private static final float[] ARM_GRIP = {0.0F, 1.25F, 1.70F};
    /**
     * 换弹：右手把 8 发漏夹从机匣**上方**压下去。
     * y=4.06 是漏夹被抬到最高的位置（静止位顶 2.06 + CLIP_DROP 2.25 ≈ 4.31），
     * z=−0.90 正对机匣的压弹口（照门座在 z −0.62…0.06，手在它前面，不穿模）。
     */
    private static final float[] ARM_CLIP = {0.0F, 4.06F, -0.90F};
    /** 压到底时手往下走的量（漏夹继续进机匣，手停在机匣顶面上方） */
    private static final float ARM_PRESS = 1.00F;
    private static final float[] TMP_B = new float[3];
    private static final float[] TMP_C = new float[3];

    /**
     * 右手目标：
     * <ol>
     *   <li>平时握着托颈（食指在扳机上）—— 半自动射击时**手不跟着枪机跑**（枪机是导气杆自己动的）</li>
     *   <li><b>压漏夹</b>：抬手到机匣上方，跟着漏夹一起往下按</li>
     *   <li><b>枪机释放</b>：抓住拉机柄（导气杆手柄）跟着它复进到位（「拉一次栓」那一下）</li>
     * </ol>
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
        float release = M1GarandItem.boltReleaseProgress(stack, now);
        if (release >= 0.0F) {                                       // 枪机释放：手抓拉机柄复进
            boltHandlePoint(1.0F - ease(release), TMP_B);
            // 开头 15% 从「压到底的漏夹手位」滑到拉机柄，后面整段跟着枪机走
            float a = Mth.clamp(release / 0.15F, 0.0F, 1.0F);
            TMP_C[0] = ARM_CLIP[0];
            TMP_C[1] = ARM_CLIP[1] - ARM_PRESS;
            TMP_C[2] = ARM_CLIP[2];
            return lerp(TMP_C, TMP_B, ease(a), out);
        }
        return copy(ARM_GRIP, out);
    }

    /** 拉机柄（导气杆手柄）在模型空间的位置：随枪机后退量 back 一起往后走 */
    private static float[] boltHandlePoint(float back, float[] out) {
        out[0] = BOLT_PX + BOLT_GRIP_DX;
        out[1] = BOLT_PY + BOLT_GRIP_DY;
        out[2] = BOLT_PZ + BOLT_GRIP_DZ + back * BOLT_BACK;
        return out;
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

    private static float[] lerp(float[] a, float[] b, float t, float[] out) {
        for (int i = 0; i < 3; i++) out[i] = a[i] + (b[i] - a[i]) * t;
        return out;
    }

    /** 扣扳机的压下量 0..1：快扣 → 慢放（-1 = 不在击发窗口里） */
    private static float triggerPullAt(float fw) {
        if (fw < 0.0F) return 0.0F;
        if (fw < 0.25F) return ease(fw / 0.25F);
        return ease(Mth.clamp((1.0F - fw) / 0.75F, 0.0F, 1.0F));
    }

    /**
     * GUI 图标 / 掉落物 / 展示框用的**静态姿态**：举枪位移、枪机、抛壳、漏夹全部归位
     * （枪机在闭锁位、弹壳与漏夹都藏起来）。
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
        CoreGeoBone clipIn = getAnimationProcessor().getBone("clip_in");
        if (clipIn != null) {
            clipIn.setHidden(true);                 // 图标里不画漏夹（在机匣内部，本来就看不见）
            clipIn.setPosY(0.0F);
        }
    }
}
