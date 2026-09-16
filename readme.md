# 六相月灾 · Hexa Lunar Calamity

[![build](https://github.com/SevenZeroMeowTeam/hexalunar/actions/workflows/build.yml/badge.svg)](https://github.com/SevenZeroMeowTeam/hexalunar/actions/workflows/build.yml)

Minecraft **1.20.1 / Forge 47.4.x** 的月相灾变 + 现代射击玩法模组。
月相会改变夜晚的威胁强度，玩家则用枪械、弩弓与投掷物应对尸潮。

- 模组 ID：`hexalunar_calamity`｜版本：`1.0.0-r20`
- 创造模式页签：**六相月灾**

---

## 一、构建与部署

| 项目 | 说明 |
|---|---|
| 需要 | JDK **17**、**Gradle 8.14.5** |
| ⚠️ 重要 | ForgeGradle `[6.0,6.2)` **不支持 Gradle 9.x**，必须用 8.x |
| 产物 | `mod/build/libs/hexalunar_calamity-1.0.0-r20.jar` |
| 部署 | 复制到 `%APPDATA%\.minecraft\versions\1.20.1-Forge_47.4.23-2\mods\` |

`.vscode/tasks.json` 里已配好两个任务（含 Java 报错问题匹配器）：

| 任务 | 作用 |
|---|---|
| `mc_check` | `gradle compileJava` — 只做类型检查，不打包 |
| `mc_build` | `gradle build` + **自动复制 jar 到 mods 目录** |

> 仓库已带 Gradle Wrapper（固定 **8.14.5**）：CI 与本地都可以直接用 `mod\gradlew.bat build`（Linux/macOS 用 `./gradlew`）。
> 推送到 GitHub 后由 `.github/workflows/build.yml` 自动编译并上传 jar 产物（Actions → 对应运行 → Artifacts）。

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

### 武器

| 武器 | 弹药 | 特性 |
|---|---|---|
| **AKM 突击步枪** | 7.62×39mm | 30 发弹匣 · 全自动（2 tick/发）· 后坐力累积影响散布 · 瞄准收紧散布 · 抛壳动画 · **有效射程 60 格**（射程内平直，超出后下坠） |
| **战术十字弩** | 弩箭 | 弹匣供弹 · 按住连发 · **4 倍镜**：右键开镜时视野 ×1/4、圆形镜筒遵罩 + 十字分划，并自动隐藏手部模型 · **有效射程 40 格** |
| **复合弓** | 复合弓箭 / 尸毒箭 | 右键蓄力（20 tick 满蓄），**三段拉弦动画**（0.65 / 0.9 蓄力切换模型）· 蓄力越高穿透与伤害越强 · 没普通箭时自动改用尸毒箭 · **有效射程 34 格** |

> **获取途径**：三把武器本体可在原版探险箱里按概率开出（附赠一份对应弹药）—— 常见箱 6%（地牢 / 矿井 / 神庙 / 前哨 / 村庄武器商…）、稀有箱 16%（古城 / 林宅 / 末地城 / 宝藏 / 堡垒…），权重 复合弓 > 十字弩 > AKM；也可在创造模式「六相月灾」页签直接取用。

### 弹药与弹药盒

| 物品 | 容量 | 获取 |
|---|---|---|
| 弩箭 | — | 木棍 + 燧石 ×4 |
| 复合弓箭 | — | 木棍 + 燧石 + 线 ×4 |
| 尸毒箭 | — | 复合弓箭 + 尸毒萃取剂 ×2 |
| 7.62×39mm | — | 火药 + 铁粒 ×6 |
| 弩箭 / 箭矢 / 步枪弹药盒 | 64 / 96 / 300 | 同一形状 `ppp/p■p/iii`，**中心槽放对应弹药**（三个配方靠中心材料区分，不会互相冲突） |
| 创造弹药箱 | ∞ | 创造页；潜行+右键切换弹种，自动匹配手持武器 |

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
│   ├── weapon/     枪械、弩、弓、弹药工具（AmmoType / AmmoUtil / WeaponAmmo）
│   ├── item/       弹药盒、创造弹药箱、解毒剂、手雷（GrenadeItem）
│   ├── entity/     弹丸与投掷物（子弹、弩箭、箭矢、手雷 GrenadeEntity）+ 特殊感染者
│   ├── client/     输入、FOV/瞄准、HUD、渲染器、物品属性注册
│   ├── net/        网络包（月相同步 / 命中反馈 / 开火 / 装填）
│   ├── registry/   物品、实体、音效、效果、创造页签
│   └── moon/       月相管理
└── src/main/resources/
    ├── assets/hexalunar_calamity/     模型（OBJ+MTL）、贴图、语言、音效
    ├── assets/minecraft/atlases/      ★ 方块图集扩展（见下）
    └── data/hexalunar_calamity/       配方

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

---

## 五、开发辅助工具（`tools/`）

| 脚本 | 用途 |
|---|---|
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
| AKM 弹匣容量 / 换弹时长 / 射速 / 散布 | `weapon/AkmRifleItem.java`（`MAG_SIZE` / `RELOAD_TICKS` / `FIRE_INTERVAL` / `fire()`） |
| 弩的倍镜倍率 | `weapon/CrossbowWeaponItem.java` 的 `SCOPE_ZOOM`（`4.0F` = 4 倍）；开镜 FOV 由 `ClientEvents` 用 `1/SCOPE_ZOOM` 计算 |
| 手雷拔销时长 / 捏雷时限 | `item/GrenadeItem.java`（`PIN_TICKS` / `COOK_TICKS`） |
| 手雷引信、伤害、效果半径 | `entity/GrenadeEntity.java` |
| 三武器的有效射程与超距下坠 | `weapon/Ballistics.java`（`AKM_RANGE` / `BOLT_RANGE` / `BOW_RANGE` 与各 `*_IN_RANGE_GRAVITY`） |
| 武器手持姿态 / 物品栏图标大小 | 各 `models/item/*.json` 的 `display`，或跑 `tools/scale_weapons.py` |
| 月相效果 | `moon/MoonManager.java` |

---

## 七、更新日志（本次开发）

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
