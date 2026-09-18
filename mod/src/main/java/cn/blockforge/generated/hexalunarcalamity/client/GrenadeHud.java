package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.item.GrenadeItem;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * 手雷 HUD：准星下方一行状态提示。
 *
 * <p>物品图标上的原版耐久条负责显示进度（拔销 / 插销 / 剩余引信），
 * 这里只补一句人话：现在该按住右键还是该丢出去。
 */
public final class GrenadeHud {

    private GrenadeHud() {}

    public static void render(Minecraft mc, GuiGraphics g) {
        Player player = mc.player;
        if (player == null) return;
        // heldGrenade() 手里没手雷时返回 null —— 这里必须判空，否则每帧 NPE 直接 FATAL 崩客户端
        ItemStack stack = GrenadeItem.heldGrenade(player);
        if (stack == null || !(stack.getItem() instanceof GrenadeItem)) return;

        Component line = switch (GrenadeItem.state(stack)) {
            case GrenadeItem.STATE_PULLING -> with(ChatFormatting.AQUA,
                    "tooltip.hexalunar_calamity.grenade_pulling");
            case GrenadeItem.STATE_REINSERTING -> with(ChatFormatting.GREEN,
                    "tooltip.hexalunar_calamity.grenade_reinserting");
            case GrenadeItem.STATE_PRIMED -> with(ChatFormatting.GOLD,
                    "hud.hexalunar_calamity.grenade_primed");
            case GrenadeItem.STATE_ARMED -> Component.translatable(
                            "hud.hexalunar_calamity.grenade_armed",
                            String.format(java.util.Locale.ROOT, "%.1f",
                                    GrenadeItem.progress(stack) * GrenadeItem.FUSE_TICKS / 20.0F))
                    .withStyle(ChatFormatting.RED, ChatFormatting.BOLD);
            default -> with(ChatFormatting.GRAY, "hud.hexalunar_calamity.grenade_safe");
        };

        Font font = mc.font;
        int w = font.width(line);
        int x = (g.guiWidth() - w) / 2;
        int y = g.guiHeight() / 2 + 26;
        g.drawString(font, line, x, y, 0xFFE6E6E6, true);
    }

    private static Component with(ChatFormatting color, String key) {
        return Component.translatable(key).withStyle(color);
    }
}
