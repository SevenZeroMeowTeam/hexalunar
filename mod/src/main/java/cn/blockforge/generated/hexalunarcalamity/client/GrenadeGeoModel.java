package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.item.FragGrenadeItem;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import software.bernie.geckolib.core.animatable.model.CoreGeoBone;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;

/**
 * 碎片手雷的 GeckoLib 模型（真骨骼，6 根：root → move → body → fuze → spoon / pin）。
 *
 * <p>模型由 {@code tools/grenade_gen.py} 按参考模型 {@code 模型/mud.bbmodel} 的实测比例重建：
 * 菠萝弹体（半径 5.4 缩到手持大小）、引信颈+帽、背面压把、穿过引信的保险销+拉环。
 * 保险销拉出方向 = <b>-Z（北）</b>。
 *
 * <p>拔销 / 压把弹开是连续动作，所以在这里程序化推骨骼（照 SuperbWarfare 的 BocekItemModel
 * 用 bowPullPos 推枪身的做法）：拔销进度直接取 {@code GrenadeItem.clientPullProgress}，
 * 压把在引信开始跑之后弹开。
 */
public class GrenadeGeoModel extends GeoModel<FragGrenadeItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/mud.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/mud_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/mud.animation.json");

    /** 压把弹开的目标角度（度） */
    private static final float SPOON_OPEN_DEG = 38.0F;
    /** 保险销被拉出的最大距离（模型像素） */
    private static final float PIN_PULL_DIST = 1.05F;

    /** 压把弹开程度 0..1，平滑跟随，免得状态切换时跳变 */
    private static float spoonOpen;

    /** 插回销进度，用来把压把压回去 */
    private static float closed;

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

        float pull = GrenadeAnimState.pullProgress();
        float reinsert = GrenadeAnimState.reinsertProgress();
        boolean armed = GrenadeAnimState.armed() || GrenadeAnimState.throwing();

        // 拔销：保险销 + 拉环整体沿 -Z（北）滑出去
        CoreGeoBone pin = getAnimationProcessor().getBone("pin");
        if (pin != null) {
            float out = Math.max(0.0F, pull) * PIN_PULL_DIST;
            if (reinsert >= 0.0F) {
                out = (1.0F - Mth.clamp(reinsert, 0.0F, 1.0F)) * PIN_PULL_DIST;
            } else if (armed) {
                out = PIN_PULL_DIST;      // 拔出来之后就一直保持拔出状态
            }
            pin.setPosZ(-out);
        }

        // 压把：销一拔、引信开始跑，它就被簧弹开；插回销时压回去
        CoreGeoBone spoon = getAnimationProcessor().getBone("spoon");
        if (spoon != null) {
            float target = armed ? 1.0F : 0.0F;
            if (reinsert >= 0.0F) {
                target = 1.0F - Mth.clamp(reinsert, 0.0F, 1.0F);
            }
            spoonOpen += (target - spoonOpen) * 0.25F;
            spoon.setRotX(-spoonOpen * SPOON_OPEN_DEG * Mth.DEG_TO_RAD);
        }
        closed = armed ? 0.0F : 1.0F;
    }
}
