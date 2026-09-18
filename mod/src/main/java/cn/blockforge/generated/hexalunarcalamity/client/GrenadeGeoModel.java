package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.item.FragGrenadeItem;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;

/**
 * 碎片手雷的 GeckoLib 模型（真骨骼，6 根：root → move → body → fuze → spoon / pin）。
 *
 * <p>模型由 {@code tools/grenade_gen.py} 按参考模型 {@code 模型/mud.bbmodel} 的实测比例重建：
 * 菠萝弹体（半径 5.4 缩到手持大小）、引信颈+帽、背面压把、穿过引信的保险销+拉环。
 * 保险销拉出方向 = <b>-Z（北）</b>。
 *
 * <p>动作（拔销手腕外翻 / 投掷甩手 / 走路摆动）+ 保险销 / 压把的推法，全部在
 * {@link GrenadePose} 里（碎片手雷与震爆弹共用一份，离线验算 tools/_gren_story.py）。
 */
public class GrenadeGeoModel extends GeoModel<FragGrenadeItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/mud.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/mud_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/mud.animation.json");

    /** 这一遍渲染是不是「拿在手上」（由 {@link GrenadeGeoRenderer} 设入） */
    static boolean handPass;

    @Override
    public ResourceLocation getModelResource(FragGrenadeItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(FragGrenadeItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(FragGrenadeItem animatable) {
        return ANIMATION;
    }

    @Override
    public void setCustomAnimations(FragGrenadeItem animatable, long instanceId,
                                    AnimationState<FragGrenadeItem> animationState) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return;
        // ★ GUI 图标 / 掉落物 / 展示框：一律静态（销插着、压把不弹）——
        //   不然物品栏里的图标会跟着手上的拔销/投掷动作一起变
        if (!handPass) return;
        GrenadePose.drive(this, WeaponAnim.Kind.GRENADE);
    }
}
