package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.List;

/**
 * 复合弓的 GeckoLib 物品渲染器。
 *
 * <p>挂在物品的 {@code IClientItemExtensions#getCustomRenderer()} 上，
 * 于是物品本身（含 GUI 图标、第一人称手持、第三人称）全部由 GeckoLib 用骨骼模型渲染，
 * 换弹 / 拉弦 / 放箭动画都能看到。
 */
public class BowGeoRenderer extends GeoItemRenderer<CompoundBowItem> {

    private static BowGeoRenderer instance;

    /**
     * 当前这一遍渲染是不是「拿在手上」（第一/第三人称）。
     * GeckoLib 的 {@code setCustomAnimations} 对 GUI 图标 / 掉落物 / 展示框一样会跑，
     * 不加这个判断的话「拉弦对心」的骨骼位移会把物品栏里的图标也一起推走。
     */
    static boolean handPass = false;

    /** 会动的光泽层：抛光高光处自发光 + 拉弦/放箭时更亮 */
    private final GlossGlintLayer<CompoundBowItem> glint;

    public BowGeoRenderer() {
        super(new BowGeoModel());
        this.glint = new GlossGlintLayer<>(this, GlossGlintLayer.mask("compound_bow_geo"),
                0.55F, WeaponAnim.Kind.BOW);
    }

    @Override
    public void renderByItem(net.minecraft.world.item.ItemStack stack,
                            net.minecraft.world.item.ItemDisplayContext transformType,
                            com.mojang.blaze3d.vertex.PoseStack poseStack,
                            net.minecraft.client.renderer.MultiBufferSource bufferSource,
                            int packedLight, int packedOverlay) {
        handPass = AkmGeoRenderer.isHand(transformType);
        try {
            super.renderByItem(stack, transformType, poseStack, bufferSource, packedLight, packedOverlay);
        } finally {
            handPass = false;
        }
    }

    /** GeckoLib 4.8.4 的 getRenderLayers() 是 default 方法，重写即可挂上流光层 */
    @Override
    public List<GeoRenderLayer<CompoundBowItem>> getRenderLayers() {
        return List.of(glint);
    }

    /** 单例：物品的客户端扩展每次调用都要返回同一个实例。 */
    public static BowGeoRenderer get() {
        if (instance == null) {
            instance = new BowGeoRenderer();
        }
        return instance;
    }
}
