package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.entity.GiantArrowEntity;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRendererProvider;

/** 巨型箭矢：放大渲染的追踪箭 */
public class GiantArrowRenderer extends SimpleArrowRenderer<GiantArrowEntity> {

    public GiantArrowRenderer(EntityRendererProvider.Context context) {
        super(context, SPECTRAL_TEX);
    }

    @Override
    public void render(GiantArrowEntity arrow, float yaw, float partialTick,
                       PoseStack stack, MultiBufferSource source, int light) {
        stack.pushPose();
        stack.scale(2.4F, 2.4F, 2.4F);
        super.render(arrow, yaw, partialTick, stack, source, light);
        stack.popPose();
    }
}
