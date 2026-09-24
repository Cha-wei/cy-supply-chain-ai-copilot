# Canonical Data Model

**Document / Topic:** Canonical Data Model
**Parent Design:** [POC Design v0.2](../../poc-design-v0.2.md)
**Legacy Section:** §4.1（§4.1.1 ～ §4.1.13 编号保留）
**Design Status:** `DESIGN RESOLVED`
**Implementation Status:** `NOT STARTED`
**Canonical Authority:** 本文件是 Canonical Data Model concern 的唯一 current canonical source；parent design 保留 navigation/status 入口。
**Migration Base:** `5917cb2fa4b71d4a7379128447bc9e766d17e6da`

<!-- BEGIN MIGRATED LEGACY §4.1 BODY -->
### 4.1 Canonical Data Model

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

#### 4.1.1 Purpose & Scope

本子章节只回答：

> POC 业务逻辑中有哪些 **canonical business entities**，它们分别代表什么，如何关联，由哪些既有 Rule 使用。

**本 Task 不回答**：

- 数据库表怎么建
- SQL Schema
- ORM model
- JSON Schema
- API Contract
- CSV column layout
- concrete file format
- database selection
- backend framework
- storage engine
- implementation class

#### 4.1.2 Source of Truth

本模型**从当前 Repository 已 `DESIGN RESOLVED` 的内容反向提取**：

- `§2` P0 Business Rules（`BR-SHORTAGE-001`、`BR-INVENTORY-001`、`BR-SUBSTITUTE-001`、
  `BR-REQUIREMENT-001`、`BR-PROCUREMENT-001`、`BR-INBOUND-001`、`BR-SUPPLIER-RISK-001`）
- `§3` System Boundary
- `§5` AI / Tool Boundary

**不得凭空增加未来能力需要的数据对象。**

如果某字段 / 概念是否必要**无法从现有 Design 支撑**，则标记为 `DESIGN PENDING` 或 `UNKNOWN`，**不得猜测**。

#### 4.1.3 Canonical Entity Catalog

| # | Entity | Purpose | Canonical identity / grain | 主要使用方 |
| --- | --- | --- | --- | --- |
| A | **Plant** | 业务计算边界 | `plant_id` | 全部 Rule |
| B | **Material** | canonical material identity | `material_code` | 全部 Rule |
| C | **Production Requirement** | 生产需求来源 | `plant_id` + `material_code` + `required_date` | `BR-REQUIREMENT-001`、`BR-SHORTAGE-001` |
| D | **Inventory Snapshot** | 可用库存观测 | `plant_id` + `material_code` + `inventory_snapshot_time` ＋ status context | `BR-INVENTORY-001` |
| E | **Inbound Supply** | 未来可能成为有效供给的 inbound record | `plant_id` + `material_code` ＋ inbound identity | `BR-INBOUND-001` |
| F | **Substitute Relationship** | 已登记的替代关系（**有方向**） | `plant_id` + `target_material_code` + `substitute_material_code` | `BR-SUBSTITUTE-001` |
| G | **Substitute Allocation** | 明确分配（**独立于 F**） | source substitute ＋ target ＋ effective demand context | `BR-SUBSTITUTE-001` |
| H | **Supplier** | supplier identity | `supplier_id` | `BR-SUPPLIER-RISK-001` |
| I | **Supplier-Material Relationship** | 供应商—物料关系与 eligibility context | `supplier_id` + `material_code` | `BR-SUPPLIER-RISK-001` |
| J | **Supplier Performance** | performance 观测（含 measurement period） | `supplier_id` + `material_code` + `PerformancePeriod` | `BR-SUPPLIER-RISK-001` |
| K | **Procurement Recommendation** | 采购数量建议 | 业务 grain：`plant_id` + `material_code` + `RecommendationNeedDate`；**observation context：** Analysis Run ＋ 上述 grain | `BR-PROCUREMENT-001` |
| L | **Procurement Request Draft** | POC 内 Draft | 由 K 派生（POC 内） | `§3`、`§5` |
| M | **Analysis Run** | 一次分析运行的上下文 | canonical identity：analysis run identity；temporal context：`AnalysisDate` | `BR-SHORTAGE-001`、`BR-PROCUREMENT-001`、`BR-SUPPLIER-RISK-001` |

**支撑性 canonical concepts**（由既有 Rule 直接要求，不属最低 A–M 清单）：

