# Data Dictionary

**Document / Topic:** Data Dictionary
**Parent Design:** [POC Design v0.2](../../poc-design-v0.2.md)
**Legacy Section:** §4.2（§4.2.1 ～ §4.2.17 编号保留）
**Design Status:** `DESIGN RESOLVED`
**Implementation Status:** `NOT STARTED`
**Canonical Authority:** 本文件是 Data Dictionary concern 的唯一 current canonical source；parent design 保留 navigation/status 入口。
**Migration Base:** `5917cb2fa4b71d4a7379128447bc9e766d17e6da`

<!-- BEGIN MIGRATED LEGACY §4.2 BODY -->
### 4.2 Data Dictionary

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **仅**表示 **canonical field semantics defined**。
>
> **不表示**：source mapping complete、physical schema complete、import contract complete、
> data validated、implemented、tested。

#### 4.2.1 Purpose & Scope

本子章节建立 **canonical business field dictionary**：

- canonical field name
- 所属 entity / derived result
- business semantic
- logical type
- requiredness
- valid / invalid boundary
- missing behavior
- producing / consuming Rule
- source / derived / context 属性

**边界 —— Data Dictionary：**

```
≠ Database Schema
≠ API Contract
≠ JSON Schema
≠ CSV layout
≠ ORM Model
≠ ERP field mapping
```

**本 Task 不定义**：SQL types、varchar length、primary key、foreign key、index、
JSON structure、file columns、source table / column、serialization format。

#### 4.2.2 Dictionary Conventions

**Logical Types（technology-neutral，仅业务逻辑类型）：**

| Logical Type | 含义 |
| --- | --- |
| `IDENTIFIER` | 业务标识 |
| `ANALYSIS_RUN_ID` | Analysis Run 的业务标识 |
| `DATE` | 业务日期（日粒度） |
| `TIMESTAMP` | 观测时间点 |
| `DECIMAL_QUANTITY` | 可为小数的数量 |
| `NON_NEGATIVE_QUANTITY` | 非负数量 |
| `RATIO` | 比例（无量纲，非百分比） |
| `PERCENTAGE` | 百分比 |
| `STATUS` | 业务状态 / 分类 |
| `TEXT_CONTEXT` | 业务上下文文本 |

**不得映射成**：`VARCHAR`、`DECIMAL(18,2)`、`UUID`、`BIGINT`、`JSONB` 等数据库类型。

**Requiredness 语义：**

| 值 | 含义 |
| --- | --- |
| `REQUIRED` | 对相应业务事实 / Rule **必须可靠存在** |
| `CONDITIONAL` | 仅在特定 capability / state 下必须存在 |
| `DERIVED` | 由 deterministic rule 产生 |
| `CONTEXT` | 用于 traceability / observation context |

**不得**把 `missing` 等同于 `0` / `false` / empty string / `UNKNOWN` status ——
除非已有 Rule 明确定义（见 §4.2.12）。

**Source Classification：**

| 值 | 含义 |
| --- | --- |
| `SOURCE` | 来自受控数据源的业务事实 |
| `DERIVED` | 由 deterministic rule 产生 |
| `CONTEXT` | 观测 / 追溯上下文 |
| `POLICY_INPUT` | 业务配置 / 策略输入 |

> **不得**因此决定真实 ERP 来源。

#### 4.2.3 Identity & Context Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `plant_id` | `IDENTIFIER` | `REQUIRED` | `CONTEXT` | 业务计算边界中的 Plant 标识 | `NOT DEFINED` | `DATA_INCOMPLETE` | 全部 Rule |
| `material_code` | `IDENTIFIER` | `REQUIRED` | `CONTEXT` | canonical material identity | `NOT DEFINED` | `DATA_INCOMPLETE` | 全部 Rule |
| `supplier_id` | `IDENTIFIER` | `CONDITIONAL`（Supplier Risk 评估时 `REQUIRED`） | `SOURCE` | supplier identity | `NOT DEFINED` | `DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |
| `analysis_run_id` | `ANALYSIS_RUN_ID` | `REQUIRED` | `CONTEXT` | 一次短缺分析运行的标识 | `NOT DEFINED`；**ID 生成方式未设计** | `DATA_INCOMPLETE` | `BR-SHORTAGE-001`、`BR-PROCUREMENT-001`、`BR-SUPPLIER-RISK-001` |
| `AnalysisDate` | `DATE` | `CONDITIONAL`（Lead Time Feasibility 时 `REQUIRED`） | `CONTEXT` | 分析运行日期（`DaysUntilNeed` 的减数） | `NOT DEFINED` | `LeadTimeRisk = DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |

> **Canonical field identifier clarification（Issue #118 Human Decision）：**
> 本节的 `analysis_run_id` 为 **exact canonical field identifier**；
> `ANALYSIS_RUN_ID` 继续是它的 **Logical Type**，**不是** field identifier
> （见本节上方 **§4.2.2** Logical Types）。
> 本决定**只**固定 identifier 命名 —— **不**决定 Analysis Run ID generation，
> **不**决定其 runtime creation mechanism，**不**改变 Class ／ Requiredness ／ business semantic。

#### 4.2.4 Requirement / BOM Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `required_date` | `DATE` | `REQUIRED` | `SOURCE` | 需求日期（累计计算的 `t`） | `NOT DEFINED` | `DATA_INCOMPLETE` | `BR-REQUIREMENT-001`、`BR-SHORTAGE-001` |
| `ProductionQty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 生产数量 | `ProductionQty >= 0` | `DATA_INCOMPLETE` | `BR-REQUIREMENT-001` |
| `BOMComponentQty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 单位父项所需组件数量 | `BOMComponentQty >= 0`；必须来自**可靠解析的 applicable BOM relationship** | `DATA_INCOMPLETE` | `BR-REQUIREMENT-001` |
| `loss_rate` | `RATIO` | `REQUIRED`（for `BR-REQUIREMENT-001`） | `POLICY_INPUT` | 预计投入总量中发生损耗的比例 | `0 <= loss_rate < 1` | `DATA_INCOMPLETE` ＋ Data Quality Issue | `BR-REQUIREMENT-001` |

**`loss_rate` Applicability / Owner Boundary（consistency sync；**未**改变其 canonical semantic 与 Class）**

`loss_rate` 的 **canonical semantic** 与 **Class = `POLICY_INPUT`** **保持不变**；
本节**不新增** Data Dictionary field row，**不新增** canonical field。

**Canonical Owner（正式定义）：**

```
loss_rate
is resolved for
an exact Requirement Calculation Context
```

此处 **owner** 表示「**哪一个 business calculation context 决定该 `loss_rate` 是否适用**」，
**不是**「哪个 entity / table 持久化保存该字段」。

```
Canonical Owner                ≠  Physical Source Owner
Canonical Applicability Grain  ≠  Database Primary Key
```

**Requirement Calculation Context（conceptual）：**

```
Production Requirement
        +
Applicable BOM Relationship
        +
Component Material
        ↓
Requirement Calculation Context
```

其 **applicability grain** **至少**能够区分：

```
plant_id
+ parent / requirement material_code
+ required_date
+ component material_code
```

> 「**至少**」必须保留：若未来真实 source evidence 需要**额外维度**才能可靠唯一解析，
> `Adapter` **不得**把差异静默压扁（见 **§4.5.22 Option E Implementation Record**）。
> 但当前 Design **不得发明** `routing` / `operation` / `work center` / BOM version number /
> production version / policy ID 等额外维度。

**Canonical Resolution Contract：**

```
exactly one applicable canonical loss_rate
或
unresolved
```

在进入 `BR-REQUIREMENT-001` **确定性计算之前**必须完成该解析；
**不得**让 Rule 面对多个 candidate `loss_rate` 再临时选择。

**Source / Carrier：**

```
SOURCE-SPECIFIC / physical carrier not yet defined
```

`loss_rate` **不是** `Material` / `BOM Component` / `Production Requirement`
任何 persisted entity 的 attribute；具体 source representation 由未来
**Adapter / source-specific mapping** 提供。

**本 Task 未**把 `loss_rate` 加入 `BOM Component` attributes，
也**未**修改 `Production Requirement` 或 `BOM Component` 的 grain。

> `loss_rate` applicability 与 applicable BOM relationship 一起被解析
> **≠** `loss_rate` belongs to `BOM Component` as persisted attribute。

