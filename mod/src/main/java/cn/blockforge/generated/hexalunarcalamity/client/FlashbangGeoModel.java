package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.item.FlashbangItem;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;

/**
 * 震爆弹的 GeckoLib 模型（真骨骼，6 根：root → move → body → fuze → spoon / pin）。
 *
 * <p>模型由 {@code tools/flashbang_gen.py} 按参考模型 {@code 模型/mtx.bbmodel} 的实测比例重建：
 * 军绿圆柱弹体（十字双盒拟八边形）+ 蓝色环带 + 加宽底盖 + 引信头 + 侧面压把 + 穿引信的保险销/拉环。
 * 保险销拉出方向 = <b>-Z（北）</b>，原点在弹体中心（握在手里）。
 *
 * <p>拔销 / 压把弹开是连续动作，这里每帧程序化推骨骼（同碎片手雷 GrenadeGeoModel 的做法）：
 * 进度直接取 {@code GrenadeItem.clientPullProgress / clientReinsertProgress}
 * （震爆弹也继承 GrenadeItem，状态机是同一套）。
 */
public class FlashbangGeoModel extends GeoModel<FlashbangItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/flashbang.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/flashbang_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/flashbang.animation.json");

    /** 这一遍渲染是不是「拿在手上」（由 {@link FlashbangGeoRenderer} 设入） */
    static boolean handPass;

    @Override
    public ResourceLocation getModelResource(FlashbangItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(FlashbangItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(FlashbangItem animatable) {
        return ANIMATION;
    }

    @Override
    public void setCustomAnimations(FlashbangItem animatable, long instanceId,
                                    AnimationState<FlashbangItem> animationState) {
        if (!net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) return;
        // GUI 图标 / 掉落物 / 展示框：静态（动作与推骨骼都在 GrenadePose 里）
        if (!handPass) return;
        GrenadePose.drive(this, WeaponAnim.Kind.FLASH);
    }
}