| # | Concept | Purpose | Canonical identity / grain | 依据 |
| --- | --- | --- | --- | --- |
| N | **BOM Component** | requirement-scoped applicable BOM relationship | `Production Requirement context` + component `material_code`<br>（= `plant_id` + parent / requirement `material_code` + `required_date` + component `material_code`） | §2.4.2、§2.4.3；**Human-approved amendment（PR #30 ／ Option A）** |
| O | **Configured Safety Stock** | 业务配置的安全库存 | `plant_id` + `material_code` | §2.2.5 |

> `N` / `O` **不是**本 Task 新引入的能力，而是 §2 已 `DESIGN RESOLVED` 规则**直接引用**的输入；
> 因此**必须**在 canonical model 中有明确归属，否则模型无法支撑既有 Rule。

#### 4.1.4 Entity Definitions

**A. Plant**

- **Purpose：** 表示业务计算边界中的 Plant。
- **Canonical identity：** `plant_id`
- **Attributes：** 至少 `plant_id`
- **不得设计** Plant Master 全量属性。

**B. Material**

- **Purpose：** canonical material identity。
- **Canonical identity：** `material_code`
- **Attributes：** 至少 `material_code`
- **不得扩展**成完整 Material Master。

**C. Production Requirement**

- **Purpose：** 表达生产需求，支撑 `BR-REQUIREMENT-001` 与 `BR-SHORTAGE-001`。
- **Canonical identity / grain：** `plant_id` + `material_code` + `required_date`
- **Attributes：** 至少
  - plant → `plant_id`
  - material → `material_code`
  - `required_date`
  - `ProductionQty`
- **必要来源关系：** 必须能够**追溯到** `BOM relationship`（见 `N`）与 `loss_rate` 计算来源（见 §4.1.12）。
- **约束：** **不得跨 Plant 合并需求**。
- **Human-authorized Canonical Model Amendment（PR #38 Human Decision）：**
  `required_quantity` 已从本 entity 的 **attributes** 中**移除**。
  原因：它被证明**无 approved independent semantic**、**无 Rule consumer**、
  **无独立 source evidence**、**无独立 grain / ownership**，
  且**删除不影响**任何现有 approved calculation（详见 **§4.2.4**）。
  这是 **Human-approved removal** —— **不是** Agent 自行清理字段。
  **grain 未改变**（仍 `plant_id` + `material_code` + `required_date`），**未新增**任何替代字段。

**D. Inventory Snapshot**

- **Purpose：** 支撑 `BR-INVENTORY-001`。
- **Canonical identity / grain：** `plant_id` + `material_code` + `inventory_snapshot_time` ＋ status context
- **Attributes：** 至少
  - plant → `plant_id`
  - material → `material_code`
  - `inventory_snapshot_time`
  - inventory status
  - quantity
- 必须能区分 `AVAILABLE` / `INSPECTION` / `FROZEN`。
  **不得设计数据库 enum implementation。**
- **约束：** 状态未知或非法时**不得猜测**，**不得静默归类为 `AVAILABLE`**。

**E. Inbound Supply**

- **Purpose：** 支撑 `BR-INBOUND-001`；表示未来**可能**成为有效供给的 inbound business record。
- **Canonical identity / grain：** `plant_id` + `material_code` ＋ inbound record identity
- **Attributes：** 至少
  - plant → `plant_id`
  - material → `material_code`
  - `ordered_qty`
  - `received_qty`
  - `effective_arrival_date`
  - status / eligibility context
- **派生：** `RemainingInboundQty = ordered_qty - received_qty`
- **约束：** **不得绑定真实 ERP PO Schema**。

**F. Substitute Relationship**

- **Purpose：** 支撑 `BR-SUBSTITUTE-001`；表示**已登记**的替代关系。
- **Canonical identity / grain：** `plant_id` + `target_material_code` + `substitute_material_code`
- **Attributes：** 至少
  - plant → `plant_id`
  - target material → `target_material_code`
  - substitute material → `substitute_material_code`
  - `substitution_ratio`
  - approval context → `approval_status`
- **方向性：** 关系**有方向**；`A 可被 B 替代` **不代表** `B 可以被 A 替代`；**不得自动建立双向关系**。

**G. Substitute Allocation**

- **Purpose：** 支撑 `BR-SUBSTITUTE-001`；表达**实际被分配**的替代供给量。
- **必须与 `F` 分开评估**，因为：
  ```
  Approved relationship
    ≠ actual allocated quantity
  ```
- **Canonical identity / grain：** source substitute material ＋ target material ＋ effective demand context（**未改变**）
- **Attributes：** 至少
  - source substitute material
  - target material
  - `AllocatedSubstituteQty`
  - effective demand context
