package cn.blockforge.generated.hexalunarcalamity.item;

import cn.blockforge.generated.hexalunarcalamity.entity.GrenadeEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import cn.blockforge.generated.hexalunarcalamity.util.GrenadeBlasts;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

/**
 * 手雷基类：保险销 + 压杆 + 引信三段式状态机。
 *
 * <p>状态写在 ItemStack NBT 里，只在切换的那一刻写一次（拔销进度与引信倒计时都由
 * 「世界时间」推算，避免每 tick 同步槽位）：
 * <pre>
 *   SAFE         保险销插着、压杆被手压住 —— 完全安全，可以一直拿着
 *   PULLING      按住右键拔销中（1 秒）。中途松手 —— 保险销自动插回 SAFE
 *   ARMED        拔销完成，引信点燃（5 秒）。此时压杆仍被手压着，所以：
 *                  · 左键投掷 —— 压杆自然脱落，剩余引信交给抛射体
 *                  · 再按住右键 1 秒 —— 压杆还被手压着，可以把保险销重新插回去
 *                  · 一直攥在手里不丢 —— 5 秒到点，在掌心自爆
 *                  · 换槽位 / 收进背包 —— 压杆一松，保险销自己弹回去
 *   REINSERTING  正在插回保险销（1 秒）。中途松手则回到 ARMED，引信继续烧
 * </pre>
 *
 * <p>右键按下/松开由 {@code ClientWeaponInput} 轮询后打包成
 * {@code ModNetwork.GrenadeAction} 交给服务端裁决；客户端本地计数只用于进度条显示。
 */
public class GrenadeItem extends Item {

    /** 拔销（或插回保险销）所需时长：1 秒 */
    public static final int PIN_TICKS = 20;
    /** 引信总时长：5 秒 */
    public static final int FUSE_TICKS = 100;

    public static final int STATE_SAFE = 0;
    public static final int STATE_PULLING = 1;
    public static final int STATE_ARMED = 2;
    public static final int STATE_REINSERTING = 3;

    private static final String TAG_STATE = "hlc_g_state";
    private static final String TAG_HOLD_FROM = "hlc_g_hold_from";
    private static final String TAG_LIT_AT = "hlc_g_lit_at";
    private static final String TAG_FUSE = "hlc_g_fuse";

    /** 爆炸类型 */
    public enum Kind {
        /** 碎片手雷：破片杀伤 */
        FRAG,
        /** 震爆弹：眩晕 + 致盲 */
        FLASH
    }

    /**
     * 下面三个静态量由客户端 tick 写入，只服务于物品图标上的进度条与悬浮提示。
     * 刻意放在 common 代码里，避免 Item 直接引用客户端类。
     */
    public static volatile float clientPullProgress = -1.0F;
    public static volatile float clientReinsertProgress = -1.0F;
    public static volatile long clientGameTime = 0L;

    private final Kind kind;
    /** 投掷初速 */
    private final float throwPower;

    public GrenadeItem(Properties properties, Kind kind, float throwPower) {
        super(properties.stacksTo(1));
        this.kind = kind;
        this.throwPower = throwPower;
    }

    public Kind kind() {
        return kind;
    }

    // ------------------------------------------------------------------ NBT 状态

    public static int state(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? STATE_SAFE : tag.getInt(TAG_STATE);
    }

    /** 进入某个瞬时状态（拔销 / 插销），记录起始世界时间 */
    private static void beginHold(ItemStack stack, int state, long gameTime) {
        CompoundTag tag = stack.getOrCreateTag();
        tag.putInt(TAG_STATE, state);
        tag.putLong(TAG_HOLD_FROM, gameTime);
    }

    /** 点燃引信：记下点燃时刻与引信总长 */
    private static void lightFuse(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getOrCreateTag();
        tag.putInt(TAG_STATE, STATE_ARMED);
        tag.putLong(TAG_LIT_AT, gameTime);
        tag.putInt(TAG_FUSE, FUSE_TICKS);
    }

