package cn.blockforge.generated.hexalunarcalamity.client;

import cn.blockforge.generated.hexalunarcalamity.HexaLunarCalamity;
import cn.blockforge.generated.hexalunarcalamity.weapon.AwpRifleItem;
import cn.blockforge.generated.hexalunarcalamity.weapon.WeaponMount;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import software.bernie.geckolib.core.animatable.model.CoreGeoBone;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;

/**
 * AWP 的 GeckoLib 模型定义 + 程序化骨骼细节。
 *
 * <h2>资源</h2>
 * <ul>
 *   <li>几何 {@code geo/awp.geo.json}：**18 骨骼 / 180 方块 / 512² 逐面 UV**
 *       （v2 几何，由 {@code tools/awp_v2.py} 生成：空心圆管枪管 + 空心镜筒 + 5 发可见子弹）</li>
 *   <li>贴图 {@code textures/models/awp_geo.png}（+ {@code _glowmask} 供流光层）</li>
 *   <li>动画 {@code animations/awp.animation.json}（控制器 {@code main}，**全部空通道**）</li>
 * </ul>
 *
 * <h2>骨骼（18 根，v2）</h2>
 * {@code root → move → body →{ barrel → bipod, scope →{ scope_adjust / scope_elev / scope_wind }}}
 * + {@code magazine → mag_r1..mag_r4}、{@code round_in}、{@code bolt}、{@code trigger}、{@code casing}}。
 * 朝向：枪口 = -Z、上 = +Y、原点 = 机匣中心。
 * <ul>
 *   <li>{@code magazine} = 弹匣盒（换弹时整盒掉下去/升上来）</li>
 *   <li>{@code mag_r1..mag_r4} = 弹匣里往下第 2..5 发；{@code round_in} = 最上一发（要上膛那发）</li>
 *   <li>{@code bolt} = 整个枪机（八棱机体 + 右侧下弯拉机柄 + 球头）</li>
 *   <li>{@code casing} = 弹膛里那枚空弹壳（只在拉栓窗口里显示，抛完自动藏）</li>
 * </ul>
 *
 * <h2>★★ 持枪与动作数值来源（r114：照 TaCZ 的 {@code ai_awp}）</h2>
 * TaCZ 里没有单独的 {@code awp}，只有**精密国际 {@code ai_awp}**（AWP / AWM 同枪族），
 * 它的 {@code ai_awp_display.json} 写着 {@code use_default_animation: "rifle"}
 * （= 通用步枪持枪那一套）+ {@code iron_zoom 1.5} / {@code zoom_model_fov 35} /
 * {@code state_machine: manual_action}（栓动）+ {@code bolt_shell_ejecting_time 0.4}；
 * 逐帧动作在 {@code animations/ai_awp.animation.json}（已导出到 {@code build/ai_awp/}，
 * 用 {@code tools/_ai_awp_times.py} 看）。本类取的是：
 * <ul>
 *   <li>{@code bolt}：拉机柄转 **60°**（→ {@link #BOLT_LIFT} 62°）、整枪侧倾 **11.87°**
 *       （→ {@link #BOLT_ROLL}）、微抬 **4.59°**（→ {@link #BOLT_PITCH}）、下沉 −0.80
 *       （按枪长比例折半 → {@link #BOLT_SINK}）</li>
 *   <li>{@code shoot}：枪口上抬 **7.94°** → {@link WeaponHandGrip#AWP_FIRE_PITCH} 6.0
 *       （另有一路镜头后坐，所以不取满）</li>
 *   <li>{@code reload_tactical} / {@code reload_empty}：弹匣**翻转着**脱出
 *       （它的 rotation Z 到 −131°）→ {@link #MAG_TILT} 45°</li>
 * </ul>
 *
 * <h2>为什么换弹/拉栓/抛壳要程序化推骨骼</h2>
 * 动画 JSON 是「固定秒数」，而实际时长由物品 NBT 的 {@code RELOAD_TICKS / BOLT_TICKS} 决定。
 * 按 NBT 进度推骨骼，读条和动作永远对得上；弹壳也就不用「计时槽」，
 * 直接由 {@code boltProgress} 算出「被枪机带出 → 边翻边抛向右上方」这条轨迹。
 */
