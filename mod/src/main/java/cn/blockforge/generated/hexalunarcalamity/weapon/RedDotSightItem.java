package cn.blockforge.generated.hexalunarcalamity.weapon;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

import java.util.List;

/** 红点瞄准镜：装到 AKM 顶部导轨上，举枪时屏幕正中会有一个红点（仍然看得见枪本体）。 */
public class RedDotSightItem extends Item {

    public RedDotSightItem(Properties properties) {
        super(properties);
    }

    @Override
    public void appendHoverText(ItemStack stack, Level level, List<Component> tips, TooltipFlag flag) {
        tips.add(Component.translatable("tooltip.hexalunar_calamity.sight_mount")
                .withStyle(ChatFormatting.GRAY));
    }
}
