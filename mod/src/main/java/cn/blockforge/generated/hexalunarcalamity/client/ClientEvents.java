package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import cn.blockforge.generated.hexalunarcalamity.moon.MoonPhase;
import cn.blockforge.generated.hexalunarcalamity.registry.ModEffects;
import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoType;
import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoUtil;
import cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponAmmo;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ComputeFovModifierEvent;
import net.minecraftforge.client.event.RenderGuiEvent;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** 客户端月相视觉：雾色、天空着色、尸潮 HUD、命中标记、环境尘埃 */
@Mod.EventBusSubscriber(modid = HexaLunarCalamity.MOD_ID, value = Dist.CLIENT)
public final class ClientEvents {

    /** 月相雾色 */
    @SubscribeEvent
    public static void onFogColor(ViewportEvent.ComputeFogColor event) {
        MoonPhase phase = activePhase();
        if (phase == null) return;
        event.setRed(((phase.fogColor >> 16) & 0xFF) / 255F);
        event.setGreen(((phase.fogColor >> 8) & 0xFF) / 255F);
        event.setBlue((phase.fogColor & 0xFF) / 255F);
    }

    /**
     * 右键举枪时的世界变焦：照 TaCZ（永恒枪械工坊）的手感数值来。
     *
     * <p>★ r84 起可以给真变焦了：枪模那一遍有**自己的投影**（{@link GunPose#MODEL_FOV_AIM}，
     * TaCZ 的 {@code zoom_model_fov = 45}），世界缩几倍枪本体都是那个大小（见 {@link #onRenderHand}）。
     * 之前只敢给 0.72，是因为那时枪模跟世界共用一个投影，强变焦会把枪一起放大。
     */
    /** TaCZ 的 {@code iron_zoom = 1.33}：机瞄 / 红点举枪 */
    private static final float IRON_ZOOM = 1.33F;
    /** 4 倍镜 */
    private static final float SCOPE_4X_ZOOM = 4.0F;
    /** AWP 的 8 倍镜 */
    private static final float SCOPE_8X_ZOOM = 4.0F;   // r103: 4x (was 8x)

    /** 右键持枪瞄准时收紧视野：十字弩 4 倍 / AKM 4 倍镜 / AWP 8 倍镜 / 机瞄 1.33 倍 */
    @SubscribeEvent
    public static void onFovModifier(ComputeFovModifierEvent event) {
        Player player = event.getPlayer();
        if (player == null) return;
        // 眩晕：视野缓慢呼吸，配合镜头倾斜制造天旋地转感
        if (player.hasEffect(ModEffects.STUN.get())) {
            float amp = stunStrength(player);
            event.setNewFovModifier(event.getNewFovModifier()
                    * (1.0F + 0.055F * amp * Mth.sin(player.tickCount * 0.13F)));
        }
        if (!player.isUsingItem()) return;
        if (AmmoUtil.weaponAmmoType(player.getUseItem()) == null) return;
        if (scoping(player)) {
            net.minecraft.world.item.Item using = player.getUseItem().getItem();
            // 十字弩：整屏镜筒遮罩（枪与手都藏掉）
            if (using instanceof cn.blockforge.generated
                    .hexalunarcalamity.weapon.CrossbowWeaponItem) {
                event.setNewFovModifier(1.0F / cn.blockforge.generated
                        .hexalunarcalamity.weapon.CrossbowWeaponItem.SCOPE_ZOOM);
                return;
            }
            // AWP：8 倍镜。★ 现在是真的 8 倍 —— 枪模走自己的 45° 投影，不会被世界变焦带着放大，
            //   所以分划照旧在屏幕中心、枪本体照旧看得见（用户要的就是这个）。
            if (using instanceof cn.blockforge.generated
                    .hexalunarcalamity.weapon.AwpRifleItem) {
                event.setNewFovModifier(1.0F / SCOPE_8X_ZOOM);
                return;
            }
            // ★ r105 Kar98k：自带 **4 倍镜** —— 与 AWP 同一套整屏镜筒开镜，只是倍率低一档
            if (using instanceof cn.blockforge.generated
                    .hexalunarcalamity.weapon.Kar98kItem) {
                event.setNewFovModifier(1.0F / cn.blockforge.generated.hexalunarcalamity.weapon
                        .Kar98kItem.SCOPE_ZOOM);
                return;
            }
            // ★ r106 莫辛-纳甘：自带的 4 倍镜（TaCZ 的 scope_98k：zoom 4.25）
            if (using instanceof cn.blockforge.generated
                    .hexalunarcalamity.weapon.MosinRifleItem) {
                event.setNewFovModifier(1.0F / cn.blockforge.generated.hexalunarcalamity.weapon
                        .MosinRifleItem.SCOPE_ZOOM);
                return;
            }
            // 剩下的就是 AKM 装了 4 倍镜
            event.setNewFovModifier(1.0F / SCOPE_4X_ZOOM);
            return;
        }
        // AKM 机瞄 / 红点：TaCZ 的 iron_zoom = 1.33
        if (player.getUseItem().getItem() instanceof cn.blockforge.generated
                .hexalunarcalamity.weapon.AkmRifleItem) {
            event.setNewFovModifier(1.0F / IRON_ZOOM);
            return;
        }
        // ★ r106 莫辛机瞄：TaCZ kar98k 的 {@code iron_zoom = 2}（比 AKM 的 1.33 更“拉近”）
        if (player.getUseItem().getItem() instanceof cn.blockforge.generated
                .hexalunarcalamity.weapon.MosinRifleItem) {
            event.setNewFovModifier(1.0F / cn.blockforge.generated.hexalunarcalamity.weapon
                    .MosinRifleItem.IRON_ZOOM);
            return;
        }
        // ★ r108 M1 加兰德：只有机瞄 ⇒ 用 **TaCZ 步枪的 iron_zoom = 1.33**（同 AK47 / AKM）
        if (player.getUseItem().getItem() instanceof cn.blockforge.generated
                .hexalunarcalamity.weapon.M1GarandItem) {
            event.setNewFovModifier(1.0F / IRON_ZOOM);
            return;
        }
        boolean aiming = !(player.getUseItem().getItem() instanceof cn.blockforge.generated
                .hexalunarcalamity.weapon.CompoundBowItem)
                || cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem
                .pullProgress(player.getUseItemRemainingTicks()) > 0.9F;
        if (aiming) {
            event.setNewFovModifier(event.getNewFovModifier() * 0.72F);
        }
    }

