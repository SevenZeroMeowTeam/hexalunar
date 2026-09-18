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
 * 十字弩的 GeckoLib 模型（真骨骼，12 根）。
 *
 * <p>模型由 {@code tools/crossbow_gen.py} 按参考模型 {@code 模型/十字弩.bbmodel} 的实测比例重建：
 * root → move → body（机匣导轨）→ stock / grip / scope / prod_left / prod_right /
 * string_left / string_right / nock / bolt。弩箭飞出方向 = <b>-Z（北）</b>，原点在握把上方。
 *
 * <p><b>拉弦装弹</b>是连续动作（按住/R 键共 {@code RELOAD_TICKS}=30 tick），所以按
 * {@code CrossbowWeaponItem.reloadProgress} 程序化推骨骼：
 * 弦两段绕弓臂梢（<b>Y 轴</b>）转 φ、弦心后退 DRAW_Z，弩箭在后半段滑上弦。
 * 弦长取拉满所需（hypot(6.0, 3.40)=6.896），未拉时两段在中点重叠、被弦心缠绳盖住 ——
 * 与复合弓同一套算法。DRAW_DZ 必须与 {@code tools/crossbow_v3.py} 的同名常数一致：
 * 拉满时弦心落在 z = NOCK_Z0 + DRAW_DZ（生成器自检会打印该值）。
 */
