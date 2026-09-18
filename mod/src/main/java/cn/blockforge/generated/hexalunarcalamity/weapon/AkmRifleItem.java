package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.client.AkmAnimState;
import cn.blockforge.generated.hexalunarcalamity.client.AkmItemClientExtensions;
import cn.blockforge.generated.hexalunarcalamity.entity.BulletEntity;
import cn.blockforge.generated.hexalunarcalamity.registry.ModSounds;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.List;
import java.util.function.Consumer;

/**
 * AKM 突击步枪（卡拉什尼科夫 7.62x39）。
 *
 * <h2>模型与骨骼</h2>
 * 几何由 {@code tools/akm_v2.py} 按参考模型 {@code 模型/akm.bbmodel} 的 PCA 对齐实测比例
 * 手工重建（67 方块 / 14 骨骼 / 512² 逐面 UV 贴图）。骨骼：
 * {@code root → move → body → barrel / sights / handguard / dust_cover / bolt /
 * magazine / trigger / grip / stock / selector / camera}。
 * 朝向约定：<b>枪口 = -Z（北）</b>、<b>上 = +Y</b>、<b>原点 = 握把</b>。
 *
 * <h2>操作</h2>
 * <ul>
 *   <li>左键：单发点射；按住左键 = 全自动（每 {@value #FIRE_INTERVAL} tick 一发）</li>
 *   <li>右键按住：抵肩瞄准（散布大幅收紧）</li>
 *   <li>R 键：战术换弹（弹匣没满就能补弹）；打空后右键也能触发换弹</li>
 * </ul>
 *
 * <h2>动画</h2>
 * 骨骼动画来自 {@code animations/akm.animation.json}，控制器名 {@value #GEO_CONTROLLER}；
 * 状态由客户端 {@link AkmAnimState} 的计时窗口给出（不走服务端 {@code triggerAnim}，
 * 避免丢包/延迟）。换弹进度另外读物品 NBT，见 {@link #reloadProgress}。
 */
public class AkmRifleItem extends Item implements WeaponAmmo, GeoItem {

    // ---------------------------------------------------------------- 数值
    /** 弹匣容量 */
    public static final int MAG_SIZE = 30;
    /** 换弹耗时（tick） */
    public static final int RELOAD_TICKS = 40;
    /** 全自动射速：客户端按此间隔发开火包（tick） */
    public static final int FIRE_INTERVAL = 2;
    /** 停火多久开始掉热量（tick） */
    private static final int HEAT_DECAY_IDLE_TICKS = 12;
    /** 热量上限（决定最大散布惩罚） */
    private static final int HEAT_MAX = 30;

    // ---------------------------------------------------------------- 动画
    /** GeckoLib 控制器名（配合 animations/akm.animation.json） */
    public static final String GEO_CONTROLLER = "main";

    public static final String ANIM_IDLE = "idle";
    public static final String ANIM_RUN = "run";
    public static final String ANIM_RUN_FAST = "run_fast";
    public static final String ANIM_FIRE = "fire";
    public static final String ANIM_RELOAD = "reload";
    public static final String ANIM_BOLT = "bolt_pull";
    public static final String ANIM_SAFETY = "safety";

    private static final RawAnimation PLAY_IDLE = RawAnimation.begin().thenLoop(ANIM_IDLE);
    private static final RawAnimation PLAY_RUN = RawAnimation.begin().thenLoop(ANIM_RUN);
    private static final RawAnimation PLAY_RUN_FAST = RawAnimation.begin().thenLoop(ANIM_RUN_FAST);
    private static final RawAnimation PLAY_FIRE = RawAnimation.begin().thenPlay(ANIM_FIRE);
    private static final RawAnimation PLAY_RELOAD = RawAnimation.begin().thenPlay(ANIM_RELOAD);
    private static final RawAnimation PLAY_BOLT = RawAnimation.begin().thenPlay(ANIM_BOLT);
    private static final RawAnimation PLAY_SAFETY = RawAnimation.begin().thenPlay(ANIM_SAFETY);