**时间边界：** `loss_rate` applicability **未**被声明为 timeless，
也**未**被声明为每个 `required_date` 都不同 ——
不同 `required_date` 的 `Requirement Calculation Context` **既允许**解析出相同值，**也允许**解析出不同值。

**`BOMComponentQty` Context Boundary（consistency sync；**未**改变其 quantity semantic）**

`BOMComponentQty` **不是**一个脱离 requirement applicability 即可全局复用的
`Plant` + `Parent` + `Component` 固定值。

它属于：

```
Production Requirement context
+
component Material
```

其中：

```
Production Requirement context = plant_id + parent / requirement material_code + required_date
```

因此：即使 `Plant` / `Parent Material` / `Component Material` **完全相同**，
不同 `required_date` 的 requirement context **不得默认共享** `BOMComponentQty`。

**Applicability anchor（`SIMULATED POC Design Policy` ＋ `Human-approved`）：**

```
Production Requirement.required_date
```

**不得**用 Snapshot creation time / Package export time / `AnalysisDate` /
system current time **替代**。

**本 Task 未新增** `BOMVersion` / `ValidFrom` / `ValidTo` / `BOM ID` /
`ProductionVersion` / `AlternativeBOM` / `Change Number` 等 canonical fields。

**`required_quantity` —— 已从 current canonical model 移除（Current-State Resolution）**

```
required_quantity = REMOVED FROM CURRENT POC v0.2 CANONICAL MODEL
```

`required_quantity` 已由 **PR #38 Human Decision** 认定为 **`ORPHAN CANONICAL FIELD`**，
并从 current POC v0.2 canonical model（`§4.1.4 C` attributes ＋ 本节 Data Dictionary）**移除**。

`ProductionQty` **继续**为 `BR-REQUIREMENT-001` **唯一**的 production quantity input：

```
BaseRequirement = ProductionQty × BOMComponentQty
```

> **`REMOVED` 表示**：该字段**不属于**当前 `POC Design v0.2` canonical model。
> **不表示**：真实 ERP 不可能存在类似 quantity / Future Design 永远禁止该概念 /
> source system 不允许有其他 quantity fields / physical source column 被删除 / migration 已执行。
>
> 未来若出现**新的 Human-approved evidence** 证明存在独立 business quantity，
> **可以**通过新的 **Canonical Model Design Change** 重新评估。

**Historical Review Record —— PR #38（不得作为当前状态解读）**

> 以下 **Required Quantity Semantic & Canonical Necessity Review（Review Finding）** 与
> **Human Decision Record** 是 **PR #38** 时点的原始记录，**按当时时点原样保留**，以便追溯。
>
> 其中出现的 `required_quantity semantic = DESIGN PENDING`、`Removal Recommended`、
> `Human Approval Required`、`Removal Approved, Not Yet Implemented`、`unresolved count = 4`
> 等表述**均为历史时点状态**，**不得**被解读为当前状态。
>
> **Subsequent Human-authorized removal has been implemented。**
> `required_quantity` 现为 **`REMOVED FROM CURRENT POC v0.2 CANONICAL MODEL`** ——
> 见上方 **Current-State Resolution** 与本节末
> **Required Quantity Removal Implementation Record**。

**Required Quantity Semantic & Canonical Necessity Review（Review Finding）**

**Review Question**

`required_quantity` 在 POC Design v0.2 中究竟是：

| # | 候选 |
| --- | --- |
| **A** | 必须保留、但尚未定义的**独立 canonical quantity** |
| **B** | 与 `ProductionQty` / `BaseRequirement` / `GrossRequirement` **发生重复或语义冲突**的设计遗留字段 |
| **C** | 当前 POC **根本不需要**的 unsupported canonical field |

**Evidence Review**

| 证据来源 | 是否包含 `required_quantity` |
| --- | --- |
| `FROZEN` Discovery Brief（`discovery-brief-v0.1.1.md`） | **否** |
| `FROZEN` Discovery Validation（`discovery-validation-v0.1.md`） | **否** |
| Human-approved `SIMULATED` evidence（`VR-005` ／ `SC-DATA-001`） | 只确认 **Production Plan 具备数量数据**（`D1` baseline） |
| `§2` Business Rules | 只使用 `ProductionQty` × `BOMComponentQty`（`§2.4.3`） |
| `§4.2.4` 本表 | **`语义未定`**，且 Rule(s) 栏为 **`—`（未被任何 Rule 使用）** |

**必须区分：**

```
「生产计划存在数量」                     ← 有证据
   ≠
「存在一个独立名为 required_quantity
  且区别于 ProductionQty 的业务量」       ← 无证据
```

**结论：没有任何独立业务语义证据支持 `required_quantity`。**

**不得**把行业经验（例如「生产订单通常有 required qty」）当作项目事实。

**Current Quantity Chain**

```
ProductionQty
      ↓  × BOMComponentQty
BaseRequirement
      ↓  loss_rate adjustment
GrossRequirement
      ↓  shortage calculation
ShortageQty / ProjectedAvailable / Classification
```

**`required_quantity` 在这条 chain 中没有任何位置** ——
它既不参与任何一层计算，也**没有声明所属层级**。

**Rule Consumer Search**

| 潜在 consumer | `required_quantity` 是否被消费 |
| --- | --- |
| `BR-REQUIREMENT-001` | **否** —— 使用 `ProductionQty × BOMComponentQty` |
| `BR-SHORTAGE-001` | **否** |
| `BR-PROCUREMENT-001` | **否** |
| `BR-SUBSTITUTE-001` | **否** |
| Supplier Risk（`BR-SUPPLIER-RISK-001`） | **否** |
| Validation | **否** —— 且 `§4.4.14` / `§4.4.53` **明确禁止**用它替代 `ProductionQty` |
| Recommendation / HITL | **否** |

**结论：`required_quantity` 有 0 个 Rule consumer。**

> **必须区分**「真正 Rule consumer」与「仅仅在 Data Dictionary / Open Item / Review text 中被提及」。
> **不得**把「被文档提到」等同于「有业务用途」。

**Option Review**

| Option | 内容 | 结论 |
| --- | --- | --- |
| **0** | 保持 `DESIGN PENDING` | **可短期保持，但不是设计终点**（见下） |
| **A** | `required_quantity = ProductionQty` | **拒绝** —— 无证据；且若完全同义，canonical model 没有理由保留两个字段（构成 semantic aliasing） |
| **B** | `required_quantity = BaseRequirement` | **拒绝** —— 与既有 derived result 重复，并把 **parent production quantity** 与 **component material requirement** 混进同一 entity（grain / ownership 冲突） |
| **C** | `required_quantity = GrossRequirement` | **拒绝** —— 与既有 derived result 重复，且违反 **Derived Result 不得伪装成 source attribute** |
| **D** | Independent external requirement（manual / sales / service / independent demand） | **拒绝** —— 当前 `P0` / Discovery **未批准**任何此类新需求类型 |
| **E** | 从 POC v0.2 canonical model **移除** `required_quantity` | **推荐（待 Human Approval）** |

**Option 0 —— 为何不是设计终点**

保持 `DESIGN PENDING` 不会立刻产生错误结果（Validation 已禁止使用它），
但它会让一个 **`DESIGN RESOLVED` ＋ Human-approved** 的 canonical entity **长期携带一个
无 consumer、无 semantic、无 evidence 的 ambiguous attribute**，
且该 unresolved item 的**唯一 fail-safe 路径就是「永不使用」** ——
这意味着它**无法通过后续设计被「解决」，只能被定义或删除**。

**Option B / C —— grain / ownership 冲突**

见下方 **Canonical Entity Ownership**。

**Orphan Field Test**

| # | 判据 | 结果 |
| --- | --- | --- |
| 1 | 有 approved business semantic？ | **否** —— 明确为 `语义未定` |
| 2 | 有 Rule consumer？ | **否** —— 0 个 |
| 3 | 有独立 source evidence？ | **否** —— 两份 `FROZEN` 文档均未出现 |
| 4 | 有独立 grain / ownership？ | **否** —— 未声明独立 grain |
| 5 | 删除后是否影响任何现有 approved calculation？ | **否** —— `BR-REQUIREMENT-001` 只用 `ProductionQty × BOMComponentQty` |
| 6 | 是否只是另一个 quantity 的重复命名？ | **是（最可能）** —— 唯一候选解释均与既有 quantity 重叠或冲突 |

