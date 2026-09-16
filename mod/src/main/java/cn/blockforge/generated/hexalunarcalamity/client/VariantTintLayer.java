package cn.blockforge.generated.hexalunarcalamity.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;

/**
 * 变种着色层：以半透明叠加给僵尸/骷髅整体染上标识色。
 */
public class VariantTintLayer extends RenderLayer {

    private final float r;
    private final float g;
    private final float b;
    private final float a;

    public VariantTintLayer(RenderLayerParent parent, int rgb, int alpha) {
        super(parent);
        this.r = ((rgb >> 16) & 0xFF) / 255F;
        this.g = ((rgb >> 8) & 0xFF) / 255F;
        this.b = (rgb & 0xFF) / 255F;
        this.a = Math.min(1.0F, Math.max(0.0F, alpha / 255F));
    }

    @Override
    @SuppressWarnings("unchecked")
    public void render(PoseStack stack, MultiBufferSource source, int light, Entity entity,
                       float limbSwing, float limbSwingAmount, float partialTick,
                       float ageInTicks, float netHeadYaw, float headPitch) {
        if (!(entity instanceof LivingEntity)) return;
        VertexConsumer buffer = source.getBuffer(RenderType.entityTranslucent(getTextureLocation(entity)));
        stack.pushPose();
        stack.scale(1.025F, 1.025F, 1.025F);
        ((EntityModel<LivingEntity>) getParentModel()).renderToBuffer(
                stack, buffer, light, OverlayTexture.NO_OVERLAY, r, g, b, a);
        stack.popPose();
    }
}
