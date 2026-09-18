package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.List;

/**
 * AKM 的 GeckoLib 物品渲染器。
 *
 * <p>是个 {@code BlockEntityWithoutLevelRenderer}，挂在物品的
 * {@code IClientItemExtensions#getCustomRenderer()} 上，
 * 于是物品本身（含 GUI 图标）全部由 GeckoLib 用骨骼模型渲染。
 */
public class AkmGeoRenderer extends GeoItemRenderer<AkmRifleItem> {

    private static AkmGeoRenderer instance;

    /** 会动的光泽层：抛光高光处自发光 + 开火/举枪时更亮 */
    private final GlossGlintLayer<AkmRifleItem> glint;

    public AkmGeoRenderer() {
        super(new AkmGeoModel());
        this.glint = new GlossGlintLayer<>(this, GlossGlintLayer.mask("akm_geo"), 0.55F,
                WeaponAnim.Kind.AKM);
    }

    /**
     * 把被渲染的那把枪的瞄具 NBT 传给模型（GeckoLib 的 animatable 是物品单例，拿不到 NBT）。
     * GUI 图标也一样：装了红点/倍镜的枪，图标上也会显示那个瞄具。
     */
    @Override
    public void renderByItem(net.minecraft.world.item.ItemStack stack,
                            net.minecraft.world.item.ItemDisplayContext transformType,
                            com.mojang.blaze3d.vertex.PoseStack poseStack,
                            net.minecraft.client.renderer.MultiBufferSource bufferSource,
                            int packedLight, int packedOverlay) {
        AkmGeoModel.sightNow = cn.blockforge.generated.hexalunarcalamity.weapon.Sights.sight(stack);
        AkmGeoModel.handPass = isHand(transformType);
        try {
            super.renderByItem(stack, transformType, poseStack, bufferSource, packedLight, packedOverlay);
        } finally {
            AkmGeoModel.sightNow = cn.blockforge.generated.hexalunarcalamity.weapon.Sights.IRON;
            AkmGeoModel.handPass = false;
        }
    }

    /**
     * 是不是「拿在手上」（第一/第三人称）—— 举枪位移与开火后坐只在这种语境下生效；
     * GUI 图标 / 掉落物 / 展示框不算，否则物品栏里的图标会跟着一起动。
     */
    static boolean isHand(net.minecraft.world.item.ItemDisplayContext type) {
        return type == net.minecraft.world.item.ItemDisplayContext.FIRST_PERSON_RIGHT_HAND
                || type == net.minecraft.world.item.ItemDisplayContext.FIRST_PERSON_LEFT_HAND
                || type == net.minecraft.world.item.ItemDisplayContext.THIRD_PERSON_RIGHT_HAND
                || type == net.minecraft.world.item.ItemDisplayContext.THIRD_PERSON_LEFT_HAND;
    }

    /** GeckoLib 4.8.4 的 getRenderLayers() 是 default 方法，重写即可挂上流光层 */
    @Override
    public List<GeoRenderLayer<AkmRifleItem>> getRenderLayers() {
        return List.of(glint);
    }

    /** 单例：物品的客户端扩展每次调用都要返回同一个实例。 */
    public static AkmGeoRenderer get() {
        if (instance == null) {
            instance = new AkmGeoRenderer();
        }
        return instance;
    }
}
