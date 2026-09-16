package cn.blockforge.generated.hexalunarcalamity.item;

import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoType;
import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoUtil;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundSource;
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
 * 弹药盒：右手键收纳背包里对应弹药；武器装填时优先从手持弹药盒取弹。
 */
public class AmmoBoxItem extends Item {

    public final AmmoType type;

    public AmmoBoxItem(AmmoType type, Properties properties) {
        super(properties);
        this.type = type;
    }

    public static int stored(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0 : tag.getInt("HlcStored");
    }

    public static void put(ItemStack stack, int value) {
        stack.getOrCreateTag().putInt("HlcStored", Math.max(0, value));
    }

    /** 取出至多 want 发，返回实际数量 */
    public static int take(ItemStack stack, int want) {
        int have = stored(stack);
        int moved = Math.min(have, Math.max(0, want));
        if (moved > 0) put(stack, have - moved);
        return moved;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        int capacity = type.boxCapacity;
        int have = stored(stack);
        if (have >= capacity) {
            return InteractionResultHolder.fail(stack);
        }
        if (!level.isClientSide) {
            int moved = AmmoUtil.takeFromInventory(player, type.get(), capacity - have);
            if (moved > 0) {
                put(stack, have + moved);
                level.playSound(null, player.getX(), player.getY(), player.getZ(),
                        cn.blockforge.generated.hexalunarcalamity.registry.ModSounds.RELOAD.get(),
                        SoundSource.PLAYERS, 0.8F, 1.05F);
            } else {
                player.displayClientMessage(
                        Component.translatable("message.hexalunar_calamity.no_ammo_to_store"), true);
            }
        }
        return InteractionResultHolder.success(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> lines, TooltipFlag flag) {
        lines.add(Component.translatable("tooltip.hexalunar_calamity.ammo_box_type",
                type.get().getDescription())
                .withStyle(net.minecraft.ChatFormatting.GRAY));
        lines.add(Component.translatable("tooltip.hexalunar_calamity.ammo_box",
                stored(stack), type.boxCapacity)
                .withStyle(net.minecraft.ChatFormatting.GRAY));
        lines.add(Component.translatable("tooltip.hexalunar_calamity.ammo_box_hint")
                .withStyle(net.minecraft.ChatFormatting.DARK_GRAY));
    }
}
