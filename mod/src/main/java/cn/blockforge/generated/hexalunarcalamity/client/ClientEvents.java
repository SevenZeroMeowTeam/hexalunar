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

    /** 右键持枪瞄准时收紧视野：十字弩开 4 倍镜，其余武器适度拉近 */
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
            // 4 倍镜：视野缩到 1/4；同时保留原版最小视角钳制
            event.setNewFovModifier(1.0F / cn.blockforge.generated
                    .hexalunarcalamity.weapon.CrossbowWeaponItem.SCOPE_ZOOM);
            return;
        }
        // AKM 装了红点：只轻微拉近（仍然看得见枪本体）
        if (player.getUseItem().getItem() instanceof cn.blockforge.generated
                .hexalunarcalamity.weapon.AkmRifleItem) {
            int sight = cn.blockforge.generated.hexalunarcalamity.weapon.Sights
                    .sight(player.getUseItem());
            event.setNewFovModifier(event.getNewFovModifier()
                    * (sight == cn.blockforge.generated.hexalunarcalamity.weapon.Sights.DOT
                    ? 0.88F : 0.72F));
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
     * 开镜（十字弩 / AKM+4 倍镜）时隐藏第一人称的手与武器（像原版望远镜那样只看镜内）。
     *
     * <p>非开镜时，主手拿 AKM / 十字弩再把玩家自己的**两条手臂**补上（见 {@link WeaponArms}）——
     * 原版对非空物品只画物品不画手；左手还会按换弹进度做事：AKM 托护木 / 抽弹匣 / 拉机柄，
     * 十字弩拉弦 / 递箭上槽。
     */
    @SubscribeEvent
    public static void onRenderHand(net.minecraftforge.client.event.RenderHandEvent event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && scoping(mc.player)) {
            event.setCanceled(true);
            return;
        }
        if (event.getHand() != net.minecraft.world.InteractionHand.MAIN_HAND) return;
        net.minecraft.world.item.Item item = event.getItemStack().getItem();
        if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon.AkmRifleItem) {
            WeaponArms.renderAkm(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        } else if (item instanceof cn.blockforge.generated.hexalunarcalamity.weapon
                .CrossbowWeaponItem) {
            WeaponArms.renderCrossbow(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        } else if (item instanceof cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem) {
            // 手雷 / 震爆弹：右手握雷；左手只在拔销 / 插销时伸进来抓拉环
            WeaponArms.renderGrenade(mc, event.getPoseStack(), event.getMultiBufferSource(),
                    event.getPackedLight());
        }
    }

    /** 开镜时绘制倍镜遮罩：圆形视野 + 镜缘暗角 + 对称十字分划 */
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
        // 十字分划：对称，中心留空，外侧一段更淡
        int gap = 10;
        int len = Math.max(14, Math.min(r / 4, 40));
        int tick = Math.max(5, len / 2);
        int near = 0x8CFFFFFF;
        int far = 0x3AFFFFFF;
        g.fill(cx - 1, cy - gap - tick, cx, cy - gap, near);          // 上
        g.fill(cx - 1, cy - gap - len, cx, cy - gap - tick, far);
        g.fill(cx - 1, cy + gap, cx, cy + gap + tick, near);          // 下
        g.fill(cx - 1, cy + gap + tick, cx, cy + gap + len, far);
        g.fill(cx - gap - tick, cy - 1, cx - gap, cy, near);          // 左
        g.fill(cx - gap - len, cy - 1, cx - gap - tick, cy, far);
        g.fill(cx + gap, cy - 1, cx + gap + tick, cy, near);          // 右
        g.fill(cx + gap + tick, cy - 1, cx + gap + len, cy, far);
        g.fill(cx - 1, cy - 1, cx, cy, 0x9CFFFFFF);                   // 中心 1px
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
            boolean zoom = scoping(mc.player);
            if (zoom) {
                drawScopeOverlay(g);
            } else {
                drawAmmoHud(mc, g);
                GrenadeHud.render(mc, g);
                drawRedDot(mc, g);
            }
            drawHitMarker(g);
        }

        // 震爆弹：整屏白光按剩余 tick 淡出（F3 隐藏界面时也该瞎一下）
        float flash = ClientGrenadeState.overlayAlpha();
        if (flash > 0.0F) {
            int a = (int) Math.min(255.0F, flash * 255.0F);
            g.fill(0, 0, g.guiWidth(), g.guiHeight(), (a << 24) | 0xFFFFFF);
        }
    }

    /** 开镜时用倍镜分划线代替原版准星（红点不动准星：红点就画在准星中心） */
    @SubscribeEvent
    public static void onRenderGuiOverlay(net.minecraftforge.client.event.RenderGuiOverlayEvent.Pre event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && event.getOverlay().id().getPath().equals("crosshair")
                && scoping(mc.player)) {
            event.setCanceled(true);
        }
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
                : reserveText;
        int x = g.guiWidth() - 78;
        int y = g.guiHeight() - 38;
        g.fill(x - 6, y - 5, x + 72, y + 19, 0x66000000);
        g.renderItem(new ItemStack(type.get()), x - 2, y);
        Font font = mc.font;
        g.drawString(font, line, x + 18, y + 5, 0xE5E5E5, true);
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