    // ---------------------------------------------------------------- NBT（沿用旧键名，兼容老存档）
    /** 弹匣内余弹 */
    private static final String TAG_MAG = "HlcMag";
    /** 换弹结束的游戏刻（不存在 = 没在换弹） */
    private static final String TAG_RELOAD_UNTIL = "HlcReloadUntil";
    /** 连射热量 0..HEAT_MAX */
    private static final String TAG_HEAT = "HlcHeat";
    /** 最后一发的游戏刻（用于热量衰减） */
    private static final String TAG_LAST_SHOT = "HlcLastShot";

    private final AnimatableInstanceCache geoCache = GeckoLibUtil.createInstanceCache(this);

    public AkmRifleItem(Properties properties) {
        super(properties);
    }

    // ================================================================ GeckoLib
    /**
     * 动画状态机：优先级 开火 &gt; 拉栓 &gt; 换弹 &gt; 保险 &gt; 跑动 &gt; idle。
     * 全部用 {@code setAndContinue}，同一状态每 tick 重复设置不会重置进度。
     */
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, GEO_CONTROLLER, 1, state -> {
            if (!AkmAnimState.held()) return state.setAndContinue(PLAY_IDLE);
            if (AkmAnimState.firing()) return state.setAndContinue(PLAY_FIRE);
            if (AkmAnimState.bolting()) return state.setAndContinue(PLAY_BOLT);
            if (AkmAnimState.reloading()) return state.setAndContinue(PLAY_RELOAD);
            if (AkmAnimState.safety()) return state.setAndContinue(PLAY_SAFETY);
            if (AkmAnimState.sprintFast()) return state.setAndContinue(PLAY_RUN_FAST);
            if (AkmAnimState.sprinting()) return state.setAndContinue(PLAY_RUN);
            return state.setAndContinue(PLAY_IDLE);
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return geoCache;
    }

    @Override
    public void initializeClient(Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(AkmItemClientExtensions.INSTANCE);
    }

    @Override
    public AmmoType ammoType() {
        return AmmoType.RIFLE;
    }

    // ================================================================ 弹匣 / 换弹状态
    public static int mag(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0 : tag.getInt(TAG_MAG);
    }

    public static void setMag(ItemStack stack, int value) {
        stack.getOrCreateTag().putInt(TAG_MAG, Mth.clamp(value, 0, MAG_SIZE));
    }

    public static boolean reloading(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.getLong(TAG_RELOAD_UNTIL) > gameTime;
    }

