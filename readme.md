# 六相月灾 · Hexa Lunar Calamity

[![build](https://github.com/SevenZeroMeowTeam/hexalunar/actions/workflows/build.yml/badge.svg)](https://github.com/SevenZeroMeowTeam/hexalunar/actions/workflows/build.yml)

Minecraft **1.20.1 / Forge 47.4.x** 的月相灾变 + 现代射击玩法模组。
月相会改变夜晚的威胁强度，玩家则用枪械、弩弓与投掷物应对尸潮。

- 模组 ID：`hexalunar_calamity`｜版本：`1.0.0-r65`
- 武器模型：**GeckoLib 4.8.4 骨骼模型**（`geo/*.geo.json` + `animations/*.animation.json`，可在 Blockbench 里直接改）
- 创造模式页签：**六相月灾**

---

## 一、构建与部署

| 项目 | 说明 |
|---|---|
| 需要 | JDK **17**、**Gradle 8.14.5** |
| 依赖 | **GeckoLib 4.8.4**（`software.bernie.geckolib:geckolib-forge-1.20.1:4.8.4`，由 Gradle 自动拉取） |
| ⚠️ 重要 | ForgeGradle `[6.0,6.2)` **不支持 Gradle 9.x**，必须用 8.x |
| 产物 | `mod/build/libs/hexalunar_calamity-1.0.0-r65.jar` |
| 部署 | 复制到 `%APPDATA%\.minecraft\versions\1.20.1-Forge_47.4.23-2\mods\` |
| ⚠️ 运行前置 | **GeckoLib 4.8.4** 必须与 jar 一起放进 `mods/`（武器骨骼模型靠它渲染，缺了直接加载失败） |

`.vscode/tasks.json` 里已配好两个任务（含 Java 报错问题匹配器）：

| 任务 | 作用 |
|---|---|
| `mc_check` | `gradle compileJava` — 只做类型检查，不打包 |
| `mc_build` | `gradle build` + **自动复制 jar 到 mods 目录** |

> 仓库已带 Gradle Wrapper（固定 **8.14.5**）：CI 与本地都可以直接用 `mod\gradlew.bat build`（Linux/macOS 用 `./gradlew`）。
> 推送到 GitHub 后由 `.github/workflows/build.yml` 自动编译并上传 jar 产物；
> 若 `mod/build.gradle` 里的版本号还没有对应 tag，还会**自动打 `v1.0.0-rXX` 标签并创建 Release（附 jar）**。

手动执行等价命令：

```powershell
$env:JAVA_HOME='C:\Users\Administrator\.jdks\temurin-17'
& <gradle-8.14.5>\bin\gradle.bat build --console=plain
```

> VS Code 的 Java 语言服务器没有本工程的 Forge 类路径（会把 `net.minecraftforge.*` 全标红），
> **判断真假以 `gradle compileJava` 的输出为准**。

---

## 二、玩法

### 通用操作

| 输入 | 行为 |
|---|---|
| 右键按住 | 瞄准（各武器行为不同） |
| 左键 | 开火 / 投掷（按住连发由武器决定） |
| `R` | 换弹（AKM，默认键位，可在设置里改） |
| 潜行 + 右键 | **装/拆 AKM 顶部导轨上的瞄具**：副手拿着瞄具 = 装上（消耗一个），空着 = 拆下还给你 |

### 武器

| 武器 | 弹药 | 特性 |
|---|---|---|
| **AKM 突击步枪** | 7.62×39mm | **子弹 10 点伤害**（5 颗心）· 30 发弹匣 · 全自动（2 tick/发）· 后坐力累积影响散布 · 瞄准收紧散布 · **抛壳口会真抛黄铜空弹壳**（含硝烟）+ 枪口焰 · **顶部导轨**（可装红点/4 倍镜）· 退弹匣→上匣→拉栓的换弹动画 · **有效射程 60 格**（射程内平直，超出后下坠） |
| **战术十字弩** | 弩箭 | 弹匣供弹 · 按住连发 · **4 倍镜**：右键开镜时视野 ×1/4、圆形镜筒遮罩 + 十字分划，并自动隐藏手部模型 · 拉弦/装填箭矢为骨骼动画 · **拉弦时弓臂向内收缩**（r63，见下）· **上弦后弦贴回两弓臂之间**（不往后拉，见下）· **有效射程 40 格** |

> **十字弩外形（r61）**：换成参考网格 `模型/十字弩_v2.bbmodel` 那把**现代复合弩**（窄弓臂 + 高导轨 + 枪式握把 + 镜筒 + 线缆），
> 由 `tools/crossbow_vox.py` **表面体素化**成 824 个方块（逐格从原 512² 贴图采样 UV）。
> 骨骼名 / 握把原点 / 显示缩放都保持原样，所以武器动画、手部锚点不用重写。
| **复合弓** | 复合弓箭 / 尸毒箭 | 右键蓄力（20 tick 满蓄），**三段拉弦动画**（0.65 / 0.9 蓄力切换模型）· 蓄力越高穿透与伤害越强 · 没普通箭时自动改用尸毒箭 · **有效射程 34 格** |

> **十字弩的弦（r60）**：上弦（已装填）后弦**不往后拉**，直接贴回两弓臂之间 ——
> 拉回去的弦心比弓臂梢**离镜头近 0.17 格**，透视放大后会像一根「∧」浮在弩上方（用户要求看不见）。
> 拉弦动作本身照旧（装填期间 `draw` 0→1，能看到弦被拉回），一上弦就弹回弓臂前面。
> 实现在 `client/CrossbowGeoModel.java`（`draw = cocked ? 0 : p/0.65`）。

> **十字弩的弓臂（r63~r65）**：拉弦时两弓臂**向内收 + 往射手方向后弯** ——
> 绕「贴导轨的内端」向内转 **8°**，同时整根弓臂**后滑 0.35**（只靠转的话外端主要只往内走，看着像贴在弩身上）：
> 外端实测**向内 0.51 + 向后 0.77**（模型像素）。
> **弓臂本身在 r65 被拉长加粗了一轮**（生成器 `LIMB_SX = 1.7` / `LIMB_SY = 1.25`，绕各自内端缩放）：
> 弓臂外端从 ±3.77 到 **±4.51**、跨度 **7.06 → 9.02**（另一份参考 `十字弩.bbmodel` 的弓臂是 ±6.8、
> 而机身带只 ±0.8，所以我们这版弓臂偏短、看着总像贴在弩身上）。
> 弦与凸轮盘的 pivot 就在弓臂梢上，所以它们跟着弓臂一起走（弦不会脱开）；
> 弦心 / 弩箭 / 左手的目标点共用同一份 `nockTravel(draw)`（弦锚点被弓臂带走的位移 + 弦绷直所需的后退），
> 这样弦内端永远正落在弦心上（拉满时偏差 0.00）。
> **击发/未拉弦时回到参考网格（图片）那个张开姿态**（`draw = 0` ⇒ 转角与后滑量都为 0）。
> 离线验算 + 出图：`python tools/_cb_flex.py [--bake 1.0]`。

### 光学瞄具（AKM 顶部导轨）

| 物品 | 开镜表现 |
|---|---|
| **红点瞄准镜** `red_dot_sight` | 只把屏幕正中画一个红点（与原版准星同心），**枪身照旧可见**，视野略微拉近（×0.88） |
| **4 倍瞄准镜** `scope_4x` | 与十字弩同款**整屏开镜**：视野 ×1/4 + 圆形镜筒近黑遮罩 + 对称十字分划，开镜时隐藏手与武器 |

- 两种瞄具的**光轴参照点**（模型 Y=3.79 / 4.00）写在 `weapon/WeaponMount.java` 里，
  举枪时会被顶到屏幕正中 —— 也就是说“瞄具装在哪，准镜就对哪”，**改模型高度必须同步改这里**
- 目前只能在创造模式「六相月灾」页签取用（还没加合成配方）

### 双手持枪（第一人称）

原版对**非空物品**只画物品、不画手臂（`renderArmWithItem` 里只有空手才走 `renderPlayerArm`），
所以枪看着像浮在空中。现在主手拿 AKM / 十字弩时，用**玩家自己的皮肤**另外补画两条手臂：
**右手始终握在握把上**，左手则按动作走（见 `client/WeaponArms.java`）：

| 武器 | 左手动作（按换弹读条推进） |
|---|---|
| **AKM** | 托护木 → 抓住弹匣抽出来（跟着弹匣下坠/前倾）→ 满弹匣升上来时扶着往上推 → 换到拉机柄拉栓上膛 → 回护木 |
| **十字弩** | 托护木 → 抓住弩弦往后拉（跟着弦心）→ 松手下去取箭 → 把箭推上箭槽 → 回护木 |

- 手的目标点写在各自 GeoModel 里（模型像素），经 `client/GunFrame.java` 换成相机空间；
  `GunFrame` 记的是 `move` 骨骼（含**举枪位移**与**开火后坐**），所以手臂自动跟着枪一起动，
  不需要在手臂代码里重复任何武器逻辑
- **枪稳在手里、开火时双手跟着一起顿**（r59）：
  - 原版对非空物品会套一段「**攻击挥动**」（`applyItemArmAttackTransform`，最多 `rotX −80°`），
    而 `LivingEntity#swing` 在 swingTime 过半时会重置 ⇒ **按住左键就一直重触发**；
    全自动射击时枪就一直在手里上下点头。现在用 Forge 的
    `IClientItemExtensions#applyForgeHandTransform` 接管这一步（只保留手部基准平移，见 `client/WeaponHandGrip.java`）
  - `move` 骨骼只允许在**开火**那一瞬动（后坐：沿枪管方向**平行后拖** 1.35px，弩 0.95px）；
    走路 / 待机 / 换弹 / 拉栓 / 拨保险这些动画推的位移与俯仰（idle ±0.11、run ±0.5、run_fast ±0.9 像素 + 3~5°）
    一律收平 —— 枪不再在手里晃
  - **位移只留 Z（前后），X/Y 与角度一律清零（r62）**：用户要求「只前后动、不上下动」——
    fire 动画自己还推了 +0.15px 的 Y（上下）、reload 推 −1.2px / +7°，全部收掉；
    后坐就是纯后拖，冲量衰减后自己滑回去 ⇒ **真实的后坐感来自沿枪管的往复**
  - **镜头的后坐反馈只留给开火（r62）**：`camera` 骨骼只在 `firing()` 时叠到视角上，
    换弹 / 拉栓（含换完弹那一下）镜头是稳定的，不再“换完弹再上下动一下”
  - **举枪位移 / 后坐只在「拿在手上」时生效（r62/r63）**：GeckoLib 的 `setCustomAnimations`
    对 **GUI 图标 / 掉落物 / 展示框**一样会跑 ⇒ 不加判断的话开火时**物品栏里的图标也往后跟**
    （用户反馈）；现在按 `ItemDisplayContext` 只在第一/第三人称推骨骼（`*GeoRenderer.handPass`）
  - **图标现在是彻底的静态姿态（r63）**：非手持语境直接走 `*GeoModel.staticPose()` —— 举枪位移、
    后坐、换弹的弹匣/枪机、抛壳、弩弦全部归位。r62 只门控了「举枪位移与后坐」，而
    「开火中」是**本地玩家的全局状态**，所以图标还是会跟着移动（用户反馈「7 格物品栏里 akm 发射时还是往后移动」）；
    弩的箭是否显示改看被渲染那把弩自己的 `cockedNow`，不再拿本地玩家的换弹进度去画图标
  - **手臂与枪的同步靠 frame 捕获（r63/r64）**：`WeaponArms` 是在 `RenderHandEvent` 里、**比物品先画**，
    所以「渲染时再捕获 frame」永远只能拿到**上一帧**的值 —— 开火那一瞬枪和手差一帧（用户：
    「akm 发射和手臂都多一帧上下晃动一下」）。现在把 move 骨骼的姿态收成**一份共用数学**
    （`AkmGeoModel.computeMovePose` / `CrossbowGeoModel.captureNow`），手臂画之前先自己算当前帧：
    开枪那一瞬间枪和手一定同拍
  - **视角不再点头（r64）**：`camera` 空骨骼会被 `ClientEvents.applyAkmCamera` 叠到视角上，
    而动画给它的角度是**阶跃**的 ⇒ 每开一发**整个视角（连枪和双臂）上下点一下头**，
    就是用户说的「多一帧上下晃」。现在 `AkmGeoModel.zeroCamera()` 一律清零，后坐只保留沿枪管的平移
  - **动画推在 `move` 上的 Z 也不放行（r64）**：以前开火时给动画的 Z 放行，而动画位置是
    「首帧跳到位、末帧跳回去」的阶跃 ⇒ 每发都让枪顿一下。现在 Z 只由 `WeaponAnim` 的冲量驱动
    （开火那一 tick 加上去、之后每 tick ×0.55 衰减，天生平滑）
  - **枪身角度一律保持「平行」（r60）**：任何动画给 `move` 推的角度（fire 的 −2.8°、reload 的 +7°）
    都会让枪和双手一起低头/抬头，所以开火与瞄准时 `move` 的角度都清零；后座**只后拖不给俯仰**
  - **肩点必须放在画面外（r65）**：肩点原来在 `z≈−0.42`（离相机只有 0.42 格），为了够到枪还要把手臂
    拉到 1.7 倍长 ⇒ 屏幕上就是**一大片皮肤色梯形把枪遮住**（用户录屏里的主要问题）。
    现在肩点放到画面下缘外、约 0.8 格处，肩距≈0.9 格（拉伸只有 ~1.2 倍），手臂粗细再乘 0.85
  - **后坐走的是 **`move` 骨骼**（不是 display/pose），而手臂读的就是 `move` ⇒
    **开火时双手一定跟着枪动**，不用在手臂那边再补一套
- 手臂摆放：手臂方块在 pose 坐标里是 **原点端=肩、局部 +0.75 格端=手**，所以「把手放到 H」= 原点平移 `H − R·(方块局部 x 中心, 0.75·s, 0)`；
  只沿长度方向拉伸（`pose.scale(1,s,1)`），粗细保持原版。注意右臂方块局部 x 中心是 **−0.375**、左臂（mirror）是 **+0.375**，不补偿手就偏半个方块
- 离线核对：`mod/tools/_armstory.py akm|crossbow` 会按进度渲出故事板（枪 + 双臂），
  改手位不用反复进游戏

> **获取途径**：三把武器本体可在原版探险箱里按概率开出（附赠一份对应弹药）—— 常见箱 6%（地牢 / 矿井 / 神庙 / 前哨 / 村庄武器商…）、稀有箱 16%（古城 / 林宅 / 末地城 / 宝藏 / 堡垒…），权重 复合弓 > 十字弩 > AKM；也可在创造模式「六相月灾」页签直接取用。

### 弹药与弹药盒

| 物品 | 容量 | 获取 |
|---|---|---|
| 弩箭 | — | 木棍 + 燧石 ×4 |
| 复合弓箭 | — | 木棍 + 燧石 + 线 ×4 |
| 尸毒箭 | — | 复合弓箭 + 尸毒萃取剂 ×2 |
| 7.62×39mm | — | 火药 + 铁粒 ×6 |
| 弩箭 / 箭矢 / 步枪弹药盒 | 64 / 96 / 300 | 同一形状 `ppp/p■p/iii`，**中心槽放对应弹药**（三个配方靠中心材料区分，不会互相冲突） |
| 创造弹药箱 | ∞ | 创造页；**放在物品栏（快捷栏 / 背包 / 副手）里就生效**：三把武器无限供弹，不用手持、不用切弹种 |

### 投掷物

| 物品 | 效果 |
|---|---|
| **碎片手雷 `mud`** | 半径 4.5 格爆炸伤害（最高 14，按距离衰减）+ 短暂缓慢 |
| **震爆弹 `mtx`** | 半径 6 格：**致盲 + 眩晕**（缓慢 III / 反胃 / 虚弱，时长随距离衰减），近距离额外 4 点伤害 |

**操作流程（两者相同）**：

1. **按住右键 1 秒** → 拔掉保险销（有咔哒声与提示）
2. **左键丢出**；直接砸中生物会提前起爆
3. **压杆规则**（引信何时开始跑）：
   - **还握在手里**（主手/副手）→ 压杆被手压住，**引信不走表**，绝对安全
   - **一离开手**（换到其它格 / 放回背包 / 丢出去）→ 压杆弹开，从那一瞬开始计 **5 秒**
   - 到点在它所在的位置起爆 —— **在背包里也会炸**
4. **潜行 + 右键** → 把保险销插回去（前提正是“压杆还被手压着”）；离开手之后就插不回去了

### 月相

血月 / 蓝月 / 黄月，以及更强的**超级**版本；不同月相影响尸潮数量、速度与掉落。
伴随六种特殊感染者：自爆尸、喷吐尸、蛮兵尸、巨尸、突袭骷髅、剧毒骷髅。

---

## 三、项目结构

```
mod/
├── src/main/java/cn/blockforge/generated/hexalunarcalamity/
│   ├── weapon/     枪械、弩、弓、**瞄具**、射击数学（AkmRifleItem / WeaponMount / Sights / Ballistics / WeaponFx）
│   ├── item/       弹药盒、创造弹药箱、解毒剂、手雷（GrenadeItem）
│   ├── entity/     弹丸与投掷物（子弹、弩箭、箭矢、手雷 GrenadeEntity）+ 特殊感染者
│   ├── client/     输入、FOV/瞄准、HUD、**GeckoLib 模型与渲染器**（*GeoModel / *GeoRenderer）、物品属性注册
│   ├── net/        网络包（月相同步 / 命中反馈 / 开火 / 装填）
│   ├── registry/   物品、实体、音效、效果、创造页签
│   └── moon/       月相管理 + 僵尸进化（ZombieEvolution）
└── src/main/resources/
    ├── assets/hexalunar_calamity/geo/         ★ GeckoLib 骨骼模型（.geo.json）
    ├── assets/hexalunar_calamity/animations/  ★ GeckoLib 动画（.animation.json）
    ├── assets/hexalunar_calamity/             OBJ/MTL 旧模型、贴图（含 *_glowmask.png）、语言、音效
    ├── assets/minecraft/atlases/              ★ 方块图集扩展（见下）
    └── data/hexalunar_calamity/               配方

tools/  开发辅助脚本（见第五节）
```

---

## 四、踩过的坑（改模型/资源前务必读）

1. **Forge 的 OBJ 顶点单位是「方块」**
   `ObjLoader` 把 OBJ 的 `v` 坐标直接当方块塞进 `BakedQuad`，**不除以 16**。
   Blockbench 导出的 0..16 坐标在游戏里就是 **16 格大** —— 症状是 GUI 图标被甩到格子角落只剩裁剪碎片、手持模型离手一格像"漂浮"。
   → 所有 OBJ 必须 `÷16` 并让几何**居中在 (0.5, 0.5, 0.5)**（`ItemRenderer` 会无条件 `translate(-0.5,-0.5,-0.5)`）。
   工具：`tools/obj_normalize.py`

2. **自定义方块图集只能放 `assets/minecraft/atlases/blocks.json`**
   `SpriteResourceLoader` 只会读 `minecraft:atlases/blocks.json` 这一个位置（多包叠加），
   放在 `assets/<你的命名空间>/atlases/` 里的文件**根本不会被加载**。
   目录源写法：`{"type":"directory","source":"models","prefix":"models/"}`（`source`/`prefix` 都是必填）。

3. **`firstperson_lefthand` 要和右手条目同旋转、同平移**
   镜像由 MC 自己施加，把 yaw 取反会让副手模型穿进镜头。

4. **拉弦动画＝两件事缺一不可**
   `UseAnim.BOW`（决定手部/持弓姿态）＋ `pull`/`pulling` 物品属性 + 模型 `overrides`（决定弦的形变）。
   弩必须也用 `UseAnim.BOW`：原版 FP 的 `case CROSSBOW` 只认 `items.crossbow`，模组弩用 `CROSSBOW` 会完全没有手持动作。

5. **`AbstractArrow` 的重力写死在 `tick()` 里**（每 tick 减 0.05），没有可覆盖的 `getGravity()`。
   开镜后射击距离变远会明显下坠脱靶 → 在 `tick()` 里先把 0.05 补回去。

6. **手雷引信用 `inventoryTick`**
   它是原版对背包内每个物品每 tick 的钩子，因此拔销后换手、丢回背包都不会"断表"。
   （已知边界：按 Q 丢到地上的掉落物形态不走该钩子。）

7. 物品属性（`pull` / `pulling`）在 `FMLClientSetupEvent` 里 `ItemProperties.register`；
   用自己命名空间时，**JSON 谓词键要写全名**（`hexalunar_calamity:pull`）。

8. `MobEffect.addAttributeModifier` 必须传 **UUID**，传资源名字符串会触发 FATAL 注册回滚。

9. **GeckoLib 物品的 `display` 包装不生效**
   GeckoLib 的 GeoItem 自己控制变换，套 `BakedModelWrapper` 去改 `display` 没有用。
   举枪/瞄准一律改**骨骼位移**（`CoreGeoBone#setPosX/Y/Z`）；骨骼位移在 display 的 scale **之内**，
   所以“想让骨骼等价于 display 平移 t”要给 `d = t / S`（复合弓 `S=0.75` 必须 ×4/3，AKM `S=1` 两者相等）。

10. **`handleAnimations` 会把没动画的骨骼拉回初始快照**
    `tickAnimation` 先写骨骼，再按 `getBoneResetTime()` 把非动画骨骼归位 —— 所以要在 `setCustomAnimations`
    里做“读-改-写”，别指望跨帧累加（也因此每帧都会重算，不需要自己存状态）。

11. **`UseAnim.BOW` 会给物品额外叠一段“拉弓”位移**
    原版 `ItemInHandRenderer` 对 `UseAnim.BOW` 的额外变换：平移 ±0.28 格 + rotX −13.9° +
    rotY 35.3°/−45° + rotZ −9.8° + z 轴拉伸 20%。枪一旦被套上就会歪着斜、枪托被拉长。
    枪械请用 `UseAnim.NONE`；弓/弩要拉弦效果才用 `BOW`。

12. **物品 NBT 要主动喂给 GeoModel**
    GeoItem 的 animatable 是**物品单例**（不是这一个 ItemStack），所以“装了哪个瞄具”这类 NBT
    要在 `GeoItemRenderer#renderByItem(stack, …)` 里存到静态字段，再给 model 的 `setCustomAnimations` 读。

13. **模型共面会 z-fighting 闪烁**
    两个方块的面完全重合时（例：后移的瞄具底座与机匣盖同为 `±0.42`），渲染会闪；把里面那层缩 0.02 就好。

14. **JOML 的 `Matrix3f` 9 参数构造是「列优先命名」**
    `new Matrix3f(m00, m01, m02, m10, …)` 里的 `m01` 是**第 0 列第 1 行**。照 `(x, y, z)` 的顺序
    把三个基向量写进去，拿到的是**转置矩阵**（= 反向旋转）。第一人称手臂用它就会整条翻到相机后面去、
    被近平面切一刀 → 屏幕上一大片皮肤色（r57 的 bug）。建正交基要**一列一列地填**：
    `new Matrix3f().setColumn(0, x).setColumn(1, y).setColumn(2, z).getNormalizedRotation(q)`。
    离线自查：`mod/tools/_joml_probe/`（`JomlProbe` 验 JOML 约定、`ArmSim` 算手臂方块落点）。

15. **原版会给第一人称的「非空物品」套一段攻击挥动**
    `ItemInHandRenderer#renderArmWithItem` 的物品分支 = `applyItemArmTransform`（手部基准
    `(±0.56, −0.52 − 0.6·equip, −0.72)`）+ `applyItemArmAttackTransform`（挥剑用的，最多 `rotX −80°`）。
    而 `LivingEntity#swing` 在 swingTime 过半时会重置 ⇒ **按住左键（全自动射击）就一直重触发**，
    枪会在手里不停上下点头。枪械要接管这一步：`IClientItemExtensions#applyForgeHandTransform`
    返回 `true` = 原版跳过它自己那些变换（物品照旧渲染，只是少一段 pose）。
    自己补画的第一人称手臂是跟着骨骼走的，跟不到这段 pose 变换 ⇒ 不接管就会「枪在手心里自己晃」。
    举弓类姿态（十字弩按住右键拉弦）仍要交回原版（`UseAnim.BOW` 那套位移本来就是给弓写的）。

16. **GeckoLib 画不了网格 ⇒ 参考网格要「表面体素化」**
    GeckoLib 4.8.4 的 `PolyMesh` 只在 `loading/json/raw/` 里（只解析），渲染侧的 `GeoBone` 只有
    `getCubes()` ⇒ **poly_mesh 导进来能加载但看不见**（AKM 当时就是这么撞的）。所以 mesh 参考模型
    只能体素化。两种做法在 `tools/` 里都有：
    · `akm_voxel_gen.py`（**单层壳**参考）：射线沿 +X 穿越，按「穿入/穿出」成对填充 —— 会把内部填实；
    · `crossbow_vox.py`（**多部件、互相重叠**的参考）：射线成对填充会把空隙一起填掉、薄壁被吸成大块，
      渲染出来是一坨乱方块 ⇒ 改成**表面体素化**（沿三角面密采样、采样点落在哪格就标记哪格），
      既贴合轮廓、方块数又少，视觉上一样（里面看不见）。
    另外 mesh 的 UV 要看是哪种空间（归一化 / 分辨率单位 / 像素）：
    用 `sqrt(uv面积 / 3D面积)` 算出来的「平均密度」在长条面上是不准的，
    体素面直接取**标称密度**（`step × 贴图/分辨率`）观感最好（详见 `crossbow_vox.py` 里的 `uv_space()`）。

17. **GeckoLib 的 `setCustomAnimations` 对「GUI 图标 / 掉落物 / 展示框」一样会跑**
    它只认「渲染这个物品」，不认语境。所以往 `move` 骨骼上推的**举枪位移**与**开火后坐**
    会把**物品栏里的图标**也一起推走（用户反馈：开火时「物品栏物品也随之后移」）。
    正确做法是让渲染器按 `ItemDisplayContext` 记一个 `handPass`（第一/第三人称 = true，
    GUI / GROUND / FIXED = false），模型里再决定推不推骨骼
    （见 `AkmGeoRenderer.isHand()` + `*GeoModel.handPass`）；
    瞄准/拉弦这类「手持姿态」在第三人称也是要看的，所以判据要含第三人称，不能只判第一人称。
    ★ **只把「后坐」门控起来是不够的**（r62 就只做到这一步）：
    · `firing()` / 换弹进度 / 拉弦进度都是**本地玩家的全局状态**，非手持语境下它们一样是真的
      ⇒ 动画推在 `move` 上的 Z、弹匣下坠、弩弦回拉都会一起跑到图标上（r63 才收干净：非手持走 `staticPose()`）；
    · 更隐蔽的是**手臂用的 `GunFrame` 也会被覆盖**：第一人称手臂在 `RenderHandEvent` 里比物品**先**画，
      读的是上一帧的捕获值，而图标那一遍（通常在关卡之后渲染）会把空值写进去
      ⇒ 下一帧手臂按「无举枪、无后坐」摆位，看起来就是「枪在动、手不跟着」。
      所以 frame 必须只在 `handPass` 为真时捕获。
    ★ **即使只在手持语境捕获，也还是差一帧**（r64 用户反馈「akm 发射和手臂都多一帧上下晃动一下」）：
    手臂比物品先画，「渲染时捕获」拿到的永远是上一帧的值。正确做法是把骨骼姿态写成**一份共用数学**
    （纯函数：`AkmGeoModel.computeMovePose`），手臂画之前先自己算当前帧 ⇒ 枪与手同拍。
18. **别让「动画的阶跃位移」直接驱动任何东西**
    动画键值在「开播首帧」与「结束那一帧」是**跳变**的，直接把它当位置用就是每一发都顿一下。
    两个真实病例（r64）：
    · `camera` 空骨骼被 `ClientEvents.applyAkmCamera` 叠到视角上 ⇒ 每开一发整个视角（含模型与双臂）
      上下点一下头 —— 修法：一律清零，要「后坐上跳」就用冲量自己做平滑；
    · `move` 骨骼的 Z 在开火时给动画放行 ⇒ 枪在动画首/末帧跳一下 —— 修法：Z 只由冲量驱动。
    结论：**位置只用能自己控阶跃的量（冲量/插值），动画键值只当「要不要演动作」的开关**。

---

## 五、开发辅助工具（`tools/`）

| 脚本 | 用途 |
|---|---|
| `akm_v3.py` / `bow_v3.py` / `grenade_v3.py` / `flashbang_v3.py` | **武器/投掷物模型生成器**（几何 + 逐面 UV 贴图 + 自检），产物写到 `build/*.geo.json` / `*.png`；自检会打印骨骼名、瞄准线水平/居中、弦端点、导轨高度余量（**十字弩 r61 起改用下表的 `crossbow_vox.py` 体素化**，`crossbow_v3.py` 仅作历史参考） |
| `boxlib.py` | 上面各生成器共用的几何/上色库（倒角、圆角、椭圆、螺栓、通风口、布纹…） |
| `install_models.py` | 把 `build/*.geo.json` + `*.png` 装进 `assets/.../geo` 与 `textures/models`（先备份旧文件） |
| `gen_glowmask.py` | 按亮度阈值自动生成自发光遮罩 `*_glowmask.png`（**改完贴图必跑**） |
| `geo2bbmodel.py` | 把 `.geo.json` 反导成 `.bbmodel`，方便在 Blockbench 里看/改 |
| `bbmcp.py` | Blockbench MCP 的 JSON-RPC 直连客户端（`list` / `call` / `batch` / `schema`） |
| `bbpush.py` | 把 geo + 贴图推进正在运行的 Blockbench 工程（现在的模型迭代主力） |
| `_ads_check.py` | 离线验算举枪对心：按 `WeaponMount` 的变换链算出锚点落在屏幕哪里（要 0.00% / 0.00%） |
| `_joml_probe/`（Java） | 第一人称手臂离线验算：`JomlProbe` 验 JOML 旋转约定（`Matrix3f` 构造顺序 / `rotateAxis` 语义），`ArmSim` 按 `WeaponArms` 同一套数学算出双臂方块 8 个角在相机空间的位置并投影到屏幕，顺带告警「是否越过相机平面」（越过了就是糊屏） |
| `crossbow_vox.py` | 把**参考网格**（`模型/十字弩_v2.bbmodel`，11 个 mesh 部件）**表面体素化**成 GeckoLib 方块模型：逐格从原贴图采 UV、按 mesh 名分骨骼、弦/弦心/弩箭另外用方块画；末尾打印并自检「拉满时两段弦内端是否正好落在弦心」。`--step` 调体素大小（0.45 → ~820 方块） |
| `_cb_flex.py` | 十字弩**弓臂内收**的离线验算 + 姿态烘焙：打印「弓臂外端往内/往后走了多少」「弦内端相对弦心的偏差」，`--bake 1.0` 能把该姿态烘成 `build/cb_flex_*.geo.json` 直接用 `geo_texview.py` 出图。<br>★ 常数（`FLEX_DEG` / `FLEX_PX` / `FLEX_PZ`）必须与 `client/CrossbowGeoModel.java` 一致 |
| `_scopemock.py` | 离线复刻倍镜遮罩绘制数学出 PNG（调分划参数不用反复进游戏） |
| `gen_sight_icons.py` | 生成红点 / 4 倍镜的物品图标 PNG |
| `fp_preview.py` | 第一人称 / GUI / 第三人称离线预览：读模型 JSON 的 `display` + OBJ，按游戏同样的矩阵光栅化出 PNG，并打印屏幕像素包围盒。<br>调手持姿态用它：`python fp_preview.py --json akm.json --obj akm.obj --ctx firstperson_righthand --rot 0,0,0 --trans=-5,-3,4.5 --scale=0.5 --out t.png` |
| `obj_normalize.py` | OBJ 顶点 ÷16（单位修复），自动留 `.unit16bak` 备份 |
| `bbmodel_to_obj.py` | Blockbench `.bbmodel`（网格模型）→ OBJ + MTL，自动 ÷16、居中、UV 归一化 |
| `weapon_string.py` / `bow_gen_pull.py` | 生成拉弦变体：在原模型两梢之间补一条会被拉成 V 形的弦 |
| `scale_weapons.py` | 批量改所有武器（含拉弦变体）的 `gui` / `firstperson_*` scale |
| `obj_rotate.py` | 绕几何中心旋转 OBJ 顶点（`--x/--y/--z`），用于把模型长轴对齐到原版物品的 Y 轴约定 |
| `recipe_audit.py` | 合成表静态体检：JSON 合法性、物品/标签存在性、pattern 自检、配方冲突、无产出物品 |
| `lang_audit.py` | 翻译键体检：代码里用到的 key 是否在 `zh_cn`/`en_us` 都存在、中英是否对齐 |
| `log_audit.py` | 日志体检：扫 `mod/logs`（含轮转 `.gz`）捞出模组相关堆栈/报错，汇总关键信号 |
| `github_ip.py` | 扫 GitHub 可用 IP（TCP + 真 TLS 握手双重验证），`--apply` 写 hosts |
| `push.py` | 一键推送：**先扫 IP → 写 hosts → 再 push**，失败自动重扫重试（`-m` 可顺便提交，中文安全） |

---

## 六、常用参数速查

| 想改什么 | 位置 |
|---|---|
| **武器形状 / 贴图** | `mod/tools/akm_v3.py`（弩 `crossbow_vox.py`（体素化参考网格）、弓 `bow_v3.py`、手雷 `grenade_v3.py`、震爆弹 `flashbang_v3.py`）→ 再跑 `install_models.py` + `gen_glowmask.py` |
| **瞄具挂点高度 / 举枪对心** | `weapon/WeaponMount.java`（`SIGHT_Y` / `AKM_DOT_Y` / `AKM_SCOPE_Y` / `akmAimDy`）—— **必须**与生成器里 `build_dot_sight` / `build_scope_4x` 的注释值一致 |
| **红点 / 倍镜显示逻辑** | `client/AkmGeoModel.java`（`sightNow` 隐藏骨骼 + 举枪位移）+ `client/ClientEvents.java`（`scoping` / `drawRedDot` / `drawScopeOverlay`） |
| **枪口/抛壳位置、射击方向** | `weapon/WeaponMount.java`（`AKM_MUZZLE` / `AKM_EJECT`）+ `AkmRifleItem.fire()`；子弹从模型点出发、朝准星收敛点飞 |
| **手持动作幅度 / 速度** | `client/WeaponAnim.java`（冲量大小与衰减）+ `client/WeaponPose.java`（折算成 display 增量的数值） |
| **后坐幅度 / 镜头反馈强度** | 各 `client/*GeoModel.java` 的 `KICK_BACK` 与 `kick` 计算（AKM 1.35px / 弩 0.95px）；`camera` 骨骼只在 `firing()` 时叠加，换弹期间镜头必须为零 |
| **谁的手持变换被接管** | `client/WeaponHandGrip.java`（`applyForgeHandTransform` 的返回与基准平移）+ 各 `client/*ItemClientExtensions.java` |
| **骨骼该不该被推（渲染语境）** | `client/AkmGeoRenderer.java#isHand` + 各 `*GeoModel.handPass`：GUI 图标 / 掉落物 / 展示框一律不推 |
| **双手持枪的手臂摆位** | `client/WeaponArms.java`（肩点 / 臂长 / 握把锚点）+ 各 `*GeoModel` 里的手部目标点；离线核对 `tools/_armstory.py` |
| 手持动作是否生效 | `client/AnimatedWeaponModel.java` + `ModClient.onModifyBakingResult`；日志里会打“手持动作动画已启用：包装了 N 个武器模型” |
| AKM 弹匣容量 / 换弹时长 / 射速 / 散布 | `weapon/AkmRifleItem.java`（`MAG_SIZE` / `RELOAD_TICKS` / `FIRE_INTERVAL` / `fire()`） |
| 弩的倍镜倍率 | `weapon/CrossbowWeaponItem.java` 的 `SCOPE_ZOOM`（`4.0F` = 4 倍）；开镜 FOV 由 `ClientEvents` 用 `1/SCOPE_ZOOM` 计算 |
| 手雷拔销时长 / 捏雷时限 | `item/GrenadeItem.java`（`PIN_TICKS` / `COOK_TICKS`） |
| 手雷引信、伤害、效果半径 | `entity/GrenadeEntity.java` |
| 三武器的有效射程与超距下坠 | `weapon/Ballistics.java`（`AKM_RANGE` / `BOLT_RANGE` / `BOW_RANGE` 与各 `*_IN_RANGE_GRAVITY`） |
| 武器手持姿态 / 物品栏图标大小 | 各 `models/item/*.json` 的 `display`，或跑 `tools/scale_weapons.py` |
| **弩弓臂内收 / 后弯 / 长短** | `client/CrossbowGeoModel.java` 的 `FLEX_DEG` / `FLEX_BACK` / `FLEX_PX` / `FLEX_PZ`；**弓臂本身的长度与粗细**在 `tools/crossbow_vox.py` 的 `LIMB_SX` / `LIMB_SY`（改完跑生成器 + `install_models.py`，它会把新的 TIP_X / FLEX_PX / FLEX_PZ 打印出来） |
| **第一人称手臂大小 / 位置** | `client/WeaponArms.java` 的 `SHOULDER_R/L`（必须放在画面外，否则一片色块挡住枪）、`THICK`、`ROLL_R/L`；离线故事板 `tools/_armstory.py akm|crossbow` |
| **开火时的视角反馈** | `client/AkmGeoModel.java#zeroCamera`（清零 = 不点头）+ `client/ClientEvents.java#applyAkmCamera`（camera 骨骼→视角的管道）；要做「后坐上跳」就在 `computeMovePose` 里用冲量自己做 |
| 月相效果 | `moon/MoonManager.java` |

---

## 七、更新日志（本次开发）

> 版本 `1.0.0-r65`

- **修「第一人称手臂巨大，一大片皮肤色挡住枪」**（用户录屏里的主要问题）：
  - 肩点原来在 `z≈−0.42`（离相机只有 0.42 格），而手在 `z≈−0.9` ⇒ 既要拉长 1.7 倍去够、近端又离镜头极近，
    屏幕上就是一大片梯形。现在肩点放到**画面下缘外约 0.8 格**（右 `x 0.55` / 左 `x −0.42`，两只手从
    下方两个角伸进来，像原版那样），肩距≈0.9 格（拉伸降到 ~1.2 倍），手臂粗细再乘 **0.85**
  - 离线可先看故事板：`python tools/_armstory.py akm`（`tools/_dblhold.py` 的肩点/粗细已与 Java 同步）
- **十字弩弓臂拉长加粗**（用户要求「像参考模型那样明显探出机身」）：
  - 参考 `模型/十字弩.bbmodel` 的弓臂是 ±6.8、而 `十字弩_v2`（现在用的这版）机身带就 ±2.8 ⇒
    弓臂只探出 0.76，看着就贴在弩身上。生成器新增 `LIMB_SX = 1.7` / `LIMB_SY = 1.25`：
    **弓臂（连同线缆、弦）绕各自内端横向拉长**（单侧分件绕内端、横跨两侧的绕 x=0，否则模型会不对称），
    外端 ±3.77 → **±4.51**、跨度 **7.06 → 9.02**；同时弩箭前端再前伸 0.5（弦心后退变多，不然拉满时箭头会缩进导轨）
  - 弦心 / 弩箭 / 左手的目标点改用**同一份** `nockTravel(draw)`（锚点被弓臂带走的位移 + 弦绷直所需的后退），
    弦内端永远精确落在弦心上（之前弓臂一放大就差了 0.36）

> 版本 `1.0.0-r64`

- **修「akm 发射和手臂都多一帧上下晃动一下」**（两个独立病因，两处都改了）：
  - **视角每发点一下头**：`camera` 空骨骼会被 `ClientEvents.applyAkmCamera` 叠到视角上，
    而动画给它的角度是**阶跃**的 ⇒ 整个视角（连枪和双臂）上下动一下。现在 `zeroCamera()` 一律清零；
    后坐只保留**沿枪管的平移**（这一条 r62 就该一起做，当时只拦了「换弹时别动镜头」）
  - **动画推在 `move` 上的 Z 也不放行**：以前只在「不在开火」时清零，于是动画首/末帧的跳变
    会让枪顿一下。现在 Z 只由 `WeaponAnim` 的冲量驱动（每 tick ×0.55 衰减，天生平滑）
  - **手臂改成算「当前帧」**：手臂比物品先画，靠渲染时捕获就永远差一帧（`akm 发射和手臂都` 里的「手臂」）；
    现在把 move 姿态收成一份共用数学（`computeMovePose`），手臂画之前先自己算 ⇒ 枪与手同拍
  - 十字弩同一套处理（`captureNow` + move 的 Z 只由后坐驱动）
- **十字弩弓臂改成「又向内又向后」**（用户要求「拉弦时弓臂向内收缩」且 r63 的 9° 太不明显）：
  - 内收角 9° → **8°**，另加**整根弓臂往射手方向后滑 0.35** ⇒ 外端实测**向内 0.49 + 向后 0.63**；
    只靠绕 Y 轴转的话外端主要只往内走（弓臂是「内端靠前、外端靠后」的斜杆），看上去就是贴着弩身
  - 弦与凸轮盘跟着弓臂走，弦心 / 弩箭的行程同步 +0.35（保持弦贴在弦心上，搭接量 0.49 仍在弦心方块内）

> 版本 `1.0.0-r63`

- **十字弩：拉弦时弓臂向内收缩**（用户要求「发射完为图片里那样，拉弦时弓臂向内收缩」）：
  - 两弓臂绕**贴导轨的内端**（模型像素 `(±1.50, -8.60)`）向内转，拉满 **9°**；
    外端因此往**内 0.55 + 后 0.31** 走，弓臂外缘宽度 7.06 → 6.24（收 **12%**）；
    `draw = 0`（未拉 / 已击发）时转角为 0 ⇒ 回到参考网格（图片）那个张开姿态
  - **弦与凸轮盘的 pivot 就在弓臂梢上**，所以它们跟着弓臂平移同样的位移（`δ = R(θ)(A−P)+P−A`），
    否则弦会跟弓臂脱开；实测弦内端相对弦心的偏差 (−0.55, +0.13)，仍在弦心方块内（±0.60 / ±0.26）
  - GeckoLib 的骨骼变换是 `pivot + pos + R(rot)·(p − pivot)`，所以「绕任意点转」是「原旋转 + pos 补偿」；
    新增 `tools/_cb_flex.py` 做离线验算与出图（`--bake` 出姿态 ×2 用 `geo_texview.py` 对比）
- **修「AKM 射击时手臂上下晃、不平行」**：手臂读的 `GunFrame` 被**图标那一遍**（GUI display）覆盖了 ——
  手臂在 `RenderHandEvent` 里比物品先画、读的是上一帧的捕获，而 r62 的门控让图标那一遍写入一套
  「无举枪、无后坐」的空值，于是枪动、手不跟着（右键瞄准时垂直错位最明显）。现在 frame **只在手持语境捕获**
- **修「物品栏里 AKM 发射时还是往后移动」**：r62 只门控了「后坐」，而 **`firing()` / 换弹进度是本地玩家的全局状态**，
  非手持语境里动画推在 `move` 上的 Z（以及弹匣下坠、弩弦回拉、抛壳）照样生效 ⇒ 现在非手持语境直接走
  `staticPose()`（静态一帧），弩的箭按被渲染那把弩自己的 `cockedNow` 决定看不看得到

> 版本 `1.0.0-r62`

- **后坐只前后动、不上下动**（用户要求「只前后动不是上下动」）：
  - `move` 骨骼上的垂直位移有三处来源 —— **fire 动画自带的 `+0.15px Y`**、r59 我加的 `KICK_UP`、
    以及 idle/run 的 Y —— 现在**全部清零**（`setPosX/Y(0)`、`setRotX/Y/Z(0)`），只留 Z；
    后坐 = 沿枪管**纯后拖**（AKM 1.35px / 弩 0.95px），冲量衰减后自己滑回去 ⇒ 真实的后坐感来自往复
  - 瞄具开镜只做**平移**（`PosX/PosY/PosZ`），不叠加任何角度 ⇒ 瞄准始终与枪管平行
- **物品栏图标不再跟着后坐跑**：GeckoLib 的 `setCustomAnimations` 对 **GUI 图标 / 掉落物 / 展示框**一样会跑，
  所以举枪位移与后坐会把**热栏里那把枪的图标**也往后推（用户反馈「物品栏物品也随之后移」）。
  现在渲染器按 `ItemDisplayContext` 记 `handPass`（第一/第三人称 = true，`AkmGeoRenderer.isHand()`），
  AKM / 十字弩 / 复合弓三个模型都按它决定推不推骨骼（详见第四节坑 17）
- **换弹 / 拉栓全程镜头稳定**：`camera` 骨骼原来在 `!firing()` 条件下才清零（换弹、拉栓也算「有动作」），
  所以换完弹那一下镜头会跟着 `bolt_pull` 的角度（0.6° / −1.1°）抖一下；
  现在**只有开火时**才把 camera 叠到视角上 ⇒ 换弹稳定、开火仍保留镜头后坐感

> 版本 `1.0.0-r61`

- **十字弩换成参考网格里那把现代复合弩**（用户要求按 `模型/十字弩_v2.bbmodel` 替换外形）：
  - 新增 `tools/crossbow_vox.py`：**表面体素化**（沿三角面密采样，采样点落在哪格就标记哪格）→
    824 个方块 / 14 骨骼，逐格从原 512² 贴图采 UV（避开「平均密度」在长条面上不准的问题，取标称密度 `step × 贴图/分辨率`）
  - 11 个 mesh 部件按名字分骨骼（弓片 → `prod_right/left`、机匣/导轨/线缆 → `body`、镜筒/握把/枪托各自成骨骼），
    **握把原点保持 (0, −0.95, 0.66)** ⇒ `WeaponArms` 的锚点、display 缩放都不用改
  - 弦面与拉弦行程重新推导：`TIP_X 6.0 → 2.62`、`DRAW_DZ 3.40 → 1.80`、`NOCK_Z0 −5.80 → −5.20`，
    弦长 = `hypot(2.62, 1.80)`，生成器自检「拉满时两段弦内端是否正好落在弦心」；弦 / 弦心 / 弩箭照旧用方块画（要能绕弓臂梢转）
  - 为什么不用 GeckoLib 的 `poly_mesh`：4.8.4 只解析不渲染（渲染侧 `GeoBone` 只有 `getCubes()`，见第四节坑 16）
- 贴图按 v2 原画重排到 480²，右边缘留一条色带给弦 / 弦心 / 弩箭 / 尾羽采样；`install_models.py` 的弩改为装 `crossbow_geo.*`

> 版本 `1.0.0-r60`

- **后坐与瞄准都保持「平行」**：原来我加的俯仰（AKM −3.2°、弩 −2.4°）加上动画自己给的角度
  （fire −2.8°、reload +7°、弩 +2.4°）会让枪和双手一起低头/抬头 —— 现在 `move` 的角度一律清零，
  后坐只后拖（+0.10px 轻微上抬），**枪口不上跳也不低头**，右键瞄准时模型也是水平的
- **十字弩上弦后弦不往后拉**（用户选择「贴在两弓臂之间」）：拉回去的弦心比弓臂梢**离镜头近 0.17 格**，
  透视放大约 17%，看起来像一根「∧」浮在弩上方 ⇒ `draw = cocked ? 0 : clamp(p/0.65,0,1)`，
  一上弦弦就弹回弓臂前面；拉弦动作本身照旧（装填期间 `draw` 0→1，能看到弦被拉回）

> 版本 `1.0.0-r59`

- **枪不再在手里晃**：原版对非空物品套的「攻击挥动」（`applyItemArmAttackTransform`，最多 `rotX −80°`）
  会被按住左键反复重触发（`LivingEntity#swing` 在 swingTime 过半时重置）⇒ 全自动射击时枪在手里不停点头。
  现在用 Forge 的 `IClientItemExtensions#applyForgeHandTransform` 接管（只保留手部基准平移，见 `client/WeaponHandGrip.java`）
- **开火时双手跟着枪一起动**：后坐改走 `move` 骨骼 —— 第一人称手臂读的就是 `move`（`client/GunFrame.java`），
  所以不需要在手臂那边重复任何武器逻辑；同时 idle / run / run_fast / 换弹 / 拉栓推的位移与俯仰一律收平
- 手臂基准 Y 跟着原版的「抬起物品」位移（`baseY() = ARM_Y − 0.6·equipNow`），切枪那几帧手也不脱把

> 版本 `1.0.0-r58`

- **AKM 抛壳动画**：抛出的是真的黄铜空弹壳（模型里 4 根 `casing_0..3` 骨骼 + 黄铜方块），
  不再只有粒子：
  - 每开一发的时刻记在 `client/AkmAnimState` 里（4 个槽轮流用），`AkmGeoModel.driveCasings`
    按「现在 − 那发的时刻」算这枚弹壳飞到哪了：右上方抛物线 + 绕 Z/X/Y 三轴翻滚，
    飞满 12 tick（≈0.6s）就 `setHidden`
  - 全自动 2 tick/发 ⇒ 同时有 4~6 枚空壳在空中，看起来就是一串往外冒弹壳
  - 弹壳真实尺寸只有 0.6px（看不见），模型里故意放大到 ~2.4px；原来的黄铜粒子/硝烟特效保留
    （第三人称与远处也能看到）
- `readme.md` / `mod/README.md` 同步到 r57

> 版本 `1.0.0-r56`

- **左手开始干活**（在 r54 的双臂基础上）：
  - **AKM**：托护木 → 抽出空弹匣（跟着弹匣一起下坠前倾）→ 满弹匣升上来时扶着往上推 →
    换到拉机柄拉栓上膛 → 回护木
  - **十字弩**：托护木 → 抓住弦往后拉（跟着弦心）→ 松手下去取箭 → 把箭推上箭槽 → 回护木；
    弩箭也改成在左手送到箭槽那一刻（p≈0.84）才出现，不再凭空冒出来
  - 新增 `client/GunFrame.java`：记下 `move` 骨骼（含举枪位移与各动画）的变换，
    手臂的目标点（模型像素）经它换成相机空间 ⇒ **手臂自动跟随举枪/换弹/开火动画**
  - `client/AkmArms.java` 升级为通用的 `client/WeaponArms.java`（双臂渲染 + 运行时摆位，
    不再靠离线算好的欧拉角），十字弩也补上了双臂
  - 新增 `mod/tools/_armstory.py`：按换弹进度渲故事板（枪 + 双臂），改手位不用反复进游戏
- `readme.md` / `mod/README.md` 同步到 r56

> 版本 `1.0.0-r55`

- **十字弩：白弦往玩家方向再拉 0.8**。拉弦行程 `DRAW_DZ` 2.60 → **3.40**
  （拉满时弦心从 z=−3.20 退到 **z=−2.40**），弩箭、弦心、凸轮盘一起跟着走：
  - 弦长必须 = `hypot(6.0, DRAW_DZ)`（6.54 → 6.896）：**两段内端只能在这个长度下才在 x=0 相遇**，
    否则拉满时弦会从中间断开（生成器 main() 里有自检会打印落点）
  - 弩箭跟着后移会让箭尖被弩身吞掉，所以箭杆/箭头同时前伸 0.8（`BOLT_EXT`），
    拉满时箭尖露出弓片前方仍然一样多
  - 凸轮盘转角按行程等比从 46° → 60°
- `readme.md` / `mod/README.md` 同步到 r55

> 版本 `1.0.0-r54`

- **子弹伤害改 10 点**：`entity/BulletEntity.java` 里提成常量 `BULLET_DAMAGE = 10.0F`
  （原来是散在 `onHitEntity` 里的 `9.0F`）
- **创造弹药盒改成“在物品栏里就生效”**：不再需要手持、也不再需要手动切弹种
  - 新增 `CreativeAmmoBoxItem.inInventory(player)`（扫快捷栏 + 背包 + 副手），
    `AmmoUtil.count/consumeOne/takeFromBox` 先问这一句，命中就直接 `Integer.MAX_VALUE` / 不扣弹
  - 删掉原来的“潜行右键轮换弹种”与 `HlcMode` NBT；tooltip 改成说明现在怎么用
- **双手持枪（第一人称双臂）**：新增 `client/AkmArms.java`，主手拿 AKM 时用玩家皮肤
  补画右手（握把）与左手（托护木），举枪时跟着枪一起挪；常数由 `tools/_dblhold.py` 离线算
- `readme.md` / `mod/README.md` 同步到 r54

> 版本 `1.0.0-r53`

- **武器模型全面重做**：四把武器 + 两种投掷物从「OBJ 网格 + display 变换」迁到
  **GeckoLib 4.8.4 骨骼模型**（`geo/*.geo.json` + `animations/*.animation.json`）：
  - AKM `bones 16 / cubes 128`、十字弩 `bones 14 / cubes 96`，另有复合弓、手雷 `mud`、震爆弹 `mtx`
  - 每个模型都有生成器（`tools/*_v3.py`）并带**自检**：骨骼名、瞄准线水平/居中、弦端点、导轨高度余量…
  - 512² 贴图由脚本逐面绘制，`tools/gen_glowmask.py` 自动出 `*_glowmask.png`
- **瞄准（ADS）数学收拢成一份单一真源** `weapon/WeaponMount.java`：
  模型像素 → 世界的完整变换链 `Trans(±0.56,-0.52,-0.72)·Trans(display/16)·R·S·(px/16)`，
  举枪时把「照门顶—准星顶」那条线顶到屏幕正中（`Tx=-8.96`、`Ty=8.32-S·anchorY`）：
  - **按瞄具改参照高度**：机械瞄具 3.44 / 红点 3.79 / 4 倍镜 4.00
  - 子弹从**枪口模型点**出发、朝准星落点飞（收敛距离夹 8..96 格），不再从屏幕中间斜着飞出来
  - 离线验算：`tools/_ads_check.py akm|akm_aim|bow|bow_draw`（0.00% / 0.00% 为过）
- **AKM 顶部导轨 + 两种光学瞄具**（新物品）：
  - **红点瞄准镜** `red_dot_sight`：开镜时枪身照旧可见，屏幕正中画红点
  - **4 倍瞄准镜** `scope_4x`：与十字弩同款整屏开镜（视野 ×1/4 + 圆形镜筒 + 十字分划）
  - 装/拆：**潜行 + 右键**（副手拿瞄具 = 装上，空手 = 拆下），状态存在物品 NBT（`weapon/Sights.java`）
- **枪械不再用 `UseAnim.BOW`**：原版对 `BOW` 的额外位移会把枪拉歪/拉长 → 改 `UseAnim.NONE`，
  举枪全部由 `move` 骨骼接管
- **开镜遮罩全程序化**：删掉整屏炫光贴图（曾把画面糊成白雾，两次反馈看不见生物），
  改为圆筒近黑遮罩 + 镜缘暗角 + 对称分划，镜内不叠任何白光
- **手部动作全部由武器本体表现**（不再有实体手方块）：
  AKM 退弹匣 → 空窗 → 新匣上行 → 拉栓；十字弩拉弦 / 装填箭矢由弦、弦卡与弩箭骨骼程序化驱动
- **月相/夜晚**：左上角天数 HUD（随月相上色）+ **僵尸进化**（`moon/ZombieEvolution.java`：
  生成即进化 3% 起每天 +1.4%、存活进化 1.2% 起每 8 秒掷一次，按天数解锁 弓箭手→爆破手→油桶兵→巨人）

> 版本 `1.0.0-r22`

- **倍镜十字不再挡视野**：原先的分划是从中心 6px 一直画到半径一半（480p 下约 100px）、
  不透明度 `0xB0`（69%）的纯白线 + 2×2 亮中心点，糊在目标上很挡视角；现改为：
  - 中心留白 9px，不再压住瞄准点
  - 分划总长压到 `min(r/3, 52)`（约为原来一半），内段 `0x74`、外段 `0x3C` 递淡，保留刻度感但不遮目标
  - 中心点缩小为 1px（`0x9C`），仍可精确对准
- 新增 `tools/scope_preview.py`：离线复刻倍镜遮罩绘制数学出 PNG，调分划参数不用反复进游戏

> 版本 `1.0.0-r21`

- **手持动作动画**（参考 SuperbWarfare 的表现，但用**程序化变换**实现，不引入 GeckoLib / Mixin）：
  - 新增 `client/WeaponAnim.java`（每 tick 推进的冲量状态机）、`client/WeaponPose.java`（折算 display 增量）、
    `client/AnimatedWeaponModel.java`（`BakedModelWrapper`，在 `ModelEvent.ModifyBakingResult` 给武器模型套上）
  - **AKM**：开火后坐（后拖 + 上抬 + 随机枪口偏摆，连发会累积）、举枪过渡、40 tick 换弹整套起伏
    （含插弹匣/拉机柄两次顿挫）、走路摆动与呼吸微漂
  - **复合弓**：拉弦把弓往身前拉、放箭向前回弹（回弹幅度按蓄力）
  - **十字弩**：开镜往画面中心收 + 开火后坐
  - **手雷 / 震爆弹**：拔销时手腕外翻使劲、引信越短抖得越厉害、出手向前上方甩
  - **第三人称手臂姿态**（`IClientItemExtensions#getArmPose`）：步枪 / 弩双手持握、瞄准改端平、手雷拔销后抬手持投
  - 数值全部用 `tools/fp_preview.py` 离线验过屏幕包围盒，不会把武器甩出画面
- **CI 自动发布**：`build.yml` 新增 release 作业 —— 推到 main 时若 `mod/build.gradle` 的版本号还没有对应 tag，
  自动打 `v1.0.0-rXX` 标签 + 建 Release 并附上 jar（版本号没变就跳过，不会重复发）

> 版本 `1.0.0-r20`

- **修复「一进世界就崩」**（日志实锤）：`GrenadeHud.render` 把 `GrenadeItem.heldGrenade()` 的 `null` 直接解引用，
  手里没手雷时每帧 NPE → `[Minecraft/FATAL]: Unreported exception thrown!` 直接崩客户端；
  `ModNetwork` 的开火/装填包也补上判空（客户端点完枪立刻切手，服务器就会 NPE）
- 新增 `tools/log_audit.py`：扫 `mod/logs`（含轮转 `.gz`）提取模组相关堆栈与关键信号
- 新增 `tools/github_ip.py` + `tools/push.py`：**每次推送自动扫描 GitHub 可用 IP**（TCP 通才再试真 TLS 握手，
  只信能完成 HTTPS 的节点）、写 hosts 并重试；VS Code 任务 `mc_push` / `mc_logs` / `mc_audit`

> 版本 `1.0.0-r19`

- **尸毒瓶获得途径**：新增配方「尸毒萃取剂 + 玻璃瓶 → 尸毒瓶 ×2」（之前无配方、也无掉落，只能创造模式拿）
- **喷吐尸掉落尸毒萃取剂**（1~2 个，受抢夺影响）—— 萃取剂不再只有剧毒骷髅一个来源
- **三把武器进箱子战利品**：新增 Forge 全局战利品修饰器 `hexalunar_calamity:weapon_cache`
  （`loot/WeaponCacheModifier.java` + `data/hexalunar_calamity/loot_modifiers/*.json` + `data/forge/loot_modifiers/global_loot_modifiers.json`），
  常见箱 6% / 稀有箱 16%，按权重抽取并附赠 8~20 发对应弹药
- 体检脚本 `tools/recipe_audit.py` 扩展为同时校验战利品修饰器（战利品表 id、物品 id、启用列表）

> 版本 `1.0.0-r18`

- **修复手持物品回归**（对照 `backup_20260917_700131` 逐项恢复）：
  - `akm/crossbow/compound_bow/bolt` 的 OBJ 又被还原成 0..16 单位（Forge 把 `v` 直接当方块 → 手里 16 倍大、离手漂浮），四把模型重新 ÷16 归一化，与拉弦变体 / 手雷模型回到同一单位
  - 三把武器的 `display` 手持参数与 `crossbow.json` / `compound_bow.json` 的 `overrides` 被改坏（拉弦变体成了死资源），按备份恢复
  - `crossbow.mtl` / `compound_bow.mtl` 丢了 `newmtl str`（弓弦材质），恢复
  - 十字弩 `getUseAnimation` 被改成 `UseAnim.CROSSBOW`：原版只有 `items.crossbow` 才走弩的姿势分支，模组弩会完全丢失手持/拉弦动作 → 改回 `UseAnim.BOW`
  - `ModClient` 丢了 `pull` / `pulling` 物品属性注册 → 拉弦动画（`pulling_0/1/2`）重新生效
  - `ModClient` 把子弹渲染器换成 `ThrownItemRenderer` → 恢复 `BulletRenderer`（弹尖朝向飞行方向）
  - `ModNetwork.sendReload()` 丢失导致 `ClientGunController` 编译失败；`ClientWeaponInput` 里重复处理 R 键会吞掉点击 → 恢复由 `ClientGunController` 统一处理
  - `CreativeAmmoBoxItem` 丢了 `inventoryTick` 自动切弹种 → 恢复（持枪时自动切到对应弹种，不再“持枪无弹”）
- **合成表**：`ammo_box_rifle` 的图案被改成 `iii/pmp/ppp`（与文档「三盒同形 `ppp/p•p/iii`」不一致）→ 恢复为 `ppp/p•p/iii`
- 新增体检脚本 `tools/recipe_audit.py`、`tools/lang_audit.py`、`tools/obj_rotate.py`

- **射击有效距离**：AKM 40 格 / 十字弩 60 格 / 复合弓 35 格 —— 射程内平直，超出后恢复重力下坠
- **第一人称手持放大**：AKM `0.68`、弩与弓 `0.62`（物品栏图标 `0.72`）
- 手雷压杆规则：握在手里不走表、离手开始 5 秒引信、潜行+右键插回保险销

- 修复 FATAL 注册回滚（`CorpsePoisonEffect` 改用 UUID）
- 修复枪械紫黑贴图：新增 `assets/minecraft/atlases/blocks.json`，OBJ 贴图迁到 `textures/models/`
- **修复模型 16 倍大与离手漂浮**：所有武器/弹丸 OBJ 归一化为方块单位并居中
- 复合弓：三段拉弦动画（程序生成的弓弦变体 + `pull`/`pulling` + `overrides`）
- 十字弩：`UseAnim.BOW` 手持姿态 + **4 倍镜**（视野 ×0.25、圆形镜筒、绿色十字线、开镜隐藏手模）
- 十字弩：弹道无重力（修复开镜打不中）+ 开镜零散布
- AKM：第一人称改为竖直握持；枪械模型整体放大（物品栏图标 0.42 → 0.72）
- 弹药盒：三个配方改为"同形不同芯"，tooltip 显示装填类型
- 新增投掷物：碎片手雷 `mud`、震爆弹 `mtx`（右键拔销 / 左键投掷 / 5 秒引信 / 背包内也会炸）
- 语言文件去重统一（中英）