```
required_quantity = ORPHAN CANONICAL FIELD
```

**Recommended Direction**

```
Option E —— 从 POC v0.2 canonical model 移除 required_quantity
```

移除范围（**本 Review 不执行**）：

- `§4.1.4 C Production Requirement` 的 **attributes** 中的 `required_quantity`
- `§4.2.4` Data Dictionary 的 `required_quantity` 行
- 所有 authoritative unresolved list 中的 `required_quantity` semantic 条目

**注意：`§4.1 Canonical Data Model` 是 `DESIGN RESOLVED` ＋ Human-approved ——
本 Review 不得自行执行，必须经 Human Approval。**

**ProductionQty Boundary（保持）**

`ProductionQty` 是当前 `BR-REQUIREMENT-001` **明确使用**的生产数量输入。
**不得**因为 `required_quantity` 的存在而把 `ProductionQty` deprecated，
也**不得**把 `ProductionQty` 变成 `required_quantity` 的 alias ——
**除非 Human 后续明确批准**。

**Derived Quantity Boundary（保持）**

`BaseRequirement` 与 `GrossRequirement` 是 **deterministic derived quantities**。
**不得**为了给 `required_quantity` 找定义而把它们重新登记成
`Production Requirement` 的 **source attribute**。

**Canonical Entity Ownership**

`§4.1.4 C Production Requirement` 的 grain：

```
plant_id + material_code + required_date
```

其中 `material_code` 表示 **parent / production material** 角色
（该 contextual role 已由 **§4.1.4 N** 的 role clarification 明确）。

因此该 entity 表达的是 **production-order-demand 层级**，**不是 component 层级**。

任何把 `required_quantity` 解释成 **component-level material requirement** 的方案
（Option B / C）都会让**同一个 entity 同时表示**：

```
production order demand
+
exploded component requirement
```

→ **ownership conflict：明确拒绝。**

**Source Evidence Boundary**

Discovery evidence 只确认 **Production Plan 具备数量数据**。
**不得**据此推导 `required_quantity` 是独立 source field。

应优先保持既有原则：

```
source-specific physical field  ≠  canonical semantic field name
```

**loss_rate / ApplicableMOQ / Provenance Boundary**

本 Review **不解决** `loss_rate` owner / grain（保持 **`UNKNOWN`**），
也**不推进** `ApplicableMOQ` source 与 provenance carrier。
本 Review **只**引用「`loss_rate` 当前用于 `GrossRequirement` calculation」这一既有事实。

**Status（PR #38 Review 时点）**

```
required_quantity semantic = DESIGN PENDING    ← 本 Review 不改变
Status                     = Removal Recommended ＋ Human Approval Required
unresolved count           = 仍为 4
```

**本 Review 不得直接删除字段。** 结论为
**`ORPHAN CANONICAL FIELD` ＋ `Removal Recommended`**，
但**必须**先经 **Human Approval**。

**Human Decision Required**

请 Human 决定：

1. 是否接受 **`required_quantity = ORPHAN CANONICAL FIELD`**
2. 是否批准从 **`Production Requirement` attributes** 移除 `required_quantity`
3. 是否批准从 **`§4.2` Data Dictionary** 移除 `required_quantity`
4. 是否确认 **`ProductionQty` 继续作为 `BR-REQUIREMENT-001` 的唯一 production quantity input**
5. 是否确认 **`BaseRequirement` / `GrossRequirement` 保持 derived quantity**，
   不由 `required_quantity` 替代
6. 是否授权 **`§4.1` / `§4.2` / `§4.4` / `§4.5`** 必要的最小 consistency synchronization

**Human Approval 后**，下一 Task 才正式实施。

**No Physical Schema**

本 Review **未创建**：`required_qty` source column / alias field / DB schema / JSON schema /
CSV layout / Adapter / mapping code / migration / test。**未选择技术。**

**Human Decision Record —— Human-approved Canonical Model Change（Removal Approved）**

> 以下为 Human 对上述 6 项的**正式回复**（本 Review 由 **PR #38** 提交）。
> 本节**只记录决定**；**未**执行字段删除，**未**修改 `§2` / `§4.1`。

| # | 决定项 | Human Decision |
| --- | --- | --- |
| 1 | `required_quantity = ORPHAN CANONICAL FIELD` | **APPROVED** |
| 2 | 从 `§4.1.4 C Production Requirement` attributes 移除 | **AUTHORIZED** |
| 3 | 从 `§4.2.4` Data Dictionary 移除（含 ambiguity 说明） | **AUTHORIZED** |
| 4 | `ProductionQty` boundary | **CONFIRMED** |
| 5 | `BaseRequirement` / `GrossRequirement` = derived, unchanged | **CONFIRMED** |
| 6 | `§4.1` / `§4.2` / `§4.4` / `§4.5` 最小 consistency synchronization | **AUTHORIZED** |

**决定 1 —— `ORPHAN CANONICAL FIELD` = APPROVED**

该结论**仅针对当前**：

- `POC Design v0.2`
- 现有 `FROZEN` Discovery / Validation
- Human-approved `SIMULATED` evidence
- 现有 Business Rules

当前**没有**证据支持 `required_quantity` 作为独立于 `ProductionQty` / `BaseRequirement` /
`GrossRequirement` 的 canonical quantity。

> 该结论**不表示**未来真实 ERP / MRP **绝不可能**存在另一种 requirement quantity。
> 如果未来出现新的 Human-approved evidence，**必须**通过新的 Design Change **重新评估**。

**决定 2 —— 从 `§4.1.4 C` attributes 移除 = AUTHORIZED**

原因（本项当前）：

- 无 approved independent semantic
- **无 Rule consumer**
- 无独立 source evidence
- 无独立 grain / ownership
- 删除**不影响**现有 approved calculation

**不得**借此修改 `Production Requirement` grain —— 仍保持：

```
plant_id + material_code + required_date
```

**不得新增替代字段。**

**决定 3 —— 从 `§4.2.4` Data Dictionary 移除 = AUTHORIZED**

删除范围：`required_quantity` Data Dictionary row ＋ 紧邻的
`required_quantity vs ProductionQty —— SEMANTIC AMBIGUITY` current-state 说明。

> **PR #38 Review History 中关于 `required_quantity` 的历史分析必须保留** ——
> **不得篡改 Review Finding。**

**决定 4 —— `ProductionQty` Boundary = CONFIRMED**

`ProductionQty` **继续**作为 `BR-REQUIREMENT-001` **唯一**的 production quantity input。

```
BaseRequirement = ProductionQty × BOMComponentQty
```

**不得**：

- `ProductionQty` → `required_quantity` alias
- `required_quantity` removal → 修改 `ProductionQty` semantic
- 创建新的 production quantity field

**决定 5 —— Derived Quantity Boundary = CONFIRMED**

`BaseRequirement` 与 `GrossRequirement` **继续保持 deterministic derived quantities**。
它们**不是** `Production Requirement` source attributes。
**不得**用 `required_quantity` 替代其中任何一个。

```
ProductionQty
        ↓ × BOMComponentQty
BaseRequirement
        ↓ loss_rate adjustment
GrossRequirement
```

该 quantity chain **不因本决定改变**。

**决定 6 —— Minimal Consistency Synchronization = AUTHORIZED（授权边界）**

**授权范围仅包括：**

- **`§4.1`** —— 从 `Production Requirement` attributes 删除 `required_quantity`；**grain 不变**；`ProductionQty` 不变
- **`§4.2`** —— 删除 `required_quantity` Data Dictionary row；删除其 authoritative ambiguity / pending wording；
  同步 open-item / current-state lists
- **`§4.4`** —— 删除或同步**仅用于防止** `required_quantity` 被错误使用的 current-state Validation wording；
  **不得修改其他 Validation semantics**；Review History **可保留历史说明**
- **`§4.5`** —— 记录 implementation result；移除 `required_quantity` semantic unresolved item；
  unresolved count **4 → 3**；同步 current-state status summary

**不得借此**：

- 修改 `§2` Business Rules
- 修改 `Production Requirement` grain
- 修改 `BOMComponentQty` / `ProductionQty` / `BaseRequirement` / `GrossRequirement`
- 解决 `loss_rate` owner / grain
- 解决 `ApplicableMOQ` source
- 解决 provenance carrier
- 创建新 canonical field / 新 Rule / ADR
- 选择技术

