package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.List;

/**
 * AWP 的 GeckoLib 物品渲染器（挂在物品的 {@code getCustomRenderer()} 上，
 * 所以物品本身与 GUI 图标全部由骨骼模型渲染）。
 */
public class AwpGeoRenderer extends GeoItemRenderer<AwpRifleItem> {

    private static AwpGeoRenderer instance;

    /** 会动的光泽层：抛光高光处自发光 + 开火/举枪时更亮 */
    private final GlossGlintLayer<AwpRifleItem> glint;

    public AwpGeoRenderer() {
        super(new AwpGeoModel());
        this.glint = new GlossGlintLayer<>(this, GlossGlintLayer.mask("awp_geo"), 0.55F,
                WeaponAnim.Kind.AWP);
    }

    /**
     * 记录这一遍是不是「拿在手上」（第一/第三人称）：举枪位移、开火后坐、换弹/拉栓/抛壳
     * 只在这种语境下生效，否则物品栏图标、掉落物、展示框里的枪也会跟着动。
     */
    @Override
    public void renderByItem(net.minecraft.world.item.ItemStack stack,
                             net.minecraft.world.item.ItemDisplayContext transformType,
                             com.mojang.blaze3d.vertex.PoseStack poseStack,
                             net.minecraft.client.renderer.MultiBufferSource bufferSource,
                             int packedLight, int packedOverlay) {
        AwpGeoModel.handPass = isHand(transformType);
        try {
            super.renderByItem(stack, transformType, poseStack, bufferSource, packedLight, packedOverlay);
        } finally {
            AwpGeoModel.handPass = false;
        }
    }

    /** 是不是「拿在手上」（第一/第三人称） */
    static boolean isHand(net.minecraft.world.item.ItemDisplayContext type) {
        return type == net.minecraft.world.item.ItemDisplayContext.FIRST_PERSON_RIGHT_HAND
                || type == net.minecraft.world.item.ItemDisplayContext.FIRST_PERSON_LEFT_HAND
                || type == net.minecraft.world.item.ItemDisplayContext.THIRD_PERSON_RIGHT_HAND
                || type == net.minecraft.world.item.ItemDisplayContext.THIRD_PERSON_LEFT_HAND;
    }

    /** GeckoLib 4.8.4 的 getRenderLayers() 是 default 方法，重写即可挂上流光层 */
    @Override
    public List<GeoRenderLayer<AwpRifleItem>> getRenderLayers() {
        return List.of(glint);
    }

    public static AwpGeoRenderer get() {
        if (instance == null) {
            instance = new AwpGeoRenderer();
        }
        return instance;
    }
}
