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
