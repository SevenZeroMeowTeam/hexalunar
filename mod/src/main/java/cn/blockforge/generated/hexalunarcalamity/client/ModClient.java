package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.entity.BoltEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.PiercingArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.ToxicArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.SkeletonRenderer;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.client.renderer.entity.ZombieRenderer;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.ModelEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;

import java.util.ArrayList;
import java.util.Map;

/** 实体渲染器注册：投射物与六只特殊感染者 */
@Mod.EventBusSubscriber(modid = HexaLunarCalamity.MOD_ID, value = Dist.CLIENT, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class ModClient {

    private static final org.slf4j.Logger LOGGER =
            org.slf4j.LoggerFactory.getLogger(HexaLunarCalamity.MOD_ID);

    /**
     * 给武器模型套上会动的一层（见 {@link AnimatedWeaponModel}）：
     * 模型键是 {@code hexalunar_calamity:akm#inventory} 这种，拉弦变体是
     * {@code hexalunar_calamity:item/compound_bow_pulling_0#inventory}，按路径前缀认领。
     */
    @SubscribeEvent
    public static void onModifyBakingResult(ModelEvent.ModifyBakingResult event) {
        Map<net.minecraft.resources.ResourceLocation, net.minecraft.client.resources.model.BakedModel> models =
                event.getModels();
        int wrapped = 0;
        for (net.minecraft.resources.ResourceLocation id : new ArrayList<>(models.keySet())) {
            if (!HexaLunarCalamity.MOD_ID.equals(id.getNamespace())) continue;
            WeaponAnim.Kind kind = kindOfModel(id.getPath());
            if (kind == null) continue;
            net.minecraft.client.resources.model.BakedModel baked = models.get(id);
            if (baked == null || baked instanceof AnimatedWeaponModel) continue;
            models.put(id, new AnimatedWeaponModel(baked, kind));
            wrapped++;
        }
        // 十字弩的弩箭 / 左手分件（上弦动画，见 CrossbowPartAnim）
        CrossbowPartModels.capture(models);
        LOGGER.info("手持动作动画已启用：包装了 {} 个武器模型", wrapped);
    }

    /** 登记不会被任何物品引用的分件模型，否则烘焙阶段不会加载它们 */
    @SubscribeEvent
    public static void onRegisterAdditionalModels(ModelEvent.RegisterAdditional event) {
        CrossbowPartModels.registerAdditional(event);
    }

    /** 模型路径 → 动作种类；返回 null 表示该模型不需要动（弹药、分件、图标等） */
    private static WeaponAnim.Kind kindOfModel(String path) {
        // 分件由 AnimatedWeaponModel 在渲染时合成，不能自己再包一层，否则会被重复施加变换
        if (path.contains("akm_mag") || path.contains("akm_bolt")) return null;
        if (path.contains("crossbow_bolt")) return null;
        // AKM 用 GeckoLib 骨骼渲染（AkmGeoRenderer），不再需要 OBJ 分件包装
        if (path.startsWith("akm")) return null;
        // AWP 同样用 GeckoLib 骨骼渲染（AwpGeoRenderer + geo/awp.geo.json）
        if (path.startsWith("awp")) return null;
        // ★ r105 Kar98k 也用 GeckoLib 骨骼渲染（Kar98kGeoRenderer + geo/kar98k.geo.json）
        if (path.startsWith("kar98k")) return null;
        // ★ r106 莫辛-纳甘（MosinGeoRenderer + geo/mosin.geo.json）
        if (path.startsWith("mosin")) return null;
        // ★ r108 M1 加兰德（M1GarandGeoRenderer + geo/m1_garand.geo.json）
        if (path.startsWith("m1_garand")) return null;
        // 十字弩也改 GeckoLib 骨骼渲染（CrossbowGeoRenderer + geo/crossbow_geo.geo.json），
        // 拉弦装弹由 CrossbowGeoModel 程序化驱动，不再走 OBJ 分件/display 包装
        if (path.startsWith("crossbow") || path.contains("crossbow_pulling")) return null;
        // 复合弓也用 GeckoLib 骨骼渲染（BowGeoRenderer + geo/compound_bow.geo.json），
        // 拉弦/换弹由骨骼动画驱动，不再需要 OBJ 分件包装
        if (path.contains("compound_bow")) return null;
        // 碎片手雷用手 GeckoLib 骨骼渲染（GrenadeGeoRenderer + geo/mud.geo.json），
        // 拔销/压把由 GrenadeGeoModel 程序化驱动，不再需要 OBJ display 包装
        if (path.startsWith("mud") || path.contains("frag_grenade")) return null;
        // 震爆弹同样改 GeckoLib 骨骼渲染（FlashbangGeoRenderer + geo/flashbang.geo.json）
        if (path.startsWith("mtx") || path.contains("flashbang")) return null;
        return null;
    }

    /**
     * 拉弦动画：注册与原版弓同名的物品属性（本项目用自己的命名空间避免冲突），
     * 模型 crossbow.json / compound_bow.json 里的 overrides 靠它们切到 pulling_0/1/2 三段弦形。
     */
    @SubscribeEvent
    public static void onClientSetup(FMLClientSetupEvent event) {
        event.enqueueWork(() -> {
            for (net.minecraft.world.item.Item weapon : new net.minecraft.world.item.Item[]{
                    ModItems.COMPOUND_BOW.get(), ModItems.CROSSBOW.get()}) {
                ItemProperties.register(weapon,
                        ResourceLocation.fromNamespaceAndPath(HexaLunarCalamity.MOD_ID, "pull"),
                        (stack, level, entity, seed) -> {
                            // 上弦（装填）时用上弦进度驱动弦形：手一拉就往后收
                            if (stack.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem
                                    && level != null) {
                                float p = cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem
                                        .reloadProgress(stack, level.getGameTime());
                                if (p >= 0.0F) {
                                    // 弦在拉弦阶段（前 62%）收完，剩下时间留给推箭入槽
                                    return Math.min(1.0F, p / 0.62F);
                                }
                            }
                            if (entity == null || entity.getUseItem() != stack) return 0.0F;
                            // 与原版弓一致：已蓄力 tick / 20（20 tick = 满蓄）
                            return (float) (stack.getUseDuration() - entity.getUseItemRemainingTicks()) / 20.0F;
                        });
                ItemProperties.register(weapon,
                        ResourceLocation.fromNamespaceAndPath(HexaLunarCalamity.MOD_ID, "pulling"),
                        (stack, level, entity, seed) -> {
                            if (stack.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem
                                    && level != null
                                    && cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem
                                            .reloading(stack, level.getGameTime())) {
                                return 1.0F;
                            }
                            return entity != null && entity.isUsingItem() && entity.getUseItem() == stack
                                    ? 1.0F : 0.0F;
                        });
            }
        });
    }

    /**
     * ★ Q 弹版：注册 Q 版僵尸的模型层（几何 + 64×64 UV 布局，见 {@link QChibiZombieModel}）。
     *
     * <p>普通版也照常注册（只是没人用）—— 注册一个模型层没有任何副作用，
     * 而这样代码里就不用为「要不要注册」再分一次支。
     */
    @SubscribeEvent
    public static void onRegisterLayerDefinitions(
            net.minecraftforge.client.event.EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(QChibiZombieModel.LAYER, QChibiZombieModel::createBodyLayer);
    }

    @SubscribeEvent
    public static void onRegisterRenderers(EntityRenderersEvent.RegisterRenderers event) {
        // 投射物
        event.registerEntityRenderer(ModEntities.BOLT.get(), BoltRenderer::new);
        event.registerEntityRenderer(ModEntities.COMPOUND_ARROW.get(), CompoundArrowRenderer::new);
        event.registerEntityRenderer(ModEntities.TOXIC_ARROW.get(), ToxicArrowRenderer::new);
        event.registerEntityRenderer(ModEntities.GIANT_ARROW.get(), GiantArrowRenderer::new);
        event.registerEntityRenderer(ModEntities.BULLET.get(), BulletRenderer::new);
        event.registerEntityRenderer(ModEntities.POISON_BOTTLE.get(),
                ctx -> new ThrownItemRenderer(ctx, 0.9F, false));
        // 手雷：出手后压杆脱落，靠引信火星与烟迹表现，模型沿用物品贴图
        event.registerEntityRenderer(ModEntities.GRENADE.get(),
                ctx -> new ThrownItemRenderer(ctx, 0.85F, false));

        // 特殊感染者：僵尸变种
        // ★ Q 弹版（-Pqmode=true）：自爆尸换成「大头矮胖 + 果冻晃动」的 Q 版渲染器；
        //   普通版保持原样（Q_MODE 是编译期常量，普通版这段分支会被 javac 直接折掉）
        if (cn.blockforge.generated.hexalunarcalamity.BuildInfo.Q_MODE) {
            event.registerEntityRenderer(ModEntities.BOMBER_ZOMBIE.get(),
                    ctx -> new QChibiZombieRenderer<>(ctx));
        } else {
            event.registerEntityRenderer(ModEntities.BOMBER_ZOMBIE.get(),
                    ctx -> tintedZombie(ctx, 0xFFB45A, 120));
        }
        event.registerEntityRenderer(ModEntities.ARCHER_ZOMBIE.get(),
                ctx -> tintedZombie(ctx, 0x59C46B, 96));
        event.registerEntityRenderer(ModEntities.BARREL_ZOMBIE.get(),
                ctx -> tintedZombie(ctx, 0x6E6E78, 110));
        event.registerEntityRenderer(ModEntities.GIANT_ZOMBIE.get(), ModClient::giantZombie);

        // 骷髅变种
        event.registerEntityRenderer(ModEntities.RUSHER_SKELETON.get(),
                ctx -> tintedSkeleton(ctx, 0x7FB6FF, 110));
        event.registerEntityRenderer(ModEntities.TOXIC_SKELETON.get(),
                ctx -> tintedSkeleton(ctx, 0x8FE04A, 130));
    }


    private static ZombieRenderer giantZombie(EntityRendererProvider.Context ctx) {
        // 巨尸：靠缩放渲染体放大 1.9 倍（1.20.1 无 SCALE 属性）
        return new ZombieRenderer(ctx) {
            @Override
            protected void scale(net.minecraft.world.entity.monster.Zombie zombie,
                                 com.mojang.blaze3d.vertex.PoseStack stack, float partialTick) {
                stack.scale(1.9F, 1.9F, 1.9F);
            }
        };
    }

    private static ZombieRenderer tintedZombie(EntityRendererProvider.Context ctx, int rgb, int alpha) {
        ZombieRenderer renderer = new ZombieRenderer(ctx);
        renderer.addLayer(new VariantTintLayer(renderer, rgb, alpha));
        return renderer;
    }

    private static SkeletonRenderer tintedSkeleton(EntityRendererProvider.Context ctx, int rgb, int alpha) {
        SkeletonRenderer renderer = new SkeletonRenderer(ctx);
        renderer.addLayer(new VariantTintLayer(renderer, rgb, alpha));
        return renderer;
    }

    /** 弩箭：沿用原版箭模型，用弩的贴图 */
    public static class BoltRenderer extends SimpleArrowRenderer<BoltEntity> {
        public BoltRenderer(EntityRendererProvider.Context ctx) {
            super(ctx, SimpleArrowRenderer.ARROW_TEX);
        }
    }

    /** 复合弓箭 */
    public static class CompoundArrowRenderer extends SimpleArrowRenderer<PiercingArrowEntity> {
        public CompoundArrowRenderer(EntityRendererProvider.Context ctx) {
            super(ctx, SimpleArrowRenderer.ARROW_TEX);
        }
    }

    /** 尸毒箭：发光箭贴图 */
    public static class ToxicArrowRenderer extends SimpleArrowRenderer<ToxicArrowEntity> {
        public ToxicArrowRenderer(EntityRendererProvider.Context ctx) {
            super(ctx, SimpleArrowRenderer.SPECTRAL_TEX);
        }
    }

    private ModClient() {}
}
