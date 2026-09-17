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
import java.util.List;
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
        LOGGER.info("手持动作动画已启用：包装了 {} 个武器模型", wrapped);
    }

    /** 模型路径 → 动作种类；返回 null 表示该模型不需要动（弹药、图标等） */
    private static WeaponAnim.Kind kindOfModel(String path) {
        if (path.contains("crossbow_bolt")) return null;
        if (path.startsWith("akm")) return WeaponAnim.Kind.AKM;
        if (path.startsWith("crossbow") || path.contains("crossbow_pulling")) {
            return WeaponAnim.Kind.CROSSBOW;
        }
        if (path.contains("compound_bow")) return WeaponAnim.Kind.BOW;
        if (path.startsWith("mud") || path.contains("frag_grenade")) return WeaponAnim.Kind.GRENADE;
        if (path.startsWith("mtx") || path.contains("flashbang")) return WeaponAnim.Kind.FLASH;
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
                            if (entity == null || entity.getUseItem() != stack) return 0.0F;
                            // 与原版弓一致：已蓄力 tick / 20（20 tick = 满蓄）
                            return (float) (stack.getUseDuration() - entity.getUseItemRemainingTicks()) / 20.0F;
                        });
                ItemProperties.register(weapon,
                        ResourceLocation.fromNamespaceAndPath(HexaLunarCalamity.MOD_ID, "pulling"),
                        (stack, level, entity, seed) ->
                                entity != null && entity.isUsingItem() && entity.getUseItem() == stack ? 1.0F : 0.0F);
            }
        });
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
        event.registerEntityRenderer(ModEntities.BOMBER_ZOMBIE.get(),
                ctx -> tintedZombie(ctx, 0xFFB45A, 120));
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
