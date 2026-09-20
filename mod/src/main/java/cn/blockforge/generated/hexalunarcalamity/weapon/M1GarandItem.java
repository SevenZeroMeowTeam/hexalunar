package cn.blockforge.generated.hexalunarcalamity.weapon;

import cn.blockforge.generated.hexalunarcalamity.client.M1GarandAnimState;
import cn.blockforge.generated.hexalunarcalamity.client.M1GarandItemClientExtensions;
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
 * M1 加兰德（M1 Garand）半自动步枪 —— **7.62x61**、8 发漏夹、机瞄。
 *
 * <h2>模型与骨骼</h2>
 * 几何由 {@code tools/m1_garand_gen.py} 生成：{@code geo/m1_garand.geo.json}
 * （10 骨骼 / 27 方块 / 128² 分带贴图 + 流光遮罩）。
 * 骨骼名沿用 AWP / Kar98k 那一套：
 * {@code root → move → body → {barrel, handguard, bolt, casing, clip_in, magazine, trigger}}，
 * 所以动画直接复用 {@code animations/awp.animation.json}（idle / run / run_fast / fire / bolt /
 * reload 六段），需要动的部分全部程序化驱动（见 {@code M1GarandGeoModel}）。
 * 朝向：<b>枪口 = −Z（北）</b>、<b>上 = +Y</b>、<b>原点 = 握把</b>。
 *
 * <h2>★ 连射（半自动）+ 自动枪机循环</h2>
 * 按住左键每 {@link #FIRE_INTERVAL} tick 打一发；**每发都由导气杆自动完成
 * 「枪机后退 → 把空弹壳带出来抛向右上 → 复进闭锁、顶上下一发」**（{@link #BOLT_TICKS}），
 * 不需要玩家自己拉栓 —— 这就是「拉一次栓即可」：一个漏夹只拉一次栓（换弹最后那一下）。
 *
 * <h2>★ 换弹：右手把 8 发漏夹压进机匣（与 Kar98k 一样是「手动压弹」，不是换弹匣）</h2>
 * <pre>
 *   右手把漏夹从机匣上方压下去（{@link #CLIP_PUSH_TICKS}）→ 枪机释放、复进闭锁上膛（{@link #CLIP_CLOSE_TICKS}）
 *   时间轴结束时一次性消耗 {@link #MAG_SIZE} 发 7.62x61：弹仓 7 + 膛内 1
 * </pre>
 * 漏夹只能**打空后**整体压入（真枪也是这样：M1 的漏夹打空会被托弹板顶出来），
 * 所以 {@code R} 只在「弹仓空且膛内无弹」时才开始装填；**最后一发打完**时整只漏夹弹出，
 * 伴有 M1 标志性的「叮」一声（{@link #clipPing}）。
 *
 * <h2>弹药与伤害</h2>
 * 弹种是 {@link AmmoType#RIFLE_762_61}（7.62x61，与 7.62x39 / 7.62x59 / .338 都不通用）。
 * 初速 {@link #BULLET_SPEED} = 5.15 ⇒ {@code BulletEntity} 里落在 **M1 档**：
 * 伤害 **22**、爆头 ×1.5、有效射程 {@link Ballistics#M1_RANGE} 格。
 *
 * <h2>NBT</h2>
 * <pre>
 *   HlcMag / HlcChamber        漏夹余弹 0..8 / 膛内是否有弹
 *   HlcBoltUntil               自动枪机循环结束刻（不存在 = 枪机在闭锁位）
 *   HlcFireAt                  最后一次击发时刻（扣扳机动画窗口）
 *   HlcClipAt / HlcClipSeat    换弹开始刻 / 漏夹是否已经压到位（用于补一声「咔」）
 * </pre>
 */
public class M1GarandItem extends Item implements WeaponAmmo, GeoItem {

    // ---------------------------------------------------------------- 数值
    /** 漏夹容量（M1 的 8 发漏夹）—— 装填后是「弹仓 7 + 膛内 1」= 身上最多 8 发 */
    public static final int MAG_SIZE = 8;
    /** 连射节奏（tick）：按住左键每这么多 tick 一发（半自动，不用自己拉栓） */
    public static final int FIRE_INTERVAL = 10;
    /** 自动枪机循环（tick）：后退抽壳 → 抛壳 → 复进闭锁上膛 */
    public static final int BOLT_TICKS = 8;
    /** 扣扳机动画窗口（tick） */
    public static final int FIRE_TICKS = 5;
    /** 子弹初速（格/tick）：7.62x61 ⇒ BulletEntity 走「M1 档」（伤害 22） */
    public static final float BULLET_SPEED = 5.15F;

    // ---------------------------------------------------------------- 漏夹装填
    /** 右手把漏夹压进机匣（tick） */
    public static final int CLIP_PUSH_TICKS = 22;
    /** 漏夹到位后枪机释放、复进闭锁上膛（tick）—— 也就是「拉一次栓」那一下 */
    public static final int CLIP_CLOSE_TICKS = 10;
    /** 换弹总时长 */
    public static final int CLIP_TOTAL_TICKS = CLIP_PUSH_TICKS + CLIP_CLOSE_TICKS;

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
    private static final String TAG_BOLT_UNTIL = "HlcBoltUntil";
    private static final String TAG_FIRE_AT = "HlcFireAt";
    /** 换弹：开始刻 + 漏夹是否已压到位（压到位那一下补一声「咔」） */
    private static final String TAG_CLIP_AT = "HlcClipAt";
    private static final String TAG_CLIP_SEAT = "HlcClipSeat";

    private final AnimatableInstanceCache geoCache = GeckoLibUtil.createInstanceCache(this);

    public M1GarandItem(Properties properties) {
        super(properties);
    }

    // ================================================================ GeckoLib
    /**
     * 动画状态机：优先级 装填 &gt; 枪机循环 &gt; 扣扳机 &gt; 跑动 &gt; idle。
     * 全部 {@code setAndContinue}，同一状态每 tick 重复设置不会重置进度。
     */
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, GEO_CONTROLLER, 1, state -> {
            if (!M1GarandAnimState.held()) return state.setAndContinue(PLAY_IDLE);
            long now = M1GarandAnimState.now();
            ItemStack stack = M1GarandAnimState.heldStack();
            if (stack != null && loading(stack, now)) return state.setAndContinue(PLAY_RELOAD);
            if (stack != null && bolting(stack, now)) return state.setAndContinue(PLAY_BOLT);
            if (stack != null && fireWindow(stack, now) >= 0.0F) return state.setAndContinue(PLAY_FIRE);
            if (M1GarandAnimState.sprintFast()) return state.setAndContinue(PLAY_RUN_FAST);
            if (M1GarandAnimState.sprinting()) return state.setAndContinue(PLAY_RUN);
            return state.setAndContinue(PLAY_IDLE);
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return geoCache;
    }

    @Override
    public void initializeClient(Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(M1GarandItemClientExtensions.INSTANCE);
    }

    /** 7.62x61：加兰德专用（与 7.62x39 / 7.62x59 / .338 都不通用） */
    @Override
    public AmmoType ammoType() {
        return AmmoType.RIFLE_762_61;
    }

    // ================================================================ 漏夹 / 膛内弹 / 计时
    public static int mag(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null ? 0 : Mth.clamp(tag.getInt(TAG_MAG), 0, MAG_SIZE);
    }

    public static void setMag(ItemStack stack, int value) {
        stack.getOrCreateTag().putInt(TAG_MAG, Mth.clamp(value, 0, MAG_SIZE));
    }

    /** 膛内是否有弹 */
    public static boolean chambered(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.getBoolean(TAG_CHAMBER);
    }

    public static void setChambered(ItemStack stack, boolean value) {
        stack.getOrCreateTag().putBoolean(TAG_CHAMBER, value);
    }

    /** 弹仓 + 膛内都没有弹（= 漏夹已经打空弹出来了） */
    public static boolean empty(ItemStack stack) {
        return mag(stack) == 0 && !chambered(stack);
    }

    /** 空仓挂机：没在装填、枪机也没在动，且漏夹已空 ⇒ 枪机停在后位（M1 打空的标志样子） */
    public static boolean boltHoldOpen(ItemStack stack, long gameTime) {
        return empty(stack) && !loading(stack, gameTime) && !bolting(stack, gameTime);
    }

    // ---------------------------------------------------------------- 自动枪机循环
    public static boolean bolting(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.contains(TAG_BOLT_UNTIL) && tag.getLong(TAG_BOLT_UNTIL) > gameTime;
    }

    /** 枪机循环进度 0..1；没在动返回 -1 */
    public static float boltProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_BOLT_UNTIL)) return -1.0F;
        long left = tag.getLong(TAG_BOLT_UNTIL) - gameTime;
        if (left <= 0L || left > BOLT_TICKS) return -1.0F;
        return Mth.clamp(1.0F - left / (float) BOLT_TICKS, 0.0F, 1.0F);
    }

    /** 扣扳机动画窗口进度 0..1；没在窗口内返回 -1 */
    public static float fireWindow(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_FIRE_AT)) return -1.0F;
        long age = gameTime - tag.getLong(TAG_FIRE_AT);
        if (age < 0 || age > FIRE_TICKS) return -1.0F;
        return age / (float) FIRE_TICKS;
    }

    // ---------------------------------------------------------------- 漏夹装填
    /** 正在换弹（压漏夹 + 枪机释放，全过程） */
    public static boolean loading(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_CLIP_AT)) return false;
        return gameTime - tag.getLong(TAG_CLIP_AT) < CLIP_TOTAL_TICKS;
    }

    /** 换弹总进度 0..1；没在换弹返回 -1 */
    public static float reloadProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_CLIP_AT)) return -1.0F;
        long elapsed = gameTime - tag.getLong(TAG_CLIP_AT);
        if (elapsed < 0L || elapsed >= CLIP_TOTAL_TICKS) return -1.0F;
        return Mth.clamp(elapsed / (float) CLIP_TOTAL_TICKS, 0.0F, 1.0F);
    }

    /**
     * **压漏夹**进度 0..1（右手把漏夹按下去的量）；不在压漏夹那一段返回 -1。
     * 模型里漏夹从机匣上方落进弹仓、右手跟着一起往下按，都按它算。
     */
    public static float clipProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_CLIP_AT)) return -1.0F;
        long elapsed = gameTime - tag.getLong(TAG_CLIP_AT);
        if (elapsed < 0L || elapsed >= CLIP_PUSH_TICKS) return -1.0F;
        return elapsed / (float) CLIP_PUSH_TICKS;
    }

    /**
     * **枪机释放**进度 0..1（压完漏夹、枪机复进闭锁 —— 「拉一次栓即可」的就是这一下）；
     * 不在那一段返回 -1。
     */
    public static float boltReleaseProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(TAG_CLIP_AT)) return -1.0F;
        long elapsed = gameTime - tag.getLong(TAG_CLIP_AT) - CLIP_PUSH_TICKS;
        if (elapsed < 0L || elapsed >= CLIP_CLOSE_TICKS) return -1.0F;
        return elapsed / (float) CLIP_CLOSE_TICKS;
    }

    // ================================================================ 右键（抵肩瞄准，机瞄）
    /** 右键：进入瞄准；漏夹打空则先压漏夹 */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        long now = level.getGameTime();
        if (empty(stack) && !loading(stack, now) && !bolting(stack, now)) {
            if (tryStartLoad(level, player, stack)) {
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

    /** 换弹结束就自动松手（不必一直按着右键），瞄准可继续按住 */
    @Override
    public void onUseTick(Level level, LivingEntity living, ItemStack stack, int remaining) {
        if (!(living instanceof Player player) || level.isClientSide) return;
        CompoundTag tag = stack.getTag();
        if (tag != null && tag.contains(TAG_CLIP_AT) && !loading(stack, level.getGameTime())) {
            player.releaseUsingItem();
        }
    }

    // ================================================================ 开火
    /**
     * 左键（服务端）：**连射**——按住时客户端按 {@link #FIRE_INTERVAL} 的节奏发请求，
     * 每发只要求「膛内有弹」；打完由导气杆自动完成枪机循环与抛壳。
     */
    @Override
    public void serverFire(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        long now = level.getGameTime();
        if (loading(stack, now) || bolting(stack, now)) return;      // 装填 / 枪机循环中不能击发
        if (!chambered(stack)) {
            // 空膛：漏夹里还有弹就自动上膛（拉一下枪机），没弹就压漏夹 / 空响
            if (mag(stack) > 0) {
                startBolt(level, player, stack);
            } else if (!tryStartLoad(level, player, stack) && !level.isClientSide) {
                player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
            }
            return;
        }
        boolean aiming = player.isUsingItem() && player.getUseItem() == stack;
        fire(level, player, stack, aiming);
        setChambered(stack, false);
        startBolt(level, player, stack);                            // 导气杆自动抽壳抛壳 + 复进上膛
    }

    private void fire(Level level, Player player, ItemStack stack, boolean aiming) {
        stack.getOrCreateTag().putLong(TAG_FIRE_AT, level.getGameTime());

        // 半自动步枪：腰射散布偏大，抵肩机瞄几乎指哪打哪
        float spread = aiming ? 0.12F : 1.05F;

        Vec3 muzzle = WeaponMount.m1Garand(player, aiming, WeaponMount.M1_MUZZLE);
        Vec3 dir = WeaponMount.fireDir(player, level, muzzle, 8.0D, aiming ? 40.0D : 24.0D);

        BulletEntity bullet = new BulletEntity(level, player);
        bullet.setPos(muzzle.x, muzzle.y, muzzle.z);
        bullet.shoot(dir.x, dir.y, dir.z, BULLET_SPEED, spread);
        level.addFreshEntity(bullet);

        // 音效复用 AWP 的枪声（全曲目唯一的大口径枪声），音调再高一点
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AWP_SHOT.get(), SoundSource.PLAYERS, 1.15F,
                1.12F + level.random.nextFloat() * 0.06F);

        if (level instanceof ServerLevel server) {
            WeaponFx.muzzleFlash(server, muzzle, dir, aiming);
            WeaponFx.ejectCasing(server,
                    WeaponMount.m1Garand(player, aiming, WeaponMount.M1_EJECT), dir);
        }
    }

    /** 自动枪机循环：后退抽壳 → 复进闭锁（抛壳动画由 {@code M1GarandGeoModel} 按进度驱动） */
    private void startBolt(Level level, Player player, ItemStack stack) {
        if (level.isClientSide) return;
        stack.getOrCreateTag().putLong(TAG_BOLT_UNTIL, level.getGameTime() + BOLT_TICKS);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 0.34F,
                1.28F + level.random.nextFloat() * 0.06F);
    }

    /**
     * 枪机循环结束：把漏夹里下一发顶上膛（弹仓 −1、膛内 +1）；
     * **漏夹空了 ⇒ 整只漏夹弹出机匣**，响一声 M1 标志性的「叮」。
     */
    private void finishBolt(Level level, Player player, ItemStack stack) {
        if (mag(stack) > 0) {
            setMag(stack, mag(stack) - 1);
            setChambered(stack, true);
        } else {
            setChambered(stack, false);
            clipPing(level, player);                                // ★ 最后一发：漏夹弹出（叮）
        }
    }

    /** 漏夹弹出的「叮」（公用音频里没有专门的 ping，用拉栓音效调高音调代替） */
    private static void clipPing(Level level, Player player) {
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 0.55F,
                1.92F + level.random.nextFloat() * 0.05F);
    }

    // ================================================================ 压漏夹
    /**
     * R 键（服务端）：压漏夹。**只在漏夹打空时**才能压（真枪如此：漏夹要从上面压进去，
     * 打空后托弹板才把它顶出来）。
     */
    @Override
    public void serverReload(Player player, ItemStack stack, InteractionHand hand) {
        Level level = player.level();
        if (level.isClientSide) return;
        long now = level.getGameTime();
        if (loading(stack, now) || bolting(stack, now)) return;
        if (!empty(stack)) return;                                  // 还有弹：不换（M1 不能补弹）
        if (!tryStartLoad(level, player, stack)) {
            player.playSound(ModSounds.EMPTY.get(), 0.6F, 1.0F);
        }
    }

    private boolean tryStartLoad(Level level, Player player, ItemStack stack) {
        if (level.isClientSide) return true;
        if (AmmoUtil.count(player, AmmoType.RIFLE_762_61) <= 0) return false;
        CompoundTag tag = stack.getOrCreateTag();
        tag.putLong(TAG_CLIP_AT, level.getGameTime());
        tag.putBoolean(TAG_CLIP_SEAT, false);
        // 掏漏夹的动静（AWP 那条换弹音频正好是「手在枪上忙活」的声音）
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AWP_RELOAD.get(), SoundSource.PLAYERS, 0.85F,
                1.15F + level.random.nextFloat() * 0.06F);
        return true;
    }

    /** 漏夹压到位：一声「咔」（真正消耗弹药在 {@link #finishLoad}） */
    private void clipSeat(Level level, Player player, ItemStack stack) {
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 0.5F,
                1.18F + level.random.nextFloat() * 0.06F);
    }

    /** 换弹收尾：一次性吃掉一整只漏夹（8 发），枪机释放上膛一发（弹仓 7 + 膛内 1） */
    private void finishLoad(Level level, Player player, ItemStack stack) {
        int want = MAG_SIZE - mag(stack);
        int got = want <= 0 ? 0 : AmmoUtil.takeFromBox(player, AmmoType.RIFLE_762_61, want);
        if (got < want) {
            got += AmmoUtil.takeFromInventory(player, AmmoType.RIFLE_762_61.get(), want - got);
        }
        setMag(stack, mag(stack) + got);
        CompoundTag tag = stack.getOrCreateTag();
        tag.remove(TAG_CLIP_AT);
        tag.remove(TAG_CLIP_SEAT);
        if (mag(stack) > 0) {                                       // 枪机复进，顶一发进膛
            setMag(stack, mag(stack) - 1);
            setChambered(stack, true);
        }
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                ModSounds.BOLT.get(), SoundSource.PLAYERS, 1.0F,
                1.02F + level.random.nextFloat() * 0.05F);
        player.swing(InteractionHand.MAIN_HAND);
    }

    /** 中断换弹（漏夹还没压进去、弹药也还没扣）：只收尾，不掉弹 */
    private void cancelLoad(Level level, Player player, ItemStack stack, boolean playSfx) {
        CompoundTag tag = stack.getTag();
        if (tag == null) return;
        tag.remove(TAG_CLIP_AT);
        tag.remove(TAG_CLIP_SEAT);
        if (playSfx) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    ModSounds.AKM_BOLT.get(), SoundSource.PLAYERS, 0.5F, 1.1F);
        }
    }

    // ================================================================ tick
    @Override
    public void inventoryTick(ItemStack stack, Level level, net.minecraft.world.entity.Entity entity,
                              int slot, boolean selected) {
        super.inventoryTick(stack, level, entity, slot, selected);
        if (level.isClientSide || !(entity instanceof Player player)) return;
        CompoundTag tag = stack.getTag();
        if (tag == null) return;
        long now = level.getGameTime();

        // ---- 换弹：压漏夹 → （咔）→ 枪机释放上膛 ----
        if (tag.contains(TAG_CLIP_AT)) {
            if (!selected) {
                cancelLoad(level, player, stack, false);            // 换走了 = 停下
            } else {
                long elapsed = now - tag.getLong(TAG_CLIP_AT);
                if (elapsed >= CLIP_TOTAL_TICKS) {
                    finishLoad(level, player, stack);
                } else if (elapsed >= CLIP_PUSH_TICKS && !tag.getBoolean(TAG_CLIP_SEAT)) {
                    tag.putBoolean(TAG_CLIP_SEAT, true);            // 漏夹到位那一下的「咔」
                    clipSeat(level, player, stack);
                }
            }
        }

        if (tag.contains(TAG_BOLT_UNTIL) && tag.getLong(TAG_BOLT_UNTIL) <= now) {
            tag.remove(TAG_BOLT_UNTIL);
            finishBolt(level, player, stack);
        }
    }

    // ================================================================ 提示
    @Override
    public void appendHoverText(ItemStack stack, Level level, List<Component> tips, TooltipFlag flag) {
        tips.add(Component.translatable("tooltip.hexalunar_calamity.m1_garand_controls")
                .withStyle(ChatFormatting.GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.range_hint",
                (int) Ballistics.M1_RANGE).withStyle(ChatFormatting.DARK_GRAY));
        tips.add(Component.translatable("tooltip.hexalunar_calamity.m1_garand_ammo",
                        mag(stack), MAG_SIZE, chambered(stack) ? 1 : 0)
                .withStyle(ChatFormatting.DARK_GRAY));
    }
}