    /** 换弹进度 0..1（供客户端手持动画使用）；没在换弹返回 -1 */
    public static float reloadProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null) return -1.0F;
        long until = tag.getLong(TAG_RELOAD_UNTIL);
        if (until <= gameTime) return -1.0F;
        float left = (float) (until - gameTime);
        return Mth.clamp(1.0F - left / RELOAD_TICKS, 0.0F, 1.0F);
    }

    /** 连射热量 0..1（供 HUD 显示 / 散布提示） */
    public static float heat(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0.0F : Mth.clamp(tag.getInt(TAG_HEAT) / (float) HEAT_MAX, 0.0F, 1.0F);
    }

    // ================================================================ 右键
    /** 右键：潜行时装/拆瞄具；空仓时自动换弹，否则进入瞄准（抵肩）姿态 */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.isShiftKeyDown() && hand == InteractionHand.MAIN_HAND) {
            InteractionResultHolder<ItemStack> swapped = swapSight(level, player, stack);
            if (swapped != null) return swapped;
        }
        if (mag(stack) == 0 && !reloading(stack, level.getGameTime())) {
            if (tryStartReload(level, player, stack)) {
                player.startUsingItem(hand);
                return InteractionResultHolder.success(stack);
            }
            if (!level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return InteractionResultHolder.fail(stack);
        }
        player.startUsingItem(hand);
        return InteractionResultHolder.success(stack);
    }

    /** 装/拆瞄具；返回 null 表示“这次右键不是装/拆”，交回给下游逻辑 */
    private InteractionResultHolder<ItemStack> swapSight(Level level, Player player, ItemStack stack) {
        ItemStack off = player.getOffhandItem();
        int want = Sights.fromItem(off.getItem());
        int has = Sights.sight(stack);
        if (!level.isClientSide) {
            if (want != Sights.IRON && want != has) {
                Sights.set(stack, want);
                if (!player.getAbilities().instabuild) off.shrink(1);
                player.displayClientMessage(Component.translatable("msg.hexalunar_calamity.sight_on",
                        Component.translatable(Sights.key(want))), true);
            } else if (want == Sights.IRON && has != Sights.IRON) {
                player.getInventory().placeItemBackInInventory(Sights.itemOf(has));
                Sights.set(stack, Sights.IRON);
                player.displayClientMessage(Component.translatable("msg.hexalunar_calamity.sight_off"), true);
            } else {
                return null;                    // 副手不是瞄具、枪上也没装 → 不当成装/拆
            }
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 0.55F, 1.25F);
        }
        return InteractionResultHolder.success(stack);
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    /**
     * ★ 不能返回 {@code BOW}：原版 {@code ItemInHandRenderer} 对 {@code UseAnim.BOW} 的物品
     * 会额外套一段「拉弓」位移（平移 ±0.28 格 + rotX -13.9° + rotY 35.3°/-45° + rotZ -9.8°
     * + z 轴拉伸 20%）。枪一旦被套上这套位移，就会在举枪时歪着斜、枪托被拉长，画面上
     * 就是「照门准星不在准星上、枪身斜着朝下」。{@code NONE} 才是「物品原样端在手上」。
     */
    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.NONE;
    }

    /** 换弹读条结束就自动松手（不必一直按着右键），瞄准可继续按住 */
    @Override
    public void onUseTick(Level level, LivingEntity living, ItemStack stack, int remaining) {
        if (!(living instanceof Player player) || level.isClientSide) return;
        CompoundTag tag = stack.getTag();
        if (tag != null && tag.contains(TAG_RELOAD_UNTIL) && !reloading(stack, level.getGameTime())) {
            player.releaseUsingItem();
        }
    }

    // ================================================================ 开火
    /** 左键（服务端）：全自动击发一发 */
    @Override
    public void serverFire(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        if (reloading(stack, level.getGameTime())) return;
        if (mag(stack) <= 0) {
            if (!tryStartReload(level, player, stack) && !level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return;
        }
        boolean aiming = player.isUsingItem() && player.getUseItem() == stack;
        fire(level, player, stack, aiming);
    }

    private void fire(Level level, Player player, ItemStack stack, boolean aiming) {
        setMag(stack, mag(stack) - 1);
        CompoundTag tag = stack.getOrCreateTag();
        int heat = Mth.clamp(tag.getInt(TAG_HEAT) + 1, 0, HEAT_MAX);
        tag.putInt(TAG_HEAT, heat);
        tag.putLong(TAG_LAST_SHOT, level.getGameTime());

        // 腰射散布大，瞄准压到很小；连射热量再放大散布
        float spread = (aiming ? 0.16F : 0.85F) + heat * 0.045F;

        // ★ 从**枪口**出发，朝准星落点飞（不是从眼前 0.7 格沿视线飞）：
        //   这样弹道起点在枪口、终点在准星，画面上就是「枪口 → 准星」一条直线，
        //   而不是从屏幕中间斜着飞出来。收敛距离夹在 8..96 格，近距离也不会出现大偏角。
        Vec3 muzzle = WeaponMount.akm(player, aiming, Sights.sight(stack), WeaponMount.AKM_MUZZLE);
        Vec3 dir = WeaponMount.fireDir(player, level, muzzle, 8.0D, 96.0D);

        BulletEntity bullet = new BulletEntity(level, player);
        bullet.setPos(muzzle.x, muzzle.y, muzzle.z);
        bullet.shoot(dir.x, dir.y, dir.z, aiming ? 5.0F : 4.5F, spread);
        level.addFreshEntity(bullet);

        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_SHOT.get(), SoundSource.PLAYERS, 1.1F,
                0.97F + level.random.nextFloat() * 0.08F);

        // 枪口焰（白闪 + 火星 + 枪口烟）与抛壳：位置都取模型上的实际点
        if (level instanceof ServerLevel server) {
            WeaponFx.muzzleFlash(server, muzzle, dir, aiming);
            WeaponFx.ejectCasing(server,
                    WeaponMount.akm(player, aiming, Sights.sight(stack), WeaponMount.AKM_EJECT), dir);
        }
    }

    // ================================================================ 换弹
    /** R 键（服务端）：战术换弹——弹匣未满就能补弹；满仓 / 换弹中 / 无弹则忽略 */
    @Override
    public void serverReload(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        if (level.isClientSide || reloading(stack, level.getGameTime())) return;
        if (mag(stack) >= MAG_SIZE) return;
        if (!tryStartReload(level, player, stack)) {
            player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
        }
    }

    private boolean tryStartReload(Level level, Player player, ItemStack stack) {
        if (level.isClientSide) return true;
        int available = Math.min(MAG_SIZE - mag(stack), AmmoUtil.count(player, AmmoType.RIFLE));
        if (available <= 0) return false;
        stack.getOrCreateTag().putLong(TAG_RELOAD_UNTIL, level.getGameTime() + RELOAD_TICKS);
        // 骨骼动画：客户端 AkmAnimState 读这个 NBT 选 reload 动画（退匣 → 新匣 → 释放枪机）
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_RELOAD.get(), SoundSource.PLAYERS, 1.0F,
                0.94F + level.random.nextFloat() * 0.12F);
        return true;
    }

    private void finishReload(Level level, Player player, ItemStack stack) {
        int want = MAG_SIZE - mag(stack);
        int got = AmmoUtil.takeFromBox(player, AmmoType.RIFLE, want);
        if (got < want) {
            got += AmmoUtil.takeFromInventory(player, AmmoType.RIFLE.get(), want - got);
        }
        setMag(stack, mag(stack) + got);
        player.swing(InteractionHand.MAIN_HAND);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 1.0F,
                0.98F + level.random.nextFloat() * 0.08F);
    }

    // ================================================================ tick
    @Override
    public void inventoryTick(ItemStack stack, Level level, net.minecraft.world.entity.Entity entity,
                              int slot, boolean selected) {
        super.inventoryTick(stack, level, entity, slot, selected);
        if (level.isClientSide || !(entity instanceof Player player)) return;
        CompoundTag tag = stack.getTag();
        if (tag == null) return;

        // 换弹计时结束：上弹（无需继续按住右键）
        if (tag.contains(TAG_RELOAD_UNTIL) && tag.getLong(TAG_RELOAD_UNTIL) <= level.getGameTime()) {
            tag.remove(TAG_RELOAD_UNTIL);
            finishReload(level, player, stack);
        }
        // 停火后热量自然衰减
        if (tag.getInt(TAG_HEAT) > 0
                && level.getGameTime() - tag.getLong(TAG_LAST_SHOT) >= HEAT_DECAY_IDLE_TICKS) {
            tag.putInt(TAG_HEAT, tag.getInt(TAG_HEAT) - 1);
        }
    }

    // ================================================================ 提示
    @Override
    public void appendHoverText(ItemStack stack, Level level, List<Component> tips, TooltipFlag flag) {
        tips.add(Component.translatable("tooltip.hexalunar_calamity.akm_controls")
                .withStyle(ChatFormatting.GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.range_hint", (int) Ballistics.AKM_RANGE)
                .withStyle(ChatFormatting.DARK_GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.sight_now",
                        Component.translatable(Sights.key(Sights.sight(stack))))
                .withStyle(ChatFormatting.DARK_GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.sight_mount")
                .withStyle(ChatFormatting.DARK_GRAY));
    }
}
