package cn.blockforge.generated.hexalunarcalamity.item;

import cn.blockforge.generated.hexalunarcalamity.entity.PoisonBottleEntity;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * 尸毒瓶：投掷后在落点炸开一团尸毒雾。
 */
public class PoisonBottleItem extends Item {

    public PoisonBottleItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!level.isClientSide) {
            PoisonBottleEntity bottle = new PoisonBottleEntity(level, player);
            bottle.setPos(player.getEyePosition().add(player.getLookAngle().scale(0.5D)));
            bottle.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, 0.95F, 0.6F);
            level.addFreshEntity(bottle);
        }
        level.playSound(player, player.getX(), player.getY(), player.getZ(),
                SoundEvents.SPLASH_POTION_THROW, SoundSource.PLAYERS, 0.7F, 0.95F + level.random.nextFloat() * 0.1F);
        if (!player.getAbilities().instabuild) stack.shrink(1);
        player.getCooldowns().addCooldown(this, 14);
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }
}
