package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.List;

/** 十字弩的 GeckoLib 物品渲染器。 */
public class CrossbowGeoRenderer extends GeoItemRenderer<CrossbowWeaponItem> {

    private static CrossbowGeoRenderer instance;

    /** 会动的光泽层：镜筒/弓臂的抛光高光自发光 + 开镜上弦时更亮 */
    private final GlossGlintLayer<CrossbowWeaponItem> glint;

    public CrossbowGeoRenderer() {
        super(new CrossbowGeoModel());
        this.glint = new GlossGlintLayer<>(this, GlossGlintLayer.mask("crossbow_geo"), 0.55F,
                WeaponAnim.Kind.CROSSBOW);
    }

    /**
     * 记下这一遍是不是「拿在手上」（第一/第三人称）：后坐在这些语境下才生效，
     * 否则物品栏图标 / 掉落物 / 展示框也会跟着往后拖（见 {@link CrossbowGeoModel#handPass}）。
     */
    @Override
    public void renderByItem(net.minecraft.world.item.ItemStack stack,
                            net.minecraft.world.item.ItemDisplayContext transformType,
                            com.mojang.blaze3d.vertex.PoseStack poseStack,
                            net.minecraft.client.renderer.MultiBufferSource bufferSource,
                            int packedLight, int packedOverlay) {
        CrossbowGeoModel.handPass = AkmGeoRenderer.isHand(transformType);
        try {
            super.renderByItem(stack, transformType, poseStack, bufferSource, packedLight, packedOverlay);
        } finally {
            CrossbowGeoModel.handPass = false;
        }
    }

    @Override
    public List<GeoRenderLayer<CrossbowWeaponItem>> getRenderLayers() {
        return List.of(glint);
    }

    public static CrossbowGeoRenderer get() {
        if (instance == null) {
            instance = new CrossbowGeoRenderer();
        }
        return instance;
    }
}
