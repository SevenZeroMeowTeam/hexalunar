package cn.blockforge.generated.hexalunarcalamity.registry;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.entity.BoltEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.BulletEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.GiantArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.GrenadeEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.PiercingArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.PoisonBottleEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.ToxicArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.ArcherZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.BarrelZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.BomberZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.GiantZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.RusherSkeleton;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.ToxicSkeleton;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModEntities {
    public static final DeferredRegister<EntityType<?>> ENTITIES =
            DeferredRegister.create(ForgeRegistries.Keys.ENTITY_TYPES, HexaLunarCalamity.MOD_ID);

    // 投射物
    public static final RegistryObject<EntityType<BoltEntity>> BOLT = ENTITIES.register("crossbow_bolt_proj",
            () -> EntityType.Builder.<BoltEntity>of(BoltEntity::new, MobCategory.MISC).sized(0.2F, 0.2F)
                    .clientTrackingRange(4).updateInterval(20).build("crossbow_bolt_proj"));
    public static final RegistryObject<EntityType<PiercingArrowEntity>> COMPOUND_ARROW = ENTITIES.register("compound_arrow_proj",
            () -> EntityType.Builder.<PiercingArrowEntity>of(PiercingArrowEntity::new, MobCategory.MISC).sized(0.2F, 0.2F)
                    .clientTrackingRange(4).updateInterval(20).build("compound_arrow_proj"));
    public static final RegistryObject<EntityType<ToxicArrowEntity>> TOXIC_ARROW = ENTITIES.register("toxic_arrow_proj",
            () -> EntityType.Builder.<ToxicArrowEntity>of(ToxicArrowEntity::new, MobCategory.MISC).sized(0.2F, 0.2F)
                    .clientTrackingRange(4).updateInterval(20).build("toxic_arrow_proj"));
    public static final RegistryObject<EntityType<BulletEntity>> BULLET = ENTITIES.register("bullet_762",
            () -> EntityType.Builder.<BulletEntity>of(BulletEntity::new, MobCategory.MISC).sized(0.1F, 0.1F)
                    .clientTrackingRange(4).updateInterval(20).build("bullet_762"));
    public static final RegistryObject<EntityType<GiantArrowEntity>> GIANT_ARROW = ENTITIES.register("giant_arrow",
            () -> EntityType.Builder.<GiantArrowEntity>of(GiantArrowEntity::new, MobCategory.MISC).sized(1.2F, 1.2F)
                    .clientTrackingRange(8).updateInterval(3).build("giant_arrow"));
    public static final RegistryObject<EntityType<PoisonBottleEntity>> POISON_BOTTLE = ENTITIES.register("poison_bottle_proj",
            () -> EntityType.Builder.<PoisonBottleEntity>of(PoisonBottleEntity::new, MobCategory.MISC).sized(0.25F, 0.25F)
                    .clientTrackingRange(4).updateInterval(10).build("poison_bottle_proj"));

    public static final RegistryObject<EntityType<GrenadeEntity>> GRENADE = ENTITIES.register("grenade_proj",
            () -> EntityType.Builder.<GrenadeEntity>of(GrenadeEntity::new, MobCategory.MISC).sized(0.25F, 0.25F)
                    .clientTrackingRange(4).updateInterval(3).build("grenade_proj"));

    // 特殊感染者
    public static final RegistryObject<EntityType<BomberZombie>> BOMBER_ZOMBIE = ENTITIES.register("bomber_zombie",
            () -> EntityType.Builder.<BomberZombie>of(BomberZombie::new, MobCategory.MONSTER).sized(0.6F, 1.95F)
                    .build("bomber_zombie"));
    public static final RegistryObject<EntityType<ArcherZombie>> ARCHER_ZOMBIE = ENTITIES.register("archer_zombie",
            () -> EntityType.Builder.<ArcherZombie>of(ArcherZombie::new, MobCategory.MONSTER).sized(0.6F, 1.95F)
                    .build("archer_zombie"));
    public static final RegistryObject<EntityType<BarrelZombie>> BARREL_ZOMBIE = ENTITIES.register("barrel_zombie",
            () -> EntityType.Builder.<BarrelZombie>of(BarrelZombie::new, MobCategory.MONSTER).sized(0.75F, 2.4F)
                    .build("barrel_zombie"));
    public static final RegistryObject<EntityType<GiantZombie>> GIANT_ZOMBIE = ENTITIES.register("giant_zombie",
            () -> EntityType.Builder.<GiantZombie>of(GiantZombie::new, MobCategory.MONSTER).sized(1.14F, 3.7F)
                    .build("giant_zombie"));

    // 骷髅变种
    public static final RegistryObject<EntityType<RusherSkeleton>> RUSHER_SKELETON = ENTITIES.register("rusher_skeleton",
            () -> EntityType.Builder.<RusherSkeleton>of(RusherSkeleton::new, MobCategory.MONSTER).sized(0.6F, 1.99F)
                    .build("rusher_skeleton"));
    public static final RegistryObject<EntityType<ToxicSkeleton>> TOXIC_SKELETON = ENTITIES.register("toxic_skeleton",
            () -> EntityType.Builder.<ToxicSkeleton>of(ToxicSkeleton::new, MobCategory.MONSTER).sized(0.6F, 1.99F)
                    .build("toxic_skeleton"));

    public static void register(net.minecraftforge.eventbus.api.IEventBus bus) {
        ENTITIES.register(bus);
    }

    private ModEntities() {}
}
