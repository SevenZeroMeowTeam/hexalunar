package cn.blockforge.generated.hexalunarcalamity.registry;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.item.AmmoBoxItem;
import cn.blockforge.generated.hexalunarcalamity.item.AntidoteItem;
import cn.blockforge.generated.hexalunarcalamity.item.CreativeAmmoBoxItem;
import cn.blockforge.generated.hexalunarcalamity.item.FlashbangItem;
import cn.blockforge.generated.hexalunarcalamity.item.FragGrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.item.PoisonBottleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoType;
import cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.CrossbowWeaponItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.RedDotSightItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.Scope4xItem;
import net.minecraft.world.item.Item;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModItems {
    public static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.Keys.ITEMS, HexaLunarCalamity.MOD_ID);

    // 三武器
    public static final RegistryObject<Item> CROSSBOW =
            ITEMS.register("crossbow", () -> new CrossbowWeaponItem(new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> COMPOUND_BOW =
            ITEMS.register("compound_bow", () -> new CompoundBowItem(new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> AKM =
            ITEMS.register("akm", () -> new AkmRifleItem(new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> AWP =
            ITEMS.register("awp", () -> new cn.blockforge.generated.hexalunarcalamity.weapon
                    .AwpRifleItem(new Item.Properties().stacksTo(1)));
    /** ★ r105 Kar98k 栓动步枪：与 AWP 同款栓动逻辑 / 共用 .338 弹，换 4 倍镜与自己的模型 */
    public static final RegistryObject<Item> KAR98K =
            ITEMS.register("kar98k", () -> new cn.blockforge.generated.hexalunarcalamity.weapon
                    .Kar98kItem(new Item.Properties().stacksTo(1)));
    /** ★ r106 莫辛-纳甘 M91/30：栓动 + 逐发压弹（5 发弹仓）+ 出厂自带 4 倍镜，用 7.62x59 弹 */
    public static final RegistryObject<Item> MOSIN_NAGANT =
            ITEMS.register("mosin_nagant", () -> new cn.blockforge.generated.hexalunarcalamity.weapon
                    .MosinRifleItem(new Item.Properties().stacksTo(1)));
    /** ★ r108 M1 加兰德：**半自动**（每扣一次扳机一发，按住不连发；枪机自动循环）+ 8 发漏夹（右手压弹）+ 机瞄，用 7.62x61 弹 */
    public static final RegistryObject<Item> M1_GARAND =
            ITEMS.register("m1_garand", () -> new cn.blockforge.generated.hexalunarcalamity.weapon
                    .M1GarandItem(new Item.Properties().stacksTo(1)));

    // 三种弹药 + 毒箭
    public static final RegistryObject<Item> CROSSBOW_BOLT =
            ITEMS.register("crossbow_bolt", () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> COMPOUND_ARROW =
            ITEMS.register("compound_arrow", () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> AMMO_762 =
            ITEMS.register("ammo_762", () -> new Item(new Item.Properties()));
    /** .338 狙击弹（AWP 专用） */
    public static final RegistryObject<Item> AMMO_338 =
            ITEMS.register("ammo_338", () -> new Item(new Item.Properties()));
    /** ★ r106 7.62x59 步枪弹（莫辛-纳甘 / Kar98k） */
    public static final RegistryObject<Item> AMMO_762_59 =
            ITEMS.register("ammo_762_59", () -> new Item(new Item.Properties()));
    /** ★ r108 7.62x61 步枪弹（M1 加兰德专用） */
    public static final RegistryObject<Item> AMMO_762_61 =
            ITEMS.register("ammo_762_61", () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> POISON_ARROW =
            ITEMS.register("poison_arrow", () -> new Item(new Item.Properties()));

    // 弹药盒
    public static final RegistryObject<Item> AMMO_BOX_BOLT =
            ITEMS.register("ammo_box_bolt", () -> new AmmoBoxItem(AmmoType.BOLT, new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> AMMO_BOX_ARROW =
            ITEMS.register("ammo_box_arrow", () -> new AmmoBoxItem(AmmoType.ARROW, new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> AMMO_BOX_RIFLE =
            ITEMS.register("ammo_box_rifle", () -> new AmmoBoxItem(AmmoType.RIFLE, new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> AMMO_BOX_SNIPER =
            ITEMS.register("ammo_box_sniper", () -> new AmmoBoxItem(AmmoType.SNIPER, new Item.Properties().stacksTo(1)));
    /** ★ r106 7.62x59 弹药盒 */
    public static final RegistryObject<Item> AMMO_BOX_762_59 =
            ITEMS.register("ammo_box_762_59", () -> new AmmoBoxItem(AmmoType.MOSIN, new Item.Properties().stacksTo(1)));
    /** ★ r108 7.62x61 弹药盒（M1 加兰德） */
    public static final RegistryObject<Item> AMMO_BOX_762_61 =
            ITEMS.register("ammo_box_762_61", () -> new AmmoBoxItem(AmmoType.GARAND, new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> CREATIVE_AMMO_BOX =
            ITEMS.register("creative_ammo_box", () -> new CreativeAmmoBoxItem(new Item.Properties().stacksTo(1)));

    // 药剂
    public static final RegistryObject<Item> ANTIDOTE =
            ITEMS.register("antidote", () -> new AntidoteItem(new Item.Properties().stacksTo(16)));
    public static final RegistryObject<Item> POISON_REAGENT =
            ITEMS.register("poison_reagent", () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> POISON_BOTTLE =
            ITEMS.register("poison_bottle", () -> new PoisonBottleItem(new Item.Properties().stacksTo(16)));

    // 投掷武器：保险销 + 压杆 + 引信
    public static final RegistryObject<Item> FRAG_GRENADE =
            ITEMS.register("frag_grenade", () -> new FragGrenadeItem(new Item.Properties()));
    public static final RegistryObject<Item> FLASHBANG =
            ITEMS.register("flashbang", () -> new FlashbangItem(new Item.Properties()));

    // 瞄具（装到 AKM 顶部导轨上：潜行 + 右键）
    public static final RegistryObject<Item> RED_DOT_SIGHT =
            ITEMS.register("red_dot_sight", () -> new RedDotSightItem(new Item.Properties()));
    public static final RegistryObject<Item> SCOPE_4X =
            ITEMS.register("scope_4x", () -> new Scope4xItem(new Item.Properties()));

    public static void register(net.minecraftforge.eventbus.api.IEventBus bus) {
        ITEMS.register(bus);
    }

    private ModItems() {}
}
