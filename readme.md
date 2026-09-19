# 六相月灾 · Hexa Lunar Calamity

[![build](https://github.com/SevenZeroMeowTeam/hexalunar/actions/workflows/build.yml/badge.svg)](https://github.com/SevenZeroMeowTeam/hexalunar/actions/workflows/build.yml)

Minecraft **1.20.1 / Forge 47.4.x** 的月相灾变 + 现代射击玩法模组。
月相会改变夜晚的威胁强度，玩家则用枪械、弩弓与投掷物应对尸潮。

- 模组 ID：`hexalunar_calamity`｜版本：`1.0.0-r83`
- 武器模型：**GeckoLib 4.8.4 骨骼模型**（`geo/*.geo.json` + `animations/*.animation.json`，可在 Blockbench 里直接改）
- 创造模式页签：**六相月灾**

---

## 一、构建与部署

| 项目 | 说明 |
|---|---|
| 需要 | JDK **17**、**Gradle 8.14.5** |
| 依赖 | **GeckoLib 4.8.4**（`software.bernie.geckolib:geckolib-forge-1.20.1:4.8.4`，由 Gradle 自动拉取） |
| ⚠️ 重要 | ForgeGradle `[6.0,6.2)` **不支持 Gradle 9.x**，必须用 8.x |
| 产物 | `mod/build/libs/hexalunar_calamity-1.0.0-r83.jar` |
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
| `R` | 换弹（AKM / **AWP 换弹匣** / 十字弩上弦，默认键位，可在设置里改）· **手里有已拔销 / 引信在烧的手雷时 = 紧急投掷**（立刻按准星丢出）|
| 右键按住（手雷 / 震爆弹） | **拔保险销**（1 秒）；拔销后**必须一直按住**（松手 / **切武器** 就点火）；销已拔出时可 **潜行 + 右键 1 秒** 插回销 |
| 潜行 + 右键 | **装/拆 AKM 顶部导轨上的瞄具**：副手拿着瞄具 = 装上（消耗一个），空着 = 拆下还给你 |

### 武器

| 武器 | 弹药 | 特性 |
|---|---|---|
| **AKM 突击步枪** | 7.62×39mm | **子弹 10 点伤害**（5 颗心）· 30 发弹匣 · 全自动（2 tick/发）· 后坐力累积影响散布 · 瞄准收紧散布 · **抛壳口会真抛黄铜空弹壳**（含硝烟）+ 枪口焰 · **顶部导轨**（可装红点/4 倍镜）· 退弹匣→上匣→拉栓的换弹动画 · **有效射程 60 格**（射程内平直，超出后下坠） |
| **战术十字弩** | 弩箭 | 弹匣供弹 · 按住连发 · **4 倍镜**：右键开镜时视野 ×1/4、圆形镜筒遮罩 + 十字分划，并自动隐藏手部模型 · 拉弦/装填箭矢为骨骼动画 · **拉弦时弓臂向内收缩**（r63，见下）· **上弦后弦贴回两弓臂之间**（不往后拉，见下）· **有效射程 40 格** |

> **十字弩外形（r61）**：换成参考网格 `模型/十字弩_v2.bbmodel` 那把**现代复合弩**（窄弓臂 + 高导轨 + 枪式握把 + 镜筒 + 线缆），
> 由 `tools/crossbow_vox.py` **表面体素化**成 824 个方块（逐格从原 512² 贴图采样 UV）。
> 骨骼名 / 握把原点 / 显示缩放都保持原样，所以武器动画、手部锚点不用重写。
| **AWP 栓动狙击枪** | .338 狙击弹 | **单发 24 点伤害**（12 颗心，一枪基本带走）· **5 发弹匣 + 膛内 1 发**· 栓动（必须膛内有弹才能击发）· **每发后自动拉栓抛壳**（拉机柄抬 **88°**、枪机后退 **3.4px**、弹壳翻滚抛出，约 1.4 s 一发）· **8 倍镜**（右键抵肩）· 腰射散布大、抵肩几乎指哪打哪 · **有效射程 96 格**（射程内重力 0.004，比步枪弹更平）· 第一人称**双手：右手握把/拉栓、左手托护木** |
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
| **4 倍瞄准镜** `scope_4x` | 开镜**不铺整屏遮罩**：枪本体与手臂一起抬起来瞄准（看得见枪与镜环），只叠对称十字分划；变焦是轻微的 ×0.72 |

- 两种瞄具的**光轴参照点**（模型 Y=4.07 / 4.28）写在 `weapon/WeaponMount.java` 里，
  举枪时会被顶到屏幕正中 —— 也就是说“瞄具装在哪，准镜就对哪”，**改模型高度必须同步改这里**
  （r67 把护木导轨齿顶抬到瞄准线 3.44，两个参照点也随之 +0.28）
- 目前只能在创造模式「六相月灾」页签取用（还没加合成配方）

> **AWP 的 8 倍镜（r79，r83 改样式）**：不是装在导轨上的配件，而是枪自带的 —— 按住右键抵肩，
> 把**镜筒光轴**顶到屏幕正中、**枪与手臂一起抬起来瞄准**（看得见枪与八棱镜环）；
> r83 起**不再铺整屏近黑遮罩**，只叠 **duplex 双柱式十字分划**（外侧粗柱 / 内侧细线（贯穿中心不断开）/
> 线上每 r/4 一个密位点 / 中心暖色亮点，见 `client/ClientEvents.java#drawCrossReticle`）。
> ⚠️ **变焦只能给轻微的（×0.72 ≈ 1.4 倍）**：原版第一人称手持渲染用的是**同一个投影矩阵**
> （`ItemInHandRenderer` 里没有自己的 perspective）⇒ 强变焦（1/8、1/4）会把枪本体一起放大 4~8 倍、
> 糊满全屏（vanilla 望远镜正因此把手藏起来）。试过的「在眼睛处乘 1/倍率反向缩放」方案在游戏里不可靠
> （r83 实测把枪缩成了一根细针），已回退。要真正做到「强变焦 + 看得见枪」，必须改成
> **自己用独立投影画枪并立刻 flush**（cancel `RenderHandEvent`，自己调 BEWLR + 手臂）。
> 整屏镜筒遮罩现在只剩十字弩在用。
> 光轴参照点 = 模型 Y 3.15（`WeaponMount.AWP_SCOPE_Y`，必须与 `tools/awp_gen.py` 打印的 `SCOPE_AXIS` 一致）。

### 双手持枪（第一人称）

原版对**非空物品**只画物品、不画手臂（`renderArmWithItem` 里只有空手才走 `renderPlayerArm`），
所以枪看着像浮在空中。现在主手拿 AKM / 十字弩 / **AWP** 时，用**玩家自己的皮肤**另外补画两条手臂：
**右手始终握在握把上**，左手则按动作走（见 `client/WeaponArms.java`）：

| 武器 | 左手动作（按换弹读条推进） |
|---|---|
| **AKM** | 托护木 → 抓住弹匣抽出来（跟着弹匣下坠/前倾）→ 满弹匣升上来时扶着往上推 → 换到拉机柄拉栓上膛 → 回护木 |
| **十字弩** | 托护木 → 抓住弩弦往后拉（跟着弦心）→ 松手下去取箭 → 把箭推上箭槽 → 回护木 |
| **AWP** | 托护木（**拉栓时不动**，栓动步枪的支撑手就该留在原地）→ 换弹时伸手抓弹匣、跟着它下坠/前倾 → 回护木 |

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
- **AWP 是唯一的「右手干活」武器（r80~r82）**：右手平时握把（食指在扳机上），**拉栓时抬起来抓拉机柄**
  —— 手的落点与枪机**共用同一份数学**（`boltLiftAt` / `boltBackAt`：抬 62° + 后退 1.9 像素），
  所以手永远不脱手，拉完自动回握把；左手全程托着护木，只在换弹时去抓弹匣
  - 拉栓还带 **6 帧缓冲**（`AwpRifleItem.BOLT_DELAY`）：击发后右手先留在握把上扣扳机，
    **拉栓音效也晚 6 帧响**，不会和枪声糊在一起
  - ★ **扣扳机是程序化推的**：`animation.awp.fire` 那段 11° 键帧**永远轮不到**
    （击发同一帧就开始拉栓，控制器优先级 bolt > fire），现在按 `fireWindow` 推 `trigger` 骨骼
- ★ **第一人称持枪与 AKM 同一套规则**：`move` 骨骼**不做任何额外旋转**，枪管轴线始终平行于视线
  （`AwpGeoModel.computeMovePose` 三个角度恒为 0），枪口 / 抛壳点的世界坐标直接用模型点（`WeaponMount.awp`）
  · r82 曾为了「屏幕上的轴线水平」给过 `HIP_PITCH = -14°`，但那等于让枪在世界里真的朝下 14°
  （用户反馈「枪口下垂」），**已去掉**；以后要调屏幕上的倾斜感请改 display 旋转并同步 `WeaponMount`
- ★ **display 平移按「轴线重合」定**：`awp.json` 的 firstperson TY `4.22 → **1.575**`
  （= `AKM_TY + (AKM 轴线 Y 1.75 − AWP 轴线 Y 1.575)`）⇒ 两把枪的枪管轴线在屏幕上**完全重合**（都是 39.1°），
  也就是「AWP 用 AKM 的持枪方式」。注意 AWP 的握把比它的枪管轴线低 2.65（AKM 的握把正好就在轴线上），
  所以这样摆以后**双手会比 AKM 低 0.165 格** —— 模型原点不同带来的必然结果，不是 bug；
  `mod/tools/_awp_arms.py` 会复核双臂可达性（当前拉伸 0.58~1.31x，硬门槛 0.1~3.0）
- **离线第一人称预览器（r82）**：`python mod/tools/_awpfp.py <geo> <tex> out.png
  [--aim --kick --bp --pitch --hands --rot]` —— 按原版手持变换链从**眼睛**做透视渲染
  （Z-buffer + 透视正确 UV），渲染结果与游戏截图逐像素级对得上，调手持姿态再也不必开游戏；
  `--hands` 会把两条手臂画成方块，校核「手有没有连在枪上」。扫角度用 `mod/tools/_awpscan.py`

> **获取途径**：四把武器本体可在原版探险箱里按概率开出（附赠一份对应弹药）—— 常见箱 6%（地牢 / 矿井 / 神庙 / 前哨 / 村庄武器商…）、稀有箱 16%（古城 / 林宅 / 末地城 / 宝藏 / 堡垒…），权重 复合弓 6 : 十字弩 3 : AKM 1 : **AWP 1**（稀有箱 3 : 4 : 3 : **2**）；也可在创造模式「六相月灾」页签直接取用。

### 弹药与弹药盒

| 物品 | 容量 | 获取 |
|---|---|---|
| 弩箭 | — | 木棍 + 燧石 ×4 |
| 复合弓箭 | — | 木棍 + 燧石 + 线 ×4 |
| 尸毒箭 | — | 复合弓箭 + 尸毒萃取剂 ×2 |
| 7.62×39mm | — | 火药 + 铁粒 ×6 |
| **.338 狙击弹** | — | 火药 + 铁锭 ×4（AWP 专用，与 7.62 **不通用**）|
| 弩箭 / 箭矢 / 步枪弹药盒 | 64 / 96 / 300 | 同一形状 `ppp/p■p/iii`，**中心槽放对应弹药**（三个配方靠中心材料区分，不会互相冲突） |
| **.338 弹药盒** | 120 | 同上形状，**中心槽放 .338 狙击弹**；快捷栏 HUD 占第 4 格 |
| 创造弹药箱 | ∞ | 创造页；**放在物品栏（快捷栏 / 背包 / 副手）里就生效**：四把武器无限供弹，不用手持、不用切弹种 |

### 投掷物

| 物品 | 效果 |
|---|---|
| **碎片手雷 `mud`** | 半径 4.5 格爆炸伤害（最高 14，按距离衰减）+ 短暂缓慢 |
| **震爆弹 `mtx`** | 半径 6 格：**致盲 + 眩晕**（缓慢 III / 反胃 / 虚弱，时长随距离衰减），近距离额外 4 点伤害 |

**操作流程（两者相同）**：

1. **按住右键 1 秒** → 拔出保险销（咔哒声 + 提示）。**拔销途中松手** = 销还没出来，自动插回
2. **拔销之后必须一直按住右键**：压杆被手压着、撞针不会释放 —— 这时可以**潜行 + 右键 1 秒**把销插回去反悔
3. ★ **一松手（没及时按住 / 手滑）⇒ 撞针击发、引信立刻点燃**（r77 写实规则）：
   **5 秒内必须左键丢出去**，不然就在掌心爆（`GrenadeBlasts.detonateInHand`）；
   引信点着后插不回销了，**收回背包 / 换到别的格子也照样烧**，到点炸在身上
4. **左键丢出** —— 飞行中继续读秒，撞到方块弹一下、撞到生物不会停，引信说了算
5. ★ **按 `R` 紧急投掷**（r78）：只要手上（主手或副手）有一颗已拔销 / 引信在烧的雷就丢它
   —— 主手举着枪、副手那颗雷在烧时也能救急（`grenadeInEitherHand`）

| 手雷状态 | 行为 |
|---|---|
| 插着销 | 完全安全，拿多久都行 |
| 销已拔出、**手压着压杆**（按住右键） | 引信未点；可投出，也可潜行 + 右键把销插回 |
| **销已拔出、手松开了** | ★ **撞针击发、引信点燃**（5 秒）—— 丢出去，或在手里爆 |
| **销已拔出、切武器 / 收回背包** | ★ 同样算「脱手」 ⇒ **撞针击发、引信点燃**（r78，`gripped()` 判定）|
| 引信燃烧中（`ARMED`） | 手里 / 背包 / 护甲里都继续烧；右键想插销会被拒绝 |
| **主手举着枪 + 副手有活雷** | 默认按键轮不到它 ⇒ **按 `R` 紧急投掷**（按准星丢出）|
| 开界面 / 切手持物（被动中止） | 手还抓着，**不点火** |

### 月相

六种月相（血月 / 蓝月 / 黄月 + 各自的**超级**版本）**随机出现**，各有专属的月亮颜色与天空颜色
（自画的月盘 + 天穹染色，见 `client/MoonSkyRenderer.java`）：

- ★ **不再是按夜数轮转**（r75）：每夜独立掷骰、六相同权重 ⇒ **可能连着两夜同一个月相，
  也可能几十夜都不出月相**；基础概率 **25%**，连续 10 夜没出之后每夜 +1%（上限 60%）。
  连续无月概率：3 夜 42% / 5 夜 24% / 10 夜 5.6% / 15 夜 1.2% / 20 夜 0.17%
- 月升时全服弹标题与提示、客户端同步（`MoonManager` → `ModNetwork.syncToAll`）

| 月相 | 月亮颜色 | 天顶 / 地平线 | 效果 |
|---|---|---|---|
| **血月** | `#FF4A38` 红 | `#1C0608` / `#521114` | **四波尸潮**（每波 6/9/13/18 只·人）+ **亡灵随时间进化**（黄昏 ×1 → 天亮 ×2）+ **晚上不能睡觉** |
| **蓝月** | `#AECBFF` 淡青蓝 | `#06101F` / `#143A6E` | **玩家获得幸运 I**（僵尸没有任何加成）|
| **黄月** | `#FFD35E` 金 | `#141005` / `#453512` | **作物加速生长**（每 20 tick 催一次）|
| **超级血月** | `#FF6E52` + 大光晕 | `#28070B` / `#6E1616` | 同上 + **尸潮 ×1.5** + **巨箭弹幕** + 长夜不眠 |
| **超级蓝月** | `#D2E8FF` + 大光晕 | `#08142E` / `#1C4A88` | **玩家获得幸运 II** |
| **超级黄月** | `#FFE9A0` + 大光晕 | `#1C1608` / `#57431A` | 作物生长更快（每 7 tick）+ **巨箭弹幕** |

- **尸潮细节（r74）**：固定 **4 波**（波间隔 6 秒），开波与每波都有 action bar 播报；
  **第 14 天（含 28 / 42…）那晚**开波概率 0.35 → 0.75 且规模再 ×1.5；
  **天亮自动收尾**：按离玩家最近排序，每个玩家只留 4 只徘徊者，其余清除，留下的**白天不燃烧**
- **管理指令（OP 2 级 / 单人开作弊，`/hlc` 是简写别名）**：

| 指令 | 作用 |
|---|---|
| `/hexalunar moon set <blood_moon\|blue_moon\|yellow_moon\|super_blood\|super_blue\|super_yellow\|none>` | 强制指定月相（今夜不再掷骰）|
| `/hexalunar moon clear` | 清除月相 = 今夜无月 |
| `/hexalunar moon random` | 立刻按随机规则掷一次 |
| `/hexalunar moon info` | 看状态（已入夜次数 / 当前月相 / 概率 / 连旱夜数 / 尸潮）|
| `/hexalunar moon list` | 列出全部月相 id |
| `/hexalunar moon chance <0~1>` | 改每晚出月相的概率（写进存档）|
| `/hexalunar horde start \| stop \| wave <1~4>` | 手动开 / 停尸潮、单放某一波 |
| `/hexalunar barrage` | 立刻触发巨箭弹幕 |

伴随六种特殊感染者：自爆尸、喷吐尸、蛮兵尸、巨尸、突袭骷髅、剧毒骷髅。

---

## 三、项目结构

```
mod/
├── src/main/java/cn/blockforge/generated/hexalunarcalamity/
│   ├── weapon/     枪械、弩、弓、**瞄具**、射击数学（AkmRifleItem / **AwpRifleItem** / WeaponMount / Sights / Ballistics / WeaponFx）
│   ├── item/       弹药盒、创造弹药箱、解毒剂、手雷（GrenadeItem）
│   ├── entity/     弹丸与投掷物（子弹、弩箭、箭矢、手雷 GrenadeEntity）+ 特殊感染者
│   ├── client/     输入、FOV/瞄准、HUD、**GeckoLib 模型与渲染器**（*GeoModel / *GeoRenderer）、物品属性注册
│   ├── net/        网络包（月相同步 / 命中反馈 / 开火 / 装填）
│   ├── registry/   物品、实体、音效、效果、创造页签
│   └── moon/       月相管理（MoonPhase / MoonManager / MoonPhaseData / **MoonCommands**）+ 月相效果（**MoonBlessings**）+ 僵尸进化（ZombieEvolution）
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

19. **javac 只报「找不到符号」而 `tools/_check.py` 会把明细过滤掉**
    r75 一次报 13 个「找不到符号」但看不出原因，真因有两个：
    · **`Component` 接口没有 `withStyle()`**（只有 `MutableComponent` 有）⇒ 辅助方法声明返回 `Component` 时，
      调用处 `.withStyle(...)` 全栈编译不过；把返回类型改成 `MutableComponent` 即可。
    · **局部变量会遮蔽同名方法**：`ServerLevel level = level(src);` 里正在声明的 `level`
      从声明处就开始生效 ⇒ 右边的 `level(src)` 被当成访问变量 ⇒ 一行代码 13 个错误。方法改名 `targetLevel`。
    取明细：`cmd /c "gradlew.bat compileJava --offline --console=plain > build\err.log 2>&1"` 再读日志
    （`--offline` 顺带绕开本机偶发的依赖卡网络）。改完记得用 `get_errors`（语言服务器）交叉核对。

20. **★ 枪管轴线与视线平行 ⇒ 它在屏幕上「必然是斜的」（这是透视，不是模型歪）**
    一阶近似：相机在眼睛处朝 −Z，枪管轴线上离相机 t 处的点投影屏幕坐标 ∝ `offset / t`
    ⇒ **近端（枪托）远远偏离画面中心、远端（枪口）贴着中心**。实测 AWP 屏幕倾角 **21.6°**
    （AKM 更斜 **40°**，因为它的 display TY 更低、枪整体更靠下）。
    所以「枪看着斜着往上翘、枪托往下掉」不是模型长歪了，也**不能靠挪 display 平移修** ——
    只能给一个**俯仰角**：让枪管轴线不再与视线平行，它的收敛点就会离开屏幕中心。
    AWP 用 `AwpGeoModel.HIP_PITCH = -14°`（绕 `move` pivot 下压），轴线在屏幕上变成水平（-0.2°）；
    **举枪时必须归零**（镜筒光轴不能歪），**第三人称也不加**（`AwpGeoRenderer.firstPerson`）。
    ⚠️ 加了角度以后，**枪口 / 抛壳点的世界坐标必须同步转**（`WeaponMount.awpHipPitch`），
    否则弹道与枪口焰会和枪管对不上（这个项目的弹道是从模型点出发的）。
    离线定位：`python mod/tools/_awpfp.py <geo> <tex> out.png [--pitch -14]`（会打印轴线倾角）、
    `mod/tools/_awpscan.py`（扫角度）。

21. **`setCustomAnimations` 在动画控制器之后跑 ⇒ 程序化推骨骼一定赢，但也可能「让动画白播」**
    GeckoLib 的顺序是：控制器挑一段动画 → 按时间写骨骼 → 再调 `setCustomAnimations` 让你覆盖。
    所以「控制器选了 `bolt` 动画」和「我在 `setCustomAnimations` 里把 `bolt` 骨骼设成我算的值」
    完全不冲突 —— 后者是最终值（AWP 的拉栓/抛壳/弹匣/扳机全靠这条）。
    **反面**：某段动画的骨骼如果**每一根**都被程序化覆盖，那它就等于没播。
    AWP 的 `animation.awp.fire` 就这么消失过 —— 击发**同一帧**就开始拉栓，控制器优先级 `bolt > fire`
    ⇒ 那段 11° 扣扳机键帧**永远轮不到**。要用「按下扳机的进度」就把窗口时间存进 NBT
    （`HlcFireAt` + `AwpRifleItem.fireWindow`），再自己推骨骼。

22. **参考包坐标系与本项目相反时，要把旋转「烘进几何」，不能挂在根骨骼上**
    AWP 参考包是 **X = 枪口向前**，本项目是 **枪口 = −Z**。看着最省事的做法是加一根 `rotY = 90°`
    的根骨骼 —— 但**子骨骼的位移是写在父级局部系里的**：`move` 骨骼往 Z 推会变成「往侧面推」、
    抬枪会变成歪着抬。正确做法是在生成几何时就把 `R_y(+90°)` 乘进每个顶点
    （见 `tools/awp_gen.py`：`(x, y, z) → (z, y, -x)`），导出的 geo 里**没有任何根旋转**，
    后续动画/骨骼位移的语义才和 AKM、十字弩一致。

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
| `_gren_pin.py` | 手雷 / 震爆弹**保险销行为**离线自检：核对手持状态机规则（尤其是「手里攥着永远不点燃引信」这条硬保证）、检查语言键，并把状态转移表打印出来 |
| `_moon_r74.py` | 月相系统离线自检：月相数值（蓝=幸运 / 黄=催作物 / 血=四波尸潮）、尸潮规模推演、**随机出现与连旱概率**、指令树完整性 |
| `_joml_probe/`（Java） | 第一人称手臂离线验算：`JomlProbe` 验 JOML 旋转约定（`Matrix3f` 构造顺序 / `rotateAxis` 语义），`ArmSim` 按 `WeaponArms` 同一套数学算出双臂方块 8 个角在相机空间的位置并投影到屏幕，顺带告警「是否越过相机平面」（越过了就是糊屏） |
| `crossbow_vox.py` | 把**参考网格**（`模型/十字弩_v2.bbmodel`，11 个 mesh 部件）**表面体素化**成 GeckoLib 方块模型：逐格从原贴图采 UV、按 mesh 名分骨骼、弦/弦心/弩箭另外用方块画；末尾打印并自检「拉满时两段弦内端是否正好落在弦心」。`--step` 调体素大小（0.45 → ~820 方块） |
| `_cb_flex.py` | 十字弩**弓臂内收**的离线验算 + 姿态烘焙：打印「弓臂外端往内/往后走了多少」「弦内端相对弦心的偏差」，`--bake 1.0` 能把该姿态烘成 `build/cb_flex_*.geo.json` 直接用 `geo_texview.py` 出图。<br>★ 常数（`FLEX_DEG` / `FLEX_PX` / `FLEX_PZ`）必须与 `client/CrossbowGeoModel.java` 一致 |
| `_scopemock.py` | 离线复刻倍镜遮罩绘制数学出 PNG（调分划参数不用反复进游戏） |
| `gen_sight_icons.py` | 生成红点 / 4 倍镜的物品图标 PNG |
| `awp_gen.py` | **AWP 模型生成器**：把参考包 `模型/AWP_Printstream_Minecraft` 转成 GeckoLib 用的 geo + 贴图（烘 `R_y(+90°)`、缩放 0.75、逐面 UV 重映射、重排成 512² 图集 @19 像素/单位），再按本项目的骨骼/动画约定做二次造型（机匣瘦身、枪管加长、倍镜改八边形、扳机拆骨骼、弹壳双段、点阵明细…）；末尾打印骨骼表 / 包围盒 / 图集密度 / 关键模型点。**流光遮罩由它自己画**（参考图几乎全白，`gen_glowmask.py` 的百分位法失效，那个脚本已排除 awp） |
| `install_awp_sounds.py` | 把 `模型/` 里用户提供的音频改名拷进 `sounds/weapon/`（`awp枪声.ogg` / `AWP狙击步枪换弹音效.ogg` / **`拉栓上膛.ogg`**）|
| `gen_ammo338_icons.py` | 画 `.338 狙击弹` 与 `.338 弹药盒` 的 16×16 图标（并出大图预览）|
| `_awpfp.py` | ★ **第一人称离线预览器**：按原版手持变换链（`ItemInHandRenderer` + `ItemRenderer` 的 display）从**眼睛**做**透视**渲染（Z-buffer + 透视正确 UV），与游戏截图逐像素级对得上。`--aim / --kick / --bp / --pitch / --hands / --rot / --h --aspect` 可复现举枪 / 后坐 / 拉栓 / 下压角 / 双臂，并打印**枪管轴线在屏幕上的倾角**（调姿态不用开游戏）|
| `_awpscan.py` | 扫描「俯仰角 ↦ 枪管轴线屏幕倾角」（display 旋转 / `move` 骨骼旋转两套都算），用来定腰射下压角 |
| `_awp_arms.py` | AWP 双手**可达性校核**：把手部落点换算到相机空间，检查肩距是否在 `drawArm` 的 (0.1, 3.0) 格内、拉伸倍率多少、在画面哪个位置 |
| `_awpanim.py` | 把某段动画按时间点烘成静态 geo 再出图（拉栓 / 抛壳 / 换弹 / 开镜的**故事板**）|
| `_oggdur.py` | 不装第三方库读 Ogg 时长（解析 page 的 granule / 采样率）—— 配音效前先量长度，再用 `playSound` 的 pitch 对齐动作时长 |
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
| **武器形状 / 贴图** | `mod/tools/akm_v3.py`（弩 `crossbow_vox.py`（体素化参考网格）、弓 `bow_v3.py`、手雷 `grenade_v3.py`、震爆弹 `flashbang_v3.py`、**AWP `awp_gen.py`**）→ 再跑 `install_models.py` + `gen_glowmask.py`（awp 的遮罩由 `awp_gen.py` 自己画，不用跑后者）|
| **AWP 腰射姿态 / 屏幕斜不斜** | `client/AwpGeoModel.java` 的 `HIP_PITCH`（**-14°**，举枪时 ×(1-aim) 归零、第三人称不加）+ `weapon/WeaponMount.java` 的 `AWP_HIP_PITCH` / `awpHipPitch()`（**两处必须一致**，后者给枪口/抛壳取点用）；离线扫角 `tools/_awpscan.py`、看效果 `tools/_awpfp.py --pitch -14` |
| **AWP 数值（弹匣 / 时序 / 弹道）** | `weapon/AwpRifleItem.java`（`MAG_SIZE` 5 · `RELOAD_TICKS` 44 · `BOLT_TICKS` 22 · `BOLT_DELAY` 6 · `CYCLE_TICKS` 28 · `BULLET_SPEED` 6.2 · `SCOPE_ZOOM` 8）+ `Ballistics.AWP_RANGE` / `AWP_IN_RANGE_GRAVITY` + `BulletEntity.SNIPER_DAMAGE`（24；用初速 >5.5 识别狙击弹）|
| **AWP 栓动 / 抛壳 / 扳机 / 手** | `client/AwpGeoModel.java`：`boltLiftAt` / `boltBackAt`（**骨骼与右手共用**）、`BOLT_LIFT` 62° / `BOLT_BACK` 1.9px、抛壳轨迹常数（`CASE_T0/T1` / `CASE_VX/Y/G` / 三轴翻滚）、`triggerPullAt`（按 `fireWindow` 推扳机）；左手目标 `ARM_SUPPORT`（**不要放到 z<-4.2**，那儿是露出的枪管 + 折叠两脚架）|
| **瞄具挂点高度 / 举枪对心** | `weapon/WeaponMount.java`（`SIGHT_Y` = 照门顶/准星顶/**导轨齿顶** = 3.44、`AKM_DOT_Y` / `AKM_SCOPE_Y` / `akmAimDy`）—— **必须**与生成器 `akm_v3.py` 里的 `SIGHT_Y` / `RAIL_LIFT` 及 `build_dot_sight` / `build_scope_4x` 的注释值一致 |
| **红点 / 倍镜显示逻辑** | `client/AkmGeoModel.java`（`sightNow` 隐藏骨骼 + 举枪位移）+ `client/ClientEvents.java`（`scoping` / `drawRedDot` / `drawScopeOverlay`） |
| **枪口/抛壳位置、射击方向** | `weapon/WeaponMount.java`（`AKM_MUZZLE` / `AKM_EJECT`）+ `AkmRifleItem.fire()`；子弹从模型点出发、朝准星收敛点飞（收敛上限 = **归零距离**：举枪 16 / 腰射 24 格，`tools/_akm_ballistic.py` 验算） |
| **手持动作幅度 / 速度** | `client/WeaponAnim.java`（冲量大小与衰减）+ `client/WeaponPose.java`（折算成 display 增量的数值） |
| **后坐幅度 / 镜头反馈强度** | 各 `client/*GeoModel.java` 的 `KICK_BACK` 与 `kick` 计算（AKM 1.35px / 弩 0.95px）；`camera` 骨骼只在 `firing()` 时叠加，换弹期间镜头必须为零 |
| **谁的手持变换被接管** | `client/WeaponHandGrip.java`（`applyForgeHandTransform` 的返回与基准平移）+ 各 `client/*ItemClientExtensions.java` |
| **骨骼该不该被推（渲染语境）** | `client/AkmGeoRenderer.java#isHand` + 各 `*GeoModel.handPass`：GUI 图标 / 掉落物 / 展示框一律不推 |
| **双手持枪的手臂摆位** | `client/WeaponArms.java`（肩点 / 臂长 / 握把锚点）+ 各 `*GeoModel` 里的手部目标点；离线核对 `tools/_armstory.py` |
| 手持动作是否生效 | `client/AnimatedWeaponModel.java` + `ModClient.onModifyBakingResult`；日志里会打“手持动作动画已启用：包装了 N 个武器模型” |
| AKM 弹匣容量 / 换弹时长 / 射速 / 散布 | `weapon/AkmRifleItem.java`（`MAG_SIZE` / `RELOAD_TICKS` / `FIRE_INTERVAL` / `fire()`） |
| 弩的倍镜倍率 | `weapon/CrossbowWeaponItem.java` 的 `SCOPE_ZOOM`（`4.0F` = 4 倍）；开镜 FOV 由 `ClientEvents` 用 `1/SCOPE_ZOOM` 计算 |
| **弩上弦 / 装填时机** | `weapon/CrossbowWeaponItem.java`：`RELOAD_TICKS`（上弦时长）、`tryStartReload()`（真正开始上弦，只有 R 键与右键两个入口）、`serverFire()`（击发后**只复位不复装**）、`cocked()`（图标/弩箭显隐就靠它） |
| 手雷拔销时长 / 引信时长 / 投掷力道 | `item/GrenadeItem.java`（`PIN_TICKS` 20 / `FUSE_TICKS` 100 / **`AUTO_BACK_TICKS` 30（刚拔完就松手 ⇒ 自动插回销）** / `THROW_LIFT_DEG` 上抬角 / `THROW_INACCURACY`）；**各弹种初速**在 `FragGrenadeItem`（1.30）与 `FlashbangItem`（1.38）的构造参数 |
| **手雷动作与手（拔销/投掷/左手拉环）** | `client/GrenadePose.java`（move 骨骼姿态 / 左右手模型点 / 手雷专用肩点）+ `client/WeaponArms.renderGrenade`；离线故事板 `tools/_gren_story.py mud\|flashbang` |
| 手雷引信、伤害、效果半径 | `entity/GrenadeEntity.java` |
| 三武器的有效射程与超距下坠 | `weapon/Ballistics.java`（`AKM_RANGE` / `BOLT_RANGE` / `BOW_RANGE` 与各 `*_IN_RANGE_GRAVITY`） |
| 武器手持姿态 / 物品栏图标大小 | 各 `models/item/*.json` 的 `display`，或跑 `tools/scale_weapons.py` |
| **弩弓臂内收 / 后弯 / 长短 / 弦粗细** | `client/CrossbowGeoModel.java` 的 `FLEX_DEG` / `FLEX_BACK` / `FLEX_PX` / `FLEX_PZ`（**内收量**与**弦拉动量**是两个自变量：上膛后 flexAmt=1、draw=0 ⇒ 弓臂保持内敛）；**弓臂长度/粗细**与**弦/弦心/尾羽的尺寸**在 `tools/crossbow_vox.py`（`LIMB_SX` / `LIMB_SY` / 画弦处的 `th` / 弦心与尾羽的 box）；`SKIP_MESHES` 决定哪些参考网格**不**生成方块（弦与线缆必须跳过，否则就是“又厚又分叉”）（改完跑生成器，它会把新的 TIP_X / FLEX_PX / FLEX_PZ 打印出来；再手动装 `crossbow_geo.*`）|
| **第一人称手臂大小 / 位置** | `client/WeaponArms.java` 的 `SHOULDER_R/L`（必须放在画面外，否则一片色块挡住枪）、`THICK`、`ROLL_R/L`；离线故事板 `tools/_armstory.py akm|crossbow` |
| **开火时的视角反馈** | `client/AkmGeoModel.java#zeroCamera`（清零 = 不点头）+ `client/ClientEvents.java#applyAkmCamera`（camera 骨骼→视角的管道）；要做「后坐上跳」就在 `computeMovePose` 里用冲量自己做 |
| **月相效果** | 颜色（月亮/光晕/天顶/地平线/雾色/全屏叠色/尘埃）全在 `moon/MoonPhase.java` 枚举里；蓝月幸运 / 黄月催作物 / 血月不眠 + 天亮收尾在 `moon/MoonBlessings.java`；四波尸潮在 `moon/MoonManager.java`；改配色跑一遍 `tools/_moonsky_mock.py` |
| **月相出现概率 / 随机规则** | `moon/MoonManager.java`（`DEFAULT_MOON_CHANCE` 0.25、`DROUGHT_GRACE` 10、`DROUGHT_STEP` 0.01、上限 0.60）+ 存档字段 `MoonPhaseData.moonChance`（也可用 `/hexalunar moon chance` 改） |
| **新增月相 / 改指令** | 枚举加一项（`moon/MoonPhase.java`：7 个颜色参数 + `superMoon`）+ `lang` 补 `moon.<id>` / `moon.title.<id>`；指令树在 `moon/MoonCommands.java` |

---

## 七、更新日志（本次开发）

> 版本 `1.0.0-r82`

- **AWP：腰射姿态压平 + 补齐生存获取**
  - ★ **枪不再「斜着往上翘、枪托往下掉」**：枪管轴线与视线平行时，透视下它的投影必然收敛到
    屏幕正中（实测屏幕倾角 21.6°）。现在腰射给 `move` 骨骼 **`HIP_PITCH = -14°`** 的枪口下压角，
    轴线在屏幕上变成水平（-0.2°）；举枪线性归零、第三人称不加，
    **枪口 / 抛壳点的世界坐标同步转同一个角**（`WeaponMount.awpHipPitch`）
  - 新增 **`tools/_awpfp.py`（第一人称离线透视预览器）** + `tools/_awpscan.py`，本轮的角度就是它扫出来的
  - 补齐配方：`.338 狙击弹 ×4`（火药 + 铁锭）、`.338 弹药盒`（木板围框 + 中心弹 + 三铁锭）；
    AWP 进武器箱战利品池（常见箱权重 1 / 稀有箱 2，附 6 / 10 发 .338）
  - 修中文名错字：`AWP 德动狙击枪` → **`AWP 栓动狙击枪`**

> 版本 `1.0.0-r81`

- **AWP：拉栓音效 + 右手真的去拉栓 + 扣扳机看得见了**
  - 用户提供的 `模型/拉栓上膛.ogg` → `sounds/weapon/bolt_1.ogg`，新增音效事件 `ModSounds.BOLT`，
    **AKM 与 AWP 共用**（AKM 打空自动拉栓也补上了声音，以前只有动作没声）；装瞄具那声「咔」保留 `akm_bolt`
  - **击发后顿 6 帧（`BOLT_DELAY`）再拉栓**：这 6 帧右手还握在握把上扣扳机，**拉栓音效也晚 6 帧响**
    （`TAG_BOLT_SFX` 定时），不会和枪声糊在一起；`CYCLE_TICKS = 28`（≈1.4 s 一发，约 43 RPM）
  - **右手拉栓**：`rightHandPx` 把「相对 bolt pivot 的握点」按抬 62° 旋转 + 后退 1.9px，
    与枪机**共用同一份数学**（`boltLiftAt` / `boltBackAt`）—— 手永远不脱手
  - ★ **修正「扳机从来不扣」**：`animation.awp.fire` 那段 11° 键帧**永远轮不到**（击发同一帧就开
    始拉栓，控制器优先级 bolt > fire），现改成按 `fireWindow` **程序化推 `trigger` 骨骼**

> 版本 `1.0.0-r80`

- **AWP：第一人称双手**（`WeaponArms.renderAwp` + `AwpGeoModel.rightHandPx / leftHandPx`）
  - 右手握把（枪本来就画在右手位置），左手托在护木下方；换弹时左手跟着弹匣一起下坠、前倾
    （与弹匣骨骼共用 `magDropAt`，所以手与匣不会脱开）
  - 手臂经 `GunFrame` 换到相机空间 ⇒ 举枪 / 后坐 / 拉栓时**枪动、手一定跟着动**；
    离线可达性校核 `tools/_awp_arms.py`

> 版本 `1.0.0-r79`

- **AWP 栓动狙击枪整套接入**（参考包 `模型/AWP_Printstream_Minecraft`）
  - **模型**：`tools/awp_gen.py` 烘 `R_y(+90°)` + 缩放 0.75 + 逐面 UV 重映射 + 重排 512² 图集（19 px/单位），
    13 骨骼 / 58 方块 / 348 四边面；坐标约定：**枪口 = -Z、上 = +Y、原点 = 机匣中心、握把（`move`）在 (0, -1.07, 1.31)**
  - **弹道**：`.338` 初速 6.2 · **有效射程 96 格** · 射程内重力 0.004 · 命中 **24 点伤害**
    （`BulletEntity.SNIPER_DAMAGE`，用初速 >5.5 区分狙击弹，不必新增同步字段）
  - **8 倍镜**：`SCOPE_ZOOM = 8` + 圆形镜筒遮罩 + 新增 **duplex 双柱式十字分划**；HUD 显示「弹匣 + 膛内」
  - **弹药**：`.338 狙击弹` / `.338 弹药盒`（`AmmoType.SNIPER`，容量 120，快捷栏 HUD 第 4 格）
  - **音效**：用户提供的 `模型/awp枪声.ogg`、`模型/AWP狙击步枪换弹音效.ogg`（中文名由 `install_awp_sounds.py` 改名拷入）

> 版本 `1.0.0-r78`

- **手雷：切武器 = 松手（点火）、`R` 键紧急投掷**
  - 销已拔出后**切到别的武器 / 收回背包**，压杆同样算脱手 ⇒ 撞针击发、引信点燃
    （`gripped()` 判定；主手一举枪，副手那颗就等于被胳臂夹着）
  - 新增 **`R` 紧急投掷**：手上（主手或副手）有已拔销 / 引信在烧的雷时，`R` 不再是换弹而是
    立刻按准星丢出（`grenadeInEitherHand` + `serverThrow` 回退）—— 专门解决「拔完销正好碰到
    敌对生物、主手还举着枪」的处境

> 版本 `1.0.0-r77`

- **手雷 / 震爆弹：改成写实规则（撞针会真的击发）**
  - 拔销之后**必须一直按住右键**：一松手（没及时按住 / 手滑）⇒ `lightFuse()` 点燃引信，
    **5 秒内必须丢出去**，不然 `GrenadeBlasts.detonateInHand()` 在掌心起爆
  - 引信点着后插不回销了（`fuse_no_pin_back`）；**收回背包 / 换格也照样烧**，到点爆在身上
  - 新增网络包 `HOLD_CANCEL`：开界面 / 切手持物属于「手还抓着」，**不点火**
  - 副手的雷 + 主手枪械 = 被胳臂夹着（销自动弹回）—— 顺便避开「丢不出去只能等死」

> 版本 `1.0.0-r76`

- **修复 Mod 列表里的显示名乱码**：`build.gradle` 的 `mod_name` 曾被写坏成
  `閸忣厾娴夐張鍫绩`（UTF-8 双重编码），Mod 列表标题因此显示为乱码；现恢复为 `六相月灾`。
  新增 `tools/_namecheck.py`：直接读 **jar 里的 `META-INF/mods.toml`**，校验 displayName /
  description 的原始 UTF-8 字节（现在打印 `utf-8 bytes = e585ad e79bb8 e69c88 e781be` ✓）

> 版本 `1.0.0-r75`

- **月相改成随机 + 管理指令 + 手雷保险销手感**
  - 月相不再按夜数轮转：每夜独立掷骰（基础 25% + 旱情补偿），**可能连着两夜同一个月相，
    也可能连旱几十夜**；随时可用 `/hexalunar moon set|random|chance|info` 调用（`/hlc` 简写）
  - 尸潮波次推进移出血月分支 ⇒ 无月之夜用指令开的尸潮也能走完 4 波
  - 手雷 / 震爆弹：**刚拔完 1.5 秒内松手 ⇒ 保险销自动插回**；手里攥着（任何状态）
    **永远不点燃引信**（`ARMED` 只属于飞行中的抛射体，背包 / 副手 / 护甲里的雷一律折回安全态）

> 版本 `1.0.0-r74`

- **六相月灾重做：每个月相各管各的事**
  - **蓝月 / 超级蓝月 = 玩家的幸运 I / II**（`MoonBlessings` 每 40 tick 续 300 tick），
    **僵尸不再有任何加成** —— 旧版蓝月的移速修改器（`MoonSpawnEvents` 里的 `AttributeModifier`）已删
  - **黄月 / 超级黄月 = 只催作物**：每 20 / 7 tick 在玩家 18 格内抽 24 处作物替它们跑一次原版
    `randomTick`（`BlockTags.CROPS` / `SAPLINGS` 通吃）；**掉落翻倍已删**
  - **血月 / 超级血月 = 四波尸潮 + 亡灵随时间进化 + 不能睡觉**：
    尸潮固定 4 波（每波 6/9/13/18 只·人，间隔 6 秒，超级 ×1.5，第 14 天倍数那晚概率 0.75 且规模 ×1.5）；
    `ZombieEvolution.nightRamp()` 让进化概率黄昏 ×1 → 天亮 ×2；
    `PlayerSleepInBedEvent` → `NOT_POSSIBLE_NOW`；天亮 `dawnCleanup()` 清场只留 4 只孅徊者、白天不燃烧
  - HUD 第三行跟着月相走：蓝 = 幸运等级 / 黄 = 作物加速 / 血 = 进化% + 夜不能寐

> 版本 `1.0.0-r73`

- **十字弩：弦挂回弓臂桁上、上弦后弦成 V、图标也分两种姿态、离手自动退弦退箭**
  - **弦的位置（根因）**：`scale_limbs()` 原来按弓臂包围盒**中心**做 Y 方向放大（×1.25）⇒
    弓臂**桁部被抬高**，而弦还在参考高度 ⇒ 弦看上去掉在桁下面、两头也够不到桁。
    现改成**以弦面为锚点**放大：桁部原地不动、只有弓臂肚子变深。
    实测（生成器自检）：弓臂桁体素顶面 y 1.66｜弦面 y 1.70｜导轨顶面 y 1.60 ⇒ 弦正好挂在桁上、
    跟导轨顶面齐平（弩箭尾落在弦心上）。同时把弦/线缆的 `tip_x`/`str_y` 也回归参考值
    （弦半跨 5.371、弦面 1.700）。
  - **未上弦 = 未缩放的 U + 一条直线弦**（弦平行于导轨顶面）；**上弦后 = 缩小的 U + V 字形弦**：
    `draw = cocked ? 1.0F : …` —— 上弦完成后弦**保持拉着**（弦心/弩箭都在后位），击发才弹回（带弦震动）。
  - **图标（GUI / 掉落物 / 展示框）也分两种姿态**（`staticPose()` 按 `cockedNow`）：
    已上弦 → 弓臂内敛 + 弦成 V + 弩箭在槽；未上弦 → 弓臂张开 + 弦贴回弓臂之间 + 看不到弩箭。
  - **离手就自动退弦**（`CrossbowWeaponItem.inventoryTick`，判据是“主手/副手都不再拿着它”）：
    取消正在进行的上弦、`cocked` 置回 false，并**把已经上好弦的那支弩箭退回背包**
    （新增 `AmmoUtil.refund()`；创造模式/有创造弹药盒时不折腾），同时给一句提示。

> 版本 `1.0.0-r72`

- **十字弩：击发后不再自动上弦，什么时候装填由玩家决定**
  - `serverFire()` 末尾原来会立刻 `tryStartReload()`（“击发后弦复位：立刻开始下一轮上弦”）——
    现在**只把 `cocked` 置回 false 就停下**：弩箭不在箭槽、弦在初始位置、弓臂也回到张开姿态，
    图标（`staticPose()` + `cockedNow`）同步显示“未使用”样子（拿在手上 / 放在背包里都一样）。
  - **上弦入口改成两个都行**：`use()`（右键）——未上弦时右键 = 上弦装填（1.5 秒，拉弦 + 箭入槽）；
    上弦之后右键才是开镜瞮准；R 键（`serverReload`）仍旧可以用。
  - 未上弦时左键不再“自动上弦”，只空响 + 屏幕提示「未上弦：右键（或 R 键）上弦装填」
    （新语言条目 `message.hexalunar_calamity.need_cock`）；客户端也同步：没上弦时按住左键
    不会每 5 tick 刷一次请求（只在按下的那一下发一次）。
  - 跨包提示文案重写：`tooltip.hexalunar_calamity.crossbow_controls`

> 版本 `1.0.0-r71`

- **十字弩：按参考照片加回「两根线缆」（细线、交叉）**
  - 参考图（`模型/` 里的实物照片）上，两根线从两片弓臂梢斜向内、在弦前方**交叉**。
    现在在 `tools/crossbow_vox.py` 里给每侧再画一根 **0.07 像素的细线缆**（颜色 `COL_CABLE`，
    新色块 `PAT_CABLE`），它们就放在 `string_left` / `string_right` **骨骼内部** ⇒
    拉弦与弓臂内收时跟弦一起走（“使用时”的样子），静止时就是照片里那两根交叉的线（“未使用时”）。
    · 线缆长度 = 弓臂桁 + 0.85 像素（越过中线 ⇒ 交叉）；两根分别放在弦后方 0.50 / 0.66 像素、
      下方 0.26 像素处，交叉处一前一后，不会 z-fighting
  - 弦/弦心/尾羽尺寸与弓臂跨度同 r70（弦 0.07 像素、跨度 10.32）；改用它的纹理重生成后
    `crossbow_geo_glowmask.png` 也跟着重算（顺带把 r67 改了 AKM 贴图后一直没更新的
    `akm_geo_glowmask.png` 一起刷新，4% 像素的高光位置归位）
  - 离线核对：`python tools/_cb_flex.py`（弦/弦心/弩箭三者仍严格一致，四状态全 OK）

> 版本 `1.0.0-r70`

- **十字弩：弦细到 0.07 像素、拆掉假弦、弓臂再外扩、上完膛保持内敛**
  - **「又厚又分叉」的真凶找到了**：参考网格的 `string`（薄壳）与 `cables`（线缆）被体素化成
    **0.45 像素的方块串**，位置恰好压在运行时那根细弦旁边 ——
    string 在 y 1.67~1.74、|x| 到 5.37；cables 在 y 1.21~2.11、|x| 到 **5.82（比弓臂梢 5.16 还外）**。
    于是画面上是「一根细弦 + 一串粗方块」，弓臂内收时两者还会分开 ⇒ 看着就是厚 + 分叉。
    现在 `SKIP_MESHES = ('cables', 'string')`（参考 string 仍参与 TIP_X / NOCK_Z0 / 包围盒计算，
    只是不生成方块）：body 体素 **464 → 339**，body 里再无 |x|>2.2 的方块。
  - **弦与相关小件再收细**：弦方块截面 0.10 → **0.07 像素**（th 0.05 → 0.035）；
    弦心（缠绳）1.2×0.52×0.52 → **0.9×0.32×0.32**；弩箭尾羽 0.72×0.6×0.48 → **0.52×0.42×0.40**
    （从射手视角看，这三块才是「厚」的主因）。
  - **未使用时弓臂再向外扩**：`LIMB_SX` 1.9 → **2.05**（跨度 9.76 → **10.32** 像素，每侧再多探出 0.28）；
    同步 `CrossbowGeoModel.TIP_X` 4.978 → **5.371**、`STRING_LEN` 5.293 → **5.665**（`tools/_cb_flex.py` 同步）。
  - **上完膛保持内敛**：把「弓臂内收量」与「弦拉动量」拆成两个自变量（`flexAmt` / `draw`）：
    拉弦时 flexAmt 跟着 draw 走（0→1）；**装填完成（cocked）后 flexAmt 钉在 1** —— 弓臂不回弹，
    击发（cocked → false）之后才张开。弦本身仍按原设计在上膛后贴回两弓臂之间（draw = 0，
    否则弦心离镜头太近会像一根浮在弩上方的「∧」）。弦心 / 弩箭 / 左手三者的位移统一走
    `nockTravel(flexAmt, draw)`，仍然严格一致（离线自检四状态全 OK）。
  - 离线验算：`python tools/_cb_flex.py`（新增「上膛保持内敛」一行；出图用 `--bake 0 --flex 1`）

> 版本 `1.0.0-r69`

- **手雷 / 震爆弹：手上真的有动作了（拔销拽销、单手投掷、抛物线）**
  - **新增 `client/GrenadePose.java`**（碎片手雷与震爆弹共用一份）：把 `move` 骨骼姿态、左右手模型点、
    保险销 / 压把推法、手臂用的肩点全部收在这里。以前只有保险销与压把在动，
    手上完全没有动作 —— `WeaponPose` 那套 display 增量对 GeckoLib 物品**不生效**。
    · 拔销：手腕外翻 16° + 抬腕 8° + 抬手 1.6 / 前移 0.8（模型像素）；插销反向
    · 投掷：向前上方甩（rotX −34°、+Y 2.6、−Z 3.6）；拔了销以后手微微抖；另有走路摆动 + 呼吸
    · 压把：碎片手雷在背面绕 X 弹开 38°，震爆弹在 −X 侧绕 Z 弹开 42°（两个型号轴不同）
  - **第一人称双手**（`WeaponArms.renderGrenade`）：**右手**握在弹体上（模型点 1.55,−0.50,1.05；
    震爆弹 1.60,−2.20,1.15），**左手只在拔销 / 插销时伸进来抓拉环**（0,2.68,−1.65；0,2.28,−2.86），
    并跟着销一起往前移（1.05 / 1.15 像素）——**投掷时左手完全不出现**（要的就是「不是双手投掷」）。
    · 手雷专用肩点 ±(0.88, −1.18, −1.02)：雷就攥在离相机 0.7 格的地方，
      沿用持枪那套肩点会让手臂横在画面中间把雷挡住（离线故事板里一眼可见）
  - **第三人称也只有一只手**：`WeaponArmPose` 里非持雷那只手保持 `ITEM`；`WeaponPose` 的 display 增量
    也只加给右手（以前左右手都加，镜像后就是「双手一起拔销 / 一起扔」）
  - **图标不再跟着动**：两个渲染器加了 `handPass` 门控（GUI / 掉落物 / 展示框走静态姿态），
    销与压把只在「拿在手上」那遍推 —— 同 AKM 在 r64 的教训
  - **投掷力道与弧度**：初速 1.15→**1.30**（碎片手雷）/ 1.25→**1.38**（震爆弹，更轻扔更远），
    出手再加 **6° 上抬**（`GrenadeItem.THROW_LIFT_DEG`）；随机偏差 0.02→0.4（原版雪球是 1.0）
    ⇒ 平视扔出约 11 格、抬 10° 约 20 格，弹道是一条看得见的抛物线
  - **插回保险销改成「潜行 + 右键」**（`GrenadeItem.serverBeginHold` 要求 `isShiftKeyDown`）：
    以前随手右键就开始插销，丢出去前手一抖就把销插回去了；没按潜行会提示怎么插（中英文案同步）
  - 离线验算：`python tools/_gren_story.py mud|flashbang [--sh a|b|c]` → `build/_gren_mud.png`
    （上一排远景 0.45 格 / 下一排游戏视角；手心带一个小标记块，用来确认手搭在弹体 / 拉环上）

> 版本 `1.0.0-r68`

- **十字弩：弓臂再往外扩一点 + 拉弦变细**
  - **弓臂外扩**：`tools/crossbow_vox.py` 的 `LIMB_SX` **1.7 → 1.9**（弓臂/线缆/弦三个分件一起放，
    锚点仍是各自内端/ x=0）⇒ 弓臂外端 ±4.51 → **±4.88**、跨度 **9.02 → 9.76**（每侧再多探出 0.37 像素）。
    同步的 Java 常数：`CrossbowGeoModel.TIP_X` 4.454 → **4.978**、`STRING_LEN` 4.804 → **5.293**
    （= hypot(4.978, 1.80)，`tools/_cb_flex.py` 同步）；`FLEX_PX/FLEX_PZ`（弓臂弯折支点）没动，因为锚点在内端。
  - **弦变细**：画弦处的 `th` **0.075 → 0.05**（弦方块截面 0.15 → **0.10 像素** = 0.6 cm）。
    弦长/位置没变，所以拉弦数学与“弦内端落在弦心”的判据不受影响。
  - 自检：`python tools/crossbow_vox.py`（弦拉满内端 → X 0.0000 / Z −3.4000，目标一致 OK）、
    `python tools/_cb_flex.py`（拉满时外端向内 0.52 / 向后 0.82，弦内端与弦心偏差 0.00）。
  - 只换了弩的 geo（贴图 md5 未变，glowmask 不用重生）；没跑 `install_models.py`（会覆盖五行）。

> 版本 `1.0.0-r67`

- **AKM 瞄准线：“准星柱 = 照门 = 护木导轨顶面”三点共线 + 弹道归零**
  （用户反馈：手持 AKM 开火时弹道在准星下方；且举枪时应以「导管上方凸点（准星柱）与护木装倍镜的导轨顶面」为准）
  - **模型**（`tools/akm_v3.py`，新常数 `RAIL_LIFT = 0.28`）：护木顶部导轨的**齿顶从 Y=3.16 抬到 3.44**，
    与照门顶、准星柱顶同高（导轨座同时加高到 3.34，免得齿悬空）；两种瞄具整体跟着抬 0.28 ——
    红点圆心 3.79→**4.07**、4 倍镜光轴 4.00→**4.28**（`WeaponMount.AKM_DOT_Y/AKM_SCOPE_Y` 同步改）。
    因为举枪位姿只是纯平移（无旋转），模型里的水平线投影后仍是水平线 ⇒ 举枪时**三点精确落在屏幕中心那条水平线上**：
    离线验算 `tools/_ads_check.py akm_aim` ⇒ 照门顶 / 准星柱顶 / 导轨齿顶 **X +0.00% Y +0.00%**（枪管轴 −14.61% = 瞄具高出膛线 0.11 格，正常）。
  - **弹道**（`AkmRifleItem.fire()`）：枪口比眼睛低（腰射 0.32 格 / 举枪 0.11 格：枪口在枪管轴线上、瞄准线在导轨齿顶），
    而收敛距离上限原来写死 96 格 ⇒ 弹道几乎与准星射线平行、近距离就整段压低（5~60 格偏低 0.31~0.65 格）。
    改成当「归零距离」用：**举枪 16 格 / 腰射 24 格** ⇒ 5~60 格内最大偏差
    **0.65 → 0.26 格（腰射）**、**0.49 → 0.12 格（举枪）**；下限 8 格不变（太近时枪口横向偏移会被放大成大偏角）。
  - 验收工具 `tools/_akm_ballistic.py`：逐 tick 复刻 Java 的发射链（枪口模型点 → 收敛点 → 速度、再 `×0.99` 阻尼 + 重力），
    输出各距离上「弹道 y − 准星射线 y」（负 = 偏低），并扫描收敛上限 16/24/32/40/48/96 的腰射/举枪最差偏差。
  - 模型重生成后只手动装了 AKM 两个文件（`geo/akm.geo.json` md5 `0fa6a709`、`textures/models/akm_geo.png` md5 `920d278c`），
    没跑 `install_models.py`（它会一次性覆盖五把武器，会把弩/弓的现调数值冲掉）。

> 版本 `1.0.0-r66`

- **给每个月相加「月亮颜色 + 天空颜色」**：
  - 原版天空（天穹 + 日月）是在 `LevelRenderer.renderSky` 里用固定颜色画的，Forge 只给了雾色钩子，
    没有「改天穹/月盘颜色」的事件 ⇒ 在 **`Stage.AFTER_SKY`**（原版天空画完、地形之前）自己叠两层：
    · **天穹**：以相机为球心（该阶段的位姿原点就是相机，原版天体就是在 y=±100 画的）画一个半径 100 的球，
      顶点色从天顶色渐变到地平线色（下半球另封一层很淡的暗色，避免天地交界出现硬缝）；
    · **月盘**：照拄原版那两步旋转（`YP(-90°)` + `XP(时间×360°)`），在 **y=−100** 的平面上画
      本阶段颜色的圆盘（半径 20.6 > 原版 ±20，不透明 ⇒ 把原版月亮整个盖住），加三个同色系陨石坑，
      超级月相再叠一圈更大的叠加混合光晕
  - 两层都关掉深度测试/深度写入（天空在最远处、不写深度），地形随后照常把它们盖住；
    ★ 天穹的不透明度取 0.42~0.60，免得把原版星空压死
  - 全屏那层属相叠色（`skyTint`）**只留一半强度**（它同时给地形/生物上氛围色，全强度会把天空压成一片平色）
  - 配色离线预览（改色不用进游戏）：`python tools/_moonsky_mock.py` → `build/_moonsky_mock.png`

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
