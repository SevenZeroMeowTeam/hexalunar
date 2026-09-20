package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.MosinRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.Sights;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.List;

/**
 * 莫辛-纳甘的 GeckoLib 物品渲染器（挂在物品的 {@code initializeClient} 上，
 * 所以物品本身与 GUI 图标全部由骨骼模型渲染）——照 {@link Kar98kGeoRenderer} / {@link AkmGeoRenderer} 抄。
 */
public class MosinGeoRenderer extends GeoItemRenderer<MosinRifleItem> {

    private static MosinGeoRenderer instance;

    /** 会动的光泽层：抛光高光处自发光 + 开火/举枪时更亮（遮罩 {@code mosin_geo_glowmask.png}） */
    private final GlossGlintLayer<MosinRifleItem> glint;

    public MosinGeoRenderer() {
        super(new MosinGeoModel());
        this.glint = new GlossGlintLayer<>(this, GlossGlintLayer.mask("mosin_geo"), 0.52F,
                WeaponAnim.Kind.MOSIN);
    }

    /**
     * 记录这一遍是不是「拿在手上」（第一/第三人称），并按物品 NBT 设置**瞄具档位**
     * —— 4 倍镜筒只在装了镜子时显示（莫辛出厂自带，拆掉后就是机瞄）。
     */
    @Override
    public void renderByItem(net.minecraft.world.item.ItemStack stack,
                             net.minecraft.world.item.ItemDisplayContext transformType,
                             com.mojang.blaze3d.vertex.PoseStack poseStack,
                             net.minecraft.client.renderer.MultiBufferSource bufferSource,
                             int packedLight, int packedOverlay) {
        MosinGeoModel.sightNow = MosinRifleItem.sight(stack);
        MosinGeoModel.handPass = isHand(transformType);
        try {
            super.renderByItem(stack, transformType, poseStack, bufferSource, packedLight, packedOverlay);
        } finally {
            MosinGeoModel.sightNow = Sights.SCOPE;
            MosinGeoModel.handPass = false;
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
    public List<GeoRenderLayer<MosinRifleItem>> getRenderLayers() {
        return List.of(glint);
    }

    public static MosinGeoRenderer get() {
        if (instance == null) {
            instance = new MosinGeoRenderer();
        }
        return instance;
    }
}
