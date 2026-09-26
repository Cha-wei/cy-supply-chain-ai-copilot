# Master Data Mapping

**Document / Topic:** Master Data Mapping
**Parent Design:** [POC Design v0.2](../../poc-design-v0.2.md)
**Legacy Section:** §4.5（§4.5.1 ～ §4.5.26 编号保留）
**Design Status:** `DESIGN RESOLVED`
**Implementation Status:** 原文未单独登记本专题的 implementation 状态；source-specific / runtime realization 属 Adapter Boundary 范围，仍为 `NOT IMPLEMENTED`（见原文）。
**Canonical Authority:** 本文件是 Master Data Mapping concern 的唯一 current canonical source；parent design 保留 navigation/status 入口。
**Migration Base:** `5917cb2fa4b71d4a7379128447bc9e766d17e6da`

<!-- BEGIN MIGRATED LEGACY §4.5 BODY -->
### 4.5 Master Data Mapping

> **子章节整体状态：现为 `DESIGN RESOLVED`。**
>
> 本节已完成：Canonical Identity Resolution ＋ Relationship Resolution Boundary
> ＋ **Warehouse Role Resolution**（**§4.5.12**）
> ＋ **BOM Version / Validity Mapping**（**§4.5.7** ／ **§4.1.4 N**）
> ＋ **Supplier Eligibility Vocabulary Mapping**（**§4.5.11**）
> ＋ **Effective Arrival Date Source Mapping**（**§4.5.21**）
> ＋ **Allocation Demand-Window Mapping**（**§4.5.9**）
> ＋ **Other Source-Semantic Mapping**（**§4.5.22**）
> ＋ **Final Master Data Mapping**（**§4.5.25** ／ **§4.5.22 Final Master Data Mapping Closure Implementation Record**）。
>
> **仍为 `DESIGN PENDING` 的层级：** 无。

**层级状态登记：**

| 层 | Status |
| --- | --- |
| Identity Resolution Boundary | **`DESIGN RESOLVED`** |
| Relationship Resolution Boundary | **`DESIGN RESOLVED`** |
| Mapping Conflict / Failure Boundary | **`DESIGN RESOLVED`** |
| Mapping Provenance Requirement | **`DESIGN RESOLVED`** |
| Warehouse Role Resolution | **`DESIGN RESOLVED`** |
| BOM Version / Validity Mapping | **`DESIGN RESOLVED`** |
| Supplier Eligibility Vocabulary Mapping | **`DESIGN RESOLVED`** |
| Effective Arrival Date Source Mapping | **`DESIGN RESOLVED`** |
| Allocation Demand-Window Mapping | **`DESIGN RESOLVED`** |
| Other Source-Semantic Mapping | **`DESIGN RESOLVED`** |
| Final Master Data Mapping | **`DESIGN RESOLVED`** |

> **`Master Data Mapping` overall 现为 `DESIGN RESOLVED`。**
>
> `BOM Version / Validity Mapping` 的 **BOM Applicability Design Review** 曾判定
> **`INSUFFICIENT`（Blocking Finding / Canonical Model Conflict）** —— 见 **§4.5.7**；
> 该冲突已由 **Human-approved Option A ＋ Canonical Model Amendment** **RESOLVED**，
> 因此现为 **`DESIGN RESOLVED`**。
>
> `Supplier Eligibility Vocabulary Mapping` 的 **Supplier Eligibility Mapping Design Review**
> 与 **Human Decision Record**（**Option B APPROVED**）见 **§4.5.11**；
> 其 `§4.1` / `§4.2` / `§4.4` semantic synchronization **已实施**，
> 因此现为 **`DESIGN RESOLVED`**，unresolved count **7 → 6**。
>
> `effective_arrival_date` source mapping 的
> **Effective Arrival Date Source Mapping Design Review** 与 **Option D Implementation Record**
> 见 **§4.5.21**；其 `§4.2` / `§4.4` / `§4.5` semantic synchronization **已实施**，
> 因此现为 **`DESIGN RESOLVED`**（登记为 **Effective Arrival Date Source Mapping** 层），
> unresolved count **6 → 5**。
>
> `Other Source-Semantic Mapping` 的 **`provenance carrier`（最后一个 internal unresolved item）**
> 已由 **§4.5.22 Option D Implementation Record** 解析；因此该层现为 **`DESIGN RESOLVED`**，
> unresolved count **1 → 0**。
>
> `allocation demand-window mapping` 的
> **Substitute Allocation Demand-Window Mapping Design Review** 与 **Option B Implementation Record**
> 见 **§4.5.9**；其 `§4.1` / `§4.2` / `§4.4` / `§4.5` semantic synchronization **已实施**，
> 因此现为 **`DESIGN RESOLVED`**（登记为 **Allocation Demand-Window Mapping** 层），
> unresolved count **5 → 4**。
>
> `required_quantity` semantic 的
> **Required Quantity Semantic & Canonical Necessity Review**、**Human Decision Record** 与
> **Required Quantity Removal Implementation Record** 见 **§4.2.4**；
> 该字段已 **`REMOVED FROM CURRENT POC v0.2 CANONICAL MODEL`**（**Human-authorized Canonical Model Amendment**），
> unresolved count **4 → 3**。
>
> `loss_rate` owner / grain 的 **Option E semantic synchronization 已实施**
> （见 **§4.5.22 Option E Implementation Record**）；
> owner = **exact Requirement Calculation Context**，
> resolution contract = **exactly one applicable `loss_rate` or `unresolved`**，
> unresolved count **3 → 2**。
>
> `ApplicableMOQ` source 的 **Option D semantic synchronization 已实施**
> （见 **§4.5.22 Option D Implementation Record**）；其 **canonical applicability resolution**
> 现为 **`DESIGN RESOLVED`**（owner = **exact Procurement Recommendation Context**；
> resolution contract = **exactly one applicable `ApplicableMOQ` or `unresolved`**），
> unresolved count **2 → 1**。
>
> `provenance carrier` 的 **Option D semantic synchronization 已实施**
> （见 **§4.5.22 Option D Implementation Record**）；**Layered Logical Provenance Contract** 已落地，
> 因此其状态已变更为 **`DESIGN RESOLVED`**，unresolved count **1 → 0** ——
> **`Other Source-Semantic Mapping` 现为 `DESIGN RESOLVED`**。
>
> **`Final Master Data Mapping` 现为 `DESIGN RESOLVED`**（其 scope 与 `MC-1` ～ `MC-10` 已正式登记，
> 见 **§4.5.25** ／ **§4.5.22 Final Master Data Mapping Closure Implementation Record**）；
> **`Master Data Mapping` overall 现为 `DESIGN RESOLVED`**。

#### 4.5.1 Purpose & Scope

本 Task 定义：Controlled Snapshot 中的 **source evidence** 在进入 canonical business model 时，
Plant / Material / Supplier 以及关键业务 relationship **必须满足什么条件**，
才能被认为 **reliably resolved**。

**本 Task 只定义：**

- canonical identity resolution principle
- Plant identity resolution
- Material identity resolution
- Supplier identity resolution
- relationship resolution
- unresolved / conflicting mapping behavior
- mapping provenance requirement
- mapping failure blast radius

> 后续 Task 已追加 **Warehouse Role Resolution**（见 **§4.5.12**）、**BOM Version / Validity Mapping**（见 **§4.5.7**）、**Supplier Eligibility Vocabulary Mapping**（见 **§4.5.11**）、**Effective Arrival Date Source Mapping**（见 **§4.5.21**）与 **Allocation Demand-Window Mapping**（见 **§4.5.9**）。

**不得定义**：ERP vendor / ERP version / source table / source column / CSV column / JSON path /
SQL / mapping code / fuzzy matching algorithm / MDM product / database / API / Adapter implementation。

**本 Task 不设计真实 ERP mapping。**

#### 4.5.2 Core Principle

正式定义：

```
Source Identifier  ≠  Canonical Identity
```

只有经过**可靠 mapping** 后，source evidence 才能作为 **canonical business evidence** 使用。

Mapping **必须**：

```
deterministic
explicit
traceable
reproducible
```

**不得依赖**：

- LLM guess
- name similarity
- fuzzy matching
- human-name intuition
- silent normalization

#### 4.5.3 Identity Resolution Outcomes

**不创建新的 Business Enum。**

只描述 **conceptual mapping condition**：

| # | Condition | 含义 |
| --- | --- | --- |
| **A** | **Reliably Resolved** | source identity 能够**唯一、明确、可追溯**地对应**一个** canonical identity |
| **B** | **Unresolved** | **无法可靠确定** canonical identity |
| **C** | **Conflicting / Ambiguous** | 同一 source context 能对应**多个互相冲突**的 canonical identity，**且不存在已批准 precedence rule** |

**B / C 均不得**：

- 随机选择
- first wins
- latest wins
- LLM choose

应按既有 **Validation Taxonomy** 影响对应 **evidence / grain / capability**。

#### 4.5.4 Plant Mapping

**Canonical identity：** `plant_id`

任何需要 Plant grain 的 source evidence（**Inventory** / **Requirement** / **Inbound** /
**Substitute** / **Safety Stock**）**必须**能够可靠解析：

```
source Plant context → canonical plant_id
```

**不得**：

- 把未知 Plant 自动映射到默认 Plant
- 跨 Plant fallback
- 按名称相似度匹配
- 把 missing Plant 当作当前 Plant

无法解析 → **`UNRESOLVED_IDENTITY`** → affected grain **不得形成正常结果**。

#### 4.5.5 Material Mapping

**Canonical identity：** `material_code`

以下 source evidence **均必须**解析至 canonical Material：

- Production Requirement
- BOM parent material
- BOM component material
- Inventory
- Inbound
- Substitute target
- Substitute source
- Supplier-Material Relationship
- Supplier Performance
- Procurement context

**不得**：

- 自动改 Material code
- fuzzy match Material name
- alias guessing
- 用 description 代替 identity

如果未来需要 **alias / cross-system code mapping**：**必须**作为**明确 mapping evidence**，
而**不是** LLM inference。

> 本 Task **不设计** alias table 的 physical form。

#### 4.5.6 Supplier Mapping

**Canonical identity：** `supplier_id`

Supplier Performance 以及 Supplier-Material Relationship **必须**可靠解析到 canonical `supplier_id`。

**不得**：

- `supplier name similarity → supplier_id`
- 同名 Supplier → 自动认为相同实体

#### 4.5.7 BOM Relationship Resolution

BOM evidence **必须**能够可靠解析：

```
Production Requirement context + component Material
（= plant_id + parent / requirement material_code + required_date + component material_code）
```

才能供 **`BR-REQUIREMENT-001`** 使用。

**已解析（Human-authorized Canonical Model Amendment，PR #30 ／ Option A）：**

```
BOM version / validity selection = DESIGN RESOLVED
  → requirement-scoped BOM applicability
```

**不得设计**（仍然 `DESIGN PENDING`，超出本 POC canonical model 所需）：

- `BOMVersion`
- `ValidFrom`
- `ValidTo`
- latest BOM wins
- version selection algorithm（作为真实 ERP BOM selection engine）

如果 applicable BOM **无法可靠确定**：继承现有 Validation → **`DATA_INCOMPLETE`**。

**BOM Applicability Design Review（Review Finding）**

**Critical Scenario**

```
Plant-A / Parent MAT-A

BOM Definition 1：valid before 2026-10-01
  MAT-A → MAT-B × 2

BOM Definition 2：valid from 2026-10-01
  MAT-A → MAT-B × 3

Requirement R1：required_date = 2026-09-25，ProductionQty = 100
Requirement R2：required_date = 2026-10-10，ProductionQty = 100
```

**Question**

当前 BOM Component canonical grain（`plant_id` + parent material + component `material_code`）
如何**同时、无歧义**地表达：

```
R1 → BOMComponentQty = 2
R2 → BOMComponentQty = 3
```

**Analysis**

| 项目 | R1 | R2 |
| --- | --- | --- |
| applicable BOM definition | Definition 1 | Definition 2 |
| requirement calculation grain（`§2.4.2`） | `Plant-A` + `MAT-B` + `2026-09-25` | `Plant-A` + `MAT-B` + `2026-10-10` |
| required `BOMComponentQty` | **2** | **3** |
| **BOM Component canonical grain（`§4.1.4 N`）** | `Plant-A` + `MAT-A` + `MAT-B` | `Plant-A` + `MAT-A` + `MAT-B` |

R1 与 R2 映射到**同一个** BOM Component canonical grain key，
却要求**两个互相冲突**的 `BOMComponentQty` 值。

**必须明确区分两个不同的 grain：**

| Grain | 定义位置 | 是否足以区分 R1 / R2 |
| --- | --- | --- |
| `plant_id` + `material_code` + `required_date`（calculation grain） | `§2.4.2` / `§2.4.3` | **足以** —— `required_date` 不同 |
| `plant_id` + parent material + component `material_code`（BOM Component canonical grain） | `§4.1.3` / `§4.1.4 N` | **不足** —— 无 applicability carrier |

即：

> **`BR-REQUIREMENT-001` 的 requirement calculation grain 本身没有问题；
> 不足的是 `§4.1` 中 BOM Component 这一 supporting canonical entity 的 grain。**

`§4.1.4 N` 的 attributes 为「至少 `BOMComponentQty`、`material_code`」，
**不含**任何 applicability context；且本节上文（`§4.5.7`）**明确禁止**设计
`BOMVersion` / `ValidFrom` / `ValidTo`。

**因此：Canonical Model has insufficient applicability grain.**

**Canonical Model Compatibility Result**

```
B. INSUFFICIENT
```

**Blocking Finding**

```
现有 BOM Component canonical grain
（plant_id + parent material + component material_code）
无法无歧义表达 time-varying / version-varying BOM。
```

直接后果：

- `§4.4.52` 要求 Production Requirement 可追溯到 **reliably resolved applicable BOM relationship** ——
  但该 trace 的**目标本身不可唯一识别**（两个 definition 共享同一 grain key）
- 因此 `BOM Version / Validity Mapping` **不能**在本轮标记为 `DESIGN RESOLVED`

**Canonical Model Conflict**

```
§4.1 Canonical Data Model = DESIGN RESOLVED + Human-approved
                       ≠
BOM Applicability 所需的 applicability context
```

**不得**自行修改 `§4.1` / `§4.2` 中已批准的 grain 或 attributes。

**Option Review**

| Option | 内容 | 是否解决 grain collision | 是否违反既有 Design | 结论 |
| --- | --- | --- | --- | --- |
| **0** | 保持 BOM version / validity unresolved | 否（但**不产生错误结果**） | 否 | 可保留，但**长期阻塞可运行性** |
| **1** | Latest BOM Wins | 否 —— 仍只有一个 grain key，且会**静默选错** | **是** —— 违反 business time ≠ package / snapshot time 与 `required_date` semantics | **拒绝** |
| **2** | Source Pre-resolved Applicable BOM | **否** —— 解决了「谁决定 applicability」，**未解决**「模型在哪里承载 applicability」 | 否 | **必要但不充分** |
| **3** | Temporal / Applicability Context in Canonical Model | **是** | 需要 Human 批准的 Canonical Model Change | **候选（Human Decision）** |
| **4** | POC Constraint：一个 Analysis context 内同一 Plant + Parent 只允许一个 BOM definition | 条件成立时**是**（代价是禁止合法 evidence） | **无既有 Design 依据** —— 属于**新的 POC assumption** | **不予采用（无依据）** |

**Option 0 —— 评估**

保持未决**不会产生错误结果**（既有 fail-safe 返回 `DATA_INCOMPLETE`），
但会在**任何存在 BOM 变更的场景**下长期阻塞 `BR-REQUIREMENT-001` 的**可运行性** ——
BOM 变更在制造业属常态，因此该阻塞**不是边缘情况**。

**Option 1 —— 拒绝依据**

```
business time  ≠  package / snapshot time
```

`§4.1.6 Time Semantics` 已明确 `required_date` 属 **requirement time**，
与 snapshot / observation time **互不相同**。

「按 snapshot / export / system current time 选择最新 BOM」会：

- 用 **snapshot time** 替代 **requirement business time**
- 使 R1（`2026-09-25`）被**错误地**按 Definition 2 计算（`3` 而非 `2`）
- **违反** `§2.4` 既有的「不得猜 BOM ／ 不得自动选择 latest BOM」

**Option 2 —— 必要但不充分**

Source pre-resolution 是**必要的**（POC 不自行重新执行真实 ERP BOM selection），
但**不足以**解决本 finding：即使 source 已可靠解析出
「R1 → Definition 1、R2 → Definition 2」，
当前 canonical grain **仍然无处承载**该区别。

> 结论：Option 2 应作为**未来实现的组成部分**，但**不能单独**使
> `BOM Version / Validity Mapping` 变为 `DESIGN RESOLVED`。

**Option 3 —— 候选方向（Human Decision）**

见下方 **Recommended Minimal Change Options**。

**Option 4 —— 不予采用**

- 这是**新的 POC business / data assumption**，**没有**现有 Design 依据
- 它会**错误处理**跨 validity boundary 的 requirement ——
  本 Review 的 **Critical Scenario**（R1 ＋ R2 同时存在）会被**直接禁止**
- 它**只是为了避免修改 Model 而人为缩小现实问题**
- 若采用，仍需 Validation 判定该约束是否被违反，而**违反时的业务后果未被任何既有 Rule 定义**

> **没有充分依据，不得自动采用。**

**Recommended Minimal Change Options（本轮不实施）**

| # | 候选最小变更 | correctness | complexity | traceability | reversibility | 对 `§4.1` / `§4.2` / `§4.4` 的影响 |
| --- | --- | --- | --- | --- | --- | --- |
| **A** | 将 BOM relationship **显式关联**到 Production Requirement context | 高 | 中 | 最高（trace 目标唯一） | 中 | `§4.1` entity N 的 grain / relationship 需扩展；`§4.2` 可能新增 context field；`§4.4.52` 需强化 |
| **B** | 增加 **conceptual BOM applicability identity / context**（不创建 BOM Header / Version Entity） | 高 | 中 | 高 | 中 | `§4.1` entity N grain 需扩展；`§4.2` / `§4.4` 需同步 |
| **C** | 增加 **temporal validity context** | 高 | **高** | 高 | 中 | 影响最大 —— 需定义 overlap / open-ended validity 语义，风险最高 |
| **D** | 限制 POC：一个 Analysis context 内同一 Plant + Parent 只允许单 BOM definition | **低**（拒绝合法 evidence） | 低 | 低 | 高 | `§4.1` 不变，但需新增 POC constraint ＋ 违反后果定义 |

**推荐（供 Human 决定，非本 Agent 决定）：**

优先评估 **Option A**（显式关联到 Production Requirement context）：

- 直接消除 grain collision，且**不需要**引入 `BOMVersion` / `ValidFrom` / `ValidTo` 等字段
- **不创建**新的 canonical entity（保持 `§4.5` 既有约束）
- 与 `§2.4.2`「必须能够追溯到 Production Requirement ＋ BOM relationship」**方向一致**
- **不需要** POC 人为缩小现实问题（优于 D）

> 若 Human 选择 **C**，必须先定义 validity overlap / open-ended 语义，
> 并明确 `required_date` 与 validity 边界的**包含 / 排除**规则。
> 若 Human 选择 **D**，必须同时定义**违反该约束时的业务后果**。

**Required Date as Applicability Anchor —— Human-approved Policy（未实施）**

**Human 已批准**以下 business-time anchor 为：

```
Production Requirement.required_date
```

**支持依据（既有 Design）：**

- Production Requirement grain **包含** `required_date`（`§4.1.4` / `§4.2.4`）
- `BR-REQUIREMENT-001` 的需求计算以 requirement context 为基础（`§2.4.2` / `§2.4.3`）
- `§4.1.6` 已明确 `required_date` 属 **requirement time**，与 snapshot / observation time **互不相同**

**但必须明确：这是一个新的 Design Decision，不是当前既有事实。**

**不得**使用以下时间**替代** `required_date`，除非另有正式 Design：

- Snapshot creation time
- `AnalysisDate`
- system current time
- package / export time

若未来采用，**必须**标记为：

```
SIMULATED POC Design Policy  +  Human-approved after merge
```

**不得**描述为**真实 CY 企业 BOM selection 规则**。

> **本轮状态：`Human-approved`（`SIMULATED POC Design Policy`）；implementation 仍属后续 Design Change Task。** `BOM Version / Validity Mapping` 仍为 `DESIGN PENDING`。

**Applicable BOM Definition（conceptual）**

允许定义 conceptual：**Applicable BOM Definition** ——
对于一个明确 Production Requirement context，能够唯一确定一组

```
parent Material → component Material → BOMComponentQty
```

的 BOM relationship set。

这**只是 mapping / applicability concept**。

**不得**据此自动创建新的 canonical entity：`BOM Header` / `BOM Version Entity` / `BOM ID`
—— 除非 Human 后续批准（见上文 Recommended Minimal Change Options）。

**One Definition, Multiple Components**

必须明确：

```
exactly one applicable BOM  ≠  只有一条 BOM Component row
```

一个 applicable BOM definition **可以包含多个** component relationships。例如：

```
MAT-A BOM（一个 definition）：
  MAT-B × 2
  MAT-C × 1
  MAT-D × 0.5
```

这是 **one applicable BOM definition with multiple components**。

**不得**将 multiple components **误判**为 multiple BOM versions。

**Zero Applicable BOM**

如果 BOM evidence role **已提供**，但对于当前
`Plant` + `Parent Material` + **requirement business-time context**
**没有任何** BOM 能够可靠确定为 applicable：

**不得**：

- 使用任意 BOM
- 使用 latest BOM
- 使用 previous BOM
- 使用 next BOM
- 使用 default BOM

结果：`BR-REQUIREMENT-001` → **`DATA_INCOMPLETE`**。

Validation Issue 应使用 **`§4.4.80` / `§4.4.81`** 既有 taxonomy 表达具体 root condition。
**不得创建**新的 Business Status。

**Multiple Applicable BOM Definitions**

如果同一 Production Requirement context **同时存在多个**候选 BOM definitions，
且**没有** approved precedence / selection evidence：

**不得**：

- first wins
- latest wins
- highest version wins
- lowest version wins
- most recent update wins
- LLM choose

这是 **ambiguous applicability / consistency problem**。业务结果：**`DATA_INCOMPLETE`**。

按具体 root condition 映射到既有 taxonomy：

```
SEMANTIC_UNRESOLVED   或   CONSISTENCY_CONFLICT
```

**不得创建**新的 Business enum（例如 `BOM_AMBIGUOUS`）。

**Validity Evidence Boundary**

如果 source system 提供 version / valid-from / valid-to / change-number /
effectivity / production-version / alternative BOM 或类似信息，**本 Task 不定义真实字段名**。

只能定义：**必须存在足够的 explicit applicability evidence**，
使 mapping 能 **deterministic** 地判断某 BOM definition **是否适用于当前 requirement context**。

**不得声称**真实 ERP **一定**拥有 `BOMVersion` / `ValidFrom` / `ValidTo`。

**Version Identity vs Applicability**

必须区分：

```
BOM version identity   ≠   BOM applicability
```

一个 version label **本身不能证明**它对当前 requirement 是 applicable：

```
Version V3 exists   ⇏   V3 automatically applies to required_date
```

同样：

```
higher version number   ⇏   more applicable
```

**Time Boundary**

必须保持以下时间概念**分离**：

- Package creation time
- Snapshot time
- `AnalysisDate`
- `required_date`
- BOM applicability time

**不得**建立如下**隐式链路**：

```
latest package → latest BOM → applicable BOM
```

**Source Pre-resolution Boundary**

如果采用 source-pre-resolved applicable BOM，必须明确：

```
"pre-resolved"  ≠  "trust blindly"
```

POC 仍需要 evidence 能说明**为什么**这组 relationship 对当前 Production Requirement applicable。

至少必须：`deterministic` / `explicit` / `traceable` / `reproducible`，
并**绑定当前** Snapshot Package ＋ requirement context。

**Provenance**

如果未来采用 applicability mapping，**必须未来能够追溯**：

```
Production Requirement
→ applicability evidence
→ selected BOM definition
→ component relationships
→ Snapshot Package
```

**但**：**physical provenance carrier 仍属 `§4.3` 后续设计**（**logical provenance carrier = `DESIGN RESOLVED`**，见 **§4.5.22 Option D Implementation Record**）。

**不得创建**：BOM mapping table / JSON / CSV / DB schema / lineage DB。

**Failure Blast Radius**

一个 Parent Material / Production Requirement 的 BOM applicability unresolved
**默认只影响**：

```
对应 requirement
→ affected component requirements
→ affected material shortage capability
```

**不得**：`one BOM ambiguity → entire Package invalid` ——
除非同时构成 **Package Structural Failure**。

**No BOM Explosion**

本 Review **只处理**「哪个 BOM relationship set 对当前 Production Requirement applicable」。

**不得设计**：multi-level BOM explosion / recursive BOM explosion / phantom assembly handling /
co-product / by-product / routing / work center / alternative component optimization。

```
BOM explosion algorithm = DESIGN PENDING / OUTSIDE THIS TASK
```

**未修改已批准 Canonical Model（PR #30 Review 时点）**

该 Review **当时未修改**：

- `§4.1` 的 BOM Component canonical grain
- `§4.1.3` / `§4.1.4 N` 的 attributes
- `§4.2.4` 的 `BOMComponentQty` 定义
- `§4.4.52` 的 consistency rule
- `§2.4` 的任何 Business Rule

**Status（PR #30 Review 时点）**

```
BOM Version / Validity Mapping = DESIGN PENDING
Master Data Mapping overall    = DESIGN PENDING
```

未决项数量**不减少**（当时仍为 **8 项**）。

> 以上为**历史记录**。后续 **Human-authorized Canonical Model Amendment** 已实施并变更该状态 ——
> 见下方 **Option A Implementation Record**。

**Human Decision Required**

必须由 Human 决定：

1. 是否接受 **`Canonical Model Compatibility = INSUFFICIENT`** 这一 finding
2. 采用哪个 **Recommended Minimal Change Option**（A / B / C / D）
3. 若采用 A / B / C：是否授权**修改 `§4.1` Canonical Data Model**
   （当前为 `DESIGN RESOLVED` ＋ Human-approved）
4. 是否采用 `required_date` 作为 **BOM applicability business-time anchor**
   （需标记 `SIMULATED POC Design Policy`）
5. 是否接受 **8 项未决项保持不变**（本轮**不**减少 unresolved count）

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 以下为 Human 对上述 5 项的**正式回复**（本 Review 由 **PR #30** 提交）。
> 本节**只记录决定**；**未**执行任何 Canonical Model 修改。

| # | 决定项 | Human Decision |
| --- | --- | --- |
| 1 | 是否接受 `Canonical Model Compatibility = INSUFFICIENT` | **ACCEPTED** —— finding 成立 |
| 2 | 采用哪个 Recommended Minimal Change Option | **Option A APPROVED** |
| 3 | 是否授权修改 `§4.1` Canonical Data Model | **AUTHORIZED** —— 仅限后续专门的 **Design Change Task** |
| 4 | 是否采用 `required_date` 作为 BOM applicability business-time anchor | **APPROVED** |
| 5 | 是否接受 8 项未决项保持不变 | **ACCEPTED** |

**Option A —— Authorized Scope（授权边界）**

被批准的方案为：

```
将 applicable BOM relationship
显式关联到 Production Requirement context
```

后续专门的 **Design Change Task** **只允许**解决：

```
time-varying / version-varying BOM
无法由当前 BOM Component grain 无歧义表达的问题
```

**不得借此**：

- 重构其他 canonical entities
- 改其他 Business Rule grain
- 解决 `loss_rate` owner / grain
- 解决 `required_quantity` semantic
- 扩展 BOM explosion
- 创建真实 ERP BOM schema

> **本 PR 不执行**该 Design Change。
> `§4.1` / `§4.2` / `§4.4` 的 canonical design modification **不在本 PR 范围内**。

**`required_date` anchor —— 批准状态**

```
Production Requirement.required_date
  = POC v0.2 的 BOM applicability business-time anchor
```

**标记（必须）：**

```
SIMULATED POC Design Policy  ＋  Human-approved
```

**不得**描述成**真实 CY 企业 BOM selection rule**。

**不得**使用以下时间**替代** `required_date`：

- Snapshot creation time
- Package export time
- `AnalysisDate`
- system current time

**执行状态（PR #30 时点）**

```
Human Decision                 = RECORDED
Canonical Model Change         = NOT YET IMPLEMENTED
Option A implementation        = DEFERRED → follow-up Design Change Task
BOM Version / Validity Mapping = DESIGN PENDING
unresolved count               = 仍为 8 项
```

`BOM Version / Validity Mapping` **保持 `DESIGN PENDING`**，
直到 approved Canonical Model Change **完成并通过 Review** 为止。

**Option A Implementation Record（Human-authorized Canonical Model Amendment）**

**授权来源**

```
PR #30 Human Decision
  → Finding ACCEPTED（Canonical Model Compatibility = INSUFFICIENT）
  → Option A APPROVED
  → §4.1 minimal Canonical Model Change AUTHORIZED
  → required_date applicability anchor APPROVED
```

**Before / After canonical grain**

| | BOM Component canonical grain |
| --- | --- |
| **Before** | `plant_id` + parent material + component `material_code` |
| **After** | `Production Requirement context` + component `material_code`<br>（= `plant_id` + parent / requirement `material_code` + `required_date` + component `material_code`） |

**关键变化：** `required_date` applicability context 现由所属 **Production Requirement context** 承载，
因此两个不同 `required_date` 可以合法拥有**不同**的 `BOMComponentQty`。

**Canonical Model Conflict：`RESOLVED BY` Human-approved Option A ＋ Canonical Model Amendment。**

**BOM applicability mapping（正式定义）**

```
Production Requirement context
+ required_date business-time anchor
→ exactly one applicable BOM definition
→ component relationships（可多个）
```

- **exactly one applicable BOM definition** **不表示**只有一条 component row ——
  一个 definition **可以**包含多个 components
  （例如 `MAT-B × 2` / `MAT-C × 1` / `MAT-D × 0.5` 属于**同一个** definition）
- **Applicable BOM Definition** **不是**新的 canonical entity，
  只是 requirement-scoped applicable BOM relationships 的 **conceptual grouping**
- **exactly one** 指 **definition 层面**唯一，**不**限制 component 数量

**Critical Scenario —— 现已可无歧义表达**

| Requirement context | applicable BOM definition | `BOMComponentQty`（MAT-B） |
| --- | --- | --- |
| `R1` = `Plant-A` + `MAT-A` + `2026-09-25` | Definition 1 | **2** |
| `R2` = `Plant-A` + `MAT-A` + `2026-10-10` | Definition 2 | **3** |

```
R1 Context + MAT-B → BOMComponentQty = 2
R2 Context + MAT-B → BOMComponentQty = 3
```

**两者不再发生 grain collision** —— `required_date` 已成为 canonical grain 的组成部分。

**§4.1 内对应变更**

- `§4.1.3` Entity N 的 `Canonical identity / grain` 已替换为 requirement-scoped grain
- `§4.1.4 N` 的 grain / attributes / context boundary 已更新
- `§4.1.5` relationship model 已强化为 `Production Requirement → has applicable BOM Component relationships`
- Entity C `Production Requirement` 的 grain **未修改**（仍为 `plant_id` + `material_code` + `required_date`）
- `§4.1` 仍为 **`DESIGN RESOLVED`** —— 本次为 **Human-authorized Canonical Model Amendment**，
  **不是** Agent 自行更正已批准模型

**继续继承的既有边界（本 Task 未变更）**

- **Zero Applicable Definition** —— 无任何 BOM 可可靠确定为 applicable →
  `BR-REQUIREMENT-001` → **`DATA_INCOMPLETE`**；**不得**使用 default / previous / next / latest /
  arbitrary BOM；使用**既有** Validation Taxonomy 表达 root condition，**不得创建**新 Business Status
- **Multiple Applicable Definitions** —— 多定义竞争且无 approved applicability evidence →
  `DATA_INCOMPLETE`；按 root condition 映射到既有 **`SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED`**
  或 **`CONSISTENCY` / `CONSISTENCY_CONFLICT`**；**不得创建** `BOM_AMBIGUOUS` 等新 enum
- **Source Applicability Evidence** —— POC **不**自行重新实现真实 ERP version-selection engine；
  evidence 必须 `deterministic` / `explicit` / `traceable` / `reproducible`；
  `"pre-resolved" ≠ "trust blindly"`
- **Snapshot Boundary** —— applicability evidence 必须属于当前 Analysis Run 绑定的
  **accepted Snapshot Package**；跨 Package 继续继承 **`PROVENANCE_MISMATCH`**
- **Failure Blast Radius** —— 单个 Production Requirement 的 applicability unresolved
  默认只影响该 requirement → its component requirements → affected shortage grains；
  **不得** `one BOM issue → entire Package rejected`，除非同时构成 **Package Structural Failure**
- **Provenance** —— 必须未来可追溯 `Production Requirement → applicability evidence →
  applicable BOM relationship set → component relationship → Snapshot Package`；
  **physical provenance carrier 仍属 `§4.3` 后续设计**（**logical provenance carrier = `DESIGN RESOLVED`**，见 **§4.5.22 Option D Implementation Record**）；**不得**创建 lineage DB / JSON schema / mapping table
- **No BOM Explosion** —— `BOM explosion algorithm = DESIGN PENDING / OUTSIDE THIS TASK`

**Terminology Clarification**

`BOM Version / Validity Mapping` 在 POC v0.2 中**不要求**保存 ERP BOM version number。

它解决的是 **BOM applicability** —— 即：对于当前 Production Requirement context，
**哪组 BOM relationships applicable**。

真实 source 的 version / validity / effectivity mechanism 由**后续 Adapter / source mapping**
转换成这个 canonical applicability result。

**执行状态（本 Task 完成时点）**

```
Human Decision                 = RECORDED
Canonical Model Change         = IMPLEMENTED（Human-authorized Option A）
BOM Version / Validity Mapping = DESIGN RESOLVED
Master Data Mapping overall    = DESIGN PENDING
unresolved count               = 8 → 7
```

#### 4.5.8 Substitute Relationship Resolution

**必须保持有方向：**

```
substitute → target
```

mapping **必须**能够可靠解析：`plant_id` / `target_material_code` / `substitute_material_code`。

**不得**：

- 自动反向
- 因两个 Materials 都存在而**创建**替代关系
- 跨 Plant 创建关系
- 用 LLM 判断可替代性

Relationship approval semantic **继续继承现有 Rule**。

#### 4.5.9 Substitute Allocation Resolution

Allocation evidence **必须**能够解析到：

```
对应 Substitute Relationship + target context + source substitute context
```

**当前 authoritative state（PR #36 实施后）：**

```
canonical demand-window mapping contract = DESIGN RESOLVED
concrete source evidence                 = SOURCE-SPECIFIC / Adapter-defined
```

因此**不得创建** `demand_window_id` / `requirement_id` / `allocation_period` / `valid_from` / `valid_to`
等字段；也**不得**创建 persisted applicability / overlap field。

本 Task **只定义**：allocation relationship identity **必须可追溯且不可猜测**。

**Substitute Allocation Demand-Window Mapping Design Review（Review Finding）**

**Existing Rule Boundary（不得修改）**

| 事实 | 来源 |
| --- | --- |
| `CumulativeApprovedSubstituteSupply` grain = `plant_id` + `target_material_code` + `required_date` | `§2.3.12` |
| `EquivalentTargetQty = AllocatedSubstituteQty × substitution_ratio` | `§2.3.12` |
| allocation 必须：`approved relationship` / `same Plant` / eligible `AVAILABLE` source inventory / `explicit allocation` / **对当前 `required_date` 有效** | `§2.3.12` |
| **No Double Allocation**：`Σ AllocatedSubstituteQty <= EligibleSubstituteSupply` | `§2.3.10` |
| Supply Conservation / Reservation：`RemainingUnallocatedSourceSupply = EligibleSubstituteSupply - Σ AllocatedSubstituteQty >= 0` | `§2.3.10` |
| reservation **只作用于 allocation 有效的 demand window** | `§2.3.10` 时间边界 |
| 无法可靠判断 allocation 与 Source Material 自身需求窗口是否重叠 → `DATA_INCOMPLETE` ＋ Data Quality Issue | `§2.3.10` |
| allocation 无法可靠关联当前需求窗口 → `DATA_INCOMPLETE` ＋ Data Quality Issue | `§2.3.12` |
| canonical grain = `source substitute material` + `target material` + `effective demand context` | `§4.1.4 G` |
| `effective demand context` 关联机制 `DESIGN PENDING`；**不得创建** `demand_window_id` / `requirement_id` / `allocation_period` | `§4.2.7` / `§4.4.32` / `§4.4.60` |

**Current Canonical Model Boundary**

`§4.1.4 G Substitute Allocation` 的 grain **已包含** **`effective demand context`** 这一组成部分，
且其 attributes 已列出 `effective demand context`。

但该 context **尚未被正式解析**。**不得假装**它已经等于：

- `required_date`
- `requirement_id`
- 某个 date range
- `allocation_period`

**Two Different Time Questions（必须分开）**

| # | 问题 | 含义 |
| --- | --- | --- |
| **A** | **Target Applicability** | 这笔 allocation 对 **Target Material** 的**哪一个** `required_date` / demand context 可以作为 **Approved Substitute Supply**？ |
| **B** | **Source Reservation** | 同一笔已分配 Source Supply，对 **Source Material** 的**哪些** demand contexts **不得**再作为 uncommitted Eligible Supply 重复使用？ |

**必须明确：**

```
Target Applicability  ≠  Source Reservation
```

两者**相关**，但**不一定是同一个问题**。

**不得只解决 Target 侧，然后宣称 No Double Allocation 已完整解决。**

**Critical Scenario（必须回答 —— 当前 Design 无法唯一回答）**

```
Plant-A

MAT-B AVAILABLE = 100
approved substitute：MAT-B → MAT-A
Allocation：60 MAT-B → MAT-A

Target demands：
  R1：MAT-A，required_date = 2026-10-10
  R2：MAT-A，required_date = 2026-10-20

Source demand：
  S1：MAT-B，required_date = 2026-10-12
```

| # | 问题 | 当前 Design 能否唯一回答 |
| --- | --- | --- |
| 1 | 这 60 属于 `R1`、`R2`、**两者**还是**某个区间**？ | **不能** —— `effective demand context` mapping 仍 `DESIGN PENDING` |
| 2 | 在 `2026-10-12`，`MAT-B` 自己**还能否使用**这 60？ | **不能** —— Source Reservation overlap **无法可靠判断** |
| 3 | 到 `2026-10-20`，这 60 是否**仍可作为 `MAT-A` substitute supply 再次累计**？ | **不能** —— 同一 allocation 的 applicability context **未解析** |

**因此：当前 Design 存在明确缺口 —— 不得自行猜。**

**Option Review**

| Option | 内容 | 评估 | 结论 |
| --- | --- | --- | --- |
| **0** | 保持 demand-window mapping unresolved | 安全，但 Substitute capability 仍不可可靠执行 | **安全但长期阻塞** |
| **A** | 仅绑定 Target `required_date`（Target Production Requirement context） | 只能解决 **Target inclusion**；**不足以**解决 **Source reservation overlap** | **不足（不得据此宣称完整解决）** |
| **B** | **source-specific mapping → canonical allocation applicability relation**（同时回答 A 与 B，**不新增 field**） | 与现有架构一致 | **推荐方向（待 Human Decision）** |
| **C** | Canonical validity interval（`valid_from` / `valid_to` 等） | 属**新增 canonical fields ＋ 新的时间业务规则** | **拒绝（无 Human Approval 不得采用）** |
| **D** | 新增 `requirement_id` / `demand_window_id` / `allocation_period` | `§2` / `§4.4` 已明确禁止本阶段自行创建 | **拒绝** |
| **E** | Allocation 永远 reserve **整个 Analysis Run** | 会把已有「**same effective demand window**」偷换成「**entire run**」 | **拒绝（无依据）** |

**Option A —— 不足的依据**

把 allocation 直接绑定 `plant_id` + `target_material` + `required_date` 只能确定
「这笔 allocation 对 **Target** 是否 applicable」；
它**不自动**回答「Source Material 在**哪些** demand contexts 上**不得**再使用该 supply」。

**Option C —— 拒绝依据**

引入 `valid_from` / `valid_to` 属于**新增 canonical fields**，
并会引入**新的时间业务规则**（区间语义、开闭区间、重叠判定）；
**没有 Human Approval 不得采用**。

**Option E —— 拒绝依据**

`§2.3.10` 明确的边界是 **`same effective demand window`**，**不是** `entire Analysis Run`。
把二者等同属于**未经授权的语义扩张**。

**Recommended Direction（Option B，待 Human Decision）**

```
source-specific allocation evidence
        ↓
explicit deterministic mapping
        ↓
canonical allocation applicability relation
        ├── Target Applicability
        └── Source Reservation Overlap
```

Canonical Design **只**定义：**必须能够可靠回答上述两个关系**；
**不统一**真实 source 字段，**不创建** physical field。

未来 Adapter **可以**依据真实系统的 `allocation record` / `reservation record` / `planning link` /
`schedule context` / ERP-specific evidence ——
**但当前 Design 不得声明**真实系统一定拥有上述任何字段 / object。

**统一的是 canonical relationship semantics，不是 source representation。**

**Target Demand Context（conceptual）**

允许 conceptual：

```
Allocation → one or more explicitly resolved Target Demand Contexts
```

其中 Target Demand Context **至少**能够确定：

```
plant_id
target_material_code
required_date
```

**不得创建** `requirement_id`。

**若使用 `required_date`，必须明确：它解决的是 Target Applicability，
不自动解决 Source Reservation。**

**Source Reservation Context**

Canonical mapping **必须**能够可靠判断：某 **Source Demand Context** 是否与
allocation reservation 属于 **overlapping / applicable context**。

如果**无法判断** → `DATA_INCOMPLETE`。

**但不得在本 Task 自行定义**：时间区间算法 / priority / scheduling / FIFO / earliest demand wins。

**Mapping Outcome Concept（conceptual）**

```
Target Applicability:        applicable  /  not applicable   /  unresolved
Source Reservation Overlap:  overlaps    /  does not overlap /  unresolved
```

这些**只是 conceptual mapping outcomes** —— **不是** runtime enum、canonical persisted field、
Business Status 或 Validation Status。

**不得创建** `AllocationApplicabilityStatus` / `DemandWindowStatus` 等字段。

**Explicitly Not Applicable vs Unresolved**

| # | 情形 | 性质 | 处理 |
| --- | --- | --- | --- |
| **A** | allocation **明确不适用**于某 `required_date` | **valid but not applicable** | **不得** `DATA_INCOMPLETE` |
| **B** | **无法判断**是否适用 | semantic / mapping **unresolved** | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED`；capability 需要时 → `DATA_INCOMPLETE` |

**不得把两者混为一类。**

**Cumulative Supply Boundary**

`CumulativeApprovedSubstituteSupply(<= t)` **不能**因为 cumulative 就**重复累计同一笔 allocation**。

同一 allocation 一旦已经归属于明确的 **Target Demand Context / applicability context**，
其 quantity **不得**在多个 `required_date` 被当成**新的独立 allocation** 重复相加。

**但本 Task 不设计** allocation consumption engine —— **只定义** same allocation **must not be double counted**。

**Source Conservation Boundary**

```
EligibleSubstituteSupply = 100
Allocation = 60
→ RemainingUnallocatedSourceSupply = 40     （在 allocation reservation 有效的 context 内）
```

**不得**：Target 得到 `60`，同时 Source Material 仍按**完整 `100`** 作为 uncommitted supply。

**但 reservation 超出 / 不适用于某 context 时如何处理，必须来自可靠 demand-window mapping，不得猜。**

**Multiple Targets**

```
MAT-B AVAILABLE = 100
  60 → MAT-A
  30 → MAT-C
```

**不能**只把 `60 + 30` 机械比较 `100` —— **除非两个 reservation context 确实重叠**。

因此必须评估：现有

```
Σ AllocatedSubstituteQty <= EligibleSubstituteSupply
```

是否应被理解为 **within the same effective reservation context**，
而**不是**所有历史 allocation **永久相加**。

> **注意**：如果这构成对 `§2.3.10` 的 **substantive semantic modification**，
> 则**必须** `STOP` ＋ **Human Attention** —— **不得自行重写 Business Rule**。
>
> **本 Review 的判断**：`§2.3.10` 自身已写明 reservation **只作用于 allocation 有效的 demand window**，
> 因此「在同一有效 reservation context 内求和」与既有文本**方向一致**；
> **但该读法是否构成语义修改，须由 Human 确认**（见 **Human Decision Required** 第 5 项）。

**Missing vs Unresolved vs Conflict**

| # | 情形 | 处理 |
| --- | --- | --- |
| **A** | Allocation evidence role **missing** when required | 既有 `MISSING` / capability handling |
| **B** | Allocation **exists**，但 demand-window mapping **无法解析** | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED` → `DATA_INCOMPLETE` when required |
| **C** | Mapping **已解析**，但同一 effective context 出现 **over-allocation** | `CONSISTENCY` / `CONSISTENCY_CONFLICT` → `DATA_INCOMPLETE` |

**不得全部归为** `Allocation Conflict`。

**No Automatic Allocation**

本 Task **只处理**「已有 **explicit** allocation 如何映射到需求时间上下文」。

**不得设计**：shortage priority / target priority / source priority / earliest `required_date` first /
proportional allocation / greedy allocation / optimization / auto reallocation / scheduling。

**Provenance**

每个 allocation mapping **未来必须能够追溯**：

```
source allocation evidence
→ Substitute Relationship
→ Target Demand Context
→ Source Reservation Context
→ Snapshot Package
```

**但 physical provenance carrier 仍属 `§4.3` 后续设计**（**logical provenance carrier = `DESIGN RESOLVED`**，见 **§4.5.22 Option D Implementation Record**）；
**不得创建** lineage schema / allocation ID schema / DB table / JSON metadata。

**Canonical Model Compatibility Result**

```
A. COMPATIBLE
```

**依据**：`§4.1.4 G` 的 grain **已包含** `effective demand context` 作为组成部分，
且 attributes 已列出该 context。**Option B 在不新增 canonical field 的前提下**，
把 `effective demand context` 定义为 **conceptual resolved context**
（引用**既有** `Production Requirement` 的 `plant_id` / `material_code` / `required_date`）。

因此**无需**新增 `required_date` / `valid_from` / `valid_to` / `requirement_id` /
`allocation_period` 或其他 canonical identity component。

> **本 Review 未发现**需要修改 `§4.1` 的理由 —— 因此**不触发** Blocking Finding，
> **不需要** Minimal Model Change Options。

**Status（PR #36 Review 时点）**

```
allocation demand-window mapping = DESIGN PENDING    ← 本 Review 不改变
unresolved count                 = 仍为 5
```

**Human Decision Required**

请 Human 决定：

1. 是否接受 **`Canonical Model Compatibility = COMPATIBLE`**
2. 是否采用 **Option B**（source-specific mapping → canonical **Target Applicability** ＋ **Source Reservation Overlap**）
3. 是否确认 **`explicitly not applicable` ≠ `unresolved`**
4. 是否确认 **demand-window mapping 只解释已有 explicit allocation，不产生 allocation**
5. 是否确认 `Σ AllocatedSubstituteQty <= EligibleSubstituteSupply` 应被理解为
   **within the same effective reservation context**（而非所有历史 allocation 永久相加）——
   即确认该读法**不构成**对 `§2.3.10` 的 **substantive semantic modification**
6. 是否授权必要的 **`§4.1` / `§4.2` / `§4.4` / `§4.5` 最小 consistency synchronization**

**Human Approval 后**，下一 Task 才正式实施。

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 以下为 Human 对上述 6 项的**正式回复**（本 Review 由 **PR #36** 提交）。
> 本节**只记录决定**；**未**执行 `§4.1` / `§4.2` / `§4.4` / `§4.5` 的 Option B semantic synchronization。

| # | 决定项 | Human Decision |
| --- | --- | --- |
| 1 | `Canonical Model Compatibility` | **`COMPATIBLE` ACCEPTED** |
| 2 | 是否采用 Option B | **APPROVED** |
| 3 | `Target Applicability` 与 `Source Reservation Overlap` 是否分离 | **CONFIRMED（必须分离）** |
| 4 | Conceptual mapping outcomes | **APPROVED** |
| 5 | `explicitly not applicable` ≠ `unresolved` | **CONFIRMED** |
| 6 | `§2.3.10` summation interpretation | **APPROVED（`§2` semantic 未修改）** |
| 7 | `§4.1` / `§4.2` / `§4.4` / `§4.5` 最小 consistency synchronization | **AUTHORIZED** |

**决定 1 —— Canonical Model Compatibility = `COMPATIBLE`（ACCEPTED）**

接受 Review 结论：当前 `§4.1.4 G Substitute Allocation` 的 grain

```
source substitute material
+ target material
+ effective demand context
```

**已经具有足够的 conceptual capacity** 承载本 POC 的 demand-window mapping contract。

因此当前**不需要**新增：`required_date` canonical field / `requirement_id` / `demand_window_id` /
`allocation_period` / `valid_from` / `valid_to` / 新 canonical entity。

**不得改变**现有 Substitute Allocation grain。

**决定 2 —— Option B = APPROVED**

```
source-specific allocation evidence
        ↓
explicit deterministic mapping
        ↓
canonical allocation applicability relation
        ├─ Target Applicability
        └─ Source Reservation Overlap
```

Canonical Design 统一的是 **relationship semantics**，**不是** **source representation**。

未来不同 Adapter **可以**使用不同真实 source evidence，但**必须**可靠产生上述两个 conceptual relation。

**决定 3 —— Target Applicability / Source Reservation = CONFIRMED（必须分离）**

```
Target Applicability  ≠  Source Reservation Overlap
```

- **Target Applicability** 回答：该 allocation 对 **Target Material** 的**哪些** `required_date` /
  demand contexts **可以作为** Approved Substitute Supply
- **Source Reservation Overlap** 回答：同一 Source Supply 在**哪些** Source Material demand contexts
  **不得继续**作为 uncommitted supply 重复使用

**不得**只解析 Target Applicability 就宣称 **No Double Allocation / Supply Conservation** 已经可靠完成。

**决定 4 —— Conceptual Mapping Outcomes = APPROVED**

```
Target Applicability:        applicable / not applicable   / unresolved
Source Reservation Overlap:  overlaps   / does not overlap / unresolved
```

**只属于 conceptual mapping outcomes** —— **不是** Business Status / runtime enum /
canonical persisted field / Validation Status / DB enum / API enum。

**不得创建** `AllocationApplicabilityStatus` / `DemandWindowStatus` 等字段。

**决定 5 —— `explicitly not applicable` ≠ `unresolved`（CONFIRMED）**

| # | 情形 | 性质 | 处理 |
| --- | --- | --- | --- |
| **A** | allocation evidence 本身有效，但**明确不适用**于当前 Target Demand Context | **valid but not applicable** | 默认 **NO `DATA_INCOMPLETE`** |
| **B** | **无法可靠判断** allocation 是否适用于当前 context | semantic / mapping **unresolved** | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED`；capability 需要该 allocation 时 → `DATA_INCOMPLETE` |

**不得混淆 A / B。**

**决定 6 —— Demand-Window Mapping 不产生 Allocation（CONFIRMED）**

本 mapping **只解释已经存在的 explicit allocation**。**不得**：

- 创建 allocation
- 决定 allocation quantity
- 修改 `AllocatedSubstituteQty`
- 自动分配 supply
- 自动 reallocation
- shortage priority / target priority / source priority
- earliest demand wins
- proportional allocation / greedy allocation
- optimization / scheduling

**决定 7 —— `§2.3.10` Summation Interpretation = APPROVED（`§2` semantic 未修改）**

```
Σ AllocatedSubstituteQty <= EligibleSubstituteSupply
```

**应理解为 within the same effective reservation context**，
而**不是**所有历史 allocation **跨所有时间永久累计**。

该解释**不构成**对 `§2.3.10` 的 **substantive semantic modification**。

原因：`§2.3.10` 已明确规定 reservation **只作用于 allocation 有效的 demand window**，
并要求「如果 allocation 与 Source Material 自身 demand window 是否重叠无法可靠判断 → `DATA_INCOMPLETE`」。

因此本决定只是 **clarification / consistency interpretation** ——
**不得修改 `§2` Business Rule 正文**。

**Multiple Contexts Boundary**

```
Eligible MAT-B Supply = 100
  Context W1：60 → MAT-A
  Context W2：50 → MAT-C
```

**只有当 `W1` 与 `W2` reservation overlap 时**，才可以**在同一 conservation context** 判断 `60 + 50 > 100`。

如果 `W1` / `W2` overlap **无法可靠判断**：

```
SEMANTIC_UNRESOLVED → DATA_INCOMPLETE
```

**不得**自动视为重叠，也**不得**自动视为不重叠。

**决定 8 —— Cumulative Supply Boundary（CONFIRMED）**

`CumulativeApprovedSubstituteSupply(<= t)` 中的 **cumulative 不得**导致同一 allocation
在多个 `required_date` 被当作**新的独立 supply** 重复累计。

同一 allocation **只能**根据其已解析的 **Target Applicability context** 参与对应 calculation。

**但本 Design 不实现** consumption engine。

**决定 9 —— Missing / Unresolved / Conflict Boundary（CONFIRMED）**

| # | 情形 | 处理 |
| --- | --- | --- |
| **A** | required Allocation evidence role **missing** | 使用既有 `MISSING` / capability-evidence handling |
| **B** | allocation **exists**，但 demand-window mapping **无法可靠解析** | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED` → `DATA_INCOMPLETE` when required |
| **C** | mapping **已可靠解析**，且在同一 effective reservation context **真实发生** over-allocation | `CONSISTENCY` / `CONSISTENCY_CONFLICT` → `DATA_INCOMPLETE` |

**不得全部叫** `Allocation Conflict`。

**决定 10 —— Minimal Consistency Synchronization = AUTHORIZED（授权边界）**

后续专门的 **Design Change Task** 被授权对 `§4.1` / `§4.2` / `§4.4` / `§4.5` 做实施 Option B
所必需的**最小 consistency synchronization**。

**`§4.1` 授权边界尤其严格** —— **只允许澄清**：

```
effective demand context 现在承载
Target Applicability ＋ Source Reservation Overlap
的 conceptual resolved context
```

**不得**：修改 Substitute Allocation grain / 新增 canonical field / 新增 canonical entity /
新增 identity component / 重构 Canonical Model。

**`§4.2` / `§4.4` / `§4.5` 只允许**：mapping contract / applicability·overlap semantics /
not applicable vs unresolved / conservation context / validation path / status synchronization。

**决定 11 —— Provenance Boundary（保持）**

```
source allocation evidence
→ Substitute Relationship
→ Target Demand Context
→ Source Reservation Context
→ Snapshot Package
```

**必须未来可追溯。** 但 **physical provenance carrier 仍属 `§4.3` 后续设计**（**logical provenance carrier = `DESIGN RESOLVED`**，见 **§4.5.22 Option D Implementation Record**）；
**不得**因本决定创建任何 physical lineage carrier。

**执行状态（PR #36 时点）**

```
Human Decision                   = RECORDED
Canonical Model                  = COMPATIBLE
Option B                         = APPROVED
§2.3.10 semantic                 = UNCHANGED
Semantic Synchronization         = NOT YET IMPLEMENTED
allocation demand-window mapping = DESIGN PENDING
unresolved count                 = 仍为 5
```

**PR #36 当时不实施** `§4.1` / `§4.2` / `§4.4` / `§4.5` 的 Option B semantic synchronization；
`allocation demand-window mapping` 当时**保持 `DESIGN PENDING`**，unresolved count 当时**仍为 5**。

> 以上为**历史记录**。后续 **Human-authorized Option B Implementation** 已实施并变更该状态 ——
> 见下方 **Option B Implementation Record**。

**Option B Implementation Record（Human-authorized Design Change）**

**Human Authorization Source**

```
PR #36 Human Decision
  → Canonical Model                        = COMPATIBLE
  → Option B                               = APPROVED
  → Target Applicability ≠ Source Reservation Overlap
  → conceptual outcomes                    = APPROVED
  → not applicable ≠ unresolved            = APPROVED
  → mapping does not create allocation     = APPROVED
  → summation within same effective reservation context = APPROVED
  → §2.3.10 semantic                       = UNCHANGED
  → minimal synchronization（§4.1/§4.2/§4.4/§4.5）    = AUTHORIZED
```

**Implementation Result**

```
source-specific allocation evidence
        ↓
explicit deterministic mapping
        ↓
canonical allocation applicability relation
        ├─ Target Applicability
        └─ Source Reservation Overlap
```

该 contract 统一的是 **relationship semantics**，**不是** **source representation**。

**Target Applicability（正式定义）**

对某个 **Target Demand Context**，至少能够可靠确定：

```
plant_id
+ target_material_code
+ required_date
```

**不得创建** `requirement_id`；**不得修改** `Production Requirement` grain。

Allocation **可以**被映射到 **one or more explicitly resolved Target Demand Contexts** ——
例如同一 allocation `A1` 对 `R1` **applicable**、对 `R2` **not applicable** 或 **unresolved**。

**必须来自 explicit source-specific mapping evidence** ——
**不得**按 `required_date` proximity 自动匹配。

| Outcome | 含义 | 处理 |
| --- | --- | --- |
| **`applicable`** | 该 explicit allocation 对当前 Target Demand Context **可以进入** `CumulativeApprovedSubstituteSupply` 的**候选计算** | 仍必须同时满足既有 `approved relationship` / `same Plant` / eligible `AVAILABLE` source supply / valid quantity / `substitution_ratio` / 其他 `BR-SUBSTITUTE-001` 约束；**Target applicable 不自动等于最终 supply result** |
| **`not applicable`** | allocation evidence **本身有效**，但**明确不属于**当前 Target Demand Context | **valid but not applicable**；默认 **NO Validation Issue**、**NO `DATA_INCOMPLETE`**；**不得计入**当前 Target `CumulativeApprovedSubstituteSupply`；**必须保持 `not applicable ≠ unresolved`** |
| **`unresolved`** | **无法可靠判断**是否适用于当前 Target Demand Context | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED` → capability 需要该 substitute evidence 时 `DATA_INCOMPLETE`；**不得** default applicable / default not applicable / closest date wins / earliest date wins / LLM guess |

**Source Reservation Overlap（正式定义）**

回答：当前 explicit allocation 占用的 Source Supply，与某 **Source Material Demand Context**
是否属于**同一个 effective reservation context**。

| Outcome | 处理 |
| --- | --- |
| **`overlaps`** | 已分配 quantity **不得**在该 context：再分配给其他 overlapping Target ／ 作为 unallocated substitute supply ／ 被多个 shortage 重复消费 ／ 继续作为 Source Material 自身**完整** uncommitted supply；继续继承 `RemainingUnallocatedSourceSupply = EligibleSubstituteSupply - Σ AllocatedSubstituteQty`，但 **sum 必须属于 same effective reservation context** |
| **`does not overlap`** | **不得**因为历史上存在 allocation 就**永久锁死**该 Source Supply；必须明确 allocation reservation **不是** forever reservation、**也不是** entire Analysis Run reservation（除非 source-specific evidence 明确支持该 context）；**但本 Task 不设计** allocation release / consumption / inventory replenishment engine |
| **`unresolved`** | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED` → 当 shortage / substitute calculation 需要判断该 supply 是否仍可使用时 `DATA_INCOMPLETE`；**不得**默认 overlap、**不得**默认 no-overlap，尤其**不得**为了**保守**或**乐观**而自动选边 |

**Conceptual Outcomes Boundary**

`applicable` / `not applicable` / `unresolved` 与 `overlaps` / `does not overlap` / `unresolved`
**只是 conceptual mapping outcomes** —— **不是** Business Status / runtime enum /
canonical persisted field / database enum / API enum / Validation Status。

**不得创建** `AllocationApplicabilityStatus` / `DemandWindowStatus` / `ReservationOverlapStatus`。

**§2.3.10 Summation Interpretation（记录于 downstream Design；`§2` 正文未修改）**

```
Σ AllocatedSubstituteQty <= EligibleSubstituteSupply
    → within the same effective reservation context
```

**不是** all historical allocations **forever accumulated**。
这是 **Human-approved clarification（PR #36 Human Decision）**，**不是** Business Rule semantic change。

**Cumulative / No Double Counting**

`CumulativeApprovedSubstituteSupply(<= t)` 中的 **cumulative 不表示**同一 allocation
每经过一个 `required_date` 都重新贡献一次 quantity。
同一 explicit allocation **必须保持其 identity / evidence continuity**，
只能依据**已解析的 Target Applicability** 参与相应 context 的计算 ——
**不得** `A1` 在 `R1` 算一次，到 `R2` 又当作一笔**新的** allocation 再次累计。

**No Double Counting（canonical invariant）—— 同一 explicit allocation 不得：**

- 作为两个独立 allocation 重复出现
- 在 overlapping Target contexts 被重复消费
- 同时作为 Target allocated supply **和** Source full uncommitted supply
- 被 cumulative calculation 重复累计

> 如何通过代码 enforcement 属于 **Implementation**；本 Task **只定义 canonical invariant**。

**Mapping Does Not Create Allocation**

Demand-Window Mapping **只解释 already-existing explicit allocation**。**不得**产生：
allocation quantity / allocation decision / allocation priority / target priority / source priority /
shortage priority / auto assignment / auto reallocation / proportional allocation / greedy allocation /
earliest demand first / optimization / scheduling。

**Provenance / Cross-Package（保持）**

追溯链：

```
source allocation evidence
→ Substitute Relationship
→ Target Demand Context
→ Source Reservation Context
→ Snapshot Package
```

**但 physical provenance carrier 仍属 `§4.3` 后续设计**（**logical provenance carrier = `DESIGN RESOLVED`**，见 **§4.5.22 Option D Implementation Record**）；**不得创建** allocation ID schema / lineage table /
JSON metadata / DB relation / physical provenance fields。

跨 Package 继续继承 **`PROVENANCE` / `PROVENANCE_MISMATCH`** ——
**不得**让 Package P1 的 allocation evidence 静默组合 Package P2 的
Target Demand Context / Source Reservation mapping evidence。

**Critical Scenario Resolution（`§4.5.9` Review 场景重新验证）**

```
MAT-B AVAILABLE = 100 ／ Allocation A1 = 60 MAT-B → MAT-A
Target：R1 = MAT-A / 2026-10-10、R2 = MAT-A / 2026-10-20
Source：S1 = MAT-B / 2026-10-12
```

**新 Design 不会「自动给出答案」** —— 而是**要求** source-specific mapping 可靠给出：

| # | 必须 resolved 的 relation |
| --- | --- |
| 1 | `A1` → `R1` applicable? |
| 2 | `A1` → `R2` applicable? |
| 3 | `A1` reservation overlaps `S1`? |

**一旦三者均 resolved**，deterministic Rule 才能可靠计算；
**如果其中必要 relation unresolved → `DATA_INCOMPLETE`**。

**这正是 Design Resolution** —— **不是**要求当前 POC 发明真实 source evidence。

**Meaning of `DESIGN RESOLVED`**

`DESIGN RESOLVED` **只**表示 **canonical allocation applicability mapping contract 概念设计完成**，
**不表示**：real ERP allocation evidence known / reservation source field known /
planning-link source known / Adapter implemented / overlap calculation implemented /
allocation enforcement implemented / tested / Substitute Supply implemented / production-ready。

**执行状态（本 Task 完成时点）**

```
Human Decision                   = RECORDED
Option B                         = IMPLEMENTED
allocation demand-window mapping = DESIGN RESOLVED
unresolved count                 = 5 → 4
Other Source-Semantic Mapping    = 仍 DESIGN PENDING
Master Data Mapping overall      = 仍 DESIGN PENDING
```

**Allocation Demand-Window Mapping —— G5-A Relation Outcome 实现登记（Human Decision `Option A′` ＋ `CB-1′`）**

**Registration Status：`REGISTERED`** —— 依据 **Human Decision `Option A′` ＋ `CB-1′`**。

本登记**只**把已经 `DESIGN RESOLVED` 的 allocation applicability mapping contract 落实到
first deterministic tranche 的 runtime realization；它**不新增** canonical field ／ entity ／
identity component，**不修改**本小节前述结论，**不修改** `§4.1.4 G` 的 grain 与 attributes。

**A. Demand Context citation（`CB-1′` 第 1 ／ 2 ／ 3 ／ 4 ／ 5 条）**

```text
Target Applicability       → same AcceptedPackage 内已 resolved 的 Target Production Requirement
                             context（plant_id ＋ target_material_code ＋ required_date）
Source Reservation Overlap → same AcceptedPackage 内已 resolved 的 Source-Material
                             Production Requirement context
                             （plant_id ＋ substitute material_code ＋ required_date）
```

每条 G5-A relation handoff **必须**引用一个 exact resolved Demand Context；caller 只能提供
**待验证的 citation**，**不得**提供可信 `DemandContextReference` ／ outcome ／ Boolean。

**B. 已登记的 SIMULATED relation basis registry（exact literal → exact outcome）**

`Target Applicability`（**必须**引用 Target Demand Context）：

| exact `mapping_basis` literal | exact outcome | required observation semantics |
| --- | --- | --- |
| `SIMULATED-G5A-TA-APPLICABLE` | `applicable` | 必须登记在 `Substitute Allocation` record 的 `target_material_code` association 上 |
| `SIMULATED-G5A-TA-NOT-APPLICABLE` | `not applicable` | 同上；**合法 deterministic 结果**，**不是** DQ Issue、**不是** `DATA_INCOMPLETE` |
| `SIMULATED-G5A-TA-UNRESOLVED` | `unresolved` | 同上；source 侧**显式声明**无法可靠判断 |

`Source Reservation Overlap`（**必须**引用 Source-Material Demand Context）：

| exact `mapping_basis` literal | exact outcome | required observation semantics |
| --- | --- | --- |
| `SIMULATED-G5A-SRO-OVERLAPS` | `overlaps` | 必须登记在 `Substitute Allocation` record 的 `substitute_material_code` association 上 |
| `SIMULATED-G5A-SRO-NO-OVERLAP` | `does not overlap` | 同上；**合法 deterministic 结果**；**不得**解释为 reservation 永久失效 ／ 已 release ／ 已消耗 |
| `SIMULATED-G5A-SRO-UNRESOLVED` | `unresolved` | 同上；**不得**为保守或乐观自动选边 |

这些 literal 是 **SIMULATED POC 的 technical mapping identifiers**（`§4.5.22` Layer 4 的一个
approved family）：**不是** canonical property、**不是** wire property、**不是** status vocabulary、
**不是** enum，也**不**定义任何真实 ERP field naming。

**C. 上下文中立性（不得编码 context）**

```text
一个字面 literal **不得**编码 context identity（例如 ...-TA-APPLICABLE-R1）：
同一 literal 必须可服务任意多个已 resolved demand contexts；
per-context 结论只由「citation ＋ basis」组合决定。
```

**D. 严格边界**

```text
basis ≠ outcome；context citation ≠ outcome；三者职责分离（CB-1′ 第 7 条）
literal 与 citation 一律 exact 比较：无 trim ／ case conversion ／ Unicode normalization ／
numeric coercion
basis 只绑定 same-AcceptedPackage 的 exact association（§4.3.28 E）；跨 package citation ⇒ 不解析
Target Applicability 与 Source Reservation Overlap 完全独立；不得组成 joint pair；
不得形成 R×S Cartesian product（CB-1′ 第 9 ／ 10 条）
cardinality：for each allocation ＋ relation ＋ exact resolved Demand Context
             exactly one deterministic outcome reference or unresolved（CB-1′ 第 12 条）
runtime 唯一 outcome 推导路径：exact association ＋ exact registered mapping_basis
                              ＋ 已验证的 exact Demand Context citation
```

**D.1 G5-A mapping evidence 的 Stable Source Evidence Locator 要求（已批准 authority 的 consistency sync）**

```text
G5-A mapping evidence **必须**携带 non-null Stable Source Evidence Locator；
handoff 的 evidence_locator **必须**与 selected association 的 evidence[] 中至少一个 locator
**exact 相等**（无 trim ／ case conversion ／ Unicode normalization ／ numeric coercion）；
缺 locator 或 locator 不匹配 ⇒ SEMANTIC_RESOLUTION ／ SEMANTIC_UNRESOLVED；
**不得**仅凭 observation ＋ mapping_basis 选择 association。
```

本项是 **Issue #146 已批准 authority 的 consistency sync**（`CB-1′` 第 6 条：context citation 不是新的
mapping-basis evidence role），**不是**新的 Human Decision。它**不扩张** `HandoffEvidence.evidence_locator`
在其他 seam 上的通用 optional contract —— 该通用契约保持不变；本条只在 **G5-A path** 上 fail closed。

**E. 本条不采用**

```text
plant_id association 作为 outcome basis                     ← 不采用（Q2 CLOSED）
Substitute Relationship（role 7）record 作为 basis host       ← 收敛为 role 8（Q3 ／ Q4 CLOSED）
由 required_date ／ 日期 proximity ／ material equality ／
AllocatedSubstituteQty ／ approval_status 推导 outcome        ← 禁止
新增 canonical field ／ entity ／ identity component          ← 未新增
```

**执行状态（本登记时点）**

```text
Human Decision                     = RECORDED（Option A′ ＋ CB-1′）
CB-1′                              = IMPLEMENTED（authority sync ＋ runtime seam）
G5-A relation outcome realization  = DESIGN RESOLVED（Phase A runtime realization registered）
BR-SUBSTITUTE-001                  = NOT STARTED（未授权，本登记不改变）
canonical field / grain / entity    = 未新增 / 未修改
ADR-001                            = 未修改
```

> `DESIGN RESOLVED` 与 runtime realization 均**不表示** `BR-SUBSTITUTE-001` 已实现，也**不表示**
> `CumulativeApprovedSubstituteSupply` 已可计算。

**F. Downstream consumption consistency sync（Issue #148 ／ B2-A′ ＋ Option A′-R）**

本子项只为 `BR-SUBSTITUTE-001` 的 **conservation 消费**与 **allocation 绑定**提供最小一致性说明。
`§4.5.9` 前述 Target Applicability ／ Source Reservation Overlap 的定义、registry、cardinality 与
locator 要求**均未改变**。

```text
exact Source Demand Context reference 可作为 downstream conservation 的 grouping boundary
different exact Source Demand Contexts 不形成 automatic overlap relation
不得新增 reservation_group ／ demand_window_id ／ allocation_period ／ validity interval
不得修改 G5-A cardinality ／ I-8 handoff contract

retained allocation records 继续以 exact record_reference 独立绑定 G5-A relations
context mapping 不合并 allocation records
downstream BR-SUBSTITUTE-001 才执行 authorized sum ／ conservation

已注册 "unresolved" basis ⇒ 该 demand context 的 reference 仍然形成，但不携带 outcome 值
                            （不新增 canonical field ／ entity ／ identity component）
未注册 ／ 无法验证 ／ 不匹配 ／ 有歧义的 basis ⇒ 仍然不产生 reference
```

**F.1 已注册 "unresolved" basis 的 reference 形成（`§2.3.11 B` 可达性）**

`§2.3.11` B 要求**存在**替代关系但数据无法可靠取得时返回 `DATA_INCOMPLETE`，**不得**默认成 0。
该判断必须落在**该 allocation 自己那个 demand context 的 grain** 上，所以当 accepted record 注册的是
已批准的 "unresolved" basis 时，reference 仍然形成并携带已解析的 Demand Context，只是
**不携带 outcome 值**。这不是新的 outcome 推导路径：basis 仍然只从 accepted record 的 association
按 exact locator ＋ exact `mapping_basis` 选出，caller 仍然不能设置 outcome，也没有任何 Boolean 被合成。
它只是让 `BR-SUBSTITUTE-001` 能够对该 grain 报告 `DATA_INCOMPLETE`，而不是把它当作 `0` 或整个丢弃。

#### 4.5.10 Supplier-Material Relationship

**必须明确：**

```
Supplier exists + Material exists
  ≠
Supplier-Material Relationship exists
```

Supplier Risk evidence **必须**能够解析到：

```
supplier_id + material_code + relationship context
```

**不得**：Supplier Master 有该 Supplier → 自动认为其**可供应所有 Material**。

#### 4.5.11 `sourcing_status` Boundary

保持：

```
sourcing_status semantic
  = Supplier-Material relationship eligibility context
```

**当前 authoritative state（PR #33 实施后）：**

```
source vocabulary                      = SOURCE-SPECIFIC / Adapter-defined
canonical eligibility mapping contract = DESIGN RESOLVED
specific source value → eligibility condition
                                       = 仍由未来 Adapter / source-specific mapping 提供
```

`SOURCE-SPECIFIC` 是**设计描述**，**不得**创建成 runtime enum。

因此 Mapping **可以**保证：source value 与对应 relationship **被保留并可追溯**；
但**不得自行解释** `ACTIVE` / `APPROVED` / `QUALIFIED` / `BLOCKED` 等值。

如果 capability 需要 eligibility，但 **`source value → eligibility condition` 缺少足够可靠的
explicit deterministic mapping evidence**，继承：

```
SEMANTIC_RESOLUTION / SEMANTIC_UNRESOLVED
```

> **注意**：「**没有全局 source vocabulary**」**本身不是** Validation Issue ——
> 按 Human-approved **Option B**，source vocabulary **本来就是 `SOURCE-SPECIFIC`**。
> 真正的问题是 **eligibility mapping 无法可靠完成**。
>
> **PR #32 Review 时点**的 `vocabulary = DESIGN PENDING` 表述属于**历史记录**
> （见下方 Review Finding 与 Human Decision Record），
> **不再**作为本节 authoritative boundary。

**Supplier Eligibility Mapping Design Review（Review Finding）**

> **Historical record —— PR #32 Review 时点。**
> 本节中的「推荐方向（待 Human Approval）」等表述均为**该时点状态**；
> Human Decision 见下方 **Human Decision Record**，
> 实施结果见 **Option B Implementation Record**。

**Evidence Boundary**

现有 `FROZEN` / Human-approved evidence 与既有 Design 支持：

| 事实 | 来源 |
| --- | --- |
| 存在结构化 Supplier Data | `VR-006`（SC-DATA-002，Human-approved `SIMULATED`） |
| 存在 **Supplier-Material Relationship**：`supplier_id` / `material_code` / `sourcing_status` / `standard_lead_time_days` / `updated_at` | `VR-006` §A-2 |
| `sourcing_status` 的**逻辑语义** = relationship eligibility context | `§2.7.24` ／ `§4.1.4 I` ／ `§4.2.8` |
| 允许**一个 Material 对应多个已批准 Supplier** | `VR-006` §A-2 |
| Data Quality baseline **可以出现 Inactive Supplier**（`supplier_status`） | `VR-006` §A-1 |
| mapping **不得**由 Agent / AI 猜测 | `§2.7.24` ／ `§4.1.4 I` ／ `§4.4.62` ／ `§4.5.2` |

**`VR-006` 没有定义 `sourcing_status` 的具体允许值集合。**

因此：

> **不得**把任何现实 ERP / SRM 常见状态当作当前项目事实。

**本 Review 不得发明** `APPROVED` / `ACTIVE` / `QUALIFIED` / `BLOCKED` / `INACTIVE` 等 source-system enum。

**Existing Business Boundary（继续保持）**

`§2.7.24` 已定义：`sourcing_status` 用于判断该 relationship 是否属于
**当前可评估的 candidate relationship**；并明确：

```
relationship eligibility
  ≠ Supplier Ranking
  ≠ Supplier Selection
  ≠ Supplier Recommendation
```

Supplier Risk 仍**只做** **Risk Evidence evaluation**。
本 Review **不得**增加任何自动供应商选择能力。

**Critical Semantic Distinction（三态）**

必须明确区分**三种**情况：

| # | 情况 | 含义 | Business 后果 |
| --- | --- | --- | --- |
| **A** | **Relationship eligible** | 存在可靠 Supplier-Material Relationship，**且**有足够 evidence 明确确认其可进入 Risk Evaluation | 进入 Risk Evidence evaluation |
| **B** | **Relationship explicitly ineligible** | relationship 存在且可识别，但 evidence **明确**表示其不属于可评估 candidate relationship | **valid but ineligible** —— 不进入 candidate evaluation；**默认 NO Validation Issue** |
| **C** | **Relationship eligibility unresolved** | relationship 存在，但 `sourcing_status` / eligibility evidence **无法可靠解释** | **semantic unresolved**；若当前请求需要 Supplier Risk → Risk Evidence → **`DATA_INCOMPLETE`** |

**必须保持：**

```
explicitly ineligible  ≠  unresolved
```

**Option Review**

| Option | 内容 | 现有证据是否支持 | 结论 |
| --- | --- | --- | --- |
| **0** | 保持 `sourcing_status` unresolved | 支持（安全） | **安全但长期阻塞** —— Supplier Risk eligibility 无法可靠执行 |
| **A** | 定义 source `sourcing_status` enum（`APPROVED` / `ACTIVE` / `QUALIFIED` / `BLOCKED`） | **不支持** —— `VR-006` 未定义允许值集合 | **拒绝** —— 会发明 source semantic |
| **B** | source-specific status → **canonical eligibility condition**（explicit deterministic mapping） | 支持 —— 只要求存在足够 explicit eligibility evidence | **推荐方向（待 Human Approval）** |
| **C** | 引入 canonical `is_eligible` Boolean | **不支持** —— 无法可靠表达三态 | **拒绝** |
| **D** | Relationship Exists = Eligible | **违反** `§2.7.24` 与 `VR-006` | **拒绝** |

**Option 0 —— 评估**

不发明任何 source semantic（优点），但 Supplier Risk eligibility **长期无法可靠执行**。
`§4.4.62` 已为「无法解释」定义了 fail-safe 路径，因此 Option 0
**只是安全但长期阻塞**，**不是**设计终点。

**Option A —— 拒绝依据**

`VR-006` 只确认 `sourcing_status` **字段存在**，**未定义**其允许值集合。
因此定义 source enum 属于**发明 source semantic**：

- 违反 `§2.7.24`「本 Task **不定义**具体 `sourcing_status` enum / vocabulary」
- 违反 `§4.1.4 I`「**不得自行定义** `sourcing_status` enum / vocabulary」
- 违反 `§4.4.62`「**不得创建** `APPROVED` / `ACTIVE` / `QUALIFIED` / `BLOCKED` 等 source enum」

> **不得**因为「企业通常这样」就定义 source enum。

**Option B —— 推荐方向（待 Human Approval）**

保持：

```
sourcing_status  =  source / mapping evidence
```

**不要求**全企业存在一个**统一** source vocabulary。

由 **explicit deterministic mapping** 把 source-specific status 解释成 conceptual eligibility condition：

```
source-specific sourcing_status
        ↓
explicit mapping evidence
        ↓
Relationship Eligibility Condition
        ↓
eligible  /  ineligible  /  unresolved
```

**注意：** `eligible` / `ineligible` / `unresolved` **只属于**
**canonical mapping outcome / condition** —— 它们**不是**：

- source enum
- Business Status
- Risk Level
- Supplier Ranking
- persisted field schema

**Option C —— 拒绝依据**

`is_eligible = true / false` 会**错误压平**三态：
`false` 可能表示 **explicitly ineligible**，也可能被误解为 **unknown / missing**。

二者在 Business 上的后果**完全不同**（前者 NO Validation Issue；后者 `DATA_INCOMPLETE`）。
**无法可靠表示三态 → 不得采用。**

**Option D —— 拒绝依据**

```
supplier_id + material_code relationship exists   ⇏   eligible
```

违反 `§2.7.24`（`sourcing_status` 存在的意义正是判断是否属于可评估 candidate relationship），
也违反 `VR-006` 中允许出现的 **Inactive Supplier** 与非 approved relationship context。

**Source Vocabulary Boundary**

即使采用 **Option B**，**也不得**声明：

```
APPROVED → eligible
ACTIVE   → eligible
BLOCKED  → ineligible
```

等**具体映射** —— 因为当前**没有** source vocabulary evidence。

具体：

```
source value → eligibility condition
```

仍属于 **Adapter / source-specific mapping**。

**本层只定义 mapping contract。**

**`eligible` 语义**

如果最终采用 Option B，`eligible` 表示：

> 该 Supplier-Material Relationship 拥有**足够可靠的 eligibility evidence**，
> 允许其进入 `BR-SUPPLIER-RISK-001` 的 Risk Evidence evaluation。

它**不表示**：

- supplier is selected
- supplier is recommended
- supplier is best
- purchase should be placed
- procurement recommendation belongs to this supplier

**`explicitly ineligible` 语义**

如果 relationship 被**可靠判断**为 ineligible：

- 该 relationship **不进入**当前 Supplier Risk candidate evaluation
- 但 **relationship record 本身仍可能有效**

因此默认：

```
NO Validation Issue
```

只属于 **valid but ineligible**。

**不得**输出 `OverallSupplierRisk = DATA_INCOMPLETE` 来表示
「这个 relationship 明确不 eligible」—— 因为 `DATA_INCOMPLETE` 表示
**应该能够评估但 evidence 不完整**，**不是**明确的业务不适用。

**`unresolved` 语义**

如果 relationship **存在**，但 eligibility **无法可靠判断**：

```
SEMANTIC_RESOLUTION / SEMANTIC_UNRESOLVED
```

如果当前 capability **确实需要**评估该 relationship：

```
Risk Evidence Status → DATA_INCOMPLETE
```

**不得**：默认 eligible ／ 默认 ineligible ／ LLM guess。

**Missing Relationship Boundary**

| 情形 | 性质 | 处理 |
| --- | --- | --- |
| Supplier exists + Material exists + **Relationship absent** | relationship **不存在** | **不得**凭空建立 Supplier-Material Relationship（见 `§4.5.10`） |
| Relationship exists but **eligibility unresolved** | relationship **semantic resolution** 问题 | `SEMANTIC_UNRESOLVED` → Risk Evidence `DATA_INCOMPLETE` |

**不得**把后者混为 `sourcing_status missing`，也**不得**把前者当作 eligibility 问题。

**Multiple Suppliers**

`VR-006` 已允许**一个 Material 对应多个已批准 Supplier**。因此：

```
多个 eligible relationships 同时存在  =  合法情况
```

**不得**：

- 因多个 eligible Supplier 产生 conflict
- 自动排名
- 自动选择一个
- 用 SupplierRisk 高低做自动采购选择

例如：

```
Supplier A  eligible  →  LOW risk
Supplier B  eligible  →  HIGH risk
```

两者**都可以展示**。仍**不得**自动 `A > B` 或选择 `A`。

**Supplier Master Status Boundary**

`VR-006` §A-1 允许 **Inactive Supplier**（`supplier_status`）作为 Data Quality / business context。

必须评估：**Supplier Master status** 与 **Supplier-Material `sourcing_status`** 是否同一语义。

默认：

```
Supplier Master status  ≠  Supplier-Material `sourcing_status`
```

**不得**：`Supplier inactive` **自动推导** `sourcing_status` —— 除非已有**明确 approved mapping evidence**。

如果二者冲突，需要使用既有 **consistency / semantic boundary**，而**不是静默选择一个**。

**Canonical Model Impact Review**

`§4.1.4 I` `Supplier-Material Relationship` 的 attributes 已包含 `sourcing_status`。

**结论：`NO` —— 不需要修改 canonical entity grain。**

```
Supplier-Material Relationship grain = supplier_id + material_code   （保持不变）
```

Eligibility mapping **不应改变**该 relationship grain。
本 Review **未**发现需要修改 `§4.1` 的理由。

**Data Dictionary Impact Review（PR #32 Review 时点）**

`§4.2.8` / `§4.2.14` / `§4.2.16` 当时登记：

```
sourcing_status vocabulary = DESIGN PENDING
```

如果 Human 批准 **Option B**，未来可能改写为：

```
source vocabulary                      = source-specific / Adapter mapping
canonical eligibility mapping contract = DESIGN RESOLVED
```

**但本 Review PR 不修改**已批准的 canonical semantic ——
该改写涉及语义层面变化，**必须**先经 **Human Approval**（见下方 **Human Decision Required**）。

**Validation Alignment**

保持 `§4.4.62` 的核心规则：

```
eligibility 无法可靠确定 → semantic unresolved → Risk Evidence DATA_INCOMPLETE
```

**本 Review 补充结论（PR #32 Review 时点；已由 `§4.4.62` 实施）：**

```
explicitly ineligible  ≠  semantic unresolved
```

**不得**把 **valid but ineligible** 错误变成 Validation Issue。

**No New Business Enum**

**不得**把 `ELIGIBLE` / `INELIGIBLE` / `UNRESOLVED` 加入：

- Supplier Risk enum
- Business Classification
- Source System status enum

如果使用这些词，必须明确它们**只是 conceptual mapping conditions**。

**不得创建** `SupplierEligibilityStatus` field —— 除非 Human 后续明确批准。

**No Implementation**

本 Review **未创建**：source enum、database enum、`is_eligible` field、schema、mapping table、
code、Adapter、test、API、workflow、supplier ranking、supplier selector、ADR。

**未选择技术。**

**Status（PR #32 Review 时点）**

```
Supplier Eligibility Vocabulary Mapping = DESIGN PENDING    ← 本 Review 不改变
unresolved count                        = 仍为 7
```

**Human Decision Required**

请 Human 决定：

1. 是否接受 **source vocabulary 不做全局统一 enum**
2. 是否采用 **Option B**（source-specific `sourcing_status` → conceptual eligibility condition）
3. 是否接受三种 conceptual outcome：**`eligible` / `ineligible` / `unresolved`**
4. 是否确认 **`explicitly ineligible` = valid but ineligible**，**不产生** `DATA_INCOMPLETE`
5. 是否授权必要的 **`§4.1` / `§4.2` / `§4.4` 最小 consistency synchronization**
   （含 `§4.2.8` / `§4.2.16` 的 status 表述，以及 `§4.4.62` 的
   `explicitly ineligible ≠ semantic unresolved` 补充）

**只有 Human Approval 后**，下一 Task 才正式实施。

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 以下为 Human 对上述 5 项的**正式回复**（本 Review 由 **PR #32** 提交）。
> 本节**只记录决定**；**未**执行 `§4.1` / `§4.2` / `§4.4` 的 semantic synchronization。

| # | 决定项 | Human Decision |
| --- | --- | --- |
| 1 | source `sourcing_status` vocabulary 是否建立全局统一 enum | **NOT ADOPTED** —— 不建立全局统一 enum |
| 2 | 是否采用 Option B（source-specific → conceptual eligibility condition） | **APPROVED** —— 当前 POC 正式设计方向 |
| 3 | 三种 conceptual mapping outcome | **APPROVED** —— `eligible` / `ineligible` / `unresolved` |
| 4 | `explicitly ineligible` 语义 | **APPROVED** —— valid but ineligible，**NO Validation Issue / NO `DATA_INCOMPLETE`** |
| 5 | `§4.1` / `§4.2` / `§4.4` 最小 consistency synchronization | **AUTHORIZED** —— 仅限后续专门的 **Design Change Task** |

**决定 1 —— Source Global Enum = NOT ADOPTED**

原因：当前 `FROZEN` / Human-approved evidence **只支持** `sourcing_status` **存在**及其
**logical meaning**，**不支持**任何真实 ERP / SRM source vocabulary。

**不得发明**：

- `APPROVED`
- `ACTIVE`
- `QUALIFIED`
- `BLOCKED`
- `INACTIVE`

等 **source-system enum**。

**决定 2 —— Option B = APPROVED**

```
source-specific sourcing_status
        ↓
explicit deterministic mapping
        ↓
conceptual Relationship Eligibility Condition
```

该 **mapping contract** 为当前 POC 的**正式设计方向**。

**决定 3 —— Conceptual Tri-State = APPROVED**

```
eligible  /  ineligible  /  unresolved
```

**必须明确**：它们**只是 conceptual mapping conditions**，**不是**：

- source enum
- Business Status
- Supplier Risk enum
- database enum
- canonical persisted field
- Supplier Ranking
- Supplier Selection

**不得创建** `SupplierEligibilityStatus` field —— 除非未来**另行 Human-approved**。

**决定 4 —— `explicitly ineligible` 语义 = APPROVED**

```
explicitly ineligible  =  valid but ineligible
```

因此：

- **不进入**当前 Supplier Risk **candidate evaluation**
- 默认：**NO Validation Issue**、**NO `DATA_INCOMPLETE`**

**必须保持：**

```
explicitly ineligible  ≠  unresolved
```

**只有**：relationship exists，但 eligibility **无法可靠判断** 时，才：

```
SEMANTIC_RESOLUTION / SEMANTIC_UNRESOLVED
```

并在当前 capability **确实需要**该 relationship 时：

```
Risk Evidence → DATA_INCOMPLETE
```

**决定 5 —— Minimal Synchronization = AUTHORIZED（授权边界）**

后续专门的 **Design Change Task** 被授权对 `§4.1` / `§4.2` / `§4.4` 执行
**必要的最小 consistency synchronization**。

**授权范围仅包括：**

- `§4.1` **Supplier-Material Relationship eligibility semantic clarification**
- `§4.2.8` `sourcing_status` 的
  **source-vocabulary / canonical mapping-contract status synchronization**
- `§4.2` **open-items / status synchronization**
- `§4.4.62` 补充：**`explicitly ineligible ≠ semantic unresolved`**

**不得借此**：

- 修改 Supplier-Material Relationship **grain**
- 创建新的 **Business enum**
- 创建 **source enum**
- 创建 **`is_eligible` field**
- 创建 **`SupplierEligibilityStatus` field**
- 修改 **Supplier Risk thresholds**
- 引入 **Supplier Ranking**
- 引入 **Supplier Selection**
- 将 **Risk Result 自动绑定采购建议**
- 修改**其他** Business Rules

**继续保持 —— Supplier Master Status Boundary**

```
Supplier Master status  ≠  Supplier-Material sourcing_status
```

**不得**：`Supplier inactive` → 自动推导 relationship **ineligible** ——
除非**未来存在明确 approved mapping evidence**。

**继续保持 —— Multiple Eligible Relationships**

**多个 eligible Supplier-Material Relationships 同时存在是合法情况。** 例如：

```
Supplier A  →  eligible  →  LOW risk
Supplier B  →  eligible  →  HIGH risk
```

**允许同时展示。不得自动**：

- 排名
- 选择 `A`
- 排除 `B`
- 将 Risk 高低转换为采购决策

**执行状态（PR #32 时点）**

```
Human Decision                          = RECORDED
Option B                                = APPROVED
Semantic Synchronization                = NOT YET IMPLEMENTED
Supplier Eligibility Vocabulary Mapping = DESIGN PENDING
unresolved count                        = 仍为 7
```

**PR #32 当时不实施** `§4.1` / `§4.2` / `§4.4` 的 semantic synchronization；
`Supplier Eligibility Vocabulary Mapping` 当时**保持 `DESIGN PENDING`**，unresolved count 当时**仍为 7**。

> 以上为**历史记录**。后续 **Human-authorized Option B Implementation** 已实施并变更该状态 ——
> 见下方 **Option B Implementation Record**。

**Option B Implementation Record（Human-authorized Design Change）**

**Human Authorization Source**

```
PR #32 Human Decision
  → source global enum      = NOT ADOPTED
  → Option B                = APPROVED
  → conceptual tri-state    = APPROVED
  → explicitly ineligible   = APPROVED（valid but ineligible）
  → minimal synchronization = AUTHORIZED（§4.1 / §4.2 / §4.4）
```

**已实施的设计**

```
source-specific sourcing_status
        ↓
explicit deterministic mapping evidence
        ↓
conceptual Relationship Eligibility Condition
        ↓
eligible  /  ineligible  /  unresolved
```

**Source Vocabulary Policy（正式关闭错误前提）**

「需要定义全局 `sourcing_status` vocabulary」这一前提**已被正式关闭**。

```
source sourcing_status vocabulary = SOURCE-SPECIFIC
```

具体 `source value → eligibility condition` 映射由**未来 Adapter / source-specific mapping** 明确提供。
`SOURCE-SPECIFIC` 是**设计描述**，**不得**创建成 runtime enum value。

**不得建立**全局 `APPROVED` / `ACTIVE` / `QUALIFIED` / `BLOCKED` / `INACTIVE` 等 source enum。

**Tri-state Semantics（正式定义）**

| Condition | 含义 | Business 后果 |
| --- | --- | --- |
| **`eligible`** | 该 relationship 具有**足够可靠的 eligibility evidence** | **允许进入** `BR-SUPPLIER-RISK-001` Risk Evidence evaluation |
| **`ineligible`** | relationship 存在 ＋ 可识别 ＋ evidence 可可靠解释，但明确不属于当前可评估 candidate relationship | **valid but ineligible** —— 不进入 candidate evaluation；**NO Validation Issue**、**NO `DATA_INCOMPLETE`** |
| **`unresolved`** | relationship 存在，但当前 evidence **无法可靠判断**其 eligibility | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED`；capability 需要评估时 → Risk Evidence **`DATA_INCOMPLETE`** |

**必须保持：**

```
explicitly ineligible  ≠  invalid relationship
explicitly ineligible  ≠  semantic unresolved
```

**`eligible` 不表示：** supplier selected / supplier recommended / supplier best /
purchase should be placed / Procurement Recommendation belongs to that supplier。

**多个 eligible relationships 可以同时存在**（该边界见上方 **Human Decision Record**）。

**§4.1 / §4.2 / §4.4 同步结果**

- `§4.1.4 I` —— `sourcing_status` 明确为 **source / mapping eligibility evidence context**；
  补充 conceptual Relationship Eligibility Condition；**grain 未改变**（`supplier_id` + `material_code`）
- `§4.2.8` / `§4.2.14` / `§4.2.16` —— `sourcing_status` 的
  **source-vocabulary / canonical mapping-contract status** 已同步；`§4.2.16` 的 stale open item 已移除
- `§4.4.62` —— 三条路径（`eligible` / `ineligible` / `unresolved`）已同步，
  并补充 `explicitly ineligible ≠ semantic unresolved`
- `§4.4.89` —— `valid but ineligible` 原则已扩展覆盖 explicitly ineligible Supplier-Material Relationship

**不得**创建 `is_eligible` / `SupplierEligibilityStatus` 等 canonical field。
**未创建**任何 source enum、persisted eligibility field、schema、mapping table、Adapter、API、ADR。

**Supplier Selection Boundary（未改变）**

```
Relationship Eligibility  ≠  Supplier Ranking
Relationship Eligibility  ≠  Supplier Selection
Supplier Risk             ≠  Supplier Recommendation
```

**Supplier Risk 不得自动改变** `RecommendedPurchaseQty`。

**Rename Interpretation Clarification**

本项名称 `Supplier Eligibility Vocabulary Mapping` 容易被误读为「定义一个统一 vocabulary」。

**本项被解析的方式恰恰是：不建立统一 source vocabulary** ——
而是建立 **source-specific vocabulary → canonical eligibility condition** 的 **mapping contract**。

**Status**

```
Supplier Eligibility Vocabulary Mapping = DESIGN RESOLVED
Master Data Mapping overall             = 仍 DESIGN PENDING
unresolved count                        = 7 → 6
```

`DESIGN RESOLVED` **只**表示 **POC canonical eligibility mapping contract 概念设计已完成**，
**不表示**：actual source values known / ERP · SRM vocabulary known /
Adapter mapping implemented / mapping configuration exists / Supplier Risk implemented / tested。

#### 4.5.12 Warehouse Role Resolution

**Decision Question**

Warehouse 在 POC v0.2 中究竟是：

| 选项 | 内容 |
| --- | --- |
| **A** | first-class canonical business entity |
| **B** | canonical calculation grain |
| **C** | source / mapping / scope context |
| **D** | completely irrelevant |

**必须基于现有 Design 判断。**

**不得**因为真实 ERP 通常存在 Warehouse 就自动创建 canonical Warehouse entity。

**Option Review**

| 比较维度 | Option 0：保持 unresolved | Option 1：first-class canonical entity | Option 2：source / mapping / scope context | Option 3：canonical calculation grain（即 Decision Question 的 **B**） |
| --- | --- | --- | --- | --- |
| 是否改变 `BR-INVENTORY-001` grain | 否 | 否 | **否** | **是 —— 违反 Human-approved Rule** |
| 是否增加当前 P0 不需要的复杂度 | 保持现状 | **是** | **否** | **是** |
| 对 Plant-level aggregation 的影响 | **是 —— eligibility 无法判断** | 改变 aggregation 的语义来源 | 只影响 eligibility 判断，**不改变 aggregation grain** | **是 —— 直接改变 aggregation grain** |
| 对 traceability 的影响 | 无（也不提升） | 提升 | **保持 source-level granularity 可追溯** | 破坏既有 grain 一致性 |
| 是否要求新增 Business Rule | 否 | **是** | **否** | **是** |
| 是否与现有 Canonical Data Model 冲突 | 否（但**长期悬置**） | **是 —— `§4.1.4 D` 的 Inventory Snapshot attributes 不含 Warehouse** | **否** | **是 —— `§4.1.3` / `§4.1.4 D`** |
| Reversibility | —— | 低（成为 canonical identity 后移除属 breaking change） | **高** | 低 |

**Option 0 不予采用**：`§2.2.9` 已把 `warehouse ownership unresolved` 列为
**Data Quality fail-safe 触发项**，`§2.2.4` 又要求「Warehouse 必须属于同一 Plant，
且位于当前 POC Inventory Scope 中」—— 说明 Warehouse 在当前 POC 中**已经承担**必要的
reliability 判断职责，长期悬置**会阻碍** Capability Readiness。

**Option 1 不予采用**：会要求在 `§4.1 Canonical Data Model` 中**新增 canonical entity** ——
这超出本 Task 授权，且 `§4.1` 已是 `DESIGN RESOLVED` / Human-approved；
当前 `§2` 的 P0 Business Rules **全部为 Plant-level**，**没有任何 P0 requirement 是 Warehouse-level**；
项目为 **`SIMULATED` POC**，**不存在**真实 ERP Warehouse 主数据，无法可靠设计 Warehouse canonical identity。

**Option 3（canonical calculation grain）不予采用**：
直接违反 `BR-INVENTORY-001` `§2.2.1` 的 **Human-approved** grain，
并使 `OpeningUsableInventory` 与 `§2.2.5` 的 `SafetyStock` grain
（`plant_id + material_code`）**无法对齐**。

**Option D（completely irrelevant）不予采用**：
`§2.2.4`、`§2.2.9`、`§2.2.11`、`§4.2.5`、`§4.4.50` 均以 Warehouse context 作为
reliability / eligibility 的判断依据，因此 Warehouse **并非无关**。

**因此推荐并采用 Option 2。**

> 现有 Design 在**所有相关位置**一致地只把 Warehouse 当作 source-side context，
> 因此**不存在 substantive ambiguity** —— 本项可以可靠关闭，**不需要**升级 Human Attention。

**Selected Role —— 正式表述**

```
Warehouse is a source / mapping / scope context
for Plant-level inventory aggregation;
it is not a first-class canonical entity
or calculation grain in POC v0.2.
```

中文正式表述：

```
Warehouse canonical role = source / mapping / scope context
```

Warehouse 在当前 POC 中**只**用于可靠判断：

```
source inventory → belongs to which canonical Plant
source inventory → whether inside current POC Inventory Scope
```

**Warehouse 在当前 POC 中不是：**

- first-class canonical business entity
- shortage calculation grain
- independent supply-sharing boundary

**Calculation Grain 保持不变（重要）**

本 Task **不改变** `BR-INVENTORY-001` `§2.2.1` 的 canonical calculation grain：

```
OpeningUsableInventory grain
  = plant_id
  + material_code
  + inventory_snapshot_time
```

**明确禁止**改成：

```
plant_id + warehouse + material_code + inventory_snapshot_time
```

Warehouse **可以**保留 **source-level granularity**；
但 **aggregation 之后的 canonical business calculation 仍使用既有 Plant-level grain**。

同时保持 `§2.2.5` 的既有 grain：

```
SafetyStock grain = plant_id + material_code
```

**Warehouse Identity Boundary**

当前 POC **不需要、也不创建** `canonical warehouse_id`。

source-side warehouse identifier **可以存在**，但：

```
source warehouse identifier  ≠  canonical business entity identity
```

**不得**自动升级为 canonical business entity identity。

**POC Inventory Scope —— conceptual requirement**

POC Inventory Scope 的 membership 判定**必须**：

- `explicit`
- `deterministic`
- `traceable`

**不得**由以下方式决定：

- LLM
- Warehouse name
- Warehouse description
- 经验猜测

**本 Task 不设计**：physical scope list、database table、warehouse whitelist file、
configuration format、API、field name。

> POC Inventory Scope 的 **logical / source-semantic boundary** 已由现有 **Master Data Mapping** Design 解析
> （**`Other Source-Semantic Mapping` 现为 `DESIGN RESOLVED`**，见 **§4.5.22 Option D Implementation Record**）；
> **physical carrier design** 已由 **`§4.3 Field Carrier Mapping`**（见 **§4.3.25** ／ **§4.3.27**）
> 与 **`Final Import Contract`**（见 **§4.3.28** ／ **§4.3.29**，**Issue #66 Closure**）关闭，二者**均为 `DESIGN RESOLVED`**；
> 但 **actual source representation ／ extraction** 仍属 **source-specific / Adapter realization**
> —— 该部分**不属于** `Master Data Mapping` scope（**`Final Master Data Mapping` 现为 `DESIGN RESOLVED`**），
> 而属 **`Adapter Boundary`** 的范围 —— 其 **conceptual design 已由 Issue #90 Closure Validation = `PASS`** 登记为 **`DESIGN RESOLVED`**（见 **§4.6.21**）；但 **source-specific ／ runtime realization 仍 `NOT IMPLEMENTED`**，**不得**被声称已完成（**design closure ≠ implemented**）。

**两种可接受的 Source Evidence Shape**

**Shape A —— Warehouse-level source evidence**

如果 source inventory **包含** Warehouse-level records，则在进入 Plant-level aggregation 前，
**必须**能够可靠解析：

```
source warehouse context → canonical plant_id
```

并且**必须**能够可靠判断：

```
该 Warehouse 是否属于当前 POC Inventory Scope
```

如果：

- Plant ownership **unresolved**
- 或 scope membership **unresolved**

则该 inventory **不得**计入正常 `OpeningUsableInventory` —— 继承既有 Validation **fail-safe**（见 `§4.4`）。

**Shape B —— Already Plant-scoped aggregate evidence**

如果 Controlled Export **本身已经提供** **Plant + Material** 粒度的 inventory aggregate，
则**不得**强制要求人为拆回 Warehouse-level data。

**但必须**有可靠 evidence / provenance 说明：

```
该 aggregate 已经按照当前 POC Inventory Scope 形成
```

因此：

```
Warehouse-level identity
≠ 所有 Inventory evidence 的 universal required field
```

**不得**：`Warehouse absent → 自动 DATA_INCOMPLETE` —— **如果** source evidence
已经能够可靠证明 **Plant-level scope semantics**。

**Warehouse Status vs Inventory Status（概念分离）**

**不得发明** `Warehouse Status` 来替代 `Inventory Status`。

已批准的：

```
AVAILABLE  /  INSPECTION  /  FROZEN
```

是 **Inventory eligibility semantics**（`§2.2.3`）。

以 `§2.2.4` 的既有 example 为例：

| Warehouse | 状态 | 数量 |
| --- | --- | --- |
| Warehouse-01 | `AVAILABLE` | 100 |
| Warehouse-02 | `AVAILABLE` | 30 |
| Warehouse-QA | `INSPECTION` | 40 |
| Warehouse-FR | `FROZEN` | 20 |

**必须**理解为：

```
inventory records 具有对应的 Inventory Status
```

**不得**推导：

```
Warehouse-QA 这个 Warehouse 永远属于 INSPECTION
```

**Warehouse 名称与 Inventory Status 必须保持概念分离。**

> 该 example 中的 Warehouse **名称**不得被当作业务状态来源。

**Cross-Plant Boundary**

继续保持：

如果 Warehouse context 解析到 `Plant-B`，则其 Inventory：

```
不得计入 Plant-A OpeningUsableInventory
```

**但**：`Plant-B` Inventory **本身不因此 invalid**。

它只是：

```
对 Plant-A 当前 calculation ineligible
```

**不得设计**：cross-plant transfer / rebalancing / shared warehouse。

**Unknown Warehouse**

如果 Warehouse-level source evidence **存在**，但 `warehouse → Plant` **无法可靠解析**：

```
IDENTITY_RESOLUTION / UNRESOLVED_IDENTITY
```

或既有适用 Validation Reason —— 按 `§4.4.80` / `§4.4.81` 既有 Taxonomy 处理。

**不得**：`unknown warehouse → current Plant`。

如果 **Plant 已可靠确定**，但**是否在 POC Inventory Scope 无法确定**：

```
SCOPE_COVERAGE / UNRESOLVED_SCOPE
```

**不得**默认 **included**、也**不得**默认 **excluded** 后**继续宣称结果完整**。

**Warehouse Mapping Provenance**

如果 Warehouse-level mapping 被使用，则**必须未来可追溯**：

```
source warehouse context
→ Plant
→ scope resolution evidence
→ Snapshot Package
```

**但**：**physical provenance carrier 仍属 `§4.3` 后续设计**（**logical provenance carrier = `DESIGN RESOLVED`**，见 **§4.5.22 Option D Implementation Record**）。

**不得创建**：mapping table / schema / JSON / CSV / database。

**No Physical Mapping**

本 Task **不得定义**：`warehouse_code` / `storage_location` / `storage_location_id` /
`sloc` / `warehouse_number` / `plant_storage_location` / ERP field 等真实系统字段。

这些属于 **Adapter / real source mapping**。

本 Task **只解决 canonical role**。

**Future Extension（不得过度外推）**

如果未来需要：

- Warehouse-level shortage
- Warehouse transfer
- Warehouse replenishment
- warehouse-specific Safety Stock
- warehouse-specific reservation
- cross-Warehouse optimization

则**必须重新评估**：

```
Canonical Model  +  Business Rule  +  calculation grain
```

当前 Warehouse Role Resolution **不得**被解释为：

```
Warehouse 永远不会成为 canonical entity
```

它只表示：**POC v0.2 当前范围内不需要**。

**Preserve Other Pending Items（Warehouse Task 时点）**

该 Task **只**解决 Warehouse Role；当时其余未决项**继续保持**（见 **§4.5.22**）：

- `loss_rate` owner / grain —— **已由 §4.5.22 Option E Implementation Record 解析**（当时本 Task 未推进）
- `required_quantity` semantic
- BOM version / validity
- `sourcing_status` vocabulary
- `effective_arrival_date` source mapping
- allocation demand-window mapping
- `ApplicableMOQ` source —— **ApplicableMOQ Source / Applicability Design Review（Review Finding）** 与 **Human Decision Record**（**Option D = APPROVED**）见 **§4.5.22**（**Implementation = NOT YET EXECUTED**，本 Task **未**推进）
- provenance carrier

> 其中 `BOM version / validity` 已由后续 **§4.5.7** ／ **§4.1.4 N** 解析
> （**Human-authorized Canonical Model Amendment**，PR #30 ／ Option A）。

**Warehouse Acceptance Examples（A–F）**

以下为 **conceptual examples**。

**Example A —— Warehouse-level inventory**

`WH-01` → reliably mapped to `Plant-A` → **in POC scope** → `AVAILABLE` inventory `100`

**Expected：** `100` **可以**参与 `Plant-A` aggregation。

**Example B —— Warehouse belongs to another Plant**

`WH-02` → `Plant-B`；当前分析：`Plant-A`

**Expected：** **不得**计入 `Plant-A`。

> 该 source record **不是 invalid** —— 它只是对 `Plant-A` 当前 calculation **ineligible**。

**Example C —— Warehouse Plant unresolved**

`WH-X` → Plant **unknown**

**Expected：** `IDENTITY_RESOLUTION` / `UNRESOLVED_IDENTITY`；
affected inventory grain **不得形成正常结果**。

**Example D —— Scope unresolved**

`WH-01` → `Plant-A` resolved；但**是否属于 POC Inventory Scope** 无法确定

**Expected：** `SCOPE_COVERAGE` / `UNRESOLVED_SCOPE`；
**不得**默认 included / excluded。

**Example E —— Plant-level aggregate**

Source evidence：`Plant-A` / `MAT-A` / `AVAILABLE = 130`，
并有可靠 export provenance 表明该值**已经按 POC Inventory Scope** 汇总。

**Expected：** **不要求**必须存在 Warehouse-level records；
**可以**作为 Plant-level inventory evidence 使用。

**Example F —— Warehouse name does not define status**

Warehouse name：`WH-QA`；Inventory status：`AVAILABLE`

**Expected：** **不得**因为名称含 `QA` 就自动改为 `INSPECTION`。

**Status**

```
Warehouse canonical role      = DESIGN RESOLVED
Warehouse Role Resolution     = DESIGN RESOLVED
```

`Master Data Mapping` overall **现为 `DESIGN RESOLVED`**。

**A′ —— Inventory ownership ／ POC Inventory Scope Runtime Seam（Issue #136 Human Decision）**

**Registration Status：`REGISTERED`** —— 依据 **Issue #136 Human Decision**（**Inventory Runtime
Seam Decision `A′` = `APPROVED`**，2026-09-25；`Architecture Decision required = NO`、
`External runtime evidence = NO`）。

本节**只**登记既有 Warehouse role resolution（Option 2）在 runtime 上的落地契约，
**不**改变 `§2.2.1` 的 canonical calculation grain，**不**创建 Warehouse 实体／字段，
**不**重开本节的 Option Review。

```text
Warehouse remains source / mapping / scope context.
Shape A 与 Shape B 共用一个 runtime contract（§4.3.31 G I-9）。
```

**运行时判定链（caller 不可声明 outcome）：**

```text
exact association（exact canonical observation + exact Stable Source Evidence Locator）
+ exact registered mapping_basis on that association
+ approved inventory-scope mapping rule
  → deterministic scope outcome
```

**Shape A —— Warehouse-level Inventory evidence**

```text
Warehouse-level Inventory evidence
→ exact existing association
→ source warehouse context resolves canonical plant_id
→ approved basis also resolves POC Inventory Scope membership
```

**不得**：

```text
plant_id resolved → automatically in scope
warehouse name → scope
warehouse description → scope
```

**Shape B —— already Plant-scoped aggregate evidence**

```text
already Plant-scoped aggregate evidence
→ exact existing association
→ approved basis must explicitly establish that
  this aggregate was formed under current POC Inventory Scope
```

**不得**：

```text
Plant-level aggregate → automatically in scope
```

**已登记的 SIMULATED scope basis registry（exact literal → exact semantic）**

| exact `mapping_basis` literal | source shape | scope membership | required observation semantics |
| --- | --- | --- | --- |
| `SIMULATED-INV-SCOPE-A-IN` | A（warehouse-level） | `IN_SCOPE` | 必须登记在 `plant_id` association 上 |
| `SIMULATED-INV-SCOPE-A-OUT` | A（warehouse-level） | `OUT_OF_SCOPE` | 必须登记在 `plant_id` association 上 |
| `SIMULATED-INV-SCOPE-B-IN` | B（already Plant-scoped aggregate） | `IN_SCOPE` | `plant_id` 或 `on_hand_qty` association |
| `SIMULATED-INV-SCOPE-B-OUT` | B（already Plant-scoped aggregate） | `OUT_OF_SCOPE` | `plant_id` 或 `on_hand_qty` association |

这些 literal 是 **SIMULATED POC 的 technical mapping identifiers**（`§4.5.22` Layer 4
Mapping ／ Resolution Basis 的一个 approved family）；它们**不是** canonical property、
**不是** wire property、**不是** status vocabulary，也**不**定义任何真实 ERP field naming。

**Shape A 的 ownership provenance（重要）**

warehouse-level 家族的 basis **必须**登记在 `plant_id` association 上：只有该 association 才证明

```text
source warehouse context → canonical plant_id
```

若 A 系 basis 登记在 `on_hand_qty` ／ `inventory_status` ／ `inventory_snapshot_time` ／
`material_code` 等其它 association 上，则：

```text
Plant ownership 未被证明 → IDENTITY_RESOLUTION / UNRESOLVED_IDENTITY
scope membership 保持 unresolved → SCOPE_COVERAGE / UNRESOLVED_SCOPE
```

**不得**因为 record 上恰好存在 `plant_id` value 就把它当作已证明 ownership。
Shape B 不得因此退化：Plant-scoped aggregate 仍由其 approved aggregate ／ Plant association
＋ basis 证明「该 aggregate 已按当前 POC Inventory Scope 形成」。

**三类 prerequisite 相互独立**

```text
canonical Inventory grain readiness
  !=  Plant ownership resolution
  !=  POC Inventory Scope resolution
```

missing `inventory_snapshot_time` 或 missing `material_code` 只令 canonical Inventory grain
readiness 不成立；Plant ownership 仍按 accepted canonical evidence 中可用的 `plant_id` 独立判断，
scope resolution 亦独立执行。三者由后续 deterministic rule 分别检查。

**Runtime 行为（不得默认 included ／ excluded）：**

```text
resolved IN_SCOPE        → scope context resolved / in_scope = true
resolved OUT_OF_SCOPE    → scope context resolved / in_scope = false（合法 exclusion，
                           不是 DATA_INCOMPLETE、不是 Data Quality defect；contribution = 0）
no handoff ／ unverifiable association ／ unknown basis ／ cardinality != 1
                         → SCOPE_COVERAGE / UNRESOLVED_SCOPE
ownership 无法可靠建立    → IDENTITY_RESOLUTION / UNRESOLVED_IDENTITY
```

同一条 record 上存在多个 association 时，**必须**使用 `exact observation` ＋ `exact locator`
命中的 association；**不得**从 association A 借 `mapping_basis` 给 association B 使用。
只有 scope resolution 完成后，Inventory evidence 才能进入正常 numeric inventory calculation。

#### 4.5.13 Cross-System Identifier Boundary

当前 POC **可以**存在 source-specific identifier 与 canonical identifier **不同**的情况。

**但是：** 两者之间**必须有 explicit mapping evidence**。

**不得**要求它们字符串**完全一致**。

同时**不得允许**：没有 mapping evidence，却通过 `trim` / case conversion / prefix removal /
substring / name similarity 等方式**自行推断**相同实体。

任何 **normalization policy**，如果未来需要，**必须显式设计**。

#### 4.5.14 Mapping Provenance

每个成功 mapping **必须未来可追溯**：

```
source identity context
  → canonical identity
  → mapping evidence
  → Snapshot Package
```

**现行状态：**

```
provenance carrier = DESIGN RESOLVED
```

**Mapping Provenance Requirement** 为 **`DESIGN RESOLVED`**；
其 **carrier contract** 已由 **Option D（Layered Logical Provenance Contract）** 落地
（见 **§4.5.22 Option D Implementation Record**）。

本 Task **不设计**：mapping table / lineage DB / JSON object / `source_system_id` schema ——
**physical carrier** 仍属 **§4.3** 后续设计。

> **Mapping Provenance Requirement** 本身为 **`DESIGN RESOLVED`**；
> **carrier contract** 的 **Design Review** ／ **Human Decision Record** ／ **Option D Implementation Record**
> 见 **§4.5.22** —— **Layered Logical Provenance Contract** 已落地，
> 因此 `provenance carrier` **现为 `DESIGN RESOLVED`**（physical carrier 仍属 **§4.3**）。

#### 4.5.15 Snapshot Consistency

Mapping **必须属于**当前 Analysis Run 所绑定的 **accepted Snapshot Package context**。

**不得：**

```
Package P1 的 business evidence
+
Package P2 的 identity mapping
```

静默组成**同一个** Analysis Run。

如果跨 Package mapping 未来被允许：**必须作为新 Design**。

#### 4.5.16 Mapping Conflict

如果**同一 source identity** 在**同一有效 mapping context** 中指向**多个不同** canonical identities，
且**无既有 precedence rule**，**不得**：

- first wins
- latest wins
- choose smallest ID
- choose most frequent
- LLM decide

应视为 **unresolved identity / consistency issue**，并限制到：

```
affected evidence → grain → capability
```

**不得默认** reject entire Package —— **除非**同时破坏 **Package structural integrity**。

#### 4.5.17 Missing Mapping

必须区分：

```
source evidence absent
与
source evidence exists but canonical mapping unavailable
```

后者是 **identity / relationship resolution problem**。

**不得** `mapping missing → business value = 0`。

例如：**Inbound Material 无法解析** **不得**解释成「该 Material 没有 Inbound」。

#### 4.5.18 No Silent Canonicalization

**禁止：**

- `source Material = "MAT-001 "` 自动变成 `MAT-001`
- `source Supplier name` 自动变成 `supplier_id`
- `source Plant nickname` 自动变成 `plant_id`

**除非**未来批准**明确 normalization / mapping rule**。

本 Task **不设计**这些规则。

#### 4.5.19 Mapping Registry Concept

允许定义 conceptual：**Master Data Mapping Registry**，用于表达：

- Source Identity Context
- Canonical Entity Type
- Canonical Identity
- Mapping Evidence / Basis
- Snapshot / provenance context
- resolution condition

**但不得设计**：DB schema / CSV / JSON / table name / mapping service / API。

#### 4.5.20 Relationship Mapping Registry

允许 conceptual 表达 **relationship mapping**，至少包括：

- BOM parent → component（requirement-scoped；见 **§4.1.4 N**）
- Substitute source → target
- Supplier ↔ Material
- Warehouse → Plant / scope context

**但不得创建新的 Business Relationship。**

它**只记录**已有 Design 要求的 relationship resolution。

#### 4.5.21 Effective Arrival Date Source Mapping

**Effective Arrival Date Source Mapping Design Review（Review Finding）**

**Evidence Boundary**

现有 `FROZEN` / Human-approved evidence 与既有 Design 支持：

| 事实 | 来源 |
| --- | --- |
| Purchase Order / Inbound 数据可得且具备最低必要结构 | `VR-005`（SC-DATA-001，Human-approved `SIMULATED`）§D |
| 最低概念属性中存在 `promised_date` 与 `expected_arrival_date` | `VR-005` §D |
| 数据能够表达 **Promised Date** 与 **Expected Arrival Date** | `VR-005` §D |
| `effective_arrival_date` 的 **canonical business semantic** | `§2.6.4`（`BR-INBOUND-001`） |
| 只有 `effective_arrival_date <= t` 的 eligible inbound 进入累计 | `§2.6.5` ／ `§2.6.6` |
| `effective_arrival_date` **missing / invalid** → `DATA_INCOMPLETE`（**不得**默认任何日期） | `§2.6.5` |
| **source-field mapping 留给后续 Data Dictionary ＋ Adapter Contract** | `§2.6.4` |

**`VR-005` 没有批准**：

```
promised_date          = effective_arrival_date
expected_arrival_date  = effective_arrival_date
```

**也没有批准** `expected > promised` 或 `promised > expected` 的 **precedence**。

因此：**不得**把任何一个字段直接声明为**全局 canonical source**。

**Semantic Distinction Review**

必须明确评估 `promised_date` 与 `expected_arrival_date` **是否可以安全假定为同一个 semantic**。

**默认：不得假定。**

| 字段 | 可能的**解释**（possible interpretation，**非**企业事实） |
| --- | --- |
| `promised_date` | supplier / PO **commitment** context |
| `expected_arrival_date` | 当前**预计实际到达** context |

> 当前项目**没有真实 ERP / SRM semantic evidence** ——
> 以上只是 **possible interpretations**，**不得**写成**真实 CY 企业事实**。

**Option Review**

| Option | 内容 | 现有证据是否支持 | 结论 |
| --- | --- | --- | --- |
| **0** | 保持 mapping unresolved（要求 `effective_arrival_date` 必须可可靠取得，否则 `DATA_INCOMPLETE`） | 支持（安全） | **安全但长期阻塞** |
| **A** | Always use `promised_date` | **不支持** —— `VR-005` 未赋予其 canonical precedence | **拒绝** |
| **B** | Always use `expected_arrival_date` | **不支持** —— 同上 | **拒绝** |
| **C** | Global deterministic precedence（例如 `expected` fallback `promised`） | **不支持** —— 无任何 Human-approved evidence 支持 precedence | **拒绝** |
| **D** | **source-specific mapping → canonical `effective_arrival_date`** | 支持 —— 只要求存在 explicit deterministic mapping evidence | **推荐方向（待 Human Decision）** |
| **E** | Take earliest / latest candidate date（`min` / `max`） | **不支持** —— 会**创造新的业务算法** | **拒绝** |

**Option 0 —— 评估**

不发明 source semantics（优点），但 `Effective Inbound` **长期无法可靠执行**；
`§2.6.5` 已为 fail-safe 定义了 `DATA_INCOMPLETE` 路径，
因此 Option 0 **只是安全但长期阻塞**，**不是**设计终点。

**Option A / B —— 拒绝依据**

`VR-005` 只确认两个字段**存在**且可表达，**未**赋予任何一方 canonical precedence。
选定其一等于**发明 source semantic**。

**Option C —— 拒绝依据**

建立**全局** precedence 需要 Human-approved evidence；
当前**没有任何** evidence 支持 `expected > promised` 或 `promised > expected`。

**Option E —— 拒绝依据**

`min` / `max` **不是** mapping，而是**新的业务算法** ——
它会在没有业务依据的情况下**改变**有效供给的日期口径。

**Recommended Direction（Option D）**

```
source-specific arrival-date evidence
        ↓
explicit deterministic mapping
        ↓
canonical effective_arrival_date
```

该 contract 的目标是统一：

```
business semantic
```

而**不是**统一：

```
source field name
```

不同 source system **可以**拥有不同的 arrival-date semantics；未来 Adapter **可以**明确声明：

```
Source A: field X → effective_arrival_date
Source B: field Y → effective_arrival_date
```

或：

```
source-specific approved precedence → one canonical date
```

**但本层不定义真实 source field / precedence。**

> **与当前架构一致**：canonical semantic 属于本 Design；
> 具体 field 解析属于 **future source-specific Adapter mapping**（见下方 **Adapter Boundary**）。

**Canonical Outcome**

canonical side **只需要**：

```
effective_arrival_date   （一个已解析的 DATE business value）
```

**不得创建**：`ArrivalDateSourceType` / `ArrivalDatePriority` / `PromisedOrExpected` /
`ArrivalConfidence` 等**新 canonical fields** —— 除非未来 Human 另行批准。

**Exactly One Resolved Date per Inbound Context**

对一个需要参与 `BR-INBOUND-001` 判断的 inbound context，最终**必须**能够得到：

```
exactly one reliably resolved effective_arrival_date
            或
unresolved
```

**不得**让 deterministic business rule 同时面对 `promised_date` ＋ `expected_arrival_date`
然后**临时自行选择**。

```
source semantic resolution 必须发生在进入 BR-INBOUND-001 之前
```

**Multiple Candidate Dates**

如果 source context 中 `promised_date` ＋ `expected_arrival_date` **同时存在且不同**，
但**没有** source-specific approved mapping / precedence evidence：

**不得**：

- choose `promised_date`
- choose `expected_arrival_date`
- earliest wins
- latest wins
- newest `updated_at` wins
- average
- LLM choose

结果：

```
effective_arrival_date = unresolved
```

当前 capability 需要 inbound 时：**`DATA_INCOMPLETE`**，
并使用**既有 Validation Taxonomy** 表达 root cause。

**Single Candidate Does Not Automatically Mean Canonical**

即使 source record **只有一个**日期字段存在，**也不得**仅因为「只有它有值」
就自动认为它 `= effective_arrival_date`。

**必须先有 approved source-specific semantic mapping。** 例如：

```
promised_date exists  ＋  expected_arrival_date missing
   ≠  promised_date automatically canonical
```

**Missing Value vs Unresolved Mapping**

必须区分：

| # | 情形 | 处理 |
| --- | --- | --- |
| **A** | **approved mapping 已存在**，但 mapped source value **missing** | `FIELD_VALUE` / `MISSING` 或既有适用 reason |
| **B** | source value **存在**，但**不知道哪个 source semantic** 应映射到 `effective_arrival_date` | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED` |

**不得**把两者都写成 `effective_arrival_date missing`。

**Invalid Date Boundary**

如果 approved mapping **已确定**（`Source Field X → effective_arrival_date`），
但值本身**无法解析成合法 `DATE`**，属于：

```
FIELD_VALUE / INVALID_TYPE
```

或既有适用 Field Validation reason。

**不得** fallback 到另一个**未批准**字段。

**Date Conflict Is Not Automatically Data Error**

```
promised_date  ≠  expected_arrival_date
```

**本身不一定是** `CONSISTENCY_CONFLICT` —— 它们可能本来就具有**不同 business semantic**。

**只有**当前 approved source-specific mapping **明确要求**它们满足某 consistency relation，
才能判断 conflict。**当前没有该 relation。**

因此**不得**：`dates differ → Data Quality Issue` 自动成立。

**`updated_at` Boundary**

**不得**使用 `updated_at` **替代** `effective_arrival_date`。

也**不得**建立 `latest updated record wins` ——
除非 future **Adapter Design** 明确批准 source-specific precedence。

`updated_at` 仍**只是** record update context。

**Status Boundary**

Inbound status（`OPEN` / `CONFIRMED` / `PARTIALLY_RECEIVED` / `CANCELLED` / `CLOSED` / `COMPLETED`）
与 **arrival-date mapping** 是**两个不同维度**。

**不得**：`CONFIRMED → use confirmed_date` ——
因为当前 Design **没有** approved `confirmed_date` field，也**没有**该 mapping rule。

**不得**从 status 推导 source-date precedence。

**`promised_date` / `expected_arrival_date` Boundary**

`VR-005` 中 `promised_date` 与 `expected_arrival_date` 仍是
**`SIMULATED` conceptual source attributes**。

它们**不是** POC canonical fields 的**强制 persisted representation**。

未来 Adapter **可以**：

- 使用其中之一
- 使用 ERP-specific field
- 使用明确批准的 deterministic source-specific rule

只要最终能够可靠产生 `effective_arrival_date`。

**Provenance Requirement**

每个 resolved `effective_arrival_date` **必须未来能够追溯**：

```
source inbound context
→ source date evidence
→ source-specific mapping basis
→ canonical effective_arrival_date
→ Snapshot Package
```

**但**：**physical provenance carrier 仍属 `§4.3` 后续设计**（**logical provenance carrier = `DESIGN RESOLVED`**，见 **§4.5.22 Option D Implementation Record**）。

**不得创建**：lineage DB / mapping table / JSON metadata /
`source_field_name` persisted field 等 **physical design**。

**Cross-Package Boundary**

**不得**：`Inbound from Package P1` 使用 `Package P2 的 arrival-date mapping evidence`
静默产生 `effective_arrival_date`。

必须继承：

```
Analysis Run → exactly one accepted Snapshot Package
```

与 **`PROVENANCE_MISMATCH`** 边界。

**Adapter Boundary**

具体 `source value / field → effective_arrival_date` 属于
**future source-specific Adapter mapping**。

**但是**：**canonical semantic contract 属于当前 Design**。
Adapter **不得**自行重新定义 `effective_arrival_date` 是什么意思。

**Canonical Model / Business Rule Impact**

```
BR-INBOUND-001 semantic                 = 未修改
effective_arrival_date <= required_date = 未修改
missing / invalid → DATA_INCOMPLETE     = 未修改
Inbound canonical grain                 = 未修改
```

本 Review **未**发现需要修改 `§2.6` / `§4.1.4 E` / `§4.2.6` 的理由。

**No Technology / Implementation**

本 Review **未创建**：source field precedence code、Adapter、mapping table、schema、SQL、JSON、
API、fallback algorithm、source enum、date confidence score、test、fixture、ADR。

**未选择技术。**

**Status（PR #34 Review 时点）**

```
effective_arrival_date source mapping = DESIGN PENDING    ← 本 Review 不改变
unresolved count                      = 仍为 6
```

**Human Decision Required**

请 Human 决定：

1. 是否**拒绝**建立**全局 source-field precedence**
2. 是否采用 **Option D**（source-specific mapping → canonical `effective_arrival_date`）
3. 是否确认：每个 applicable inbound context **必须**解析成
   **exactly one `effective_arrival_date`** 或 **unresolved**
4. 是否确认：`promised_date ≠ expected_arrival_date` **本身不构成** Data Quality Issue
5. 是否授权后续 **`§4.2` / `§4.4` / `§4.5`** 必要的最小 consistency synchronization

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 以下为 Human 对上述 5 项的**正式回复**（本 Review 由 **PR #34** 提交）。
> 本节**只记录决定**；**未**执行 `§4.2` / `§4.4` / `§4.5` 的 semantic synchronization。

| # | 决定项 | Human Decision |
| --- | --- | --- |
| 1 | 是否建立 **global source-field precedence** | **NOT ADOPTED** |
| 2 | 是否采用 **Option D**（source-specific mapping → canonical `effective_arrival_date`） | **APPROVED** |
| 3 | **Exactly-one-or-unresolved** contract | **APPROVED** |
| 4 | `promised_date ≠ expected_arrival_date` 是否自动构成 Data Quality Issue | **不构成**（APPROVED） |
| 5 | `§4.2` / `§4.4` / `§4.5` 最小 consistency synchronization | **AUTHORIZED** |

**决定 1 —— Global Source-Field Precedence = NOT ADOPTED**

当前 POC **不建立**全局规则，例如：

- `promised_date` always wins
- `expected_arrival_date` always wins
- `expected` fallback `promised`
- `promised` fallback `expected`
- earliest wins
- latest wins
- newest `updated_at` wins

原因：当前 Human-approved `SIMULATED` evidence **没有提供**这些 precedence 的**业务依据**。

**不得**为了让 `Effective Inbound` 可运行而**发明 global precedence**。

**决定 2 —— Option D = APPROVED**

```
source-specific arrival-date evidence
        ↓
explicit deterministic mapping
        ↓
canonical effective_arrival_date
```

该 **mapping contract** 是当前 POC 的**正式设计方向**。

目标是统一 **canonical business semantic**，**不是** **source field name**。

不同 source system **可以**采用不同 source-specific mapping，
但**必须** `explicit` / `deterministic` / `traceable` ——
**不得**由 LLM 或 runtime business rule **临时选择**。

**决定 3 —— Exactly-One Resolution Contract = APPROVED**

对于每一个需要参与 `BR-INBOUND-001` 判断的 applicable inbound context，
**进入 deterministic business rule 之前**必须得到：

```
exactly one reliably resolved effective_arrival_date
            或
unresolved
```

**不得**让 `BR-INBOUND-001` 同时面对 `promised_date` / `expected_arrival_date` / `ETA`
或**多个候选日期**，然后**自行决定**。

**必须保持：**

```
source semantic resolution 发生在 deterministic business rule 之前
```

**决定 4 —— `promised_date ≠ expected_arrival_date` 本身不构成 Data Quality Issue**

正式确认：两个日期值**不同**，**不自动**意味着：

- `CONSISTENCY_CONFLICT`
- Data Quality Issue
- invalid evidence

因为当前 Design **没有批准**「两者必须相等」或「必须满足某个先后关系」。

**只有**未来某个 **approved source-specific mapping contract** 明确要求某种 consistency relation，
且该 relation **被违反**时，才能形成对应 Validation Issue。

**决定 5 —— Minimal Consistency Synchronization = AUTHORIZED（授权边界）**

后续专门的 **Design Change Task** 被授权对 `§4.2` / `§4.4` / `§4.5` 执行必要的最小同步。

**授权范围仅包括：**

- `effective_arrival_date` **source semantic / mapping status**
- **source-specific mapping contract**
- **exactly-one-or-unresolved boundary**
- **missing mapped value** vs **unresolved semantic mapping**
- **multiple source dates** 的处理边界
- **provenance / cross-package boundary**
- **stale `DESIGN PENDING` wording synchronization**

**不得借此**：

- 修改 `BR-INBOUND-001`
- 修改 `effective_arrival_date` business semantic
- 创建 **global source-field precedence**
- 创建 **fallback algorithm**
- 创建 `ArrivalDateSourceType`
- 创建 `ArrivalDatePriority`
- 创建 `ArrivalConfidence`
- 创建新的 **Business Status**
- 创建新的 **Validation Reason**
- 修改 **Inbound grain**
- 选择**真实 ERP field**

**继续确认的边界（详见上方 Review Finding）**

**Missing vs Unresolved Boundary：**

| # | 情形 | 处理 |
| --- | --- | --- |
| **A** | approved mapping 已存在，但 mapped source value **missing** | `FIELD_VALUE` / `MISSING` 或既有适用 Validation Reason |
| **B** | source value **存在**，但**无法可靠判断**如何映射成 `effective_arrival_date` | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED`；capability 需要该 inbound 时 → **`DATA_INCOMPLETE`** |

**不得**把 A / B 混为一类。

**Invalid Value Boundary** —— approved mapping 已存在，但 mapped source value
**无法解析成合法 `DATE`** → `FIELD_VALUE` / `INVALID_TYPE`；
**不得** fallback 到另一个**未经批准**的 source date。

**Adapter Responsibility Boundary** —— 未来 Adapter **可以**定义
`Source A: field X → effective_arrival_date`、`Source B: field Y → effective_arrival_date`，
或 **source-specific approved precedence → one canonical `effective_arrival_date`**；

**但 Adapter 不得重新定义** `effective_arrival_date` 的 **canonical semantic** ——
canonical semantic **继续由 `BR-INBOUND-001` 定义**。

**执行状态（PR #34 时点）**

```
Human Decision                 = RECORDED
Option D                       = APPROVED
Semantic Synchronization       = NOT YET IMPLEMENTED
effective_arrival_date mapping = DESIGN PENDING
unresolved count               = 仍为 6
```

**本 PR 不实施** `§4.2` / `§4.4` / `§4.5` 的正式 semantic synchronization。

**PR #34 当时**：`effective_arrival_date` source mapping **保持 `DESIGN PENDING`**，
unresolved count 当时**仍为 6**。

> 以上为**历史记录**。后续 **Human-authorized Option D Implementation** 已实施并变更该状态 ——
> 见下方 **Option D Implementation Record**。

**Option D Implementation Record（Human-authorized Design Change）**

**Human Authorization Source**

```
PR #34 Human Decision
  → Global source-field precedence          = NOT ADOPTED
  → Option D                                = APPROVED
  → exactly-one-or-unresolved               = APPROVED
  → date difference ≠ automatic DQ Issue    = APPROVED
  → minimal synchronization（§4.2/§4.4/§4.5） = AUTHORIZED
```

**Implementation Result**

```
source-specific arrival-date evidence
        ↓
explicit deterministic mapping
        ↓
exactly one canonical effective_arrival_date
        或
unresolved
```

该 contract 统一的是 **canonical business semantic**，**不是** **source field name**。

**Global Source-Field Precedence = `NOT ADOPTED`（正式保持）**

**不得**建立以下任何一项：

- `promised_date` always wins
- `expected_arrival_date` always wins
- `expected` fallback `promised`
- `promised` fallback `expected`
- earliest wins
- latest wins
- newest `updated_at` wins
- `min` / `max` / `average`
- LLM choose

**这些均不进入 canonical mapping contract。**

**Source-Specific Mapping Semantics**

不同 source system **可以**有不同 mapping，例如（**conceptual**）：

```
Source A: field X → canonical effective_arrival_date
Source B: field Y → canonical effective_arrival_date
Source C: approved source-specific deterministic rule → canonical effective_arrival_date
```

**具体 X / Y / precedence 由未来 Adapter / source-specific mapping 提供。**
**本 Task 不定义**任何真实 ERP field / SRM field / column / JSON path / source vocabulary。

**Exactly-One-or-Unresolved Contract（正式落地）**

对每一个参与 `BR-INBOUND-001` 的 applicable inbound context，
**进入 deterministic business rule 之前**必须已经得到：

```
exactly one reliably resolved effective_arrival_date
    或
unresolved
```

**不得**让 `BR-INBOUND-001` 同时面对 `promised_date` / `expected_arrival_date` / `ETA` /
`planned_delivery_date` 或**多个 candidate dates** 然后自行选一个。

**正式保持：** `source semantic resolution 发生在 deterministic business rule 之前`。

**Multiple Candidate Dates**

多个 candidate dates 存在且不同时：

- **如果**存在 approved source-specific mapping → 按该 mapping 得到 **exactly one** `effective_arrival_date`
- **如果**不存在 → **不得选择任何一个**；结果 = **mapping unresolved**；
  Validation：`SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED`；
  若当前 capability 需要该 inbound → **`DATA_INCOMPLETE`**

**Date Difference Boundary（正式落实 Human Decision）**

```
promised_date  ≠  expected_arrival_date
```

**本身不是** `CONSISTENCY_CONFLICT`、**不是** Data Quality Issue、**也不是** invalid evidence ——
因为两者可能具有**不同 business semantic**。

**只有**未来某个 approved source-specific mapping contract 明确声明某 consistency relation，
且该 relation **被违反**时，才可以产生对应 Validation Issue。

**Single Candidate Boundary**

即使 source record **只有一个** candidate date 有值，**也不得**因为「只有它存在」
就自动把它当成 `effective_arrival_date` —— **必须先存在 approved source-specific semantic mapping**。

```
single candidate  ≠  automatically canonical
```

**Missing vs Unresolved vs Invalid（正式区分）**

| # | Root condition | Validation Reason | Business consequence |
| --- | --- | --- | --- |
| **A** | mapping 已批准，但 mapped source value **不存在** | `FIELD_VALUE` / `MISSING`（或现有适用 Field Validation reason） | `DATA_INCOMPLETE` |
| **B** | source date evidence **存在**，但无法可靠确定如何映射到 `effective_arrival_date` | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE`（capability 需要时） |
| **C** | approved mapping 已确定，但 mapped value **无法解析为合法 `DATE`** | `FIELD_VALUE` / `INVALID_TYPE` | `DATA_INCOMPLETE` |

**不得**把 A / B / C 都写成 `effective_arrival_date missing`；
**不得**在 C 的情况下 fallback 到另一个**未经批准**的 candidate date；**不得创建**新 Validation Reason。

**Inbound Status Boundary（保持）**

`Inbound status` 与 `arrival-date mapping` **继续是两个独立维度**。**不得**：

- `CONFIRMED` → automatically use `confirmed_date`
- `OPEN` → automatically use `promised_date`
- `PARTIALLY_RECEIVED` → automatically use `expected_arrival_date`

**不得**由 status 推导 source-field precedence。

**`updated_at` Boundary（保持）**

```
updated_at  ≠  effective_arrival_date
```

**不得** `latest updated record wins`；**不得**把 `updated_at` 当作 canonical arrival date。
`updated_at` **只是** record-update context。

**Adapter Responsibility（正式定义）**

| 角色 | 负责 |
| --- | --- |
| **Adapter / source-specific mapping** | source semantic → canonical `effective_arrival_date` |
| **Canonical Design** | `effective_arrival_date` **是什么意思** |

```
Adapter MAY decide:  哪个 approved field / approved source-specific rule 产生 canonical date
Adapter MUST NOT:    重新定义 effective_arrival_date 在业务上代表什么
```

后者仍由 **`BR-INBOUND-001`** 定义。

**Provenance / Cross-Package（保持）**

追溯链保持：

```
source inbound context
→ source date evidence
→ source-specific mapping basis
→ canonical effective_arrival_date
→ Snapshot Package
```

**但 physical provenance carrier 仍属 `§4.3` 后续设计**（**logical provenance carrier = `DESIGN RESOLVED`**，见 **§4.5.22 Option D Implementation Record**）；**不得创建** lineage DB / mapping table /
JSON metadata / `source_field_name` persisted field / physical lineage schema。

跨 Package 继续继承 **`PROVENANCE_MISMATCH`**；**不得创建新 reason**。

**§4.2 / §4.4 / §4.5 Synchronization Result**

- `§4.2.6` —— `effective_arrival_date` 的 source mapping / mapping contract 已同步；
  root-condition distinction（A / B / C）已补入
- `§4.2.16` —— stale open item **已移除**
- `§4.3.17` / `§4.4.41` / `§4.4.76` / `§4.4.99` / `§4.4` closure 表 —— 已同步
- `§4.4.49` —— date boundary 扩展为「exactly-one-or-unresolved ＋ 三类 root condition ＋
  **Date Difference Boundary**」
- `§4.4.95` —— 新增 arrival-date semantic unresolved 示例，并明确
  「**没有 global source-field precedence**」**本身不是错误**，而是**正式设计选择**

**§4.1 的最小 status synchronization（已获额外授权）**

`§4.1 Canonical Data Model` 的 **entity grain / attributes / Inbound canonical model 均未修改**；
`effective_arrival_date` 的 **canonical semantic** 亦**未改变**。

**仅**对 `§4.1.12 Open Items` 中与 `effective_arrival_date` **相关的那一条**做了
**最小 consistency synchronization** —— 另经
**Human-authorized documentation/status alignment（PR #34 ／ PR #35）** 授权；
这**不是**新的 Business Decision，也**不是**重新打开 `§4.1 Canonical Data Model`。

同步后 `§4.1.12` 登记：**`effective_arrival_date` source mapping policy = `DESIGN RESOLVED`**，
并明确 **`DESIGN RESOLVED` ≠ real ERP field known ≠ Adapter implemented ≠ mapping tested**。

**Meaning of `DESIGN RESOLVED`**

`DESIGN RESOLVED` **只**表示 **canonical source-mapping contract 概念设计完成**，
**不表示**：

- real ERP field known
- source mapping configuration exists
- Adapter implemented
- source data validated
- mapping tested
- `Effective Inbound` implemented
- production-ready

**执行状态（本 Task 完成时点）**

```
Human Decision                 = RECORDED
Option D                       = IMPLEMENTED
effective_arrival_date mapping = DESIGN RESOLVED
unresolved count               = 6 → 5
Other Source-Semantic Mapping  = 仍 DESIGN PENDING
Master Data Mapping overall    = 仍 DESIGN PENDING
```

#### 4.5.22 Preserve Unresolved Items

以下未决项本轮**必须继续保持**（`Warehouse canonical role` **已由 §4.5.12 解析**、`BOM version / validity` **已由 §4.5.7 ／ §4.1.4 N 解析**、`sourcing_status` vocabulary **已由 §4.5.11 解析**、`effective_arrival_date` source mapping **已由 §4.5.21 解析**、allocation demand-window mapping **已由 §4.5.9 解析**、`loss_rate` owner / grain **已由 §4.5.22 Option E Implementation Record 解析**、`ApplicableMOQ` source **已由 §4.5.22 Option D Implementation Record 解析**、`provenance carrier` **已由 §4.5.22 Option D Implementation Record 解析**）：

| 未决项 | 状态 |
| --- | --- |
| `loss_rate` owner / grain | **`DESIGN RESOLVED`** —— owner = **`Requirement Calculation Context`**；resolution contract = **exactly one applicable `loss_rate` or `unresolved`**（**§4.5.22**） |
| Warehouse canonical role | **`DESIGN RESOLVED`** —— source / mapping / scope context（**§4.5.12**） |
| BOM version / validity | **`DESIGN RESOLVED`** —— requirement-scoped BOM applicability（**§4.5.7** ／ **§4.1.4 N**） |
| `sourcing_status` vocabulary | **`DESIGN RESOLVED`** —— source vocabulary = **`SOURCE-SPECIFIC`**；canonical eligibility mapping contract 见 **§4.5.11** |
| `effective_arrival_date` source mapping | **`DESIGN RESOLVED`** —— source mapping = **source-specific / Adapter-defined**；canonical mapping contract 见 **§4.5.21** |
| allocation demand-window mapping | **`DESIGN RESOLVED`** —— canonical allocation applicability mapping contract 见 **§4.5.9** |
| `ApplicableMOQ` source | **`DESIGN RESOLVED`** —— owner = **exact Procurement Recommendation Context**；source semantic role = **`SOURCE-SPECIFIC` purchasing-policy evidence**；resolution contract = **exactly one applicable `ApplicableMOQ` or `unresolved`**（**§4.5.22 Option D Implementation Record**）；physical carrier **仍 SOURCE-SPECIFIC / not yet defined** |
| provenance carrier | **`DESIGN RESOLVED`** —— **Layered Logical Provenance Contract**（**§4.5.22 Option D Implementation Record**）：`Snapshot Package Identity` + `Logical Dataset Role` + **`Stable Source Evidence Locator`** + `Mapping / Resolution Basis`（when applicable）+ `Analysis Run linkage`；physical carrier **仍属 §4.3 后续设计** |

> `BOM version / validity` 的 **Blocking Finding**（`Canonical Model Compatibility = INSUFFICIENT`）
> 已由 **Human-approved Option A ＋ Canonical Model Amendment** **RESOLVED**（见 **§4.5.7**）；
> 因此其状态已变更为 **`DESIGN RESOLVED`**，未决项数量 **8 → 7**。
>
> `sourcing_status` vocabulary 的 **Option B semantic synchronization 已实施**
> （见 **§4.5.11 Option B Implementation Record**）；
> 因此其状态已变更为 **`DESIGN RESOLVED`**，未决项数量 **7 → 6**。
>
> `effective_arrival_date` source mapping 的 **Option D semantic synchronization 已实施**
> （见 **§4.5.21 Option D Implementation Record**）；
> 因此其状态已变更为 **`DESIGN RESOLVED`**，未决项数量 **6 → 5**。
>
> `allocation demand-window mapping` 的 **Option B semantic synchronization 已实施**
> （见 **§4.5.9 Option B Implementation Record**）；
> 因此其状态已变更为 **`DESIGN RESOLVED`**，未决项数量 **5 → 4**。
>
> `required_quantity` semantic 的 **Human-authorized removal 已实施**
> （见 **§4.2.4** Human Decision Record ＋ **Required Quantity Removal Implementation Record**）；
> 该字段 **`REMOVED FROM CURRENT CANONICAL MODEL`**，因此**不再属于未决项**，
> 未决项数量 **4 → 3**。
>
> `loss_rate` owner / grain 的 **Option E semantic synchronization 已实施**
> （见下方 **Option E Implementation Record**）；
> owner = **exact Requirement Calculation Context**，
> resolution contract = **exactly one applicable `loss_rate` or `unresolved`**；
> 因此其状态已变更为 **`DESIGN RESOLVED`**，未决项数量 **3 → 2**。
>
> `ApplicableMOQ` source 的 **Option D semantic synchronization 已实施**
> （见下方 **Option D Implementation Record**）；
> owner = **exact Procurement Recommendation Context**，
> resolution contract = **exactly one applicable `ApplicableMOQ` or `unresolved`**；
> 因此其状态已变更为 **`DESIGN RESOLVED`**，未决项数量 **2 → 1**。
>
> `provenance carrier` 的 **Option D semantic synchronization 已实施**
> （见下方 **Option D Implementation Record**）；
> **Layered Logical Provenance Contract** 已落地，
> 因此其状态已变更为 **`DESIGN RESOLVED`**，未决项数量 **1 → 0**；
> `Other Source-Semantic Mapping` 随之成为 **`DESIGN RESOLVED`**。

本 Task **不以「Master Data Mapping」为名一次性消灭这些问题**。

**Historical Review Record —— PR #40（不得作为当前状态解读）**

> 以下 **`loss_rate` Canonical Owner / Grain Design Review（Review Finding）**、
> **Known Risks** 与 **Human Decision Record** 是 **PR #40** 时点的原始记录，
> **按当时时点原样保留**，以便追溯。
>
> 其中出现的 `loss_rate canonical owner / grain = UNKNOWN`、
> `Option E Implementation = NOT YET EXECUTED`、`unresolved count = 3`
> 等表述**均为 PR #40 时点状态**，**不得**被解读为当前状态。
>
> **Option E 已由后续 Human-authorized Design Change 实施** ——
> `loss_rate` canonical owner / grain 现为 **`DESIGN RESOLVED`**，
> unresolved count 现为 **2**（见下方 **Option E Implementation Record**）。

**loss_rate Canonical Owner / Grain Design Review（Review Finding）**

**Review Question**

本 Review **只解决一个问题**：

> 对于某一次 **`BR-REQUIREMENT-001` GrossRequirement calculation**，
> **哪一个 business context 拥有 / 决定 applicable `loss_rate`？**

**Evidence Boundary**

| 证据来源 | 是否定义 `loss_rate` source field / owner / grain / precedence |
| --- | --- |
| `FROZEN` Discovery Brief（`discovery-brief-v0.1.1.md`） | **否** |
| `FROZEN` Discovery Validation（`discovery-validation-v0.1.md`） | **否** |
| `§2.4`（`BR-REQUIREMENT-001`） | 只定义 semantic / formula / range / missing behavior，**未定义** owner / grain |
| `§4.1.12` Canonical Model Open Items | 明确登记 owner / grain = **`UNKNOWN`** |
| `§4.2.16` Open Semantic / Mapping Items | 明确登记 canonical owner / grain = **`UNKNOWN`** |
| `§4.4.15` / `§4.4.54` | 只要求「能可靠关联到当前计算上下文」，并**明确禁止**决定其来源 |

- Discovery Validation 明确将 **Scrap / Loss** 归入 **`VB-17` / `POC Design v0.2`**，
  而**不是** Discovery Data Readiness 已确认的 source field。
- 两份 `FROZEN` Discovery **没有**定义 `loss_rate` 的 source field / owner / grain / precedence。
- 因此**不得声称**真实 CY / ERP 中 `loss_rate` 一定属于 `Material` ／ `BOM` ／
  `BOM Component` ／ `Plant-Material` ／ `Production Order` ／ `Routing` ／ `Work Center` ／
  Policy table 中的**任何一个**。
- **行业常见做法只能作为 option reasoning，不能作为项目事实。**

**Existing Calculation Context**

`§2.4.2` 规定 Gross Requirement calculation **至少对齐** `plant_id` + `material_code` + `required_date`，
且必须能够**追溯到** `Production Requirement` + `BOM relationship`。

当前实际 calculation chain：

```
Production Requirement（parent / production material context）
        ↓
Applicable BOM Relationship（requirement-scoped；applicability anchor = required_date）
        ↓
Component Material
        ↓
BOMComponentQty
        ↓
BaseRequirement = ProductionQty × BOMComponentQty
        ↓
applicable loss_rate          ← 本 Review 的唯一问题所在
        ↓
GrossRequirement = BaseRequirement / (1 - loss_rate)
```

**Review 必须回答：** `loss_rate` 是在**哪一层**被可靠解析到这个 calculation？

现状：

```
loss_rate canonical semantic          = DESIGN RESOLVED
loss_rate formula / range / missing   = DESIGN RESOLVED
loss_rate canonical owner / grain     = UNKNOWN
```

因此当前只能要求「**必须能够可靠关联到当前计算上下文**」，
同时**明确禁止**决定它来自哪个 Entity / Dataset / Source Field ——
即 **requirement 存在，但无法判定它是否已被满足**。

**Critical Scenario（必须回答 —— 当前 Design 无法唯一回答）**

```
Plant-A

Production Requirement R1:
  parent MAT-A
  required_date = 2026-10-10

Applicable BOM:
  MAT-B × 2
  MAT-C × 1

Source evidence:
  loss evidence X = 0.05
  loss evidence Y = 0.02
```

必须回答：X / Y 到底对应 `MAT-A`？`MAT-B` / `MAT-C`？`Plant-A` + component？
`R1`？某一条 BOM relationship？某个 configuration context？

当前 evidence **没有给答案**。没有 owner / grain 就**无法可靠决定**
`MAT-B` 用 5% 还是 2% → `GrossRequirement` **不可可靠执行** → **`DATA_INCOMPLETE`**。

**不得**：`first wins` ／ `latest wins` ／ `max` ／ `min` ／ `average` ／
`copy previous` ／ `LLM choose`。

**Cross-Requirement Scenario**

```
R1: Plant-A / MAT-A / required_date = 2026-10-10 / BOM relationship: MAT-B × 2
R2: Plant-A / MAT-A / required_date = 2026-11-10 / BOM relationship: MAT-B × 3
```

必须回答：是否允许 `R1 loss_rate = 0.02`、`R2 loss_rate = 0.05`？

当前 evidence **没有给答案**。

关键检查：`§4.1.4 N` 已明确 **同一 `Plant` + `Parent` + `Component` 跨 `required_date`
不得视作同一个 BOM Component grain** —— 即 BOM applicability **已经是 requirement-scoped**。

若 owner 只定义为 `Material MAT-B`，则**强制** R1 与 R2 共享同一个 `loss_rate`。
这种共享**没有 evidence 支持**，因此**不得自动采用**；
反之也**不得**自动声明两者必须不同（见 **Time Semantics**）。

**Multi-Parent Scenario**

```
MAT-B 同时是 MAT-A 与 MAT-X 的 component
```

必须回答：是否允许

```
MAT-A → MAT-B   loss_rate = 0.02
MAT-X → MAT-B   loss_rate = 0.06
```

若 owner 只定义为 `Material`，则二者**不能区分** —— 会发生 **information loss**，
且该损失**不可被 Validation 检测**（两个 requirement 各自「有」一个 `loss_rate`，
表面上都合法，因此不会被 `SEMANTIC_UNRESOLVED` 捕获）。

必须评估这种 information loss 是否可接受。
**不得凭行业经验回答。**

**Canonical Owner ≠ Physical Carrier（必须显式区分）**

```
Canonical Owner / Applicability Grain   ≠   Physical Source Owner
Canonical Grain                          ≠   Database Primary Key
```

- 这里的 **owner** **不是**「哪个数据库表拥有该字段」，
  而是「**哪一个 business context 决定当前 `loss_rate` 的适用范围**」。
- 未来 `loss_rate` 可能物理来源于 BOM export ／ Material master ／ planning configuration ／
  custom ERP table ／ controlled configuration file ——
  这些属于 **carrier / source representation**。
- 本 Review **只定义 canonical applicability semantics**；
  **不得因为 carrier 未知就认为 owner 无法设计**。
- **provenance carrier 仍是独立 unresolved item**，本 Review **不得顺手解决**
  （见 **§4.5.22** ／ **§4.5.24**）。

**Option Review**

**Option 0 —— Keep owner / grain `UNKNOWN`**

- 保持：`loss_rate` 无法可靠关联 → **`DATA_INCOMPLETE`**。
- 评估：**正确但非设计终点**。它是**安全 fallback**，长期会**阻塞 `GrossRequirement`**，
  使 `BR-REQUIREMENT-001` 在当前 POC 中**永远不能形成可靠 result**。
- 结论：**安全但不足**；只有当前述缺口**无法在现有 canonical model 内表达**时才应保持。

**Option A —— Material-level loss_rate**

- grain：`material_code`，或 `plant_id` + `material_code`。
- 优点：**简单**。
- 必须检查它是否能够区分：

| 需要区分的情形 | Option A 能否区分 |
| --- | --- |
| 同一 component 在不同 Parent 下 | **不能** |
| 不同 BOM relationship（`MAT-B × 2` vs `MAT-B × 3`） | **不能** |
| 不同 `required_date` | **不能** |
| 不同 Plant | 仅当采用 `plant_id` + `material_code` 时**能** |

- 结论：**无法区分** → 会把同一 `loss_rate` **silent reuse** 到语义上不同的
  calculation context。没有 evidence 支持 → **不得采用**。

**Option B —— Plant-Material loss_rate**

- grain：`plant_id` + component `material_code`。
- 比 Option A **多了 Plant 维度**，但**仍无法区分**：不同 Parent、
  不同 Production Requirement、不同 BOM applicability context。
- 结论：**仍不足**。**不得因为它「比较常见」就采用。**

**Option C —— BOM Relationship-level loss_rate**

- conceptually：`loss_rate` belongs to **applicable BOM Component relationship**。
- grain：`Production Requirement context` + component `material_code`
  —— 与 `BOMComponentQty` **同一 applicability context**。
- 优点：同一 component 可以在不同 Parent / requirement context 拥有不同 `loss_rate`，
  恰好消除 Option A / B 的 information loss。
- **但**：若把它实现为 **`§4.1.4 N` BOM Component 的 canonical persisted attribute**，
  则这是 **substantive Canonical Model Change**（修改 `§4.1.4 N` 的 attributes / ownership），
  必须 **Human Approval**。
  并且 `§4.1.4 N` 在 **PR #30** 的授权范围中已明确**未**改动 `loss_rate` owner / grain。
- 结论：**语义方向正确，但按「BOM Component attribute」实现需要 Canonical Model Amendment
  → 记为 `INSUFFICIENT`**。

**Option D —— Production Requirement-level loss_rate**

- grain：`plant_id` + parent / requirement `material_code` + `required_date`。
- 优点：与 `§4.1.4 N` 的 **Production Requirement context** **完全对齐**，时间语义天然正确。
- **但**：一个 Production Requirement 有多个 components（`MAT-B` ／ `MAT-C` ／ `MAT-D`），
  该 grain **意味着三者必须共用同一个 `loss_rate`**。
- 现有 Design / evidence **没有**支持「同一 requirement 下所有 component 共用同一 loss rate」。
- 结论：**Option D 无法表达 component-specific loss** —— 本 Review **明确指出**这一点，
  因此它**不足以**作为最终 owner。

**Option E —— Calculation-Context Configuration（重点评估）**

不把 `loss_rate` 强行定义成 Material attribute ／ BOM Component persisted attribute ／
Production Requirement attribute，而是定义：

```
loss_rate
= required configuration evidence
  resolved for an exact Requirement Calculation Context
```

conceptual grain（**至少**能够区分）：

```
plant_id
+ parent / requirement material_code
+ required_date
+ component material_code
```

解析契约：

```
source-specific loss evidence
        ↓
explicit deterministic mapping
        ↓
exactly one applicable canonical loss_rate
      for this GrossRequirement calculation
```

**是否能够在不创建新 canonical entity、不新增 persisted field 的前提下解决 owner / grain？**

**能** —— 理由：

1. 上述所需 grain **已经存在**：`§4.1.4 N` 的 BOM Component canonical grain 就是
   `Production Requirement context`（= `plant_id` + parent / requirement `material_code`
   + `required_date`）`+ component material_code`。
2. `§4.1.4 N` 已明确该 grain **不是** physical composite key / database primary key，
   而是表达 **grain** ——「哪个 requirement context 下的哪一条 component relationship」——
   与 Option E 所需的 **conceptual applicability context** 语义**一致**。
3. 因此 Option E **只需声明**：`loss_rate` 是**在该 context 上被解析出来的 required
   configuration evidence**，而**不是**任何 entity 的 persisted attribute ——
   这属于 **applicability / resolution contract** 层面的声明，
   **不改变**任何 entity 的 attributes 列表、**不新增** entity、**不新增** identity component。

- 结论：**推荐方向（Option E，待 Human Decision）。**

**Requirement Calculation Context（conceptual）**

若 Option E 获 Human Approval，需要正式定义的只是**一个 conceptual context**，
**不是**新的 canonical entity：

```
Requirement Calculation Context
= Production Requirement（plant_id + parent / requirement material_code + required_date）
+ applicable BOM relationship
+ component material_code
```

- 它**由既有 canonical fields 组合表达**，**不引入**新的 identity 字段。
- **不得创建** `requirement_calculation_id` ／ `loss_policy_id` ／ `scrap_policy_id`
  等 physical / canonical ID。
- **不得**把它实现为新的 entity、table、schema 或 registry。
- 它的**唯一**用途是表达：`loss_rate` 的 **applicability grain**。

**Canonical Model Compatibility Result**

推荐方向 **Option E** 的判定：

```
Canonical Model Compatibility = COMPATIBLE
```

依据（**不新增**任何 field / entity / identity component）：

| 需要表达的内容 | 现有 Canonical Model 是否已能表达 |
| --- | --- |
| `plant_id` | **已有**（`§4.1.4 C` ／ `§4.1.4 N`） |
| parent / requirement material | **已有**（`§4.1.4 C` ＋ `§4.1.4 N` 的 contextual role clarification） |
| `required_date` | **已有**（`§4.1.4 C` ＋ `§4.1.4 N` 的 applicability anchor） |
| component material | **已有**（`§4.1.4 N`） |
| 「哪个 requirement context 下的哪一条 component relationship」 | **已有**（`§4.1.4 N` grain） |

**必须明确 —— 判为 `COMPATIBLE` 的唯一前提：**
Option E 的 **resolution-contract** 形式，即 `loss_rate` 作为 **required configuration evidence**
被解析到该 context，**不**成为任何 entity 的 attribute。

**同时必须明确（不得模糊）：**

- 若 Human 选择 **Option C 的 attribute 实现形式**
  （把 `loss_rate` 加入 `§4.1.4 N` BOM Component 的 attributes / ownership），
  则 **`Canonical Model Compatibility = INSUFFICIENT`**，
  必须走 **Human-approved Canonical Model Amendment**（与 PR #30 同类）。
- **Option A ／ B ／ D** 在**表达能力**上不足（无法区分 Multi-Parent / Cross-Requirement）
  或**过度合并**（Option D 强制同一 requirement 下所有 component 共用），
  因此**不推荐**；但它们的失败属于**表达能力不足**，
  **不构成** canonical model 冲突。

**Exactly-One-or-Unresolved Contract（评估）**

建议采用，且**仅作为 canonical resolution contract**：

```
对每一个 GrossRequirement calculation context：
  必须解析出 exactly one applicable canonical loss_rate
  或
  unresolved
```

- 好处：`BR-REQUIREMENT-001` **不必**面对多个 candidate `loss_rate` 再临时选择 ——
  这与 **§4.5.21** 已批准的 **Exactly-One-or-Unresolved Contract** **同构**。
- **这只是 canonical resolution contract**：它**不**定义 precedence、
  **不**定义 source field、**不**定义 carrier、**不**创建 ID。
- 若无法解析出唯一值 → `GrossRequirement` = **`DATA_INCOMPLETE`**。

**Relationship to `BOMComponentQty`（必须明确）**

```
BOMComponentQty = 净用量系数
loss_rate       = Gross-up loss configuration
```

- 两者**用途不同**，**不得**相互替代或合并。
- 两者作用于**同一个** `Production Requirement` + component calculation。
- 本 Review 判断：**`loss_rate` applicability 必须与 applicable BOM relationship 一起被解析**。
  **理由：** `loss_rate` 的放大对象是 `BaseRequirement = ProductionQty × BOMComponentQty`，
  而 `BOMComponentQty` **只**在其所属 **Production Requirement context** 中具有 canonical meaning
  （`§4.1.4 N`）。若 `loss_rate` 在同一 calculation 中不遵循同一 context，
  就会对**同一个 `BaseRequirement`** 应用**来自不同 context** 的放大系数 ——
  这在语义上**不可辩护**。
- **但**：这**不**意味着 `loss_rate` 成为 `BOMComponentQty` 的属性 ——
  **不得自动把 `loss_rate` 变成 BOM Component 的 attribute，除非 Human 后续批准**
  （见 Option C 的 `INSUFFICIENT` 判定）。

**Time Semantics**

- 当前 calculation **明确存在** `required_date`，且 BOM applicability **已 requirement-scoped**
  （`§4.1.4 N`）。
- 若两个 `required_date` 可能使用**不同 loss configuration**，
  Option E 的 grain（含 `required_date`）**能够表达**；Option A ／ B **不能**。
- 当前**没有 evidence** 证明 `loss_rate` 永久固定 →
  **不得自动声明 `loss_rate` timeless**。
- 同样**不得自动声明**每个 `required_date` 都不同 →
  **不得**推断「按日期分裂」是业务事实。
- 结论：**source-specific applicability mapping 更安全** ——
  模型只要求「对当前 context 解析出 exactly one」，
  **不预设**时间维度上的相同或不同。

**Multiple Candidate Loss Evidence Boundary**

若同一 calculation context 出现多个 candidate `loss_rate`（例如 `0.02` ／ `0.05`），
且**没有 approved precedence**：

**不得**：`max` ／ `min` ／ `average` ／ `latest wins` ／ `first wins` ／ `most specific wins`。

处理：**`SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED`** →
`GrossRequirement` = **`DATA_INCOMPLETE`**。

> **不得新增** Validation Reason —— 只使用既有 **11 个 canonical reason** 之一（`§4.4.81`）。

**Missing vs Unresolved vs Invalid（必须区分）**

| 情形 | 判定 | 结果 |
| --- | --- | --- |
| **A** applicable owner / grain 已可靠解析，但 **value missing** | `FIELD_VALUE` ／ `MISSING` | `DATA_INCOMPLETE` |
| **B** `loss_rate` evidence 存在，但**无法可靠判断哪个适用于当前 calculation context** | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE` |
| **C** applicable `loss_rate` 已解析，但 `loss_rate < 0` 或 `loss_rate >= 1` | `FIELD_VALUE` ／ 既有 invalid / range reason | `DATA_INCOMPLETE` |

**不得**把三者都叫 `loss_rate missing`。

**Zero Boundary（保持）**

```
loss_rate = 0
```

继续是**合法显式配置**。

**不得**：`0 → missing`、`0 → fallback`、`0 → use another record`。

**No Precedence Invention**

本 Review **不定义**：

- BOM-level wins Material-level
- Material-level wins Plant-level
- most specific wins
- latest configuration wins
- requirement-level wins default
- Plant-specific overrides global

除非现有 approved evidence 已经支持 —— 当前**没有**。

**Option E 的重点是**「**mapping 必须最终产生 exactly one applicable `loss_rate`**」，
而**不是**「本 Review 发明 precedence」。

**Status（本 Review 时点）**

```
loss_rate canonical semantic          = DESIGN RESOLVED   ← 未变
loss_rate formula / range / missing   = DESIGN RESOLVED   ← 未变
loss_rate canonical owner / grain     = UNKNOWN           ← 未变
unresolved count                      = 3                 ← 未变
Other Source-Semantic Mapping         = DESIGN PENDING    ← 未变
```

本 Review **不**修改 `§2.4`，**不**修改 `§4.1` canonical model，
**不**实施任何 Option，**不**减少 unresolved count。

**Human Decision Required**

1. 是否接受 **Canonical Model Compatibility = `COMPATIBLE`**
   （按 Option E 的 **resolution-contract** 形式）？
2. 是否接受 **canonical owner** 定义：
   `loss_rate` **belongs to / is resolved for** an exact **Requirement Calculation Context**？
3. 是否接受 **applicability grain** **至少**区分：
   `plant_id` ／ parent / requirement `material_code` ／ `required_date` ／ component `material_code`？
4. 是否接受 **exactly one applicable `loss_rate` or `unresolved`**
   作为 canonical resolution contract？
5. 是否确认 **owner / applicability grain ≠ physical carrier / source table**？
6. 是否授权后续 **`§4.1` ／ `§4.2` ／ `§4.4` ／ `§4.5` 最小 consistency synchronization**？

**若 Human 选择 Option C 的 attribute 实现形式**，则还需额外给出：
**Blocking Finding** ＋ **Minimal Canonical Model Change Options** ＋ **trade-offs** ＋
**Human Approval Required**（本 Review 当前**不**推荐该形式）。

**Known Risks（本 Review 识别，未消除）**

| # | Risk | 说明 | 当前状态 |
| --- | --- | --- | --- |
| 1 | **适用性信息丢失不可检测** | 若 owner 退化为 `Material`-level，同一 component 在不同 Parent / requirement context 下的不同 `loss_rate` 会被 **silent reuse**；两个 calculation 各自「有」一个 `loss_rate`，表面上都合法，因此**不会**被 `SEMANTIC_UNRESOLVED` 捕获 | **未消除** —— 只能靠 applicability grain 承载 Parent / requirement context |
| 2 | **Carrier 未知** | 真实 physical carrier（BOM export ／ Material master ／ planning configuration ／ ERP-specific configuration ／ controlled configuration file ／ other approved source）**仍未知** | **未消除** —— `provenance carrier` 仍为独立 **`DESIGN PENDING`** |
| 3 | **时间维度不可预设** | 无 evidence 证明 `loss_rate` 永久固定，也无 evidence 证明每个 `required_date` 都不同 | **未消除** —— 模型只要求「每个 context 独立解析 exactly one or unresolved」，**不预设**相同或不同 |
| 4 | **Source evidence 可能需要额外维度** | 未来 source-specific evidence 可能需要更多维度才能唯一解析 | **未消除** —— `Adapter` ／ `mapping` **必须保留足够 evidence**，**不得 silently drop** |
| 5 | **Attribute 形式会使 `COMPATIBLE` 失效** | 若改为把 `loss_rate` 加入 `§4.1.4 N` BOM Component attributes（或其他 canonical entity）作为 persisted attribute | **已设边界** —— 该变化**必须重新进入** **Canonical Model Compatibility Review** ＋ **Human-approved Canonical Model Amendment** |
| 6 | **无 precedence** | 无 approved precedence 时，多 candidate 只能解析为 `unresolved` | **已设边界** —— 未来如需 precedence，**必须**另有新的 **Human-approved Design Decision** |
| 7 | **`Other Source-Semantic Mapping` 仍未闭合** | `loss_rate` 只是该层其中一个子项，本层整体仍 `DESIGN PENDING` | **未消除** —— 本 PR **未**减少 unresolved count |

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 本节是对**上方 Review Finding** 的 **Human Decision**。
> 上方 Review Finding 中的 `待 Human Decision` ／ `Human Decision Required` 表述
> **已在本节获得答案**；未实施部分见本节末 **执行状态**。
>
> 上方 **Evidence Boundary** ／ **Critical Scenarios** ／ **Option Review** ／
> **Canonical Owner ≠ Physical Carrier** ／ **Canonical Model Compatibility Result** ／
> **Known Risks** **全部保留，未删除、未改写**。

**决定 1 —— Canonical Model Compatibility = `COMPATIBLE`（ACCEPTED，附严格限定）**

接受：

```
Canonical Model Compatibility = COMPATIBLE
```

**该结论严格限定于：**

```
Option E
= Calculation-Context Configuration
+ resolution-contract implementation form
```

即：`loss_rate` **不是**新增到任何 canonical entity 中的 **persisted attribute**，
而是 **required configuration evidence** 针对一个明确的 **Requirement Calculation Context**
被**可靠解析**。

**若未来方案改变为**：将 `loss_rate` 直接加入 `§4.1.4 N` BOM Component attributes
或其他 canonical entity 作为 **persisted attribute** ——
则当前 **`COMPATIBLE`** 结论**不再适用**，
该变化**必须重新进入**：

```
Canonical Model Compatibility Review
        +
Human-approved Canonical Model Amendment
```

**决定 2 —— Option E = APPROVED**

**决定 3 —— Canonical Owner Definition = CONFIRMED**

正式批准 `loss_rate` canonical owner 应理解为：

```
loss_rate is resolved for
an exact Requirement Calculation Context
```

此处的 **owner** 表示「**哪一个 business context 决定该 `loss_rate` 的适用范围**」，
**不表示**：

- 哪个数据库表拥有字段
- 哪个 ERP module 拥有字段
- 哪个 Dataset 物理保存字段
- 哪个 API object 保存字段

因此：

```
Canonical Owner  ≠  Physical Source Owner
```

**决定 4 —— Requirement Calculation Context = ADOPTED（conceptual）**

正式采用 conceptual **`Requirement Calculation Context`**，
其 applicability grain **必须至少能够区分**：

```
plant_id
+ parent / requirement material
+ required_date
+ component material
```

同时**必须能够可靠关联到** the applicable BOM relationship：

```
Production Requirement
        +
Applicable BOM Relationship
        +
Component Material
        ↓
Requirement Calculation Context
```

**不得创建** `requirement_calculation_id` ／ `loss_policy_id` ／ `scrap_policy_id`
等新 canonical / physical ID。

**决定 5 —— Applicability Grain Boundary = CONFIRMED**

上述 `plant_id` + parent material + `required_date` + component material 是：

```
canonical applicability distinction
```

**不是** database primary key ／ physical schema ／ source table key。

- **不得**因本 Human Decision 创建新的 **persisted grain object**。
- 未来 source-specific evidence 若**需要额外维度**才能唯一解析：**不得 silently drop** ——
  `Adapter` ／ `mapping` **必须保留足够 evidence** 以可靠解析到当前 `Requirement Calculation Context`。

**决定 6 —— Exactly-One-or-Unresolved Contract = APPROVED**

对于每一个 `GrossRequirement` calculation context，在进入 **`BR-REQUIREMENT-001`**
确定性计算**之前**，**必须得到**：

```
exactly one applicable canonical loss_rate
或
unresolved
```

**不得**让 `BR-REQUIREMENT-001` 面对多个 candidate `loss_rate` 后**自行选择**。

**不得**：`first wins` ／ `latest wins` ／ `max` ／ `min` ／ `average` ／
`most specific wins` ／ `copy previous` ／ `LLM choose` ——
**除非未来另有 Human-approved precedence rule**。

**决定 7 —— Resolved `loss_rate` Semantics = UNCHANGED（CONFIRMED）**

一旦 **exactly one applicable `loss_rate`** 被可靠解析，**继续使用**现有 Human-approved：

```
0 <= loss_rate < 1
GrossRequirement = BaseRequirement / (1 - loss_rate)
```

**不得修改公式。** **`loss_rate = 0` 继续是合法显式配置。**

**决定 8 —— Missing ／ Unresolved ／ Invalid = 三类保持分离（CONFIRMED）**

| 情形 | 判定 | 结果 |
| --- | --- | --- |
| **A** applicability context 已可靠解析，但 required `loss_rate` value **missing** | `FIELD_VALUE` ／ `MISSING` | `DATA_INCOMPLETE` |
| **B** `loss_rate` evidence 存在，但**无法可靠判断哪一个适用于当前 Requirement Calculation Context** | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE` |
| **C** applicable `loss_rate` 已可靠解析，但 `loss_rate < 0` 或 `loss_rate >= 1` | existing `FIELD_VALUE` ／ range-invalid handling | `DATA_INCOMPLETE` |

**不得**把三者统一叫 `loss_rate missing`。

**决定 9 —— Owner vs Carrier = CONFIRMED（carrier 仍 OPEN）**

正式确认：

```
canonical owner / applicability grain  ≠  physical carrier / source table
```

未来 physical carrier 可能来自：BOM export ／ Material master ／ planning configuration ／
ERP-specific configuration ／ controlled configuration file ／ other approved source，
但**当前 Design 不决定真实 physical source**。

因此 **`provenance carrier` 仍保持独立：`DESIGN PENDING`** ——
**不得**在本 Decision **顺手关闭** `provenance carrier`。

**决定 10 —— Relationship to BOM = CONFIRMED**

正式确认：**`loss_rate` applicability 必须与 applicable BOM relationship 一起被可靠解析。**

**原因：** `loss_rate` 放大的是

```
BaseRequirement = ProductionQty × BOMComponentQty
```

而 `BOMComponentQty` 本身**只**在其 `Production Requirement` ＋ `applicable BOM relationship`
context 中具有可靠 canonical meaning。

**但：** 这**不表示** `loss_rate` 就是 **BOM Component persisted attribute**。
必须保持：

```
applicability relationship  ≠  persisted ownership field
```

**决定 11 —— Cross-Requirement Boundary = CONFIRMED**

**不得**因为 `Plant` ／ Parent Material ／ Component Material 相同，
就默认不同 `required_date` 的 `Requirement Calculation Context` **共享**同一个 `loss_rate`。

例如：

```
R1: 2026-10-10
R2: 2026-11-10
```

**允许** future source evidence 解析出**不同**的 applicable `loss_rate`。

**但本 Design：既不规定必须相同，也不规定必须不同。**
只要求**每个 context 独立可靠解析** exactly one or unresolved。

**决定 12 —— Multi-Parent Boundary = CONFIRMED**

同一 component Material `MAT-B` 出现在 `MAT-A → MAT-B` 与 `MAT-X → MAT-B` 时，
**不得**因为 `component material_code` 相同就**自动共享** `loss_rate` ——
**Parent / requirement context 属于 applicability grain**，**不得 silent reuse**。

**决定 13 —— No Precedence Rule（未批准任何 precedence）**

本 Human Decision **不批准任何 source precedence**，尤其**未批准**：

- BOM-level wins
- Material-level wins
- Plant-level wins
- requirement-level wins
- most specific wins
- latest configuration wins
- global fallback

未来如需要 precedence：**必须**有新的 **Human-approved Design Decision**。

**决定 14 —— Minimal Consistency Synchronization = AUTHORIZED（授权边界）**

授权后续**专门 Design Change Task** 对 `§4.1` ／ `§4.2` ／ `§4.4` ／ `§4.5`
执行实施 **Option E** 所需要的最小 consistency synchronization：

| 章节 | 授权内容 |
| --- | --- |
| **`§4.1`** | **仅**澄清 `Requirement Calculation Context` 可由现有 `Production Requirement` ＋ applicable BOM relationship ＋ component context 表达；**不新增** canonical entity；**不新增** canonical field；**不修改**现有 entity grain |
| **`§4.2`** | 记录 `loss_rate` applicability contract；记录 owner / grain = `Requirement Calculation Context`；source / physical carrier **继续未定义**；同步 current open-item status |
| **`§4.4`** | 同步 missing vs unresolved vs invalid；同步 exactly-one-or-unresolved boundary；**不新增** Validation Reason |
| **`§4.5`** | 记录 Option E implementation；同步 owner / grain current status；同步 unresolved count |

**不得修改 `§2` Business Rules。**

**决定 15 —— Explicitly Not Authorized**

本 Human Decision **不授权**：

- 将 `loss_rate` 加入 BOM Component attributes
- 将 `loss_rate` 加入 Production Requirement attributes
- 新增 `LossRatePolicy` entity
- 新增 `ScrapPolicy` entity
- 新增 `loss_policy_id`
- 新增 `requirement_calculation_id`
- 新增 precedence rule
- 新增 source field
- 新增 source table
- 新增 schema
- 新增 Adapter
- 新增 mapping config
- 新增 API
- 新增 Validation Reason
- 解决 `ApplicableMOQ` source
- 解决 `provenance carrier`
- 重新引入 `required_quantity`
- 修改 `loss_rate` formula

**执行状态（PR #40 时点）**

```
Canonical Model Compatibility = COMPATIBLE（Option E resolution-contract form only）
Option E                      = APPROVED
canonical owner               = exact Requirement Calculation Context
applicability grain           = plant_id + parent / requirement material
                                + required_date + component material
applicable BOM relationship   = required applicability context
Exactly-One-or-Unresolved     = APPROVED
owner / grain                 ≠ physical carrier / source table
minimal §4.1/§4.2/§4.4/§4.5 sync = AUTHORIZED

Option E Implementation       = NOT YET EXECUTED
loss_rate owner / grain       = UNKNOWN until follow-up implementation
unresolved count              = 3
Other Source-Semantic Mapping = DESIGN PENDING
provenance carrier            = DESIGN PENDING
```

**本 PR 不实施 Option E semantic synchronization。** 在 follow-up
**Human-authorized Design Change** 完成前：

```
loss_rate canonical owner / grain = UNKNOWN
unresolved count                  = 3
Other Source-Semantic Mapping     = DESIGN PENDING
```

**Option E Implementation Record（Human-authorized Design Change）**

**Human Authorization Source**

```
PR #40 Human Decision — Human-approved
  → Canonical Model Compatibility    = COMPATIBLE（Option E resolution-contract form only）
  → Option E                         = APPROVED
  → canonical owner                  = exact Requirement Calculation Context
  → applicability grain              = APPROVED
  → Exactly-One-or-Unresolved        = APPROVED
  → owner / grain ≠ physical carrier = CONFIRMED
  → minimal §4.1/§4.2/§4.4/§4.5 sync = AUTHORIZED
```

**Implementation Result**

```
loss_rate
is resolved for
an exact Requirement Calculation Context

with:
  exactly one applicable canonical loss_rate
  或
  unresolved
```

**Requirement Calculation Context（正式定义，conceptual）**

```
Production Requirement
        +
Applicable BOM Relationship
        +
Component Material
        ↓
Requirement Calculation Context
        ↓
applicable canonical loss_rate
```

**Applicability Grain（正式记录）**

```
plant_id
+ parent / requirement material_code
+ required_date
+ component material_code
```

> 「**至少**」保留：未来 source evidence 若需**额外维度**才能唯一解析，
> `Adapter` **不得**把差异静默压扁。
> 当前 Design **不得发明** `routing` / `operation` / `work center` / BOM version number /
> production version / policy ID 等额外维度。

**本 Task 未创建：** `RequirementCalculationContext` entity ／ `requirement_calculation_id` ／
`context_id` ／ `loss_policy_id` ／ `scrap_policy_id` ／ 任何 canonical field ／ identity component。

**Canonical Owner ≠ Physical Carrier（正式保持）**

```
Canonical Owner                ≠  Physical Source Owner
Canonical Applicability Grain  ≠  Database Primary Key
```

`loss_rate` **不是** `BOM Component` ／ `Production Requirement` 或任何 persisted entity 的 attribute。
**canonical owner 现为 `DESIGN RESOLVED`** 的同时，**physical carrier 仍未知** ——
本 Task **未**因 carrier 未知而继续保留 owner 为 `UNKNOWN`，也**未**声称 carrier 已完成。

**Cross-Requirement Boundary（正式确认）**

```
R1: Plant-A / Parent MAT-A / required_date = 2026-10-10 / Component MAT-B
R2: Plant-A / Parent MAT-A / required_date = 2026-11-10 / Component MAT-B
```

**不得**因为 `Plant` ／ Parent ／ Component 相同就**自动共享** `loss_rate`。
**允许** future source evidence 解析出 `R1 = 0.02`、`R2 = 0.05`，
**也允许**解析成相同值。当前 Design **既不规定必须相同，也不规定必须不同** ——
只要求**每个 context 独立可靠解析**。

**Multi-Parent Boundary（正式确认）**

```
MAT-A → MAT-B
MAT-X → MAT-B
```

**不得**因为 `component material = MAT-B` 就**自动共享** `loss_rate` ——
**不得** `Material`-level silent reuse；Parent / requirement context 属于 applicability distinction。

**Exactly-One-or-Unresolved Contract（正式落地）**

对每一个 `GrossRequirement` calculation context，进入 `BR-REQUIREMENT-001` **之前**必须解析出：

```
exactly one applicable canonical loss_rate
或
unresolved
```

**不创建任何 precedence：** `Material`-level wins ／ BOM-level wins ／ Plant-level wins ／
requirement-level wins ／ most specific wins ／ latest wins ／ first wins ／ `max` ／ `min` ／
`average` ／ `copy previous` ／ `fallback to global` ／ `LLM choose` —— **全部不采用**。
多 candidate 无法唯一解析 → **`unresolved`**，而**不是**自动选择。

**Missing ／ Unresolved ／ Invalid（正式同步）**

| Root condition | 判定 | 结果 |
| --- | --- | --- |
| **A** context 已可靠解析，但 required `loss_rate` value **missing** | `FIELD_VALUE` ／ `MISSING` | `DATA_INCOMPLETE` |
| **B** `loss_rate` evidence 存在，但**无法可靠确定哪个适用于当前 Requirement Calculation Context** | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE` |
| **C** applicable `loss_rate` 已可靠解析，但 `loss_rate < 0` 或 `loss_rate >= 1` | 继承既有 field / range invalid handling | `DATA_INCOMPLETE` |

**不得**把三者全部描述为 `loss_rate missing`。
**未新增**任何 Validation Reason ／ Business Status ／ Error Code（`§4.4.80` ／ `§4.4.81` 未变）。

**Acceptance Examples**

**Example —— Multiple Candidate（unresolved，不得自动选择）**

```
Context:            Plant-A / Parent MAT-A / required_date = 2026-10-10 / Component MAT-B
Candidate evidence: 0.02、0.05
```

若**没有** approved mapping evidence 能够唯一选择：

```
SEMANTIC_UNRESOLVED
        ↓
GrossRequirement = DATA_INCOMPLETE
```

**不得**：`average = 0.035` ／ `max = 0.05` ／ `latest = …` ／ `first = …`。

**Example —— Resolved**

```
Context:        Plant-A / Parent MAT-A / required_date = 2026-10-10 / Component MAT-B
mapping:        source-specific mapping 可靠解析 loss_rate = 0.05
BaseRequirement = 200
        ↓
GrossRequirement = 200 / (1 - 0.05)
```

继续按 **`BR-REQUIREMENT-001`** 计算。**本 Task 未重新定义公式**，
**未**把 `loss_rate` 改成 markup，**未**采用 `BaseRequirement × (1 + loss_rate)`，
**未**引入 `round` ／ `ceil` ／ `floor`。

**Zero Boundary（保持）**

```
loss_rate = 0
```

表示**明确配置为无损耗**，**VALID**。
**不得**：`0 → missing` ／ `0 → unresolved` ／ `0 → fallback` ／ `0 → choose another candidate`。

**Source-Specific Evidence Boundary（保持）**

具体 source representation **当前不定义**。未来可能来自 BOM-related source evidence ／
Material configuration ／ planning configuration ／ ERP-specific configuration ／
controlled configuration data —— 但当前 POC **不声明任何一个是真实来源**。

```
source-specific evidence
        ↓
explicit deterministic resolution
        ↓
one applicable canonical loss_rate
for exact Requirement Calculation Context
```

**Provenance Carrier Boundary（保持）**

`provenance carrier` **仍为 `DESIGN PENDING`**。
**未创建** `source_record_id` ／ `lineage_id` ／ `trace_id` ／ metadata JSON ／ mapping table ／
source table reference field ／ physical provenance schema。
**只允许**说明：resolved `loss_rate` 未来**必须能够追溯到**其 source evidence / mapping basis。

**`§4.1` / `§4.2` / `§4.4` / `§4.5` Synchronization Result**

| 章节 | 同步内容 |
| --- | --- |
| **`§4.1`** | `§4.1.12` open item 同步为 **`DESIGN RESOLVED`**；**仅**澄清 `Requirement Calculation Context` 可由现有 `Production Requirement` ＋ requirement-scoped applicable BOM relationship ＋ component material 表达；**未新增** canonical entity / field；**未修改** `Production Requirement` 或 `BOM Component` grain；**未**给 `BOM Component` 增加 `loss_rate` attribute |
| **`§4.2`** | `§4.2.4` 记录 applicability / owner boundary（canonical semantic 与 `Class = POLICY_INPUT` **未变**，**未新增** field row）；`§4.2.16` 将该 open item 移出 |
| **`§4.4`** | `§4.4.15` ／ `§4.4.54` 同步 owner / grain / resolution contract，并同步 missing vs unresolved vs invalid；**未新增** Validation Reason |
| **`§4.5`** | 本节记录 Option E implementation；同步 owner / grain current status 与 unresolved count |

**未修改 `§2` Business Rules**（**byte-semantically identical**）。

**Meaning of `DESIGN RESOLVED`**

`loss_rate` canonical owner / grain = **`DESIGN RESOLVED`** **只**表示
**canonical owner / applicability grain / resolution contract 概念设计完成**，
**不表示**：

- real ERP source known
- source table known
- source field known
- mapping config exists
- Adapter implemented
- validation code implemented
- tested
- `GrossRequirement` engine implemented
- production-ready

**执行状态（本 Task 完成时点）**

```
Human Decision                    = RECORDED
Option E                          = IMPLEMENTED
loss_rate canonical owner / grain = DESIGN RESOLVED
unresolved count                  = 3 → 2
Other Source-Semantic Mapping     = 仍 DESIGN PENDING
Master Data Mapping overall       = 仍 DESIGN PENDING
```

**未新增**任何 Master Data Mapping layer —— 这是 **`Other Source-Semantic Mapping`
内部 unresolved item 的关闭**，`DESIGN RESOLVED` layer 数**仍为 9**。

**剩余未决项（2 项）**

```
1. ApplicableMOQ source = DESIGN PENDING
2. provenance carrier   = DESIGN PENDING
```

**ApplicableMOQ Source / Applicability Design Review（Review Finding）**

**Review Question**

本 Review **只处理一个问题**：

> 对于一条明确的 **Procurement Recommendation**，
> 如何从 **source-specific purchasing-policy evidence** 可靠解析出
> **exactly one canonical `ApplicableMOQ`**，或 **`unresolved`**？

并且**必须同时满足**（不得为求解而放弃）：

- **不做** Supplier Selection ／ Supplier Ranking
- **不猜** Supplier
- **不发明** source precedence
- **不把** `missing` 默认成 `0`

**Evidence Boundary**

| 证据来源 | 是否定义 `ApplicableMOQ` source field / owner / applicability / precedence |
| --- | --- |
| `FROZEN` Discovery Brief（`discovery-brief-v0.1.1.md`） | **否** —— 只把「采购最小批量是否影响采购建议？」作为 **`G-10` 原问题**提出，并把 **MOQ 规则**明确划归后续设计 |
| `FROZEN` Discovery Validation（`discovery-validation-v0.1.md`） | **否** —— `G-10` 的 **RESOLVED** 只针对 **P0-2 字段可得性**（`VR-005` ＋ `VR-006`：数量与供应商数据可得）；遗留设计项为 **MOQ 规则 ／ 建议数量计算逻辑**，归属 **`VB-18` / `POC Design v0.2`** |
| `§2.5.5` | 只定义 **canonical semantic**；**明确不决定**真实来源（Supplier-Material Master ／ Contract ／ Purchasing Info Record ／ ERP proprietary field ／ 其他采购主数据） |
| `§2.5.13` | 只定义 **Supplier Boundary**（本 POC **不做** Supplier Selection）；MOQ 必须是**已可靠确定**的 canonical input |
| `§4.2.9` | Data Dictionary row ＋ **`Source Mapping = DESIGN PENDING`**；**不得**自行绑定 Supplier ／ Contract ／ ERP Purchasing Info Record |
| `§4.4.67` | `source mapping = DESIGN PENDING`；**不得**自行决定来源 |

**必须明确：**

- 两份 `FROZEN` Discovery 都**没有**定义 `ApplicableMOQ` 的 **source field**、**owner**、
  **applicability grain** 或 **precedence**。
- `G-10` 被标为 **RESOLVED** 的是「**P0-2 字段清单可得**」，
  **不是**「MOQ 的来源已确定」—— 这两件事**不得混淆**。
- 因此**不得声称**真实 MOQ 一定属于 **Supplier-Material Master ／ Contract ／
  Purchasing Info Record ／ ERP Material Master ／ Supplier Master ／ 采购组织配置**
  中的**任何一个**。这些只能作为 **possible source forms**，**不能作为项目事实**。

**Existing Procurement Recommendation Context**

`§4.1.4 K` 已定义 **Procurement Recommendation**：

```
Business grain:
  plant_id
  + material_code
  + RecommendationNeedDate

Canonical observation context:
  Analysis Run
  + plant_id
  + material_code
  + RecommendationNeedDate
```

其 **attributes 已包含 `ApplicableMOQ`**。

`§2.5` 已确定的 **Human-approved** 语义：

```
Classification = SHORTAGE
  → BasePurchaseNeed = ShortageQty at FirstShortageDate

RecommendedPurchaseQty = max(BasePurchaseNeed, ApplicableMOQ)
MOQAdjustmentQty       = RecommendedPurchaseQty - BasePurchaseNeed
```

**本 Review 不重新计算 `ShortageQty`**，**不把 `BufferGap` 加入 `BasePurchaseNeed`**，
**不修改**上述公式。

**因此必须回答：** 现有 Procurement Recommendation Context
**是否足以承载 `ApplicableMOQ` applicability resolution**，
而**无需**新增 `supplier_id` ／ `contract_id` ／ `purchasing_info_record_id` ／
`MOQPolicyId` 或任何新 canonical entity？

**Existing Supplier Boundary（不得修改）**

继承 **`§2.5.13`**：

```
Supplier-Material Relationship Eligibility
  ≠ Supplier Ranking
  ≠ Supplier Selection
  ≠ Supplier Recommendation
```

因此即使：

```
Supplier A MOQ = 50
Supplier B MOQ = 100
```

也**不得**为了得到 MOQ 而自动选择 Supplier A 或 Supplier B，
**更不得**用 `min = 50` ／ `max = 100` ／ `average = 75` **伪装**成 `ApplicableMOQ`。

**Critical Scenario A —— Multiple Eligible Suppliers**

```
Plant-A / MAT-X
Classification   = SHORTAGE
BasePurchaseNeed = 30

Supplier A：eligible relationship，MOQ = 50
Supplier B：eligible relationship，MOQ = 100

当前 Procurement Recommendation 没有 approved Supplier Selection。
```

必须回答：`ApplicableMOQ` 是 **50**？**100**？**其他**？还是 **`unresolved`**？

**不得**通过以下任一方式解决：

- `lowest MOQ wins`
- `highest MOQ wins`
- `lowest risk wins`
- `preferred supplier guess`
- `first supplier`
- `latest supplier`
- `LLM choose`

**结论：** 在当前 POC 中，**多个 eligible supplier 且无 approved Supplier Selection** 时，
`ApplicableMOQ` 的适用性**无法唯一确定** → **`unresolved`** → **`DATA_INCOMPLETE`**。

**Critical Scenario B —— Multiple Policy Sources**

同一个 Procurement Recommendation：

```
Contract evidence：           MOQ = 80
Purchasing Info Record：      MOQ = 100
```

两个 evidence 都看似有效，但当前**没有 approved precedence**
（`Contract > PIR` 或 `PIR > Contract`）。

**结论：** **不得**形成 exactly one `ApplicableMOQ` →
**`SEMANTIC_UNRESOLVED`** → **`DATA_INCOMPLETE`**。

**不得**：`latest wins` ／ `most specific wins` ／ `max` ／ `min` ／ `first wins`。

**Critical Scenario C —— Explicit Zero**

存在可靠 source-specific evidence：

```
ApplicableMOQ = 0
```

必须保持：

```
0 = explicit no MOQ constraint
```

**不是** `missing`、**不是** `invalid`、**不是** `unresolved`。

**不得**因为另一个 candidate 存在非零 MOQ 就自动覆盖 `0` ——
除非未来存在 **Human-approved precedence rule**。

**Critical Scenario D —— Supplier-Independent Policy Evidence**

假设某 source-specific purchasing policy 能够**直接、可靠**地针对：

```
Plant-A
+ MAT-X
+ 当前 Procurement Recommendation Context
```

产生 `ApplicableMOQ = 50`，**且无需选择 Supplier**。

**结论：可以**直接解析为 canonical `ApplicableMOQ`。

**为什么不需要 `supplier_id` 进入 canonical recommendation grain：**
canonical applicability context 是 **recommendation 本身**（`plant_id` ＋ `material_code`
＋ `RecommendationNeedDate`），**不是** Supplier。Supplier（若存在于 source 侧）只是
**source-side dimension**；`Adapter` / mapping 必须能够**在 source 侧确定性地解析**它，
而**不得**把「选择 Supplier」这一步**引入 canonical model**。

**这正是本 Review 的关键分界：**

```
source 侧能够确定性解析 supplier-dependent evidence
  且无需在 canonical 侧做 Supplier Selection
        ↓
可以形成 exactly one ApplicableMOQ   →  resolved

唯一性只能靠「在多个 eligible supplier 中挑一个」达成
        ↓
unresolved  →  DATA_INCOMPLETE
```

**Source vs Applicability vs Carrier（必须三分）**

```
A. Canonical applicability context
   「这个 MOQ 对哪条 recommendation 有效」

B. Source semantic role
   「哪类 source-specific business evidence 可以解析 ApplicableMOQ」

C. Physical carrier
   「在哪个 table / file / field / artifact 中承载」
```

**本 Review 只设计 A 与 B。不得设计 C。**
`provenance carrier` 仍是**独立 unresolved item**（**§4.5.22** ／ **§4.5.24**），
**不得**在本 Review 顺手关闭。

**Supplier Eligibility ≠ MOQ Applicability**

已有：

```
Supplier-Material Relationship
  eligible
```

**只**表示该 relationship 可以进入 **Risk Evidence evaluation**。

**不得**推导：

```
eligible supplier's MOQ = 当前 recommendation ApplicableMOQ
```

尤其：**多个 eligible suppliers 存在时，eligibility 不能解决 `ApplicableMOQ` 的唯一性** ——
因为 eligibility 是**准入判断**，不是**商业选择**。

**Valid Absence Boundary**

如果：

```
Classification = NORMAL
或
Classification = BUFFER_BREACH
```

当前本来就 **No Purchase Recommendation**，因此 `ApplicableMOQ` **not present by design**
是 **valid absence** —— **不是** `missing`，**不是** `DATA_INCOMPLETE`。

**只有** `Classification = SHORTAGE` **且需要 numeric recommendation** 时，
`ApplicableMOQ` resolution 才成为 **Required**。

**Time Applicability Boundary**

**不得**自动声明 `ApplicableMOQ` **timeless**；
**也不得**自动声明每个 `RecommendationNeedDate` 一定有**不同** MOQ。

如果 source policy 存在**时效差异**，source-specific mapping **必须**能够可靠确定
「当前 recommendation 适用哪一个 policy evidence」。

**如果无法判断** → **`SEMANTIC_UNRESOLVED`**。

**不得**：`latest record wins` ／ `current system date wins` ／ `AnalysisDate wins` ——
除非已有 **approved rule**。

**Option Review**

| Option | 内容 | 判定 |
| --- | --- | --- |
| **0** | Keep `ApplicableMOQ` source `DESIGN PENDING` | **安全但非终点** —— `SHORTAGE` 下**永远**只能 `DATA_INCOMPLETE` / No Numeric Recommendation，等于 procurement 建议**无法在无人介入时可靠执行** |
| **A** | Material / Plant-Material MOQ | **拒绝** —— 当前 evidence **未证明** MOQ 与 Supplier / Contract 无关。**不得**因为「企业经常这样配置」就当成项目事实 |
| **B** | Supplier-Material MOQ（`supplier_id` ＋ `material_code`） | **拒绝** —— 当前 POC **没有** Supplier Selection，**无法确定**用哪个 Supplier 的 MOQ。若必须先选 Supplier，则与 **§2.5.13** 冲突；**不得**把 Supplier Eligibility 偷偷变成 Supplier Selection |
| **C** | Aggregate candidate supplier MOQs（`min` / `max` / `average`） | **拒绝** —— 这实际上**创建了一条新的商业决策规则**（`§4.4.42 No Stringency Inflation`），当前**没有 evidence** 支持 |
| **D** | Source-Specific Purchasing-Policy Resolution → exact Procurement Recommendation Context | **推荐方向**（见下） |
| **E** | Default missing MOQ to `0` | **拒绝** —— `§2.5.6` 明确 `missing ≠ 0`，该方案与现有 Human-approved Rule **直接冲突** |
| **F** | Delay numeric recommendation until Supplier Selection | **拒绝（本 Task 不得采用）** —— 它会改变 **`BR-PROCUREMENT-001`** 的「**one baseline numeric recommendation**」设计语义，**需要修改 `§2`** → 必须另行 **Human Gate** |

**Recommended Direction —— Option D**

Conceptually：

```
source-specific purchasing-policy evidence
        ↓
explicit deterministic resolution
        ↓
exact Procurement Recommendation Context
        ↓
exactly one canonical ApplicableMOQ
        or unresolved
        ↓
BR-PROCUREMENT-001
```

`Procurement Recommendation Context` **至少已有**：

```
plant_id
+ material_code
+ RecommendationNeedDate
```

并**属于明确 Analysis Run**。

**Option D 不要求：**

- 统一真实 source table / field
- `ApplicableMOQ` 永久属于 Material ／ Supplier ／ Contract 中**某一个 persisted entity**

**如果 source evidence 无法在不做 Supplier Selection 的情况下唯一解析：**

```
→ unresolved
→ DATA_INCOMPLETE
```

**不得**为了解决 source 问题而**反向引入** Supplier Selection。
`§2.5.13` 的边界**优先于**「让 recommendation 一定能算出数」这一便利性诉求。

**Missing ／ Unresolved ／ Invalid ／ Explicit Zero Boundary（必须区分）**

| # | 情形 | 判定 | 结果 |
| --- | --- | --- | --- |
| **A** | applicable source mapping / policy **已可靠确定**，但 required MOQ value **missing** | `FIELD_VALUE` ／ `MISSING` | `DATA_INCOMPLETE` |
| **B** | MOQ evidence **存在**，但**无法可靠判断哪个适用于当前 recommendation** | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE` |
| **C** | applicable MOQ 已解析，但 `ApplicableMOQ < 0` | 继承既有 `FIELD_VALUE` ／ `OUT_OF_DEFINED_RANGE` handling | `DATA_INCOMPLETE` |
| **D** | `ApplicableMOQ = 0` | **VALID explicit no MOQ constraint** | 正常参与 `max(BasePurchaseNeed, ApplicableMOQ)` |

**不得混淆四者。** 尤其**不得**把 **A / B** 默认成 **D**。

**Exactly-One-or-Unresolved Contract（评估）**

建议采用，且**仅作为 canonical resolution contract**：

```
对于每一个需要生成 numeric Procurement Recommendation 的 context：
  必须在进入 BR-PROCUREMENT-001 数量计算之前解析出
    exactly one applicable canonical ApplicableMOQ
    或
    unresolved
```

- 好处：`BR-PROCUREMENT-001` **不必**面对多个 candidate MOQ 再临时选择 ——
  与 **§4.5.21**（`effective_arrival_date`）及 **§4.5.22**（`loss_rate`）已批准的同类契约**同构**。
- **这只是 canonical resolution contract**：它**不**定义 precedence、
  **不**定义 source field、**不**定义 carrier、**不**创建 ID。
- 无法解析出唯一值 → **`DATA_INCOMPLETE`** → **No Numeric Recommendation**。

**Canonical Model Compatibility Result**

推荐方向 **Option D** 的判定：

```
Canonical Model Compatibility = COMPATIBLE
```

依据（**不新增**任何 entity / field / identity component）：

| 需要表达的内容 | 现有 Canonical Model 是否已能表达 |
| --- | --- |
| canonical applicability context | **已有** —— `§4.1.4 K` Procurement Recommendation grain（`plant_id` ＋ `material_code` ＋ `RecommendationNeedDate`） |
| observation context | **已有** —— Analysis Run（**observation context，不因此成为 MOQ 的业务 owner**） |
| 承载 `ApplicableMOQ` 的 attribute | **已有** —— `§4.1.4 K` attributes ／ `§4.2.9` Data Dictionary row |
| `missing` ／ `unresolved` ／ `invalid` ／ `explicit zero` 的可表达性 | **已有** —— `§2.5.6` ／ `§2.5.7` ／ `§4.4.35` ／ `§4.4.67` |
| 「无法唯一解析」的可表达性 | **已有** —— 既有 fail-safe 路径 `DATA_INCOMPLETE` / No Numeric Recommendation |

**必须明确 —— 判为 `COMPATIBLE` 的前提：**

Option D 的 **resolution-contract** 形式，即 `ApplicableMOQ` 是
**针对 exact Procurement Recommendation Context 解析出的 canonical purchasing constraint**，
**不要求** Supplier 进入 canonical decision path。

**同时必须明确（不得模糊）：**

- 若 Human 要求 **Option B 作为 resolution path**（即必须由 `supplier_id` ＋ `material_code`
  决定 MOQ），则 **`Canonical Model Compatibility = INSUFFICIENT`** ——
  必须把 Supplier 引入 recommendation 的 applicability/resolution 路径，
  与 **`§2.5.13`**（不做 Supplier Selection）**冲突**，
  属于 **Canonical Model Change**，**必须另行走 Human-approved Amendment**。
- **Option A ／ C ／ E ／ F** 均**不推荐**：A 无 evidence、C 发明商业规则、E 与既有 Rule 冲突、
  F 需要修改 `§2`。

**Known Risks（本 Review 识别，未消除）**

| # | Risk | 说明 | 当前状态 |
| --- | --- | --- | --- |
| 1 | **真实 MOQ 可能是 supplier-dependent** | 若真实 evidence 只在 supplier 维度唯一，则在不做 Supplier Selection 的前提下**只能 `unresolved`** —— Procurement Recommendation 将**长期**停在 `DATA_INCOMPLETE` | **未消除** —— 这是本 Review 的**核心未决事实**，只能由真实 evidence ＋ Human Decision 解决 |
| 2 | **Carrier 未知** | 真实 physical carrier（Supplier-Material Master ／ Contract ／ PIR ／ ERP-specific object ／ controlled configuration）**仍未知** | **未消除** —— `provenance carrier` 仍为独立 **`DESIGN PENDING`** |
| 3 | **Supplier 数据可得 ≠ supplier-level MOQ** | `G-10` 的 RESOLVED 只说明**数量与供应商数据可得** | **已设边界** —— 不得据此推断 MOQ 属于 Supplier |
| 4 | **无 precedence** | 多 policy source（Contract vs PIR）无 approved precedence → 只能 `unresolved` | **已设边界** —— 未来如需 precedence，**必须**另有新的 **Human-approved Design Decision** |
| 5 | **Eligibility 被误用** | 把 eligible relationship 当作可推导 ApplicableMOQ | **已设边界** —— eligibility ≠ applicability（**§4.5.11** ／ 本 Review） |
| 6 | **隐性 Supplier Selection** | 为「让建议能出数」而在 mapping 层偷偷选 Supplier | **已设边界** —— 唯一性若只能靠挑 Supplier 达成 → **`unresolved`** |
| 7 | **`Other Source-Semantic Mapping` 仍未闭合** | `ApplicableMOQ` 只是该层其中一个子项 | **未消除** —— 本 PR **未**减少 unresolved count |

**Status（本 Review 时点）**

```
ApplicableMOQ canonical semantic        = DESIGN RESOLVED   ← 未变
ApplicableMOQ zero / missing semantics  = DESIGN RESOLVED   ← 未变
ApplicableMOQ range                     = DESIGN RESOLVED   ← 未变
Procurement quantity formula            = DESIGN RESOLVED   ← 未变
ApplicableMOQ source / applicability    = DESIGN PENDING    ← 未变
provenance carrier                      = DESIGN PENDING    ← 未变
unresolved count                        = 2                 ← 未变
Other Source-Semantic Mapping           = DESIGN PENDING    ← 未变
```

本 Review **不**实施任何 Option，**不**修改 `§2` / `§4.1`，
**不**减少 unresolved count。

**Human Decision Required**

1. 是否接受 **`Canonical Model Compatibility = COMPATIBLE`**？
2. 是否采用 **Option D** —— source-specific purchasing-policy evidence
   → exact Procurement Recommendation Context → **exactly one `ApplicableMOQ` or `unresolved`**？
3. 是否确认 **Supplier Eligibility ≠ Supplier Selection**，且**不得**用于隐式决定 MOQ？
4. 是否确认 **supplier-dependent MOQ** 在 Supplier 未被独立可靠确定时
   → **`unresolved` / `DATA_INCOMPLETE`**？
5. 是否确认 **`ApplicableMOQ = 0`** 为 **valid explicit no MOQ**，
   而 **`missing` / `unresolved` 不得默认 `0`**？
6. 是否授权 **`§4.1` / `§4.2` / `§4.4` / `§4.5`** 必要的最小 consistency synchronization？

**若 Human 要求 Option B 作为 resolution path**，则需额外给出：
**Blocking Finding** ＋ **Minimum Model Change Options** ＋ **trade-offs** ＋
**Human Approval Required**（本 Review 当前**不**推荐该形式）。

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 本节是对**上方 Review Finding** 的 **Human Decision**。
> 上方 Review Finding 中的 `Human Decision Required` 表述**已在本节获得答案**；
> 未实施部分见本节末 **执行状态**。
>
> 上方 **Evidence Boundary** ／ **Critical Scenarios** ／ **Option Review** ／
> **Canonical Model Compatibility Result** ／ **Known Risks**
> **全部保留，未删除、未改写**。

**决定 1 —— Canonical Model Compatibility = `COMPATIBLE`（ACCEPTED，附严格限定）**

接受：

```
Canonical Model Compatibility = COMPATIBLE
```

**该结论严格限定于：**

```
Option D
= Source-Specific Purchasing-Policy Resolution
+ resolution-contract form
```

即 `ApplicableMOQ` **继续作为现有 Procurement Recommendation 的 canonical input**。

**不新增：**

- `supplier_id` 到 Recommendation grain
- `contract_id`
- `purchasing_info_record_id`
- `MOQPolicy` entity
- policy identity
- Supplier Selection result
- canonical source field

**如果未来方案要求** Supplier 必须成为 Procurement Recommendation
**canonical identity / grain 的一部分**，则当前 **`COMPATIBLE`** 结论**失效**，
必须重新进入：

```
Canonical Model Compatibility Review
        +
Human-approved Canonical Model Amendment
```

**决定 2 —— Option D = APPROVED**

正式采用：

```
source-specific purchasing-policy evidence
        ↓
explicit deterministic resolution
        ↓
exact Procurement Recommendation Context
        ↓
exactly one canonical ApplicableMOQ
        or unresolved
```

这是当前 POC 的**正式设计方向**。

Canonical Design 统一的是 **`ApplicableMOQ` applicability semantics**，
**不是**真实 ERP source table / field。

**决定 3 —— Procurement Recommendation Context = CONFIRMED**

`ApplicableMOQ` **必须**针对一个明确的 **Procurement Recommendation Context** 被解析。

当前已有的 canonical business grain：

```
plant_id
+ material_code
+ RecommendationNeedDate
```

以及 **Analysis Run** 作为 observation context。

**必须保持：**

```
Analysis Run  ≠  MOQ business owner
```

Analysis Run **只**用于 **observation / traceability context**。
**不得**因本决定修改 **Procurement Recommendation grain**。

**决定 4 —— Exactly-One-or-Unresolved Contract = APPROVED**

对于每一个需要生成 **numeric Procurement Recommendation** 的 context，
**在进入 `BR-PROCUREMENT-001` 之前**必须解析出：

```
exactly one applicable canonical ApplicableMOQ
或
unresolved
```

**不得**让 `BR-PROCUREMENT-001` 面对多个 candidate MOQ 然后临时选择。

**禁止：**

- `lowest wins` ／ `highest wins`
- `min` ／ `max` ／ `average`
- `latest wins` ／ `first wins` ／ `most specific wins`
- `LLM choose` ／ `silent fallback`

**除非**未来另有 **Human-approved precedence rule**。

**决定 5 —— Supplier Eligibility ≠ Supplier Selection（CONFIRMED）**

正式确认：

```
Supplier-Material Relationship Eligibility
  ≠ Supplier Ranking
  ≠ Supplier Selection
  ≠ Supplier Recommendation
```

Supplier eligibility **不得**用于隐式决定 `ApplicableMOQ`。

例如：

```
Supplier A eligible / MOQ 50
Supplier B eligible / MOQ 100
```

在没有**独立可靠 Supplier determination** 的情况下，**不得**：

- 选 A ／ 选 B
- 取 50 ／ 取 100
- `min` ／ `max` ／ `average`
- `lowest risk wins`

结果：

```
unresolved
  → DATA_INCOMPLETE
```

**决定 6 —— Supplier-Dependent MOQ Boundary（CONFIRMED）**

正式确认：**supplier-dependent MOQ 本身不是无效。**

必须区分：

| 情形 | 判定 |
| --- | --- |
| **A** Supplier 已由**独立、可靠**、且**不是为了「拿到 MOQ」**而执行的业务上下文唯一确定，且对应 MOQ evidence 可可靠解析 | **可以**继续解析 `ApplicableMOQ` |
| **B** Supplier **尚未**被独立可靠确定，必须通过「在多个 eligible suppliers 中挑一个」才能决定 MOQ | **不允许** → `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` → `DATA_INCOMPLETE` → **No Numeric Recommendation** |

**不得**为了得到 MOQ **反向实现** Supplier Selection。

**决定 7 —— Multiple Policy Source Boundary（CONFIRMED）**

例如：

```
Contract MOQ = 80
PIR      MOQ = 100
```

如果没有 **Human-approved source precedence**，**不得**：

```
Contract wins ／ PIR wins ／ latest wins ／ most specific wins ／ min ／ max
```

结果：

```
SEMANTIC_UNRESOLVED
  → DATA_INCOMPLETE
```

**本 Human Decision 不建立任何 source precedence。**

**决定 8 —— Explicit Zero Boundary（CONFIRMED）**

正式确认：

```
ApplicableMOQ = 0
```

表示 **valid explicit no MOQ constraint**，是**合法业务输入**。

必须保持：

```
0 ≠ missing
0 ≠ unresolved
0 ≠ invalid
```

**不得**：`missing → 0` ／ `unresolved → 0` ／ `invalid → 0`。

**也不得**因为存在另一个非零 candidate 就**自动覆盖**可靠的 `0` ——
除非未来存在 **Human-approved precedence rule**。

**决定 9 —— Missing ／ Unresolved ／ Invalid ／ Explicit Zero = 四种情况保持分离（CONFIRMED）**

| # | 情形 | 判定 | 结果 |
| --- | --- | --- | --- |
| **A** | mapping ／ applicability 已可靠确定，但 required MOQ value **missing** | `FIELD_VALUE` ／ `MISSING` | `DATA_INCOMPLETE` |
| **B** | MOQ evidence 存在，但**无法可靠判断哪个适用于当前 Procurement Recommendation Context** | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE` |
| **C** | applicable MOQ 已解析，但 `ApplicableMOQ < 0` | 继承既有 `FIELD_VALUE` ／ `OUT_OF_DEFINED_RANGE` | `DATA_INCOMPLETE` |
| **D** | `ApplicableMOQ = 0` | **VALID explicit no MOQ** | 正常进入 `max(...)` calculation |

**不得**把 **A ／ B** 默认成 **D**。

**决定 10 —— Valid Absence Boundary（CONFIRMED）**

继续保持：`Classification = NORMAL` 或 `BUFFER_BREACH` 时 **No Purchase Recommendation**，
因此：

```
ApplicableMOQ not present by design = valid absence
```

**不是** `missing`，**不是** `DATA_INCOMPLETE`。

**只有** `Classification = SHORTAGE` **且需要形成 numeric recommendation** 时，
`ApplicableMOQ` resolution 才成为 **Required**。

**决定 11 —— MOQ Semantic Boundary（CONFIRMED）**

必须保持：

```
ApplicableMOQ = Minimum Order Quantity only
```

**不得**扩展为：`order multiple` ／ `pack size` ／ `carton quantity` ／ `pallet quantity` ／
`rounding rule` ／ `UOM conversion` ／ `lead-time adjustment`。

**不得修改：**

```
RecommendedPurchaseQty = max(BasePurchaseNeed, ApplicableMOQ)
MOQAdjustmentQty       = RecommendedPurchaseQty - BasePurchaseNeed
```

**决定 12 —— Source ／ Applicability ／ Carrier Separation（CONFIRMED）**

正式确认三层分离：

```
A. Canonical Applicability Context —— 这个 MOQ 对哪条 Recommendation 有效
B. Source Semantic Role          —— 哪些 source-specific purchasing-policy
                                    evidence 可以用于解析 ApplicableMOQ
C. Physical Carrier              —— 实际存在于哪个 table / file / field / artifact
```

**本次批准：A ＋ B。本次不解决：C。**

因此：

```
provenance carrier = DESIGN PENDING   ← 保持不变
```

**决定 13 —— Physical Source Boundary（CONFIRMED）**

当前**不得声称**真实 MOQ 一定来自：

- Supplier-Material Master
- Contract
- Purchasing Info Record
- Material Master
- Supplier Master
- Purchasing Organization configuration
- ERP proprietary object

这些**只能**作为 **possible source forms**。真实 ERP source **当前没有 evidence**。

**决定 14 —— Minimal Consistency Synchronization = AUTHORIZED（授权边界）**

授权后续**专门 Design Change Task** 对 `§4.1` ／ `§4.2` ／ `§4.4` ／ `§4.5`
执行实施 **Option D** 所需的最小 consistency synchronization：

| 章节 | 授权内容 |
| --- | --- |
| **`§4.1`** | **仅**允许澄清：现有 Procurement Recommendation Context **足以**承载 `ApplicableMOQ` applicability。**不得**修改 Recommendation grain、**不得**新增 Supplier identity ／ canonical field ／ entity ／ identity component |
| **`§4.2`** | 允许同步 `ApplicableMOQ` source ／ applicability contract、**exactly-one-or-unresolved**、source-specific policy evidence boundary、current open-item status |
| **`§4.4`** | 允许同步 missing vs unresolved vs invalid vs explicit zero、supplier-dependent unresolved path、multiple policy source unresolved path。**不得新增** Validation Reason |
| **`§4.5`** | 允许记录 Option D Implementation Record、current-state synchronization、unresolved count update |

**不得修改 `§2`。**

**决定 15 —— Explicitly Not Authorized**

本 Human Decision **不授权**：

- Supplier Selection
- Supplier Ranking
- preferred supplier
- lowest MOQ supplier
- lowest risk supplier
- `Contract > PIR` precedence
- `PIR > Contract` precedence
- `min` ／ `max` ／ `average` MOQ
- fallback supplier
- Supplier 进入 Recommendation grain
- Contract entity
- MOQ Policy entity
- source table
- source field
- physical carrier
- Adapter
- mapping config
- DB schema
- API
- ADR
- pack size
- order multiple
- rounding
- UOM conversion

**执行状态（PR #42 时点）**

```
Canonical Model Compatibility = COMPATIBLE（Option D resolution-contract form only）
Option D                      = APPROVED
Exactly-One-or-Unresolved     = APPROVED
Supplier Eligibility ≠ Supplier Selection = CONFIRMED
supplier-dependent MOQ w/o independently resolved Supplier = unresolved / DATA_INCOMPLETE
ApplicableMOQ = 0             = valid explicit no MOQ
missing / unresolved          ≠ 0（不得默认）
Source / Applicability / Carrier = separated（A ＋ B approved；C not resolved）
provenance carrier            = STILL DESIGN PENDING
minimal §4.1/§4.2/§4.4/§4.5 sync = AUTHORIZED

Option D Implementation       = NOT YET EXECUTED
ApplicableMOQ source / applicability = DESIGN PENDING until follow-up implementation
unresolved count              = 2
Other Source-Semantic Mapping = DESIGN PENDING
```

**本 PR 不实施 Option D semantic synchronization。** 在 follow-up
**Human-authorized Design Change** 完成前：

```
ApplicableMOQ source / applicability = DESIGN PENDING
provenance carrier                   = DESIGN PENDING
unresolved count                     = 2
```

**Option D Implementation Record（Human-authorized Design Change）**

**Human Authorization Source**

```
PR #42 Human Decision — Human-approved
  → Canonical Model Compatibility    = COMPATIBLE（Option D resolution-contract form only）
  → Option D                         = APPROVED
  → Exactly-One-or-Unresolved        = APPROVED
  → Supplier Eligibility ≠ Supplier Selection = CONFIRMED
  → supplier-dependent MOQ boundary  = APPROVED
  → ApplicableMOQ = 0                = valid explicit no MOQ
  → Source / Applicability / Carrier = separated（A ＋ B approved；C not resolved）
  → minimal §4.1/§4.2/§4.4/§4.5 sync = AUTHORIZED
```

**Implementation Result**

```
source-specific purchasing-policy evidence
        ↓
explicit deterministic resolution
        ↓
exact Procurement Recommendation Context
        ↓
exactly one applicable canonical ApplicableMOQ
        or unresolved
        ↓
BR-PROCUREMENT-001
```

**Procurement Recommendation Context（正式使用，**不改变 grain**）**

```
plant_id
+ material_code
+ RecommendationNeedDate
```

**observation / traceability context：** Analysis Run。

**必须保持：**

```
Analysis Run  ≠  MOQ business owner
```

**Canonical applicability resolution（正式落地）**

```
Canonical Applicability Context = exact Procurement Recommendation Context
Source Semantic Role            = SOURCE-SPECIFIC purchasing-policy evidence
Resolution Contract             = exactly one applicable ApplicableMOQ
                                  或 unresolved
Physical Carrier                = NOT YET DEFINED（provenance carrier = DESIGN PENDING）
```

`ApplicableMOQ` **仍是** `§4.1.4 K` Procurement Recommendation 的**既有 canonical attribute**。

**本 Task 未创建：** `supplier_id` 到 canonical grain ／ `contract_id` ／ `policy_id` ／
`purchasing_info_record_id` ／ `MOQPolicy` entity ／ policy identity ／ Supplier Selection result ／
任何 canonical field ／ identity component。

**Exactly-One-or-Unresolved Contract（正式落地）**

对于每一个 `Classification = SHORTAGE` **且需要生成 numeric Procurement Recommendation** 的 context，
**在进入 `BR-PROCUREMENT-001` 数量计算之前**必须得到：

```
exactly one applicable canonical ApplicableMOQ
或
unresolved
```

**不得**让多个 candidate MOQ 进入 deterministic formula ——
`ApplicableMOQ` **不是**由 `BR-PROCUREMENT-001` 临时选择出来的。

**不创建任何 precedence：** `lowest wins` ／ `highest wins` ／ `min` ／ `max` ／ `average` ／
`latest wins` ／ `first wins` ／ `most specific wins` ／ `Contract wins` ／ `PIR wins` ／
`LLM choose` ／ `silent fallback` —— **全部不采用**。

**Supplier Eligibility ≠ Supplier Selection（正式保持）**

```
Supplier-Material Relationship Eligibility
  ≠ Supplier Ranking  ≠ Supplier Selection  ≠ Supplier Recommendation
```

`eligible` supplier **不能自动贡献** `ApplicableMOQ`；
多个 eligible suppliers 存在时，eligibility **不能**解决唯一性。

**Supplier-Dependent MOQ Boundary（正式同步）**

| 情形 | 允许性 |
| --- | --- |
| **A** Supplier 已由**独立可靠**业务上下文唯一确定（且该 determination **不是**为了拿到 MOQ 而执行的隐藏 Supplier Selection），且对应 MOQ evidence 可可靠解析 | **允许**继续 resolution |
| **B** Supplier 只能通过「从多个 eligible Supplier 中挑一个」才能确定 MOQ | **不允许** → `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` → `DATA_INCOMPLETE` |

**不得**为了 MOQ **反向实现** Supplier Selection。

**Missing ／ Unresolved ／ Invalid ／ Explicit Zero（正式同步）**

| # | 情形 | 判定 | 结果 |
| --- | --- | --- | --- |
| **A** | applicability mapping 已可靠确定，但 required MOQ value **missing** | `FIELD_VALUE` ／ `MISSING` | `DATA_INCOMPLETE` |
| **B** | MOQ evidence 存在，但**无法可靠判断哪个适用于当前 Procurement Recommendation Context** | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE` |
| **C** | applicable MOQ 已解析，但 `ApplicableMOQ < 0` | 继承既有 `FIELD_VALUE` ／ `OUT_OF_DEFINED_RANGE` | `DATA_INCOMPLETE` |
| **D** | `ApplicableMOQ = 0` | **VALID explicit no MOQ constraint** | 正常参与 `max(BasePurchaseNeed, 0)` |

**不得**把 **A ／ B** 默认成 **D**；
**不得** `0 → missing` ／ `0 → unresolved` ／ `0 → invalid` ／ `0 → fallback`。

**未新增**任何 Validation Reason ／ Business Status ／ Error Code（`§4.4.80` ／ `§4.4.81` 未变）。

**Multiple Policy Source Boundary（正式同步）**

```
Contract MOQ = 80
PIR      MOQ = 100
```

在**没有** Human-approved precedence 时 → **`SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED`**。

**不得**自动归类为 `CONSISTENCY_CONFLICT` —— 除非既有语义明确说明这些 records
在**同一 canonical policy context** 本应一致；**当前没有该 Rule**。

**不建立任何 source precedence。**

**Time Applicability（正式同步）**

**不得**声明 `ApplicableMOQ` 永久固定，**也不得**声明每个 `RecommendationNeedDate` 一定不同。
若 source-specific policy 存在时间有效性，mapping **必须**可靠确定哪个 evidence 适用于
当前 `RecommendationNeedDate`；若无法判断 → **`SEMANTIC_UNRESOLVED`**。

**不得**：`latest wins` ／ `current date wins` ／ `AnalysisDate wins`。

**Valid Absence（保持）**

`Classification = NORMAL` 或 `BUFFER_BREACH` → **No Purchase Recommendation**，
因此 `ApplicableMOQ` **not present by design** 是 **valid absence** ——
**不是** `missing`、**不是** `unresolved`、**不是** `DATA_INCOMPLETE`。

**只有** `SHORTAGE` ＋ numeric recommendation required 时，resolution 才成为 **Required**。

**Physical Source Boundary（保持）**

**不得**声称 `ApplicableMOQ` 一定来自 Supplier-Material Master ／ Contract ／
Purchasing Info Record ／ Material Master ／ Supplier Master ／ Purchasing Organization config ／
ERP proprietary object —— 这些只能是 **possible source forms**。

**`§4.1` / `§4.2` / `§4.4` / `§4.5` Synchronization Result**

| 章节 | 同步内容 |
| --- | --- |
| **`§4.1`** | `§4.1.12` open item → **`DESIGN RESOLVED`**；**仅**澄清现有 Procurement Recommendation Context 已足以承载 `ApplicableMOQ` resolution；**未**修改 Recommendation grain，**未**新增 entity ／ field ／ identity component |
| **`§4.2`** | `§4.2.9` 邻接说明同步为 **Canonical Applicability Contract `DESIGN RESOLVED`**（`ApplicableMOQ` **仍是原有 attribute**，**未新增** field row）；`§4.2.16` 将该 open item 移出 |
| **`§4.4`** | `§4.4.67` 同步 applicability resolution、resolution contract 与四类 root condition；并写明 **supplier-dependent** 与 **multiple policy source** 两条 unresolved path；**未新增** Validation Reason |
| **`§4.5`** | 本节记录 Option D implementation；同步 current status 与 unresolved count |

**未修改 `§2` Business Rules**（**byte-semantically identical**）：
`RecommendedPurchaseQty = max(BasePurchaseNeed, ApplicableMOQ)` 与
`MOQAdjustmentQty = RecommendedPurchaseQty - BasePurchaseNeed` **未变**。

**Meaning of `DESIGN RESOLVED`**

`ApplicableMOQ` source / applicability = **`DESIGN RESOLVED`** **只**表示
**canonical applicability ＋ source semantic resolution contract 概念设计完成**，
**不表示**：

- real ERP source known
- Supplier selected
- Contract known
- PIR known
- mapping config exists
- Adapter implemented
- source data validated
- procurement engine implemented
- tested
- production-ready

**执行状态（本 Task 完成时点）**

```
Human Decision                       = RECORDED
Option D                             = IMPLEMENTED
ApplicableMOQ source / applicability = DESIGN RESOLVED
unresolved count                     = 2 → 1
Other Source-Semantic Mapping        = 仍 DESIGN PENDING
Master Data Mapping overall          = 仍 DESIGN PENDING
```

**未新增**任何 Master Data Mapping layer —— 这是 **`Other Source-Semantic Mapping`
内部 unresolved item 的关闭**，`DESIGN RESOLVED` layer 数**仍为 9**。

**剩余未决项（1 项）**

```
1. provenance carrier = DESIGN PENDING
```

**`Other Source-Semantic Mapping` 保持 `DESIGN PENDING`** —— 因其仍有 `provenance carrier`
未解决；**不得**提前标成 `DESIGN RESOLVED`。

**`Master Data Mapping` overall 保持 `DESIGN PENDING`** —— **不得**因
`unresolved count = 1` 就提前 closure。

**Historical Review Record —— PR #44（不得作为当前状态解读）**

> 以下 **Provenance Carrier / Minimum Traceability Contract Design Review（Review Finding）**、
> **Known Risks** 与 **Human Decision Record** 是 **PR #44** 时点的原始记录，
> **按当时时点原样保留**，以便追溯。
>
> 其中出现的 `provenance carrier = DESIGN PENDING`、`Option D Implementation = NOT YET EXECUTED`、
> `unresolved count = 1` 等表述**均为 PR #44 时点状态**，**不得**被解读为当前状态。
>
> **Option D 已由后续 Human-authorized Design Change 实施** ——
> `provenance carrier` 现为 **`DESIGN RESOLVED`**，`unresolved count` 现为 **0**，
> `Other Source-Semantic Mapping` 现为 **`DESIGN RESOLVED`**
> （见下方 **Option D Implementation Record**）。
**Provenance Carrier / Minimum Traceability Contract Design Review（Review Finding）**

**Review Question**

本 Review **只回答一个问题**：

> 为了让 **`source evidence → canonical fact / relationship → deterministic derived result
> → Procurement Recommendation`** 能够 **traceable ／ reproducible ／ auditable**，
> **当前 POC 最少需要什么 conceptual provenance carrier？**

并且**必须同时满足**：

- **不**因为「只剩最后一个 unresolved」就直接创建 **physical lineage infrastructure**
- **不**创建 `trace_id` ／ `lineage_id` ／ `source_record_id` ／ `mapping_rule_id`
- **不**新增 canonical business field ／ entity ／ identity component
- **不**修改任何 canonical entity grain
- **不**新增 Validation Reason
- **不**宣布 `Master Data Mapping` closure
- **不**顺手完成 `Snapshot / Import Contract` 的 physical 部分

**Existing Provenance Baseline（先复核并继承已有设计）**

| # | 既有设计 | 内容 |
| --- | --- | --- |
| **A** | **Snapshot Package** | 每个 accepted package 具有稳定 **`snapshot_package_id`**；它属于 **Import / Transport Context**，**不是** canonical business entity ID |
| **B** | **Analysis Run** | 每个 Analysis Run **必须能够追溯到 exactly one accepted Snapshot Package**；**不得** silent cross-snapshot mixing |
| **C** | **Logical Snapshot Manifest**（**§4.3.8**） | 至少表达 `snapshot_package_id` ／ contract version ／ export / package creation time ／ environment / evidence classification ／ included logical datasets ／ **dataset-level provenance reference** ／ dataset-level record count / integrity evidence ／ package completeness state |
| **D** | **Validation** | 已有 **Category `PROVENANCE`** ＋ **Reason `PROVENANCE_MISMATCH`**；**不得创建重复 reason** |
| **E** | **Master Data Mapping** | `Mapping Provenance Requirement` **已是 `DESIGN RESOLVED`** |

**因此本 Review 不是重新决定「要不要 provenance」，只决定 minimum carrier contract。**

**Four-Layer Traceability Question（四层必须分别回答）**

| Layer | 必须回答的问题 | 当前是否已能回答 |
| --- | --- | --- |
| **Layer 1 — Package** | 某 Analysis Run 使用了哪个 **immutable Snapshot Package**？ | **能** —— `snapshot_package_id` ＋ Analysis Run linkage（**§4.3.3** ／ **§4.3.4**） |
| **Layer 2 — Dataset / Evidence Role** | 某 canonical input 来自该 Package 中的哪个 **logical evidence role**？ | **能** —— logical dataset role（**§4.3.10**）＋ dataset-level provenance reference（**§4.3.8**） |
| **Layer 3 — Source Evidence** | 某个 canonical fact / relationship / policy input **具体由哪一份 source evidence 支撑**？ | **不能** —— **当前无 carrier contract** |
| **Layer 4 — Mapping / Derivation** | 若经过 semantic mapping / resolution，**使用了什么 mapping basis**；且 derived result 能否追溯回其 canonical inputs ＋ Analysis Run？ | **不能** —— **当前无 carrier contract** |

**不得把这四层全部压成 `snapshot_package_id`。**

**Critical Scenario A —— Dataset-Level Only Is Not Enough**

```
Package P1 包含 Inbound dataset
某 inbound source evidence 含：promised_date、expected_arrival_date
Adapter 最终解析：canonical effective_arrival_date = 2026-10-10
```

如果 provenance 只记录 **`Package P1` ＋ `Inbound dataset`**，则**无法回答**：

- 为什么最终是 `2026-10-10`？
- 来自**哪一份** source evidence？
- 依据**哪一个 approved mapping basis**？

**结论：dataset-level provenance reference 本身不足以支撑已有的
`explicit` ／ `deterministic` ／ `traceable` ／ `reproducible` 约束。**

**Critical Scenario B —— Mapping Evidence**

```
Supplier source vocabulary：ACTIVE
经 approved source-specific mapping：ACTIVE → eligible
形成 canonical：Supplier Eligibility = eligible
```

必须能够追溯：

```
source evidence → source value → mapping basis
  → canonical eligibility outcome → Snapshot Package
```

**但不得因此创建 global source vocabulary enum**（**§4.5.11** 边界保持不变）。

**Critical Scenario C —— Derived Result**

```
某 Procurement Recommendation：RecommendedPurchaseQty = 100
```

必须能够回答它属于哪个 **Analysis Run**，并能经 deterministic chain 追溯到
`ShortageQty` ／ `ApplicableMOQ` ／ Production Requirement ／ BOM ／ Inventory ／
Inbound ／ Substitute evidence 等。

**但不得要求每一个 derived value 复制全部 source provenance metadata。**

**结论：** 通过 **Analysis Run ＋ deterministic Rule ＋ upstream canonical references**
**足以**重建 derivation（见 **Derived Result Provenance**）。

**Critical Scenario D —— Cross-Package Mismatch**

```
Analysis Run R1 绑定 Snapshot Package P1
Material mapping evidence 却引用 Package P2
```

必须继续产生 **`PROVENANCE` ／ `PROVENANCE_MISMATCH`**。

**因此 carrier contract 必须至少能够判断：某 evidence reference 属于哪个 Snapshot Package。**

**Interpretation of the Existing Unresolved Item（关键澄清）**

当前登记的 `provenance carrier` unresolved 实际**混含两个不同问题**：

| | 问题 | 归属 |
| --- | --- | --- |
| **A** | **Canonical / logical carrier contract 未定义** | **本 Review 回答** |
| **B** | **Physical serialization carrier 未定义** | **不属于本 Review** —— 属 **§4.3 Field Carrier Mapping ／ Final Import Contract** |

**本 Review 的判断：** 该 unresolved 项的**真实含义是 A**（logical contract）。
**不得**因为 **CSV / JSON / DB 格式尚未决定**就永久阻塞 `Master Data Mapping`；
**但也不得**虚假声称 **physical import design 已完成**。

**Logical vs Physical Carrier（必须严格区分）**

```
Logical carrier contract   = 本 Review 定义（provenance role / layer / invariant）
Physical carrier           = serialization / file layout / field carrier mapping
                             → 仍属 §4.3 后续设计，仍 DESIGN PENDING
```

**Option Review**

| Option | 内容 | 判定 |
| --- | --- | --- |
| **0** | Keep `provenance carrier` `DESIGN PENDING` | **安全但非终点** —— `Mapping Provenance Requirement` 只有原则、没有最小承载方式，traceability **无法形成可执行设计** |
| **A** | **Package-Level Only**（只用 `snapshot_package_id`） | **不足，且相对既有要求是退步** —— 无法回答「哪个 logical dataset／哪份 source evidence／哪个 mapping basis／同 dataset 多条记录如何区分」；**§4.3.16** 已要求 dataset role |
| **B** | **Package ＋ Dataset-Level Provenance** | **必要但不充分** —— 它是 Option D 的**前置层**；**Critical Scenario A** 证明 dataset-level 无法解释 `effective_arrival_date = 2026-10-10` 的**来源与理由**；`effective_arrival_date` ／ `loss_rate` ／ `ApplicableMOQ` ／ Supplier eligibility ／ allocation applicability 都可能需要**更细 evidence**。若只能定位整个 dataset，**不得声称完整解决** |
| **C** | **Mandatory New Record-Level IDs**（`source_record_id` ／ `trace_id` ／ `lineage_id`） | **拒绝** —— 属 **physical schema invention**；当前**无真实 ERP / export schema evidence**；**没有证据不得采用** |
| **D** | **Layered Logical Provenance Contract** | **推荐方向**（见下） |
| **E** | **Full Lineage Graph / Lineage Database**（node/edge graph ／ lineage DB ／ OpenLineage-like ／ event log） | **拒绝纳入当前 canonical design** —— 属 **implementation option**，当前 POC **无必要性证据** |

**Recommended Direction —— Option D（Layered Logical Provenance Contract）**

```
Snapshot Package Identity
        ↓
Logical Dataset Role
        ↓
Stable Source Evidence Locator
        ↓
Mapping / Resolution Basis            （when applicable）
        ↓
Canonical Fact / Relationship
        ↓
Analysis Run
        ↓
Derived Result / Recommendation
```

各层复用状态：

| 层 | 状态 |
| --- | --- |
| **`snapshot_package_id`** | **已存在**（**§4.3.3**） |
| **logical dataset role** | **已存在**（**§4.3.10**） |
| **Stable Source Evidence Locator** | **本 Review 提出**（conceptual provenance role） |
| **Mapping / Resolution Basis** | **本 Review 提出**（conceptual provenance role） |
| **Analysis Run** | **已存在**（**§4.3.4**） |

**Stable Source Evidence Locator（谨慎定义）**

**语义：**

> 在当前 **immutable Snapshot Package** 内，能够**稳定重新定位**支撑当前
> canonical observation ／ relationship ／ policy input 的 **source evidence**。

**必须具备：**

```
stable within package
reproducible
package-scoped
source-specific
```

**不得要求它一定：**

- 全局唯一
- 跨 Package 不变
- 等于 ERP primary key
- 等于 canonical ID

**本 Review 不规定**它是 `row ID` ／ `primary key` ／ `file line` ／ `JSON pointer` ／
`composite business key` ／ `source record ID`。

**必须明确：**

```
Source Evidence Locator  ≠  Canonical Business Identity
```

**Dataset-Level Provenance Reference vs Source Evidence Locator（两层，不得混合）**

| 层 | 负责回答 |
| --- | --- |
| **dataset-level provenance reference**（**§4.3.8** 已要求） | 「**这整个 logical dataset** 来自哪里 / 哪份 evidence artifact」 |
| **Stable Source Evidence Locator**（本 Review 提出） | 「**dataset 内哪一份具体 evidence** 支撑当前 canonical value / relationship」 |

**不得把两者混为一层。**

**Mapping / Resolution Basis（正式角色）**

对以下**已批准**的 source-specific resolution contract，必须能够追溯
`source evidence ＋ mapping / resolution basis → canonical result`：

- Supplier eligibility（**§4.5.11**）
- `effective_arrival_date`（**§4.5.21**）
- allocation demand-window（**§4.5.9**）
- `loss_rate`（**§4.5.22 Option E**）
- `ApplicableMOQ`（**§4.5.22 Option D**）

**但不得要求 mapping basis 一定具有某个新 `mapping_rule_id` 字段。**
本轮只定义：**必须可稳定识别 / 重现**；**物理表达留给 implementation**。

**Mapping Basis vs Business Rule（不得混为一类）**

| | 例子 | provenance role |
| --- | --- | --- |
| **source semantic mapping basis** | `promised_date` → `effective_arrival_date` | **mapping / resolution basis** |
| **Business Rule calculation** | `RemainingInboundQty = ordered_qty - received_qty` | **deterministic Rule calculation** |

**Business Rule Identity Boundary：** 现有 **Rule IDs**（`BR-REQUIREMENT-001` ／
`BR-INVENTORY-001` ／ `BR-INBOUND-001` ／ `BR-SUBSTITUTE-001` ／ `BR-SHORTAGE-001` ／
`BR-PROCUREMENT-001` 等）**足以**作为 derived result 的 calculation basis **conceptual identifier**。

**不得**为了 provenance **创建新的 duplicate rule IDs**。

**Direct Source Facts**

如果 canonical value 只是 source evidence 的**直接语义映射**（例如 `on_hand_qty = 100`），
且**不经过**复杂 semantic resolution，**仍至少需要**追溯：

```
Snapshot Package
+ logical dataset role
+ source evidence locator
```

**不得**因为「直接 copy」就**完全没有 provenance**。

**Derived Result Provenance**

**Derived Result 不应复制所有 upstream source metadata。**

**可以**定义为：

```
derived result provenance
= Analysis Run identity
  + deterministic Rule / calculation identity
  + references to canonical inputs / contexts
```

然后由 **canonical inputs** 再各自追溯到 **source evidence**。

**不得创建**：每个 derived field 一个独立完整 lineage blob。

**Package Immutability Dependency（invariant）**

Option D 的可靠性建立在 **accepted Snapshot Package immutable** 这一**既有约束**上。

**必须明确 invariant：**

```
同一个 snapshot_package_id + 同一个 source evidence locator
  在 package acceptance 之后
 不得指向不同内容
```

否则 **provenance contract 失效**。

**只定义 invariant，不得设计 storage enforcement。**

**Cross-Package Rule**

任何 provenance reference **必须可以确定其 package scope**。

```
Analysis Run → P1
但 canonical input provenance → P2
且没有独立批准的 multi-package composition
        ↓
PROVENANCE_MISMATCH
```

**不得**自动 copy ／ remap ／ silently accept。

**Multiple Source Evidence（one-to-many）**

某一个 canonical fact **可能由多个 source evidence 共同支撑** ——
例如 `identity mapping` ＋ `relationship evidence` ＋ `policy evidence`。

**不得强制** exactly one source evidence per canonical fact。
carrier contract **必须支持 one-to-many provenance relation**。

**One Source Evidence → Multiple Canonical Outputs**

同一 source evidence **也可能产生多个** canonical fields / relations。

carrier contract **不得假定**：

```
one source row  =  one canonical fact
```

**但不得设计 graph database。**

**Provenance Completeness Boundary（何时足以称为 complete）**

**对于一个 canonical input**，必须能够回答：

| # | 问题 |
| --- | --- |
| 1 | 来自哪个 **Snapshot Package**？ |
| 2 | 属于哪个 **logical dataset role**？ |
| 3 | **哪份具体 source evidence** 支撑它？ |
| 4 | 如果发生 mapping，**使用什么 mapping / resolution basis**？ |
| 5 | 当前 canonical observation 属于哪个 **Analysis / business context**？ |

**对于一个 derived result**，必须能够回答：

| # | 问题 |
| --- | --- |
| 1 | 属于哪个 **Analysis Run**？ |
| 2 | 由哪个 **deterministic Rule / calculation** 产生？ |
| 3 | 使用了哪些 **canonical upstream inputs / contexts**？ |
| 4 | upstream inputs **各自能否继续追溯到 source evidence**？ |

**Provenance Missing vs Mismatch ／ Validation Taxonomy Limitation**

| 情形 | 概念类别 |
| --- | --- |
| **A** provenance reference **缺失** | 视缺失对象而定 —— 若 **required evidence role 本身未提供** → **`EVIDENCE_ROLE_NOT_PROVIDED`**；若 **canonical field value 缺失** → **`FIELD_VALUE` ／ `MISSING`** |
| **B** provenance reference **存在**，但指向**错误 Package / Analysis Context** | **`PROVENANCE` ／ `PROVENANCE_MISMATCH`** |

> **Validation Taxonomy Limitation（本 Review 报告，不自行新增 reason）：**
>
> 「**evidence 存在**，但其 **provenance reference 缺失 ／ package scope 无法确定**」
> 这一情形，当前 **`PROVENANCE_MISMATCH` 无法精确表达** ——
> 因为该 reason 的语义是 **mismatch**，不是 **absence**。
>
> 本 Review **不新增** `PROVENANCE_MISSING` ／ `LINEAGE_MISSING`，
> 也**不**重定义现有 reason。该 **taxonomy limitation 进入 Human Attention**。

**Structural vs Business Provenance（不得误分类）**

```
Snapshot Manifest / artifact integrity
        → PACKAGE_STRUCTURE

canonical fact / derived result 引用了不属于当前 Analysis Context 的 evidence
        → PROVENANCE
```

**不得**把 **artifact missing** 错误归到 **`PROVENANCE_MISMATCH`**。

**Carrier vs Business Field（边界）**

`provenance carrier` 属于 **transport / provenance metadata**，
**不是** canonical business field。

**不得**把它加入 **`§4.2` Canonical Data Dictionary** 作为
`plant_id` ／ `material_code` ／ `supplier_id` 同类字段。
**不得**修改任何 canonical entity grain。

**Canonical Model Compatibility Result**

推荐方向 **Option D** 的判定：

```
Canonical Model Compatibility = COMPATIBLE
```

依据 —— 它可作为 **transport / provenance metadata contract**，
并**复用**：Snapshot Package（**§4.3.3**）／ Snapshot Manifest（**§4.3.8**）／
Analysis Run（**§4.3.4**）／ logical dataset role（**§4.3.10**）／ existing Rule IDs。

| 需要表达的内容 | 现有 Canonical Model |
| --- | --- |
| package scope | **已有**（`snapshot_package_id`） |
| dataset / evidence role | **已有**（logical dataset role ＋ dataset-level provenance reference） |
| canonical applicability / observation context | **已有**（各 entity grain ＋ Analysis Run） |
| calculation basis | **已有**（existing Rule IDs） |
| source evidence 定位 | **本 Review 提出 conceptual role**（不新增 persisted field） |
| mapping basis 识别 | **本 Review 提出 conceptual role**（不新增 persisted field） |

**而无需**：新增 canonical business entity ／ 新增 canonical business field ／ 修改 entity grain。

**同时必须明确（不得模糊）：** 如果必须把 **`trace_id` ／ `source_record_id` ／ `lineage_id`**
**加入 canonical entities** 才能满足现有 provenance requirement，
则 **`Canonical Model Compatibility = INSUFFICIENT`** —— 本 Review **不推荐**该形式。

**Snapshot / Import Contract Boundary**

`§4.3 Snapshot / Import Contract` **overall 仍为 `DESIGN PENDING`**，其中：

```
Serialization Format        = DESIGN PENDING
Physical Dataset Layout     = DESIGN PENDING
Field Carrier Mapping       = DESIGN PENDING
Final Import Contract       = DESIGN PENDING
```

**因此：** 本 Review **不得**为了关闭 `Master Data Mapping` 的 `provenance carrier`
而**顺手完成 physical import contract**。

**判断：** **logical provenance carrier contract 可以先 `DESIGN RESOLVED`**，
同时 **physical carrier realization 仍留在 `§4.3` 后续实现设计**。
两者**不得互相替代**。

**Master Data Mapping Closure Assessment（不宣布 closure）**

**本 Review 明确不宣布任何 closure。** 仅给出评估：

| 问题 | 评估 |
| --- | --- |
| 定义 logical provenance carrier contract 后，能否关闭 `Other Source-Semantic Mapping` 中最后的 `provenance carrier`？ | **可以**（若 Option D 获批准并实施）→ `unresolved count` 将 **1 → 0**，`Other Source-Semantic Mapping` 可随之 **`DESIGN RESOLVED`** |
| `Final Master Data Mapping` 是否也可因此 `DESIGN RESOLVED`？ | **不能自动推断** —— 当前 Design 中 **`Final Master Data Mapping` 仅有层级登记，没有任何 closure criteria 定义**（全文仅在层级状态表中出现）。它构成**独立于 `provenance carrier` 之外的 closure gate** |
| `Master Data Mapping` overall 是否可 `DESIGN RESOLVED`？ | **本 Review 不判断** —— 存在上述**独立 gate**，**必须由 Human 决定** |

**必须明确：** 即使 `unresolved count` 变为 `0`，也**不等于** `Master Data Mapping` overall
可以自动 closure。**不得自动宣布 closure。**

**Do Not Close `§4.3`**

即使 `Master Data Mapping` 未来可以 closure，**必须保持**：

```
Snapshot / Import Contract overall = DESIGN PENDING
```

除非其自己的 `Serialization Format` ／ `Physical Dataset Layout` ／
`Field Carrier Mapping` ／ `Final Import Contract` **分别完成**。

**不得**把 **`Master Data Mapping` complete** 偷换成 **`Import Contract` complete**。

**Known Risks（本 Review 识别，未消除）**

| # | Risk | 说明 | 当前状态 |
| --- | --- | --- | --- |
| 1 | **Physical carrier 仍未定义** | logical contract 与 physical realization 分离；后者属 `§4.3` | **未消除** —— `Field Carrier Mapping` ／ `Final Import Contract` 仍 `DESIGN PENDING` |
| 2 | **Locator 依赖 package immutability** | 若 accepted package 内容可变，locator 语义失效 | **已设 invariant** —— 只定义不变量，不设计 enforcement |
| 3 | **`PROVENANCE_MISMATCH` 无法表达 absence** | taxonomy limitation | **已报告** —— 进入 Human Attention，**未新增 reason** |
| 4 | **`Final Master Data Mapping` closure criteria 未定义** | 构成独立 closure gate | **未消除** —— 本 Review **不**判断 overall closure |
| 5 | **无真实 ERP / export schema evidence** | 不得声称真实 carrier 形式 | **未消除** —— Option C 因此被拒绝 |
| 6 | **Multi-package composition 未批准** | 默认禁止 silent cross-snapshot mixing | **已设边界** —— `§4.3.7` 保持不变 |

**Status（本 Review 时点）**

```
Mapping Provenance Requirement        = DESIGN RESOLVED   ← 未变
Snapshot Package identity             = DESIGN RESOLVED   ← 未变
Analysis Run → exactly one Package    = DESIGN RESOLVED   ← 未变
PROVENANCE / PROVENANCE_MISMATCH      = DESIGN RESOLVED   ← 未变
provenance carrier                    = DESIGN PENDING    ← 未变
unresolved count                      = 1                 ← 未变
Other Source-Semantic Mapping         = DESIGN PENDING    ← 未变
Final Master Data Mapping             = DESIGN PENDING    ← 未变
Master Data Mapping overall           = DESIGN PENDING    ← 未变
Snapshot / Import Contract overall    = DESIGN PENDING    ← 未变
```

本 Review **不**实施任何 Option、**不**新增 canonical field ／ entity、
**不**修改 grain、**不**新增 Validation Reason、**不**宣布任何 closure。

**Human Decision Required**

1. 是否接受 **`Canonical Model Compatibility = COMPATIBLE`**？
2. 是否采用 **Option D（Layered Logical Provenance Contract）**？
3. 是否确认 **minimum provenance layers** ——
   `Snapshot Package Identity` ＋ `Logical Dataset Role` ＋ `Stable Source Evidence Locator`
   ＋ `Mapping / Resolution Basis`（when applicable）＋ `Analysis Run linkage`？
4. 是否确认 **`Source Evidence Locator` ＝ package-scoped conceptual locator
   ≠ canonical business ID ≠ required ERP primary key**？
5. 是否确认 **derived results 通过 `Analysis Run` ＋ deterministic Rule ＋
   upstream canonical references 形成 provenance，不复制全部 upstream metadata**？
6. 是否确认 **logical provenance carrier resolved ≠ physical serialization /
   Field Carrier Mapping resolved**？
7. 是否授权 **`§4.2` / `§4.3` / `§4.4` / `§4.5`** 必要的最小 consistency synchronization？

**Validation Taxonomy Limitation（单独列出，不得自行加 reason）**

> 「evidence 存在但 **provenance reference 缺失 ／ package scope 无法确定**」
> 当前**无法**由 **`PROVENANCE_MISMATCH`** 精确表达。
> 本 Review **不自行新增** reason，**不重定义**现有 reason ——
> 请 Human 决定处理方式（确认沿用现有 reason 并记录语义扩展，
> 或另行授权新的 Design Change 评估 taxonomy）。

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 本节是对**上方 Review Finding** 的 **Human Decision**。
> 上方 Review Finding 中的 `Human Decision Required` 与「请 Human 决定处理方式」表述
> **已在本节获得答案**；未实施部分见本节末 **执行状态**。
>
> 上方 **Existing Provenance Baseline** ／ **Four-Layer Traceability** ／ **Critical Scenarios** ／
> **Option Review** ／ **Logical vs Physical Carrier** ／ **Provenance Completeness Boundary** ／
> **Validation Taxonomy assessment** ／ **Master Data Mapping Closure assessment** ／ **Known Risks**
> **全部保留，未删除、未改写**。

**决定 1 —— Canonical Model Compatibility = `COMPATIBLE`（ACCEPTED，附严格限定）**

接受：

```
Canonical Model Compatibility = COMPATIBLE
```

**严格限定于：**

```
Option D = Layered Logical Provenance Contract
```

即 `provenance carrier` 作为 **transport / provenance metadata contract** 存在，
**不是** canonical business entity ／ canonical business field ／ canonical identity component。

**如果未来必须把** `trace_id` ／ `source_record_id` ／ `lineage_id`
**加入 canonical business entities** 才能满足 traceability，
则当前 **`COMPATIBLE`** 结论**失效**，必须重新进入：

```
Canonical Model Compatibility Review
        +
Human-approved Canonical Model Amendment
```

**决定 2 —— Option D = APPROVED**

正式采用 **Layered Logical Provenance Contract**：

```
Snapshot Package Identity
        ↓
Logical Dataset Role
        ↓
Stable Source Evidence Locator
        ↓
Mapping / Resolution Basis（when applicable）
        ↓
Canonical Fact / Relationship
        ↓
Analysis Run
        ↓
Derived Result / Recommendation
```

该 contract 是当前 POC provenance 的**正式设计方向**。

**决定 3 —— Minimum Provenance Layers = APPROVED**

正式确认 minimum provenance layers：

1. **Snapshot Package Identity**
2. **Logical Dataset Role**
3. **Stable Source Evidence Locator**
4. **Mapping / Resolution Basis**（when applicable）
5. **Analysis Run linkage**

其中 **derived result** 还必须能够通过
`Analysis Run` ＋ `deterministic Rule` ＋ `upstream canonical references`
回溯到 upstream source evidence。

**不得**把所有 provenance 压缩成 `snapshot_package_id`。

**决定 4 —— Stable Source Evidence Locator = CONFIRMED**

正式批准 **`Stable Source Evidence Locator`** 是 **package-scoped conceptual locator**，
必须满足：

```
stable within accepted package
reproducible
package-scoped
source-specific
```

它用于在同一 **immutable Snapshot Package** 内**稳定重新定位**支撑某
canonical fact ／ relationship ／ policy input 的 **source evidence**。

**必须明确：**

```
Source Evidence Locator  ≠  Canonical Business Identity
Source Evidence Locator  ≠  required ERP primary key
Source Evidence Locator  ≠  globally unique ID
Source Evidence Locator  ≠  cross-package stable identity
```

本 Design **不规定**它物理上是 `row ID` ／ `primary key` ／ `file line` ／
`JSON pointer` ／ `composite business key` ／ `source_record_id`。

**决定 5 —— Dataset-Level vs Evidence-Level Provenance = 两层（CONFIRMED）**

| 层 | 回答 |
| --- | --- |
| **dataset-level provenance reference** | 「**整个 logical dataset** 来自哪里 / 哪份 artifact？」 |
| **Stable Source Evidence Locator** | 「**dataset 内哪份具体 evidence** 支撑当前 canonical value / relationship？」 |

**不得混为一层。**

**决定 6 —— Mapping / Resolution Basis = CONFIRMED**

对于发生 semantic mapping / resolution 的 canonical input，**必须能够识别**
使用了哪个 **approved mapping / resolution basis**。例如：

```
source date evidence     → effective_arrival_date
source status            → supplier eligibility
source purchasing policy → ApplicableMOQ
```

**不得要求** mapping basis 一定具有新 `mapping_rule_id` persisted field。
**只要求：能够稳定识别并可重现 mapping decision。**

**决定 7 —— Derived Result Provenance = CONFIRMED**

`derived result provenance` 通过：

```
Analysis Run identity
+ existing deterministic Business Rule ID
+ references to upstream canonical inputs / contexts
```

形成。例如 `RecommendedPurchaseQty` 可以通过
`Analysis Run` ＋ `BR-PROCUREMENT-001` ＋ `ShortageQty` reference ＋ `ApplicableMOQ` reference
继续向上追溯。

**不得**把全部 upstream source metadata 复制到每个 derived value。

现有 `BR-REQUIREMENT-001` ／ `BR-INVENTORY-001` ／ `BR-INBOUND-001` ／
`BR-SUBSTITUTE-001` ／ `BR-SHORTAGE-001` ／ `BR-PROCUREMENT-001` 等 **Rule IDs 足以**作为
**calculation basis conceptual identifiers**；**不得创建 duplicate Rule IDs**。

**决定 8 —— Package Immutability Dependency = CONFIRMED**

`logical provenance contract` 依赖既有 invariant：

```
Accepted Snapshot Package = immutable
```

同一个 `snapshot_package_id` ＋ `Stable Source Evidence Locator`，
在 Package acceptance 后**不得指向不同内容**；否则 **provenance contract 失效**。

**本 Design 不规定 storage enforcement。**

**决定 9 —— Cross-Package Boundary = CONFIRMED**

正式保持：

```
Analysis Run → exactly one accepted Snapshot Package
```

如果 `Analysis Run → P1`，但某 canonical input ／ mapping evidence provenance → `P2`，
且**没有**另行批准的 **multi-package composition**：

```
→ PROVENANCE / PROVENANCE_MISMATCH
```

**不得** silent copy ／ silent remap ／ silent accept。

**决定 10 —— One-to-Many / Many-to-One = CONFIRMED**

provenance contract **必须支持**：

```
多个 source evidence → 一个 canonical fact
一个 source evidence → 多个 canonical outputs
```

**不得假定** `one source row = one canonical fact`。

**但不得因此设计** `graph database` ／ `lineage DB` ／ `node / edge schema`。

**决定 11 —— Provenance Completeness Boundary = CONFIRMED**

**对于 canonical input**，`provenance complete` 至少意味着能够回答：

| # | 问题 |
| --- | --- |
| 1 | 来自哪个 **Snapshot Package**？ |
| 2 | 属于哪个 **logical dataset role**？ |
| 3 | **哪份具体 source evidence** 支撑？ |
| 4 | 如果发生 semantic mapping，**使用什么 mapping / resolution basis**？ |
| 5 | 当前 canonical observation 属于哪个 **Analysis / business context**？ |

**对于 derived result**，`provenance complete` 至少意味着能够回答：

| # | 问题 |
| --- | --- |
| 1 | 属于哪个 **Analysis Run**？ |
| 2 | 由哪个 **deterministic Rule** 产生？ |
| 3 | 使用了哪些 **upstream canonical inputs / contexts**？ |
| 4 | upstream inputs 是否**继续可追溯**到 source evidence？ |

**决定 12 —— Logical Carrier ≠ Physical Carrier = CONFIRMED**

正式确认：

```
logical provenance carrier resolved  ≠  physical serialization resolved
logical provenance carrier resolved  ≠  §4.3 Field Carrier Mapping resolved
logical provenance carrier resolved  ≠  Final Import Contract resolved
```

**因此未来允许：** `provenance carrier = DESIGN RESOLVED`
**同时** `Snapshot / Import Contract overall = DESIGN PENDING`。

**不得**因为 CSV / JSON / DB 尚未决定就**永久阻塞** `Master Data Mapping` 的
**logical provenance design**；**同样不得虚假声称** physical import design 已完成。

**决定 13 —— Validation Taxonomy Decision：DO NOT EXTEND `PROVENANCE_MISMATCH`**

针对本 Review 报告的 **Validation Taxonomy Limitation**，正式决定：

```
DO NOT EXTEND PROVENANCE_MISMATCH
```

**原因：** `PROVENANCE_MISMATCH` 的语义是
「**reference exists but points to wrong / incompatible provenance context**」；
而「**evidence exists but required provenance reference is absent**」
属于**不同 root condition**。

**不得把 absence 伪装成 mismatch。**

**同时：** 本 PR **不新增** `PROVENANCE_MISSING` ／ `LINEAGE_MISSING` 等 reason。

**决定 14 —— Separate Validation Taxonomy Review = AUTHORIZED**

正式授权创建**独立**的 **Validation Taxonomy Design Review**，专门评估：

```
evidence exists
+ required provenance reference absent
/ package scope cannot be established
```

应如何进入现有 taxonomy。该 Review **必须评估**：

| Option | 内容 |
| --- | --- |
| **0** | 保持 taxonomy 不变，由 **higher-level readiness gate** 表达该问题 |
| **A** | 复用已有 reason，但**不改变原语义** |
| **B** | 新增 canonical reason：`PROVENANCE_MISSING` 或**其他更准确**的 reason |
| **C** | 调整 `PROVENANCE` category，使其区分 **missing provenance** vs **mismatch provenance** |

**不得在 PR #44 直接选择或实施。**
在该独立 Review 完成前，现有 **`PROVENANCE_MISMATCH` 语义保持不变**。

**决定 15 —— Structural vs Business Provenance = CONFIRMED**

必须继续保持：

```
Manifest / artifact integrity problem
        → PACKAGE_STRUCTURE

canonical fact / derived result 引用非当前 Analysis Context evidence
        → PROVENANCE / PROVENANCE_MISMATCH

evidence 本身存在，但 provenance reference 缺失
        → TAXONOMY GAP（pending separate Human-approved Review）
```

**不得**误分类为 `PACKAGE_STRUCTURE` ——
除非**真正发生** manifest / artifact structural inconsistency。

**决定 16 —— Minimal Consistency Synchronization = AUTHORIZED（授权边界）**

授权后续**专门 Design Change Task** 对 `§4.2` ／ `§4.3` ／ `§4.4` ／ `§4.5`
执行实施 **Option D** 所需的最小 consistency synchronization：

| 章节 | 授权内容 |
| --- | --- |
| **`§4.2`** | 同步 provenance metadata boundary；明确 `provenance carrier` **不是** canonical business field |
| **`§4.3`** | 同步 logical carrier contract；明确 **dataset-level provenance vs evidence-level locator**；**保持** `Serialization Format` ／ `Physical Dataset Layout` ／ `Field Carrier Mapping` ／ `Final Import Contract` **`DESIGN PENDING`** |
| **`§4.4`** | 同步 provenance completeness ／ cross-package behavior；**保留** `PROVENANCE_MISMATCH` 原语义；明确 **taxonomy gap 仍待独立 Review** |
| **`§4.5`** | 记录 **Option D Implementation Record**；同步 provenance carrier current status ／ unresolved count ／ `Other Source-Semantic Mapping` status |

**不得修改 `§2` Business Rules。**

**决定 17 —— provenance carrier Status After Implementation（条件性）**

**只有当** follow-up Option D **真正实施完成后**，才允许：

```
provenance carrier = DESIGN RESOLVED
unresolved count   = 1 → 0
Other Source-Semantic Mapping = DESIGN RESOLVED
```

（因其**最后一个 unresolved 已关闭**。）

**但不得自动关闭** `Final Master Data Mapping` 或 `Master Data Mapping overall`。

**决定 18 —— Final Master Data Mapping Closure Gate = CONFIRMED（NOT CLOSED）**

正式确认本 Review Finding 的结论：当前文档中的 **`Final Master Data Mapping`
只有 layer registration，没有明确 closure criteria**。

因此：

```
unresolved count = 0
  不自动意味着 Final Master Data Mapping = DESIGN RESOLVED

Other Source-Semantic Mapping = DESIGN RESOLVED
  也不自动意味着 Master Data Mapping overall = DESIGN RESOLVED
```

**决定 19 —— Separate Closure Review Required = AUTHORIZED**

在 provenance Option D 实施完成后，**必须单独进行**
**Master Data Mapping Closure Review**，只回答：

1. `Identity Resolution Boundary` 是否完整？
2. `Relationship Resolution Boundary` 是否完整？
3. `Mapping Conflict / Failure Boundary` 是否完整？
4. `Mapping Provenance Requirement` 是否完整？
5. 所有 source-semantic unresolved 是否已关闭？
6. 是否仍存在**未登记的 canonical mapping gap**？
7. `Final Master Data Mapping` 的**最低 closure criteria** 是什么？
8. 是否满足这些 criteria？
9. 是否允许 `Final Master Data Mapping = DESIGN RESOLVED`？
10. 是否允许 `Master Data Mapping overall = DESIGN RESOLVED`？

**不得**在 provenance implementation Task **自动宣布 overall closure**。

**决定 20 —— Snapshot / Import Contract Boundary = CONFIRMED**

无论 `Master Data Mapping` 未来是否 closure：

```
Snapshot / Import Contract overall = DESIGN PENDING
```

**直到**其自身 `Serialization Format` ／ `Physical Dataset Layout` ／
`Field Carrier Mapping` ／ `Final Import Contract` **分别完成**。

```
Master Data Mapping closure  ≠  Import Contract closure
```

**决定 21 —— Explicitly Not Authorized**

本 Human Decision **不授权**：

- `trace_id` ／ `lineage_id` ／ `source_record_id` ／ `mapping_rule_id`
- provenance table ／ lineage DB ／ graph database
- JSON lineage blob ／ metadata physical schema ／ `manifest.json`
- CSV provenance column ／ filesystem layout
- OpenLineage ／ data catalog ／ event bus
- Adapter implementation ／ test ／ fixture ／ ADR ／ technology choice
- new Validation Reason
- redefine `PROVENANCE_MISMATCH`
- `Final Master Data Mapping` closure
- `Master Data Mapping overall` closure

**执行状态（PR #44 时点）**

```
Canonical Model Compatibility       = COMPATIBLE（Option D only）
Option D                            = APPROVED
Layered Logical Provenance Contract = APPROVED
minimum provenance layers           = APPROVED
Stable Source Evidence Locator      = package-scoped conceptual locator
Source Evidence Locator             ≠ canonical business identity / ERP PK / global ID
derived provenance                  = Analysis Run + deterministic Rule + upstream refs
logical carrier                     ≠ physical serialization / Field Carrier Mapping
minimal §4.2/§4.3/§4.4/§4.5 sync    = AUTHORIZED
PROVENANCE_MISMATCH semantic        = UNCHANGED
Validation Taxonomy Limitation      = OPEN / SEPARATE DESIGN REVIEW REQUIRED
no new Validation Reason            = CONFIRMED
Final Master Data Mapping           = NOT CLOSED
Master Data Mapping overall         = NOT CLOSED

Option D Implementation             = NOT YET EXECUTED
provenance carrier                  = DESIGN PENDING
unresolved count                    = 1
Other Source-Semantic Mapping       = DESIGN PENDING
Snapshot / Import Contract overall  = DESIGN PENDING
```

**本 PR 不实施 Option D。** 在 follow-up **Human-authorized Design Change** 完成前：

```
provenance carrier            = DESIGN PENDING
unresolved count              = 1
Other Source-Semantic Mapping = DESIGN PENDING
```

**须另行进行的独立 Review：**

```
1. Validation Taxonomy Design Review（决定 14）
     —— 可在本 PR 之后独立启动
2. Master Data Mapping Closure Review（决定 19）
     —— 须在 provenance Option D 实施完成后进行
```

**Option D Implementation Record（Human-authorized Design Change）**

**Human Authorization Source**

```
PR #44 Human Decision — Human-approved
  → Canonical Model Compatibility       = COMPATIBLE（Option D resolution-contract form only）
  → Option D                            = APPROVED
  → Layered Logical Provenance Contract = APPROVED
  → minimum provenance layers           = APPROVED
  → Stable Source Evidence Locator      = APPROVED
  → derived provenance contract         = APPROVED
  → logical carrier ≠ physical carrier  = CONFIRMED
  → PROVENANCE_MISMATCH semantic        = UNCHANGED
  → taxonomy limitation                 = SEPARATE REVIEW REQUIRED
  → minimal §4.2/§4.3/§4.4/§4.5 sync    = AUTHORIZED
```

**Implementation Result**

```
provenance carrier = DESIGN RESOLVED

through:
  Snapshot Package Identity
  + Logical Dataset Role
  + Stable Source Evidence Locator
  + Mapping / Resolution Basis
  + Analysis Run linkage
```

**Layered Logical Provenance Contract（正式落地）**

```
Snapshot Package Identity
        ↓
Logical Dataset Role
        ↓
Stable Source Evidence Locator
        ↓
Mapping / Resolution Basis（when applicable）
        ↓
Canonical Fact / Relationship
        ↓
Analysis Run
        ↓
Derived Result / Recommendation
```

**Layer 1 —— Snapshot Package Identity（复用，未修改）**

复用既有 **`snapshot_package_id`**；语义保持 **Import / Transport Context identity**，
**不是** canonical business identity。**未**创建 `provenance_package_id`。

**Layer 2 —— Logical Dataset Role（复用，未修改）**

继续使用既有 **logical dataset / evidence role**（**§4.3.10**）。

```
logical dataset role  ≠  CSV filename  ≠  table name  ≠  physical artifact path
```

**未**重新设计 physical file layout。

**Layer 3 —— Stable Source Evidence Locator（正式定义，conceptual）**

定义：在一个 **immutable accepted Snapshot Package** 内，能够**稳定重新定位**支撑某
canonical fact ／ relationship ／ policy input 的**具体 source evidence**。

必须满足：

```
stable within package
reproducible
package-scoped
source-specific
```

**必须明确：**

```
Source Evidence Locator  ≠  Canonical Business Identity
Source Evidence Locator  ≠  ERP primary key requirement
Source Evidence Locator  ≠  globally unique ID
Source Evidence Locator  ≠  cross-package stable ID
```

**不得规定**物理实现一定是 `row ID` ／ `primary key` ／ `file line` ／
`JSON pointer` ／ `composite key` ／ `source_record_id`。

**Dataset-level vs Evidence-level（两层同时存在，不得混为一个字段 / concept）**

| 层 | 回答 |
| --- | --- |
| **dataset-level provenance reference** | **整个 logical dataset** 来自哪里 / 哪个 artifact |
| **Stable Source Evidence Locator** | dataset 内**哪一份具体 source evidence** 支撑当前 canonical observation |

**Layer 4 —— Mapping / Resolution Basis（when applicable）**

对于发生 semantic mapping / resolution 的 canonical input，**必须能够稳定识别**
使用了什么 **approved mapping / resolution basis**，包括但不限于既有：

- Supplier eligibility mapping（**§4.5.11**）
- `effective_arrival_date` mapping（**§4.5.21**）
- Substitute allocation applicability（**§4.5.9**）
- `loss_rate` resolution（**§4.5.22 Option E**）
- `ApplicableMOQ` resolution（**§4.5.22 Option D**）
- Master Data identity / relationship mapping（**§4.5.3** ～ **§4.5.6**）

**不得要求** mapping basis 一定具有 persisted `mapping_rule_id`。
本 Task 只定义：**mapping basis must be identifiable and reproducible**。

**Mapping Basis ≠ Business Rule（正式区分）**

| | 例子 | 作用 |
| --- | --- | --- |
| **A. Mapping / Resolution Basis** | source `promised` / `expected` evidence → canonical `effective_arrival_date` | 解释 **source semantic** |
| **B. Deterministic Business Rule** | `RemainingInboundQty = ordered_qty - received_qty` | 计算 **canonical / derived business result** |

**不得混淆。**

**Derived Result Provenance（正式落地）**

```
Derived Result Provenance
= Analysis Run + Deterministic Rule ID
+ Upstream Canonical References / Contexts
```

例如 `RecommendedPurchaseQty` 可经
`Analysis Run R1` ＋ `BR-PROCUREMENT-001` ＋ `ShortageQty context` ＋ `ApplicableMOQ context`
继续向上追溯。

**不得**把全部 upstream provenance metadata 复制到每个 derived result。

**Existing Rule IDs（复用，未新增）**

`BR-REQUIREMENT-001` ／ `BR-INVENTORY-001` ／ `BR-INBOUND-001` ／ `BR-SUBSTITUTE-001` ／
`BR-SHORTAGE-001` ／ `BR-PROCUREMENT-001` 等既有 Rule IDs
**足以**作为 **deterministic calculation basis conceptual identifier**；
**未创建** duplicate calculation rule IDs。

**Direct Source Fact Provenance**

即使 canonical value 只是 source evidence 的**直接映射**（例如 `on_hand_qty = 100`），
**仍必须**至少能够追溯 `Snapshot Package` ＋ `Logical Dataset Role` ＋ `Stable Source Evidence Locator`。

**不得** `direct copy → no provenance`。

**Provenance Completeness —— Canonical Input**

一个 canonical input 的 provenance complete，**至少**表示能够回答：

1. 来自哪个 **Snapshot Package**？
2. 属于哪个 **logical dataset role**？
3. **哪份具体 source evidence** 支撑？
4. 如果发生 semantic mapping，**使用什么 mapping / resolution basis**？
5. 当前 canonical observation 属于哪个 **Analysis / business context**？

若上述必要信息**无法可靠回答**，**不得声称** `provenance complete`。

**Provenance Completeness —— Derived Result**

一个 derived result 的 provenance complete，**至少**表示能够回答：

1. 属于哪个 **Analysis Run**？
2. 由哪个 **deterministic Rule** 产生？
3. 使用了哪些 **upstream canonical inputs / contexts**？
4. upstream inputs 是否**继续可以追溯**到 source evidence？

**不得要求** derived result 复制全部 source metadata。

**Package Immutability Invariant（只定义 invariant）**

```
同一个 snapshot_package_id + 同一个 Stable Source Evidence Locator
  在 Package acceptance 之后
 不得指向不同内容
```

否则 **provenance contract 失效**。

**本 Task 未设计** storage enforcement ／ content-addressing ／ hash schema ／ database constraint。

**Cross-Package Boundary（保持）**

```
Analysis Run → exactly one accepted Snapshot Package
```

若 `Run R1 → Package P1`，但某 canonical input ／ mapping evidence provenance → `Package P2`，
且**没有**另行批准的 **multi-package composition**：

```
→ PROVENANCE / PROVENANCE_MISMATCH
```

**不得**：silent accept ／ silent remap ／ silent copy ／ cross-package fallback。

**One-to-Many / Many-to-One（保持）**

必须支持 `multiple source evidence → one canonical fact`
以及 `one source evidence → multiple canonical outputs`。

**不得**强制 `one canonical fact = exactly one source evidence`，
也**不得**假定 `one source row = one canonical field`。
**但不得因此设计** lineage graph DB。

**Logical Carrier ≠ Physical Carrier（保持）**

```
Logical Provenance Carrier = DESIGN RESOLVED
        ≠
physical carrier realization = resolved
```

未来 `CSV` ／ `JSON` ／ `DB` ／ file layout ／ record key representation 如何承载
`Stable Source Evidence Locator` ／ `Mapping Basis` ／ references，
**仍属** **§4.3 `Field Carrier Mapping` ／ `Final Import Contract`** 后续 Design。

**Validation Taxonomy Limitation（保持 OPEN）**

```
evidence exists
+ required provenance reference absent
/ package scope cannot be established
        → 当前 PROVENANCE_MISMATCH 无法精确表达
        → Validation Taxonomy Limitation = OPEN / SEPARATE REVIEW REQUIRED
```

**未**重定义 `PROVENANCE_MISMATCH`；**未**新增 `PROVENANCE_MISSING` ／ `LINEAGE_MISSING`；
**未**创建其他新 Reason。`PROVENANCE_MISMATCH` 原语义
（reference exists but points to wrong / incompatible provenance context）**保持不变**。

**Structural vs Business Provenance（保持）**

```
Manifest / artifact missing / integrity failure       → PACKAGE_STRUCTURE
canonical evidence 引用错误 Package / Analysis Context → PROVENANCE / PROVENANCE_MISMATCH
evidence 存在但 provenance reference 缺失              → Validation Taxonomy Gap（pending separate review）
```

**`§4.2` / `§4.3` / `§4.4` / `§4.5` Synchronization Result**

| 章节 | 同步内容 |
| --- | --- |
| **`§4.2`** | `§4.2.15` 同步 provenance metadata boundary 与 **Layered Logical Provenance Contract**；`§4.2.16` 关闭该 open item；明确 `provenance carrier` **不是** canonical business field，**未**加入 Data Dictionary field table |
| **`§4.3`** | `§4.3.8` ／ `§4.3.16` 补清 **Package Identity ＋ Logical Dataset Role ＋ Stable Source Evidence Locator ＋ Mapping / Resolution Basis** 的 conceptual relation；**保持** `Serialization Format` ／ `Physical Dataset Layout` ／ `Field Carrier Mapping` ／ `Final Import Contract` **`DESIGN PENDING`** |
| **`§4.4`** | `§4.4.93` 同步 provenance completeness ／ cross-package behavior ／ derived provenance ／ logical-vs-physical boundary；**保留** `PROVENANCE_MISMATCH` 原语义；**taxonomy gap 仍待独立 Review**；**未新增** Validation Reason |
| **`§4.5`** | 本节记录 Option D implementation；`§4.5.14` ／ `§4.5.22` ／ `§4.5.24` 同步 status 与 unresolved count |

**未修改 `§2` Business Rules**（**byte-semantically identical**）。

**Meaning of `DESIGN RESOLVED`**

`provenance carrier = DESIGN RESOLVED` **只**表示 **logical provenance carrier contract 概念设计完成**，
**不表示** real ERP source known ／ source table / field known ／ mapping config exists ／
Adapter implemented ／ physical carrier finalized ／ storage enforcement exists ／ tested ／ production-ready。

**执行状态（本 Task 完成时点）**

```
Human Decision                       = RECORDED
Option D                             = IMPLEMENTED
Layered Logical Provenance Contract  = IMPLEMENTED
provenance carrier                   = DESIGN RESOLVED
unresolved count                     = 1 → 0
Other Source-Semantic Mapping        = DESIGN RESOLVED
Final Master Data Mapping            = 仍 DESIGN PENDING
Master Data Mapping overall          = 仍 DESIGN PENDING
Snapshot / Import Contract overall   = 仍 DESIGN PENDING
Validation Taxonomy Limitation       = OPEN / SEPARATE REVIEW REQUIRED
```

**未新增**任何 Master Data Mapping layer —— `Other Source-Semantic Mapping` 是**既有层**，
本 Task 只关闭其**最后一个 internal unresolved item**。
`DESIGN RESOLVED` layer 数现为 **10**；`Final Master Data Mapping` **仍为 `DESIGN PENDING`**。

**NEXT REQUIRED DESIGN REVIEW**

```
1. Validation Taxonomy Review
     问题：evidence exists + required provenance reference missing /
           package scope cannot be determined 应如何进入 canonical taxonomy
     —— **Review Finding 已记录**（见本节 **Missing Provenance Reference —
        Validation Taxonomy Gap Design Review（Review Finding）**）；
        结论 **`Current Taxonomy Compatibility = INSUFFICIENT`**。
     —— **Human Decision 已记录**（见其后的 **Human Decision Record**）：
        **`PROVENANCE_UNRESOLVED` = APPROVED FOR IMPLEMENTATION**
        （Category = `PROVENANCE`）。
     —— **taxonomy implementation 已完成**（见其后的 **Validation Taxonomy
        Implementation Record**）：`Canonical Reasons` `11 → 12`；
        **`Validation Taxonomy Limitation` `OPEN` → `DESIGN RESOLVED`**。
     —— 本 Review Finding 与 Human Decision Record 中 `11` ／ `OPEN` 的表述
        **按其各自时点原样保留**，**不得**回写。

2. Master Data Mapping Closure Review
     —— **Review Finding 已记录**（见本节 **Master Data Mapping Closure Review（Review Finding）**）：
        `Q1` ～ `Q5` = **是**；`Q6` = **否**（未发现**未登记**的 canonical mapping gap）；
        但 **closure criteria 未满足**（`MC-1` 未满足、`MC-9` 部分未满足）。
     —— **BLOCKING gap：** `B-1`（`Final Master Data Mapping` 的 **scope 未定义**）／
        `B-2`（**closure criteria 未正式登记**）。
     —— **Human Decision 已记录**（见其后的 **Human Decision Record**）：
        `Final Master Data Mapping` 的 **scope = `HUMAN APPROVED FOR REGISTRATION`**；
        **`MC-1` ～ `MC-10`**（含**修正后的 `MC-9`**）**= `HUMAN APPROVED FOR REGISTRATION`**；
        **follow-up conditional closure = `AUTHORIZED`**。
     —— **scope ／ criteria registration 已完成**（见 **§4.5.25** 与
        **Final Master Data Mapping Closure Implementation Record**）；
        **`MC-1` ～ `MC-10` = 全部 `PASS`**，**new blocking canonical mapping gap = `NONE`**。
     —— 因此 **conditional closure gate = `PASS`**，closure 已执行：
        `Final Master Data Mapping` **现为 `DESIGN RESOLVED`**，
        `Master Data Mapping` overall **现为 `DESIGN RESOLVED`**。
     —— 本 Review Finding 与 Human Decision Record 中 `DESIGN PENDING` ／
        `NOT YET EXECUTED` 的表述**按其各自时点原样保留**，**不得**回写。
```

**Missing Provenance Reference — Validation Taxonomy Gap Design Review（Review Finding）**

**Review Question**

本 Review **只回答一个问题**：

> 当 **source / canonical evidence 本身存在**、但 **required provenance reference 缺失**
> （或因此无法确定该 evidence 属于哪个 Snapshot Package / Analysis provenance context）时，
> 现有 **Category ＋ Reason** taxonomy **是否足以准确表达该 gap**？

**不得直接修改 Final Canonical Reason Set；不得在本 PR 新增 reason。**

**Existing Taxonomy Baseline（完整复核，未改变）**

**§4.4.80 —— 8 个正式 Category：**

```
PACKAGE_STRUCTURE ／ EVIDENCE_AVAILABILITY ／ FIELD_VALUE ／ IDENTITY_RESOLUTION
SCOPE_COVERAGE ／ SEMANTIC_RESOLUTION ／ CONSISTENCY ／ PROVENANCE
```

**§4.4.81 —— 11 个正式 Reason（本 Review 未修改）：**

| # | Reason | Category |
| --- | --- | --- |
| 1 | `STRUCTURAL_INCONSISTENCY` | `PACKAGE_STRUCTURE` |
| 2 | `EVIDENCE_ROLE_NOT_PROVIDED` | `EVIDENCE_AVAILABILITY` |
| 3 | `MISSING` | `FIELD_VALUE` |
| 4 | `INVALID_TYPE` | `FIELD_VALUE` |
| 5 | `OUT_OF_DEFINED_RANGE` | `FIELD_VALUE` |
| 6 | `INVALID_DEFINED_STATUS` | `FIELD_VALUE` |
| 7 | `UNRESOLVED_IDENTITY` | `IDENTITY_RESOLUTION` |
| 8 | `UNRESOLVED_SCOPE` | `SCOPE_COVERAGE` |
| 9 | `SEMANTIC_UNRESOLVED` | `SEMANTIC_RESOLUTION` |
| 10 | `CONSISTENCY_CONFLICT` | `CONSISTENCY` |
| 11 | `PROVENANCE_MISMATCH` | `PROVENANCE` |

**明确：** 旧 interim seed list **不构成**第二套 canonical taxonomy，本 Review 不引用、不复活。

**Exact Gap Scenario（Case G1）**

```
Snapshot Package         = 已 ACCEPTED
required logical dataset role = 已提供
source evidence record   = 存在
canonical business value = 可读取

例如 Inventory evidence：
  plant_id      = Plant-A
  material_code = MAT-X
  on_hand_qty   = 100

但：
  Stable Source Evidence Locator /
  required package-scoped provenance reference = 缺失

因此：
  不能可靠证明该记录属于当前 accepted Package P1
```

**这不是** `artifact missing`，**也不是** `business field on_hand_qty missing`。

**Neighboring Condition Comparison（必须逐项证明不同）**

| 邻接情形 | 既有判定 | Case G1 是否适用 | 理由 |
| --- | --- | --- | --- |
| **A. PACKAGE_STRUCTURE** | `STRUCTURAL_INCONSISTENCY`（manifest 声明 Inventory included，但 artifact absent） | **不适用** | Case G1 中 **artifact / evidence 本身存在**；不得误归 `PACKAGE_STRUCTURE` |
| **B. EVIDENCE_AVAILABILITY** | `EVIDENCE_ROLE_NOT_PROVIDED`（Supplier Performance role 根本未提供） | **不适用** | Case G1 中 **logical evidence role 已提供** |
| **C. FIELD_VALUE** | `MISSING`（`SafetyStock` 字段本应存在但缺失） | **不可复用** | `§4.4.80` 已明确 `MISSING = 字段本应存在，但不存在`，且**不得**用于 valid absence ／ not applicable ／ dataset role not provided。Case G1 中 **business value 本身存在**，缺的是 **provenance metadata / reference** —— 复用会让 `SafetyStock missing` 与 `provenance reference missing` **共享一个过宽 reason**，构成 semantic distortion |
| **D. SCOPE_COVERAGE** | `UNRESOLVED_SCOPE`（dataset 存在，但无法确认 coverage 是否覆盖 Plant-A） | **不可复用** | 需判断 **business scope coverage** 与 **package provenance scope** 是否同一 root condition —— **不是**。`UNRESOLVED_SCOPE` 回答「这份 data 覆盖不覆盖当前分析范围」；Case G1 回答「这条 evidence **属于哪个 Package**」。**不得**只因为都含 "scope" 就自动复用 |
| **E. SEMANTIC_RESOLUTION** | `SEMANTIC_UNRESOLVED`（value 存在但业务语义无法解释） | **不适用** | Case G1 中 business semantic 可能**完全明确**，问题是 **provenance linkage 缺失** |
| **F. PROVENANCE** | `PROVENANCE_MISMATCH`（reference 存在，但 Run→P1 而 reference→P2） | **不适用** | Case G1 中 **reference 不存在 / package scope 无法建立**；**absence ≠ mismatch**（PR #44 Human Decision 已裁定） |
| （补充）`UNRESOLVED_IDENTITY` | identity 无法解析到 canonical identity | **不适用** | Case G1 中 `plant_id` / `material_code` **可解析** |

**结论：Case G1 与全部 11 个既有 reason 的 root condition 均不同。**

**Root-Cause Principle（Reason ≠ Outcome）**

Validation Reason 描述**最接近根因的失败条件**（即「**为什么** evidence 不可靠」），
**不是**「最终造成的能力失败」（`§4.4.82`）。

因此以下**均不得**作为新 Reason：

```
DATA_INCOMPLETE
CAPABILITY_UNAVAILABLE
REJECTED
UNUSABLE
```

**Missing vs Unresolvable vs Mismatch（P1 ～ P4）**

| # | 情形 | 判定 |
| --- | --- | --- |
| **P1** | provenance reference **完全缺失** | 见下 |
| **P2** | provenance reference **存在**，但**无法解析为 package-scoped evidence locator** | 见下 |
| **P3** | provenance reference **可以解析**，但对应**错误 Package / Analysis Context** | **`PROVENANCE` ／ `PROVENANCE_MISMATCH`**（已明确，**不变**） |
| **P4** | provenance metadata **存在**，但**不完整到无法建立 package scope** | 见下 |

**判断：P1 ／ P2 ／ P4 应共享同一个 Reason。**

理由：三者的 root condition 在语义上**同属一类** ——
「**required provenance linkage 无法可靠建立**」；
区别只在**表现形式**（完全缺失 ／ 存在但无法解析 ／ 不完整），
而**不是**不同的失败根因。为三者各设一个 reason 会造成 **reason explosion**，
与 `§4.4.81` 的「不得引入 catch-all」精神及本 Task 的「优先避免 reason explosion」要求相悖。

**P3 与它们的分界是根本性的：** P3 的 linkage **已经建立**，只是**指向了错误的 context** ——
所以 P3 保持 `PROVENANCE_MISMATCH`，而 P1 ／ P2 ／ P4 需要一个**并列**的 reason。

**Provenance Completeness Impact**

继承 **PR #45**：canonical input `provenance complete` 至少能回答——

```
1. Snapshot Package
2. Logical Dataset Role
3. specific Source Evidence
4. Mapping / Resolution Basis（when applicable）
5. Analysis / business context
```

**逐层缺失的判定：**

| 缺失层 | root condition | 应使用 |
| --- | --- | --- |
| **Layer 2 —— logical evidence role 本身未提供** | evidence availability | **`EVIDENCE_ROLE_NOT_PROVIDED`**（已明确，**不新增**） |
| **Layer 1 / Layer 3 / Layer 4 / Layer 5 缺失**，或 **linkage 无法可靠建立** | provenance linkage 无法建立 | **本 Review 建议的同一个新 provenance reason** |

**判断：** 除「evidence role 本身未提供」这一既有情形外，
**其余任一 required provenance layer 缺失都共享同一个 reason** ——
**优先避免 reason explosion**；**不**按 layer 拆分多个 reason。

**Dataset-Level Reference Boundary**

`dataset-level provenance reference` **存在**，但**具体 `Stable Source Evidence Locator` 缺失**时，
**仍可能无法达到 canonical input `provenance complete`**。

**不得**因为 dataset-level provenance reference 存在就宣布 **provenance valid**。

**Evidence Locator Boundary（不重开 semantic design）**

继承 **PR #45** 已正式采用的 **`Stable Source Evidence Locator`**（package-scoped conceptual locator）：

| 情形 | 归属 |
| --- | --- |
| Locator **缺失** | **provenance taxonomy** |
| Locator **存在但无法解析** | **provenance taxonomy** |
| Locator **正确解析**，但与当前 Analysis Run 的 Package **不一致** | **`PROVENANCE_MISMATCH`** |

**本 Review 不重开** `Stable Source Evidence Locator` 的 semantic design。

**Derived Result Scenario**

```
RecommendedPurchaseQty = 100
Analysis Run           = 存在
BR-PROCUREMENT-001     = 存在
但 upstream ShortageQty reference 缺失
  → 无法从 recommendation 追溯到 upstream canonical input
```

**结论：该场景与「source evidence provenance reference missing」应使用同一个 canonical Reason。**

理由：两者的 root condition 相同 ——「**required provenance linkage 无法可靠建立**」，
只是一个发生在 **source → canonical fact** 方向，另一个发生在 **derived → upstream canonical input** 方向。
**方向不同不构成不同根因。**

**不得**为此新增 `DERIVATION_LINEAGE_MISSING` ／ `UPSTREAM_REFERENCE_MISSING` 等细碎 reason ——
**无充分必要性**。

**Package Acceptance Boundary（Failure Isolation）**

**`provenance reference` missing 不得必然导致整个 Snapshot Package `REJECTED`。**

必须继续遵守既有 **Failure Isolation** ＋ **minimum blast radius**：

如果问题只影响

```
一条 canonical fact ／ 一个 relationship ／ 一个 derived result ／ 一个 capability
```

则**只**在对应范围形成 Validation Issue。

**只有**当 **package-level provenance integrity 无法信任**
且**现有 Design 支持** structural / package consequence 时，才允许升级更大范围。

**Blast Radius & Business Outcome Mapping**

新 reason（若被采用）必须能配合既有 **Issue Impact** 表达（`§4.4.79`）：

```
Dataset ／ Record / Field ／ Relationship ／ Canonical Grain ／ Analysis Run ／ Capability
```

**不得新增** `HIGH` ／ `MEDIUM` ／ `LOW` severity。

**Business Outcome 影响（既有路径，不新增分类）：**

| 场景 | 后果 |
| --- | --- |
| Shortage calculation 必需的 Inventory evidence provenance 无法建立 | affected grain → **`DATA_INCOMPLETE`**（**不是**整个 Package 自动失败） |
| Supplier Risk 的某条 evidence provenance 无法建立 | 只影响对应 Risk capability / evidence scope |

**不得创建**新的 Business Classification `PROVENANCE_ERROR`。

**AI Explanation Boundary**

如果 AI Explanation 引用一个**没有可靠 provenance linkage** 的事实，
**不得**把它作为 **Evidence** 输出。

必须保持 **No Unsupported Fact** ＋ **Evidence Fidelity**。

**本 Review 只判断 taxonomy，不修改 AI / Tool Boundary。**

**Option Review**

| Option | 内容 | 判定 |
| --- | --- | --- |
| **0** | Keep Taxonomy Gap Open（不生成 canonical Validation Issue，只由 readiness / validation gate 阻止使用） | **安全但不可接受为终点** —— 见下 |
| **A** | Reuse `FIELD_VALUE` ／ `MISSING` | **拒绝** —— 与 `§4.4.80` `MISSING` 既有定义冲突；会让 `SafetyStock missing` 与 `provenance reference missing` 共享过宽 reason |
| **B** | Reuse `SCOPE_COVERAGE` ／ `UNRESOLVED_SCOPE` | **拒绝** —— root cause 不同（business coverage vs provenance linkage）；不得仅因最终「scope unknown」就误分类 |
| **C** | Reuse `PROVENANCE_MISMATCH` | **明确拒绝** —— 违反 **PR #44 Human Decision**「**DO NOT EXTEND `PROVENANCE_MISMATCH`**」 |
| **D** | Add New `PROVENANCE` Reason | **推荐**（命名见 Naming Review） |
| **E** | Split `PROVENANCE` into Two Reasons（`PROVENANCE_UNRESOLVED` ＋ `PROVENANCE_MISMATCH`） | **推荐（作为 Option D 的正式形式）** |

**Option 0 评估：** 优点是不改 taxonomy；**缺点**是一个明确的
**data quality / traceability failure 无法结构化记录**，直接影响：

- **audit** —— 无法记录「哪条 evidence、因何 provenance 原因未被采用」
- **blast radius** —— 无法表达 affected grain / capability
- **explanation** —— 无法向业务解释为何该 evidence 未被使用
- **reproducibility** —— 无法重现「同一 Package 下为何结果不同」

且与 `§4.4.90`「**不得只记录** `Data Quality Issue` 而**没有具体 reason**」及
`§4.4.79` 要求的 Issue dimensions **直接冲突**。

**Option D 与 Option E 的关系：** 二者实质相同（新增 **一个**、与 `PROVENANCE_MISMATCH` **并列**的
`PROVENANCE` reason）。**Option E 的表述更准确** —— 它把 `PROVENANCE` category 明确定义为
「**linkage 无法建立**」vs「**linkage 已建立但指向错误 context**」的**对称二分**，
从而覆盖 P1 ／ P2 ／ P4，而 `PROVENANCE_MISSING` 式的命名只能覆盖 P1。

**Option E 需检查的命名歧义：** `PROVENANCE_UNRESOLVED` 与既有
`SEMANTIC_UNRESOLVED` ／ `UNRESOLVED_SCOPE` ／ `UNRESOLVED_IDENTITY` 共享 `UNRESOLVED` 语素 ——
这**既是优点**（命名风格一致）**也是风险**（可能被误用）。
必须靠 **root condition 定义**区分：provenance linkage ≠ business semantic ≠ business scope ≠ identity。

**Naming Review**

| 候选名 | 准确覆盖 P1 | P2 / P4 | 过窄？ | 过宽？ | 命名风格 | 适用 source evidence ＋ derived lineage | 与既有 reason 混淆风险 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PROVENANCE_MISSING` | ✅ | ❌ **否** | **过窄** | 否 | 与 `MISSING` 同语素 | 否（derived lineage 不是 "missing"） | **高** —— 直接与 `FIELD_VALUE` ／ `MISSING` 混淆 |
| `PROVENANCE_REFERENCE_MISSING` | ✅ | ❌ **否** | **过窄** | 否 | 冗长 | 否 | **高** —— 仍含 `MISSING` |
| `UNRESOLVED_PROVENANCE` | ✅ | ✅ | 否 | 否 | 与既有 `UNRESOLVED_*` **词序相反** | ✅ | 中 —— 语素重叠但词序不同 |
| **`PROVENANCE_UNRESOLVED`** | ✅ | ✅ | 否 | 否 | 与 `PROVENANCE_MISMATCH` **前缀对称** | ✅ | 中 —— 需靠定义区分 `SEMANTIC_UNRESOLVED` |

**最终推荐：`PROVENANCE_UNRESOLVED`**

理由：

- **与 `PROVENANCE_MISMATCH` 对称** —— 同一 category 前缀 `PROVENANCE_`，语义二分清晰；
- **覆盖 P1 ／ P2 ／ P4** —— 「required provenance linkage 无法可靠建立」，
  **不**局限于「reference 不存在」；
- **对 source evidence 与 derived lineage 同样适用**；
- **不**含 `MISSING` 语素，**避免**与 `FIELD_VALUE` ／ `MISSING` 混淆；
- **不用** `UNRESOLVED_PROVENANCE` 的词序（与既有 `UNRESOLVED_IDENTITY` / `UNRESOLVED_SCOPE` 相反），
  避免让人以为它是 `UNRESOLVED_*` 家族的同构成员；
- 对未来实现足够稳定。

**Category Review**

**继续使用既有 `PROVENANCE` category，不创建新 Category。**

但必须明确一处**最小措辞问题**：`§4.4.80` 现有 `PROVENANCE` category 描述为
「evidence / derived result 来源上下文与当前 Analysis Context **不一致**」——
该措辞**只覆盖 mismatch**，**不完全覆盖**「无法建立」。
若 Human 批准新增 reason，则该 category 描述需要**最小扩宽**为
「…**不一致，或无法可靠建立**」。
**本 Review 不实施该修改**（属后续 authorized taxonomy synchronization）。

**Current Taxonomy Compatibility Result**

```
Current Taxonomy Compatibility = INSUFFICIENT
```

依据：**没有任何既有 reason 能准确表达 Case G1 的 root condition**，
且逐个复用均会造成 **semantic distortion**：

| 复用对象 | 造成的 distortion |
| --- | --- |
| `MISSING` | 把「provenance metadata 缺失」与「business field 缺失」混为一类 |
| `UNRESOLVED_SCOPE` | 把「package provenance scope」与「business scope coverage」混为一类 |
| `SEMANTIC_UNRESOLVED` | 把「provenance linkage 缺失」与「business semantic 无法解释」混为一类 |
| `PROVENANCE_MISMATCH` | 把 **absence** 伪装成 **mismatch**（已被 PR #44 Human Decision 明确禁止） |
| `EVIDENCE_ROLE_NOT_PROVIDED` | Case G1 中 role **已提供** |
| `STRUCTURAL_INCONSISTENCY` | Case G1 中 artifact **存在** |

**不得**因为「勉强能塞进去」就判 `SUFFICIENT`。

**Master Data Mapping Boundary**

本 Taxonomy Review **不关闭**：

```
Final Master Data Mapping  = 仍 DESIGN PENDING
Master Data Mapping overall = 仍 DESIGN PENDING
```

**也不定义** `Final Master Data Mapping` closure criteria ——
这些属于后续 **Master Data Mapping Closure Review**。

**Snapshot / Import Contract Boundary**

**不推进**：

```
Serialization Format ／ Physical Dataset Layout ／ Field Carrier Mapping ／ Final Import Contract
```

保持：

```
Snapshot / Import Contract overall = DESIGN PENDING
```

**Known Risks（本 Review 识别，未消除）**

| # | Risk | 说明 | 当前状态 |
| --- | --- | --- | --- |
| 1 | **`UNRESOLVED` 语素误用** | `PROVENANCE_UNRESOLVED` 与 `SEMANTIC_UNRESOLVED` ／ `UNRESOLVED_SCOPE` ／ `UNRESOLVED_IDENTITY` 可能被误用 | **已设边界** —— 必须靠 root condition 定义区分 |
| 2 | **Category 描述需最小扩宽** | `§4.4.80` `PROVENANCE` 现措辞只覆盖 mismatch | **已报告** —— 属后续 authorized synchronization |
| 3 | **reason count 由 11 → 12** | 唯一新增，非 explosion；但仍是 taxonomy 变更 | **待 Human Decision** |
| 4 | **既有 examples 可能受影响** | 实施时须检查既有 canonical examples 的 authoritative result 是否需同步 | **未评估** —— 本 Review **未修改**任何 example |
| 5 | **若选 Option 0** | audit ／ blast radius ／ explanation ／ reproducibility 缺口持续 | **未消除** |
| 6 | **不影响既有已解析设计** | 本 Review 不触碰 Warehouse ／ BOM ／ sourcing ／ arrival ／ allocation ／ `loss_rate` ／ `ApplicableMOQ` ／ provenance carrier 的既有决定 | **已设边界** |

**Status（本 Review 时点）**

```
§4.4.80 Canonical Issue Categories      = UNCHANGED（8 categories）
§4.4.81 Final Canonical Reason Set      = UNCHANGED（11 reasons）
PROVENANCE_MISMATCH semantic            = UNCHANGED
new canonical reason                    = NOT CREATED
Category Model                          = UNCHANGED
Validation Taxonomy Limitation          = OPEN
Final Master Data Mapping               = DESIGN PENDING
Master Data Mapping overall             = DESIGN PENDING
Snapshot / Import Contract overall      = DESIGN PENDING
```

本 Review **只记录 Review Finding**，**未**新增 reason ／ category，
**未**修改 reason count，**未**重命名 `PROVENANCE_MISMATCH`，
**未**修改任何既有 example 的 authoritative result，
**未**创建 error code ／ enum ／ API error object ／ test ／ schema。

**Human Decision Required**

1. 是否接受 **`Current Taxonomy Compatibility = INSUFFICIENT`**？
2. 是否接受 **provenance absence ／ unresolvable provenance linkage 需要独立 canonical Reason**？
3. 是否确认 **`PROVENANCE_MISMATCH` 保持原语义不变**（reference exists but wrong / incompatible context）？
4. 是否采用推荐的新 Reason 名称 **`PROVENANCE_UNRESOLVED`**
   （备选：`PROVENANCE_MISSING` ／ `PROVENANCE_REFERENCE_MISSING` ／ `UNRESOLVED_PROVENANCE`）？
5. 是否确认新 Reason 属于既有 **`PROVENANCE`** category（**不**创建新 Category）？
6. 是否确认 **missing / unresolved provenance ≠ `FIELD_VALUE` / `MISSING`
   ≠ `UNRESOLVED_SCOPE` ≠ `SEMANTIC_UNRESOLVED`**？
7. 是否授权后续 **`§4.4` 必要的最小 taxonomy synchronization**
   （含 `§4.4.80` category 描述的**最小扩辞**与 `§4.4.81` 新增第 12 个 reason）？

**若 Human 判定 `Current Taxonomy Compatibility = SUFFICIENT`**，
则**必须**明确复用哪一个既有 reason，并**证明不改变其既有 semantic**。

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 本节是对**上方 Review Finding** 的 **Human Decision**。
> 上方 Review Finding 中的 `Human Decision Required` 表述**已在本节获得答案**；
> 未实施部分见本节末 **执行状态**。
>
> 上方 **Existing Taxonomy Baseline** ／ **Exact Gap Scenario** ／ **Neighboring Condition Comparison** ／
> **Missing vs Unresolvable vs Mismatch** ／ **Option Review** ／ **Naming Review** ／
> **Category Review** ／ **`Current Taxonomy Compatibility Result`** ／ **Known Risks** ／
> **`Status（本 Review 时点）`**
> **全部保留，未删除、未改写** —— 其中包括 Review 时点的 **11 canonical reasons** baseline。

**决定 1 —— Existing Validation Taxonomy = `INSUFFICIENT`（ACCEPTED）**

接受上方 Review Finding 的判定：

```
Current Taxonomy Compatibility = INSUFFICIENT
```

现有 canonical validation taxonomy **无法准确表达**：

```
required package-scoped provenance linkage
cannot be reliably established or resolved
```

**Case G1（本决定所针对的缺口）：**

| 条件 | 状态 |
| --- | --- |
| Snapshot Package | 已 `ACCEPTED` |
| required logical dataset role | 已提供 |
| source evidence record | 存在 |
| canonical business value | 可读取 |
| required provenance reference | **缺失 ／ 无法可靠解析 ／ provenance information 不完整** |
| 结果 | **无法可靠建立** `source evidence → current Snapshot Package / Analysis provenance context` |

**该问题不是：**

- `artifact missing`
- `business field missing`
- `business scope coverage unresolved`
- `business semantic unresolved`

**决定 2 —— `PROVENANCE_MISMATCH` semantic = `UNCHANGED`（CONFIRMED）**

正式确认其 canonical meaning **保持不变**：

```
required provenance linkage 可以建立，
但指向错误 / incompatible provenance context。
```

例如：

```
Analysis Run      → Package P1
evidence reference → Package P2
        ↓
PROVENANCE_MISMATCH
```

**不得**把以下情形**扩展解释**为 `PROVENANCE_MISMATCH`：

- `absence`
- `unresolvable linkage`
- `incomplete provenance linkage`

**决定 3 —— New Canonical Reason `PROVENANCE_UNRESOLVED` = APPROVED（for implementation）**

正式批准 **`PROVENANCE_UNRESOLVED`** 作为后续 **Design Change / Implementation PR** 可实施的
**new canonical Reason**（**本 PR 不实施**）。

```
Category                  = PROVENANCE
minimal canonical semantic = Required package-scoped provenance linkage
                             cannot be reliably established or resolved.
```

**本 Human Decision 认可以下场景共享 `PROVENANCE_UNRESOLVED`：**

| # | 情形 | 判定 |
| --- | --- | --- |
| **P1** | required provenance reference **完全缺失** | **`PROVENANCE_UNRESOLVED`** |
| **P2** | provenance reference **存在**，但**无法解析为可靠的 package-scoped evidence locator** | **`PROVENANCE_UNRESOLVED`** |
| **P4** | provenance metadata **存在**，但**不完整到无法建立 required package-scoped linkage** | **`PROVENANCE_UNRESOLVED`** |
| **P3** | reference **可以解析**，但对应**错误 Package / Analysis Context** | **仍为 `PROVENANCE_MISMATCH`** |

**决定 4 —— Canonical Boundary = CONFIRMED**

必须明确：

```
PROVENANCE_UNRESOLVED
  ≠ FIELD_VALUE / MISSING
  ≠ SCOPE_COVERAGE / UNRESOLVED_SCOPE
  ≠ SEMANTIC_RESOLUTION / SEMANTIC_UNRESOLVED
  ≠ PROVENANCE_MISMATCH
```

**不得**作为 **catch-all reason**。其 root condition **必须保持**为：

```
provenance linkage cannot be reliably established or resolved
```

**不得**用于表达：

- canonical business field value 缺失
- artifact missing
- logical evidence role 未提供
- business semantic 未确定
- entity identity unresolved
- business scope coverage unresolved
- **已建立 linkage 但 context 错误**

**决定 5 —— `PROVENANCE` Category Decision = CONFIRMED（不新增 Category）**

正式确认：新增 Reason **`PROVENANCE_UNRESOLVED`** **仍属于** `PROVENANCE`；
**不得新增新的 Category**；**Canonical Category count 仍保持 `8`**。

后续 Implementation **可以**对 `PROVENANCE` category description 做**最小 semantic extension**，
使其**同时覆盖**：

```
1. linkage established but context incompatible
2. linkage cannot be reliably established / resolved
```

**决定 6 —— Implementation Authorization = AUTHORIZED（授权边界）**

本 Human Decision **授权后续独立 Design Change / Implementation PR**
执行**必要的最小 taxonomy synchronization**。允许后续 Implementation PR：

- **Canonical Reasons `11 → 12`**
- **`§4.4.81`** 新增 **`PROVENANCE_UNRESOLVED`**
- **`§4.4.80`** 更新 `PROVENANCE` category（含上述最小 semantic extension）
- 同步属于 **current-state** 的 **canonical reason count**
- 更新 **`§4.4.93` Provenance Boundary**
- 新增 **Implementation Record**
- **Implementation 完成且 Validation PASS 后**：
  **`Validation Taxonomy Limitation` `OPEN` → `DESIGN RESOLVED`**

**决定 7 —— Explicit Non-Authorization**

本 Human Decision **不授权**修改：

- canonical entity
- canonical business field
- `BR-*`
- `Stable Source Evidence Locator` semantic
- provenance carrier contract
- source-semantic mapping rules
- `Other Source-Semantic Mapping`
- `Snapshot / Import Contract`
- `Serialization Format`
- `Physical Dataset Layout`
- `Field Carrier Mapping`
- `Final Import Contract`
- `Final Master Data Mapping`
- `Master Data Mapping overall`
- AI / Tool Boundary
- Business Outcome taxonomy

**不得创建：**

- new severity
- `PROVENANCE_ERROR` Business Classification
- error code
- enum
- schema
- API error object
- test implementation

**决定 8 —— Historical Record Preservation = CONFIRMED**

以下历史记录**必须保持原样**：

- Review Finding
- Historical Review Record
- Human Decision Record
- Implementation Record

以及所有带明确时点语义的：

```
执行状态（本 Task 完成时点）
执行状态（PR #xx 时点）
Status（本 Review 时点）
```

其中如果写有 `11 canonical reasons` ／ `OPEN` ／ `DESIGN PENDING`，
**只要准确反映当时时点，不得回写**。

**决定 9 —— PR #46 Boundary = CONFIRMED**

**PR #46 最终职责**：

```
Review Finding
+ Human Decision
```

**不得在 PR #46 实施** `PROVENANCE_UNRESOLVED`；**不得修改** `§4.4.81 Final Canonical Reason Set`；
**不得修改** reason count；**不得修改**正式 Category Model；
**不得把** `Validation Taxonomy Limitation` 改为 `DESIGN RESOLVED`。

**PR #46 merge 后**：**必须另开独立 Implementation PR** 完成 taxonomy implementation。

**执行状态（PR #46 时点）**

```
Existing Validation Taxonomy       = INSUFFICIENT
PROVENANCE_MISMATCH semantic       = UNCHANGED
PROVENANCE_UNRESOLVED              = APPROVED FOR IMPLEMENTATION
PROVENANCE_UNRESOLVED in §4.4.81   = NOT YET IMPLEMENTED
Canonical Reasons                  = 11
Canonical Categories               = 8
Validation Taxonomy Limitation     = OPEN
Other Source-Semantic Mapping      = DESIGN RESOLVED
Final Master Data Mapping          = DESIGN PENDING
Master Data Mapping overall        = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
```

**本 PR 不实施 taxonomy change。** 在 follow-up **Human-authorized Design Change /
Implementation PR** 完成前：

```
Canonical Reasons              = 11
PROVENANCE_UNRESOLVED          = APPROVED FOR IMPLEMENTATION
                                 （尚未进入 Final Canonical Reason Set）
Validation Taxonomy Limitation = OPEN
```

**Validation Taxonomy Implementation Record（Human-authorized Taxonomy Design Change）**

**Human Authorization Source**

```
PR #46 Human Decision — Human-approved
  → Current Taxonomy Compatibility       = INSUFFICIENT（ACCEPTED）
  → PROVENANCE_MISMATCH semantic         = UNCHANGED
  → PROVENANCE_UNRESOLVED                = APPROVED FOR IMPLEMENTATION
  → Category                             = PROVENANCE（不新增 Category）
  → Canonical Category count             = 仍为 8
  → Canonical Reasons                    = 11 → 12（AUTHORIZED）
  → §4.4.80 PROVENANCE 最小扩辞           = AUTHORIZED
  → §4.4.81 新增第 12 个 reason           = AUTHORIZED
  → current-state reason count sync      = AUTHORIZED
  → §4.4.93 Provenance Boundary 更新      = AUTHORIZED
  → Implementation Record                = AUTHORIZED
  → Validation Taxonomy Limitation       = OPEN → DESIGN RESOLVED
                                           （implementation ＋ Validation PASS 后）
```

**Implemented Change**

```
Canonical Categories                 = 8（未变）
Canonical Reasons                    = 11 → 12
新增 reason                          = PROVENANCE_UNRESOLVED
所属 Category                        = PROVENANCE
PROVENANCE_MISMATCH semantic         = UNCHANGED
Validation Taxonomy Limitation       = OPEN → DESIGN RESOLVED
```

**`§4.4.80` —— `PROVENANCE` category（最小 semantic extension）**

`PROVENANCE` category 现**同时覆盖**两种 root condition：

```
1. required package-scoped provenance linkage
   cannot be reliably established / resolved
        → PROVENANCE_UNRESOLVED
2. required package-scoped provenance linkage
   established but points to wrong / incompatible Analysis Context
        → PROVENANCE_MISMATCH
```

**未新增** Category；`Canonical Category count` **仍为 `8`**；
`§4.4.80` 其他 7 个 category **未修改**。

**`§4.4.81` —— 第 12 个 canonical reason**

```
| 12 | `PROVENANCE_UNRESOLVED` | `PROVENANCE` |
```

既有 `1` ～ `11` 的**编号与语义未变**；`PROVENANCE_MISMATCH` **未**重命名、**未**重定义；
**未**新增 `UNKNOWN_ERROR` ／ `GENERIC_ERROR` ／ `VALIDATION_FAILED` ／ `BAD_DATA` ／ `OTHER`
等 catch-all reason。

**`PROVENANCE_UNRESOLVED` Canonical Semantic（正式落地）**

```
Category                   = PROVENANCE
canonical semantic         = Required package-scoped provenance linkage
                             cannot be reliably established or resolved.
```

覆盖（与 **PR #46 Human Decision** 决定 3 一致）：

| # | 情形 | 判定 |
| --- | --- | --- |
| **P1** | required provenance reference **完全缺失** | `PROVENANCE_UNRESOLVED` |
| **P2** | provenance reference **存在**，但**无法可靠解析为 package-scoped evidence locator** | `PROVENANCE_UNRESOLVED` |
| **P4** | provenance metadata **存在**，但**不完整到无法建立 required package-scoped linkage** | `PROVENANCE_UNRESOLVED` |

**`PROVENANCE_UNRESOLVED` vs `PROVENANCE_MISMATCH`**

```
PROVENANCE_UNRESOLVED = linkage cannot be reliably established / resolved
PROVENANCE_MISMATCH   = linkage established,
                        but points to wrong / incompatible Analysis Context
```

**P3 的归属不改变：**

| # | 情形 | 判定 |
| --- | --- | --- |
| **P3** | reference **可以可靠解析**，但指向**错误 Package / Analysis Context** | **仍为 `PROVENANCE_MISMATCH`**（**不**改为 `PROVENANCE_UNRESOLVED`） |

**Canonical Boundary（正式同步）**

```
PROVENANCE_UNRESOLVED
  ≠ EVIDENCE_AVAILABILITY / EVIDENCE_ROLE_NOT_PROVIDED
  ≠ FIELD_VALUE / MISSING
  ≠ IDENTITY_RESOLUTION / UNRESOLVED_IDENTITY
  ≠ SCOPE_COVERAGE / UNRESOLVED_SCOPE
  ≠ SEMANTIC_RESOLUTION / SEMANTIC_UNRESOLVED
  ≠ PROVENANCE_MISMATCH
```

**不得**作为 **catch-all reason**；其 root condition **必须保持**为
`provenance linkage cannot be reliably established or resolved`。

**Current-State Synchronization**

| 位置 | 同步内容 |
| --- | --- |
| `§4.4.16 Validation Issue Concept` | `Reason` dimension = **12 个 canonical reason 之一** |
| `§4.4.43 Reason Seed → Superseded` | `§4.4.81` = **12 个** canonical reason；新增清单补入 `PROVENANCE_UNRESOLVED` |
| `§4.4.67 ApplicableMOQ Boundary` | 本项**未**扩展 canonical reason set；该 set 现为 **12 个** |
| `§4.4.80 Canonical Issue Categories` | `PROVENANCE` 含 `PROVENANCE_UNRESOLVED` ＋ `PROVENANCE_MISMATCH`；Category count 仍 **8** |
| `§4.4.81 Final Canonical Reason Set` | 共 **12 个**；第 12 项 = `PROVENANCE_UNRESOLVED` |
| `§4.4.93 Provenance Boundary` | Missing ／ Unresolved ／ Mismatch 四种情形（A ／ B ／ C ／ D） |
| `§4.4.101 Final Data Validation Design Closure` | closure checklist row 8 = `8 categories ＋ 12 reasons` |
| `§4.5.22 NEXT REQUIRED DESIGN REVIEW` | Validation Taxonomy review **已完成**；仅 `Master Data Mapping Closure Review` 仍待执行 |
| `§4.5.24 Status Boundary` | `Validation Taxonomy Limitation` = `DESIGN RESOLVED` |

**Historical Record Preservation（未回写）**

以下**保持原样**（其中 `11 canonical reasons` ／ `OPEN` 表述准确反映各自时点）：

- **PR #46 Review Finding**（含 `Existing Taxonomy Baseline` ／
  `Status（本 Review 时点）` ／ `Human Decision Required` ／ `Known Risks`）
- **PR #46 Human Decision Record**（含 `执行状态（PR #46 时点）`）
- **Historical Review Record —— PR #40**
- 各 **`执行状态（本 Task 完成时点）`** ／ **`执行状态（PR #xx 时点）`** ／
  **`Status（本 Review 时点）`** 块（例如 PR #44 ／ PR #45 implementation record status）

**Meaning of `DESIGN RESOLVED`**

`Validation Taxonomy Limitation = DESIGN RESOLVED` **只**表示
**canonical validation taxonomy 概念设计同步完成**，
**不表示**：

```
runtime validator implemented
API implemented
enum implemented
schema implemented
Adapter implemented
production tested
```

**未实施**：runtime validator ／ implementation enum ／ JSON Schema ／ API error object ／
Adapter ／ 任何 runtime behavior test。

**执行状态（本 Task 完成时点）**

```
Human Decision                       = RECORDED
PROVENANCE_UNRESOLVED                = IMPLEMENTED / CANONICAL
PROVENANCE_UNRESOLVED Category       = PROVENANCE
Canonical Categories                 = 8
Canonical Reasons                    = 11 → 12
PROVENANCE_MISMATCH semantic         = UNCHANGED
Validation Taxonomy Limitation       = OPEN → DESIGN RESOLVED
Other Source-Semantic Mapping        = DESIGN RESOLVED
Final Master Data Mapping            = DESIGN PENDING
Master Data Mapping overall          = DESIGN PENDING
Snapshot / Import Contract overall   = DESIGN PENDING
```

**Master Data Mapping Closure Review（Review Finding）**

**Review Authority**

```
PR #44 Human Decision
  → 決定 18：Final Master Data Mapping Closure Gate = CONFIRMED（NOT CLOSED）
  → 決定 19：Separate Closure Review Required = AUTHORIZED
  → 決定 20：Snapshot / Import Contract Boundary = CONFIRMED
```

**Review Question**

本 Review **只回答 `§4.5.22` 決定 19 登记的 10 个问题**：

```
1.  Identity Resolution Boundary 是否完整？
2.  Relationship Resolution Boundary 是否完整？
3.  Mapping Conflict / Failure Boundary 是否完整？
4.  Mapping Provenance Requirement 是否完整？
5.  所有 source-semantic unresolved 是否已关闭？
6.  是否仍存在未登记的 canonical mapping gap？
7.  Final Master Data Mapping 的最低 closure criteria 是什么？
8.  当前是否满足这些 criteria？
9.  是否允许 Final Master Data Mapping = DESIGN RESOLVED？
10. 是否允许 Master Data Mapping overall = DESIGN RESOLVED？
```

**Review Scope Boundary**

本 Review **只做 Review Finding**：

- **不**关闭 `Final Master Data Mapping`；
- **不**关闭 `Master Data Mapping overall`；
- **不**实施 closure；
- **不**自行作 Human Decision；
- **不**修改 `Snapshot / Import Contract`；
- **不**补设计任何 gap（只登记 gap）。

**Existing Baseline（从 Repository 已存在的正式设计恢复）**

`§4.5` 层级状态登记表：

| 层 | Status | 关键 Design 位置 |
| --- | --- | --- |
| Identity Resolution Boundary | `DESIGN RESOLVED` | `§4.5.2` ／ `§4.5.3` ／ `§4.5.4` ／ `§4.5.5` ／ `§4.5.6` |
| Relationship Resolution Boundary | `DESIGN RESOLVED` | `§4.5.7` ／ `§4.5.8` ／ `§4.5.10` ／ `§4.5.12` ／ `§4.5.20` |
| Mapping Conflict / Failure Boundary | `DESIGN RESOLVED` | `§4.5.15` ／ `§4.5.16` ／ `§4.5.17` ／ `§4.5.18` |
| Mapping Provenance Requirement | `DESIGN RESOLVED` | `§4.5.14` ／ `§4.1.8` ／ `§4.5.22 Option D Implementation Record` |
| Warehouse Role Resolution | `DESIGN RESOLVED` | `§4.5.12` |
| BOM Version / Validity Mapping | `DESIGN RESOLVED` | `§4.5.7` ／ `§4.1.4 N` |
| Supplier Eligibility Vocabulary Mapping | `DESIGN RESOLVED` | `§4.5.11` |
| Effective Arrival Date Source Mapping | `DESIGN RESOLVED` | `§4.5.21` |
| Allocation Demand-Window Mapping | `DESIGN RESOLVED` | `§4.5.9` |
| Other Source-Semantic Mapping | `DESIGN RESOLVED` | `§4.5.22` |
| **Final Master Data Mapping** | **`DESIGN PENDING`** | **只有层级登记，无 scope 定义、无 closure criteria** |

```
Master Data Mapping layers = 10 / 11 DESIGN RESOLVED
Master Data Mapping overall = DESIGN PENDING
```

未决项 registry 现状：

| Registry | 现状 |
| --- | --- |
| `§4.1.12 Open Items` | **7 / 7 `DESIGN RESOLVED`**，无开放项 |
| `§4.4.41 Unknown Semantic Items` | 9 项**全部**已解析或已移除（保留历史约束记录） |
| `§4.4.101 Upstream Design Items` | **0 项**未决 ＋ 8 项已解析 ＋ 1 项已移除 |
| `§4.5.22 Preserve Unresolved Items` | 8 行**全部** `DESIGN RESOLVED`；`unresolved count = 0` |
| `§11 Open Design Backlog` | `VB-14` ～ `VB-18` ／ `VB-27` ／ `VB-28` ／ `VB-29` ＋ `BR-INBOUND-001` **全部** `DESIGN RESOLVED` |
| `§4.3 Snapshot / Import Contract` | 4 `DESIGN RESOLVED` ＋ **4 `DESIGN PENDING`**（`Serialization Format` ／ `Physical Dataset Layout` ／ `Field Carrier Mapping` ／ `Final Import Contract`） |
| `§4` 子领域表 | `Master Data Mapping` ／ `Snapshot / Import Contract` ／ `Adapter Boundary` = `DESIGN PENDING` |

> **时点说明 ／ supersede：** 本表为 **Final Master Data Mapping closure 时点**的 registry snapshot
> （历史值**保留不回写**，**不**代表 latest current state）；其后 `Snapshot / Import Contract overall` 已由
> **Issue #66 Closure**、`Adapter Boundary` 已由 **Issue #90 Closure Validation = `PASS`** 分别关闭 ⇒
> 最新状态见 **§4.3.29** ／ **§4.6.22**。

**10 Questions Assessment（摘要）**

| # | 问题 | 结论 |
| --- | --- | --- |
| 1 | `Identity Resolution Boundary` 是否完整？ | **是** |
| 2 | `Relationship Resolution Boundary` 是否完整？ | **是** |
| 3 | `Mapping Conflict / Failure Boundary` 是否完整？ | **是** |
| 4 | `Mapping Provenance Requirement` 是否完整？ | **是** |
| 5 | 所有 source-semantic unresolved 是否已关闭？ | **是**（`unresolved count = 0`，registry 无开放项） |
| 6 | 是否仍存在**未登记**的 canonical mapping gap？ | **否**（未发现未登记的 identity ／ relationship ／ source-semantic mapping gap；但存在**已文档化、未进入统一 registry** 的 deferral，见 Gap Audit `G-5` ／ `G-6`） |
| 7 | `Final Master Data Mapping` 的最低 closure criteria 是什么？ | **本 Review 提出 `MC-1` ～ `MC-10`**（见下） |
| 8 | 当前是否满足这些 criteria？ | **未满足**（`MC-1` 未满足；`MC-9` 部分未满足） |
| 9 | 是否允许 `Final Master Data Mapping = DESIGN RESOLVED`？ | **当前不允许**（见 Blocking Gaps `B-1` ／ `B-2`） |
| 10 | 是否允许 `Master Data Mapping overall = DESIGN RESOLVED`？ | **当前不允许**（依赖 `Final Master Data Mapping`，`決定 18` 保持有效） |

**Q1 —— `Identity Resolution Boundary` 是否完整？ —— 是**

- `§4.5.2` 定义 canonical principle：`Source Identifier ≠ Canonical Identity`；mapping **必须** `deterministic` ／ `explicit` ／ `traceable` ／ `reproducible`；**不得**依赖 LLM guess ／ name similarity ／ fuzzy matching ／ human-name intuition ／ silent normalization。
- `§4.5.3` 定义三种 conceptual mapping condition：**Reliably Resolved** ／ **Unresolved** ／ **Conflicting / Ambiguous**，并禁止 random ／ first wins ／ latest wins ／ LLM choose。
- `§4.5.4` Plant（`plant_id`）、`§4.5.5` Material（`material_code`）、`§4.5.6` Supplier（`supplier_id`）分别定义 boundary，并禁止 default Plant ／ cross-Plant fallback ／ 名称相似度 ／ 同名即同实体。
- `§4.1.3 Canonical Entity Catalog` 的每一个 entity 均可对应到 boundary：

| Entity | Canonical identity / grain | Boundary |
| --- | --- | --- |
| A Plant | `plant_id` | `§4.5.4` |
| B Material | `material_code` | `§4.5.5` |
| C Production Requirement | `plant_id` + `material_code` + `required_date` | `§4.5.4` ／ `§4.5.5` ＋ `§4.1.6` Time Semantics |
| D Inventory Snapshot | `plant_id` + `material_code` + `inventory_snapshot_time` ＋ status context | `§4.5.4` ／ `§4.5.5` ／ `§4.5.12` ＋ `§4.2.14` canonical vocabulary |
| E Inbound Supply | `plant_id` + `material_code` ＋ inbound identity | `§4.5.4` ／ `§4.5.5` ／ `§4.5.21` |
| F Substitute Relationship | `plant_id` + `target_material_code` + `substitute_material_code` | `§4.5.8` |
| G Substitute Allocation | source substitute ＋ target ＋ effective demand context | `§4.5.9` |
| H Supplier | `supplier_id` | `§4.5.6` |
| I Supplier-Material Relationship | `supplier_id` + `material_code` | `§4.5.10` ／ `§4.5.11` |
| J Supplier Performance | `supplier_id` + `material_code` + `PerformancePeriod` | `§4.5.6` ／ `§4.5.10` ＋ `§4.4.34` |
| K Procurement Recommendation | `plant_id` + `material_code` + `RecommendationNeedDate` | `§4.5.22`（`ApplicableMOQ` resolution） |
| L Procurement Request Draft | 由 K 派生 | `§3` ／ `§5` |
| M Analysis Run | analysis run identity；`AnalysisDate` | `§4.3`（`Analysis Run Linkage`） |
| N BOM Component | requirement-scoped applicability | `§4.5.7` ／ `§4.1.4 N` |
| O Configured Safety Stock | `plant_id` + `material_code` | `§4.5.4` ／ `§4.5.5` |
| Warehouse（**非** canonical entity） | source ／ mapping ／ scope context | `§4.5.12` |

**结论：无 identity resolution boundary 缺口。**

**Q2 —— `Relationship Resolution Boundary` 是否完整？ —— 是**

- `§4.5.7` BOM parent → component（requirement-scoped；`§4.1.4 N`）
- `§4.5.8` Substitute source → target
- `§4.5.10` Supplier ↔ Material（明确 `Supplier exists + Material exists ≠ Supplier-Material Relationship exists`）
- `§4.5.12` Warehouse → Plant ／ scope context
- `§4.5.20` 定义 conceptual relationship mapping registry，覆盖上述四类，且**不得创建新的 Business Relationship**
- `§4.1.5 Relationship Model` 中每一个关系均有对应 boundary；跨 Package 关系由 `§4.5.15` 禁止并交由未来新 Design

**结论：无 relationship resolution boundary 缺口。**

**Q3 —— `Mapping Conflict / Failure Boundary` 是否完整？ —— 是**

- `§4.5.16 Mapping Conflict`：同一 source identity 在同一有效 mapping context 指向多个 canonical identity 且无 precedence rule 时，**不得** first wins ／ latest wins ／ smallest ID ／ most frequent ／ LLM decide；应视为 unresolved identity ／ consistency issue，并限制 blast radius 到 `affected evidence → grain → capability`；**不得默认** reject entire Package。
- `§4.5.17 Missing Mapping`：必须区分 `source evidence absent` 与 `source evidence exists but canonical mapping unavailable`；**不得** `mapping missing → business value = 0`。
- `§4.5.18 No Silent Canonicalization`：禁止 trim ／ case ／ prefix ／ substring ／ name → identity 的静默归一。
- `§4.5.13 Cross-System Identifier Boundary`：必须有 explicit mapping evidence；normalization policy **必须显式设计**。
- Failure 与 canonical Validation Taxonomy 的连接已完整：`UNRESOLVED_IDENTITY` ／ `UNRESOLVED_SCOPE` ／ `SEMANTIC_UNRESOLVED` ／ `CONSISTENCY_CONFLICT` ／ `PROVENANCE_UNRESOLVED` ／ `PROVENANCE_MISMATCH`（`§4.4.80` ／ `§4.4.81`，`Canonical Reasons = 12`）。
- `§4.5.24` 明确 **Important Non-Resolution**：`DESIGN RESOLVED` 只表示 conceptual resolution boundary 已定义。

**结论：无 conflict ／ failure boundary 缺口；无 silent precedence。**

**Q4 —— `Mapping Provenance Requirement` 是否完整？ —— 是**

- `§4.5.14` 要求每个成功 mapping 未来可追溯：`source identity context → canonical identity → mapping evidence → Snapshot Package`。
- `§4.1.8` provenance requirement ＋ `§4.5.22 Option D Implementation Record` 落地 **Layered Logical Provenance Contract**：`Snapshot Package Identity` ＋ `Logical Dataset Role` ＋ `Stable Source Evidence Locator` ＋ `Mapping / Resolution Basis`（when applicable）＋ `Analysis Run linkage`。
- `§4.5.19` ／ `§4.5.20` 定义 conceptual mapping registry 必须可表达 `Mapping Evidence / Basis` 与 provenance context。
- 边界保持：**logical carrier ≠ physical carrier**；physical carrier 仍属 `§4.3`。

**结论：logical provenance requirement 完整；physical carrier 明确不属于本层 closure 范围。**

**Q5 —— 所有 source-semantic unresolved 是否已关闭？ —— 是**

| Registry | 未决 |
| --- | --- |
| `§4.1.12 Open Items` | **0**（7 / 7 已 `DESIGN RESOLVED`） |
| `§4.4.41 Unknown Semantic Items` | **0**（9 项全部已解析或已移除） |
| `§4.4.101 Upstream Design Items` | **0 项**未决（文档明示「剩余 **0 项**未决」） |
| `§4.5.22 Preserve Unresolved Items` | **0**（8 行全部 `DESIGN RESOLVED`；`unresolved count = 0`） |
| `§11 Open Design Backlog` | **0**（全部 `DESIGN RESOLVED`） |

**但**：`unresolved count = 0` **不自动**构成 overall closure（`決定 18` 明确确认）。本 Review 不因该数字降低任何 criteria。

**Q6 —— 是否仍存在未登记的 canonical mapping gap？ —— 否（未发现）**

Audit 覆盖 `§4.1` canonical entity catalog（A ～ O ＋ Warehouse）、`§4.1.5 Relationship Model`、
`§4.2 Data Dictionary` 全部 `SOURCE` ／ `CONTEXT` ／ `POLICY_INPUT` 字段与
`§4.5.1` ～ `§4.5.24` 全部 mapping boundary。

- **未发现**任何 canonical entity ／ field ／ relationship 满足以下任一条件：
  没有 identity resolution path ／ 没有 relationship resolution boundary ／
  没有 ambiguity ／ conflict behavior ／ 没有 unresolved behavior ／
  没有 provenance requirement ／ 没有 source-semantic resolution contract ／
  存在 consumer 但没有可靠 mapping boundary。
- 仅有的未定义项均属**已文档化的 deferral**，并已在 Gap Audit 逐项登记其归属与影响（`G-3` ～ `G-10`）。
- 未定义项**不得**由本 Review 自行补设计（`§4.4.42 No Stringency Inflation` 已禁止在无现有 Design 支持时新增
  identifier regex ／ freshness threshold ／ decimal precision ／ currency ／ unit-of-measure conversion ／
  timezone policy ／ quantity rounding 等）。

**Minimum Closure Criteria（本 Review 提出的 `MC-1` ～ `MC-10`）**

这些 criteria：

- 基于**现有** POC conceptual design；
- **可验证**（每一项都能在 canonical document 中判定）；
- **不依赖**真实 ERP schema；
- **不**把 physical import design 偷换成 Master Data Mapping；
- **不**新增没有现有证据支持的 business semantics。

| # | Minimum Closure Criterion | 验证方式 | 现状 |
| --- | --- | --- | --- |
| **MC-1** | `Final Master Data Mapping` 的 **scope 被正式定义**：明确它覆盖哪些 mapping 层 ／ items，并明确**不属于**它的范围（physical source field selection ／ serialization ／ physical layout ／ Adapter） | 文档中存在该 scope 定义段落 | **未满足** |
| **MC-2** | 其全部 constituent mapping layers 均为 `DESIGN RESOLVED` | `§4.5` 层级状态登记表 | 满足（10 / 10） |
| **MC-3** | mapping scope 内**无** registered unresolved item | `§4.1.12` ／ `§4.4.41` ／ `§4.5.22` ／ `§11` | 满足（0） |
| **MC-4** | 每个具 canonical identity 的 canonical entity 都有 identity resolution boundary | `§4.1.3` ↔ `§4.5.4` ／ `§4.5.5` ／ `§4.5.6` ／ `§4.5.12` | 满足 |
| **MC-5** | 每个 canonical relationship 都有 relationship resolution boundary | `§4.1.5` ↔ `§4.5.7` ／ `§4.5.8` ／ `§4.5.10` ／ `§4.5.12` ／ `§4.5.20` | 满足 |
| **MC-6** | 每个被 Rule 使用的 source-specific vocabulary ／ semantic 都有 canonical mapping contract，或已被既有 canonical vocabulary 定义 | `§4.5.11` ／ `§4.5.21` ／ `§4.5.9` ／ `§4.5.22` ＋ `§4.2.14` | 满足 |
| **MC-7** | 每个 mapping 层都有 explicit ambiguity ／ conflict ／ unresolved behaviour，且无 silent precedence | `§4.5.3` ／ `§4.5.16` ／ `§4.5.17` ／ `§4.5.18` | 满足 |
| **MC-8** | 每个成功 mapping 都被 logical provenance requirement 覆盖 | `§4.5.14` ／ `§4.1.8` ＋ `§4.5.22 Option D Implementation Record` | 满足 |
| **MC-9** | **无未登记**的 canonical mapping gap；所有**已文档化 deferral** 均已在统一 design-item registry 中登记其归属与对 closure 的影响判定 | registry 表 ＋ Gap Audit 表 | **部分未满足**（`G-5` ／ `G-6` 已文档化但未进入统一 registry） |
| **MC-10** | closure 的语义边界被显式登记：Conceptual Master Data Mapping Closure **≠** Real ERP Mapping Completed **≠** Adapter Implemented **≠** Physical Import Contract Completed **≠** Tested Production Integration | 文档中存在该边界声明 | 满足（`§4.5.24` ／ `§4.5.1`） |

**Q7 回答：** `Final Master Data Mapping` 的 minimum closure criteria = **`MC-1` ～ `MC-10`**；
其中 **`MC-1` 是前置条件** —— 没有 scope 定义，`MC-2` ～ `MC-8` 与 `MC-10` 通过也无从构成一个可判定的 closure。

**Q8 —— 当前是否满足这些 criteria？ —— 未满足**

- `MC-1`：**未满足**。全文检索确认 `Final Master Data Mapping` **只**作为层级登记标签出现
  （`§4.5` 层级状态表、`§4.5.24` status boundary 等），**没有任何** scope 定义或 closure criteria 定义
  —— 这正是 `決定 18` 的结论，且至今**未被消除**。
- `MC-9`：**部分未满足**。`G-5`（quantity precision ／ rounding ／ UoM conversion）与
  `G-6`（`PerformancePeriod` period policy）均为**已文档化** deferral，但**未**登记在任何统一 design-item registry 中，
  也**未**有 Human Decision 判定其对 mapping closure 的影响。
- 其余 criteria 满足。

**Q9 —— 是否允许 `Final Master Data Mapping = DESIGN RESOLVED`？ —— 当前不允许**

**Blocking Gaps：**

| # | Blocking Gap | Impact | Why it blocks closure |
| --- | --- | --- | --- |
| **B-1** | **`Final Master Data Mapping` 的 scope 未定义** —— 文档从未说明该层覆盖什么、不覆盖什么；且 `§4.5.12` 的现行表述把 *physical membership evidence ／ source representation* 归入「**physical mapping realization**」，并以此解释 `Final Master Data Mapping` 仍为 `DESIGN PENDING`，与 `§4.5.1`「**不得定义** source table ／ source column」及 `決定 20` ／ `決定 21` 的 physical 边界存在**范围重叠风险** | 无法判定该层的 closure；亦无法判定它与 `§4.3 Field Carrier Mapping` ／ `Adapter Boundary` 的边界 | closure 需要一个**可判定的对象**。对象未定义时，任何 `DESIGN RESOLVED` 判定都不可验证 |
| **B-2** | **closure criteria 未登记** —— 本 Review 提出的 `MC-1` ～ `MC-10` 目前**只是** Review Finding 内容，尚未成为 canonical document 中的正式登记项 | `MC-1` ～ `MC-10` 无法作为后续 implementation ／ validation 的判定依据 | 没有正式 criteria，就无法证明 closure 是**被判定通过**的，而不是**被声明**的 |

**明确：本 Review 不降低 criteria 以求 closure；也不自行补设计以消除 `B-1`。**

**Canonical Gap Audit**

| # | Gap | Impact | Blocks closure? |
| --- | --- | --- | --- |
| **G-1** | `Final Master Data Mapping` 的 **scope 定义缺失**（含与 `§4.3` ／ `Adapter Boundary` 的范围重叠风险） | 无法判定该层 closure | **BLOCKING**（＝ `B-1`） |
| **G-2** | `Final Master Data Mapping` 的 **closure criteria 未正式登记** | 后续无法以正式依据验证 | **BLOCKING**（＝ `B-2`） |
| **G-3** | `ERP source-field mapping` 仍 `DESIGN PENDING`（`§4.1.4 N` ／ `§4.5.7`） | 真实 source table ／ column 选择未定 | **不阻塞** —— 属 physical source selection；Conceptual closure **不等于** real ERP mapping（须由 `MC-1` ／ `MC-10` 显式排除） |
| **G-4** | `BOM explosion algorithm` `DESIGN PENDING / OUTSIDE THIS TASK`（`§4.5.7` ／ `§4.1.4 N`） | BOM 展开算法未设计 | **不阻塞** —— 已明确超出本 POC canonical model 所需（`§2.4.2` 直接要求 `BOMComponentQty`，不要求展开引擎） |
| **G-5** | `Quantity precision` ／ `rounding` ／ `UOM conversion` **未定义**（`§2.4.8` ／ `§2.5.11` ／ `§4.4.42`） | 数量精度 ／ 单位换算 ／ 取整未定 | **不阻塞** —— 非 identity ／ relationship ／ source-semantic mapping 项；属已文档化 deferral（`§2.4.8` 明示「由后续明确 Design Rule 决定」；`§4.4.42` 明示**不得**在无现有 Design 支持时新增）。**未进入统一 registry**（见 `MC-9`） |
| **G-6** | `PerformancePeriod` period policy `NOT DEFINED（DESIGN PENDING）`（`§4.2` Data Dictionary ／ `§4.4.34`） | measurement window vocabulary（`30d` ／ `90d` ／ rolling year ／ fiscal period）未定 | **不阻塞** —— 其 **mapping** 要求已满足（`§4.4.34` 要求 measurement period 必须可可靠识别；missing → `DATA_INCOMPLETE` fail-safe）；未定的是 business policy vocabulary。**未进入统一 registry**（见 `MC-9`） |
| **G-7** | `Normalization policy` 条件性未定义（`§4.5.13` ／ `§4.5.18`：如未来需要，**必须显式设计**） | 未来 source 若要求 trim ／ case ／ prefix 归一，需新 Design | **不阻塞** —— 现行设计是**禁止**推断（fail-safe），deferral 已显式登记 |
| **G-8** | `Cross-Package mapping`（`§4.5.15`） | 跨 Package mapping 当前**不允许** | **不阻塞** —— 已作为 prohibition 关闭；若未来放开**必须**作为新 Design |
| **G-9** | `physical carrier realization`（`§4.3`：`Serialization Format` ／ `Physical Dataset Layout` ／ `Field Carrier Mapping` ／ `Final Import Contract` 全部 `DESIGN PENDING`） | 物理承载与导入合同未设计 | **不阻塞 Master Data Mapping** —— 属 `Snapshot / Import Contract`；`決定 20` 已确认两者相互独立 |
| **G-10** | `Adapter Boundary = DESIGN PENDING`（`§4` 子领域表） | Adapter contract 未设计 | **不阻塞** —— 属独立子领域 |
| **G-11** | `§4.3.17` ／ `§4.4.41` ／ `§4.5.12` 的既有 stale provenance-carrier annotation | 局部 current-state 注释陈旧 | **不阻塞** —— 独立 consistency cleanup，**不在**本 Review 授权范围（本 Review 未处理） |

**结论：未发现 identity ／ relationship ／ source-semantic mapping 层面的未登记 canonical mapping gap。
唯一 BLOCKING 项为 `G-1` ／ `G-2`，即 `Final Master Data Mapping` 本身的 scope 与 closure criteria 未定义。**

**Snapshot / Import Contract Boundary（保持）**

```
Snapshot / Import Contract overall = DESIGN PENDING

  Serialization Format        = DESIGN PENDING
  Physical Dataset Layout     = DESIGN PENDING
  Field Carrier Mapping       = DESIGN PENDING
  Final Import Contract       = DESIGN PENDING
```

- 以下**仍不属于**本 Review：`Serialization Format` ／ `Physical Dataset Layout` ／
  `Field Carrier Mapping` ／ `Final Import Contract` ／ CSV ／ JSON ／ DB layout ／
  physical provenance columns ／ Adapter implementation。
- **必须继续保持：**

```
Master Data Mapping closure  ≠  Import Contract closure
```

- `決定 20` ／ `決定 21` 保持有效。
- `Master Data Mapping` 未来是否 closure，**均不得**改变 `Snapshot / Import Contract overall = DESIGN PENDING`。

**Known Risks**

| # | Risk | 说明 | 建议 |
| --- | --- | --- | --- |
| **R-1** | **`Final Master Data Mapping` 语义歧义** | `§4.5.12` 的 current-state 表述把 *physical membership evidence ／ source representation* 归入「physical mapping realization」，并以此解释该层仍 `DESIGN PENDING`；而 `§4.5.1` 明确「**不得定义** source table ／ source column」、`決定 21` 明确不授权 physical schema。两者对同一层级的覆盖范围理解不一致 | Human Decision **必须先行**裁定该层的 scope（conceptual 还是含 physical realization） |
| **R-2** | **若按 physical 理解则无法 closure** | 当前为 **`SIMULATED` POC**，**没有真实** ERP vendor ／ version ／ schema ／ field list；若 `Final Master Data Mapping` 被理解为 physical mapping realization，则它在当前项目状态下**不可能** closure，且会与 `§4.3` ／ `Adapter Boundary` 重叠 | 建议按 **Conceptual Master Data Mapping Closure** 定义 scope，并显式排除 physical realization（见 `MC-1` ／ `MC-10`） |
| **R-3** | **`unresolved count = 0` 被误读为 overall closure** | `決定 18` 已明确否定该推断，但仍存在被后续读者误读的风险 | 保持 `§4.5` ／ `§4.5.24` 现有显式否定表述，并把该边界写入 closure criteria（`MC-3` ＋ `MC-9`） |
| **R-4** | **closure 被误读为 implementation** | `DESIGN RESOLVED` **≠** real ERP mapping ／ Adapter implemented ／ physical import contract completed ／ tested | `MC-10` 要求把该边界正式登记 |
| **R-5** | **已文档化 deferral 未统一登记** | `G-5` ／ `G-6` 等只写在各自章节，未进入统一 design-item registry；后续 closure 判定时可能被遗漏或被当作"已完成" | 在 closure decision 中显式登记其归属与影响（`MC-9`） |
| **R-6** | **`§4.3.17` ／ `§4.4.41` ／ `§4.5.12` 既有 stale annotation** | 属已知旧 consistency defect（如 `§4.4.41` 的裸 `- provenance carrier`） | 独立 cleanup Task 处理；本 Review 不扩大范围 |
| **R-7** | **本 Review 之后容易产生"还差一点就能 closure"的推进压力** | `MC-1` 未满足时若先行宣布 closure，将破坏 `決定 18` 的 governance 语义 | 必须保持 `Final Master Data Mapping = DESIGN PENDING` 直到 Human Decision |

**Review Conclusion**

基于 Repository 中已存在的正式设计事实：

1. **Master Data Mapping 的 10 个 constituent layers 全部 `DESIGN RESOLVED`**，
   且 `Identity Resolution` ／ `Relationship Resolution` ／ `Mapping Conflict / Failure` ／
   `Mapping Provenance Requirement` 四项 boundary **完整**（`Q1` ～ `Q4` = 是）。
2. **所有已登记的 source-semantic unresolved item 已关闭**（`unresolved count = 0`，`Q5` = 是）；
   **未发现**未登记的 identity ／ relationship ／ source-semantic mapping gap（`Q6` = 否）。
3. **但 closure criteria 当前未被满足**（`Q8` = 未满足），存在两个 **BLOCKING gap**：
   - **`B-1`**：`Final Master Data Mapping` 的 **scope 未定义**（且与 `§4.3` ／ `Adapter Boundary` 存在范围重叠风险）；
   - **`B-2`**：**closure criteria 未正式登记**（本 Review 提出的 `MC-1` ～ `MC-10` 尚不构成正式依据）。
4. 因此：
   - **不允许** `Final Master Data Mapping = DESIGN RESOLVED`（`Q9`）；
   - **不允许** `Master Data Mapping overall = DESIGN RESOLVED`（`Q10`）；
   - **`決定 18` 保持有效**：`unresolved count = 0` 与 `Other Source-Semantic Mapping = DESIGN RESOLVED`
     **均不自动**意味着 closure。
5. 本 Review **未**实施 closure，**未**修改任何 status，**未**补设计以消除 gap。

**Current Status（本 Review 时点）**

```
Canonical Data Model                 = DESIGN RESOLVED
Data Dictionary                      = DESIGN RESOLVED
Data Validation                      = DESIGN RESOLVED
Master Data Mapping layers           = 10 / 11 DESIGN RESOLVED
unresolved count                     = 0
Identity Resolution Boundary         = DESIGN RESOLVED（完整）
Relationship Resolution Boundary     = DESIGN RESOLVED（完整）
Mapping Conflict / Failure Boundary  = DESIGN RESOLVED（完整）
Mapping Provenance Requirement       = DESIGN RESOLVED（完整）
Other Source-Semantic Mapping        = DESIGN RESOLVED
Final Master Data Mapping            = DESIGN PENDING   ← 未关闭
Master Data Mapping overall          = DESIGN PENDING   ← 未关闭
Snapshot / Import Contract overall   = DESIGN PENDING   ← 未关闭（独立）
Adapter Boundary                     = DESIGN PENDING
POC Design v0.2                      = DRAFT
```

**Human Decision Required**

| # | 问题 | 需要的 Human Decision |
| --- | --- | --- |
| 1 | 是否接受 **`Final Master Data Mapping` 的 scope 定义**（明确属于 ／ 不属于它的 mapping items，并显式排除 physical source field selection ／ serialization ／ physical layout ／ Adapter）？ | scope 裁定（`B-1`） |
| 2 | 是否接受本 Review 提出的 **`MC-1` ～ `MC-10`** 作为 `Final Master Data Mapping` 的正式 minimum closure criteria？ | criteria 裁定（`B-2`） |
| 3 | 是否授权一个**后续 Registration Task** 把 scope 与 criteria 正式登记进本 canonical document？ | **注意：登记 ≠ closure** |
| 4 | 是否接受 **`MC-1` 未满足** 因而 **`Final Master Data Mapping` 必须保持 `DESIGN PENDING`**？ | status 裁定 |
| 5 | 是否接受 **`G-3` ～ `G-11` 为 non-blocking** 的判定？ | gap 影响裁定 |
| 6 | 是否要求把 `G-5`（quantity precision ／ rounding ／ UoM conversion）与 `G-6`（`PerformancePeriod` period policy）等已文档化 deferral **登记进统一 design-item registry**（`MC-9`）？ | registry 裁定 |
| 7 | 是否确认 **`Master Data Mapping closure ≠ Import Contract closure`** 保持不变（`決定 20`）？ | boundary 确认 |
| 8 | 是否确认在 scope 与 criteria 被正式登记**之前**，**不得**宣布 `Final Master Data Mapping = DESIGN RESOLVED` 或 `Master Data Mapping overall = DESIGN RESOLVED`？ | governance 确认 |

**本 Review 只产出 Review Finding。** 后续必须由 **Human Decision** 决定
`Final Master Data Mapping` 的 scope ／ closure criteria 与最终 status；
**不得**由 Agent 自行宣布 closure。

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 本节是对**上方 Review Finding**
> （**Master Data Mapping Closure Review（Review Finding）**）的 **Human Decision**。
>
> 上方 Review Finding 中的 **`Human Decision Required`** 表述**已在本节获得答案**；
> **未实施部分**见本节末 **执行状态**。
>
> 上方 **Review Authority** ／ **Review Question** ／ **Review Scope Boundary** ／
> **Existing Baseline** ／ **10 Questions Assessment** ／
> **Minimum Closure Criteria（原始 `MC-1` ～ `MC-10`）** ／
> **Canonical Gap Audit（`G-1` ～ `G-11`）** ／ **Snapshot / Import Contract Boundary** ／
> **Known Risks** ／ **Review Conclusion** ／ **Current Status（本 Review 时点）**
> **全部保留，未删除、未改写** —— 其中包括 Review 时点的
> `MC-1 = 未满足` ／ `MC-9 = 部分未满足` ／
> `Final Master Data Mapping = DESIGN PENDING` ／ `Master Data Mapping overall = DESIGN PENDING`。

**决定 1 —— PR #48 Review Finding = ACCEPTED**

正式接受：

```
Identity Resolution Boundary                = COMPLETE
Relationship Resolution Boundary            = COMPLETE
Mapping Conflict / Failure Boundary         = COMPLETE
Mapping Provenance Requirement              = COMPLETE
registered source-semantic unresolved count = 0
new canonical identity / relationship / source-semantic mapping gap = 未发现
```

并接受：

```
Final Master Data Mapping 当前仍不得直接 closure
```

**接受的主要 blocker（`B-1` ／ `B-2`）：**

```
B-1：Final Master Data Mapping scope 尚未正式定义
B-2：closure criteria 尚未作为 current canonical rule 正式登记
```

**决定 2 —— `Final Master Data Mapping` Scope = DEFINED ＋ APPROVED FOR REGISTRATION**

正式批准：

```
Final Master Data Mapping
  = Master Data Mapping conceptual design 的最终 closure layer
```

**其 scope 包括：**

- canonical identity resolution
- canonical relationship resolution
- source-semantic resolution
- mapping ambiguity ／ conflict ／ unresolved behavior
- mapping provenance requirement
- 已批准的 conceptual applicability ／ resolution contracts

**其 scope 明确不包括：**

- real ERP vendor ／ version
- source table selection
- source column selection
- physical source-field realization
- serialization format
- physical dataset layout
- `Field Carrier Mapping`
- `Final Import Contract`
- Adapter implementation
- runtime implementation
- production testing

该 scope 裁定**不改变** `Snapshot / Import Contract` 与 `Adapter Boundary` 的既有状态。

**决定 3 —— Conceptual Closure Boundary = CONFIRMED**

```
Conceptual Master Data Mapping Closure
  ≠ Real ERP Mapping Completed
  ≠ Adapter Implemented
  ≠ Physical Import Contract Completed
  ≠ Tested Production Integration
```

**决定 4 —— Minimum Closure Criteria = APPROVED（`MC-1` ～ `MC-8` ＋ `MC-10`）**

正式接受 PR #48 Review Finding 提出的 **`MC-1` ～ `MC-8`** 与 **`MC-10`**（**原文不变**）
作为 `Final Master Data Mapping` 的 **minimum closure criteria**。

**决定 5 —— `MC-9` = AMENDED ＋ APPROVED**

`MC-9` **按以下修正文本**批准（取代 Review Finding 中的原始表述）：

```
MC-9：
Master Data Mapping scope 内不得存在：

  - 未登记的 canonical mapping gap
  - 未分类的 mapping gap
  - 未评估 closure impact 的 mapping gap
```

对于**已经明确文档化**、且**已确认属于 Master Data Mapping scope 之外**的 deferral：

```
不得要求为了 closure 重复复制进入统一 design-item registry
```

只要求：

```
原位置仍可追踪
scope attribution 明确
closure impact 已明确判定
```

因此：

```
G-5 quantity precision ／ rounding ／ UoM conversion  = NON-BLOCKING
G-6 PerformancePeriod period policy                   = NON-BLOCKING
```

**不得**因「未进入统一 registry」而**间接**使 `G-5` ／ `G-6` 变成
`Master Data Mapping` closure blocker。

**决定 6 —— Gap Decision = CONFIRMED（`G-3` ～ `G-11` = NON-BLOCKING）**

在当前 **Master Data Mapping conceptual closure scope** 下，正式确认：

```
G-3   real ERP source-field mapping                    = NON-BLOCKING
G-4   BOM explosion algorithm                          = NON-BLOCKING
G-5   quantity precision ／ rounding ／ UoM conversion  = NON-BLOCKING（已文档化）
G-6   PerformancePeriod period policy                   = NON-BLOCKING（已文档化）
G-7   normalization policy                              = NON-BLOCKING
G-8   cross-package mapping                             = NON-BLOCKING
G-9   physical carrier realization                      = NON-BLOCKING
G-10  Adapter Boundary                                  = NON-BLOCKING
G-11  独立 consistency cleanup                           = NON-BLOCKING
```

其中：

- `G-3` ／ `G-9` ／ `G-10` **明确属于其他 design ／ implementation domain**；
- `G-5` ／ `G-6` **已文档化**，**不属于** canonical mapping closure blocker，
  **不要求**额外建立统一 registry 才允许 closure；
- `G-11` 属于**独立 consistency cleanup**，**不阻塞** `Master Data Mapping` closure。

`G-1` ／ `G-2`（＝ `B-1` ／ `B-2`）**不因本决定而消失** —— 由 **决定 8** 的 follow-up registration 处理。

**决定 7 —— Snapshot / Import Contract Boundary = CONFIRMED（再次确认）**

```
Master Data Mapping closure  ≠  Snapshot / Import Contract closure
```

**无论**后续 `Master Data Mapping` 是否 `DESIGN RESOLVED`：

```
Snapshot / Import Contract overall = DESIGN PENDING
```

**直到**其自身以下四项**分别完成**：

```
Serialization Format
Physical Dataset Layout
Field Carrier Mapping
Final Import Contract
```

**决定 8 —— Follow-up Implementation Authorization = AUTHORIZED**

授权**后续独立 Design Change ／ Implementation PR** 执行：

```
1. 正式登记 Final Master Data Mapping scope
2. 正式登记 MC-1 ～ MC-10
   （使用本 Human Decision 修正后的 MC-9）
3. 同步 current-state references
4. 执行完整 validation
```

**本 PR 不执行上述任何一项。**

**决定 9 —— Conditional Closure Authorization = AUTHORIZED（条件性）**

**如果**该 follow-up Implementation PR 在实施后确认：

```
MC-1 ～ MC-10 全部满足
且没有发现新的 blocking canonical mapping gap
```

**则授权在同一个 follow-up Implementation PR 中**执行：

```
Final Master Data Mapping    DESIGN PENDING → DESIGN RESOLVED
Master Data Mapping overall  DESIGN PENDING → DESIGN RESOLVED
```

**不得**因此修改：

```
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
```

**如果条件不满足**：**不得**执行上述状态变更，必须重新进入 **Human Attention**。

**决定 10 —— Historical Record Preservation = CONFIRMED**

**PR #48 Review Finding 必须完整保留**，尤其其 **Review 时点**表述：

```
MC-1                        = 未满足
MC-9                        = 部分未满足
Final Master Data Mapping   = DESIGN PENDING
Master Data Mapping overall = DESIGN PENDING
```

**不得回写** PR #48 Review Finding。本节的 **Human Decision Record** 是对其的**最终裁定**，
通过**新增记录**表达，**不修改** Review Finding 原文。

**决定 11 —— Explicit Non-Authorization**

本 Human Decision **不授权**：

- real ERP mapping
- source table ／ column design
- physical schema
- Adapter design
- `Snapshot / Import Contract` design
- new canonical entity
- new canonical business field
- `BR-*` changes
- Validation Taxonomy changes
- AI ／ Tool Boundary changes
- independent stale cleanup（`§4.3.17` ／ `§4.4.41` ／ `§4.5.12`）

**执行状态（PR #48 Human Decision 时点）**

```
PR #48 Review Finding               = ACCEPTED
B-1 Final Master Data Mapping scope = CONFIRMED（Review 时点为未定义）
B-2 closure criteria                = CONFIRMED（Review 时点为未登记）
Final Master Data Mapping scope     = HUMAN APPROVED FOR REGISTRATION
Closure Criteria MC-1 ～ MC-10       = HUMAN APPROVED FOR REGISTRATION
Follow-up conditional closure       = AUTHORIZED

Final Master Data Mapping           = DESIGN PENDING   ← 未关闭
Master Data Mapping overall         = DESIGN PENDING   ← 未关闭
Snapshot / Import Contract overall  = DESIGN PENDING   ← 未关闭（独立）
Adapter Boundary                    = DESIGN PENDING
scope registration                  = NOT YET EXECUTED
closure                             = NOT YET EXECUTED
POC Design v0.2                     = DRAFT
```

**本 PR 只记录 Human Decision。**
**未**实施 scope registration，**未**实施 closure，
**未**修改 `Final Master Data Mapping` ／ `Master Data Mapping overall` 的 status。

**Final Master Data Mapping Closure Implementation Record（Human-authorized Design Change）**

**Human Authorization Source**

```
PR #48 Human Decision — Human-approved
  → 决定 2：Final Master Data Mapping Scope        = APPROVED FOR REGISTRATION
  → 决定 4：MC-1 ～ MC-8 ＋ MC-10                  = APPROVED
  → 决定 5：MC-9                                  = AMENDED ＋ APPROVED
  → 决定 6：G-3 ～ G-11                           = NON-BLOCKING
  → 决定 7：Snapshot / Import Contract Boundary    = CONFIRMED
  → 决定 8：follow-up registration                 = AUTHORIZED
  → 决定 9：conditional closure                    = AUTHORIZED（条件满足时）
  → 决定 11：Explicit Non-Authorization            = CONFIRMED
```

**Registration Result**

```
Final Master Data Mapping scope         = REGISTERED（§4.5.25 A）
Closure Criteria MC-1 ～ MC-10           = REGISTERED（§4.5.25 B）
MC-9                                    = 使用 Human Decision 修正版
Conceptual Closure Boundary             = REGISTERED（§4.5.25 A）
```

**MC-1 ～ MC-10 Validation Result**

| # | Criterion | Result |
| --- | --- | --- |
| **MC-1** | `Final Master Data Mapping` **scope 已正式登记**（`§4.5.25 A`） | **PASS** |
| **MC-2** | 全部 constituent mapping layers 均为 `DESIGN RESOLVED` | **PASS**（10 / 10） |
| **MC-3** | mapping scope 内**无** registered unresolved item | **PASS**（`§4.1.12` ／ `§4.4.41` ／ `§4.4.101` ／ `§4.5.22` ／ `§11` 均为 0） |
| **MC-4** | 每个具 canonical identity 的 entity 都有 identity resolution boundary | **PASS**（A ～ O ＋ Warehouse） |
| **MC-5** | 每个 canonical relationship 都有 relationship resolution boundary | **PASS** |
| **MC-6** | 每个被 Rule 使用的 source-specific vocabulary ／ semantic 都有 mapping contract 或 canonical vocabulary 定义 | **PASS** |
| **MC-7** | 每个 mapping 层都有 explicit ambiguity ／ conflict ／ unresolved behaviour，且**无 silent precedence** | **PASS** |
| **MC-8** | 每个成功 mapping 都被 logical provenance requirement 覆盖 | **PASS** |
| **MC-9** | scope 内**无**未登记 ／ 未分类 ／ 未评估 closure impact 的 mapping gap（**修正版**） | **PASS** |
| **MC-10** | Conceptual Closure Boundary **已正式登记** | **PASS** |

**New Blocking Gap Audit**

```
已知 deferral（G-3 ～ G-11）          = NON-BLOCKING（严格继承 PR #48 Human Decision 决定 6）
new blocking canonical mapping gap  = NONE
```

审计结论：registration 后**未发现**任何此前未知的 blocking canonical mapping gap；
**未**将任何既有 `NON-BLOCKING` 项升级为 blocker。

**Conditional Closure Result**

```
MC-1 ～ MC-10                       = ALL PASS
New Blocking Canonical Mapping Gap  = NONE
  → conditional closure gate         = PASS
```

因此执行（**PR #48 Human Decision 决定 9** 授权）：

```
Final Master Data Mapping    DESIGN PENDING → DESIGN RESOLVED
Master Data Mapping overall  DESIGN PENDING → DESIGN RESOLVED
Master Data Mapping layers   10 / 11 → 11 / 11 DESIGN RESOLVED
```

**Current-State Synchronization**

| 位置 | 同步内容 |
| --- | --- |
| `§4` 子领域表 | `Master Data Mapping` → `DESIGN RESOLVED`；`DESIGN PENDING` 子领域 3 → 2 |
| `§4.4.101 Dependency Boundary` | `Master Data Mapping` → `DESIGN RESOLVED` |
| `§4.5` 子章节状态块 | 子章节整体状态 → `DESIGN RESOLVED`；`仍为 DESIGN PENDING 的层级` → 无 |
| `§4.5` 层级状态登记表 | `Final Master Data Mapping` → `DESIGN RESOLVED` |
| `§4.5.12` | physical realization 归属的最小 direct-contradiction sync（归 `§4.3`） |
| `§4.5.22 NEXT REQUIRED DESIGN REVIEW` | conditional closure 已执行 |
| `§4.5.24 Status Boundary` | 各 current-state 语句同步为 `11 / 11` ／ `DESIGN RESOLVED` |
| `§4.5.25`（新增） | `Final Master Data Mapping` scope 与 `MC-1` ～ `MC-10` 正式登记 |

**Historical Preservation（未回写）**

- **PR #44 Review Finding ／ Human Decision Record**
- **PR #45 Option D Implementation Record**（含 `DESIGN RESOLVED layer 数现为 10`）
- **PR #46 Review Finding ／ Human Decision Record**
- **PR #47 Validation Taxonomy Implementation Record**
- **PR #48 Review Finding**（含 `MC-1 = 未满足` ／ `MC-9 = 部分未满足` ／ `10 / 11` ／ `DESIGN PENDING`）
- **PR #48 Human Decision Record**（含 `scope registration = NOT YET EXECUTED` ／ `closure = NOT YET EXECUTED`）
- 各 **`执行状态（…时点）`** ／ **`Status（…时点）`** 块

**Scope Boundary（保持）**

```
Snapshot / Import Contract overall = DESIGN PENDING
  Serialization Format             = DESIGN PENDING
  Physical Dataset Layout          = DESIGN PENDING
  Field Carrier Mapping            = DESIGN PENDING
  Final Import Contract            = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING

Master Data Mapping closure  ≠  Snapshot / Import Contract closure
```

**Meaning of `DESIGN RESOLVED`**

`Final Master Data Mapping = DESIGN RESOLVED` **只**表示
**canonical / conceptual Master Data Mapping design 已完成**，
**不表示**：

```
real ERP mapping completed
source table / column known
physical schema exists
Adapter implemented
physical import contract completed
data validated / tested
production-ready
```

**执行状态（本 Task 完成时点）**

```
Human Authorization Source          = PR #48 Human Decision
Final Master Data Mapping scope     = REGISTERED
Closure Criteria MC-1 ～ MC-10       = REGISTERED（MC-9 修正版）
MC-1 ～ MC-10                       = PASS
New Blocking Canonical Mapping Gap  = NONE
Conditional Closure Gate            = PASS
Final Master Data Mapping           = DESIGN RESOLVED
Master Data Mapping overall         = DESIGN RESOLVED
Master Data Mapping layers          = 11 / 11 DESIGN RESOLVED
Snapshot / Import Contract overall  = DESIGN PENDING
Adapter Boundary                    = DESIGN PENDING
POC Design v0.2                     = DRAFT
```

#### 4.5.23 Examples

以下为 **conceptual examples**。

**Example A — Material Resolved** —— source evidence 含 material identity；
explicit mapping evidence `Source Material X → canonical MAT-A`
→ **resolved**，usable in canonical context。

**Example B — Material Ambiguous** —— `Source Material X` 可映射到 `MAT-A` **或** `MAT-B`，
**no approved precedence** → **`UNRESOLVED_IDENTITY`**；**不得选择一个**。

**Example C — Supplier Name Only** —— source 为「云南某供应商」，
没有可靠 supplier identity mapping → **不得仅按名字**创建 canonical `supplier_id`。

**Example D — BOM Component Unresolved** —— Parent Material resolved；
Component Material **cannot be resolved** → `Gross Requirement` cannot form normal result
→ **`DATA_INCOMPLETE`**。

**Example E — Supplier Exists but Relationship Missing** —— `Supplier-A` exists、`MAT-A` exists，
但无 reliably resolved Supplier-Material Relationship → **不得假定** `Supplier-A` can supply `MAT-A`。

**Example F — Warehouse Unknown** —— Inventory record 的 Plant context 因 Warehouse ownership
unclear 而 unresolved → **不得**将 inventory 计入当前 Plant aggregation。

**Example G — Cross-Package Mapping** —— Analysis Run R1 绑定 Package P1；
business evidence 来自 P1，但 Material mapping 取自 P2
→ **`PROVENANCE_MISMATCH`**；**不得静默使用**。

> `Warehouse Role Resolution` 的 acceptance examples（**Example A ～ Example F**）见 **§4.5.12**。

#### 4.5.24 Status Boundary

`Master Data Mapping` overall **现为 `DESIGN RESOLVED`** ——
本节已完成 Canonical Identity Resolution、Relationship Resolution Boundary、
**Warehouse Role Resolution**（**§4.5.12**）、
**BOM Version / Validity Mapping**（**§4.5.7** ／ **§4.1.4 N**）、
**Supplier Eligibility Vocabulary Mapping**（**§4.5.11**）、
**Effective Arrival Date Source Mapping**（**§4.5.21**）、
**Allocation Demand-Window Mapping**（**§4.5.9**）
与 **Other Source-Semantic Mapping**（**§4.5.22**）
与 **Final Master Data Mapping**（**§4.5.25**）。

`DESIGN RESOLVED` 的十一个层级**仅**表示其 **conceptual resolution boundary 已定义**，
**不表示**：

- 真实 ERP mapping 已完成
- source table / column 已确定
- mapping implementation exists
- data validated
- tested

**Important Non-Resolution：**

**不得声称**真实 ERP Mapping 已完成。因为当前项目是 **`SIMULATED` POC**，
且**没有真实** ERP vendor / schema / field list / master-data specification。

本轮只完成 **conceptual resolution boundary**。

**Blocking Finding —— RESOLVED：** `BOM Version / Validity Mapping` **现为 `DESIGN RESOLVED`** ——
其 **BOM Applicability Design Review** 曾判定 `Canonical Model Compatibility = INSUFFICIENT`；
该冲突已由 **Human-approved Option A ＋ Canonical Model Amendment** 解决
（见 **§4.5.7 Option A Implementation Record** ／ **§4.1.4 N**）。

`DESIGN RESOLVED` **只**表示 **POC canonical applicability mapping 概念设计已完成**，
**不表示**：

- real ERP BOM mapping implemented
- ERP version fields known
- BOM selection code exists
- BOM explosion implemented
- tested

**Option B —— IMPLEMENTED：** `Supplier Eligibility Vocabulary Mapping` **现为 `DESIGN RESOLVED`** ——
其 **Option B**（source-specific `sourcing_status` → conceptual eligibility condition）
已由 **Human-authorized Design Change** 实施，`§4.1` / `§4.2` / `§4.4` 已完成最小 semantic synchronization
（见 **§4.5.11 Option B Implementation Record**）。

`DESIGN RESOLVED` **只**表示 **POC canonical eligibility mapping contract 概念设计已完成**，
**不表示**：

- actual source values known
- ERP / SRM vocabulary known
- Adapter mapping implemented
- mapping configuration exists
- Supplier Risk implemented
- tested

**Option D —— IMPLEMENTED：** `effective_arrival_date` source mapping **现为 `DESIGN RESOLVED`** ——
其 **Option D**（source-specific arrival-date evidence → explicit deterministic mapping →
exactly one canonical `effective_arrival_date` 或 `unresolved`）
已由 **Human-authorized Design Change** 实施，`§4.2` / `§4.4` / `§4.5` 已完成最小 semantic synchronization
（见 **§4.5.21 Option D Implementation Record**）。

**`Other Source-Semantic Mapping` 现为 `DESIGN RESOLVED`** ——
其最后一个 internal unresolved item `provenance carrier` 已由 **§4.5.22 Option D Implementation Record** 解析。

`DESIGN RESOLVED` **只**表示 **canonical source-mapping contract 概念设计完成**，
**不表示** real ERP field known / Adapter implemented / mapping tested / `Effective Inbound` implemented。

**Option B —— IMPLEMENTED：** `allocation demand-window mapping` **现为 `DESIGN RESOLVED`** ——
其 **Option B**（source-specific allocation evidence → explicit deterministic mapping →
canonical **Target Applicability** ＋ **Source Reservation Overlap**）
已由 **Human-authorized Design Change** 实施，`§4.1` / `§4.2` / `§4.4` / `§4.5` 已完成最小 semantic synchronization
（见 **§4.5.9 Option B Implementation Record**）。

**`Other Source-Semantic Mapping` 现为 `DESIGN RESOLVED`** ——
其最后一个 internal unresolved item `provenance carrier` 已由 **§4.5.22 Option D Implementation Record** 解析。

`DESIGN RESOLVED` **只**表示 **canonical allocation applicability mapping contract 概念设计完成**，
**不表示** real ERP allocation evidence known / reservation source field known / Adapter implemented /
overlap calculation implemented / allocation enforcement implemented / tested。

**Canonical Model Amendment —— IMPLEMENTED：** `required_quantity` 已 **`REMOVED FROM POC v0.2 CANONICAL MODEL`** ——
其 **Required Quantity Semantic & Canonical Necessity Review** 判定
**`required_quantity = ORPHAN CANONICAL FIELD`**
（无 approved business semantic、**0 个 Rule consumer**、两份 `FROZEN` 文档均无 source evidence、
无独立 grain、删除不影响任何既有 approved calculation），
该结论与**从 `§4.1` attributes ＋ `§4.2` Data Dictionary 移除**均已获 **Human Approval**，
并已由 **Human-authorized Canonical Model Amendment** **实施完成**
（见 **§4.2.4** Human Decision Record ＋ **Required Quantity Removal Implementation Record**）。

```
required_quantity = REMOVED FROM CURRENT CANONICAL MODEL
unresolved count  = 4 → 3
```

**未新增**任何 Master Data Mapping layer —— 这是 **canonical model cleanup / amendment**，
**不是**新的 resolved layer。

**Option E —— IMPLEMENTED：** `loss_rate` canonical owner / grain **现为 `DESIGN RESOLVED`** ——
其 **Option E**（Calculation-Context Configuration ＋ resolution-contract form）
已由 **Human-authorized Design Change** 实施，`§4.1` ／ `§4.2` ／ `§4.4` ／ `§4.5`
已完成最小 semantic synchronization（见 **§4.5.22 Option E Implementation Record**）。

```
Human Decision                    = RECORDED
Option E                          = IMPLEMENTED
loss_rate canonical owner / grain = DESIGN RESOLVED
owner                             = Requirement Calculation Context
resolution contract               = exactly one applicable loss_rate or unresolved
Logical Provenance Carrier         = DESIGN RESOLVED
Physical Carrier Realization       = DESIGN PENDING（§4.3 Field Carrier Mapping / Final Import Contract）
unresolved count                  = 3 → 2
```

**`Other Source-Semantic Mapping` 现为 `DESIGN RESOLVED`** ——
其最后一个 internal unresolved item `provenance carrier` 已由 **§4.5.22 Option D Implementation Record** 解析。

`DESIGN RESOLVED` **只**表示 **canonical owner / applicability grain / resolution contract 概念设计完成**，
**不表示** real ERP source known / source field known / Adapter implemented / tested /
`GrossRequirement` engine implemented。

**未新增**任何 Master Data Mapping layer —— 这是 **`Other Source-Semantic Mapping`
内部 unresolved item 的关闭**，**不是**新的 resolved layer；`DESIGN RESOLVED` layer 数现为 **11**（**`Final Master Data Mapping` 现为 `DESIGN RESOLVED`**）。

**Option D —— IMPLEMENTED：** `ApplicableMOQ` source / applicability **现为 `DESIGN RESOLVED`** ——
其 **Option D**（Source-Specific Purchasing-Policy Resolution ＋ resolution-contract form）
已由 **Human-authorized Design Change** 实施，`§4.1` ／ `§4.2` ／ `§4.4` ／ `§4.5`
已完成最小 semantic synchronization（见 **§4.5.22 Option D Implementation Record**）。

```
Human Decision                       = RECORDED
Option D                             = IMPLEMENTED
ApplicableMOQ source / applicability = DESIGN RESOLVED
owner                                = Requirement Calculation Context（Procurement Recommendation Context）
resolution contract                  = exactly one applicable ApplicableMOQ or unresolved
Supplier Selection                   = NOT INTRODUCED
unresolved count                     = 2 → 1
```

**`Other Source-Semantic Mapping` 现为 `DESIGN RESOLVED`** ——
其最后一个 internal unresolved item `provenance carrier` 已由 **§4.5.22 Option D Implementation Record** 解析。

`DESIGN RESOLVED` **只**表示 **canonical applicability ＋ source semantic resolution contract
概念设计完成**，**不表示** real ERP source known / Supplier selected / Contract known /
PIR known / Adapter implemented / procurement engine implemented / tested。

**Option D —— IMPLEMENTED：** `provenance carrier` **现为 `DESIGN RESOLVED`** ——
其 **Option D**（**Layered Logical Provenance Contract**）已由 **Human-authorized Design Change** 实施，
`§4.2` ／ `§4.3` ／ `§4.4` ／ `§4.5` 已完成最小 semantic synchronization
（见 **§4.5.22 Option D Implementation Record**）。

```
Human Decision                       = RECORDED
Option D                             = IMPLEMENTED
Layered Logical Provenance Contract  = IMPLEMENTED
provenance carrier                   = DESIGN RESOLVED
unresolved count                     = 1 → 0
Other Source-Semantic Mapping        = DESIGN RESOLVED
Final Master Data Mapping            = DESIGN PENDING   ← 未关闭（PR #45 时点）
Master Data Mapping overall          = DESIGN PENDING   ← 未关闭（PR #45 时点）
Snapshot / Import Contract overall   = DESIGN PENDING
Validation Taxonomy Limitation       = DESIGN RESOLVED
```

`DESIGN RESOLVED` **只**表示 **logical provenance carrier contract 概念设计完成**，
**不表示** real ERP source known / Adapter implemented / physical carrier finalized / tested。

**未新增**任何 Master Data Mapping layer —— `Other Source-Semantic Mapping` 是**既有层**，
本 Task 只关闭其**最后一个 internal unresolved item**。
`DESIGN RESOLVED` layer 数现为 **11**；`Final Master Data Mapping` **现为 `DESIGN RESOLVED`**。

**`Master Data Mapping` overall 现为 `DESIGN RESOLVED`** ——
`Final Master Data Mapping` 的 scope 与 `MC-1` ～ `MC-10` 已正式登记并全部 `PASS`
（见 **§4.5.25** ／ **§4.5.22 Final Master Data Mapping Closure Implementation Record**）；
**`unresolved count = 0` 本身不构成 closure 依据**（**PR #44 Human Decision 決定 18** 保持有效）。

**须另行进行的独立 Review：**

```
1. Validation Taxonomy Design Review
     —— **已完成**：Review Finding 与 Human Decision Record 见 **§4.5.22**；
        taxonomy implementation 见 **§4.5.22 Validation Taxonomy Implementation Record**
2. Master Data Mapping Closure Review
     —— **已完成**：Review Finding ／ **Human Decision Record** ／
        **Final Master Data Mapping Closure Implementation Record** 见 **§4.5.22**
     —— **scope ＋ `MC-1` ～ `MC-10` = `REGISTERED`**；`MC-1` ～ `MC-10` = **`PASS`**；
        **conditional closure 已执行**
     —— `Final Master Data Mapping` ／ `Master Data Mapping` overall **现为 `DESIGN RESOLVED`**
```

```
Validation Taxonomy Limitation = DESIGN RESOLVED
PROVENANCE_MISMATCH semantic   = UNCHANGED
Final Master Data Mapping      = DESIGN RESOLVED
Master Data Mapping overall    = DESIGN RESOLVED
```

**须另行进行的独立 Review：**

```
1. Validation Taxonomy Design Review
     —— **已完成**（见 **§4.5.22 Validation Taxonomy Implementation Record**）
2. Master Data Mapping Closure Review
     —— **已完成**：Review Finding ／ **Human Decision Record** ／
        **Final Master Data Mapping Closure Implementation Record** 见 **§4.5.22**
     —— **scope ＋ `MC-1` ～ `MC-10` = `REGISTERED`**；`MC-1` ～ `MC-10` = **`PASS`**；
        **conditional closure 已执行**
     —— `Final Master Data Mapping` ／ `Master Data Mapping` overall **现为 `DESIGN RESOLVED`**
```

**Validation Taxonomy Design Change —— IMPLEMENTED：** `Validation Taxonomy Limitation`
**现为 `DESIGN RESOLVED`** ——
其 **PR #46 Human Decision**（**`PROVENANCE_UNRESOLVED` = `APPROVED FOR IMPLEMENTATION`**）
已由 **Human-authorized Design Change** 实施，`§4.4` 已完成最小 canonical taxonomy synchronization
（见 **§4.5.22 Validation Taxonomy Implementation Record**）。

```
Human Decision                       = RECORDED
PROVENANCE_UNRESOLVED                = IMPLEMENTED / CANONICAL
Canonical Categories                 = 8
Canonical Reasons                    = 12
PROVENANCE_MISMATCH semantic         = UNCHANGED
Validation Taxonomy Limitation       = DESIGN RESOLVED
```

`DESIGN RESOLVED` **只**表示 **canonical validation taxonomy 概念设计已完成**，
**不表示** runtime validator implemented ／ API implemented ／ enum implemented ／
schema implemented ／ Adapter implemented ／ tested production behavior。

**Validation Taxonomy Design Change 未变更** `§4.5` layer status —— 本 Task **不是**
Master Data Mapping layer 变更；`DESIGN RESOLVED` layer 数**现为 11**；
`Final Master Data Mapping` **现为 `DESIGN RESOLVED`**；
`Master Data Mapping` overall **现为 `DESIGN RESOLVED`**（见 **§4.5.25**）。

**Master Data Mapping Closure Review —— COMPLETED（Review Finding only，本 Review 时点）：**
`Final Master Data Mapping` 的 closure 条件已由独立 Review 审查
（见 **§4.5.22 Master Data Mapping Closure Review（Review Finding）**）。

```
Final Master Data Mapping   = DESIGN PENDING   ← 本 Review 时点
Master Data Mapping overall = DESIGN PENDING   ← 本 Review 时点
closure criteria            = 未满足（MC-1 ／ MC-9）（本 Review 时点）
Human Decision              = NOT YET（本 Review 时点）
```

**本 Review 不实施 closure，也不改变任何 status。**
上述状态在 **PR #48 Human Decision** 之后，已由 **Final Master Data Mapping Closure Implementation**
正式推进 —— `Final Master Data Mapping` 与 `Master Data Mapping` overall **现为 `DESIGN RESOLVED`**
（见 **§4.5.25** ／ **§4.5.22 Final Master Data Mapping Closure Implementation Record**）。
`Master Data Mapping closure` **≠** `Import Contract closure`（**決定 20** 保持有效）。

**Human Decision Recorded —— `Final Master Data Mapping` scope ＋ `MC-1` ～ `MC-10` APPROVED FOR REGISTRATION（PR #48 时点）：**
**Human Decision** 已记录（见 **§4.5.22 Human Decision Record**）：
`Final Master Data Mapping` 当时**不被关闭**；其 **scope** 与 **minimum closure criteria**
已获批准并**待正式登记**（registration 已于后续 **Final Master Data Mapping Closure Implementation** 执行）。

```
Final Master Data Mapping          = DESIGN PENDING   ← 本记录时点
Master Data Mapping overall        = DESIGN PENDING   ← 本记录时点
Snapshot / Import Contract overall = DESIGN PENDING   ← 未关闭（独立）
Adapter Boundary                   = DESIGN PENDING
Final Master Data Mapping scope    = HUMAN APPROVED FOR REGISTRATION
Closure Criteria MC-1 ～ MC-10      = HUMAN APPROVED FOR REGISTRATION
Follow-up conditional closure      = AUTHORIZED
registration / closure             = NOT YET EXECUTED（本记录时点）
```

**该 Task 只记录 Human Decision** —— **未**实施 scope registration，**未**实施 closure。
`Master Data Mapping closure` **≠** `Import Contract closure`（**決定 20** 保持有效）；
`Snapshot / Import Contract overall` 与 `Adapter Boundary` **仍为 `DESIGN PENDING`**。

**Final Master Data Mapping Closure —— IMPLEMENTED：** `Final Master Data Mapping`
**现为 `DESIGN RESOLVED`** ——
其 **scope** 与 **`MC-1` ～ `MC-10`** 已由 **PR #48 Human Decision** 授权并正式登记（见 **§4.5.25**）；
**conditional closure gate = `PASS`**
（见 **§4.5.22 Final Master Data Mapping Closure Implementation Record**）。

```
Final Master Data Mapping          = DESIGN RESOLVED
Master Data Mapping overall        = DESIGN RESOLVED
Master Data Mapping layers         = 11 / 11 DESIGN RESOLVED
Snapshot / Import Contract overall = DESIGN PENDING   ← 未关闭（独立）
Adapter Boundary                   = DESIGN PENDING
```

> **时点说明 ／ supersede：** 本节的状态块（含上方 `本记录时点` 块与 **Final Master Data Mapping closure 实施块**）
> 均为**该 closure 时点**的 snapshot（历史值**保留不回写**，**不**代表 latest current state）；
> 其中 `Snapshot / Import Contract overall` 已由 **Issue #66 Closure**、`Adapter Boundary` 已由
> **Issue #90 Closure Validation = `PASS`** 分别 supersede ⇒ 最新状态见 **§4.3.29** ／ **§4.6.22**。

`DESIGN RESOLVED` **只**表示 **canonical / conceptual Master Data Mapping design 已完成**，
**不表示** real ERP mapping ／ source table ／ column known ／ physical schema exists ／
Adapter implemented ／ physical import contract completed ／ tested。
`Master Data Mapping closure` **≠** `Import Contract closure`（**決定 20** 保持有效）。

---

#### 4.5.25 Final Master Data Mapping Scope & Minimum Closure Criteria

**Registration Status：`REGISTERED`** ——
依据 **PR #48 Human Decision**（决定 2 ／ 4 ／ 5 ／ 8），见 **§4.5.22 Human Decision Record**。

**A. `Final Master Data Mapping` Scope（正式登记）**

```
Final Master Data Mapping
  = Master Data Mapping conceptual design 的最终 closure layer
```

**其 scope 包括：**

- canonical identity resolution
- canonical relationship resolution
- source-semantic resolution
- mapping ambiguity ／ conflict ／ unresolved behavior
- mapping provenance requirement
- 已批准的 conceptual applicability ／ resolution contracts

**其 scope 明确不包括：**

- real ERP vendor ／ version
- source table selection
- source column selection
- physical source-field realization
- serialization format
- physical dataset layout
- `Field Carrier Mapping`
- `Final Import Contract`
- Adapter implementation
- runtime implementation
- production testing

**Conceptual Closure Boundary（正式登记）：**

```
Conceptual Master Data Mapping Closure
  ≠ Real ERP Mapping Completed
  ≠ Adapter Implemented
  ≠ Physical Import Contract Completed
  ≠ Tested Production Integration
```

**B. Minimum Closure Criteria `MC-1` ～ `MC-10`（正式登记）**

| # | Minimum Closure Criterion |
| --- | --- |
| **MC-1** | `Final Master Data Mapping` 的 **scope 被正式定义**（见本节 `A`） |
| **MC-2** | 全部 constituent mapping layers 均为 `DESIGN RESOLVED` |
| **MC-3** | mapping scope 内**无** registered unresolved item |
| **MC-4** | 每个具 canonical identity 的 canonical entity 都有 identity resolution boundary |
| **MC-5** | 每个 canonical relationship 都有 relationship resolution boundary |
| **MC-6** | 每个被 Rule 使用的 source-specific vocabulary ／ semantic 都有 canonical mapping contract，或已被既有 canonical vocabulary 定义 |
| **MC-7** | 每个 mapping 层都有 explicit ambiguity ／ conflict ／ unresolved behaviour，且**无 silent precedence** |
| **MC-8** | 每个成功 mapping 都被 logical provenance requirement 覆盖 |
| **MC-9** | Master Data Mapping scope 内**不得存在**：未登记的 canonical mapping gap ／ 未分类的 mapping gap ／ 未评估 closure impact 的 mapping gap。对于**已经明确文档化**、且**已确认属于 Master Data Mapping scope 之外**的 deferral：**不得要求**为了 closure 重复复制进入统一 design-item registry；只要求 **原位置仍可追踪** ＋ **scope attribution 明确** ＋ **closure impact 已明确判定** |
| **MC-10** | closure 的语义边界被显式登记（见本节 `A` 的 **Conceptual Closure Boundary**） |

**C. `MC-9` 适用范围（正式登记）**

```
G-5 quantity precision ／ rounding ／ UoM conversion  = NON-BLOCKING
G-6 PerformancePeriod period policy                   = NON-BLOCKING

G-3 real ERP source-field mapping   = NON-BLOCKING（属其他 design ／ implementation domain）
G-9 physical carrier realization    = NON-BLOCKING（属其他 design domain）
G-10 Adapter Boundary               = NON-BLOCKING（属其他 design domain）
G-4 ／ G-7 ／ G-8 ／ G-11            = NON-BLOCKING
```

**不得**因「未进入统一 design-item registry」而**间接**使上述 deferral 变成
`Master Data Mapping` closure blocker。

**D. Registration Boundary**

- 本节**不新增** canonical entity ／ canonical business field，**不修改** `BR-*`。
- 本节**不代表** real ERP mapping ／ Adapter ／ physical import contract ／ tested production integration 已完成。
- `Master Data Mapping closure` **≠** `Snapshot / Import Contract closure`。

**E. Closure Result**

```
Final Master Data Mapping scope    = REGISTERED
Closure Criteria MC-1 ～ MC-10      = REGISTERED
MC-1 ～ MC-10                      = ALL PASS
New Blocking Canonical Mapping Gap = NONE
Final Master Data Mapping          = DESIGN RESOLVED
Master Data Mapping overall        = DESIGN RESOLVED
Master Data Mapping layers         = 11 / 11 DESIGN RESOLVED
```

#### 4.5.26 First-Tranche Canonicalization Mapping Boundary（Issue #125 Human Decision Record）

**Registration Status：`REGISTERED`** —— 依据 **Issue #125 Human Decision**（**D-1 ～ D-10 全部 `APPROVED`**）。

本小节只登记 first deterministic tranche 的 canonicalization 如何复用既有 Master Data Mapping
resolution boundary；它**不新增** mapping layer、**不新增** unresolved item、**不修改** `MC-1` ～ `MC-10`。

**A. 复用既有 resolution contract（未变）**

```
loss_rate        : owner = Requirement Calculation Context
                   resolution contract = exactly one applicable loss_rate or unresolved（§4.5.22 Option E）
ApplicableMOQ    : owner = exact Procurement Recommendation Context
                   resolution contract = exactly one applicable ApplicableMOQ or unresolved（§4.5.22 Option D）
physical carrier : 两者均为 SOURCE-SPECIFIC ／ not yet defined
```

resolution 的 outcome 语义与 conflict 语义按 **§4.4.102** 的 Stage A ／ Stage B 处理；
无 approved precedence 时**不得**自行裁决（§4.4.67 ／ §4.4.12 ／ §4.4.13）。

**B. Grain representation 复用（未变）**

```
BOM Component        : requirement-scoped grain；parent ／ requirement context 由 §4.1.13 C 的
                       resolved context reference 提供（§4.5.7 保持）
Substitute Allocation: effective demand context = read-only reference object（§4.1.13 D ／ §4.5.9 保持）
Inbound Supply       : first-tranche identity representation = G3-A technical record reference（§4.3.31 D）
```

**C. 未新增 unresolved item**

```
Master Data Mapping layers            = 11 / 11 DESIGN RESOLVED（未变）
New Blocking Canonical Mapping Gap    = NONE（未变）
source-specific ／ real Adapter inbound business identity = OPEN
      （属 §4.3.30 F 的既有登记项；revisit before real Adapter or production integration）
```

本登记**不**把 `§4.3.30 F` 的 source-specific item 计入 Master Data Mapping closure blocker，
也**不**声称它已关闭。

**D. Registration Boundary ／ status**

- **未新增** canonical entity ／ canonical business field ／ mapping layer ／ Rule ID；
- **未**修改 `§4.5.1` ～ `§4.5.25` 的既有结论与 `MC-9` scope attribution；
- **未**修改 `adr-001-deterministic-core.md`；
- **不代表** implementation ／ real ERP mapping ／ Adapter 已完成。

```
first-tranche canonicalization mapping boundary = REGISTERED（Issue #125 Human Decision）
Master Data Mapping overall                     = DESIGN RESOLVED（未变）
Runtime implementation                          = NOT STARTED
```

---

<!-- END MIGRATED LEGACY §4.5 BODY -->
