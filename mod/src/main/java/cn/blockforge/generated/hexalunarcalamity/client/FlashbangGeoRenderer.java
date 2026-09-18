package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.FlashbangItem;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.List;

/**
 * 震爆弹的 GeckoLib 物品渲染器（挂到物品的 IClientItemExtensions#getCustomRenderer）。
 */
public class FlashbangGeoRenderer extends GeoItemRenderer<FlashbangItem> {

    private static FlashbangGeoRenderer instance;

    /** 会动的光泽层：弹体/蓝环的抛光高光自发光（拔销/投掷时更亮） */
    private final GlossGlintLayer<FlashbangItem> glint;

    public FlashbangGeoRenderer() {
        super(new FlashbangGeoModel());
        this.glint = new GlossGlintLayer<>(this, GlossGlintLayer.mask("flashbang_geo"), 0.45F,
                WeaponAnim.Kind.FLASH);
    }

    @Override
    public List<GeoRenderLayer<FlashbangItem>> getRenderLayers() {
        return List.of(glint);
    }

    /** 只有「拿在手上」那一遍才推骨骼（拔销 / 投掷 / 走路摆动），图标与展示框保持静态 */
    @Override
    public void renderByItem(net.minecraft.world.item.ItemStack stack,
                            net.minecraft.world.item.ItemDisplayContext transformType,
                            com.mojang.blaze3d.vertex.PoseStack poseStack,
                            net.minecraft.client.renderer.MultiBufferSource bufferSource,
                            int packedLight, int packedOverlay) {
        FlashbangGeoModel.handPass = AkmGeoRenderer.isHand(transformType);
        try {
            super.renderByItem(stack, transformType, poseStack, bufferSource, packedLight, packedOverlay);
        } finally {
            FlashbangGeoModel.handPass = false;
        }
    }

    public static FlashbangGeoRenderer get() {
        if (instance == null) {
            instance = new FlashbangGeoRenderer();
        }
        return instance;
    }
}