    /**
     * 是否处于「整屏开镜」状态：十字弩开镜，或 AKM 装了 4 倍镜正在举枪。
     * （红点是"看得到枪本体"的，不算整屏开镜。）
     */
    public static boolean scoping(Player player) {
        if (player == null || !player.isUsingItem()) return false;
        ItemStack using = player.getUseItem();
        // AWP：抵肩就是开 8 倍镜（没装/拆镜的说法，望远镜就长在枪上）
        if (using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AwpRifleItem) {
            return true;
        }
        // ★ r105 Kar98k：同样自带镜筒，抵肩即开 4 倍镜（复用 AWP 那套整屏镜筒遮罩）
        if (using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .Kar98kItem) {
            return true;
        }
        // ★ r106 莫辛-纳甘：**装了 4 倍镜**才是整屏镜筒（拆了镜子就是机瞄，看得见枪）
        if (using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .MosinRifleItem) {
            return cn.blockforge.generated.hexalunarcalamity.weapon.MosinRifleItem.sight(using)
                    == cn.blockforge.generated.hexalunarcalamity.weapon.Sights.SCOPE;
        }
        if (using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .CrossbowWeaponItem) {
            return cn.blockforge.generated.hexalunarcalamity.weapon
                    .CrossbowWeaponItem.isScoping(player);
        }
        return using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AkmRifleItem
                && cn.blockforge.generated.hexalunarcalamity.weapon.Sights.sight(using)
                == cn.blockforge.generated.hexalunarcalamity.weapon.Sights.SCOPE;
    }

    /**
     * ★★ r91：需要「整屏镜筒遮罩」的开镜状态 —— **十字弩 + AWP 8 倍镜**。
     *
     * <p>用户明确要求：<b>AWP 的开镜就用十字弩那一套右键瞄准实现</b>（整屏圆形镜筒：
     * {@link #onRenderHand} 把枪与手臂一起藏掉，像原版望远镜那样，镜筒外近黑遮罩 +
     * 镜内分划 + 蓝色镜圈）—— 而不是「枪还留在屏幕上、只叠一层分划」。
     *
     * <p>AKM 的 4 倍镜仍然走「看得见枪」的那一支（{@link #drawScopeReticle}），
     * 因为机瞄 / 红点 / 4 倍镜的构图在 r88 已经按 TaCZ 那套定好了。
     */
    /**
     * ★★ r91/r99：需要「整屏镜筒遮罩」的开镜状态 —— **十字弩 4 倍镜 + AWP 8 倍镜 + AKM 4 倍镜**。
     *
     * <p>★ r99（用户要求）：AKM 装上 4 倍镜后右键开镜，也要**把枪和手一起藏掉**，
     * 画面上只留镜筒 + 分划 + 蓝色镜圈（就是 AWP / 十字弩那套）。判定直接用
     * {@link #scoping}：它已经覆盖 AWP（抵肩即开镜）、十字弩（上弦后开镜）、
     * 以及 **AKM 且瞄具 == 4 倍镜**；机瞄 / 红点仍然保持「看得见枪」——
     * 那是用户先前明确要的构图（图 1）。
     */
    private static boolean maskScoping(Player player) {
        return scoping(player);
    }

    /**
     * ★ 不再叠「镜片炫光」贴图：那张图里有大面积柔光/斜光条，拉满整屏后会形成一层
     * 白雾（用户两次反馈「白色遮布挡住倍镜看不清生物」）。现在整个开镜画面全部
     * 程序化画：镜筒外近黑遮罩 + 镜缘暗角 + 对称分划，镜内不叠任何白光。
     */

