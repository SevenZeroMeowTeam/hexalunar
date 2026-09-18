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

    /** 会动的光泽层：抛光高光处自发光 + 拉弦/放箭时更亮 */
    private final GlossGlintLayer<CompoundBowItem> glint;

    public BowGeoRenderer() {
        super(new BowGeoModel());
        this.glint = new GlossGlintLayer<>(this, GlossGlintLayer.mask("compound_bow_geo"),
                0.55F, WeaponAnim.Kind.BOW);
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