**Status Interpretation（本 PR 只记录，不执行删除）**

```
required_quantity semantic = DESIGN PENDING
                           ／ Removal Approved, Not Yet Implemented
unresolved count           = 4
```

在 **follow-up Design Change** 真正完成所有 authoritative synchronization 之前，
该 unresolved item **不关闭**。

**Follow-up 完成后**才写：

```
required_quantity = REMOVED FROM CURRENT CANONICAL MODEL
unresolved count  4 → 3
```

剩余 3 项：`loss_rate` owner / grain（`UNKNOWN`）、`ApplicableMOQ` source、provenance carrier。

**Future Reintroduction Boundary**

未来如果出现新的正式 evidence，证明存在一个**独立于** `ProductionQty` / `BaseRequirement` /
`GrossRequirement` 之外的 business quantity，**可以**通过新的 **Human-approved Canonical Model
Design Change** 重新引入。

**不得**因为本次删除声称该概念**永久禁止**。

**执行状态（PR #38 时点）**

```
Human Decision      = RECORDED
required_quantity   = ORPHAN CANONICAL FIELD
Removal             = APPROVED, NOT YET IMPLEMENTED
ProductionQty       = UNCHANGED
BaseRequirement     = UNCHANGED
GrossRequirement    = UNCHANGED
unresolved count    = 4
```

**Required Quantity Removal Implementation Record（Human-authorized Canonical Model Amendment）**

**Human Authorization Source**

```
PR #38 Human Decision
  → required_quantity = ORPHAN CANONICAL FIELD   = APPROVED
  → §4.1 removal                                 = AUTHORIZED
  → §4.2 removal                                 = AUTHORIZED
  → ProductionQty                                = CONFIRMED canonical production quantity input
  → BaseRequirement / GrossRequirement           = DERIVED, UNCHANGED
  → minimal synchronization（§4.1/§4.2/§4.4/§4.5） = AUTHORIZED
```

**Implementation Result**

```
required_quantity = REMOVED FROM CURRENT POC v0.2 CANONICAL MODEL
```

**Before / After —— `§4.1.4 C Production Requirement` attributes**

| | Attributes |
| --- | --- |
| **Before** | `plant_id` ／ `material_code` ／ `required_date` ／ **`required_quantity`** ／ `ProductionQty` |
| **After** | `plant_id` ／ `material_code` ／ `required_date` ／ `ProductionQty` |

**Canonical grain 未改变**（仍 `plant_id` + `material_code` + `required_date`）；
**未新增**任何替代字段；**未** rename `ProductionQty`；**未**创建 quantity alias。

**`§4.2.4` Data Dictionary**

- `required_quantity` row **已移除**
- current-state `SEMANTIC AMBIGUITY` 说明**已替换**为 current-state resolution note
- **PR #38 Review Finding 与 Human Decision Record 作为 Historical Review Record 完整保留**

**`§4.4` Validation**

- `§4.4.14` / `§4.4.30` / `§4.4.53` —— 已由 ambiguous-field 边界同步为 **removal boundary**
- `§4.4.41` / `§4.4.76` / `§4.4.99` / `§4.4` closure 表 —— 已同步
- **current Validation model 不再把 `required_quantity` 当作需要 validate / map / check missing /
  check type / resolve semantic 的当前字段**
- **未创建**任何新的 Validation Reason / Business Status / Error Code

**`§4.5`**

- `§4.5.22` Preserve Unresolved Items —— `required_quantity` semantic row **已移除**
- `unresolved count` **4 → 3**
- **`Other Source-Semantic Mapping` 仍为 `DESIGN PENDING`**
- **未新增**任何 Master Data Mapping layer

**Meaning of `REMOVED`**

`REMOVED` **表示**：该字段**不属于**当前 `POC Design v0.2` canonical model。

**不表示**：

- 真实 ERP 不可能存在类似 quantity
- Future Design 永远禁止该概念
- source system 不允许有其他 quantity fields
- physical source column 被删除
- migration 已执行

未来如出现**新的 Human-approved evidence** 证明存在独立 business quantity，
**可以**通过新的 **Canonical Model Design Change** 重新评估。

**Preserved Boundaries**

- `ProductionQty` —— 仍为 `BR-REQUIREMENT-001` **唯一** production quantity input
  （`BaseRequirement = ProductionQty × BOMComponentQty`）
- `BaseRequirement` / `GrossRequirement` —— 仍为 **deterministic derived quantities**，
  **未**放回 `Production Requirement` source attributes
- **未**修改 `§2` Business Rules；**未**修改 `loss_rate` owner / grain（仍 **`UNKNOWN`**）；
  **未**推进 `ApplicableMOQ` source / provenance carrier

**执行状态（本 Task 完成时点）**

```
required_quantity             = REMOVED FROM CURRENT CANONICAL MODEL
unresolved count              = 4 → 3
Other Source-Semantic Mapping = 仍 DESIGN PENDING
Master Data Mapping overall   = 仍 DESIGN PENDING
```

#### 4.2.5 Inventory Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `inventory_status` | `STATUS` | `REQUIRED` | `SOURCE` | 库存可用性状态 | 仅 `AVAILABLE` / `INSPECTION` / `FROZEN`（见 §4.2.14） | 未知 / 非法 → `DATA_INCOMPLETE`；**不得静默归类为 `AVAILABLE`** | `BR-INVENTORY-001` |
| `on_hand_qty` | `DECIMAL_QUANTITY` | `REQUIRED` | `SOURCE` | 观测到的在手库存数量 | **不得** `clamp to 0`；`on_hand_qty < 0` 为**非法输入**（见 §2.2.8） | `DATA_INCOMPLETE` ＋ Data Quality Issue | `BR-INVENTORY-001` |
| `inventory_snapshot_time` | `TIMESTAMP` | `REQUIRED` | `CONTEXT` | 库存观测时间点 | `NOT DEFINED` | `DATA_INCOMPLETE` | `BR-INVENTORY-001` |
| `SafetyStock` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `POLICY_INPUT` | 业务配置的安全库存（Configured Safety Stock） | `SafetyStock >= 0` | `DATA_INCOMPLETE`；**不得默认成 0** | `BR-INVENTORY-001`、`BR-SHORTAGE-001` |

> `warehouse ownership unresolved` 是 **Data Quality fail-safe 触发项**（见 §2.2.9）；
> **Warehouse 的 canonical role 已由 §4.5.12 解析** 为 source / mapping / scope context ——
> 它**不是** canonical field，因此本表**不新增** Warehouse field（见 §4.2.16）。

#### 4.2.6 Inbound Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ordered_qty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 已订购数量 | `ordered_qty >= 0` | `DATA_INCOMPLETE` | `BR-INBOUND-001` |
| `received_qty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 已收货数量 | `received_qty >= 0`；`received_qty > ordered_qty` 为**非法** | `DATA_INCOMPLETE` ＋ Data Quality Issue | `BR-INBOUND-001` |
| `effective_arrival_date` | `DATE` | `REQUIRED` | `SOURCE` | Inbound **真正可用于 shortage calculation** 的有效到货日（canonical semantic **未改变**） | **source mapping = source-specific / Adapter-defined**；**canonical mapping contract = `DESIGN RESOLVED`**（**§4.5.21**）；**具体 source field 不在 canonical Data Dictionary 中统一定义** | 见下方 **Root-Condition Distinction**；三类最终均为 `DATA_INCOMPLETE` | `BR-INBOUND-001` |
| `inbound_status` | `STATUS` | `REQUIRED` | `SOURCE` | 判断该 inbound 是否可计入未来供给的状态 | 见 §2.6.3 的保守分类；未知 / 非法 → **不得猜测** | `DATA_INCOMPLETE` ＋ Data Quality Issue | `BR-INBOUND-001` |

> **Canonical field identifier clarification（Issue #118 Human Decision）：**
> `inbound_status` 是 **exact canonical field identifier**（此前仅以描述性名称
> `inbound status / eligibility context` 登记）。
> 本决定**只**固定 identifier 命名 —— business semantic、Class、Requiredness 与
> `§2.6.3` ／ **§4.2.14** 已批准的 inbound status vocabulary **均未改变**；
> 本决定**不**把它改成 `SOURCE-SPECIFIC` vocabulary，也**不**重新设计 source mapping。

**`effective_arrival_date` —— source mapping / mapping contract（PR #34 Human-approved Option D）**

```
canonical semantic         = 未改变（仍由 BR-INBOUND-001 / §2.6.4 定义）
source mapping             = SOURCE-SPECIFIC / Adapter-defined
canonical mapping contract = DESIGN RESOLVED
```

**具体 source field 不由 canonical design 全局统一** —— 它是 **`SOURCE-SPECIFIC` / Adapter-defined**；
但 Adapter **必须遵守** Human-approved **canonical mapping contract**。

正式 contract：

```
source-specific arrival-date evidence
        ↓
