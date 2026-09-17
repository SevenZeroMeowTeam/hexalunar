package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.entity.PiercingArrowEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModItems;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;

/**
 * 复合弓：右键按住 = 瞄准蓄力，松开右键满蓄射击；
 * 左键 = 按当前蓄力直接击发（准度随蓄力提高）。
 * 无普通箭时自动改用尸毒箭。
 */
public class CompoundBowItem extends Item implements WeaponAmmo {

    /** 左键连点的最小间隔（tick），客户端按此节奏发开火包 */
    public static final int FIRE_INTERVAL = 8;

    public CompoundBowItem(Properties properties) {
        super(properties);
    }

    @Override
    public AmmoType ammoType() {
        return AmmoType.ARROW;
    }

    /** 客户端：第三人称手臂姿态（原版按 UseAnim.BOW 自己给拉弓姿势） */
    @Override
    public void initializeClient(java.util.function.Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(cn.blockforge.generated.hexalunarcalamity.client.WeaponArmPose.BOW);
    }

    /** 右键：瞄准蓄力 */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (AmmoUtil.count(player, AmmoType.ARROW) <= 0 && !hasPoisonArrow(player)) {
            if (!level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return InteractionResultHolder.fail(stack);
        }
        player.startUsingItem(hand);
        return InteractionResultHolder.success(stack);
    }

    private boolean hasPoisonArrow(Player player) {
        for (ItemStack stack : player.getInventory().items) {
            if (stack.is(ModItems.POISON_ARROW.get())) return true;
        }
        return false;
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.BOW;
    }

    @Override
    public void appendHoverText(ItemStack stack, Level level,
                                java.util.List<net.minecraft.network.chat.Component> tips,
                                net.minecraft.world.item.TooltipFlag flag) {
        tips.add(net.minecraft.network.chat.Component.translatable(
                "tooltip.hexalunar_calamity.bow_controls")
                .withStyle(net.minecraft.ChatFormatting.GRAY));
        tips.add(net.minecraft.network.chat.Component.translatable(
                "tooltip.hexalunar_calamity.range_hint", (int) Ballistics.BOW_RANGE)
                .withStyle(net.minecraft.ChatFormatting.DARK_GRAY));
    }

    /** 供 HUD / 视野缩放使用：由剩余使用 tick 换算蓄力成数 */
    public static float pullProgress(int remainingUseTicks) {
        return BowItem.getPowerForTime(72000 - remainingUseTicks);
    }

    /** 松开右键：以当前蓄力射击 */
    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
        if (!(entity instanceof Player player) || level.isClientSide) return;
        int useTime = this.getUseDuration(stack) - timeLeft;
        float pull = BowItem.getPowerForTime(useTime);
        if (pull < 0.15F) return;
        shoot(player, stack, level, InteractionHand.MAIN_HAND, pull);
    }

    /** 左键（服务端）：按当前瞄准蓄力击发，最低保底 0.35 成数 */
    @Override
    public void serverFire(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        float pull = 0.35F;
        if (player.isUsingItem() && player.getUseItem() == stack) {
            int useTime = this.getUseDuration(stack) - player.getUseItemRemainingTicks();
            pull = Math.max(pull, BowItem.getPowerForTime(useTime));
        }
        shoot(player, stack, level, hand, pull);
    }

    /** 实际击发：pull 为 0~1 蓄力成数 */
    private void shoot(Player player, ItemStack stack, Level level, InteractionHand hand, float pull) {
        boolean poison = false;
        if (!AmmoUtil.consume(player, AmmoType.ARROW, 1)) {
            // 改用尸毒箭
            if (AmmoUtil.takeFromInventory(player, ModItems.POISON_ARROW.get(), 1) > 0) {
                poison = true;
            } else {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
                return;
            }
        }

        PiercingArrowEntity arrow = new PiercingArrowEntity(level, player);
        arrow.setPos(player.getEyePosition().add(player.getLookAngle().scale(0.6D)));
        arrow.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F,
                2.6F + 1.4F * pull, 1.0F - pull);
        arrow.setBaseDamage(5.0D + 7.5D * pull * pull);
        arrow.setPierceLevel((byte) 2);
        arrow.setCritArrow(pull >= 1.0F);
        arrow.setToxic(poison);
        level.addFreshEntity(arrow);

        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.BOW_SHOT.get(), SoundSource.PLAYERS, 1.0F,
                Mth.clamp(0.9F + pull * 0.25F, 0.8F, 1.3F));
        player.swing(hand);
    }
}
