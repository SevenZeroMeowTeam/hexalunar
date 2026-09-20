package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.M1GarandItem;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.List;

/**
 * M1 加兰德的 GeckoLib 物品渲染器（挂在物品的 {@code initializeClient} 上，
 * 所以物品本身与 GUI 图标全部由骨骼模型渲染）——照 {@link Kar98kGeoRenderer} 抄。
 */
public class M1GarandGeoRenderer extends GeoItemRenderer<M1GarandItem> {

    private static M1GarandGeoRenderer instance;

    /** 会动的光泽层：抛光高光处自发光 + 开火/举枪时更亮（遮罩由 m1_garand_gen.py 一并生成） */
    private final GlossGlintLayer<M1GarandItem> glint;

    public M1GarandGeoRenderer() {
        super(new M1GarandGeoModel());
        this.glint = new GlossGlintLayer<>(this, GlossGlintLayer.mask("m1_garand_geo"), 0.42F,
                WeaponAnim.Kind.M1_GARAND);
    }

    /**
     * 记录这一遍是不是「拿在手上」（第一/第三人称）：举枪位移、后坐、枪机循环、抛壳、压漏夹
     * 只在这种语境下生效，否则物品栏图标、掉落物、展示框里的枪也会跟着动。
     */
    @Override
    public void renderByItem(net.minecraft.world.item.ItemStack stack,
                             net.minecraft.world.item.ItemDisplayContext transformType,
                             com.mojang.blaze3d.vertex.PoseStack poseStack,
                             net.minecraft.client.renderer.MultiBufferSource bufferSource,
                             int packedLight, int packedOverlay) {
        M1GarandGeoModel.handPass = isHand(transformType);
        try {
            super.renderByItem(stack, transformType, poseStack, bufferSource, packedLight, packedOverlay);
        } finally {
            M1GarandGeoModel.handPass = false;
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
    public List<GeoRenderLayer<M1GarandItem>> getRenderLayers() {
        return List.of(glint);
    }

    public static M1GarandGeoRenderer get() {
        if (instance == null) {
            instance = new M1GarandGeoRenderer();
        }
        return instance;
    }
}
