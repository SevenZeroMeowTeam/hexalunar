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

    /**
     * ★★ r95：客户端「构造期引导」标志 —— 只有它为 true 时才允许创建自定义 {@code ArmPose} 常量。
     *
     * <p>为什么需要这个开关：javac 给 {@code switch (枚举)} 生成的 {@code $SwitchMap} 表是按
     * **建表那一刻** {@code values().length} 定长的。原版 {@code HumanoidModel$1} 那张表通常在
     * 「世界里第一只人形生物被渲染」时就建好了（我们模组还加了僵尸，必然很早）——
     * 那时候我们的第 11 个常量还不存在，表长 10；等我们**懒加载**创建出 ordinal = 10 的常量后，
     * `switch` 就会用索引 10 去读长度为 10 的表 ⇒
     * <b>{@code ArrayIndexOutOfBoundsException: Index 10 out of bounds for length 10}</b>
     * ⇒ 整个游戏 FATAL（用户日志里那条崩溃）。
     *
     * <p>所以自定义姿势必须在**任何渲染之前**（模组构造期）就建好；{@link #clientBootstrapping}
     * 就是「现在处于这个窗口内」的标记，{@code WeaponArmPose} 的静态初始化会读它：
     * 窗口内 → 建自定义姿势；窗口外（被懒加载了）→ 直接退回原版姿势，宁可姿势朴素也不崩游戏。
     */
    public static boolean clientBootstrapping = false;

    public HexaLunarCalamity() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        ModItems.register(bus);
        ModEntities.register(bus);
        ModEffects.register(bus);
        ModSounds.register(bus);
        ModTabs.register(bus);
        WeaponCacheModifier.SERIALIZERS.register(bus);
        ModNetwork.init();

        // ★ r95：客户端要在**构造期**把自定义 ArmPose 建出来（见 clientBootstrapping 的说明）。
        //   用 `FMLEnvironment.dist.isClient()` 分支 + 直接调用：常量池里的 WeaponArmPose 是
        //   惰性解析的，专用服务器不会走到这一句、也就不会去加载客户端类（本仓库其它地方同一写法）。
        if (net.minecraftforge.fml.loading.FMLEnvironment.dist.isClient()) {
            clientBootstrapping = true;
            try {
                cn.blockforge.generated.hexalunarcalamity.client.WeaponArmPose.initArmPoses();
            } finally {
                clientBootstrapping = false;
            }
        }
    }
}