- **`effective demand context` —— conceptual resolved context（**不是** physical field）：**

  它**不是**：

  - 单一 `required_date` field
  - `requirement_id`
  - date range field
  - `allocation_period`
  - persisted window object

  它是一个 **conceptual resolved context**，用于承载**两个互相独立**的 relation：

  ```
  1. Target Applicability          —— allocation 对哪些 Target Demand Context
                                      可以作为 Approved Substitute Supply
  2. Source Reservation Overlap    —— 同一已分配 Source Supply 与哪些 Source Demand
                                      Context 发生 reservation overlap
  ```

  这两个 relation **共同**定义 allocation 在当前业务需求时间语境中的**有效性**。

  **必须保持：** `Target Applicability ≠ Source Reservation Overlap` —— **不得压成一个 Boolean**。

  **不得**把 `effective demand context` 误解成一个**新的 physical field**；
  **不得**新增 canonical field / canonical entity / identity component
  （**不得**创建 `requirement_id` / `demand_window_id` / `allocation_period` / `valid_from` / `valid_to`）。
- **用途：** 支撑 `RemainingUnallocatedSourceSupply` 与 **No Double Allocation**。
- **约束：** `Σ AllocatedSubstituteQty <= EligibleSubstituteSupply`（见 §2.3.10）。
- **Human-authorized Design Change（PR #36 ／ Option B）：**
  本节仅**澄清** `effective demand context` 的 conceptual meaning ——
  **grain 与 attributes 均未改变**，也**未新增**任何 canonical field。

**H. Supplier**

- **Purpose：** 只保留 Supplier identity。
- **Canonical identity：** `supplier_id`
- **不得扩展**为完整 Supplier Master。

**I. Supplier-Material Relationship**

- **Purpose：** 支撑 `BR-SUPPLIER-RISK-001`。
- **Canonical identity / grain：** `supplier_id` + `material_code`（**未改变**）
- **Attributes：** 至少
  - supplier → `supplier_id`
  - material → `material_code`
  - relationship eligibility context → `sourcing_status`
    （**source / mapping eligibility evidence context**）
- **Relationship Eligibility Condition（conceptual mapping outcome，非 canonical field）：**

  `sourcing_status` 作为 **source-specific evidence**，通过 **explicit deterministic mapping**
  形成 conceptual **Relationship Eligibility Condition**：

  ```
  source-specific sourcing_status
          ↓
  explicit deterministic mapping evidence
          ↓
  Relationship Eligibility Condition
          ↓
  eligible  /  ineligible  /  unresolved
  ```

  `eligible` / `ineligible` / `unresolved` **只是 conceptual mapping conditions** ——
  **不是** source-system enum、canonical persisted enum、Business Status、Supplier Risk level、
  database field、API enum、ranking 或 selection result。

  **不得**把该 tri-state 登记为**新的 canonical persisted field**。
- **Source vocabulary policy：** `source sourcing_status vocabulary = SOURCE-SPECIFIC`。
  具体 `source value → eligibility condition` 映射由**未来 Adapter / source-specific mapping** 明确提供。
  `SOURCE-SPECIFIC` 是**设计描述**，**不得**创建成 runtime enum value。
- **约束：** **不得自行定义** `sourcing_status` enum / vocabulary；**不得**建立全局
  `APPROVED` / `ACTIVE` / `QUALIFIED` / `BLOCKED` / `INACTIVE` 等 source enum。
- **Relationship Existence Boundary：**

  ```
  Supplier exists + Material exists        ≠  Supplier-Material Relationship exists
  Supplier-Material Relationship exists    ≠  relationship eligible
  ```

  必须经过 **eligibility mapping evidence**；**不得** `relationship exists → 默认 eligible`。
- **不得创建** `is_eligible` / `SupplierEligibilityStatus` 等 canonical field。
- **不得**因为 Supplier Master 中存在某 Supplier 就推断其可供应任意 Material。

**J. Supplier Performance**

- **Purpose：** 支撑 `BR-SUPPLIER-RISK-001`。
- **Canonical identity / grain：** `supplier_id` + `material_code` + `PerformancePeriod`
- **Attributes：** 至少
  - supplier → `supplier_id`
  - material → `material_code`
  - `PerformancePeriod`
  - `PerformanceUpdatedAt`
  - `DeliveryPerformance`
  - `QualityPerformance`
- **必须保持：**
  ```
  measurement period  ≠  updated_at
  ```
  即 `PerformanceUpdatedAt` **不能替代** `PerformancePeriod`。
