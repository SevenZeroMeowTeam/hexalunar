package cn.blockforge.generated.hexalunarcalamity;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEffects;
import cn.blockforge.generated.hexalunarcalamity.registry.ModEntities;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.registry.ModTabs;
import cn.blockforge.generated.hexalunarcalamity.loot.WeaponCacheModifier;
import cn.blockforge.generated.hexalunarcalamity.net.ModNetwork;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;

@Mod(HexaLunarCalamity.MOD_ID)
public final class HexaLunarCalamity {
    public static final String MOD_ID = "hexalunar_calamity";

    public HexaLunarCalamity() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        ModItems.register(bus);
        ModEntities.register(bus);
        ModEffects.register(bus);
        ModSounds.register(bus);
        ModTabs.register(bus);
        WeaponCacheModifier.SERIALIZERS.register(bus);
        ModNetwork.init();
    }
}
