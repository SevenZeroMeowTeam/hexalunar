package cn.blockforge.generated.hexalunarcalamity.registry;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.effect.CorpsePoisonEffect;
import cn.blockforge.generated.hexalunarcalamity.effect.StunEffect;
import net.minecraft.world.effect.MobEffect;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModEffects {
    public static final DeferredRegister<MobEffect> EFFECTS =
            DeferredRegister.create(ForgeRegistries.Keys.MOB_EFFECTS, HexaLunarCalamity.MOD_ID);

    /** 尸毒：持续伤害 + 减速 + 饥饿消耗 */
    public static final RegistryObject<MobEffect> CORPSE_POISON =
            EFFECTS.register("corpse_poison", CorpsePoisonEffect::new);

    /** 眩晕：震爆弹命中后的短暂失能，几乎走不动、打不出手 */
    public static final RegistryObject<MobEffect> STUN =
            EFFECTS.register("stun", StunEffect::new);

    public static void register(net.minecraftforge.eventbus.api.IEventBus bus) {
        EFFECTS.register(bus);
    }

    private ModEffects() {}
}