- 另需 `standard_lead_time_days` 供 Lead Time Feasibility 使用（见 §2.7.3 / §2.7.5）。

**K. Procurement Recommendation**

- **Purpose：** 支撑 `BR-PROCUREMENT-001`。
- **Business grain：** `plant_id` + `material_code` + `RecommendationNeedDate`
- **Canonical observation context：**
  ```
  Analysis Run
    + plant_id
    + material_code
    + RecommendationNeedDate
  ```
  **每一条 Procurement Recommendation 必须属于一个明确的 Analysis Run。**
  > 这里**不是**定义 database primary key，也**不是** UUID 设计。
  > 目的是区分：**同一个 material / plant / need date 在不同 analysis runs 中产生的 recommendation。**
- **Traceability：** Procurement Recommendation **必须可以追溯**到产生它的 Analysis Run，
  以便未来区分同一业务 grain 在**不同 snapshot / analysis time** 下得到的不同 recommendation。
- **Attributes：** 至少
  - analysis run → 所属 Analysis Run
  - plant → `plant_id`
  - material → `material_code`
  - `RecommendationNeedDate`
  - `ShortageQty`
  - `BasePurchaseNeed`
  - `ApplicableMOQ`
  - `MOQAdjustmentQty`
  - `RecommendedPurchaseQty`
- **必须明确：**
  ```
  Recommendation  ≠  Approval  ≠  Purchase Order
  ```

**L. Procurement Request Draft**

- **Purpose：** 支撑 `§3` / `§5`；表示 **POC 内** Draft。
- **Must be explicit：**
  ```
  POC Draft
    ≠ ERP Purchase Request
    ≠ Purchase Order
  ```
- **约束：** Draft 只存在于 `POC / Draft Boundary`，**不产生**真实业务系统副作用。

**M. Analysis Run / Snapshot Context**

- **Purpose：** 关联当前 snapshot、calculation timestamp、recommendation result、explanation evidence。
- **存在依据（来自既有 Design）：**
  - `§2.5.3` 以「**一次 shortage analysis run**」为建议生成边界；
  - `§2.7.4` / `§3` 使用 `AnalysisDate`；
  - `§2.1.2` 的累计计算依赖「截至 `t`」的观测口径。
- **Canonical identity：** analysis run identity
- **Attribute / temporal context：** `AnalysisDate`
- **结论：** 现有 Design **足以支持**该概念，因此**予以实体化**。
- **不得设计：** UUID format、database key、ID generation algorithm。
- **不得**把 `AnalysisDate` 与 identity **混成一个复合主键概念**。

**N. BOM Component（支撑性）**

- **Purpose：** 表达物料需求展开来源，支撑 `BR-REQUIREMENT-001`。
- **Canonical identity / grain：** `Production Requirement context` + component `material_code`

  其中：

  ```
  Production Requirement context
    = plant_id
    + parent / requirement material_code
    + required_date
  ```

  展开后的概念等价形式为：

  ```
  plant_id
  + parent / requirement material_code
  + required_date
  + component material_code
  ```

  > 这里**不是**定义 physical composite key / database primary key；
  > 而是表达 **grain** —— 即「哪个 requirement context 下的哪一条 component relationship」。
- **Relationship role clarification（不新增字段）：** 在 BOM relationship context 中，
  `Production Requirement.material_code` 扮演 **parent / produced material** 角色。

  这是 **contextual role clarification** —— **不** rename 全局 `material_code`、
  **不**新增 `parent_material_code` canonical field、
  **不**修改 Entity C `Production Requirement` 的 grain。
- **Attributes：** 至少
  - `BOMComponentQty`
  - component material identity（`material_code`）
- **`BOMComponentQty` 的 canonical meaning：** **只**在其所属 **Production Requirement context**
  中具有 canonical meaning。**不得**把同一 `Plant` + `Parent` + `Component` 跨 `required_date`
  视作**同一个** BOM Component grain —— 它们在 canonical model 中是**彼此独立**的
  requirement-scoped relationships。
- **Applicability anchor（`SIMULATED POC Design Policy` ＋ `Human-approved`）：**

  ```
  Production Requirement.required_date
    = BOM applicability business-time anchor
  ```

  **不得**描述为**真实 CY 企业 BOM selection rule**。
  **不得**使用 Snapshot creation time / Package export time / `AnalysisDate` /
  system current time **替代** `required_date` 来选择 applicable BOM。