    private static void setState(ItemStack stack, int state) {
        CompoundTag tag = stack.getOrCreateTag();
        tag.putInt(TAG_STATE, state);
        if (state == STATE_SAFE) {
            tag.remove(TAG_HOLD_FROM);
            tag.remove(TAG_LIT_AT);
            tag.remove(TAG_FUSE);
        }
    }

    private static long holdFrom(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0L : tag.getLong(TAG_HOLD_FROM);
    }

    /** 引信还剩多少 tick（未拔销返回 0） */
    public static int fuseLeft(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || tag.getInt(TAG_STATE) != STATE_ARMED) return 0;
        int fuse = tag.getInt(TAG_FUSE);
        if (fuse <= 0) return 0;
        return (int) Math.max(0L, fuse - (gameTime - tag.getLong(TAG_LIT_AT)));
    }

    public static boolean isArmed(ItemStack stack) {
        return state(stack) == STATE_ARMED;
    }

    /** 玩家手上是否攥着一颗已拔销的手雷（左键可以丢出去） */
    public static boolean isHeldArmed(net.minecraft.world.entity.player.Player player) {
        ItemStack stack = heldGrenade(player);
        return stack != null && isArmed(stack);
    }

    // ------------------------------------------------------------------ 手持查找

    /**
     * 玩家手上（主手优先）的手雷，没有则 null。
     *
     * <p>主手攥着枪械时，副手的手雷不参与按键：右键要给枪瞄准、左键要给枪开火，
     * 否则一颗雷会把整套枪械操作抢走。
     */
    @Nullable
    public static ItemStack heldGrenade(Player player) {
        ItemStack main = player.getMainHandItem();
        if (main.getItem() instanceof GrenadeItem) return main;
        if (main.getItem() instanceof cn.blockforge.generated.hexalunarcalamity.weapon.WeaponAmmo) return null;
        ItemStack off = player.getOffhandItem();
        if (off.getItem() instanceof GrenadeItem) return off;
        return null;
    }

    // ------------------------------------------------------------------ 服务端动作

    /** 服务端：右键按下 —— 插着销就拔，已拔销（压杆还被手压着）就把销插回去 */
    public static void serverBeginHold(Player player) {
        ItemStack stack = heldGrenade(player);
        if (stack == null) return;
        long now = player.level().getGameTime();
        int state = state(stack);
        if (state == STATE_SAFE) {
            beginHold(stack, STATE_PULLING, now);
            player.swing(player.getMainHandItem() == stack
                    ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND);
        } else if (state == STATE_ARMED) {
            beginHold(stack, STATE_REINSERTING, now);
        }
    }

    /** 服务端：右键松开 —— 拔销没拔完前功尽弃，保险销自动插回 */
    public static void serverEndHold(Player player) {
        ItemStack stack = heldGrenade(player);
        if (stack == null) return;
        int state = state(stack);
        if (state == STATE_PULLING) {
            setState(stack, STATE_SAFE);
            tell(player, "message.hexalunar_calamity.pin_slipped", ChatFormatting.GRAY);
        } else if (state == STATE_REINSERTING) {
            // 插到一半松手：保险销还没进去，引信继续烧
            setState(stack, STATE_ARMED);
        }
    }

    /** 服务端：左键 —— 只有已拔销的手雷能丢出去，丢出去时压杆自然脱落 */
    public static void serverThrow(Player player) {
        ItemStack stack = heldGrenade(player);
        if (stack == null || !(stack.getItem() instanceof GrenadeItem g)) return;
        Level level = player.level();
        long now = level.getGameTime();
        if (player.getCooldowns().isOnCooldown(g)) return;
        if (state(stack) != STATE_ARMED) {
            tell(player, "message.hexalunar_calamity.need_pin", ChatFormatting.YELLOW);
            player.playSound(SoundEvents.UI_BUTTON_CLICK.value(), 0.3F, 1.8F);
            return;
        }
        int remaining = Math.max(1, fuseLeft(stack, now));

        GrenadeEntity grenade = new GrenadeEntity(level, player, g.kind, remaining);
        grenade.setPos(player.getEyePosition().add(player.getLookAngle().scale(0.55D)));
        grenade.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, g.throwPower, 0.02F);
        level.addFreshEntity(grenade);

        // 压杆崩飞：火星四散 + 金属脆响，随后引信嘶嘶声
        var at = player.getEyePosition().add(player.getLookAngle().scale(0.6D));
        GrenadeBlasts.spoonFlyOff(level, at);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.TRIDENT_THROW, SoundSource.PLAYERS, 0.7F, 1.35F);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.ARMOR_EQUIP_CHAIN, SoundSource.PLAYERS, 0.5F, 1.9F);
        level.playSound(null, at.x, at.y, at.z, ModSounds.FUSE.get(), SoundSource.PLAYERS, 0.6F, 1.25F);

        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        } else {
            setState(stack, STATE_SAFE);
        }
        player.getCooldowns().addCooldown(g, 6);
    }

    /** 服务端每 tick：推进拔销/插销、烧引信、处理「压杆离开手」的情况 */
    public static void serverTick(Player player) {
        Level level = player.level();
        long now = level.getGameTime();
        for (InteractionHand hand : InteractionHand.values()) {
            ItemStack stack = player.getItemInHand(hand);
            if (!(stack.getItem() instanceof GrenadeItem g)) continue;
            switch (state(stack)) {
                case STATE_PULLING -> {
                    if (now - holdFrom(stack) >= PIN_TICKS) g.completePull(player, stack, now);
                }
                case STATE_REINSERTING -> {
                    if (now - holdFrom(stack) >= PIN_TICKS) {
                        setState(stack, STATE_SAFE);
                        player.playSound(SoundEvents.ARMOR_EQUIP_GENERIC, 0.35F, 1.55F);
                        tell(player, "message.hexalunar_calamity.pin_back", ChatFormatting.GREEN);
                    }
                }
                case STATE_ARMED -> {
                    if (g.fuseLeft(stack, now) <= 0) {
                        // 攥在手里不放超过引信时长：在掌心自爆
                        setState(stack, STATE_SAFE);
                        stack.shrink(1);
                        GrenadeBlasts.detonateInHand(level, player, g.kind);
                    }
                }
                default -> {
                }
            }
        }
        // 主手换成枪械后，副手那颗雷等于被胳膊夹着、手指没压住压杆：保险销自己弹回去
        ItemStack offhand = player.getOffhandItem();
        if (player.getMainHandItem().getItem()
                instanceof cn.blockforge.generated.hexalunarcalamity.weapon.WeaponAmmo
                && offhand.getItem() instanceof GrenadeItem
                && state(offhand) != STATE_SAFE) {
            setState(offhand, STATE_SAFE);
        }
        // 不在手上的手雷：压杆失去手的压力，保险销自己弹回去
        var slots = player.getInventory().items;
        for (int i = 0; i < slots.size(); i++) {
            ItemStack stack = slots.get(i);
            if (i == player.getInventory().selected) continue;
            if (stack.getItem() instanceof GrenadeItem && state(stack) != STATE_SAFE) {
                setState(stack, STATE_SAFE);
            }
        }
    }

    /** 拔销完成：压杆仍被手压住，但引信已经点燃 */
    private void completePull(Player player, ItemStack stack, long gameTime) {
        lightFuse(stack, gameTime);
        var at = player.getEyePosition().add(player.getLookAngle().scale(0.5D));
        GrenadeBlasts.fuseSparks(player.level(), at);
        player.playSound(SoundEvents.TNT_PRIMED, 0.6F, 1.6F);
        player.playSound(ModSounds.FUSE.get(), 0.7F, 1.0F);
        tell(player, "message.hexalunar_calamity.pin_pulled", ChatFormatting.RED);
    }

    private static void tell(Player player, String key, ChatFormatting color) {
        player.displayClientMessage(Component.translatable(key).withStyle(color), true);
    }

    /** 已拔销时把剩余秒数写进名字后缀，一眼能看出这颗是活的 */
    @Override
    public Component getName(ItemStack stack) {
        Component base = super.getName(stack);
        // 服务端没有客户端世界时间，算出的秒数没有意义，只在客户端加后缀
        if (state(stack) != STATE_ARMED || clientGameTime <= 0L) return base;
        int left = fuseLeft(stack, clientGameTime);
        return base.copy().append(Component.translatable(
                        "item.hexalunar_calamity.grenade_armed_suffix",
                        String.format(java.util.Locale.ROOT, "%.1f", Math.max(0, left) / 20.0F))
                .withStyle(ChatFormatting.RED));
    }

    // ------------------------------------------------------------------ 图标进度条

    @Override
    public boolean isBarVisible(ItemStack stack) {
        return state(stack) != STATE_SAFE;
    }

    @Override
    public int getBarWidth(ItemStack stack) {
        return Math.round(13.0F * Mth.clamp(progress(stack), 0.0F, 1.0F));
    }

    @Override
    public int getBarColor(ItemStack stack) {
        int state = state(stack);
        if (state == STATE_PULLING) return 0x4FC3FF;
        if (state == STATE_REINSERTING) return 0x5FE08A;
        float p = progress(stack);
        if (p > 0.5F) return 0xFFC24D;
        if (p > 0.2F) return 0xFF8A26;
        return (clientGameTime / 5L) % 2L == 0L ? 0xFF3131 : 0x7A1010;
    }

    /** 0..1：拔销 / 插销看客户端计数，已拔销看引信剩余 */
    public static float progress(ItemStack stack) {
        int state = state(stack);
        if (state == STATE_PULLING) {
            return Math.max(0.0F, clientPullProgress);
        }
        if (state == STATE_REINSERTING) {
            return Math.max(0.0F, clientReinsertProgress);
        }
        if (state == STATE_ARMED) {
            CompoundTag tag = stack.getTag();
            int fuse = tag == null ? FUSE_TICKS : Math.max(1, tag.getInt(TAG_FUSE));
            return Mth.clamp(fuseLeft(stack, clientGameTime) / (float) fuse, 0.0F, 1.0F);
        }
        return 0.0F;
    }

    // ------------------------------------------------------------------ 提示

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level,
                                java.util.List<Component> tips, TooltipFlag flag) {
        tips.add(Component.translatable(kind == Kind.FRAG
                        ? "tooltip.hexalunar_calamity.grenade_frag"
                        : "tooltip.hexalunar_calamity.grenade_flash")
                .withStyle(ChatFormatting.GRAY));
        switch (state(stack)) {
            case STATE_ARMED -> {
                int left = fuseLeft(stack, clientGameTime);
                tips.add(Component.translatable("tooltip.hexalunar_calamity.grenade_armed",
                                String.format(java.util.Locale.ROOT, "%.1f", Math.max(0, left) / 20.0F))
                        .withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
            }
            case STATE_PULLING -> tips.add(Component.translatable(
                    "tooltip.hexalunar_calamity.grenade_pulling").withStyle(ChatFormatting.AQUA));
            case STATE_REINSERTING -> tips.add(Component.translatable(
                    "tooltip.hexalunar_calamity.grenade_reinserting").withStyle(ChatFormatting.GREEN));
            default -> tips.add(Component.translatable(
                    "tooltip.hexalunar_calamity.grenade_safe").withStyle(ChatFormatting.DARK_GREEN));
        }
    }

    @Override
    public boolean canAttackBlock(net.minecraft.world.level.block.state.BlockState blockState, Level level,
                                  net.minecraft.core.BlockPos pos, Player player) {
        // 攥着手雷不拆方块
        return false;
    }
}
