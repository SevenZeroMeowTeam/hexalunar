package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.item.FlashbangItem;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import software.bernie.geckolib.core.animatable.model.CoreGeoBone;
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

    private static final float SPOON_OPEN_DEG = 42.0F;
    private static final float PIN_PULL_DIST = 1.15F;

    private static float spoonOpen;

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

        float pull = GrenadeAnimState.pullProgress();
        float reinsert = GrenadeAnimState.reinsertProgress();
        boolean armed = GrenadeAnimState.armed() || GrenadeAnimState.throwing();

        // 拔销：保险销 + 拉环沿 -Z（北）滑出去
        CoreGeoBone pin = getAnimationProcessor().getBone("pin");
        if (pin != null) {
            float out = Math.max(0.0F, pull) * PIN_PULL_DIST;
            if (reinsert >= 0.0F) {
                out = (1.0F - Mth.clamp(reinsert, 0.0F, 1.0F)) * PIN_PULL_DIST;
            } else if (armed) {
                out = PIN_PULL_DIST;
            }
            pin.setPosZ(-out);
        }

        // 压把：销拔出、引信开始跑之后弹开；插回销时压回去
        CoreGeoBone spoon = getAnimationProcessor().getBone("spoon");
        if (spoon != null) {
            float target = armed ? 1.0F : 0.0F;
            if (reinsert >= 0.0F) {
                target = 1.0F - Mth.clamp(reinsert, 0.0F, 1.0F);
            }
            spoonOpen += (target - spoonOpen) * 0.25F;
            // 压把在 -X 侧竖直，绕 Z 轴向外弹开（手雷那种在 +Z 背面、绕 X）
            spoon.setRotZ(-spoonOpen * SPOON_OPEN_DEG * Mth.DEG_TO_RAD);
        }
    }
}