- **Applicable BOM Definition（conceptual，非 canonical entity）：**
  对一个明确的 Production Requirement context 能够**唯一确定**的一组
  `parent Material → component Material → BOMComponentQty` relationships 的
  **conceptual grouping**。它**不是**新的 canonical entity。
- **约束：** 无法可靠确定适用 BOM → `DATA_INCOMPLETE`。
- **仍然 `DESIGN PENDING`（本 Task 不设计）：**
  - BOM explosion algorithm
  - ERP source-field mapping
  - `BOMVersion` / `ValidFrom` / `ValidTo` / `Change Number` / `Production Version` /
    `Alternative BOM` / `BOM Header` entity / `BOM Version` entity / `BOM ID`
- **Human-authorized Canonical Model Amendment：**
  本节 grain 由 **PR #30 Human Decision（Option A）** 授权修改，
  用于消除 **time-varying / version-varying BOM** 的 **applicability grain collision**。

  授权范围**仅限**该问题；**未**改动其他 canonical entities、其他 Rule 的 calculation grain、
  `loss_rate` owner / grain、`required_quantity` semantic，也**未**改动 `§2` Business Rules。

  该修改**不**表示真实 ERP BOM mapping 已实现。

**O. Configured Safety Stock（支撑性）**

- **Purpose：** 支撑 `BR-INVENTORY-001` / `BR-SHORTAGE-001`。
- **Canonical identity / grain：** `plant_id` + `material_code`
- **Attributes：** 至少 `SafetyStock`（业务配置提供的**非负**数量）
- **当前不设计：** statistical safety stock、service-level calculation、
  demand / lead-time variability model、dynamic safety stock、AI-generated safety stock。

#### 4.1.5 Relationship Model

```
Plant
  → has Material business context

Material
  → has Production Requirement
  → has Inventory Snapshot
  → has Inbound Supply

Target Material
  ← Substitute Relationship →
Substitute Material

Substitute Relationship
  → Substitute Allocation

Supplier
  ↔ Supplier-Material Relationship
  ↔ Material

Supplier-Material Relationship
  → Supplier Performance

Analysis Run
  → produces deterministic Shortage Result
     (derived result, not an independently modeled canonical entity in this Task)

Analysis Run
  → produces Procurement Recommendation

Procurement Recommendation
  → Procurement Request Draft

Production Requirement
  → has applicable BOM Component relationships
     （requirement-scoped；这些 relationships 属于该 Production Requirement context）

Material
  → Configured Safety Stock
```

**不得因为画关系就创造未批准业务流程。**

> 上述关系仅表达**既有 Rule 已依赖的关联**，**不新增**任何流程、审批或自动化能力。

**关于 `Shortage Result`（不额外实体化）：**

`Shortage Result` 是 **`BR-SHORTAGE-001` 的 deterministic derived result**，
**本 Task 不把它额外实体化** —— 它**不在** canonical entity catalog 中。

因此本 Task **不新增** `P` / `Q` 等实体，也**不**为 `Shortage Result` 定义独立身份或属性。

`Procurement Recommendation` 与 `Shortage Result` 的关系由 **Analysis Run** 承载：

```
Analysis Run
  → produces deterministic Shortage Result   (derived)
  → produces Procurement Recommendation
```

> 说明来源：`BR-SHORTAGE-001` 产出的 `Classification` / `ShortageQty` / `FirstShortageDate` 等
> 均为该规则的**计算结果**，其 canonical 定义仍归 `§2.1`，**不因本 Model 而迁移**。

#### 4.1.6 Time Semantics

必须区分：

```
event / requirement time
与
snapshot / observation time
```

以下时间语义**互不相同**，**不得合并为一个统一 `date` 字段**：

| 时间 | 语义类别 | 归属 |
| --- | --- | --- |
| `required_date` | requirement time | Production Requirement |
| `effective_arrival_date` | event time（供给可用日） | Inbound Supply |
| `inventory_snapshot_time` | observation time | Inventory Snapshot |
| `PerformancePeriod` | observation window | Supplier Performance |
| `PerformanceUpdatedAt` | observation metadata | Supplier Performance |
| `AnalysisDate` | 分析运行时间 | Analysis Run |

#### 4.1.7 Quantity Semantics

必须保持以下 canonical quantities **彼此分离**：

- `OpeningUsableInventory`
- `GrossRequirement`
- `EffectiveInbound`
- `ApprovedSubstituteSupply`
- `ShortageQty`
- `BufferGap`
- `BasePurchaseNeed`
- `MOQAdjustmentQty`
- `RecommendedPurchaseQty`

**不得因为它们都是 quantity 就合并成一个通用 `quantity` field。**