explicit deterministic mapping
        ↓
exactly one canonical effective_arrival_date
        或
unresolved
```

必须 `deterministic` / `explicit` / `traceable` / `reproducible`；
**不得**依赖 LLM guess ／ runtime business-rule choice ／ silent fallback ／ implicit precedence。

**Global Source-Field Precedence = `NOT ADOPTED`** —— **不得**声明
`promised_date` ／ `expected_arrival_date` ／ `confirmed_date` ／ `planned_delivery_date` ／ `ETA`
中的任何一个是**全局 source**，也**不得**建立
`expected` fallback `promised` ／ `promised` fallback `expected` ／ earliest wins ／ latest wins ／
newest `updated_at` wins ／ `min` ／ `max` ／ `average` ／ LLM choose。

**Root-Condition Distinction**（三类的 Business consequence 均为 `DATA_INCOMPLETE`，但 **root condition 不同**）：

| # | Root condition | Validation Reason | Business consequence |
| --- | --- | --- | --- |
| **A** | approved mapping 已存在，但 **mapped source value missing** | `FIELD_VALUE` / `MISSING`（或既有适用 Field Validation reason） | `DATA_INCOMPLETE` |
| **B** | source date evidence **存在**，但 mapping semantic **无法可靠完成** | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE`（当 capability 需要该 inbound 时） |
| **C** | approved mapping 已存在，但 mapped value **无法解析为合法 `DATE`** | `FIELD_VALUE` / `INVALID_TYPE`（或既有适用 reason） | `DATA_INCOMPLETE` |

**不得**把 A / B / C 都写成 `effective_arrival_date missing`；
**不得创建**新的 Validation Reason；
**不得**在 C 的情况下 fallback 到另一个**未经批准**的 candidate date。

**未新增** `ArrivalDateSourceType` / `ArrivalDatePriority` / `ArrivalConfidence` /
`source_field_name` 等 canonical fields。

