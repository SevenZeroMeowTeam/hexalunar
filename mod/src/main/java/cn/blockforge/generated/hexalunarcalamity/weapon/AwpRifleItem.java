package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.client.AwpAnimState;
import cn.blockforge.generated.hexalunarcalamity.client.AwpItemClientExtensions;
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
import net.minecraft.world.entity.Entity;
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
 * AWP 栓动狙击枪（.338，8 倍镜）。
 *
 * <h2>模型与骨骼</h2>
 * 几何由 {@code tools/awp_gen.py} 从参考包 {@code 模型/AWP_Printstream_Minecraft} 转换并微调而来
 * （13 骨骼 / 58 方块 / 512² 逐面 UV 贴图，密度 19 像素每单位）。骨骼：
 * {@code root → move → body → barrel → bipod / scope → scope_adjust / scope_elev / scope_wind /
 * magazine / bolt / trigger / casing}。<br>
 * 朝向：<b>枪口 = -Z（北）</b>、<b>上 = +Y</b>、<b>原点 = 机匣中心</b>、<b>握把在 move 骨骼</b>。
 *
 * <h2>操作</h2>
 * <ul>
 *   <li>左键：击发（枪机闭锁且有膛内弹才响）；每发后自动拉栓抛壳</li>
 *   <li>右键按住：抵肩瞄准，进 8 倍镜（屏幕中心出镜筒遮罩 + 视场角收窄到 1/8）</li>
 *   <li>R 键：换弹（换 5 发短弹匣，顺带上膛一发）</li>
 * </ul>
 *
 * <h2>栓动逻辑（都在 NBT 里，客户端读同一份）</h2>
 * <pre>
 *   TAG_MAG          弹匣内余弹 0..5
 *   TAG_CHAMBER      膛内是否有弹（0/1）
 *   TAG_RELOAD_UNTIL 换弹结束刻（不存在 = 没在换弹）
 *   TAG_BOLT_UNTIL   拉栓结束刻（不存在 = 没在拉栓）
 *   TAG_FIRE_AT      最后一次击发时刻（扣扳机动画窗口）
 * </pre>
 * 击发流程：{@code chamber=true → 打出去、chamber=false、开始拉栓}。
 * 拉栓结束时 {@code mag>0 ? (mag--, chamber=true) : chamber=false} —— 也就是「枪机把弹壳退出来、
 * 再把下一发顶上膛」，和 {@code animation.awp.bolt} 里弹壳被带出并翻滚抛出是同一段时间轴。
 *
 * <p>拉栓前留了 {@link #BOLT_DELAY} 帧的停顿：先扣扳机（右手还在握把上），
 * 再抬手去抓拉机柄 —— 拉栓音效也就比枪声晚这么多帧响（见 {@code TAG_BOLT_SFX}）。
 */
public class AwpRifleItem extends Item implements WeaponAmmo, GeoItem {

    // ---------------------------------------------------------------- 数值
    /** 弹匣容量（AWP 的 5 发短弹匣） */
    public static final int MAG_SIZE = 5;
    /** 换弹耗时（tick） */
    public static final int RELOAD_TICKS = 44;
    /** 拉栓耗时（tick）：抬起拉机柄 → 抽壳抛壳 → 推回闭锁 */
    public static final int BOLT_TICKS = 22;
    /** 击发到抬手拉栓之间的停顿（tick）：这段时间右手还在握把上扣扳机，拉栓音效也晚这么多帧响 */
    public static final int BOLT_DELAY = 6;
    /** 一次完整的栓动循环（击发 → 拉栓 → 可再击发） */
    public static final int CYCLE_TICKS = BOLT_DELAY + BOLT_TICKS;
    /** 扣扳机动画窗口（tick），对应 animation.awp.fire 的 0.35s */
    public static final int FIRE_TICKS = 7;
    /** 子弹初速（格/tick）；BulletEntity 用 >5.5 认作狙击弹（更高的伤害与射程） */
    public static final float BULLET_SPEED = 6.2F;
    /** 8 倍镜：开镜时视场角缩到 1/8 */
    public static final float SCOPE_ZOOM = 8.0F;

    // ---------------------------------------------------------------- 动画
    public static final String GEO_CONTROLLER = "main";

    private static final RawAnimation PLAY_IDLE = RawAnimation.begin().thenLoop("idle");
    private static final RawAnimation PLAY_RUN = RawAnimation.begin().thenLoop("run");
    private static final RawAnimation PLAY_RUN_FAST = RawAnimation.begin().thenLoop("run_fast");
    private static final RawAnimation PLAY_FIRE = RawAnimation.begin().thenPlay("fire");
    private static final RawAnimation PLAY_BOLT = RawAnimation.begin().thenPlay("bolt");
    private static final RawAnimation PLAY_RELOAD = RawAnimation.begin().thenPlay("reload");

    // ---------------------------------------------------------------- NBT
    private static final String TAG_MAG = "HlcMag";
    private static final String TAG_CHAMBER = "HlcChamber";
    private static final String TAG_RELOAD_UNTIL = "HlcReloadUntil";
    private static final String TAG_BOLT_UNTIL = "HlcBoltUntil";
    /** 拉栓音效该在第几帧响（拉栓本体开始那一刻，而不是击发那一刻） */
    private static final String TAG_BOLT_SFX = "HlcBoltSfx";
    private static final String TAG_FIRE_AT = "HlcFireAt";

    private final AnimatableInstanceCache geoCache = GeckoLibUtil.createInstanceCache(this);

    public AwpRifleItem(Properties properties) {
        super(properties);
    }

    // ================================================================ GeckoLib
    /**
     * 动画状态机：优先级 拉栓 &gt; 换弹 &gt; 扣扳机 &gt; 跑动 &gt; idle。
     * 全部 {@code setAndContinue}，同一状态每 tick 重复设置不会重置进度。
     */
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, GEO_CONTROLLER, 1, state -> {
            if (!AwpAnimState.held()) return state.setAndContinue(PLAY_IDLE);
            long now = AwpAnimState.now();
            ItemStack stack = AwpAnimState.heldStack();
            if (stack != null && bolting(stack, now)) return state.setAndContinue(PLAY_BOLT);
            if (stack != null && reloading(stack, now)) return state.setAndContinue(PLAY_RELOAD);
            if (stack != null && fireWindow(stack, now) >= 0.0F) return state.setAndContinue(PLAY_FIRE);
            if (AwpAnimState.sprintFast()) return state.setAndContinue(PLAY_RUN_FAST);
            if (AwpAnimState.sprinting()) return state.setAndContinue(PLAY_RUN);
            return state.setAndContinue(PLAY_IDLE);
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return geoCache;
    }

    @Override
    public void initializeClient(Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(AwpItemClientExtensions.INSTANCE);
    }

    @Override
    public AmmoType ammoType() {
        return AmmoType.SNIPER;
    }

    // ================================================================ 弹匣 / 膛内弹 / 计时
    public static int mag(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0 : Mth.clamp(tag.getInt(TAG_MAG), 0, MAG_SIZE);
    }

    public static void setMag(ItemStack stack, int value) {
        stack.getOrCreateTag().putInt(TAG_MAG, Mth.clamp(value, 0, MAG_SIZE));
    }

    /** 膛内是否有弹（没有就打不响，得先拉栓） */
    public static boolean chambered(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.getBoolean(TAG_CHAMBER);
    }

    public static void setChambered(ItemStack stack, boolean value) {
        stack.getOrCreateTag().putBoolean(TAG_CHAMBER, value);
    }

    public static boolean reloading(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.contains(TAG_RELOAD_UNTIL) && tag.getLong(TAG_RELOAD_UNTIL) > gameTime;
    }

    /** 换弹进度 0..1；没在换弹返回 -1 */
    public static float reloadProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_RELOAD_UNTIL)) return -1.0F;
        long until = tag.getLong(TAG_RELOAD_UNTIL);
        if (until <= gameTime) return -1.0F;
        return Mth.clamp(1.0F - (until - gameTime) / (float) RELOAD_TICKS, 0.0F, 1.0F);
    }

    public static boolean bolting(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.contains(TAG_BOLT_UNTIL) && tag.getLong(TAG_BOLT_UNTIL) > gameTime;
    }

    /**
     * 拉栓进度 0..1；没在拉栓（含「击发后、还没抬手」的停顿）返回 -1
     * （枪机位移 / 抛壳轨迹 / 右手抓拉机柄都按它算）。
     */
    public static float boltProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_BOLT_UNTIL)) return -1.0F;
        long left = tag.getLong(TAG_BOLT_UNTIL) - gameTime;
        if (left <= 0L || left > BOLT_TICKS) return -1.0F;   // 停顿期间：枪机不动、手还在握把上
        return Mth.clamp(1.0F - left / (float) BOLT_TICKS, 0.0F, 1.0F);
    }

    /** 扣扳机动画窗口进度 0..1；没在窗口内返回 -1 */
    public static float fireWindow(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_FIRE_AT)) return -1.0F;
        long at = tag.getLong(TAG_FIRE_AT);
        long age = gameTime - at;
        if (age < 0 || age > FIRE_TICKS) return -1.0F;
        return age / (float) FIRE_TICKS;
    }

    // ================================================================ 右键（抵肩瞄准）
    /** 右键：进入瞄准（8 倍镜）；弹匣打空则先换弹 */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        long now = level.getGameTime();
        if (mag(stack) == 0 && !chambered(stack) && !reloading(stack, now) && !bolting(stack, now)) {
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

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    /** 枪一律 {@code NONE}：{@code BOW} 会被原版套一段「拉弓」位移，枪会歪着斜、枪托被拉长 */
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
    /** 左键（服务端）：栓动——必须膛内有弹；打完自动拉栓抛壳 */
    @Override
    public void serverFire(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        long now = level.getGameTime();
        if (reloading(stack, now) || bolting(stack, now)) return;      // 换弹/拉栓中不能击发
        if (!chambered(stack)) {
            // 空膛：还有弹就拉一下栓上膛（没击发，不用等扣扳机的停顿），没弹就换弹/空响
            if (mag(stack) > 0) {
                startBolt(level, player, stack, 0);
            } else if (!tryStartReload(level, player, stack) && !level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return;
        }
        boolean aiming = player.isUsingItem() && player.getUseItem() == stack;
        fire(level, player, stack, aiming);
        setChambered(stack, false);
        startBolt(level, player, stack, BOLT_DELAY);                // 先扣扳机，再自动拉栓抛壳
    }

    private void fire(Level level, Player player, ItemStack stack, boolean aiming) {
        stack.getOrCreateTag().putLong(TAG_FIRE_AT, level.getGameTime());

        // 栓动狙击：腰射散布很大，抵肩 + 8 倍镜几乎指哪打哪
        float spread = aiming ? 0.06F : 1.15F;

        Vec3 muzzle = WeaponMount.awp(player, aiming, WeaponMount.AWP_MUZZLE);
        Vec3 dir = WeaponMount.fireDir(player, level, muzzle, 8.0D, aiming ? 40.0D : 24.0D);

        BulletEntity bullet = new BulletEntity(level, player);
        bullet.setPos(muzzle.x, muzzle.y, muzzle.z);
        bullet.shoot(dir.x, dir.y, dir.z, BULLET_SPEED, spread);
        level.addFreshEntity(bullet);

        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AWP_SHOT.get(), SoundSource.PLAYERS, 1.25F,
                0.97F + level.random.nextFloat() * 0.06F);

        if (level instanceof ServerLevel server) {
            WeaponFx.muzzleFlash(server, muzzle, dir, aiming);
            WeaponFx.ejectCasing(server,
                    WeaponMount.awp(player, aiming, WeaponMount.AWP_EJECT), dir);
        }
    }

    /**
     * 开始栓动：{@code delay} 帧后枪机后退、弹壳被带出翻滚抛出（客户端按进度驱动骨骼）。
     *
     * @param delay 先让右手留在握把上扣扳机的帧数；拉栓音效同样晚这么多帧响
     */
    private void startBolt(Level level, Player player, ItemStack stack, int delay) {
        if (level.isClientSide) return;
        stack.getOrCreateTag().putLong(TAG_BOLT_UNTIL,
                level.getGameTime() + delay + BOLT_TICKS);
        if (delay <= 0) {
            boltSound(level, player);
        } else {
            stack.getOrCreateTag().putLong(TAG_BOLT_SFX, level.getGameTime() + delay);
        }
    }

    /** 拉栓上膛音效（用户提供的 `模型/拉栓上膛.ogg`，与 AKM 共用） */
    private static void boltSound(Level level, Player player) {
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.BOLT.get(), SoundSource.PLAYERS, 0.95F,
                0.92F + level.random.nextFloat() * 0.05F);
    }

    /** 拉栓结束：枪机把下一发顶上膛（消耗弹匣一发），没弹就空膛 */
    private void finishBolt(Level level, Player player, ItemStack stack) {
        if (mag(stack) > 0) {
            setMag(stack, mag(stack) - 1);
            setChambered(stack, true);
        } else {
            setChambered(stack, false);
        }
    }

    // ================================================================ 换弹
    /** R 键（服务端）：换弹匣（满仓 / 换弹中 / 拉栓中则忽略） */
    @Override
    public void serverReload(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        if (level.isClientSide) return;
        long now = level.getGameTime();
        if (reloading(stack, now) || bolting(stack, now)) return;
        if (mag(stack) >= MAG_SIZE && chambered(stack)) return;
        if (!tryStartReload(level, player, stack)) {
            player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
        }
    }

    private boolean tryStartReload(Level level, Player player, ItemStack stack) {
        if (level.isClientSide) return true;
        int want = MAG_SIZE - mag(stack);
        if (want <= 0 && chambered(stack)) return false;
        if (AmmoUtil.count(player, AmmoType.SNIPER) <= 0) return false;
        stack.getOrCreateTag().putLong(TAG_RELOAD_UNTIL, level.getGameTime() + RELOAD_TICKS);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AWP_RELOAD.get(), SoundSource.PLAYERS, 1.0F,
                0.98F + level.random.nextFloat() * 0.06F);
        return true;
    }

    private void finishReload(Level level, Player player, ItemStack stack) {
        int want = MAG_SIZE - mag(stack);
        int got = want <= 0 ? 0 : AmmoUtil.takeFromBox(player, AmmoType.SNIPER, want);
        if (got < want) {
            got += AmmoUtil.takeFromInventory(player, AmmoType.SNIPER.get(), want - got);
        }
        setMag(stack, mag(stack) + got);
        setChambered(stack, true);                 // 顺手推一发上膛
        player.swing(InteractionHand.MAIN_HAND);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.BOLT.get(), SoundSource.PLAYERS, 1.0F,
                0.86F + level.random.nextFloat() * 0.06F);
    }

    // ================================================================ tick
    @Override
    public void inventoryTick(ItemStack stack, Level level, net.minecraft.world.entity.Entity entity,
                              int slot, boolean selected) {
        super.inventoryTick(stack, level, entity, slot, selected);
        if (level.isClientSide || !(entity instanceof Player player)) return;
        CompoundTag tag = stack.getTag();
        if (tag == null) return;

        if (tag.contains(TAG_RELOAD_UNTIL) && tag.getLong(TAG_RELOAD_UNTIL) <= level.getGameTime()) {
            tag.remove(TAG_RELOAD_UNTIL);
            finishReload(level, player, stack);
        }
        if (tag.contains(TAG_BOLT_UNTIL) && tag.getLong(TAG_BOLT_UNTIL) <= level.getGameTime()) {
            tag.remove(TAG_BOLT_UNTIL);
            finishBolt(level, player, stack);
        }
        // 拉栓音效的定时（比枪声晚 BOLT_DELAY 帧）
        if (tag.contains(TAG_BOLT_SFX) && tag.getLong(TAG_BOLT_SFX) <= level.getGameTime()) {
            tag.remove(TAG_BOLT_SFX);
            boltSound(level, player);
        }
    }

    // ================================================================ 提示
    @Override
    public void appendHoverText(ItemStack stack, Level level, List<Component> tips, TooltipFlag flag) {
        tips.add(Component.translatable("tooltip.hexalunar_calamity.awp_controls")
                .withStyle(ChatFormatting.GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.range_hint", (int) Ballistics.AWP_RANGE)
                .withStyle(ChatFormatting.DARK_GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.awp_ammo",
                        mag(stack), MAG_SIZE, chambered(stack) ? 1 : 0)
                .withStyle(ChatFormatting.DARK_GRAY));
    }
}