实体层**可以引用**这些 business meanings，但**不得重新定义 Rule**。

#### 4.1.8 Provenance Requirement

Canonical Data Model **必须保留**未来能够追踪：

> 这个事实来自哪里。

本 Task **只定义**：

```
provenance is required
```

**不得设计**具体：

- `source_system_id`
- lineage DB
- event bus
- audit schema

这些进入后续 **Data Dictionary / Audit Design**。

> **Provenance Carrier / Minimum Traceability Contract Design Review（Review Finding）** ／
> **Human Decision Record** ／ **Option D Implementation Record** 见 **§4.5.22** ——
> **Option D = IMPLEMENTED**；**Layered Logical Provenance Contract** 已落地，
> 因此 `provenance carrier` **现为 `DESIGN RESOLVED`**，未决项数量 **1 → 0**。

#### 4.1.9 Missing / Unknown Boundary

Canonical model **不得通过默认值隐藏缺失**。

必须继续支持：

- missing
- invalid
- unresolved
- `DATA_INCOMPLETE`

例如：

- `SafetyStock` missing
- `ApplicableMOQ` missing
- `PerformancePeriod` missing

**不得因为建立 data model 就自动补默认值。**

#### 4.1.10 Simulated Environment Boundary

必须明确：这些 canonical entities 是 **POC 内的 business representation**。

它们**不代表**：

- 真实 CY ERP schema
- 真实 CY WMS schema
- 真实 CY PLM schema

**不得声称**真实系统存在同名表 / 字段。

#### 4.1.11 Explicit Non-Model

`Canonical Data Model` **不包含**：

- physical database design
- table / column definition
- primary key / index
- UUID 生成规则
- API Contract
- Transport / file format
- storage engine
- framework / ORM

#### 4.1.12 Open Items（`DESIGN PENDING` / `UNKNOWN`）

以下项目**无法从现有 Design 可靠支撑**，因此**不得猜测**：

| 项 | 状态 | 说明 |
| --- | --- | --- |
| `loss_rate` 的 canonical owner / grain | **`DESIGN RESOLVED`** | owner = **exact Requirement Calculation Context**；applicability grain **至少** `plant_id` + parent / requirement `material_code` + `required_date` + component `material_code`；resolution contract = **exactly one applicable `loss_rate` or `unresolved`**；**未新增** canonical field / entity，**未**修改任何 entity grain；physical carrier **仍 SOURCE-SPECIFIC / not yet defined**（**§4.2.4** ／ **§4.5.22**） |
| Warehouse 是否为 canonical attribute | **`DESIGN RESOLVED`** | **不是** canonical attribute —— Warehouse 是 source / mapping / scope context（**§4.5.12**）；§2.2.1 的 grain **不含** warehouse |
| `sourcing_status` enum / vocabulary | **`DESIGN RESOLVED`** | **不建立全局 source enum** —— source vocabulary = **`SOURCE-SPECIFIC`**；canonical eligibility mapping contract 见 **§4.1.4 I** ／ **§4.5.11** |
| **`effective_arrival_date` source mapping policy** | **`DESIGN RESOLVED`** | **不建立 global source field** —— concrete source field = **`SOURCE-SPECIFIC` / Adapter-defined**；canonical mapping contract 见 **§4.2.6** ／ **§4.5.21**；**真实 ERP field 当前仍未知**（**未知 ≠ Design Pending**） |
| Allocation 与 demand window 的关联机制 | **`DESIGN RESOLVED`** | 已由 **§4.5.9** 解析为 **canonical allocation applicability mapping contract**（**Target Applicability** ＋ **Source Reservation Overlap**）；concrete source evidence = **`SOURCE-SPECIFIC` / Adapter-defined**；**未新增** canonical field |
| `ApplicableMOQ` 的来源 | **`DESIGN RESOLVED`** | canonical applicability resolution 由 **§4.5.22 Option D Implementation Record** 解析：owner = **exact Procurement Recommendation Context**（`plant_id` + `material_code` + `RecommendationNeedDate`）；source semantic role = **`SOURCE-SPECIFIC` purchasing-policy evidence**；resolution contract = **exactly one applicable `ApplicableMOQ` or `unresolved`**；**未新增** canonical field / entity，**未**修改 Recommendation grain；physical carrier **仍 SOURCE-SPECIFIC / not yet defined**（**§4.2.9** ／ **§4.4.67**） |
| Provenance 的具体承载方式 | **`DESIGN RESOLVED`** | **Layered Logical Provenance Contract** 已由 **§4.5.22 Option D Implementation Record** 实施：`Snapshot Package Identity` + `Logical Dataset Role` + **`Stable Source Evidence Locator`** + `Mapping / Resolution Basis`（when applicable）+ `Analysis Run linkage`；**logical carrier ≠ physical carrier** —— physical carrier **design** 已由 **§4.3** 关闭（`Field Carrier Mapping` 见 **§4.3.25** ／ **§4.3.27**；`Final Import Contract` 见 **§4.3.28** ／ **§4.3.29**，**Issue #66 Closure**）；**但** actual **source-specific ／ Adapter realization 仍 `NOT STARTED`**，**不得**被声称已完成；**未新增** canonical field / entity（见 §4.1.8） |

