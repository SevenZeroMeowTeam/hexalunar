package cn.blockforge.generated.hexalunarcalamity.item;

import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.weapon.AmmoType;
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
 * 创造弹药盒：潜行右键在三类弹药间切换，为任意对应武器无限供弹。
 */
public class CreativeAmmoBoxItem extends Item {

    public CreativeAmmoBoxItem(Properties properties) {
        super(properties);
    }

    @Nullable
    private static ItemStack heldBox(Player player) {
        ItemStack main = player.getMainHandItem();
        if (main.getItem() instanceof CreativeAmmoBoxItem) return main;
        ItemStack off = player.getOffhandItem();
        if (off.getItem() instanceof CreativeAmmoBoxItem) return off;
        return null;
    }

    public static AmmoType modeFor(Player player) {
        ItemStack box = heldBox(player);
        if (box == null) return AmmoType.BOLT;
        int idx = box.getTag() == null ? 0 : box.getTag().getInt("HlcMode");
        AmmoType[] all = AmmoType.values();
        return all[Math.floorMod(idx, all.length)];
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!player.isShiftKeyDown()) {
            if (!level.isClientSide) {
                player.displayClientMessage(
                        Component.translatable("message.hexalunar_calamity.cycle_hint",
                                Component.translatable("item.hexalunar_calamity." + modeFor(player).id)),
                        true);
            }
            return InteractionResultHolder.pass(stack);
        }
        int next = (stack.getTag() == null ? 0 : stack.getTag().getInt("HlcMode")) + 1;
        stack.getOrCreateTag().putInt("HlcMode", next % AmmoType.values().length);
        if (!level.isClientSide) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    ModSounds.RELOAD.get(), SoundSource.PLAYERS, 0.7F, 1.35F);
            player.displayClientMessage(
                    Component.translatable("message.hexalunar_calamity.mode_set",
                            Component.translatable("item.hexalunar_calamity." + modeFor(player).id)), true);
        }
        return InteractionResultHolder.success(stack);
    }

    /** 手上拿着武器时自动切到对应弹种（免得持枪却显示无弹） */
    @Override
    public void inventoryTick(ItemStack stack, Level level, net.minecraft.world.entity.Entity entity,
                              int slot, boolean selected) {
        super.inventoryTick(stack, level, entity, slot, selected);
        if (!(entity instanceof Player player)) return;
        ItemStack other = player.getMainHandItem() == stack
                ? player.getOffhandItem() : player.getMainHandItem();
        if (other.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon.WeaponAmmo ammo) {
            int idx = ammo.ammoType().ordinal();
            if (stack.getOrCreateTag().getInt("HlcMode") != idx) {
                stack.getOrCreateTag().putInt("HlcMode", idx);
            }
        }
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> lines, TooltipFlag flag) {
        lines.add(Component.translatable("tooltip.hexalunar_calamity.creative_box",
                Component.translatable("item.hexalunar_calamity." + mode(stack).id))
                .withStyle(net.minecraft.ChatFormatting.GOLD));
    }

    private static AmmoType mode(ItemStack stack) {
        int idx = stack.getTag() == null ? 0 : stack.getTag().getInt("HlcMode");
        AmmoType[] all = AmmoType.values();
        return all[Math.floorMod(idx, all.length)];
    }
}