    /**
     * 左上角天数显示：
     *
     * <p>天数取世界时间（第 1 天起，和月相无关）；当前有月相时第二行用该月相的尘色写月相名，
     * 顶边也按月相上色。僵尸进化概率就是按这个天数算的，所以两件事口径一致。
     */
    @SubscribeEvent
    public static void onDayHud(net.minecraftforge.client.event.RenderGuiEvent.Post event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null || mc.options.hideGui || mc.screen != null
                || mc.player.isSpectator()) {
            return;
        }
        var gg = event.getGuiGraphics();
        var font = mc.font;
        long day = mc.level.getDayTime() / 24000L + 1L;
        MoonPhase phase = ClientMoonState.phase();
        String title = "第 " + day + " 天";
        String sub = phase == null ? null : phase.zhName;
        // 第三行：当前月相的核心效果（蓝月=玩家幸运 / 黄月=作物加速 / 血月=进化+不眠）
        // 没月相时退回「时间越久进化越多」的数值（与 ZombieEvolution 同一取数口径）
        int evoPct = Math.round(cn.blockforge.generated.hexalunarcalamity.moon.ZombieEvolution
                .spawnChance(day) * 100.0F);
        int tiers = cn.blockforge.generated.hexalunarcalamity.moon.ZombieEvolution
                .unlockedTiers(day);
        String evoLine;
        if (phase == null) {
            evoLine = "僵尸进化 " + evoPct + "%  档 " + tiers + "/4";
        } else if (phase.isBlue()) {
            evoLine = "幸运 " + (phase.luckAmplifier() + 1) + " 级  直到天亮";
        } else if (phase.isYellow()) {
            evoLine = "作物加速生长  直到天亮";
        } else {
            evoLine = "僵尸进化 " + evoPct + "%  档 " + tiers + "/4  ·  夜不能寐";
        }
        int accent = phase == null ? 0xFF7C8894 : (0xFF000000 | (phase.dustColor & 0xFFFFFF));
        int w = Math.max(font.width(title),
                Math.max(sub == null ? 0 : font.width(sub), font.width(evoLine))) + 14;
        int h = 20 + (sub == null ? 0 : 12) + 12;
        gg.fill(3, 3, 3 + w, 3 + h, 0x8C0B0B12);
        gg.fill(3, 3, 3 + w, 4, accent);
        int y = 8;
        gg.drawString(font, title, 10, y, 0xFFF1F1F5, true);
        if (sub != null) {
            y += 12;
            gg.drawString(font, sub, 10, y, accent, true);
        }
        y += 12;
        gg.drawString(font, evoLine, 10, y, 0xFFC8CDD6, true);
    }

    /**
     * 开镜时不再叠炫光。旧版这里会整屏 blit 一张「镜片炫光」贴图（柔光 + 斜光条），
     * 拉满整屏后就是一层白雾 —— 用户两次反馈「白色遮布挡住倍镜」。视口效果现在全部
     * 由 {@link #drawScopeOverlay} 程序化画（镜内不叠任何白光）。
     */
    @SubscribeEvent
    public static void onScopeGlare(net.minecraftforge.client.event.RenderGuiEvent.Post event) {
        // 保留钩子：以后想做「只在镜缘一小块」的淡光斑可以加在这里，但不要再整屏叠白。
    }

    /**
     * 复合弓：第一人称蓄力时随拉弦成数渐近视野，拉满约收 22%。
     * 拉到 0.9 以上时上面那条 0.72 就不再叠（弓不走武器瞄准那一支）。
     */
    @SubscribeEvent
    public static void onBowFov(ComputeFovModifierEvent event) {
        Player player = event.getPlayer();
        if (player == null || !player.isUsingItem()) return;
        ItemStack using = player.getUseItem();
        if (!(using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem)) {
            return;
        }
        float pull = cn.blockforge.generated.hexalunarcalamity.weapon.CompoundBowItem
                .pullProgress(player.getUseItemRemainingTicks());
        if (pull <= 0.02F) return;
        event.setNewFovModifier(event.getNewFovModifier() * (1.0F - 0.22F * pull));
    }

    /** 眩晕：让镜头绕视线轻轻打横，越接近爆炸中心晃得越厉害 */
    @SubscribeEvent
    public static void onCameraAngles(ViewportEvent.ComputeCameraAngles event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) return;
        applyBowCamera(event);
        applyAkmCamera(event);
        applyRecoilKick(event);
        float amp = stunStrength(mc.player);
        if (amp <= 0.0F) return;
        float t = mc.level.getGameTime() + (float) event.getPartialTick();
        event.setRoll(event.getRoll() + 3.2F * amp * Mth.sin(t * 0.09F)
                + 1.1F * amp * Mth.sin(t * 0.27F));
        event.setPitch(event.getPitch() + 0.9F * amp * Mth.sin(t * 0.15F + 1.7F));
    }

    /**
     * 复合弓的 camera 骨骼 → 第一人称镜头。
     *
     * <p>照 SuperbWarfare BOCEK 的做法：模型里放一根没有方块的 camera 空骨骼，
     * 拉弦/放箭动画去旋转它，这里每帧把它的角度叠到视角上（GeckoLib 骨骼角度是弧度）。
     */
    private static void applyBowCamera(ViewportEvent.ComputeCameraAngles event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;
        if (!(mc.player.getMainHandItem().getItem() instanceof cn.blockforge.generated
                .hexalunarcalamity.weapon.CompoundBowItem)) {
            return;
        }
        software.bernie.geckolib.cache.object.GeoBone bone =
                BowGeoRenderer.get().getGeoModel().getBone("camera").orElse(null);
        if (bone == null) return;
        event.setPitch(event.getPitch() - bone.getRotX() * Mth.RAD_TO_DEG);
        event.setYaw(event.getYaw() + bone.getRotY() * Mth.RAD_TO_DEG);
        event.setRoll(event.getRoll() + bone.getRotZ() * Mth.RAD_TO_DEG);
    }

    /**
     * ★ r84：**后坐力只推视角** —— 枪与双手不再跟着前后上下动（用户要求「后坐力仅视角晃动」）。
     *
     * <p>冲量来自 {@link WeaponAnim} 的 {@code recoil / recoilYaw}（开火那一下最大，之后每 tick ×0.55
     * 衰减 ⇒ 天生平滑），这里每帧叠到镜头 pitch / yaw 上：枪口上跳 + 随机偏航；举枪（aim）时收掉一半。
     */
    private static void applyRecoilKick(ViewportEvent.ComputeCameraAngles event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;
        ItemStack held = mc.player.getMainHandItem();
        WeaponAnim.State st;
        if (held.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AkmRifleItem) {
            st = WeaponAnim.of(WeaponAnim.Kind.AKM);
        } else if (held.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AwpRifleItem) {
            st = WeaponAnim.of(WeaponAnim.Kind.AWP);
        } else if (held.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .Kar98kItem) {
            st = WeaponAnim.of(WeaponAnim.Kind.KAR98K);       // ★ r105
        } else if (held.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .MosinRifleItem) {
            st = WeaponAnim.of(WeaponAnim.Kind.MOSIN);        // ★ r106
        } else if (held.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .M1GarandItem) {
            st = WeaponAnim.of(WeaponAnim.Kind.M1_GARAND);    // ★ r108
        } else {
            return;
        }
        if (st.recoil < 0.002F && Math.abs(st.recoilYaw) < 0.002F) return;
        float scale = 1.0F - 0.5F * Mth.clamp(st.aim, 0.0F, 1.0F);
        event.setPitch(event.getPitch() - st.recoil * 2.2F * scale);
        event.setYaw(event.getYaw() + st.recoilYaw * 0.9F * scale);
    }

    /**
     * AKM 的 camera 骨骼 → 第一人称镜头（与复合弓同一套做法）。
     *
     * <p>开火/拉栓/换弹/拨保险动画会轻推这根空骨骼，这里每帧叠到视角上，
     * 于是有后座上跳、拉栓顿挫与换弹低头（骨骼角度是弧度）。
     */
    private static void applyAkmCamera(ViewportEvent.ComputeCameraAngles event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;
        if (!(mc.player.getMainHandItem().getItem() instanceof cn.blockforge.generated
                .hexalunarcalamity.weapon.AkmRifleItem)) {
            return;
        }
        software.bernie.geckolib.cache.object.GeoBone bone =
                AkmGeoRenderer.get().getGeoModel().getBone("camera").orElse(null);
        if (bone == null) return;
        event.setPitch(event.getPitch() - bone.getRotX() * Mth.RAD_TO_DEG);
        event.setYaw(event.getYaw() + bone.getRotY() * Mth.RAD_TO_DEG);
        event.setRoll(event.getRoll() + bone.getRotZ() * Mth.RAD_TO_DEG);
    }

    /** 武器动画的客户端状态推进：复合弓（拉弦）、手雷、十字弩、AKM */
    @SubscribeEvent
    public static void onBowTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        BowAnimState.tick();
        GrenadeAnimState.tick();
        CrossbowAnimState.tick();
        AkmAnimState.tick();
    }

    /** 眩晕强度 0..1：剩余时间越短越轻，最后一秒平滑收尾 */
    private static float stunStrength(Player player) {
        var effect = player.getEffect(ModEffects.STUN.get());
        if (effect == null) return 0.0F;
        int left = effect.getDuration();
        float fade = left > 20 ? 1.0F : Math.max(0.0F, left / 20.0F);
        return fade * (effect.getAmplifier() > 0 ? 1.0F : 0.65F);
    }

    /**
     * 第一人称：**枪模独立投影** + 补画双臂。
     *
     * <p>★ TaCZ 那套（r84）：在 {@code RenderHandEvent} 里把投影换成枪模专用的
     * {@link GunPose#modelFov}（举枪 45°，就是 TaCZ 的 {@code zoom_model_fov}；腰射 70° = 原版那遍）。
     * <b>不 cancel</b> —— 原版接着用这个投影把枪画出来，所以枪的位置/动画一行都不用自己重写；
     * 相机之后世界变焦到 4 倍 / 8 倍也不影响枪本体大小，这就是"AWP 开 8 倍镜还看得见枪与镜框"的关键。
     * 投影必须在**副手**渲染前还原（副手是普通物品，用回原版投影），见 {@link #restoreHandProjection()}。
     *
     * <p>补画的双臂在同一次里用**同一个投影**画（{@link WeaponArms}），否则手会与枪错位。
     * 十字弩的整屏开镜会把手与武器一起藏掉（像原版望远镜那样）。
     *
     * <p>主手拿 AKM / AWP / 十字弩 / 手雷时把玩家自己的**两条手臂**补上：原版对非空物品只画物品
     * 不画手；左手还会按换弹进度做事：AKM 托护木 / 抽弹匣 / 拉机柄，AWP 托护木 / 拆装弹匣，
     * 十字弩拉弦 / 递箭上槽。
     */
    /**
     * ★★ r96：最高优先级，**只做一件事** —— 记下还没被任何人动过的这一层 pose。
     *
     * <p>为什么要在别人之前：{@code RenderHandEvent} 上还挂着 TaCZ / SimpleBedrockModel 的
     * {@code FirstPersonRenderHandler}，它给自家枪做手持渲染时会直接改事件里的 {@code PoseStack}；
     * 拿我们的枪时它没画东西，但改动可能留在栈上，于是枪与我们的手臂一起被带偏
     * （用户反馈的「枪飘在手右上方、和手臂分离」）。这份干净矩阵会在
     * {@link WeaponArms#restoreCleanPose} 里被覆盖回去，枪和手共用同一份基准。
     */
    @SubscribeEvent(priority = net.minecraftforge.eventbus.api.EventPriority.HIGHEST)
    public static void onRenderHandEarly(net.minecraftforge.client.event.RenderHandEvent event) {
        if (event.getHand() == net.minecraft.world.InteractionHand.MAIN_HAND) {
            WeaponArms.captureCleanPose(event.getPoseStack());
        }
    }

    @SubscribeEvent
    public static void onRenderHand(net.minecraftforge.client.event.RenderHandEvent event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;
        if (event.getHand() != net.minecraft.world.InteractionHand.MAIN_HAND) {
            // 副手：先把枪模投影还原，副手照旧用原版投影
            restoreHandProjection();
            return;
        }
        if (maskScoping(mc.player)) {
            event.setCanceled(true);
            return;
        }
        net.minecraft.world.item.Item item = event.getItemStack().getItem();
        // ★ 枪模投影（TaCZ 的 zoom_model_fov）：举枪 45°、腰射 70°（与原版一致）
        WeaponAnim.Kind gun = WeaponHandGrip.gunKind(event.getItemStack());
        if (gun != null) {
            handProjection = com.mojang.blaze3d.systems.RenderSystem.getProjectionMatrix();
            com.mojang.blaze3d.systems.RenderSystem.setProjectionMatrix(
                    mc.gameRenderer.getProjectionMatrix(
                            // ★ r94/r105：各枪自己的 zoom_model_fov（AK47=45 / AWP=25 / Kar98k=40）
                            cn.blockforge.generated.hexalunarcalamity.weapon.GunPose
                                    .modelFovForGun(modelAimFov(gun), WeaponAnim.of(gun).aim)),
                    com.mojang.blaze3d.vertex.VertexSorting.DISTANCE_TO_ORIGIN);
        }
        if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem) {
            WeaponArms.renderAkm(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        } else if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .CrossbowWeaponItem) {
            WeaponArms.renderCrossbow(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        } else if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AwpRifleItem) {
            // AWP：右手握把 + 左手托枪管（换弹时去抓弹匣）
            WeaponArms.renderAwp(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        } else if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .Kar98kItem) {
            // ★ r105 Kar98k：右手握把 + 拉栓时抓下弯拉机柄；左手托护木（换弹时压桥夹）
            WeaponArms.renderKar98k(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        } else if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .MosinRifleItem) {
            // ★ r106 莫辛：右手握碗部 + 拉栓时抓拉机柄（抽壳抛壳）；左手托前托（装填时上机匣逐发压弹）
            WeaponArms.renderMosin(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        } else if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .M1GarandItem) {
            // ★ r108 M1：右手握托颈（射击时不动）+ 换弹时压漏夹 / 抓拉机柄复进；左手全程托前托
            WeaponArms.renderM1Garand(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        } else if (item instanceof cn.blockforge.generated.hexalunarcalamity.item
                .GrenadeItem) {
            // 手雷 / 震爆弹：右手握雷；左手只在拔销 / 插销时伸进来抓拉环
            WeaponArms.renderGrenade(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        }
    }

    /** 被我们换成「枪模投影」之前的那块投影（副手渲染前还原，见 {@link #onRenderHand}） */
    private static org.joml.Matrix4f handProjection;

    /**
     * 各枪**举枪时**的枪模投影 FOV（TaCZ 的 {@code zoom_model_fov}）：
     * AKM / 十字弩 45、AWP 25、★ r105 Kar98k 40（4 倍镜）。
     * 腰射那一档由 {@code GunPose.MODEL_FOV_HIP} 统一给（76°）。
     */
    private static float modelAimFov(WeaponAnim.Kind gun) {
        return switch (gun) {
            case AWP -> cn.blockforge.generated.hexalunarcalamity.weapon.GunPose.MODEL_FOV_AIM_AWP;
            case KAR98K -> cn.blockforge.generated.hexalunarcalamity.weapon.GunPose
                    .MODEL_FOV_AIM_KAR98K;
            case MOSIN -> cn.blockforge.generated.hexalunarcalamity.weapon.GunPose
                    .MODEL_FOV_AIM_MOSIN;                       // ★ r106（TaCZ kar98k 的 25°）
            case M1_GARAND -> cn.blockforge.generated.hexalunarcalamity.weapon.GunPose
                    .MODEL_FOV_AIM_M1;                          // ★ r108（TaCZ 步枪 AK47 的 45°）
            default -> cn.blockforge.generated.hexalunarcalamity.weapon.GunPose.MODEL_FOV_AIM;
        };
    }

    private static void restoreHandProjection() {
        if (handProjection == null) return;
        com.mojang.blaze3d.systems.RenderSystem.setProjectionMatrix(handProjection,
                com.mojang.blaze3d.vertex.VertexSorting.DISTANCE_TO_ORIGIN);
        handProjection = null;
    }

    /** 十字弩的整屏镜筒遮罩：圆形视野 + 镜缘暗角 + 分划（AWP / AKM+4 倍镜改用 {@link #drawScopeReticle}） */
    private static void drawScopeOverlay(GuiGraphics g) {
        int w = g.guiWidth();
        int h = g.guiHeight();
        int cx = w / 2;
        int cy = h / 2;
        int r = (int) (Math.min(w, h) * 0.44F);
        // 镜筒外：近黑（比纯黑略亮一点，免得跟夜间场景糊在一起）
        int mask = 0xF00A0A0C;
        for (int y = 0; y < h; y++) {
            int dy = y - cy;
            int dx2 = r * r - dy * dy;
            if (dx2 <= 0) {
                g.fill(0, y, w, y + 1, mask);
                continue;
            }
            int dx = (int) Math.sqrt(dx2);
            g.fill(0, y, cx - dx, y + 1, mask);
            g.fill(cx + dx, y, w, y + 1, mask);
        }
        // 镜筒内缘一圈柔和暗角（约占半径 7%）+ 一圈玻璃边细亮环：
        // 只压镜筒最外缘，镜内中间完全不动，保证「能看清生物」。
        int band = Math.max(3, r * 7 / 100);
        for (int y = cy - r; y <= cy + r; y++) {
            int dy = y - cy;
            int outer = (int) Math.sqrt(Math.max(0, r * r - dy * dy));
            int inner = (int) Math.sqrt(Math.max(0, (r - band) * (r - band) - dy * dy));
            if (outer > inner) {
                g.fill(cx - outer, y, cx - inner, y + 1, 0x1C000000);
                g.fill(cx + inner, y, cx + outer, y + 1, 0x1C000000);
            }
            g.fill(cx - outer, y, cx - outer + 2, y + 1, 0x33FFFFFF);
            g.fill(cx + outer - 2, y, cx + outer, y + 1, 0x33FFFFFF);
        }
        drawScopeReticle(g, r, true);
    }

    /**
     * AKM 4 倍镜：**看得见枪**的那一支 —— 只叠分划 + 蓝圈（蓝圈取短边的 20%），
     * 十字线的外段延伸到屏幕边缘（duplex 观感）。
     */
    private static void drawScopeReticle(GuiGraphics g) {
        drawScopeReticle(g, (int) (Math.min(g.guiWidth(), g.guiHeight()) * 0.20F), false);
    }

    /**
     * 倍镜分划：**蓝色圆圈 + 白色十字线**（用户图 2 画的样式）。
     *
     * <p>· 白色十字：圈内一段细线（中心留空、不挡目标），圈外一段粗线（duplex 观感）；
     * <br>· 每 {@code ringR/4} 一颗密位点；正中心一颗暖色小点；
     * <br>· 蓝色圆圈用 {@code 0xFF0099FF}（与用户标注同色）画在 {@code ringR} 上 ——
     *   整屏镜筒（十字弩 / AWP）传进来的就是镜筒半径，于是蓝圈正好压在镜筒边缘上，
     *   就是一圈蓝色镜缘。
     *
     * @param limitedToRing {@code true} = 整屏镜筒开镜（十字弩 / AWP）：十字只画圈内那一段，
     *                      圈外是黑色遮罩，不再往外画粗线
     */
    private static void drawScopeReticle(GuiGraphics g, int ringR, boolean limitedToRing) {
        int w = g.guiWidth();
        int h = g.guiHeight();
        int cx = w / 2;
        int cy = h / 2;
        int rr = Math.max(24, ringR);
        int thin = Math.max(1, rr / 60);
        int thick = Math.max(2, rr / 22);
        int gap = Math.max(6, rr / 9);
        int near = 0xA0FFFFFF;
        int far = 0x72FFFFFF;
        g.fill(cx - thin, cy - rr, cx + thin, cy - gap, near);          // 上（圈内细）
        g.fill(cx - thin, cy + gap, cx + thin, cy + rr, near);          // 下
        g.fill(cx - rr, cy - thin, cx - gap, cy + thin, near);          // 左
        g.fill(cx + gap, cy - thin, cx + rr, cy + thin, near);          // 右
        if (!limitedToRing) {                                           // 圈外粗线（只在看得见枪时画）
            g.fill(cx - thick, 0, cx + thick, cy - rr, far);
            g.fill(cx - thick, cy + rr, cx + thick, h, far);
            g.fill(0, cy - thick, cx - rr, cy + thick, far);
            g.fill(cx + rr, cy - thick, w, cy + thick, far);
        }
        int tick = Math.max(2, rr / 40);
        for (int i = 1; i <= 3; i++) {                                  // 密位点
            int d = rr * i / 4;
            g.fill(cx - tick, cy - d - tick, cx + tick, cy - d + tick, near);
            g.fill(cx - tick, cy + d - tick, cx + tick, cy + d + tick, near);
            g.fill(cx - d - tick, cy - tick, cx - d + tick, cy + tick, near);
            g.fill(cx + d - tick, cy - tick, cx + d + tick, cy + tick, near);
        }
        g.fill(cx - 1, cy - 1, cx + 1, cy + 1, 0xFFFFC08A);             // 中心暖点
        drawScopeRing(g, cx, cy, rr);                                   // ★ 蓝色圆圈
    }

    /** 蓝色镜圈：按行算内 / 外半径，逐行填 —— 比“逐点画圆”匀，且不需要贴图 */
    private static void drawScopeRing(GuiGraphics g, int cx, int cy, int radius) {
        int t = Math.max(2, radius / 40);
        int outer = radius + t;
        int inner = Math.max(1, radius - t);
        int color = 0xFF0099FF;
        for (int dy = -outer; dy <= outer; dy++) {
            int xo = (int) Math.sqrt(Math.max(0, outer * outer - dy * dy));
            int xi = dy > -inner && dy < inner
                    ? (int) Math.sqrt(Math.max(0, inner * inner - dy * dy)) : 0;
            g.fill(cx - xo, cy + dy, cx - xi, cy + dy + 1, color);
            g.fill(cx + xi, cy + dy, cx + xo, cy + dy + 1, color);
        }
    }

    /**
     * 红点：装了红点的 AKM 举枪时，在屏幕正中画一个红点（与原版交叉准星同心）。
     * ★ 只画点在正中心，不遮视野 —— 枪本体照旧渲染（用户要的就是“还能看到枪”）。
     */
    private static void drawRedDot(Minecraft mc, GuiGraphics g) {
        Player player = mc.player;
        if (player == null || !player.isUsingItem()) return;
        ItemStack using = player.getUseItem();
        if (!(using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AkmRifleItem)) {
            return;
        }
        if (cn.blockforge.generated.hexalunarcalamity.weapon.Sights.sight(using)
                != cn.blockforge.generated.hexalunarcalamity.weapon.Sights.DOT) {
            return;
        }
        int cx = g.guiWidth() / 2;
        int cy = g.guiHeight() / 2;
        // 柔光 → 亮红点 → 白心：远看就是一个发光的红点
        g.fill(cx - 4, cy - 4, cx + 4, cy + 4, 0x33FF2A14);
        g.fill(cx - 3, cy - 3, cx + 3, cy + 3, 0x88FF3316);
        g.fill(cx - 2, cy - 2, cx + 2, cy + 2, 0xFFFF3A18);
        g.fill(cx - 1, cy - 1, cx + 1, cy + 1, 0xFFFFD8C8);
    }

    /** 天空着色 + 弹药 HUD + 命中标记 */
    @SubscribeEvent
    public static void onRenderGui(RenderGuiEvent.Post event) {
        Minecraft mc = Minecraft.getInstance();
        GuiGraphics g = event.getGuiGraphics();
        if (mc.player == null || mc.level == null) return;

        MoonPhase phase = activePhase();
        if (phase != null && !mc.options.hideGui) {
            // ★ r66：天空与月盘已经按各自的阶段颜色单独画了（见 MoonSkyRenderer），
            //   这层全屏叠色只留一半强度（它同时也会给地形/生物上一层氛围色）——
            //   全强度会把刚上好的天空颜色又压成一片平色。
            int a = Math.max(0, (phase.skyTint >>> 24) / 2);
            g.fill(0, 0, g.guiWidth(), g.guiHeight(), (a << 24) | (phase.skyTint & 0xFFFFFF));
        }

        if (!mc.options.hideGui) {
            if (scoping(mc.player)) {
                if (maskScoping(mc.player)) {
                    drawScopeOverlay(g);        // 十字弩：整屏镜筒遮罩 + 分划
                } else {
                    drawScopeReticle(g);        // AWP 8 倍 / AKM 4 倍镜：只叠分划，枪本体照旧渲染
                }
            }
            drawAmmoHud(mc, g);
            GrenadeHud.render(mc, g);
            drawRedDot(mc, g);
            drawHitMarker(g);
        }

        // 震爆弹：整屏白光按剩余 tick 淡出（F3 隐藏界面时也该瞎一下）
        float flash = ClientGrenadeState.overlayAlpha();
        if (flash > 0.0F) {
            int a = (int) Math.min(255.0F, flash * 255.0F);
            g.fill(0, 0, g.guiWidth(), g.guiHeight(), (a << 24) | 0xFFFFFF);
        }
    }

    /**
     * 举枪瞄准时隐藏原版准星（★ r92：对齐 TaCZ 的 {@code "show_crosshair": false}）。
     *
     * <p>TaCZ 的 {@code ak47_display.json} 写着 {@code show_crosshair=false}，用户图 1 里
     * 举枪画面也确实没有那个白色十字 —— 机瞄靠照门/准星、红点靠那颗红点（{@link #drawRedDot}）、
     * 倍镜靠分划，所以拿我们的枪抵肩时一律把原版准星收掉。复合弓例外：拉弓时要看目标。
     */
    @SubscribeEvent
    public static void onRenderGuiOverlay(net.minecraftforge.client.event.RenderGuiOverlayEvent.Pre event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || !event.getOverlay().id().getPath().equals("crosshair")) return;
        if (!mc.player.isUsingItem()) return;
        ItemStack using = mc.player.getUseItem();
        boolean gun = using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AkmRifleItem
                || using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .AwpRifleItem
                || using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .Kar98kItem
                || using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .MosinRifleItem
                || using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .M1GarandItem
                || using.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .CrossbowWeaponItem;
        if (gun) event.setCanceled(true);
    }

    private static void drawAmmoHud(Minecraft mc, GuiGraphics g) {
        Player player = mc.player;
        ItemStack weapon = AmmoUtil.heldWeapon(player);
        if (weapon == null || !(weapon.getItem() instanceof WeaponAmmo ammo)) return;
        AmmoType type = ammo.ammoType();
        int reserve = AmmoUtil.count(player, type);
        String reserveText = reserve >= Integer.MAX_VALUE ? "∞" : String.valueOf(reserve);
        String line = weapon.getItem() instanceof AkmRifleItem
                ? AkmRifleItem.mag(weapon) + " / " + reserveText
                : weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                        .AwpRifleItem
                        ? cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem.mag(weapon)
                                + (cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem
                                .chambered(weapon) ? "+1" : "") + " / " + reserveText
                        // ★ r105 Kar98k：同样「弹仓 + 膛内一发」（内置弹仓，没有可拆弹匣）
                        : weapon.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                                .Kar98kItem
                                ? cn.blockforge.generated.hexalunarcalamity.weapon.Kar98kItem.mag(weapon)
                                        + (cn.blockforge.generated.hexalunarcalamity.weapon.Kar98kItem
                                        .chambered(weapon) ? "+1" : "") + " / " + reserveText
                                // ★ r106 莫辛-纳甘：5 发弹仓 + 膛内一发（逐发压弹，没有可拆弹匣）
                                : weapon.getItem() instanceof cn.blockforge.generated
                                        .hexalunarcalamity.weapon.MosinRifleItem
                                        ? cn.blockforge.generated.hexalunarcalamity.weapon
                                                .MosinRifleItem.mag(weapon)
                                                + (cn.blockforge.generated.hexalunarcalamity.weapon
                                                .MosinRifleItem.chambered(weapon) ? "+1" : "")
                                                + " / " + reserveText
                                // ★ r108 M1 加兰德：8 发漏夹（弹仓 7 + 膛内 1）
                                : weapon.getItem() instanceof cn.blockforge.generated
                                        .hexalunarcalamity.weapon.M1GarandItem
                                        ? cn.blockforge.generated.hexalunarcalamity.weapon
                                                .M1GarandItem.mag(weapon)
                                                + (cn.blockforge.generated.hexalunarcalamity.weapon
                                                .M1GarandItem.chambered(weapon) ? "+1" : "")
                                                + " / " + reserveText
                                : reserveText;
        // ★★ r101：框宽按**文字实测宽度**算，别再写死 —— AWP 的 "4+1 / ∞" 比 "30 / ∞" 宽，
        //   原来写死 78 宽 ⇒ ∞ 被挤到框外面（用户截图）。现在右对齐时整框随文字宽度伸缩。
        Font font = mc.font;
        int padLeft = 22;                       // 图标 18 + 间隙
        int padRight = 8;
        int boxW = padLeft + font.width(line) + padRight;
        int boxH = 24;
        int x = g.guiWidth() - boxW - 10;       // 距屏幕右边 10px（原来固定 -78 ⇒ 长文字溢出）
        int y = g.guiHeight() - 38;
        g.fill(x, y - 5, x + boxW, y - 5 + boxH, 0x66000000);
        g.renderItem(new ItemStack(type.get()), x + 4, y);
        g.drawString(font, line, x + padLeft, y + 5, 0xE5E5E5, true);
    }

    private static void drawHitMarker(GuiGraphics g) {
        if (!ClientMoonState.hitActive()) return;
        boolean kill = ClientMoonState.hitIsKill();
        int max = kill ? 18 : 10;
        int alpha = Mth.clamp((int) (220.0F * ClientMoonState.hitTicksLeft() / max), 0, 220);
        int rgb = kill ? 0xFF5555 : 0xFFFFFF;
        int color = (alpha << 24) | rgb;
        int cx = g.guiWidth() / 2;
        int cy = g.guiHeight() / 2;
        g.fill(cx - 1, cy - 7, cx + 1, cy - 2, color);
        g.fill(cx - 1, cy + 2, cx + 1, cy + 7, color);
        g.fill(cx - 7, cy - 1, cx - 2, cy + 1, color);
        g.fill(cx + 2, cy - 1, cx + 7, cy + 1, color);
    }

    /** 月相期间的飘散尘埃粒子 + 命中标记衰减 */
    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        ClientMoonState.onClientTick();
        ClientGrenadeState.onClientTick();
        Minecraft mc = Minecraft.getInstance();
        // 手持动作（后坐 / 举枪 / 换弹 / 拔销…）每 tick 推进一次
        WeaponAnim.tick(mc);
        // 诊断：每秒一行「枪 / 手臂」现场数据（写 hexalunar_diag.txt，正常玩可无视）
        WeaponDiag.tick(mc);
        Level level = mc.level;
        if (level != null) GrenadeItem.clientGameTime = level.getGameTime();
        Player player = mc.player;
        if (level == null || player == null) return;
        MoonPhase phase = activePhase();
        if (phase == null || level.random.nextInt(2) != 0) return;
        int rgb = phase.dustColor;
        DustParticleOptions options = new DustParticleOptions(
                new org.joml.Vector3f(((rgb >> 16) & 0xFF) / 255F, ((rgb >> 8) & 0xFF) / 255F,
                        (rgb & 0xFF) / 255F),
                0.7F + level.random.nextFloat() * 0.6F);
        double px = player.getX() + (level.random.nextDouble() - 0.5D) * 14.0D;
        double py = player.getY() + level.random.nextDouble() * 7.0D;
        double pz = player.getZ() + (level.random.nextDouble() - 0.5D) * 14.0D;
        level.addParticle(options, px, py, pz, 0.0D, -0.012D, 0.0D);
    }

    /** 仅在夜晚且已同步到有效月相时返回 */
    private static MoonPhase activePhase() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || !mc.level.isNight()) return null;
        return ClientMoonState.phase();
    }

    private ClientEvents() {}
}