> 以上条目**不影响** `Canonical Data Model = DESIGN RESOLVED` ——
> 它们属于**后续 Master Data Mapping / Adapter Boundary** 的范围，
> 其**语义层面**已在 **§4.2 Data Dictionary** 中登记（见 §4.2.16）。
>
> `Warehouse 是否为 canonical attribute` 已由 **§4.5.12 Warehouse Role Resolution** 解析 ——
> 结论是**不是** canonical attribute。
>
> `BOM version / validity selection` **已从本表移出** ——
> 它已由 **Human-authorized Canonical Model Amendment（PR #30 Human Decision ／ Option A）** 解析；
> 结论见 **§4.1.4 N**（BOM Component grain 现携带 Production Requirement context）
> 与 **§4.5.7 Option A Implementation Record**。
>
> `sourcing_status` enum / vocabulary 已由 **Human-authorized Design Change
> （PR #32 Human Decision ／ Option B）** 解析 —— **不建立全局 source enum**，
> 而是 **source-specific vocabulary → canonical eligibility condition** 的 **mapping contract**
> （见 **§4.1.4 I** ／ **§4.5.11 Option B Implementation Record**）。
>
> **`effective_arrival_date` source mapping policy** 已由 **Human-authorized
> documentation/status alignment（PR #34 ／ PR #35）** 同步为 **`DESIGN RESOLVED`** ——
> **不建立 global source field**；具体 source field 由 **source-specific Adapter mapping** 提供；
> canonical mapping contract 见 **§4.2.6** ／ **§4.5.21**。
>
> **必须明确：**
>
> ```
> DESIGN RESOLVED  ≠  real ERP field known
> DESIGN RESOLVED  ≠  Adapter implemented
> DESIGN RESOLVED  ≠  mapping tested
> ```
>
> 当前解决的是 **canonical source-mapping policy**，
> 而**不是** **具体 source-system field selection**。
>
> **真实 ERP field 当前仍未知** —— **真实 ERP field 未知 ≠ Design Pending**。
>
> **`loss_rate` canonical owner / grain** 已由 **Human-authorized Design Change** **解析** ——
> **Human Decision Record** 与 **Option E Implementation Record** 见 **§4.5.22**；
> owner = **exact Requirement Calculation Context**，
> resolution contract = **exactly one applicable `loss_rate` or `unresolved`**。
> 本项**不再属于未决项**，未决项数量 **3 → 2**。
>
> **`ApplicableMOQ` 的来源** 已由 **Human-authorized Design Change** **解析** ——
> **Human Decision Record** 与 **Option D Implementation Record** 见 **§4.5.22**；
> owner = **exact Procurement Recommendation Context**，
> source semantic role = **`SOURCE-SPECIFIC` purchasing-policy evidence**，
> resolution contract = **exactly one applicable `ApplicableMOQ` or `unresolved`**。
> 本项**不再属于未决项**，未决项数量 **2 → 1**。
>
> **Clarification（`§4.1` 最小澄清 —— 未新增 canonical field ／ entity ／ identity component）：**
> 现有 **Procurement Recommendation** 已经具有**足够的 canonical applicability context**
> 来承载 `ApplicableMOQ` resolution —— 其 business grain
> （`plant_id` + `material_code` + `RecommendationNeedDate`）与 Analysis Run observation context **不变**，
> 且 **`ApplicableMOQ` 仍为 `§4.1.4 K` 的既有 attribute**。
>
> **不得**把 `supplier_id` ／ `contract_id` ／ `policy_id` ／ `purchasing_info_record_id`
> 加入 canonical grain；**不得**引入 Supplier Selection result 或 Contract identity。
>
> ```
> Analysis Run  ≠  MOQ business owner
> ```
>
> Analysis Run **只**是 **observation / traceability context**。

#### 4.1.13 First-Tranche Canonical Object Construction Boundary（Issue #125 Human Decision Record）

