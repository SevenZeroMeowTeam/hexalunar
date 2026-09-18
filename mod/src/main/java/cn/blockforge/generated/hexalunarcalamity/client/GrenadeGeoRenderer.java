package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.FragGrenadeItem;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

import java.util.List;

/**
 * 碎片手雷的 GeckoLib 物品渲染器（挂到物品的 IClientItemExtensions#getCustomRenderer）。
 *
 * <p>于是手雷本体（含 GUI 图标、第一人称手持、第三人称）全部由骨骼模型渲染，
 * 拔销 / 压把弹开 / 投掷 都能看到。
 */
public class GrenadeGeoRenderer extends GeoItemRenderer<FragGrenadeItem> {

    private static GrenadeGeoRenderer instance;

    /** 会动的光泽层：弹体抛光高光自发光（拔销/投掷时更亮） */
    private final GlossGlintLayer<FragGrenadeItem> glint;

    public GrenadeGeoRenderer() {
        super(new GrenadeGeoModel());
        this.glint = new GlossGlintLayer<>(this, GlossGlintLayer.mask("mud_geo"), 0.45F,
                WeaponAnim.Kind.GRENADE);
    }

    @Override
    public List<GeoRenderLayer<FragGrenadeItem>> getRenderLayers() {
        return List.of(glint);
    }

    public static GrenadeGeoRenderer get() {
        if (instance == null) {
            instance = new GrenadeGeoRenderer();
        }
        return instance;
    }
}