public class CrossbowGeoModel extends GeoModel<CrossbowWeaponItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/crossbow_geo.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/crossbow_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/crossbow.animation.json");

    /** 弓臂梢到弦心的横向距离（生成器 TIP_X） */
    private static final float TIP_X = 6.0F;
    /** 拉满时弦心后退距离（生成器 DRAW_DZ） */
    private static final float DRAW_DZ = 3.40F;
    /** 弦段转角 φ = atan(DRAW_DZ / TIP_X) */
    private static final float PHI_RAD = (float) Math.atan2(DRAW_DZ, TIP_X);
    /** 弦心相对参考面的 z（生成器 TIP_Z，已含原点偏移） */
    private static final float NOCK_Z0 = -2.20F - 3.60F;
    /** 弩箭收起时挪走的高度（挪到看不见） */
    private static final float BOLT_HIDE_Y = -40.0F;
    /** 击发后弦震动持续 tick 数 */
    private static final int TWANG_TICKS = 9;
    /**
     * 击发后坐（模型像素 / 度，乘 WeaponAnim 的后坐冲量）：后拖 + 略上抬 + 微上跳。
     * 弩比枪轻，幅度取小一半。
     */
    private static final float KICK_BACK = 0.95F;
    private static final float KICK_UP = 0.22F;
    private static final float KICK_PITCH = 2.40F;
    /** 拉满时凸轮盘转过的角度（视觉：弦从凸轮上放开）；随 DRAW_DZ 等比放大 */
    private static final float CAM_SPIN = (float) Math.toRadians(60.0);

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

        long now = mc.level.getGameTime();
        boolean cocked = CrossbowWeaponItem.cocked(stack);
        float progress = CrossbowWeaponItem.reloadProgress(stack, now);   // 0..1，-1 表示没在装
        float p = progress < 0.0F ? 0.0F : Mth.clamp(progress, 0.0F, 1.0F);

        // 前 65% 拉弦，后 35% 把箭推上弦
        float draw = cocked ? 1.0F : Mth.clamp(p / 0.65F, 0.0F, 1.0F);
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

        // 复合十字弩：拉弦时两个凸轮盘跟着转（弦从凸轮上放/收）
        CoreGeoBone camL = getAnimationProcessor().getBone("cam_left");
        CoreGeoBone camR = getAnimationProcessor().getBone("cam_right");
        if (camL != null) camL.setRotY(-draw * CAM_SPIN);
        if (camR != null) camR.setRotY(draw * CAM_SPIN);

        // 弦心（缠绳）随拉弦后退；震动时跟着弦心一起前后抖（弦长 6.54·cosφ = 6.0）
        CoreGeoBone nock = getAnimationProcessor().getBone("nock");
        if (nock != null) {
            nock.setPosZ(draw * DRAW_DZ - 6.0F * tw);
            nock.setPosY(0.0F);
        }

        // 弩箭：没装填时挪到看不见；装填时滑到弦心（拉满后停在弦上）
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            // ★ 左手（WeaponArms）在 p≈0.84 才把箭送到箭槽，所以箭也那时候出现，
            //   否则箭会先凭空出现在导轨上、手再慢吞吞地过去「假装」放箭。
            boolean hasBolt = cocked || p > 0.84F;
            bolt.setPosY(hasBolt ? 0.0F : BOLT_HIDE_Y);
            bolt.setPosZ(draw * DRAW_DZ);
        }

        // ★ 不「在手里晃」（同 AKM）：idle / run / run_fast 会给 move 推上下位置（±0.4~0.8 像素）
        //   与俯仰（2.4~3.8°）——装填完成之后它还在摆，看起来就是弩在自己晃。
        //   除击发那一瞬，一律把 move 收平，弩稳稳端在手里。
        CoreGeoBone move = getAnimationProcessor().getBone("move");
        if (move != null) {
            if (!CrossbowAnimState.firing()) {
                move.setPosX(0.0F);
                move.setPosY(0.0F);
                move.setPosZ(0.0F);
                move.setRotX(0.0F);
                move.setRotY(0.0F);
                move.setRotZ(0.0F);
            }
            // 击发后坐：走 move 骨骼（第一人称手臂读的就是它，所以手会跟着弩一起顿）
            float kick = WeaponAnim.of(WeaponAnim.Kind.CROSSBOW).recoil;
            if (kick > 0.001F) {
                move.setPosY(move.getPosY() + KICK_UP * kick);
                move.setPosZ(move.getPosZ() + KICK_BACK * kick);
                move.setRotX(move.getRotX() - KICK_PITCH * kick * Mth.DEG_TO_RAD);
            }
        }

        // 左手动作要用（手臂在 RenderHandEvent 里先画，所以读上一帧的值就够）
        lastProgress = progress;
        lastDraw = draw;
        captureFrame();

        // ★ 拉弦/装填全靠上面这些**弩自身的动作**表现（弦两段往后转、弦心后退、凸轮盘转、
        //   弩箭滑上弦），再加上 animation.json 里 move 的摆动（低头/后拖/顿挫），
        //   以及第一人称的手臂（左手拉弦 / 递箭）；不做实体手方块。
    }

    /** 把 move 骨骼当前状态存进 {@link #frame}（手臂要跟着弩一起动） */
    private void captureFrame() {
        CoreGeoBone move = getAnimationProcessor().getBone("move");
        float ox = 0.0F, oy = 0.0F, oz = 0.0F, rx = 0.0F, ry = 0.0F, rz = 0.0F;
        if (move != null) {
            ox = move.getPosX();
            oy = move.getPosY();
            oz = move.getPosZ();
            rx = move.getRotX();
            ry = move.getRotY();
            rz = move.getRotZ();
        }
        frame.capture(0.0F, 0.0F, 0.0F, CB_SCALE,
                MOVE_PX, MOVE_PY, MOVE_PZ, ox, oy, oz, rx, ry, rz);
    }

    // ------------------------------------------------------------------ 左手动作（模型像素）
    /** 十字弩 display 的缩放（models/item/crossbow.json） */
    private static final float CB_SCALE = 0.8F;
    /** 托护木（平时：导轨前段下方） */
    private static final float[] ARM_SUPPORT = {0.0F, -1.10F, -4.60F};
    /** 去下面取箭时的位置（在导轨下方、前面） */
    private static final float[] ARM_FETCH = {0.20F, -1.80F, -6.20F};
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

    /** 弦心上的握点（弦心 z = NOCK_Z0 + draw·DRAW_DZ，手抓在它后面一点） */
    private static float[] stringPoint(float draw, float[] out) {
        out[0] = 0.26F;
        out[1] = 0.22F;
        out[2] = NOCK_Z0 + draw * DRAW_DZ + 0.30F;
        return out;
    }

    /** 弩箭上的握点（箭尾在弦心上，所以跟着 draw·DRAW_DZ 走） */
    private static float[] boltPoint(float[] out) {
        out[0] = 0.20F;
        out[1] = 0.25F;
        out[2] = -6.40F + lastDraw * DRAW_DZ;
        return out;
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