**Registration Status：`REGISTERED`** —— 依据 **Issue #125 Human Decision**（**D-1 ～ D-10 全部 `APPROVED`**）。

本小节**只**登记 first deterministic tranche 的 canonical object construction boundary：
canonical entity catalog（`§4.1.3` ／ `§4.1.4`）的 grain ／ attribute **完全未变**；本小节只补充
「构造期需要哪些已批准 context，以及未完整 grain 如何被 representative 表示」。
**未新增** canonical entity。

**A. Canonicalization target assignment**

downstream canonicalization 只在 **§4.3.31 B** 的 12 个 recognized role literal 上执行 role → target
assignment；target 仅取自 `§4.1.3` ／ `§4.1.4` 的既有 entity ／ relationship ／ context。未识别 role ⇒
`not_evaluable`（**§4.4.102**），不产生 Layer-1 rejection。

**B. Inbound Supply `inbound record identity`（`§4.1.4 E`，G3-A）**

```
first-tranche implementation representation
  = AcceptedPackage-scoped deterministic technical record reference
    = current AcceptedPackage identity
      + exact recognized logical dataset role = `Inbound Supply`
      + dataset-internal record ordinal over the accepted stable content view
```

该 reference **不是** canonical field、**不是** canonical identity 的 production resolution：
**grain 定义未改变**，`§4.1.4 E` 的 `inbound record identity` 语义**未改变**。
其 scope ／禁止项见 **§4.3.31 D**。

```
source-specific ／ real Adapter inbound business identity = OPEN
      （revisit before real Adapter or production integration）
```

**C. BOM Component（`§4.1.4 N`，G4-A）**

- `BOM Component` role 下的 `material_code` = **component material identity**（属 contextual role
  clarification，**不** rename 全局 `material_code`，**不**修改 entity C 的 grain）；
- parent ／ requirement context **必须**引用**已经 constructed ／ resolved** 的 Production Requirement
  context（`plant_id` ＋ parent `material_code` ＋ `required_date`），并保留其 upstream provenance；
- **不得**由 caller 无来源地创建 parent context。

```
形成的 grain（未改变）：
  plant_id ＋ parent ／ requirement material_code ＋ required_date ＋ component material_code
```

record 内若同时携带 `plant_id` ／ `required_date`，必须与 context **exact 相等**；不一致 ⇒
`CONSISTENCY` ／ `CONSISTENCY_CONFLICT`，**不得** silent precedence。

**不批准**：`parent_material_code` canonical field、BOM Version entity、BOM Header entity、BOM ID entity。

**D. Substitute Allocation `effective demand context`（`§4.1.4 G`，G5-A）**

`effective demand context` 采用 **read-only in-memory reference object**：

```
不是 canonical field
不是 persisted entity
不是 single boolean
不新增 identity component
```

其两个 relation outcome **必须**来自 approved mapping evidence，可追溯到 **same AcceptedPackage**，
并保留 provenance ＋ mapping basis；**不得**由 caller 手工指定 outcome 以绕过 mapping：

```
Target Applicability  ≠  Source Reservation Overlap（不得压成一个 Boolean）
```

`§4.1.4 G` 的 grain 与 attributes **未改变**；**未**新增 `requirement_id` ／ `demand_window_id` ／
`allocation_period` ／ `valid_from` ／ `valid_to`。

**E. `POLICY_INPUT` ／ `CONTEXT` context**

`loss_rate` ／ `SafetyStock` ／ `ApplicableMOQ` ／ `AnalysisDate` ／ `RecommendationNeedDate` 以
**已 resolved value ＋ provenance** 经 **§4.3.31 E** 的 in-process logical handoff 提供；
`loss_rate` 的 Entity ／ Dataset ／ Source Field 归属**仍不得**决定（§4.4.15）。
`RecommendationNeedDate` = `FirstShortageDate`（§4.4.65），**不是**任意 runtime injected date。

**F. Registration Boundary ／ status**

- **未新增** canonical entity ／ canonical business field ／ identity component；
- **未修改** 任何 entity grain ／ attributes；
- **未修改** `adr-001-deterministic-core.md`；
- 本小节**不代表** implementation。

```
first-tranche canonical object construction boundary = REGISTERED（Issue #125 Human Decision）
Canonical Data Model                                 = DESIGN RESOLVED（§4.1.1 ～ §4.1.12 结论未变）
Runtime implementation                                = NOT STARTED
```

---

<!-- END MIGRATED LEGACY §4.1 BODY -->
