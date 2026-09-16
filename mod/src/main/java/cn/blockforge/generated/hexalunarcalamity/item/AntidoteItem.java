package cn.blockforge.generated.hexalunarcalamity.item;

import cn.blockforge.generated.hexalunarcalamity.registry.ModEffects;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;

/**
 * 解毒剂：饮下清除尸毒，并短暂再生。
 */
public class AntidoteItem extends Item {

    public AntidoteItem(Properties properties) {
        super(properties);
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
        if (!level.isClientSide) {
            entity.removeEffect(ModEffects.CORPSE_POISON.get());
            entity.removeEffect(MobEffects.POISON);
            entity.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 120, 0));
            if (entity instanceof Player player && !player.getAbilities().instabuild) {
                stack.shrink(1);
                player.getInventory().add(new ItemStack(net.minecraft.world.item.Items.GLASS_BOTTLE));
            }
        }
        level.playSound(null, entity.getX(), entity.getY(), entity.getZ(),
                net.minecraft.sounds.SoundEvents.GENERIC_DRINK, entity.getSoundSource(),
                0.9F, 1.15F);
        return stack;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.DRINK;
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 24;
    }

    @Override
    public net.minecraft.world.InteractionResultHolder<ItemStack> use(Level level, Player player,
                                                                      net.minecraft.world.InteractionHand hand) {
        player.startUsingItem(hand);
        return net.minecraft.world.InteractionResultHolder.success(player.getItemInHand(hand));
    }
}