#### 4.2.7 Substitute Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `target_material_code` | `IDENTIFIER` | `REQUIRED` | `SOURCE` | 被覆盖的 Target Material | `NOT DEFINED` | `DATA_INCOMPLETE` | `BR-SUBSTITUTE-001` |
| `substitute_material_code` | `IDENTIFIER` | `REQUIRED` | `SOURCE` | 提供覆盖的 Substitute Material | `NOT DEFINED` | `DATA_INCOMPLETE` | `BR-SUBSTITUTE-001` |
| `substitution_ratio` | `RATIO` | `REQUIRED` | `SOURCE` | 1 unit Substitute 可覆盖多少 unit Target Requirement（**substitute → target**） | `substitution_ratio > 0` | `DATA_INCOMPLETE` ＋ Data Quality Issue；**不得默认成 `1.0`** | `BR-SUBSTITUTE-001` |
| `approval_status` | `STATUS` | `REQUIRED` | `SOURCE` | Substitute Relationship 的审批状态 | 仅 `APPROVED` 可参与计算（见 §4.2.14） | 缺失 / 无法判断 → `DATA_INCOMPLETE`；**不得由 LLM 自动批准** | `BR-SUBSTITUTE-001` |
| `AllocatedSubstituteQty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 明确分配给某 Target 的替代数量 | `AllocatedSubstituteQty >= 0`；`Σ AllocatedSubstituteQty <= EligibleSubstituteSupply` | `DATA_INCOMPLETE` ＋ Data Quality Issue / Allocation Conflict；**不得默认成 0** | `BR-SUBSTITUTE-001` |
| effective demand context | `TEXT_CONTEXT`（**conceptual context，不是单值 date field**） | `CONDITIONAL` | `CONTEXT` | 解析 allocation 有效性的 conceptual context —— 承载 **Target Applicability** ＋ **Source Reservation Overlap** 两个 relation | **canonical demand-window mapping contract = `DESIGN RESOLVED`**（**§4.5.9**）；具体 source evidence = **`SOURCE-SPECIFIC` / Adapter-defined**；**不得**定义真实 ERP allocation / reservation / planning-link / schedule field | 无法可靠解析 → `SEMANTIC_UNRESOLVED`（见 **§4.4.60**）；capability 需要时 `DATA_INCOMPLETE` | `BR-SUBSTITUTE-001` |

**`effective demand context` —— 不是伪 field（PR #36 Human-approved Option B）**

`effective demand context` **不是单值 date field**。它代表解析以下两个 relation 所**必需的 conceptual context**：

```
Target Applicability         （allocation → 哪些 Target Demand Context）
Source Reservation Overlap   （allocation reservation ↔ 哪些 Source Demand Context）
```

因此**不**把它硬塞成一个 persisted field row，而是在此以**紧邻说明**表达其 conceptual relation。

**具体 source evidence = `SOURCE-SPECIFIC` / Adapter-defined** ——
**不得定义**真实 ERP allocation field / reservation field / planning-link field / schedule field。

**未新增**任何 canonical field；**不得创建** `requirement_id` / `demand_window_id` /
`allocation_period` / `valid_from` / `valid_to`。

#### 4.2.8 Supplier Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `sourcing_status` | `STATUS` | `CONDITIONAL` | `SOURCE` | Supplier-Material relationship eligibility context | **source vocabulary = `SOURCE-SPECIFIC` / Adapter-defined**；**canonical eligibility mapping contract = `DESIGN RESOLVED`**（**§4.5.11**）；**不得**列举任何真实 source enum | eligibility 无法可靠映射 → `SEMANTIC_UNRESOLVED`；capability 需要时 Risk Evidence Status = `DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |
| `standard_lead_time_days` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 标准供应周期（天） | `StandardLeadTimeDays >= 0` | `LeadTimeRisk = DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |
| `PerformancePeriod` | `TEXT_CONTEXT`（observation window） | `REQUIRED` | `CONTEXT` | performance 的**统计窗口** | `NOT DEFINED`（period policy `DESIGN PENDING`） | `DeliveryRisk` / `QualityRisk` = `DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |
| `PerformanceUpdatedAt` | `TIMESTAMP` | `CONDITIONAL` | `CONTEXT` | performance 记录更新时间 | `NOT DEFINED` | 不单独导致 `DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |
| `DeliveryPerformance` | `PERCENTAGE` | `REQUIRED` | `SOURCE` | 交付绩效 | `0% ～ 100%` | `DeliveryRisk = DATA_INCOMPLETE`；**不得默认成 0** | `BR-SUPPLIER-RISK-001` |
| `QualityPerformance` | `PERCENTAGE` | `REQUIRED` | `SOURCE` | 质量绩效 | `0% ～ 100%` | `QualityRisk = DATA_INCOMPLETE`；**不得默认成 0** | `BR-SUPPLIER-RISK-001` |

> **必须保持：** `PerformancePeriod`（measurement period）**≠** `PerformanceUpdatedAt`。
> `PerformanceUpdatedAt` **不能替代** measurement period。

**`sourcing_status` —— source vocabulary / mapping contract（PR #32 Human-approved Option B）**

```
source vocabulary              = SOURCE-SPECIFIC / Adapter-defined
canonical eligibility mapping  = DESIGN RESOLVED
```

具体 source values **当前仍未知** —— 但这**不阻塞** conceptual mapping contract 被 `DESIGN RESOLVED`。

**Valid / Invalid Boundary 不得列举任何真实 source enum。**

conceptual mapping outcome：`eligible` / `ineligible` / `unresolved`
（**只是 conceptual mapping conditions** —— 不是 source enum / Business Status / Supplier Risk level /
database field / API enum / ranking / selection result）。

**不得创建** `is_eligible` / `SupplierEligibilityStatus` 等 canonical field。

#### 4.2.9 Procurement Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `RecommendationNeedDate` | `DATE` | `CONDITIONAL`（`Classification = SHORTAGE` 且 Procurement Recommendation applicable 时 `REQUIRED`） | `CONTEXT` | 采购建议所使用的 business need date | 当前 POC `= FirstShortageDate` | 见下方条件性说明 | `BR-PROCUREMENT-001` |
| `ApplicableMOQ` | `NON_NEGATIVE_QUANTITY` | `CONDITIONAL`（`Classification = SHORTAGE` 时 `REQUIRED`） | `POLICY_INPUT` | 当前采购建议所适用的最小采购数量约束 | `ApplicableMOQ >= 0` | `DATA_INCOMPLETE`；**不得默认成 0** | `BR-PROCUREMENT-001` |

> **`ApplicableMOQ` 仍是原有 canonical attribute** —— **未新增** Data Dictionary field row。
>
> **Canonical Applicability Contract = `DESIGN RESOLVED`**（**§4.5.22 Option D Implementation Record**）：
>
> ```
> Canonical Applicability Context = exact Procurement Recommendation Context
>                                   （plant_id + material_code + RecommendationNeedDate）
> Source Semantic Role            = SOURCE-SPECIFIC purchasing-policy evidence
> Resolution Contract             = exactly one applicable ApplicableMOQ
>                                   或 unresolved
> Physical Carrier                = NOT YET DEFINED（logical provenance carrier = DESIGN RESOLVED；physical realization 仍属 §4.3）
> ```
>
> **不得**把 Supplier ／ Contract ／ ERP Purchasing Info Record 声明为真实来源 ——
> 它们只能是 **possible source forms**（见 **§4.2.16**）。
> **不得**为解析 MOQ 而执行 Supplier Selection（见 **§4.4.67**）。

**`RecommendationNeedDate` 的条件性**

`RecommendationNeedDate` 的 `Requiredness` 为 **`CONDITIONAL`**，仅当：

```
Classification = SHORTAGE
且 Procurement Recommendation applicable
```

时 `REQUIRED`。

如果：

```
Classification = NORMAL
或
Classification = BUFFER_BREACH
```

则 **No Purchase Recommendation**，因此 `RecommendationNeedDate` **可以 `not present by design`**。

**这不是 `DATA_INCOMPLETE`。**

如果 `Classification = SHORTAGE`，但 required recommendation inputs **无法可靠取得**，
才进入 `DATA_INCOMPLETE`。

#### 4.2.10 Derived Result Fields

以下**全部**为 deterministic derived results，`Requiredness = DERIVED`、`Class = DERIVED`。
**不得把 derived result 伪装成 source-system fact。**

| Derived Result | Logical Type | Business Semantic | Produced By | Consumed By | Valid Boundary | Missing Behavior |
| --- | --- | --- | --- | --- | --- | --- |
| `BaseRequirement` | `NON_NEGATIVE_QUANTITY` | 未含损耗的净需求 | `BR-REQUIREMENT-001` | `GrossRequirement` | `= ProductionQty × BOMComponentQty` | `DATA_INCOMPLETE` |
| `GrossRequirement` | `NON_NEGATIVE_QUANTITY` | 含损耗的毛需求 | `BR-REQUIREMENT-001` | `CumulativeGrossRequirement` | `= BaseRequirement / (1 - loss_rate)` | `DATA_INCOMPLETE` |
| `CumulativeGrossRequirement` | `NON_NEGATIVE_QUANTITY` | 截至 `t` 的累计毛需求 | `BR-REQUIREMENT-001` | `ProjectedAvailable` | `Σ` where `required_date <= t` | `DATA_INCOMPLETE` |
| `OpeningUsableInventory` | `NON_NEGATIVE_QUANTITY` | 允许状态的在手库存之和 | `BR-INVENTORY-001` | `ProjectedAvailable` | `= Σ EligibleOnHandQty`（**不得**用 `Book Inventory Total`；**不得**减 `SafetyStock`） | `DATA_INCOMPLETE` |
| `RemainingInboundQty` | `NON_NEGATIVE_QUANTITY` | 未收货余量 | `BR-INBOUND-001` | `EffectiveInbound` | `= ordered_qty - received_qty`；`>= 0` | `DATA_INCOMPLETE` |
| `EffectiveInbound` | `NON_NEGATIVE_QUANTITY` | 单笔 inbound 的有效供给量 | `BR-INBOUND-001` | `CumulativeEffectiveInbound` | eligible 且 `effective_arrival_date <= t`；否则 `0` | `DATA_INCOMPLETE` |
| `CumulativeEffectiveInbound` | `NON_NEGATIVE_QUANTITY` | 截至 `t` 的累计有效在途 | `BR-INBOUND-001` | `ProjectedAvailable` | `Σ EffectiveInbound` | `DATA_INCOMPLETE` |
| `EquivalentTargetQty` | `NON_NEGATIVE_QUANTITY` | 换算后的等效目标供给 | `BR-SUBSTITUTE-001` | `CumulativeApprovedSubstituteSupply` | `= AllocatedSubstituteQty × substitution_ratio` | `DATA_INCOMPLETE` |
| `ApprovedSubstituteSupply` | `NON_NEGATIVE_QUANTITY` | 已批准替代供给（`0` 为**合法状态**） | `BR-SUBSTITUTE-001` | `CumulativeApprovedSubstituteSupply` | 无 Approved Substitute 时 `= 0` | `DATA_INCOMPLETE`（仅当 data 不可靠） |
| `CumulativeApprovedSubstituteSupply` | `NON_NEGATIVE_QUANTITY` | 截至 `t` 的累计批准替代供给 | `BR-SUBSTITUTE-001` | `ProjectedAvailable` | `Σ EquivalentTargetQty` | `DATA_INCOMPLETE` |
| `RemainingUnallocatedSourceSupply` | `NON_NEGATIVE_QUANTITY` | 未分配的可自由使用源供给 | `BR-SUBSTITUTE-001` | 供给守恒约束 | `= EligibleSubstituteSupply - Σ AllocatedSubstituteQty`；`>= 0` | `DATA_INCOMPLETE` |
| `ProjectedAvailable` | `DECIMAL_QUANTITY` | 截至 `t` 的预计可用量 | `BR-SHORTAGE-001` | `Classification` / `ShortageQty` / `BufferGap` | `= OpeningUsableInventory + CumulativeEffectiveInbound + CumulativeApprovedSubstituteSupply - CumulativeGrossRequirement`；**可为负** | `DATA_INCOMPLETE` |
| `Classification` | `STATUS` | 短缺分类 | `BR-SHORTAGE-001` | 下游全部 | 仅 `NORMAL` / `BUFFER_BREACH` / `SHORTAGE` / `DATA_INCOMPLETE` | `DATA_INCOMPLETE` |
| `ShortageQty` | `NON_NEGATIVE_QUANTITY` | 实际缺口数量 | `BR-SHORTAGE-001` | `BasePurchaseNeed` | `= max(0, -ProjectedAvailable)` | `DATA_INCOMPLETE` |
| `BufferGap` | `NON_NEGATIVE_QUANTITY` | Safety Stock buffer 缺口 | `BR-SHORTAGE-001` | 解释 / 展示 | `= max(0, SafetyStock - ProjectedAvailable)` | `DATA_INCOMPLETE` |
| `FirstShortageDate` | `DATE` | 最早出现 `ProjectedAvailable < 0` 的日期 | `BR-SHORTAGE-001` | `RecommendationNeedDate` | 按 `required_date` ascending 取最早；从未满足时为 `null / not present`（**valid absence**） | 数据完整但整个 analysis horizon 从未满足 → **valid absence**（**不是** `DATA_INCOMPLETE`）；仅当 shortage calculation 因关键数据缺失 / invalid / unresolved 无法可靠执行 → `DATA_INCOMPLETE` |
| `DaysUntilNeed` | `DECIMAL_QUANTITY` | 距需求日的天数 | `BR-SUPPLIER-RISK-001` | `LeadTimeRisk` | `= RecommendationNeedDate - AnalysisDate`；`>= 0` | `LeadTimeRisk = DATA_INCOMPLETE` |
| `LeadTimeRisk` | `STATUS` | Lead Time 可行性风险 | `BR-SUPPLIER-RISK-001` | `OverallSupplierRisk` | 仅 `LOW` / `HIGH`（**本版本无 `MEDIUM`**） | `DATA_INCOMPLETE` |
| `DeliveryRisk` | `STATUS` | 交付绩效风险 | `BR-SUPPLIER-RISK-001` | `OverallSupplierRisk` | 仅 `LOW` / `MEDIUM` / `HIGH` | `DATA_INCOMPLETE` |
| `QualityRisk` | `STATUS` | 质量绩效风险 | `BR-SUPPLIER-RISK-001` | `OverallSupplierRisk` | 仅 `LOW` / `MEDIUM` / `HIGH` | `DATA_INCOMPLETE` |
| `OverallSupplierRisk` | `STATUS` | 综合供应商风险 | `BR-SUPPLIER-RISK-001` | 决策支持 | `= max severity`（**非** weighted score）；`LOW < MEDIUM < HIGH` | 任一维度不可靠 → `DATA_INCOMPLETE` |
| `BasePurchaseNeed` | `NON_NEGATIVE_QUANTITY` | 基础采购需求 | `BR-PROCUREMENT-001` | `RecommendedPurchaseQty` | `= ShortageQty at FirstShortageDate`；**不得**加 `BufferGap` | `NORMAL` / `BUFFER_BREACH` → **not produced by design**；`SHORTAGE` ＋ inputs reliable → numeric；`SHORTAGE` ＋ 关键输入不可靠 → `DATA_INCOMPLETE` / **No Numeric Recommendation** |
| `MOQAdjustmentQty` | `NON_NEGATIVE_QUANTITY` | 为满足 MOQ 额外增加的数量 | `BR-PROCUREMENT-001` | 解释 / 展示 | `= RecommendedPurchaseQty - BasePurchaseNeed`；`>= 0`；**不是** `ShortageQty` | `NORMAL` / `BUFFER_BREACH` → **not produced by design**；`SHORTAGE` ＋ inputs reliable → numeric；`SHORTAGE` ＋ 关键输入不可靠 → `DATA_INCOMPLETE` / **No Numeric Recommendation** |
| `RecommendedPurchaseQty` | `NON_NEGATIVE_QUANTITY` | 建议采购数量 | `BR-PROCUREMENT-001` | Procurement Request Draft | `= max(BasePurchaseNeed, ApplicableMOQ)`；保持 canonical quantity | `NORMAL` / `BUFFER_BREACH` → **not produced by design**；`SHORTAGE` ＋ inputs reliable → numeric；`SHORTAGE` ＋ 关键输入不可靠 → `DATA_INCOMPLETE` / **No Numeric Recommendation** |

**Conditional Applicability of Procurement Derived Results**

以下 derived results 具有 **conditional applicability**：

- `BasePurchaseNeed`
- `MOQAdjustmentQty`
- `RecommendedPurchaseQty`

它们**只在**：

```
Classification = SHORTAGE
且 BR-PROCUREMENT-001 required inputs reliable
```

时产生 **numeric value**。

| 情况 | 行为 |
| --- | --- |
| `Classification = NORMAL` 或 `BUFFER_BREACH` | 这些 procurement result **not produced by design** —— **不是** `DATA_INCOMPLETE` |
| `Classification = SHORTAGE` 且 required inputs reliable | 产生 **numeric result** |
| `Classification = SHORTAGE` 但 required input 不可靠（例如 `ApplicableMOQ` missing / invalid） | **`DATA_INCOMPLETE`** ＋ **No Numeric Recommendation** |

**Valid Absence vs Missing Required Data**

```
valid absence
  ≠ missing required data
