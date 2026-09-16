package cn.blockforge.generated.hexalunarcalamity.registry;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModSounds {
    public static final DeferredRegister<SoundEvent> SOUNDS =
            DeferredRegister.create(ForgeRegistries.Keys.SOUND_EVENTS, HexaLunarCalamity.MOD_ID);

    public static final RegistryObject<SoundEvent> CROSSBOW_SHOT = sound("crossbow_shot");
    public static final RegistryObject<SoundEvent> CROSSBOW_HIT = sound("crossbow_hit");
    public static final RegistryObject<SoundEvent> BOW_SHOT = sound("bow_shot");
    public static final RegistryObject<SoundEvent> AKM_SHOT = sound("akm_shot");
    public static final RegistryObject<SoundEvent> RELOAD = sound("reload");
    public static final RegistryObject<SoundEvent> AKM_RELOAD = sound("akm_reload");
    public static final RegistryObject<SoundEvent> AKM_BOLT = sound("akm_bolt");
    public static final RegistryObject<SoundEvent> EMPTY = sound("empty");
    public static final RegistryObject<SoundEvent> HIT = sound("hit");
    public static final RegistryObject<SoundEvent> KILL = sound("kill");
    public static final RegistryObject<SoundEvent> ALARM_BLOOD = sound("alarm_blood");
    public static final RegistryObject<SoundEvent> ALARM_BLUE = sound("alarm_blue");
    public static final RegistryObject<SoundEvent> ALARM_YELLOW = sound("alarm_yellow");
    public static final RegistryObject<SoundEvent> GIANT_ARROW = sound("giant_arrow");
    public static final RegistryObject<SoundEvent> TOXIC_BURST = sound("toxic_burst");
    public static final RegistryObject<SoundEvent> FUSE = sound("fuse");

    private static RegistryObject<SoundEvent> sound(String name) {
        return SOUNDS.register(name, () -> SoundEvent.createVariableRangeEvent(
                ResourceLocation.fromNamespaceAndPath(HexaLunarCalamity.MOD_ID, name)));
    }

    public static void register(net.minecraftforge.eventbus.api.IEventBus bus) {
        SOUNDS.register(bus);
    }

    private ModSounds() {}
}
