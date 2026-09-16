package cn.blockforge.generated.hexalunarcalamity.client;

import net.minecraft.client.renderer.entity.ArrowRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.projectile.AbstractArrow;

/** 弩箭/复合箭/毒箭：沿用原版箭模型，只换贴图路径 */
public class SimpleArrowRenderer<T extends AbstractArrow> extends ArrowRenderer<T> {

    // 1.20.1 原版箭贴图实际位于 textures/entity/projectiles/ 下；为避免玩家资产
    // 缺失时报 FileNotFound，模组自带一份同布局贴图放在自己的命名空间里。
    public static final ResourceLocation ARROW_TEX =
            new ResourceLocation("hexalunar_calamity", "textures/entity/hlc_arrow.png");
    public static final ResourceLocation SPECTRAL_TEX =
            new ResourceLocation("hexalunar_calamity", "textures/entity/hlc_spectral_arrow.png");

    private final ResourceLocation texture;

    public SimpleArrowRenderer(EntityRendererProvider.Context context, ResourceLocation texture) {
        super(context);
        this.texture = texture;
    }

    @Override
    public ResourceLocation getTextureLocation(T entity) {
        return texture;
    }
}