```

- **valid absence** —— 该字段在当前业务状态下**本来就不适用**，或不产生；
  属于**字段存在性语义**，**不得**解释成 `DATA_INCOMPLETE`。
- **missing required data** —— 本来**需要**形成可靠结果，但关键数据缺失 / invalid / unresolved，
  因此无法可靠计算 → **`DATA_INCOMPLETE`**。

**不得新增** `NOT_APPLICABLE` / `N/A` / `NO_SHORTAGE` / `NO_RECOMMENDATION`
等正式业务 enum / classification。

#### 4.2.11 Time Semantics

沿用 §4.1.6 的六类时间语义，并额外登记两项：

| Field | 语义类别 | `Class` | 说明 |
| --- | --- | --- | --- |
| `required_date` | requirement time | `SOURCE` | 需求日期 |
| `effective_arrival_date` | event time | `SOURCE` | 供给真正可用日 |
| `inventory_snapshot_time` | observation time | `CONTEXT` | 库存观测时点 |
| `PerformancePeriod` | observation window | `CONTEXT` | performance 统计窗口 |
| `PerformanceUpdatedAt` | observation metadata | `CONTEXT` | performance 更新时间 |
| `AnalysisDate` | analysis run time | `CONTEXT` | 分析运行日期 |
| `FirstShortageDate` | **derived business date** | `DERIVED` | 由 `BR-SHORTAGE-001` 产生 |
| `RecommendationNeedDate` | 采购建议使用的 **business need date** | `CONTEXT` | 当前 POC `= FirstShortageDate` |

**必须明确：**

```
FirstShortageDate        = derived business date
RecommendationNeedDate   = 采购建议使用的 business need date
```

当前 POC：

```
RecommendationNeedDate = FirstShortageDate
```

但**两个 canonical concepts 不得因为当前值相同就完全混为同一字段语义**。

#### 4.2.12 Zero vs Missing

集中记录**已经批准**的 `Zero ≠ Missing` 语义（**不得改变**）：

| Field | `= 0` 的含义 | `missing` 的含义 |
| --- | --- | --- |
| `SafetyStock` | 业务明确配置为**无 Safety Stock buffer**，**合法值** | 必要配置缺失 → `DATA_INCOMPLETE`，**不得默认成 0** |
| `loss_rate` | 业务明确配置为**无损耗**，**合法值** | 必要配置缺失 → `DATA_INCOMPLETE`，**不得默认成 0** |
| `AllocatedSubstituteQty` | 该关系在本需求窗口内**未分配**任何数量，**合法值** | 必要 allocation 信息缺失 → `DATA_INCOMPLETE`，**不得默认成 0** |
| `ApplicableMOQ` | 业务明确确认**不存在**最小采购数量约束，**合法值** | 必要 MOQ 信息缺失 → `DATA_INCOMPLETE`，**不得默认成 0** |
| `DeliveryPerformance` | **合法但极差**的绩效 → `DeliveryRisk = HIGH` | 无法判断 → `DeliveryRisk = DATA_INCOMPLETE` |
| `QualityPerformance` | **合法但极差**的绩效 → `QualityRisk = HIGH` | 无法判断 → `QualityRisk = DATA_INCOMPLETE` |

**Valid Absence vs Missing Required Data**

必须区分**两类完全不同的「字段不存在」**：

| 语义 | 含义 | 是否 `DATA_INCOMPLETE` |
| --- | --- | --- |
| **valid absence / not applicable** | 该字段在当前业务状态下**本来就不适用**，或不产生 | **否** |
| **missing required data** | 本来**需要**形成可靠结果，但关键数据缺失 / invalid / unresolved | **是** |

必须保持 `DATA_INCOMPLETE` 的含义：

```
DATA_INCOMPLETE
  = 本来需要形成可靠结果，
    但关键数据缺失 / invalid / unresolved，
    因此无法可靠计算
