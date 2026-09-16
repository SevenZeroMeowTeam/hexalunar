package cn.blockforge.generated.hexalunarcalamity.registry;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public final class ModTabs {
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, HexaLunarCalamity.MOD_ID);

    public static final RegistryObject<CreativeModeTab> MAIN = TABS.register("main",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup." + HexaLunarCalamity.MOD_ID))
                    .icon(() -> new ItemStack(ModItems.AKM.get()))
                    .displayItems((params, output) -> {
                        output.accept(new ItemStack(ModItems.CROSSBOW.get()));
                        output.accept(new ItemStack(ModItems.COMPOUND_BOW.get()));
                        output.accept(new ItemStack(ModItems.AKM.get()));
                        output.accept(new ItemStack(ModItems.CROSSBOW_BOLT.get()));
                        output.accept(new ItemStack(ModItems.COMPOUND_ARROW.get()));
                        output.accept(new ItemStack(ModItems.AMMO_762.get()));
                        output.accept(new ItemStack(ModItems.POISON_ARROW.get()));
                        output.accept(new ItemStack(ModItems.AMMO_BOX_BOLT.get()));
                        output.accept(new ItemStack(ModItems.AMMO_BOX_ARROW.get()));
                        output.accept(new ItemStack(ModItems.AMMO_BOX_RIFLE.get()));
                        output.accept(new ItemStack(ModItems.CREATIVE_AMMO_BOX.get()));
                        output.accept(new ItemStack(ModItems.ANTIDOTE.get()));
                        output.accept(new ItemStack(ModItems.POISON_REAGENT.get()));
                        output.accept(new ItemStack(ModItems.POISON_BOTTLE.get()));
                        output.accept(new ItemStack(ModItems.FRAG_GRENADE.get()));
                        output.accept(new ItemStack(ModItems.FLASHBANG.get()));
                    })
                    .build());

    public static void register(net.minecraftforge.eventbus.api.IEventBus bus) {
        TABS.register(bus);
    }

    private ModTabs() {}
}
