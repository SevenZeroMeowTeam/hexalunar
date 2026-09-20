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

/** 实体渲染器注册：投射物与六只特殊感染者 */
@Mod.EventBusSubscriber(modid = HexaLunarCalamity.MOD_ID, value = Dist.CLIENT, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class ModClient {

    /**
     * 烘焙阶段收尾：只做十字弩分件的抓取（见 {@link CrossbowPartModels}）。
     *
     * <p>★ r110：这里原来还挂着一层 {@link AnimatedWeaponModel} 的 display 包装，用来给
     * OBJ 枪模套「会动的一层」。但 AKM / AWP / Kar98k / 莫辛 / M1 加兰德 / 十字弩 / 复合弓 /
     * 手雷后来**全部改成了 GeckoLib 骨骼渲染**，认领函数 {@code kindOfModel} 的每一个分支
     * 都返回 null —— 包装循环一次都没进过，日志却一直在报「包装了 0 个武器模型」，
     * 把人往「这里坏了」的方向带。既然没有任何模型会被认领，死代码直接删掉；
     * item 模型现在只负责背包图标与手持兜底，动作全部由骨骼动画驱动。
     */
    @SubscribeEvent
    public static void onModifyBakingResult(ModelEvent.ModifyBakingResult event) {
        // 十字弩的弩箭 / 左手分件（上弦动画，见 CrossbowPartAnim）
        CrossbowPartModels.capture(event.getModels());
    }

    /** 登记不会被任何物品引用的分件模型，否则烘焙阶段不会加载它们 */
    @SubscribeEvent
    public static void onRegisterAdditionalModels(ModelEvent.RegisterAdditional event) {
        CrossbowPartModels.registerAdditional(event);
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
     * ★ Q 弹版：注册 Q 版怪物的模型层。
     *
     * <p>{@code q_chibi_zombie} = 僵尸系（自爆/弓手/桶/巨尸）用的 chibi 几何；
     * {@code q_chibi_skeleton} = 骷髅系复用**同一套 chibi 几何**，只是换骨头皮肤
     * （行为由原版 {@code SkeletonModel} 提供 ⇒ 拉弓瞄准姿势不用自己写）。
     *
     * <p>普通版也照常注册（只是没人用）—— 注册一个模型层没有任何副作用，
     * 而这样代码里就不用为「要不要注册」再分一次支。
     */
    @SubscribeEvent
    public static void onRegisterLayerDefinitions(
            net.minecraftforge.client.event.EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(QChibiZombieModel.LAYER, QChibiZombieModel::createBodyLayer);
        event.registerLayerDefinition(QChibiZombieModel.SKELETON_LAYER, QChibiZombieModel::createBodyLayer);
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
        // ★ Q 弹版（-Pqmode=true）：**全部 6 种特殊感染者**都换成「大头矮胖 + 果冻晃动」的 Q 版；
        //   染色/体型沿用原来的配置（弓手 0x59C46B、桶尸 0x6E6E78、巨尸 1.9 倍、骷髅两种染色）。
        //   普通版保持原样（Q_MODE 是编译期常量，普通版这整段分支会被 javac 折掉）
        if (cn.blockforge.generated.hexalunarcalamity.BuildInfo.Q_MODE) {
            event.registerEntityRenderer(ModEntities.BOMBER_ZOMBIE.get(),
                    ctx -> new QChibiZombieRenderer<>(ctx));
            event.registerEntityRenderer(ModEntities.ARCHER_ZOMBIE.get(),
                    ctx -> new QChibiZombieRenderer<>(ctx, QChibiZombieRenderer.ZOMBIE_TEXTURE,
                            0x59C46B, 96, 1.0F));
            event.registerEntityRenderer(ModEntities.BARREL_ZOMBIE.get(),
                    ctx -> new QChibiZombieRenderer<>(ctx, QChibiZombieRenderer.ZOMBIE_TEXTURE,
                            0x6E6E78, 110, 1.0F));
            event.registerEntityRenderer(ModEntities.GIANT_ZOMBIE.get(),
                    ctx -> new QChibiZombieRenderer<>(ctx, QChibiZombieRenderer.ZOMBIE_TEXTURE,
                            0, 0, 1.9F));            // 巨尸：无标识层，只放大 1.9 倍
            event.registerEntityRenderer(ModEntities.RUSHER_SKELETON.get(),
                    ctx -> new QChibiSkeletonRenderer(ctx, QChibiSkeletonRenderer.SKELETON_TEXTURE,
                            0x7FB6FF, 110, 1.0F));
            event.registerEntityRenderer(ModEntities.TOXIC_SKELETON.get(),
                    ctx -> new QChibiSkeletonRenderer(ctx, QChibiSkeletonRenderer.SKELETON_TEXTURE,
                            0x8FE04A, 130, 1.0F));
        } else {
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
