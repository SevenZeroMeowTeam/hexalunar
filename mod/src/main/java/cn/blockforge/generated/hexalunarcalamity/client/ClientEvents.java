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
        if (cn.blockforge.generated.hexalunarcalamity.weapon
                .CrossbowWeaponItem.isScoping(player)) {
            // 4 倍镜：视野缩到 1/4；同时保留原版最小视角钳制
            event.setNewFovModifier(1.0F / cn.blockforge.generated
                    .hexalunarcalamity.weapon.CrossbowWeaponItem.SCOPE_ZOOM);
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

    /** 眩晕：让镜头绕视线轻轻打横，越接近爆炸中心晃得越厉害 */
    @SubscribeEvent
    public static void onCameraAngles(ViewportEvent.ComputeCameraAngles event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) return;
        float amp = stunStrength(mc.player);
        if (amp <= 0.0F) return;
        float t = mc.level.getGameTime() + (float) event.getPartialTick();
        event.setRoll(event.getRoll() + 3.2F * amp * Mth.sin(t * 0.09F)
                + 1.1F * amp * Mth.sin(t * 0.27F));
        event.setPitch(event.getPitch() + 0.9F * amp * Mth.sin(t * 0.15F + 1.7F));
    }

    /** 眩晕强度 0..1：剩余时间越短越轻，最后一秒平滑收尾 */
    private static float stunStrength(Player player) {
        var effect = player.getEffect(ModEffects.STUN.get());
        if (effect == null) return 0.0F;
        int left = effect.getDuration();
        float fade = left > 20 ? 1.0F : Math.max(0.0F, left / 20.0F);
        return fade * (effect.getAmplifier() > 0 ? 1.0F : 0.65F);
    }

    /** 开镜时隐藏第一人称的手与武器（像原版望远镜那样只看镜内） */
    @SubscribeEvent
    public static void onRenderHand(net.minecraftforge.client.event.RenderHandEvent event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && cn.blockforge.generated.hexalunarcalamity.weapon
                .CrossbowWeaponItem.isScoping(mc.player)) {
            event.setCanceled(true);
        }
    }

    /** 开镜时绘制倍镜遮罩：圆形视野 + 黑边 + 十字分划线 */
    private static void drawScopeOverlay(Minecraft mc, GuiGraphics g) {
        int w = g.guiWidth();
        int h = g.guiHeight();
        int cx = w / 2;
        int cy = h / 2;
        int r = Math.min(w, h) * 42 / 100;
        int ring = (0xDD << 24) | 0x0A0A0A;
        for (int y = 0; y < h; y++) {
            int dy = y - cy;
            int dx2 = r * r - dy * dy;
            if (dx2 <= 0) {
                g.fill(0, y, w, y + 1, ring);
                continue;
            }
            int dx = (int) Math.sqrt(dx2);
            g.fill(0, y, cx - dx, y + 1, ring);
            g.fill(cx + dx, y, w, y + 1, ring);
        }
        // 镜筒边缘细环
        int edge = (0x66 << 24);
        for (int y = 0; y < h; y++) {
            int dy = y - cy;
            int dx2 = (r + 2) * (r + 2) - dy * dy;
            int dxr = (r - 1) * (r - 1) - dy * dy;
            if (dx2 > 0) {
                int outer = (int) Math.sqrt(dx2);
                int inner = dxr > 0 ? (int) Math.sqrt(dxr) : 0;
                if (outer > inner) {
                    g.fill(cx - outer, y, cx - inner, y + 1, edge);
                    g.fill(cx + inner, y, cx + outer, y + 1, edge);
                }
            }
        }
        // 十字分划：中心留空 + 短分划 + 内亮外淡
        // 之前是从中心 6px 一直画到 r/2（480p 下约 100px）且不透明度 0xB0，又长又亮会挡视野；
        // 现在总长压到 min(r/3, 52)，中心留 9px 空白，外侧一段更淡，只看得到“刻度感”。
        int gap = 9;
        int len = Math.max(16, Math.min(r / 3, 52));
        int tick = Math.max(6, len / 3);
        int near = 0x74FFFFFF;      // 靠近中心的一段（相对清楚）
        int far = 0x3CFFFFFF;       // 外段（很淡，只作参考）
        // 上
        g.fill(cx - 1, cy - gap - tick, cx, cy - gap, near);
        g.fill(cx - 1, cy - gap - len, cx, cy - gap - tick, far);
        // 下
        g.fill(cx - 1, cy + gap, cx, cy + gap + tick, near);
        g.fill(cx - 1, cy + gap + tick, cx, cy + gap + len, far);
        // 左
        g.fill(cx - gap - tick, cy - 1, cx - gap, cy, near);
        g.fill(cx - gap - len, cy - 1, cx - gap - tick, cy, far);
        // 右
        g.fill(cx + gap, cy - 1, cx + gap + tick, cy, near);
        g.fill(cx + gap + tick, cy - 1, cx + gap + len, cy, far);
        // 中心 1px 细点：能对准，但不会糊住目标
        g.fill(cx - 1, cy - 1, cx, cy, 0x9CFFFFFF);
    }

    /** 天空着色 + 弹药 HUD + 命中标记 */
    @SubscribeEvent
    public static void onRenderGui(RenderGuiEvent.Post event) {
        Minecraft mc = Minecraft.getInstance();
        GuiGraphics g = event.getGuiGraphics();
        if (mc.player == null || mc.level == null) return;

        MoonPhase phase = activePhase();
        if (phase != null && !mc.options.hideGui) {
            g.fill(0, 0, g.guiWidth(), g.guiHeight(), phase.skyTint);
        }

        if (!mc.options.hideGui) {
            boolean scoping = cn.blockforge.generated.hexalunarcalamity.weapon
                    .CrossbowWeaponItem.isScoping(mc.player);
            if (scoping) {
                drawScopeOverlay(mc, g);
            } else {
                drawAmmoHud(mc, g);
                GrenadeHud.render(mc, g);
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

    /** 开镜时用倍镜分划线代替原版准星 */
    @SubscribeEvent
    public static void onRenderGuiOverlay(net.minecraftforge.client.event.RenderGuiOverlayEvent.Pre event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && event.getOverlay().id().getPath().equals("crosshair")
                && cn.blockforge.generated.hexalunarcalamity.weapon
                .CrossbowWeaponItem.isScoping(mc.player)) {
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
