package cn.blockforge.generated.hexalunarcalamity.loot;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.minecraftforge.common.loot.IGlobalLootModifier;
import net.minecraftforge.common.loot.LootModifier;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Optional;

/**
 * 箱子战利品：按概率把模组武器塞进原版箱子，并附带一小份对应弹药。
 *
 * <p>原版战利品表不能靠数据包"追加"条目，Forge 的全局战利品修饰器（Global Loot Modifier）才是正路：
 * <ul>
 *   <li>这个类提供修饰器本体（{@code hexalunar_calamity:weapon_cache}）</li>
 *   <li>具体实例写在 {@code data/hexalunar_calamity/loot_modifiers/*.json}</li>
 *   <li>再由 {@code data/forge/loot_modifiers/global_loot_modifiers.json} 列出启用哪些实例</li>
 * </ul>
 *
 * <p>战利品表过滤直接比较 {@link LootContext#getQueriedLootTableId()}，所以一份 JSON 就能覆盖一整组箱子
 * （不必给每个箱子各写一个 {@code forge:loot_table_id} 条件）。
 */
public class WeaponCacheModifier extends LootModifier {

    public static final DeferredRegister<Codec<? extends IGlobalLootModifier>> SERIALIZERS =
            DeferredRegister.create(ForgeRegistries.Keys.GLOBAL_LOOT_MODIFIER_SERIALIZERS,
                    HexaLunarCalamity.MOD_ID);

    public static final RegistryObject<Codec<? extends IGlobalLootModifier>> WEAPON_CACHE =
            SERIALIZERS.register("weapon_cache", () -> WeaponCacheModifier.CODEC);

    /** 一条战利品：武器 + 抽中权重 + 顺手给的弹药 */
    public record Entry(ResourceLocation weapon, int weight,
                        Optional<ResourceLocation> ammo, int ammoCount) {
        public static final Codec<Entry> CODEC = RecordCodecBuilder.create(inst -> inst.group(
                ResourceLocation.CODEC.fieldOf("weapon").forGetter(Entry::weapon),
                Codec.INT.optionalFieldOf("weight", 1).forGetter(Entry::weight),
                ResourceLocation.CODEC.optionalFieldOf("ammo").forGetter(Entry::ammo),
                Codec.INT.optionalFieldOf("ammo_count", 0).forGetter(Entry::ammoCount)
        ).apply(inst, Entry::new));
    }

    /** 一份修饰器配置：概率 + 作用范围（战利品表）+ 可抽的武器 */
    public record Settings(double chance, List<ResourceLocation> tables, List<Entry> entries) {
        public static final Codec<Settings> CODEC = RecordCodecBuilder.create(inst -> inst.group(
                Codec.DOUBLE.optionalFieldOf("chance", 0.08D).forGetter(Settings::chance),
                ResourceLocation.CODEC.listOf().fieldOf("tables").forGetter(Settings::tables),
                Entry.CODEC.listOf().fieldOf("entries").forGetter(Settings::entries)
        ).apply(inst, Settings::new));
    }

    public static final Codec<WeaponCacheModifier> CODEC = RecordCodecBuilder.create(inst -> inst.group(
            IGlobalLootModifier.LOOT_CONDITIONS_CODEC.fieldOf("conditions").forGetter(m -> m.conditions),
            Settings.CODEC.fieldOf("settings").forGetter(m -> m.settings)
    ).apply(inst, WeaponCacheModifier::new));

    private final Settings settings;

    public WeaponCacheModifier(LootItemCondition[] conditions, Settings settings) {
        super(conditions);
        this.settings = settings;
    }

    @Override
    public Codec<? extends IGlobalLootModifier> codec() {
        return CODEC;
    }

    @NotNull
    @Override
    protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> generatedLoot, LootContext context) {
        if (!settings.tables().contains(context.getQueriedLootTableId())) return generatedLoot;
        RandomSource random = context.getRandom();
        if (random.nextDouble() >= settings.chance()) return generatedLoot;
        Entry entry = pick(random);
        if (entry == null) return generatedLoot;
        Item weapon = ForgeRegistries.ITEMS.getValue(entry.weapon());
        if (weapon == null) return generatedLoot;
        generatedLoot.add(new ItemStack(weapon));
        if (entry.ammoCount() > 0 && entry.ammo().isPresent()) {
            Item ammo = ForgeRegistries.ITEMS.getValue(entry.ammo().get());
            if (ammo != null) generatedLoot.add(new ItemStack(ammo, entry.ammoCount()));
        }
        return generatedLoot;
    }

    /** 按 weight 抽一条；权重全为 0 时返回 null */
    @Nullable
    private Entry pick(RandomSource random) {
        int total = 0;
        for (Entry entry : settings.entries()) total += Math.max(0, entry.weight());
        if (total <= 0) return null;
        int roll = random.nextInt(total);
        for (Entry entry : settings.entries()) {
            roll -= Math.max(0, entry.weight());
            if (roll < 0) return entry;
        }
        return null;
    }
}
