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
    /** 拉满时凸轮盘转过的角度（视觉：弦从凸轮上放开）；随 DRAW_DZ 等比放大 */
    private static final float CAM_SPIN = (float) Math.toRadians(60.0);

    /** 弦震动计时（客户端静态字段，跨帧保留） */
    private static long twangUntil = 0L;
    /** 上一帧是否已上弦（用来捕捉「击发」这个边沿） */
    private static boolean wasCocked = false;
    /** 当前这一遍渲染是不是 GUI 图标（由 {@link CrossbowGeoRenderer} 每帧设置） */
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
            boolean hasBolt = cocked || load > 0.02F;
            bolt.setPosY(hasBolt ? 0.0F : BOLT_HIDE_Y);
            bolt.setPosZ(draw * DRAW_DZ);
        }

        // ★ 用户要求不要实体手方块 ⇒ 拉弦/装填全靠上面这些**弩自身的动作**表现：
        //   弦两段往后转、弦心后退、凸轮盘转、弩箭从下方滑上弦，再加上 animation.json 里
        //   move 的摆动（低头/后拖/顿挫），第一人称和第三人称都看得明白是在拉弦上箭。
    }
}