public class AwpGeoModel extends GeoModel<AwpRifleItem> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "geo/awp.geo.json");
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "textures/models/awp_geo.png");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(HexaLunarCalamity.MOD_ID, "animations/awp.animation.json");

    /**
     * 当前这一遍渲染是不是「拿在手上」（第一/第三人称；由 {@link AwpGeoRenderer} 设入）。
     * GeckoLib 的 {@code setCustomAnimations} 对 GUI 图标 / 掉落物 / 展示框一样会跑，
     * 不判断的话「举枪位移 + 后坐 + 抛壳」会跑到物品栏图标上。
     */
    static boolean handPass = false;

    /** 开火后坐：**r84 起不再推枪**（改成只推镜头，见 ClientEvents.applyRecoilKick） */
    private static final float KICK_BACK_UNUSED = 1.9F;

    /** move 骨骼 pivot（geo 里的值）—— 第一人称手臂靠它把骨骼位移换算成相机空间 */
    private static final float MOVE_PX = 0.0F;
    private static final float MOVE_PY = -1.0725F;
    private static final float MOVE_PZ = 1.305F;

    /**
     * 当前这一帧的枪本体变换（给第一人称手臂用，见 {@link GunFrame} / {@link WeaponArms}）。
     *
     * <p>手臂在 {@code RenderHandEvent} 里画，**比物品渲染早**，靠「渲染时捕获」只能拿到上一帧的值
     * —— 开火那一瞬枪和手会差一帧。所以这里由 {@link #captureNow()} 主动算当前帧。
     */
    static final GunFrame frame = new GunFrame();

    /** move 姿态临时缓冲（骨骼与手臂共用；客户端渲染单线程，不会并发） */
    private static final float[] MOVE_POSE = new float[6];

    /**
     * 拉栓：拉机柄上抬角（度）。
     *
     * <p>★★ r114：**改成 TaCZ 的 {@code ai_awp} 数值** —— `bolt` 段里 {@code bolt_rotate} 的
     * rotation Z 从 0 匀速转到 **60°**（0.25s→0.50s，占整段 1.2667s 的 20%），
     * 我们用 **62°**（同一档，取整到与 {@code tools/awp_v2.py} 自检打印的 "Java LIFT 62°" 一致）。
     * 这次 v2 几何把整个枪机（八棱柱 + 下弯柄 + 球头）都挂在 {@code bolt} 骨骼上，
     * 62° 时柄头还在镜筒底面之下，不会穿模。
     */
    private static final float BOLT_LIFT = 62.0F;
    /**
     * 拉栓：枪机后退量（模型像素）。
     *
     * <p>★★ r114：**改成 v2 几何的实测值 1.90** —— {@code tools/awp_v2.py} 的自检会扫
     * 「抛壳口 z −2.90…−2.10 闭锁被枪机体盖住、后拉 1.90 后让开」，这个数就是几何要求的最小行程。
     * （TaCZ {@code ai_awp} 的 {@code bolt_group} 后退 4.60 是它自己那把更长的枪的行程，不能照搬。）
     */
    private static final float BOLT_BACK = 1.90F;
    /**
     * ★★ r114（照 TaCZ {@code ai_awp} 的 `bolt` 段）：拉栓时**整把枪侧倾**（roll，度）。
     *
     * <p>TaCZ 的 {@code root} 骨骼在拉栓时 rotation Z 一路升到 **11.87°**、rotation X 到 **4.59°**
     * （= 枪身向右滚 + 枪口微抬），配合右侧拉机柄抡起来 —— 这就是「栓动枪拉栓」那个标志性动作，
     * 它把"拉机柄在右侧"这件事表现出来了（我们原来整枪一动不动，只有一根柄在转，看着像在"拨开关"）。
     */
    private static final float BOLT_ROLL = 11.9F;
    /** ★★ r114：拉栓时整枪的俯仰（度）—— TaCZ {@code bolt} 的 {@code root} rotation X 峰值 4.59° */
    private static final float BOLT_PITCH = 4.6F;
    /**
     * ★★ r114：拉栓时枪身**下沉**（模型像素）—— TaCZ {@code bolt} 的 {@code root} position Y 走到
     * **−0.80**。TaCZ 那把枪比我们长（它整枪约 38 单位，我们 24），按比例折一半取 0.40。
     */
    private static final float BOLT_SINK = 0.40F;
    /** {@code bolt} 骨骼 pivot（geo 里的值）—— 拉机柄绕它抬起来 */
    private static final float BOLT_PX = 0.615F;
    private static final float BOLT_PY = 1.50F;
    private static final float BOLT_PZ = 0.375F;
    /** 拉机柄握点相对 pivot 的偏移（模型像素）：v2 几何的球头中心 (1.31, 1.365, −0.045) 减 pivot */
    private static final float BOLT_GRIP_DX = 0.82F;
    private static final float BOLT_GRIP_DY = -0.135F;
    /**
     * 右手「从握把摸到拉机柄」（{@code BOLT_HAND_IN} 之前）与「拉完立即回握把」的区间。
     * r84：枪机一拉到底（0.60）就松手，在 {@code BOLT_HAND_SNAP}（约 1.8 tick）里**快速**回到握把，
     * 不再一路跟着枪机慢慢滑回去。
     */
    private static final float BOLT_HAND_IN = 0.18F;
    private static final float BOLT_HAND_OUT = 0.60F;
    /** 回握把用多少进度（r84：0.08 → 0.18，约 4 tick；太快就是「手向下甩一下」） */
    private static final float BOLT_HAND_SNAP = 0.18F;
    /** 击发：扣扳机（绕顶部销轴向后转 11°，与 animation.awp.fire 一致） */
    private static final float TRIGGER_PULL = 11.0F;

    /**
     * 换弹：弹匣掉落距离 / 前倾角。
     *
     * <p>★★ r114（照 TaCZ {@code ai_awp}）：TaCZ 换弹时 {@code magzine_and_bullet} /
     * {@code mag_and_lefthand} 的 rotation Z 一路转到 **−131°**、position Y 压到 **−22.6** ——
     * 它的弹匣是**翻着甩出去**的，不是直上直下。我们取 **45°**（够明显地"倾出去"，
     * 又不会让弹匣盒穿进拇指孔枪托）。
     */
    private static final float MAG_DROP = 2.6F;
    private static final float MAG_TILT = 45.0F;

    // ------------------------------------------------------------------ 抛壳轨迹
    /** 抛壳窗口在拉栓进度里的位置：抽壳结束才被抛壳挺顶出去（r84 窗口延长到 0.80，飞行看得更清楚） */
    private static final float CASE_T0 = 0.12F;
    private static final float CASE_T1 = 0.80F;
    /**
     * 被枪机抽出的距离 / 抛出的初速（模型像素）—— r84 整条弧线加大：
     * 抽出 1.5 → **3.0**（跟得上 3.4 的枪机行程），抛向 +X 3.4 → **5.0**、向上初速 1.7 → 2.2，
     * 让弹壳从抛壳口翻出去时**离开枪身与右臂**，能看清它三轴翻滚地飞走。
     *
     * <p>★ r114：抽出距离跟着 v2 几何的枪机行程收到 **1.90**（= {@link #BOLT_BACK}）——
     * 弹壳是被枪机带出来的，抽出量不能超过枪机后退量。
     */
    private static final float CASE_BACK = 1.90F;
    private static final float CASE_VX = 5.0F;    // ★ r107：右抛壳（+X），原来是 -5 往左飞
    /**
     * ★ r121：弹壳的**起始偏移**（模型像素，+X = 屏幕右侧 = 射手右侧）。
     *
     * <p>弹壳骨骼自己的 pivot 是 x = 0.20（r115 为了「放在机匣右壁的抛壳窗里」而压得这么靠内），
     * 结果是**贴着中线起飞**，玩家看上去就是「从枪身中间（偏左）冒出来」。
     * 再加 0.40 ⇒ 从 x ≈ 0.60 起飞，已经在机匣右壁（半宽 0.38）**外面**，
     * 与世界的 {@code WeaponMount.AWP_EJECT} 也基本对齐。
     */
    private static final float CASE_X0 = 0.40F;
    private static final float CASE_VY = 2.2F;
    private static final float CASE_G = 0.8F;
    /** 三轴翻滚（度） */
    private static final float CASE_SPIN_Z = -240.0F;   // ★ r107：自转方向跟着镜像
    private static final float CASE_SPIN_X = 150.0F;
    private static final float CASE_SPIN_Y = 90.0F;

    // ------------------------------------------------------------------ 弹匣子弹（★ r114）
    /** 拉栓进度超过它，枪机就把装填口重新盖住 ⇒ 弹匣里又看不见了（用户要的「拉完栓看不见」） */
    private static final float BOLT_SHUT = 0.95F;
    /** 托弹板把最上一发顶到弹匣口的高度（模型像素）：`round_in` 静止位 y 0.30 → 1.30 */
    private static final float FEED_LIFT = 1.00F;
    /** 枪机推弹入膛的位移：z −2.51 → −3.46（弹膛） */
    private static final float FEED_Z = 0.95F;
    /** 推弹入膛时把它抬到膛轴：1.30 → 1.575（= `BORE`，`WeaponMount.AWP_MUZZLE` 的 y） */
    private static final float FEED_Y = 0.275F;
    /** 入膛时枪弹微抬（度）—— 膛口导斜面把它顶上膛轴 */
    private static final float FEED_PITCH = 6.0F;

    @Override
    public ResourceLocation getModelResource(AwpRifleItem animatable) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(AwpRifleItem animatable) {
        return TEXTURE;
    }

    @Override
    public ResourceLocation getAnimationResource(AwpRifleItem animatable) {
        return ANIMATION;
    }

    @Override
    public void setCustomAnimations(AwpRifleItem animatable, long instanceId,
                                    AnimationState<AwpRifleItem> state) {
        if (!handPass) {
            staticPose();
            return;
        }
        ItemStack stack = AwpAnimState.heldStack();
        long now = AwpAnimState.now();

        // ---------------------------------------------------------- 举枪（ADS）
        // ★ 举枪只做平移：叠任何角度都会让「8 倍镜光轴」离开屏幕中心。
        //   腰射同样不给任何角度 —— 与 AKM 完全同一套持枪规则（见 computeMovePose）
        computeMovePose(MOVE_POSE);
        CoreGeoBone move = getAnimationProcessor().getBone("move");
        if (move != null) {
            move.setRotX(MOVE_POSE[3]);
            move.setRotY(MOVE_POSE[4]);
            move.setRotZ(MOVE_POSE[5]);
            move.setPosX(MOVE_POSE[0]);
            move.setPosY(MOVE_POSE[1]);
            move.setPosZ(MOVE_POSE[2]);
        }

        // ---------------------------------------------------------- 拉栓
        float bp = stack == null ? -1.0F : AwpRifleItem.boltProgress(stack, now);
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            bolt.setRotX(0.0F);
            bolt.setRotY(0.0F);
            bolt.setRotZ(boltLiftAt(bp) * BOLT_LIFT * Mth.DEG_TO_RAD);
            bolt.setPosX(0.0F);
            bolt.setPosY(0.0F);
            bolt.setPosZ(boltBackAt(bp) * BOLT_BACK);
        }

        // ---------------------------------------------------------- 扣扳机
        // ★ 不能靠 animation.awp.fire：击发同一帧就开始拉栓，控制器优先拉栓（bolt > fire），
        //   那段 11° 的扣扳机键帧永远轮不到。改成按 fireWindow 推骨骼，一扣就有。
        CoreGeoBone trigger = getAnimationProcessor().getBone("trigger");
        if (trigger != null) {
            float fw = stack == null ? -1.0F : AwpRifleItem.fireWindow(stack, now);
            trigger.setRotX(-TRIGGER_PULL * triggerPullAt(fw) * Mth.DEG_TO_RAD);
        }

        // ---------------------------------------------------------- 抛壳（跟着拉栓进度）
        CoreGeoBone casing = getAnimationProcessor().getBone("casing");
        if (casing != null) {
            if (bp < CASE_T0 || bp > CASE_T1) {
                casing.setHidden(true);
            } else {
                casing.setHidden(false);
                float c = (bp - CASE_T0) / (CASE_T1 - CASE_T0);      // 窗口内 0..1
                float out = Mth.clamp((c / 0.22F), 0.0F, 1.0F);      // 先跟枪机抽出来
                float fly = Mth.clamp((c - 0.22F) / 0.78F, 0.0F, 1.0F);   // 再被顶出去
                casing.setPosX(CASE_X0 + CASE_VX * fly);
                casing.setPosY(CASE_VY * fly - CASE_G * fly * fly);
                casing.setPosZ(CASE_BACK * out - 1.2F * fly);
                casing.setRotZ(fly * CASE_SPIN_Z * Mth.DEG_TO_RAD);
                casing.setRotX(fly * CASE_SPIN_X * Mth.DEG_TO_RAD);
                casing.setRotY(fly * CASE_SPIN_Y * Mth.DEG_TO_RAD);
            }
        }

        // ---------------------------------------------------------- 换弹（弹匣）
        float rp = stack == null ? -1.0F : AwpRifleItem.reloadProgress(stack, now);
        CoreGeoBone mag = getAnimationProcessor().getBone("magazine");
        if (mag != null) {
            mag.setHidden(rp >= 0.0F && magHidden(rp));   // 旧匣掉出去的那段直接藏
            float drop = rp < 0.0F ? 0.0F : magDropAt(rp);
            mag.setPosX(0.0F);
            mag.setPosY(-MAG_DROP * drop);
            mag.setPosZ(-0.5F * drop);
            mag.setRotX(MAG_TILT * drop * Mth.DEG_TO_RAD);
        }

        // ---------------------------------------------------------- 弹匣里的子弹（★ r114 重做）
        applyMagRounds(bp, rp, stack);
    }

    /**
     * 弹匣里的 5 发子弹 —— 用户（2026-09-20）：「**弹匣可以看见子弹**，
     * **拉完栓看不见弹匣里面子弹**」。
     *
     * <p>v2 几何把这 5 发做成了 5 根独立骨骼：{@code round_in}（最上一发 = 即将上膛那发）
     * 与 {@code mag_r1..mag_r4}（往下第 2..5 发），全都挂在 {@code magazine} 下面
     * （所以弹匣往下掉 / 翻转时子弹跟着走，不用额外处理）。
     *
     * <h2>为什么要「按余弹一根根藏」</h2>
     * 弹匣是**封闭的盒子**（只有上口敞开，插在机匣底的弹匣井里），所以：
     * <ul>
     *   <li><b>闭锁时</b>：机匣顶的抛壳/装填口被枪机体盖住（自检：「闭锁被枪机体盖住 OK」）
     *       ⇒ 从外面**什么都看不见** ⇒ 全部隐藏（这也正是用户要的「拉完栓看不见弹匣里面子弹」）</li>
     *   <li><b>拉栓时</b>：枪机后退让开装填口（自检：「后拉 1.90 后让开 OK」）
     *       ⇒ 看得见弹匣里的子弹 —— 而且**托弹板会把最上一发顶到弹匣口**
     *       （{@link #FEED_LIFT}），一眼就是「枪在等一发子弹上膛」</li>
     *   <li><b>枪机回位</b>：最上一发被推进弹膛（{@link #FEED_Z} / {@link #FEED_Y}），
     *       推到底就从弹匣里消失 ⇒ 「拉栓把新子弹推入发射」</li>
     * </ul>
     * 打一发少一发：显示的发数 = NBT 里的 {@link AwpRifleItem#mag}（拉栓结束才 −1，
     * 所以拉栓过程中看得见的那一发正好是「马上要进膛的那发」）。
     */
    private void applyMagRounds(float bp, float rp, ItemStack stack) {
        int mag = stack == null ? 0 : AwpRifleItem.mag(stack);
        // 只有「枪机让开装填口」这段看得见；换弹时弹匣整盒掉出去，里面更看不见
        boolean open = bp >= 0.0F && bp < BOLT_SHUT && rp < 0.0F && mag > 0;

        CoreGeoBone roundIn = getAnimationProcessor().getBone("round_in");
        if (roundIn != null) {
            if (!open) {
                roundIn.setHidden(true);
                roundIn.setPosX(0.0F);
                roundIn.setPosY(0.0F);
                roundIn.setPosZ(0.0F);
                roundIn.setRotX(0.0F);
            } else {
                float lift = ease(Mth.clamp(bp / 0.55F, 0.0F, 1.0F));      // 托弹板顶到弹匣口
                float push = ease(Mth.clamp((bp - 0.62F) / 0.33F, 0.0F, 1.0F));  // 枪机把它推进膛
                roundIn.setHidden(push >= 0.995F);                          // 进膛了就看不见了
                roundIn.setPosX(0.0F);
                roundIn.setPosY(FEED_LIFT * lift + FEED_Y * push);
                roundIn.setPosZ(-FEED_Z * push);
                roundIn.setRotX(FEED_PITCH * push * Mth.DEG_TO_RAD);
            }
        }
        // 下面第 2..5 发：显示到「弹匣里还剩几发」为止（最上一发由 round_in 演）
        for (int i = 1; i <= 4; i++) {
            CoreGeoBone bone = getAnimationProcessor().getBone("mag_r" + i);
            if (bone != null) bone.setHidden(!open || i > mag - 1);
        }
    }

    /**
     * move 骨骼当前帧的目标姿态 {@code {posX,posY,posZ,rotX,rotY,rotZ}}（模型像素 / 弧度）。
     *
     * <p>骨骼与手臂**共用这一份**：{@link #captureNow()} 也调它，所以枪和手不会差一帧。
     * 举枪只做平移（叠角度会把 8 倍镜光轴推离屏幕中心）；后坐只沿枪管后拖。
     *
     * <p>★ 静止/举枪时三个角度**恒为 0** —— 与 AKM 同一套持枪规则：枪管轴线始终平行于视线。
     * r82 曾给过第一人称 −14° 的腰射下压角，那等于让枪在世界里真的朝下 14°（看着就是「枪口下垂」），
     * 已按用户要求去掉。将来若还要调屏幕上的倾斜感，请改 display 旋转并同步 {@link WeaponMount}。
     *
     * <p>★★ r114（用户：「套用 TaCZ 的持枪动画」，TaCZ 里没有 AWP，用精密国际 {@code ai_awp} 那套）：
     * 拉栓时**整把枪**按 TaCZ {@code ai_awp} 的 `bolt` 段动作 —— 它的 {@code root} 骨骼在这里
     * rotation Z 升到 **11.87°**、rotation X 到 **4.59°**、position Y 沉 **−0.80**（那把枪比我们长，
     * 位移按枪长比例折半）。所以拉栓时枪会**向右侧倾 + 枪口微抬 + 整体下沉**，把「右手在右侧抡柄」
     * 这件事演出来；拉完（{@code boltSwayAt} 回落）自动归零。
     */
    static void computeMovePose(float[] out) {
        // ★★ r85：举枪位移**不在 move 骨骼**（改由 GunPose 在 pose 层施加，见
        //   {@link WeaponHandGrip#pushAds}）：
        //   · 举枪（ADS）：pose 层平移 —— 把眼睛贴到目镜上、镜筒光轴顶到屏幕中心
        //   · 开火后坐（★ r93）：pose 层的 **firePitch 绕手俯仰** —— 枪管微抬 + 枪托微沉
        //     （以前是整枪 lift 平抬，枪托会跟着往上走，不符合「枪托下沉」的手感）
        //   · 后坐：同时推镜头（{@code ClientEvents.applyRecoilKick}）
        // ★★ r114：**拉栓**这一路留在骨骼上（它必须是「枪 + 手」一起动，见 captureNow）
        Player player = Minecraft.getInstance().player;
        WeaponMount.awpHoldPose(player, aimNow(), holdRun(player), out);
        float sway = boltSwayAt(localBoltProgress());
        out[1] -= BOLT_SINK * sway;
        out[3] += BOLT_PITCH * sway * Mth.DEG_TO_RAD;
        out[5] += BOLT_ROLL * sway * Mth.DEG_TO_RAD;
    }

    /** 当前举枪比例（抵肩时持枪姿态全部收掉：镜筒光轴必须精确落在屏幕中心） */
    private static float aimNow() {
        return Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.AWP).aim, 0.0F, 1.0F);
    }

    /** 上一游戏刻 + 平滑后的冲刺量（渲染一帧可能调好几次，同一刻只推进一步） */
    private static long holdTick = Long.MIN_VALUE;
    private static float holdRun = 0.0F;

    /** 冲刺量的平滑（0 → 1 约 6 tick）：台阶式切换会让「枪压下去」是一下子跳过去的 */
    private static float holdRun(Player player) {
        Minecraft mc = Minecraft.getInstance();
        long now = mc.level == null ? 0L : mc.level.getGameTime();
        if (now != holdTick) {
            holdTick = now;
            float target = player != null && player.isSprinting() && player.onGround() ? 1.0F : 0.0F;
            holdRun += Mth.clamp(target - holdRun, -0.18F, 0.18F);
        }
        return holdRun;
    }

    /**
     * 拉栓时「整枪摆动量」0..1（照 TaCZ {@code ai_awp} 的 `bolt`：0.02s 就起势、中段到峰、
     * 末段随枪机回位一起归零）。骨骼与手臂共用这一份 ⇒ 枪歪的时候手跟着歪，不会脱手。
     */
    private static float boltSwayAt(float bp) {
        if (bp < 0.0F) return 0.0F;
        return ease(Mth.clamp(bp / 0.30F, 0.0F, 1.0F))
                * (1.0F - ease(Mth.clamp((bp - 0.68F) / 0.30F, 0.0F, 1.0F)));
    }

    /**
     * 手臂用：把**当前帧**的 move 姿态直接算进 {@link #frame}。
     *
     * <p>平移量用的是 {@link WeaponMount} 里那份与 {@code models/item/awp.json} 一致的 display，
     * 所以手臂拿到的手位和物品渲染出来位置完全一致。
     */
    static void captureNow() {
        computeMovePose(MOVE_POSE);
        // 举枪位移/开火上抬（相机空间、格）写进 GunPose：手臂与枪共用同一份
        Player local = Minecraft.getInstance().player;
        WeaponHandGrip.pushAds(WeaponAnim.Kind.AWP, local == null ? ItemStack.EMPTY
                : local.getMainHandItem(), local);
        frame.capture(WeaponMount.AWP_TX, WeaponMount.AWP_TY, WeaponMount.AWP_TZ, 1.0F,
                MOVE_PX, MOVE_PY, MOVE_PZ,
                MOVE_POSE[0], MOVE_POSE[1], MOVE_POSE[2],
                MOVE_POSE[3], MOVE_POSE[4], MOVE_POSE[5],
                Mth.clamp(WeaponAnim.of(WeaponAnim.Kind.AWP).aim, 0.0F, 1.0F));   // 持枪姿态（GunPose）
    }

    // ------------------------------------------------------------------ 左手动作（模型像素）
    // 手臂本体在 WeaponArms 里画；这里只回答「左手这一刻该在枪的哪个位置」。
    /** 平时：托在护木下方（狙击手的支撑手一直在这里；再往前就是折叠的两脚架了） */
    private static final float[] ARM_SUPPORT = {0.0F, -0.55F, -3.30F};
    /** 换弹：弹匣握点 */
    private static final float[] ARM_MAG = {0.0F, -0.95F, -1.95F};
    /** magazine 骨骼 pivot（geo 里的值） */
    private static final float MAG_PY = 0.0F;
    private static final float MAG_PZ = 0.90F;
    private static final float[] TMP_A = new float[3];

    /** 左手目标：换弹时伸手去抓弹匣（跟着它一起下坠），其余时间托在枪管下方 */
    static float[] leftHandPx(float[] out) {
        float rp = localReloadProgress();
        if (rp < 0.0F) {
            copy(ARM_SUPPORT, out);
        } else {
            magPoint(rp, TMP_A);
            if (rp < 0.12F) lerp(ARM_SUPPORT, TMP_A, ease(rp / 0.12F), out);
            else if (rp < 0.82F) copy(TMP_A, out);
            else lerp(TMP_A, ARM_SUPPORT, ease((rp - 0.82F) / 0.18F), out);
        }
        return out;      // 开火微抬改由 GunPose 的 lift（枪+双手一起抬），这里不再自己加
    }

    /** 弹匣上的握点（跟着弹匣下移 + 前倾） */
    private static float[] magPoint(float p, float[] out) {
        float drop = magDropAt(p);
        float tilt = MAG_TILT * drop * Mth.DEG_TO_RAD;
        float dy = ARM_MAG[1] - MAG_PY;
        float dz = ARM_MAG[2] - MAG_PZ;
        float c = Mth.cos(tilt);
        float s = Mth.sin(tilt);
        out[0] = ARM_MAG[0];
        out[1] = MAG_PY + (dy * c - dz * s) - MAG_DROP * drop;
        out[2] = MAG_PZ + (dy * s + dz * c);
        return out;
    }

    /**
     * 换弹时弹匣的「退出程度」0..1（0 = 就位，1 = 完全退出）—— 骨骼与手臂同一份。
     *
     * <p>★ r84：旧匣退到底后**继续往下掉**（>1 的部分），到 1.30 倍行程时已经被
     * {@link #magHidden} 藏起来（= 掉在地上）；新匣再从 1.30 倍处升上来卡回井里。
     * 一根骨骼演完「退旧匣 + 插新匣」两个动作，不带世界实体（TaCZ 也是这个做法）。
     */
    private static float magDropAt(float p) {
        if (p < 0.0F) return 0.0F;
        if (p < 0.28F) return ease(p / 0.28F);
        if (p < 0.46F) return 1.0F + 0.30F * ease((p - 0.28F) / 0.18F);         // 旧匣继续往下掉
        if (p < 0.58F) return 1.30F;                                            // 空窗（匣已经掉出去了）
        if (p < 0.80F) return 1.30F * (1.0F - ease((p - 0.58F) / 0.22F));        // 新匣从下面顶上来
        return 0.0F;                                                            // 到位
    }

    /** 旧匣掉出去了、新匣还没上来的那段：藏起来（否则会看成「滑下去又滑回来」） */
    private static boolean magHidden(float p) {
        return p >= 0.38F && p < 0.58F;
    }

    private static float ease(float t) {
        float x = Mth.clamp(t, 0.0F, 1.0F);
        return x * x * (3.0F - 2.0F * x);
    }

    private static float[] copy(float[] src, float[] out) {
        System.arraycopy(src, 0, out, 0, 3);
        return out;
    }

    private static float[] lerp(float[] a, float[] b, float t, float[] out) {
        for (int i = 0; i < 3; i++) out[i] = a[i] + (b[i] - a[i]) * t;
        return out;
    }

    /**
     * 拉机柄抬高量 0..1（骨骼与右手共用同一份 —— 手才跟得住枪机）：
     * 抬起 → 保持 → 末端压回。
     */
    private static float boltLiftAt(float bp) {
        if (bp < 0.0F) return 0.0F;
        if (bp < 0.20F) return bp / 0.20F;
        if (bp > 0.85F) return Mth.clamp((1.0F - bp) / 0.15F, 0.0F, 1.0F);
        return 1.0F;
    }

    /** 枪机后退量 0..1：后退 → 保持 → 推回（同样骨骼 / 手共用） */
    private static float boltBackAt(float bp) {
        if (bp < 0.0F) return 0.0F;
        return Mth.clamp((bp - 0.20F) / 0.35F, 0.0F, 1.0F)
                * (1.0F - Mth.clamp((bp - 0.62F) / 0.32F, 0.0F, 1.0F));
    }

    /** 扣扳机的压下量 0..1：快扣 → 慢放（-1 = 不在击发窗口里） */
    private static float triggerPullAt(float fw) {
        if (fw < 0.0F) return 0.0F;
        if (fw < 0.25F) return ease(fw / 0.25F);
        return ease(Mth.clamp((1.0F - fw) / 0.75F, 0.0F, 1.0F));
    }

    // ------------------------------------------------------------------ 右手动作（模型像素）
    /** 平时：握把（= move 骨骼 pivot，枪就画在这只手上） */
    private static final float[] ARM_GRIP = {0.0F, -1.07F, 1.31F};
    private static final float[] TMP_B = new float[3];

    /**
     * 右手目标：平时握住握把（食指正在扳机上），拉栓时抬起来抓拉机柄、
     * 跟着枪机一起抬起 / 后退，拉完再回到握把。换弹不动右手（换弹匣是左手的活）。
     */
    static float[] rightHandPx(float[] out) {
        float bp = localBoltProgress();
        if (bp < 0.0F) {
            copy(ARM_GRIP, out);
        } else {
            boltHandlePoint(bp, TMP_B);
            if (bp < BOLT_HAND_IN) {
                lerp(ARM_GRIP, TMP_B, ease(bp / BOLT_HAND_IN), out);
            } else if (bp < BOLT_HAND_OUT) {
                copy(TMP_B, out);
            } else {
                lerp(TMP_B, ARM_GRIP,
                        ease(Mth.clamp((bp - BOLT_HAND_OUT) / BOLT_HAND_SNAP, 0.0F, 1.0F)), out);
            }
        }
        return out;      // ★ r85：开火微抬改由 GunPose 的 lift —— 整把枪与双手一起抬
    }

    /** 拉机柄握点（模型空间的绝对点）：绕 bolt pivot 抬起 LIFT 角，再随枪机后退 */
    private static float[] boltHandlePoint(float bp, float[] out) {
        float lift = boltLiftAt(bp) * BOLT_LIFT * Mth.DEG_TO_RAD;
        float c = Mth.cos(lift);
        float s = Mth.sin(lift);
        out[0] = BOLT_PX + (BOLT_GRIP_DX * c - BOLT_GRIP_DY * s);
        out[1] = BOLT_PY + (BOLT_GRIP_DX * s + BOLT_GRIP_DY * c);
        out[2] = BOLT_PZ + boltBackAt(bp) * BOLT_BACK;
        return out;
    }

    /** 本地玩家主手 AWP 的拉栓进度；没拿 / 没拉栓（含击发后那几帧停顿）返回 -1 */
    static float localBoltProgress() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return -1.0F;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof AwpRifleItem)) return -1.0F;
        return AwpRifleItem.boltProgress(stack, player.level().getGameTime());
    }

    /** 本地玩家主手 AWP 的换弹进度；没拿 / 没换弹返回 -1 */
    static float localReloadProgress() {
        Player player = Minecraft.getInstance().player;
        if (player == null || player.level() == null) return -1.0F;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof AwpRifleItem)) return -1.0F;
        return AwpRifleItem.reloadProgress(stack, player.level().getGameTime());
    }

    /**
     * GUI 图标 / 掉落物 / 展示框用的**静态姿态**：把一切动作归位（举枪位移、后坐、拉栓、
     * 换弹的弹匣、抛壳全部清零并藏起弹壳）。
     */
    private void staticPose() {
        CoreGeoBone move = getAnimationProcessor().getBone("move");
        if (move != null) {
            move.setRotX(0.0F);
            move.setRotY(0.0F);
            move.setRotZ(0.0F);
            move.setPosX(0.0F);
            move.setPosY(0.0F);
            move.setPosZ(0.0F);
        }
        CoreGeoBone bolt = getAnimationProcessor().getBone("bolt");
        if (bolt != null) {
            bolt.setRotX(0.0F);
            bolt.setRotY(0.0F);
            bolt.setRotZ(0.0F);
            bolt.setPosX(0.0F);
            bolt.setPosY(0.0F);
            bolt.setPosZ(0.0F);
        }
        CoreGeoBone mag = getAnimationProcessor().getBone("magazine");
        if (mag != null) {
            mag.setRotX(0.0F);
            mag.setPosX(0.0F);
            mag.setPosY(0.0F);
            mag.setPosZ(0.0F);
        }
        CoreGeoBone trigger = getAnimationProcessor().getBone("trigger");
        if (trigger != null) {
            trigger.setRotX(0.0F);
        }
        CoreGeoBone casing = getAnimationProcessor().getBone("casing");
        if (casing != null) {
            casing.setHidden(true);                 // 静止时弹壳收在机匣里，本来也看不见
        }
        // ★ r114：弹匣里那 5 发（`round_in` / `mag_r1..mag_r4`）在闭锁姿态下被枪机体与弹匣壁挡着，
        //   物品栏图标 / 掉落物 / 展示框里一律藏掉（既省渲染，也避免斜看穿帮）
        CoreGeoBone roundIn = getAnimationProcessor().getBone("round_in");
        if (roundIn != null) roundIn.setHidden(true);
        for (int i = 1; i <= 4; i++) {
            CoreGeoBone bone = getAnimationProcessor().getBone("mag_r" + i);
            if (bone != null) bone.setHidden(true);
        }
    }
}
