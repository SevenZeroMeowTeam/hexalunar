package cn.blockforge.generated.hexalunarcalamity.common;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.ArcherZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.BarrelZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.BomberZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.GiantZombie;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.RusherSkeleton;
import cn.blockforge.generated.hexalunarcalamity.entity.mob.ToxicSkeleton;
import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** 特殊感染者与骷髅变种的基础属性表 */
@Mod.EventBusSubscriber(modid = HexaLunarCalamity.MOD_ID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class CommonSetup {

    @SubscribeEvent
    public static void onAttributes(EntityAttributeCreationEvent event) {
        event.put(ModEntities.BOMBER_ZOMBIE.get(), BomberZombie.createAttributes().build());
        event.put(ModEntities.ARCHER_ZOMBIE.get(), ArcherZombie.createAttributes().build());
        event.put(ModEntities.BARREL_ZOMBIE.get(), BarrelZombie.createAttributes().build());
        event.put(ModEntities.GIANT_ZOMBIE.get(), GiantZombie.createAttributes().build());
        event.put(ModEntities.RUSHER_SKELETON.get(), RusherSkeleton.createAttributes().build());
        event.put(ModEntities.TOXIC_SKELETON.get(), ToxicSkeleton.createAttributes().build());
    }

    private CommonSetup() {}
}
