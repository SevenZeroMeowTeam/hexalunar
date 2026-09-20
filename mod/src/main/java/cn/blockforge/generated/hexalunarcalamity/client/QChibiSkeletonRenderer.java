package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.SkeletonRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.monster.AbstractSkeleton;

/**
 * ★ Q 弹版：**Q 版骷髅渲染器**（冲刺骷髅 / 剧毒骷髅）。
 *
 * <p>几何复用 {@link QChibiZombieModel#SKELETON_LAYER}（同一套 chibi 大头矮胖身子，
 * 只是换成骨头皮肤 {@code q_chibi_skeleton.png}），**行为逻辑仍然交给原版的
 * {@code SkeletonModel}** —— 拉弓瞄准姿势、走路摆手全都不用自己写。
 *
 * <p>注意 1.20.1 的原版签名（用 {@code javap} 核过）：
 * <ul>
 *   <li>{@code SkeletonRenderer(Context, ModelLayerLocation, ModelLayerLocation, ModelLayerLocation)}
 *       —— 后三个参数是「主模型 / 内层甲 / 外层甲」的**层 id**，不是模型实例；
 *       我们把三个都指向 chibi 层，于是穿甲时也用 Q 版身形。</li>
 *   <li>它继承的是 {@code HumanoidMobRenderer<AbstractSkeleton, SkeletonModel<AbstractSkeleton>>}
 *       —— 所以覆写的方法参数类型是 {@code AbstractSkeleton}（不是 {@code Skeleton}）。</li>
 * </ul>
 *
 * <p>晃动与自爆尸那套一样，走 {@link QChibi}（无状态挤压拉伸 + 小跳）。
 * 染色层沿用原版那套 {@link VariantTintLayer}，所以「哪只是哪只」一眼可辨。
 */
public class QChibiSkeletonRenderer extends SkeletonRenderer {

    /** Q 版骷髅皮肤（{@code tools/q_chibi_skeleton_tex.py} 按同一张 UV 表画） */
    public static final ResourceLocation SKELETON_TEXTURE = new ResourceLocation(
            HexaLunarCalamity.MOD_ID, "textures/entity/q_chibi_skeleton.png");

    private final ResourceLocation texture;
    private final float scaleFactor;

    public QChibiSkeletonRenderer(EntityRendererProvider.Context ctx, ResourceLocation texture,
                                  int tintRgb, int tintAlpha, float scale) {
        super(ctx, QChibiZombieModel.SKELETON_LAYER,
                QChibiZombieModel.SKELETON_LAYER, QChibiZombieModel.SKELETON_LAYER);
        this.texture = texture;
        this.scaleFactor = scale;
        if (tintAlpha > 0) {
            addLayer(new VariantTintLayer(this, tintRgb, tintAlpha));
        }
    }

    @Override
    public ResourceLocation getTextureLocation(AbstractSkeleton entity) {
        return texture;
    }

    @Override
    protected void setupRotations(AbstractSkeleton entity, PoseStack pose, float ageInTicks,
                                  float bodyYaw, float partialTick) {
        super.setupRotations(entity, pose, ageInTicks, bodyYaw, partialTick);
        QChibi.hop(entity, pose, 0.085F);
    }

    @Override
    protected void scale(AbstractSkeleton entity, PoseStack pose, float partialTick) {
        if (scaleFactor != 1.0F) {
            pose.scale(scaleFactor, scaleFactor, scaleFactor);
        }
        QChibi.squash(entity, pose, partialTick, 0.11F, 0.045F, 0.16F);
    }
}
