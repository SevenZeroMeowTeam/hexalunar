package cn.blockforge.generated.hexalunarcalamity.weapon;

import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

/**
 * 武器视觉特效（轻量）。
 *
 * <p>全部用 {@link ServerLevel#sendParticles} 并**只摆粒子位置**、不依赖速度方向
 * （原版那个重载的速度是 nextGaussian 随机的，控制不了方向，所以枪口焰靠"在枪管
 * 方向上多摆两段"来做出喷出感）。也**不写世界光照**：原版没有动态光源，硬塞光源方块
 * 等于每发都改方块，连发时会很重。所以"照亮"用 FLASH 那种自发光粒子来表现。
 */
public final class WeaponFx {

    /** 黄铜弹壳色 */
    private static final Vector3f BRASS = new Vector3f(0.84F, 0.66F, 0.30F);
    /** 炽热弹道色 */
    private static final Vector3f HOT = new Vector3f(1.00F, 0.74F, 0.34F);

    private WeaponFx() {
    }

    /** 枪口焰：白闪 + 沿枪管两段火星 + 枪口烟 */
    public static void muzzleFlash(ServerLevel server, Vec3 muzzle, Vec3 dir, boolean aiming) {
        int seg = aiming ? 1 : 2;
        server.sendParticles(ParticleTypes.FLASH, muzzle.x, muzzle.y, muzzle.z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        for (int k = 0; k < seg; k++) {
            Vec3 p = muzzle.add(dir.scale(0.22D + 0.30D * k));
            server.sendParticles(ParticleTypes.SMALL_FLAME, p.x, p.y, p.z, 1, 0.04D, 0.04D, 0.04D, 0.0D);
            server.sendParticles(new DustParticleOptions(HOT, 0.9F), p.x, p.y, p.z, 1,
                    0.05D, 0.05D, 0.05D, 0.0D);
        }
        server.sendParticles(ParticleTypes.SMOKE, muzzle.x, muzzle.y, muzzle.z, 2,
                0.08D, 0.08D, 0.08D, 0.006D);
    }

    /**
     * 抛壳：从抛壳口往**射手右侧**上方甩出黄铜壳 + 一缕硝烟（port = 模型上实际的抛壳口位置）。
     *
     * <p>★ 方向必须是**射手右侧**：{@code dir × up} 本身就等于「射手的右边」——
     * 这与 {@link WeaponMount#toWorld} 把模型 +X 映射到世界坐标用的是同一个右手系约定；
     * 而枪上的抛壳口、{@code WeaponMount.*_EJECT}、第一人称 {@code casing} 骨骼的
     * {@code CASE_VX} 全部落在 **+X（右侧）**。
     *
     * <p>r87 曾在这里补过一句 {@code .scale(-1)}（注释也写成了「往射手左侧」），
     * 于是**世界里的黄铜壳往左飞**，与枪上看到的抛壳口方向正好相反；r107 把第一人称的
     * {@code CASE_VX} 改成 +X 时没带上这里，两边就一直不一致（用户反馈 98k / 莫辛 / M1 抛壳不对）。
     * 现去掉取反 —— 世界抛壳与第一人称弹壳统一都是**右侧**。
     */
    public static void ejectCasing(ServerLevel server, Vec3 port, Vec3 dir) {
        Vec3 right = dir.cross(new Vec3(0.0D, 1.0D, 0.0D));
        if (right.lengthSqr() < 1.0E-6D) {
            right = new Vec3(1.0D, 0.0D, 0.0D);
        }
        right = right.normalize();
        server.sendParticles(new DustParticleOptions(BRASS, 0.75F),
                port.x, port.y, port.z, 1, 0.02D, 0.02D, 0.02D, 0.0D);
        server.sendParticles(ParticleTypes.SMOKE, port.x, port.y, port.z, 1,
                0.05D, 0.05D, 0.05D, 0.012D);
        // 再往外摆一颗，像弹壳已经甩出去一截
        Vec3 fly = port.add(right.scale(0.35D)).add(0.0D, 0.20D, 0.0D).add(dir.scale(-0.18D));
        server.sendParticles(new DustParticleOptions(BRASS, 0.7F),
                fly.x, fly.y, fly.z, 1, 0.03D, 0.03D, 0.03D, 0.0D);
    }

    /** 曳光：弹道上的光点（每 tick 一颗，够轻） */
    public static void tracer(ServerLevel server, Vec3 pos) {
        server.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y, pos.z, 1,
                0.01D, 0.01D, 0.01D, 0.0D);
    }

    /** 弹道热痕：每 2 tick 补一颗，拉出连续光带 */
    public static void tracerHot(ServerLevel server, Vec3 pos) {
        server.sendParticles(new DustParticleOptions(HOT, 0.55F), pos.x, pos.y, pos.z, 1,
                0.02D, 0.02D, 0.02D, 0.0D);
    }

    /** 命中方块：火花 + 烟尘 + 方块碎屑（碎屑就是"弹痕"的观感） */
    public static void impactBlock(ServerLevel server, Vec3 at, BlockState state) {
        server.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 6, 0.10D, 0.10D, 0.10D, 0.0D);
        server.sendParticles(ParticleTypes.SMOKE, at.x, at.y, at.z, 3, 0.08D, 0.08D, 0.08D, 0.012D);
        if (state != null && !state.isAir()) {
            server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state),
                    at.x, at.y, at.z, 8, 0.16D, 0.16D, 0.16D, 0.06D);
        }
    }

    /** 命中生物：火花 + 一层薄烟 */
    public static void impactEntity(ServerLevel server, Vec3 at) {
        server.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 6, 0.12D, 0.14D, 0.12D, 0.0D);
        server.sendParticles(ParticleTypes.SMOKE, at.x, at.y, at.z, 2, 0.08D, 0.10D, 0.08D, 0.012D);
    }

    /* ---------------------------------------------------------------- 弩/弓 */

    /** 弩箭/箭矢拖尾：细一点，免得把视野糊住 */
    public static void arrowTrail(ServerLevel server, Vec3 pos, boolean toxic) {
        server.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y, pos.z, 1,
                0.01D, 0.01D, 0.01D, 0.0D);
        if (toxic) {
            server.sendParticles(ParticleTypes.ITEM_SLIME, pos.x, pos.y, pos.z, 1,
                    0.04D, 0.04D, 0.04D, 0.0D);
        }
    }
}
