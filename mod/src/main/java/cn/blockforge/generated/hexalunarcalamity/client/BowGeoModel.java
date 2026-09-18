package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponMount;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import software.bernie.geckolib.core.animatable.model.CoreGeoBone;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;

/**
 * 复合弓的 GeckoLib 模型定义（真骨骼，15 根）。
 *
 * <p>模型由 {@code tools/bow_gen.py} 按参考模型 {@code 模型/复合弓.bbmodel} 的实测比例重建：
 * root → move → body → grip / sight / stabilizer / upper_limb(+cam_upper) /
 * lower_limb(+cam_lower) / string_upper / string_lower / nock / arrow。
 * 箭飞向 <b>-Z（北）</b>，原点在握把中心。
 */
public class BowGeoModel extends GeoModel<CompoundBowItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/compound_bow.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/compound_bow_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/compound_bow.animation.json");

    @Override
    public ResourceLocation getModelResource(CompoundBowItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(CompoundBowItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(CompoundBowItem animatable) {
        return ANIMATION;
    }

    /**
     * 拉弓时把<b>瞄准圈圆心</b>顶到游戏准星上（并顺手把跑步摆动收掉）。
     *
     * <p>为什么要推骨骼：display 平移那套（{@link WeaponPose}）对 GeckoLib 物品不生效
     * （模型没有被 {@code AnimatedWeaponModel} 包）。
     *
     * <p>★★ 单位换算：骨骼位移在 display 的 scale <b>之内</b>，所以位移量 = display 增量 / scale
     * （弓 display scale = 0.75 ⇒ ×4/3），不是直接照搬 —— 直接照搬会“对心总差一截”。
     * 数值见 {@link WeaponMount#BOW_BONE_DX} 一组的注释。
     *
     * <p>GeckoLib 的调用顺序是 {@code tickAnimation} 先跑完（骨骼被动画/回位重置写好）、
     * 再调 {@code setCustomAnimations}，所以这里「读→改→写」每帧都从动画值起算，不会累积。
     */
    @Override
    public void setCustomAnimations(CompoundBowItem animatable, long instanceId,
                                    AnimationState<CompoundBowItem> animationState) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return;
        // 只在「拿在手上」（第一/第三人称）时才推骨骼：GUI 图标 / 掉落物 / 展示框别跟着动
        if (!BowGeoRenderer.handPass) return;
        float draw = Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.BOW).draw, 0.0F, 1.0F);
        if (draw <= 0.001F) return;
        CoreGeoBone move = getAnimationProcessor().getBone("move");
        if (move == null) return;
        float k = 1.0F - draw;
        move.setRotX(move.getRotX() * k);          // run/run_fast 会摆 ±4°
        move.setRotY(move.getRotY() * k);
        move.setRotZ(move.getRotZ() * k);
        Player local = Minecraft.getInstance().player;
        float sign = local != null && local.getMainArm() != net.minecraft.world.entity.HumanoidArm.RIGHT
                ? -1.0F : 1.0F;
        move.setPosX(move.getPosX() * k + WeaponMount.BOW_BONE_DX * sign * draw);
        move.setPosY(move.getPosY() * k + WeaponMount.BOW_BONE_DY * draw);
        move.setPosZ(move.getPosZ() * k + WeaponMount.BOW_BONE_DZ * draw);
    }
}
