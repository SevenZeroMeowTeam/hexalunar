package cn.blockforge.generated.hexalunarcalamity.item;

import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * 创造弹药盒：**只要躺在物品栏里（快捷栏 / 背包 / 副手都算）**，三把武器就无限供弹。
 *
 * <p>不需要手持、也不需要手动切换弹种 —— 供弹判断统一走 {@link #inInventory(Player)}，
 * 命中就直接当成无限弹药（见 {@code weapon/AmmoUtil}）。所以这个物品不再有任何交互逻辑，
 * 「右键」只是给一句提示，免得玩家以为还得拿在手上。
 */
public class CreativeAmmoBoxItem extends Item {

    public CreativeAmmoBoxItem(Properties properties) {
        super(properties);
    }

    /** 玩家物品栏（含快捷栏与副手）里有没有创造弹药盒 */
    public static boolean inInventory(Player player) {
        if (player == null) return false;
        for (ItemStack stack : player.getInventory().items) {
            if (stack.getItem() instanceof CreativeAmmoBoxItem) return true;
        }
        for (ItemStack stack : player.getInventory().offhand) {
            if (stack.getItem() instanceof CreativeAmmoBoxItem) return true;
        }
        return false;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!level.isClientSide) {
            player.displayClientMessage(
                    Component.translatable("message.hexalunar_calamity.creative_box_hint"), true);
        }
        return InteractionResultHolder.pass(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> lines,
                                TooltipFlag flag) {
        lines.add(Component.translatable("tooltip.hexalunar_calamity.creative_box")
                .withStyle(net.minecraft.ChatFormatting.GOLD));
    }
}