```

**不得**将「该字段在当前业务状态下本来就不适用」**错误解释成** `DATA_INCOMPLETE`。

典型 valid absence 情形：

- `FirstShortageDate` —— 数据完整且整个 analysis horizon **从未**出现 `ProjectedAvailable < 0` → `null / not present`
- `RecommendationNeedDate` 与 procurement derived results —— `Classification` 为 `NORMAL` / `BUFFER_BREACH` 时 **not produced by design**

> 以上均为**字段存在性语义**，**不是**新的业务 status / enum。

#### 4.2.13 Quantity Constraints

**从已有 Rule 引用，而非重新发明：**

| Field / Result | Constraint | 依据 |
| --- | --- | --- |
| `ProductionQty` | `>= 0` | §2.4.3 |
| `BOMComponentQty` | `>= 0` | §2.4.3 |
| `loss_rate` | `0 <= loss_rate < 1` | §2.4.6 |
| `SafetyStock` | `>= 0` | §2.2.5 |
| `substitution_ratio` | `> 0` | §2.3.6 |
| `AllocatedSubstituteQty` | `>= 0` | §2.3.7 |
| `ordered_qty` | `>= 0` | §2.6.2 |
| `received_qty` | `>= 0` | §2.6.2 |
| `ApplicableMOQ` | `>= 0` | §2.5.7 |
| `DeliveryPerformance` | `0% ～ 100%` | §2.7.16 |
| `QualityPerformance` | `0% ～ 100%` | §2.7.16 |
| `standard_lead_time_days` | `>= 0` | §2.7.16 |

如果现有 Rule **未定义**某字段范围，则写：`NOT DEFINED`（**不得猜测**）。

#### 4.2.14 Status Semantics

对已有 status / classification **只引用现有 Rule**，**不得新增新的 status**：

| Status Field | Vocabulary | 依据 |
| --- | --- | --- |
| `inventory_status` | `AVAILABLE` / `INSPECTION` / `FROZEN` | §2.2.3 |
| `inbound_status` | 见 §2.6.3 的保守分类（含 `OPEN` / `CONFIRMED` / `PARTIALLY_RECEIVED` / `CANCELLED` / `CLOSED` / `COMPLETED`） | §2.6.3 |
| `Classification` | `NORMAL` / `BUFFER_BREACH` / `SHORTAGE` / `DATA_INCOMPLETE` | §2.1.4 |
| `approval_status` | 仅 `APPROVED` 可参与；`PENDING` / `REJECTED` / `UNKNOWN` 不得进入 | §2.3.5 |
| `LeadTimeRisk` | `LOW` / `HIGH` | §2.7.5 |
| `DeliveryRisk` / `QualityRisk` / `OverallSupplierRisk` | `LOW` / `MEDIUM` / `HIGH` / `DATA_INCOMPLETE` | §2.7.6 / §2.7.7 / §2.7.8 |
| `sourcing_status` | **source vocabulary = `SOURCE-SPECIFIC` / Adapter-defined**（**不建立全局 source enum**） | §2.7.24；**§4.5.11** |

**特别注意 `sourcing_status`：**

```
logical meaning    : Supplier-Material relationship eligibility context
source vocabulary  : SOURCE-SPECIFIC / Adapter-defined
canonical mapping  : DESIGN RESOLVED（explicit deterministic mapping → eligibility condition）
```

**不得自行创造** `ACTIVE` / `APPROVED` / `QUALIFIED` / `BLOCKED` / `INACTIVE` 等 source enum。

**不得**把 `eligible` / `ineligible` / `unresolved` 加入本状态词表 ——
它们**不是** `sourcing_status` 的 source values，而是 **canonical mapping outcome**。

#### 4.2.15 Provenance Requirement

- 所有 `SOURCE` / `POLICY_INPUT` 字段都**需要未来能够追溯 source provenance**。
- 所有 `DERIVED` result 都**必须能追溯**：

```
input evidence
+ Rule ID
+ Analysis Run
```

**但本 Task 不设计**：provenance schema、`source_system_id`、lineage database、audit event format。

> **`DERIVED` result** 的 provenance 已由 **Option D（Layered Logical Provenance Contract）**
> 正式落地（见 **§4.5.22 Option D Implementation Record**）：
>
> ```
> Derived Result Provenance = Analysis Run + Deterministic Rule ID
>                             + Upstream Canonical References / Contexts
> ```
>
> 对发生 semantic mapping 的 `SOURCE` ／ `POLICY_INPUT`，还必须能够识别
> **Mapping / Resolution Basis**（**§4.2.15** ／ **§4.4.93**）。
>
> **`provenance carrier` 属于 provenance metadata / mapping boundary，
> 不是 canonical business field** —— **未**加入 `§4.2` Canonical Data Dictionary field table。

#### 4.2.16 Open Semantic / Mapping Items

以下项目**仍然开放**，**不得为了让 Data Dictionary 看起来「完整」而消灭**：

| 项 | 状态 |
| --- | --- |
| Warehouse canonical role | **`DESIGN RESOLVED`** —— source / mapping / scope context（**§4.5.12**） |
| Provenance carrier | **`DESIGN RESOLVED`** —— **Layered Logical Provenance Contract**（**§4.5.22 Option D Implementation Record**）；**不是** canonical business field，**不进入** Data Dictionary |

> 以上条目**不影响** `Data Dictionary = DESIGN RESOLVED` ——
> 它们属于 **source mapping / Master Data Mapping / Adapter Boundary / Data Validation** 的范围。
>
> `Warehouse canonical role` 已由 **§4.5.12** 解析 ——
> Warehouse 是 **source / mapping / scope context**，**不进入** Data Dictionary 的 canonical field 集合。
>
> `BOM version / validity selection` **已从本表移出** ——
> 已由 **Human-authorized Canonical Model Amendment（PR #30 ／ Option A）** 解析为
> **requirement-scoped BOM applicability**（见 **§4.1.4 N** / **§4.5.7**）；
> `BOMComponentQty` 的 context boundary 见 **§4.2.4**。
>
> `sourcing_status` vocabulary **已从本表移出** ——
> **Supplier eligibility mapping contract** 已由 **PR #32 Human-approved Option B** 解析为
> **source-specific vocabulary → canonical eligibility condition** 的 mapping contract
> （见 **§4.1.4 I** / **§4.2.8** / **§4.5.11**）。
>
> **真实 source vocabulary 与具体 `source value → eligibility condition` 映射**
> 仍由 **Adapter / source-specific mapping** 承担 ——
> 这**不再属于** **Master Data Mapping unresolved semantic**。
>
> 因此 **unresolved count `7 → 6`**。
>
> `effective_arrival_date` source field **已从本表移出** ——
> 已由 **PR #34 Human-approved Option D** 解析：
> **canonical mapping contract = `DESIGN RESOLVED`**；
> **concrete source field / Adapter mapping = source-specific / implementation-time**。
>
> > 「**真实 source field 未知**」**不再等于** `canonical semantic DESIGN PENDING`。
>
> 因此 **unresolved count `6 → 5`**。
>
> `Allocation demand-window mapping` **已从本表移出** ——
> 已由 **PR #36 Human-approved Option B** 解析为
> **canonical allocation applicability mapping contract**
> （**Target Applicability** ＋ **Source Reservation Overlap**，见 **§4.1.4 G** / **§4.2.7** / **§4.5.9**）。
>
> > 「**真实 allocation / reservation source evidence 当前未知**」**不等于**
> > `canonical mapping contract` **仍 Design Pending**。
>
> 因此 **unresolved count `5 → 4`**。
>
> `required_quantity` vs `ProductionQty`（`SEMANTIC AMBIGUITY`）**已从本表移出** ——
> 已由 **PR #38 Human Decision** 认定为 **`ORPHAN CANONICAL FIELD`** 并从
> current POC v0.2 canonical model **移除**（详见 **§4.2.4**）。
>
> > 其当前状态是 **`REMOVED FROM CURRENT CANONICAL MODEL`** ——
> > **不是**「现在定义完成的字段」（**不是** `DESIGN RESOLVED`）。
>
> 因此 **unresolved count `4 → 3`**。
>
> **未新增** `BOMVersion` / `ValidFrom` / `ValidTo` / `BOM ID` / `ProductionVersion` /
> `AlternativeBOM` / `Change Number` / `ArrivalDateSourceType` / `ArrivalDatePriority` /
> `ArrivalConfidence` / `source_field_name` 等 canonical fields。
>
> **本 Task 不定义任何 source table / column**，因此**未被偷渡**任何 source mapping。
>
> `loss_rate` canonical owner / grain 的 **Design Review** 见 **§4.5.22** ——
> `loss_rate` canonical owner / grain **已从本表移出** ——
> 其 **Option E semantic synchronization 已实施**（见 **§4.5.22 Option E Implementation Record**）；
> owner = **exact Requirement Calculation Context**，
> resolution contract = **exactly one applicable `loss_rate` or `unresolved`**。
>
> > 其当前状态是 **`DESIGN RESOLVED`** —— 但 **physical carrier** 仍
> > **`SOURCE-SPECIFIC` / not yet defined**（不因本项关闭）。
>
> 因此 **unresolved count `3 → 2`**。

#### 4.2.17 Status Semantics Boundary

`Data Dictionary = DESIGN RESOLVED` **仅**表示：

```
canonical field semantics defined
```

**不表示**：source mapping complete、physical schema complete、import contract complete、
data validated、implemented、tested。

---

<!-- END MIGRATED LEGACY §4.2 BODY -->
