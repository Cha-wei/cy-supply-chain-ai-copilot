# POC Design v0.2

**Document:** POC Design
**Version:** v0.2
**Status:** `DRAFT`
**Phase:** POC Design
**Entry Gate:** `READY`

**继承的 FROZEN baseline：**

- `docs/discovery/discovery-brief-v0.1.1.md`（v0.1.1，`FROZEN`）
- `docs/discovery/discovery-validation-v0.1.md`（v0.1，`FROZEN`，Human-approved，Frozen Date 2026-09-21）

> **文档性质**：本文件是 **POC Design 阶段的 Canonical Source**。
>
> 它**继承**上述两个 `FROZEN` baseline，但**不得重新解释或覆盖** FROZEN Discovery 的任何内容。
>
> **当前状态**：`DRAFT`。本文档继承已冻结的 Discovery Baseline，并已包含若干已经 Human-approved、状态为 `DESIGN RESOLVED` 的 P0 business rules；**尚未解决的设计项继续登记为 `DESIGN PENDING` / `NOT STARTED`**。
>
> **`DESIGN RESOLVED` 不代表 `IMPLEMENTED`，也不代表 `TESTED`**；本文档**未获得** `APPROVED` / `FROZEN`，也**仍未包含**任何 implementation code。

---

## Language Convention

本文档采用：

- **正式说明默认中文。**

以下保留 English：

- technical identifiers
- code elements
- filenames / paths
- API / DB fields
- Git / GitHub metadata
- formal status words
- necessary technical terms

例如：`DRAFT`、`FROZEN`、`READY`、`Adapter`、`HITL`、`RBAC`、`Rule Engine`、`Mock API`。

不强行全部翻译为中文，也不把整篇文档写成英文。

---

## Design Principles Inherited from Discovery

本节登记**已经成立的设计约束**，**不扩展为具体 Architecture**。

### 事实与计算

Structured facts 来自受控数据源 / Tool。

LLM **不创造**：

- Inventory
- BOM
- Purchase Order
- Lead Time
- Supplier Performance
- deterministic calculation result

确定性问题**优先使用 deterministic logic**。

### AI Boundary

LLM 主要负责：

- natural-language understanding
- orchestration
- explanation
- recommendation presentation

**不得**让 LLM 替代可确定性实现的业务计算。

### HITL

AI **可以**生成：

- Procurement Recommendation
- Procurement Request Draft

AI **不可以**：

- Approve
- Formal Submit
- Create Purchase Order
- Override Approval

**最终采购决策属于 Human。**

### Integration

当前 POC Integration baseline：

- **Controlled Export / Snapshot**
- Source-system write：**`DENIED`**
- Production write-back：**`OUT OF SCOPE`**

### Simulation Boundary

> **Fake the enterprise environment, not the product behavior.**

**模拟：**

- enterprise data
- ERP / WMS / PLM logical environment
- enterprise integration interface

**真实实现：**

- application behavior
- deterministic business logic
- Tool orchestration
- HITL
- permissions
- tests / evals
- audit behavior

---

## 1. Design Goals & Scope

> 本节待设计。以下为占位说明，**不重新定义 P0 / P1**。

### P0 设计目标

`DESIGN PENDING`

> P0 范围以 `FROZEN` Discovery Brief §11 为准（缺料分析 → 采购建议 → HITL）。本节**不重新定义 P0 / P1**，只登记待设计的设计目标。

### POC 成功边界

`DESIGN PENDING`

> 成功标准以 `FROZEN` Discovery Brief §16 为准；失败条件以 §17 为准。

### In Scope

`DESIGN PENDING`

### Out of Scope

`DESIGN PENDING`

> P1 能力（RAG、高级供应商比较、自然语言供应链查询、自动报告）以 `FROZEN` Discovery Brief §12 为准。

---

## 2. P0 Business Rules

> 本节各项均对应 `FROZEN` Discovery Validation v0.1 中的 Open Design Backlog。
>
> **当前状态**：`§2.1` ～ `§2.7` **全部 business-rule sections** 现已 `DESIGN RESOLVED`（均 Human-approved）：
> `§2.1` `BR-SHORTAGE-001`；`§2.2` `BR-INVENTORY-001`；`§2.3` `BR-SUBSTITUTE-001`；
> `§2.4` `BR-REQUIREMENT-001`；`§2.5` `BR-PROCUREMENT-001`；`§2.6` `BR-INBOUND-001`；
> `§2.7` `BR-SUPPLIER-RISK-001`。
>
> **本节范围内仍为 `DESIGN PENDING` 的项**：无。
>
> > **范围限定**：以上**仅**表示
> >
> > ```
> > Section 2 P0 Business Rules = DESIGN RESOLVED
> > ```
> >
> > **不表示** `POC Design v0.2` **整体完成**。
> >
> > **已可声明：**
> >
> > ```
> > Discovery-carried Design Backlog = RESOLVED
> > ```
> >
> > 即所有原先从 Discovery 带入 `POC Design` 的 `VB` backlog 均已完成 Design resolution。
> >
> > **但仍存在以下未完成设计：**
> >
> > - `§4` Data & Integration Design
> > - `§6` HITL Workflow
> > - `§7` remaining Permission & Security（除 `Read / Write Boundary` 外）
> > - `§8` Audit & Observability
> > - `§9` Test & AI Eval
> > - `§10` Architecture Decisions

### 2.1 Shortage Definition

**Rule ID:** `BR-SHORTAGE-001`

**Backlog:** `VB-14`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

#### 2.1.1 Business Definition

**「缺料」不是判断当前账面库存是否小于需求。**

缺料判断必须基于：

```
某 Plant
+ 某 Material
+ 某 Required Date
```

**截至该需求日期的累计可用供给，是否能够覆盖累计物料需求。**

**Calculation Grain：**

```
plant_id
+ material_code
+ required_date
```

**默认：不得跨 Plant 自动共享或借用库存。**

> Warehouse 在同一 Plant 内**是否以及如何汇总**，属于 `VB-15`，**本 Task 不定义**。

#### 2.1.2 Deterministic Rule

概念公式：

```
ProjectedAvailable(t)
  = OpeningUsableInventory
  + CumulativeEffectiveInbound(<= t)
  + CumulativeApprovedSubstituteSupply(<= t)
  - CumulativeGrossRequirement(<= t)
```

其中 `t = required_date`。

该公式**必须**按照：

```
plant_id
→ material_code
→ required_date ascending
```

进行**累计**计算。

**不得对每个需求日期独立重复使用同一份库存。**

#### 2.1.3 Dependency Boundary

以下输入的**含义**由本规则引用，但其**具体计算方式不在本 Task 定义**：

| 输入 | 归属 | 状态 |
| --- | --- | --- |
| `OpeningUsableInventory` | **`BR-INVENTORY-001` / §2.2** | **`DESIGN RESOLVED`** |
| `SafetyStock` | **`BR-INVENTORY-001` / §2.2** | **`DESIGN RESOLVED`** |
| `CumulativeEffectiveInbound` | **`BR-INBOUND-001` / §2.6** | **`DESIGN RESOLVED`** |
| `CumulativeApprovedSubstituteSupply` | **`BR-SUBSTITUTE-001` / §2.3** | **`DESIGN RESOLVED`** |
| `CumulativeGrossRequirement` | **`BR-REQUIREMENT-001` / §2.4** | **`DESIGN RESOLVED`** |

因此：

> `BR-SHORTAGE-001` 的 **Shortage Classification 设计可以 `DESIGN RESOLVED`**，且其**五项核心依赖现已全部解决**：
>
> - `OpeningUsableInventory`、`SafetyStock` ← **`BR-INVENTORY-001`**
> - `CumulativeEffectiveInbound` ← **`BR-INBOUND-001`**
> - `CumulativeApprovedSubstituteSupply` ← **`BR-SUBSTITUTE-001`**
> - `CumulativeGrossRequirement` ← **`BR-REQUIREMENT-001`**
>
> 因此可以声明：
>
> > **Shortage Engine core dependency chain = `DESIGN COMPLETE`**
>
> 但**必须明确**：`DESIGN COMPLETE` **≠** `IMPLEMENTED` **≠** `TESTED` **≠** production-ready。
>
> **仍不得声称**：`IMPLEMENTED`、`TESTED`、或**可运行**。

#### 2.1.4 Classification States

定义四个**确定性**状态：

**A. `NORMAL`**

- **条件：** `ProjectedAvailable >= SafetyStock`
- **含义：** 供给覆盖需求，且并未跌破 Safety Stock。

**B. `BUFFER_BREACH`**

- **条件：** `0 <= ProjectedAvailable < SafetyStock`
- **含义：** 当前仍能满足需求，但 Safety Stock buffer 已被侵蚀。

> **注意：`BUFFER_BREACH` 不是 `SHORTAGE`。**

**C. `SHORTAGE`**

- **条件：** `ProjectedAvailable < 0`
- **含义：** 截至该 Required Date，累计可用供给已经不足以覆盖累计需求。

**D. `DATA_INCOMPLETE`**

当完成分类所必需的**关键输入无法可靠取得**时：

**不得**返回 `NORMAL` / `BUFFER_BREACH` / `SHORTAGE`，而返回 **`DATA_INCOMPLETE`**。

该状态表示：**计算无法可靠完成** —— **不是业务风险等级**。

#### 2.1.5 Quantity Definitions

```
ShortageQty = max(0, -ProjectedAvailable)
```

```
BufferGap   = max(0, SafetyStock - ProjectedAvailable)
```

> **注意**：当 `ProjectedAvailable >= 0` 但 `ProjectedAvailable < SafetyStock` 时，则 `ShortageQty = 0`。
>
> 即：**Safety Stock breach 不得被错误解释为实际生产缺料。**

#### 2.1.6 Time-based Results

```
FirstShortageDate
  = 按 required_date ascending，最早满足 ProjectedAvailable < 0 的日期
```

```
FirstBufferBreachDate
  = 按 required_date ascending，最早满足 ProjectedAvailable < SafetyStock 的日期
```

如果从未满足对应条件：`result = null / not present`。

> 具体代码表现形式留待 **implementation**。

#### 2.1.7 `DATA_INCOMPLETE` Principle

至少记录以下原则：

如果关键输入存在无法解析的情况，例如：

- material mapping missing
- BOM unresolved
- required_date missing
- inventory snapshot unusable
- dependent calculation cannot provide reliable value

则：**不得由 LLM 或 deterministic engine 自行猜测或补值。**

**必须返回 `DATA_INCOMPLETE`。**

> **注意**：本 Task **不定义**完整 Data Quality error taxonomy，只定义该 **classification safety rule**。

#### 2.1.8 Decision Table

| Condition | Classification |
| --- | --- |
| Required critical data unavailable | `DATA_INCOMPLETE` |
| `ProjectedAvailable < 0` | `SHORTAGE` |
| `0 <= ProjectedAvailable < SafetyStock` | `BUFFER_BREACH` |
| `ProjectedAvailable >= SafetyStock` | `NORMAL` |

**优先级：`DATA_INCOMPLETE` 优先于所有业务分类。**

#### 2.1.9 Acceptance Examples

以下为 **deterministic examples**。

**Example A — `NORMAL`**

| 输入 | 值 |
| --- | --- |
| Usable Inventory | 100 |
| Effective Inbound | 50 |
| Gross Requirement | 100 |
| Safety Stock | 30 |

`ProjectedAvailable = 100 + 50 - 100 = 50`

**Expected：** `NORMAL`，`ShortageQty = 0`，`BufferGap = 0`

**Example B — `BUFFER_BREACH`**

| 输入 | 值 |
| --- | --- |
| Usable Inventory | 100 |
| Effective Inbound | 40 |
| Gross Requirement | 120 |
| Safety Stock | 30 |

`ProjectedAvailable = 100 + 40 - 120 = 20`

**Expected：** `BUFFER_BREACH`，`ShortageQty = 0`，`BufferGap = 10`

**Example C — `SHORTAGE`**

| 输入 | 值 |
| --- | --- |
| Usable Inventory | 100 |
| Effective Inbound | 40 |
| Gross Requirement | 160 |
| Safety Stock | 30 |

`ProjectedAvailable = 100 + 40 - 160 = -20`

**Expected：** `SHORTAGE`，`ShortageQty = 20`

**Example D — Cumulative calculation**

| 输入 | 值 |
| --- | --- |
| Opening Inventory | 100 |
| Effective Inbound | 0 |
| Safety Stock | 0 |

`2026-10-10`：Demand = 80 → Cumulative `ProjectedAvailable = 100 - 80 = 20`

**Expected：** `NORMAL`

`2026-10-15`：Additional Demand = 60 → Cumulative Demand = 140 → `ProjectedAvailable = 100 - 140 = -40`

**Expected：** `SHORTAGE`

**`FirstShortageDate`：`2026-10-15`**

> **必须明确：不得错误计算为 `100 >= 80` 与 `100 >= 60`** —— 因为这样会**重复使用同一份库存**。

**Example E — `DATA_INCOMPLETE`**

场景：Material mapping cannot be resolved.

**Expected：** `DATA_INCOMPLETE`

**不得输出** `NORMAL` / `BUFFER_BREACH` / `SHORTAGE`。

#### 2.1.10 AI Boundary

**Shortage Classification 必须由 deterministic logic 产生。**

正确链路：

```
Structured Data
↓
Deterministic Shortage Engine
↓
Classification + Quantities + Evidence
↓
LLM
↓
Explanation
```

LLM **可以**：

- 解释为什么缺料
- 解释缺多少
- 解释什么时候开始缺
- 总结主要 Supply / Demand evidence

LLM **不可以**：

- 自己决定是否 `SHORTAGE`
- 自己修改 `ProjectedAvailable`
- 猜测缺失数据
- 自己产生 `SafetyStock`
- 自己产生 `Effective Inbound`

#### 2.1.11 Risk Boundary

**`BR-SHORTAGE-001` 只定义 Shortage Classification。**

**不得在本规则定义**：`HIGH RISK`、`MEDIUM RISK`、`LOW RISK`、Supplier Risk Score、Risk Severity。

这些属于 **`VB-27`（Supplier Risk / Risk Evidence）**。

因此：

- **`SHORTAGE` ≠ `HIGH RISK`**
- **`BUFFER_BREACH` ≠ `MEDIUM RISK`**

**不得建立未经批准的映射。**

> 关联的 FROZEN 原问题：「缺料」在业务上如何定义？（依据 `K-BR-1`；关联 `G-07`）

### 2.2 Available Inventory / Safety Stock

**Rule ID:** `BR-INVENTORY-001`

**Backlog:** `VB-15`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

#### 2.2.1 Calculation Grain

`OpeningUsableInventory` 的计算粒度：

```
plant_id
+ material_code
+ inventory_snapshot_time
```

**默认：不得跨 Plant 自动共享库存。**

> 跨 Plant transfer / rebalancing **不属于本规则自动能力**。
>
> 如果未来需要，必须作为**独立 Supply Event / Design Rule** 处理。

#### 2.2.2 OpeningUsableInventory

定义：

```
OpeningUsableInventory
  = 同一 Plant 内
    所有符合 POC Inventory Scope
    且状态允许使用的 On-hand Inventory 之和
```

概念公式：

```
OpeningUsableInventory = Σ EligibleOnHandQty
```

其中：`EligibleOnHandQty` **只来自允许的 Inventory Status**。

> **不得直接使用 `Book Inventory Total` 作为 `OpeningUsableInventory`。**

#### 2.2.3 Inventory Status Eligibility

当前 POC 采用**保守规则**。

**A. `AVAILABLE`**

- **Eligibility:** **100%**
- **处理：** 计入 `OpeningUsableInventory`。

**B. `INSPECTION`**

- **Eligibility:** **0%**
- **处理：** **不计入** `OpeningUsableInventory`。
- **原因：** 尚未完成质量放行，POC **不提前假定**其可用于生产。

**C. `FROZEN`**

- **Eligibility:** **0%**
- **处理：** **不计入** `OpeningUsableInventory`。
- **原因：** 冻结库存当前**不可用于缺料覆盖**。

**D. Unknown / Invalid Status**

**不得猜测其可用性。**

结果：`DATA_INCOMPLETE` 或明确的 **Data Quality Issue**。

**不得静默归类为 `AVAILABLE`。**

#### 2.2.4 Warehouse Aggregation

同一个 Plant 内：**只聚合被纳入 POC Inventory Scope 的 Warehouse。**

例如 `Plant-A`：

| Warehouse | 状态 | 数量 |
| --- | --- | --- |
| Warehouse-01 | `AVAILABLE` | 100 |
| Warehouse-02 | `AVAILABLE` | 30 |
| Warehouse-QA | `INSPECTION` | 40 |
| Warehouse-FR | `FROZEN` | 20 |

则：

- **Book Inventory = 190**
- **`OpeningUsableInventory` = 130**
- **Excluded Inventory = 60**

**注意：**

- 当前规则**不因为 Warehouse 不同就禁止同 Plant 聚合**。
- 但：Warehouse **必须属于同一 Plant**，且位于**当前 POC Inventory Scope** 中。
- **不同 Plant 的库存：不得自动聚合。**

#### 2.2.5 Safety Stock Baseline

当前 POC 采用：**Configured Safety Stock**

粒度：

```
plant_id
+ material_code
```

定义：

```
SafetyStock = 由业务配置提供的非负数量
```

**当前不设计**：

- statistical safety stock
- service-level calculation
- demand variability model
- lead-time variability model
- dynamic safety stock
- AI-generated safety stock

> 这些**均不属于本 Task**。

#### 2.2.6 Zero vs Missing

**必须严格区分：`SafetyStock = 0` 与 `SafetyStock = missing`。**

**`SafetyStock = 0`**

表示业务**明确配置**为：无 Safety Stock buffer。

**这是合法值。**

**`SafetyStock = missing`**

表示**必要配置缺失**。

**不得默认成 0。**

应导致：**`DATA_INCOMPLETE`**。

**不得让 LLM 或 Rule Engine 猜测默认值。**

#### 2.2.7 Safety Stock Must Not Be Double-counted

**明确禁止：**

```
OpeningUsableInventory = Inventory - SafetyStock      ← 禁止
```

因为 `BR-SHORTAGE-001` 已经使用 `SafetyStock` 作为 **Classification Threshold**：

```
ProjectedAvailable >= SafetyStock        → NORMAL
0 <= ProjectedAvailable < SafetyStock    → BUFFER_BREACH
ProjectedAvailable < 0                   → SHORTAGE
```

因此**正确关系**：

```
Inventory
↓
OpeningUsableInventory
↓
ProjectedAvailable
↓
compare with SafetyStock
```

**`SafetyStock` 是 Classification Threshold，不是 Opening Inventory 的预先扣减项。**

> 否则会导致 **Safety Stock double counting**。

#### 2.2.8 Negative Inventory

当前 POC 对 `on_hand_qty < 0` 采用**保守规则**。

**不得自动** `clamp to 0`。

**不得自行解释成**正常可用库存。

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**。

**原因**：负库存可能来源于：

- posting delay
- inventory discrepancy
- data quality issue
- unresolved business condition

> 其具体业务含义**不在本 Task 定义**。

#### 2.2.9 Data Quality Safety Rule

如果以下关键数据**无法可靠取得**：

- `material_code` unresolved
- `plant_id` unresolved
- warehouse ownership unresolved
- `inventory_status` missing / invalid
- `on_hand_qty` invalid
- `inventory_snapshot_time` missing
- `SafetyStock` missing

则：**不得产生正常业务分类输入。**

输出应进入：**`DATA_INCOMPLETE`**。

> **注意**：本 Task **不设计**完整 Data Quality taxonomy，只定义**库存输入的 fail-safe behavior**。

#### 2.2.10 Acceptance Examples

以下为 **deterministic examples**。

**Example A — Eligible warehouses**

`Plant-A` / `MAT-001`：

| Warehouse | 状态 | 数量 |
| --- | --- | --- |
| Warehouse-01 | `AVAILABLE` | 100 |
| Warehouse-02 | `AVAILABLE` | 30 |
| Warehouse-QA | `INSPECTION` | 40 |
| Warehouse-FR | `FROZEN` | 20 |

**Expected：**

- **Book Inventory = 190**
- **`OpeningUsableInventory` = 130**

**Example B — `BUFFER_BREACH` interaction**

| 输入 | 值 |
| --- | --- |
| `OpeningUsableInventory` | 130 |
| Effective Inbound | 0 |
| Gross Requirement | 105 |
| `SafetyStock` | 30 |

`ProjectedAvailable = 130 + 0 - 105 = 25`

**Expected：** `BUFFER_BREACH`，`ShortageQty = 0`，`BufferGap = 5`

**Example C — `SafetyStock = 0`**

`OpeningUsableInventory = 100`，`SafetyStock = 0`

该配置**合法**。

**不得解释为 missing。**

**Example D — `SafetyStock` missing**

`SafetyStock = missing`

**Expected：** `DATA_INCOMPLETE`

**不得默认成 0。**

**Example E — Negative Inventory**

`Warehouse-01`：`AVAILABLE = -5`

**Expected：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得自动变成 0。**

**Example F — Cross Plant**

| Plant | `AVAILABLE` |
| --- | --- |
| `Plant-A` | 20 |
| `Plant-B` | 100 |

计算 `Plant-A` 时：**`OpeningUsableInventory` = 20**

**不得自动得到 120。**

#### 2.2.11 AI Boundary

**库存可用性判断必须由 deterministic rules 决定。**

LLM **不可以**：

- 将 `INSPECTION` 猜成 `AVAILABLE`
- 将 `FROZEN` 库存释放
- 将 missing `SafetyStock` 默认成 0
- 将负库存改成 0
- 跨 Plant 自动借库存
- 猜测 Warehouse 所属 Plant

LLM **可以**解释：

- 为什么某库存未被计入
- 哪些 Warehouse 被排除
- 为什么返回 `DATA_INCOMPLETE`

> 关联的 FROZEN 原问题：安全库存如何计算？（关联 `G-04`）

### 2.3 Substitute Material

**Rule ID:** `BR-SUBSTITUTE-001`

**Backlog:** `VB-16`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

> 关联的 FROZEN 原问题：替代料如何处理？（关联 `G-05`）

#### 2.3.1 Business Definition

本规则回答：

> 某 Target Material 在某个 `required_date` 之前，可以从**已批准的替代关系**获得多少**等效供给**。

**Core Principle — 替代料不得由 AI 自行推断。**

只有**同时满足**以下**全部**条件的替代供给，才可以进入：

```
CumulativeApprovedSubstituteSupply
```

1. **明确存在 Substitute Relationship**（来自受控数据源中**已登记**的关系）；
2. 该 relationship **已 `APPROVED`**；
3. `source`（Substitute Material）与 `target`（Target Material）**可可靠映射**；
4. **同一 Plant**；
5. `source` inventory 符合 **`BR-INVENTORY-001`** 的 eligible inventory rule（`AVAILABLE`）；
6. **存在明确 allocation**。

上述任一条件不满足，或无法可靠判断，该替代供给**不得计入**。

如果因此无法可靠完成计算：**`DATA_INCOMPLETE`**（见 §2.3.11）。

#### 2.3.2 Calculation Grain

`CumulativeApprovedSubstituteSupply` 按以下粒度计算，与 **`BR-SHORTAGE-001`** 对齐：

```
plant_id
+ target_material_code
+ required_date
```

**不得跨 Plant 合并或借用**替代供给。

#### 2.3.3 Directional Relationship

**替代关系必须是有方向的。**

```
Target Material A
  ← can be covered by
Substitute Material B
```

即：**A 可被 B 替代。**

**不代表：B 可以被 A 替代。**

**不得自动建立双向关系。**

**不得**根据以下任何依据**创建**替代关系：

- name similarity
- description similarity
- LLM reasoning
- embedding similarity

替代关系**只能**来自受控数据源中**已登记**的 Substitute Relationship。

> 本 Task **不设计**该关系的维护 / 录入流程。

#### 2.3.4 Minimum Relationship Attributes

一个 Substitute Relationship 概念上至少需要：

| Attribute | 含义 |
| --- | --- |
| `plant_id` | 该替代关系适用的 Plant |
| `target_material_code` | 被覆盖的 Target Material |
| `substitute_material_code` | 提供覆盖的 Substitute Material |
| `substitution_ratio` | 换算率（见 §2.3.6） |
| `approval_status` | 审批状态（见 §2.3.5） |

这些是 **canonical business attributes**。

**本 Task 不定义**：

- database schema
- ERP field mapping
- API contract

#### 2.3.5 Approval Requirement

**只有**：

```
approval_status = APPROVED
```

的关系**可以参与** shortage calculation。

其他状态，例如：

- `PENDING`
- `REJECTED`
- `UNKNOWN`

**不得进入** Approved Substitute Supply。

如果 `approval_status` **缺失**或**无法可靠判断**：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得由 LLM 自动批准。**

> 本 Task **不定义** approval workflow（由谁批准、通过什么流程批准、如何记录审批人）。

#### 2.3.6 `substitution_ratio` Canonical Semantic

`substitution_ratio` 表示：

> **1 unit Substitute Material 可以覆盖多少 unit Target Material Requirement。**

例如：

```
substitution_ratio = 1.0
```

表示：

```
1 B
  → equivalent to 1 A
```

```
substitution_ratio = 0.5
```

表示：

```
1 B
  → equivalent to 0.5 A
```

定义：

```
EquivalentTargetQty
  = AllocatedSubstituteQty × substitution_ratio
```

**要求：**

```
substitution_ratio > 0
```

**注意语义方向**：这是 **substitute → target** 的换算率，**不是** target → substitute。

如果 `substitution_ratio` **missing** 或 **invalid**（包含 `<= 0`）：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得猜测。**

**不得**：

- `clamp`
- **默认成 `1.0`**
- 自动改成其他数值
- 让 LLM 修正

#### 2.3.7 Explicit Allocation

**不得**将 Substitute Material 的**全部库存**自动视为 Target Material 的供给。

**必须存在明确 allocation：**

```
AllocatedSubstituteQty
```

例如：

```
MAT-B AVAILABLE = 100

Human-approved allocation:
  60 MAT-B
    → MAT-A
```

则：

```
AllocatedSubstituteQty = 60
```

**而不是** `100`。

**要求：**

```
AllocatedSubstituteQty >= 0
```

`AllocatedSubstituteQty = 0` 是**合法值**，表示该替代关系在本需求窗口内**未分配**任何数量。

但 `AllocatedSubstituteQty` **missing** 或 **invalid** 表示必要 allocation 信息**缺失**：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得默认成 0。**

> 本 Task **不定义** allocation 的产生方式（人工配置 / 计划系统 / 算法），只要求 allocation **可追溯**。

#### 2.3.8 Eligible Source Supply

当前 POC 第一版**只允许**使用：

```
同一 Plant
+ BR-INVENTORY-001 判定为 AVAILABLE 的 Substitute Inventory
```

参与 allocation。

**不得自动使用**：

- `INSPECTION`
- `FROZEN`
- Future Substitute Inbound
- Cross-Plant Inventory

这些如未来需要，**必须通过后续独立 Design Change 引入**。

> 关于 `AVAILABLE` / `INSPECTION` / `FROZEN` 的判定口径，见 **`BR-INVENTORY-001` / §2.2**，本规则**不重新定义**。

#### 2.3.9 Same Plant Boundary

Target Material 与 Substitute Supply **默认必须属于同一 `plant_id`**。

例如：

```
Target               = Plant-A / MAT-A
Substitute Inventory = Plant-B / MAT-B
```

**不得直接计入。**

跨 Plant **必须先形成独立的**：

```
transfer / supply event
```

**本 Task 不设计该机制。**

如果 Plant 映射无法可靠判断：`DATA_INCOMPLETE` ＋ **Data Quality Issue**。

#### 2.3.10 No Double Allocation

**同一份 Substitute Supply 不得被重复分配。**

必须满足：

```
Σ AllocatedSubstituteQty
  <= EligibleSubstituteSupply
```

例如：

```
MAT-B AVAILABLE = 100

  60 → MAT-A
  40 → unallocated
```

则**已分配的 60 不得同时**：

- 分配给其他 Target（例如 `MAT-C`）；
- 作为**未分配** Substitute Supply；
- 被多个 shortage **同时重复消费**；
- 继续作为 `MAT-B` **自身可自由使用的完整** Available Supply。

如果约束被违反（例如 `60 → MAT-A` 且 `50 → MAT-C`，合计 `110 > 100`）：

**处理：** `DATA_INCOMPLETE` ＋ **Allocation Conflict**

**不得 silently over-allocate。**

**Supply Conservation / Reservation Constraint**

一旦 `AllocatedSubstituteQty` 被分配给某 Target Material，该数量**必须**从 Source Material 在**相同有效需求窗口**内仍可自由使用的 **Eligible Supply Pool** 中**保留 / 扣除**。

因此，**已分配数量不得同时**：

- 分配给其他 Target；
- 作为**未分配** Substitute Supply；
- 被多个 shortage **重复消费**；
- 继续作为 Source Material 自身**可自由使用的完整** Available Supply。

定义：

```
RemainingUnallocatedSourceSupply
  = EligibleSubstituteSupply
  - Σ AllocatedSubstituteQty
```

要求：

```
RemainingUnallocatedSourceSupply >= 0
```

> 这**只是 supply-conservation invariant**，**不是**新的 optimization / allocation algorithm。

**与 `BR-INVENTORY-001` 的关系**

`BR-INVENTORY-001` 定义的是**原始 eligible inventory baseline**（见 §2.2）。

本规则**不修改** `BR-INVENTORY-001` 的原始定义。

但当某部分 `AVAILABLE` inventory **已形成有效 Substitute Allocation** 时，后续 shortage evaluation **不得**继续把该**已分配数量**视为 Source Material 的 **uncommitted supply**。

本节只建立 **`BR-SUBSTITUTE-001` 的 allocation reservation constraint**，**不重新定义** `BR-INVENTORY-001`。

**时间边界（Demand Window）**

该 reservation **只作用于 allocation 有效的 demand window**。

由于本 Task **不设计复杂 allocation timing engine**：

如果**无法可靠判断** allocation 与 Source Material **自身需求窗口是否重叠**：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得同时把 supply 计入两边。**

> 本 Task **只定义约束**。**不得设计**：
>
> - optimization algorithm
> - allocation priority
> - shortage prioritization
> - auto scheduling

#### 2.3.11 Zero vs Missing

必须区分两种**语义完全不同**的情况：

**A. 没有批准的 Substitute Relationship**

如果业务**明确**：Target Material **没有** Approved Substitute

则：

```
ApprovedSubstituteSupply = 0
```

这是**合法状态**，**不得**返回 `DATA_INCOMPLETE`。

**B. Substitute data 无法可靠取得**

如果**存在**替代关系，但出现以下任一情况：

- `substitution_ratio` missing / invalid
- `approval_status` unknown
- allocation qty invalid
- source material unresolved
- target material unresolved
- plant mapping unresolved

则：

**`DATA_INCOMPLETE`**

**不得默认成 0。**

#### 2.3.12 Deterministic Formula

对于**每一个有效 allocation** `i`：

```
EquivalentTargetQty(i)
  = AllocatedSubstituteQty(i) × substitution_ratio(i)
```

随后：

```
CumulativeApprovedSubstituteSupply(<= t)
  = Σ EquivalentTargetQty(i)
```

**仅包含**同时满足以下条件的 allocation：

- approved relationship
- same Plant
- eligible `AVAILABLE` source inventory
- explicit allocation
- allocation 对当前 `required_date` **有效**

**本 Task 不设计复杂 allocation timing engine。**

如果 allocation **无法可靠关联**当前需求窗口：

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

> allocation 与需求窗口的关联机制属 **canonical business meaning 之后的 source mapping**，进入后续 **Data Dictionary / Adapter Design**。

#### 2.3.13 Acceptance Examples

以下为 **deterministic examples**。

**Example A — 1:1 substitute**

| 字段 | 值 |
| --- | --- |
| MAT-B AVAILABLE | 100 |
| Approved allocation to MAT-A | 60 |
| `substitution_ratio` | 1.0 |

**Expected：**

- `EquivalentTargetQty = 60`

**Example B — Conversion ratio**

| 字段 | 值 |
| --- | --- |
| `AllocatedSubstituteQty` | 60 |
| `substitution_ratio` | 0.8 |

**Expected：**

- `EquivalentTargetQty = 48`

**Example C — Relationship not approved**

| 字段 | 值 |
| --- | --- |
| `approval_status` | `PENDING` |

**Expected：**

- **不得计入** Approved Substitute Supply

**Example D — Cross Plant**

| 字段 | 值 |
| --- | --- |
| Target | Plant-A / MAT-A |
| Substitute | Plant-B / MAT-B |

**Expected：**

- **不得直接计入**

**Example E — No substitute exists**

业务**明确**无 Approved Substitute。

**Expected：**

- `ApprovedSubstituteSupply = 0`
- **不得**返回 `DATA_INCOMPLETE`

**Example F — Missing ratio**

Approved relationship exists，但 `substitution_ratio` **missing**。

**Expected：**

- `DATA_INCOMPLETE`

**Example G — No double allocation**

| 字段 | 值 |
| --- | --- |
| Eligible MAT-B | 100 |
| Allocation | 60 → MAT-A；50 → MAT-C |

**Expected：**

- **`INVALID`**

因为：

```
110 > 100
```

必须：

- `DATA_INCOMPLETE`
- ＋ **Allocation Conflict**

**不得 silently over-allocate。**

**Example H — Source supply conservation**

| 字段 | 值 |
| --- | --- |
| MAT-B AVAILABLE | 100 |
| Allocation | 60 MAT-B → MAT-A |
| `substitution_ratio` | 1.0 |

**Expected：**

- `MAT-A ApprovedSubstituteSupply = 60`
- `RemainingUnallocatedSourceSupply(MAT-B) = 40`

对于**同一有效需求窗口**：

- `MAT-B` **不得继续按 `100` 作为完全未承诺 supply 使用**。

如果**无法可靠判断** allocation 与 `MAT-B` **自身需求窗口是否重叠**：

- `DATA_INCOMPLETE`

#### 2.3.14 AI Boundary

**Alternative supply eligibility、allocation 与 quantity 必须由 deterministic logic 决定。**

LLM **不可以**：

- 创建 substitute relationship
- 批准 substitute relationship
- 猜 `substitution_ratio`
- 自行决定 allocation qty
- 跨 Plant 自动调货
- 自动决定 shortage priority
- 重复使用同一 supply

LLM **可以**解释：

- 哪个 Substitute 被批准
- 分配了多少
- conversion 后等效多少
- 为什么某替代料未被计入
- 为什么出现 `DATA_INCOMPLETE`

#### 2.3.15 Source-field Boundary

**本规则定义 business semantic，而不是 source schema。**

因此**不得创建**：

- ERP field mapping
- API Contract
- database column definition
- adapter implementation
- allocation engine
- optimization engine

例如 `substitution_ratio`、`approval_status`、`AllocatedSubstituteQty` **只是 canonical business meaning**。

其 **source mapping** 进入后续 **Data Dictionary / Adapter Design**。

### 2.4 Scrap / Loss

**Rule ID:** `BR-REQUIREMENT-001`

**Backlog:** `VB-17`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

#### 2.4.1 Business Definition

本规则回答：

> 在某个 Production Requirement 下，某 Material 为满足生产**所需要准备的 Gross Material Requirement 是多少**。

原则：

先依据：

```
Production Requirement
× BOM Component Quantity
```

计算**净物料需求**，再依据**明确配置的 `loss_rate`** 放大为 **Gross Requirement**。

**不得让 LLM 自行估算需求或损耗率。**

#### 2.4.2 Calculation Grain

计算**至少对齐**：

```
plant_id
+ material_code
+ required_date
```

并能够**追溯到**：

```
Production Requirement
+ BOM relationship
```

**不得跨 Plant 合并需求。**

#### 2.4.3 BaseRequirement

定义：

```
BaseRequirement = ProductionQty × BOMComponentQty
```

其中：

```
ProductionQty    >= 0
BOMComponentQty  >= 0
```

**示例：**

```
ProductionQty   = 100
BOMComponentQty = 2
→ BaseRequirement = 200
```

**注意**：本规则**只使用已经可靠解析的 BOM input**。

**不得在本 Task 设计**：

- BOM version selection
- BOM validity selection
- BOM explosion algorithm
- ERP source-field mapping

如果**无法可靠确定适用 BOM**：**`DATA_INCOMPLETE`**。

#### 2.4.4 `loss_rate` Canonical Semantic

正式定义 POC 中 `loss_rate` 表示：

> **预计投入总量中会发生损耗的比例。**

因此：

```
loss_rate = 0.05
```

表示：**预计投入量的 5% 会损耗**。

**这是 POC 的 canonical business semantic。**

**不得将其混淆为**"在净需求上额外加 5%"。

如果未来真实系统中的字段语义是 `markup`、`allowance`、`scrap add-on` 或其他定义，**必须**在后续 **Data Mapping / Adapter 层**转换为本规则的 canonical semantic。

**不得偷偷改变本公式。**

#### 2.4.5 GrossRequirement Formula

定义：

```
GrossRequirement = BaseRequirement / (1 - loss_rate)
```

前提：

```
0 <= loss_rate < 1
```

**示例：**

```
BaseRequirement = 200
loss_rate       = 0.05
→ GrossRequirement = 200 / 0.95 = 210.526315...
```

#### 2.4.6 `loss_rate` Validation

**合法范围：**

```
0 <= loss_rate < 1
```

**合法示例：** `0`、`0.03`、`0.15`

**非法示例：** `-0.05`、`1.0`、`1.2`

**非法值处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得**：

- `clamp`
- 自动改为 0
- 自动改成最大值
- 让 LLM 修正

#### 2.4.7 Zero vs Missing

**必须严格区分：`loss_rate = 0` 与 `loss_rate = missing`。**

**`loss_rate = 0`**

表示：业务**明确配置为无损耗**。

**这是合法值。**

**`loss_rate = missing`**

表示：**必要业务配置缺失**。

**处理：** `DATA_INCOMPLETE`

**不得默认成 0。**

**不得让 LLM 或 Rule Engine 猜测。**

#### 2.4.8 Quantity Precision Boundary

本规则产生 **canonical `GrossRequirement` quantity**。

**本 Task 不定义**：

- `ceil`
- `floor`
- `round`
- integer packaging rule
- UOM-specific precision
- pack size rounding

例如：

```
GrossRequirement = 210.526315...
```

本规则**保持该 canonical quantity**。

**不得本轮自行变成 `210` 或 `211`。**

> 具体 quantity precision / rounding 由**后续明确 Design Rule** 决定。

#### 2.4.9 CumulativeGrossRequirement

对同一 `plant_id` + `material_code`，按 `required_date ascending` 累计：

```
CumulativeGrossRequirement(<= t) = Σ GrossRequirement   where required_date <= t
```

**示例：**

```
2026-10-10  GrossRequirement = 100
2026-10-15  GrossRequirement = 70
```

则：

```
CumulativeGrossRequirement(<= 2026-10-10) = 100
CumulativeGrossRequirement(<= 2026-10-15) = 170
```

**不得把每个日期当成彼此独立需求。**

#### 2.4.10 Substitute Boundary

本规则**只负责原目标 Material 的需求侧计算**。

**不得**因为存在 Substitute Material 而降低 `BaseRequirement` 或 `GrossRequirement`。

替代料属于**供给侧** `CumulativeApprovedSubstituteSupply`，由 **`BR-SUBSTITUTE-001` / §2.3**（`VB-16`）单独设计。

因此必须保持 **`GrossRequirement` 与 `Substitute Supply` 两个概念分离**。

**不得 double counting。**

#### 2.4.11 Data Quality / Fail-safe

如果以下关键输入**无法可靠取得**：

- ProductionQty missing / invalid
- `ProductionQty < 0`
- BOM unresolved
- BOMComponentQty missing / invalid
- `BOMComponentQty < 0`
- `loss_rate` missing
- `loss_rate` invalid
- `plant_id` unresolved
- `material_code` unresolved
- `required_date` missing / invalid

则：**`DATA_INCOMPLETE`**

**不得**：

- 猜测 BOM
- 猜测 `loss_rate`
- 猜测 `required_date`
- 自动填默认值
- 让 LLM 补业务事实

> 本 Task **不设计**完整 Data Quality taxonomy，只定义**本规则的 fail-safe behavior**。

#### 2.4.12 Acceptance Examples

以下为 **deterministic examples**。

**Example A — No loss**

| 输入 | 值 |
| --- | --- |
| ProductionQty | 100 |
| BOMComponentQty | 2 |
| `loss_rate` | 0 |

**Expected：**

- `BaseRequirement = 200`
- `GrossRequirement = 200`

**Example B — 5% loss**

| 输入 | 值 |
| --- | --- |
| ProductionQty | 100 |
| BOMComponentQty | 2 |
| `loss_rate` | 0.05 |

**Expected：**

- `BaseRequirement = 200`
- `GrossRequirement = 200 / 0.95 = 210.526315...`

**不得自动 round / ceil。**

**Example C — Missing loss rate**

`loss_rate = missing`

**Expected：** `DATA_INCOMPLETE`

**不得默认成 0。**

**Example D — Invalid loss rate**

`loss_rate = 1.0`

**Expected：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**Example E — BOM unresolved**

`ProductionQty = 100`，BOM cannot be reliably resolved

**Expected：** `DATA_INCOMPLETE`

**不得让 LLM 猜 `BOMComponentQty`。**

**Example F — Cumulative requirement**

| required_date | GrossRequirement |
| --- | --- |
| `2026-10-10` | 100 |
| `2026-10-15` | 70 |

**Expected：**

- `CumulativeGrossRequirement(<= 2026-10-10) = 100`
- `CumulativeGrossRequirement(<= 2026-10-15) = 170`

**Example G — Substitute must not reduce requirement**

Original Material `GrossRequirement = 100`；存在 Substitute Supply = 30。

**Expected：** `GrossRequirement` 仍然 **= 100**

**不得自动改成 70。**

> Substitute Supply 的影响由 **`BR-SUBSTITUTE-001` / §2.3**（supply-side rule）单独处理。

#### 2.4.13 AI Boundary

`BaseRequirement`、`GrossRequirement`、`CumulativeGrossRequirement` **必须由 deterministic logic 产生**。

LLM **不可以**：

- 生成 `loss_rate`
- 修改 `ProductionQty`
- 修改 `BOMComponentQty`
- 猜 BOM
- 选择 BOM version
- 对 `GrossRequirement` 自行 round
- 用 Substitute Supply 修改需求端

LLM **可以**解释：

- `BaseRequirement` 如何得到
- `loss_rate` 如何影响 `GrossRequirement`
- 为什么返回 `DATA_INCOMPLETE`
- 某日期累计需求如何形成

> 关联的 FROZEN 原问题：损耗率规则？（关联 `G-03`）

### 2.5 MOQ / Purchase Recommendation Quantity

**Rule ID:** `BR-PROCUREMENT-001`

**Backlog:** `VB-18`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。

> 关联的 FROZEN 原问题：采购最小批量（MOQ）是否影响采购建议？（关联 `G-10`）

#### 2.5.1 Business Definition

本规则回答：

> 当 Shortage Engine 已确认某 Material 存在**真实 `SHORTAGE`** 时，POC 应建议采购**多少数量**。

当前 POC 采用**保守原则**：

只有：

```
Classification = SHORTAGE
```

才生成 **numeric Purchase Recommendation**。

以下状态当前 POC **不自动生成采购数量建议**：

- `NORMAL`
- `BUFFER_BREACH`

其中 `BUFFER_BREACH` **只是 Safety Stock buffer 被侵蚀**，**并不等同于实际缺料**。

**不得为了恢复 Safety Stock 自动创建采购需求。**

#### 2.5.2 Recommendation Trigger

必须先由 **`BR-SHORTAGE-001`** 产生：

```
Classification = SHORTAGE
```

以及：

```
ShortageQty > 0
```

才进入本规则。

| Classification | 本规则行为 |
| --- | --- |
| `NORMAL` | **No Purchase Recommendation** |
| `BUFFER_BREACH` | **No Purchase Recommendation**（当前 POC 不自动执行 buffer replenishment） |
| `SHORTAGE` | Quantity Rule applicable |
| `DATA_INCOMPLETE` | **No Numeric Recommendation** |

对于 `DATA_INCOMPLETE`：**不得由 LLM 猜测采购数量。**

#### 2.5.3 FirstShortageDate Boundary

当前 POC 第一版对每个：

```
plant_id
+ material_code
```

在一次 shortage analysis run 中，**只依据 `FirstShortageDate`** 形成**一条**基础采购数量建议。

定义：

```
RecommendationNeedDate
  = FirstShortageDate
```

```
BasePurchaseNeed
  = ShortageQty at FirstShortageDate
```

**原因：** 当前 POC **尚未设计**完整的 **time-phased replenishment loop**。

如果对每个未来 shortage date 分别创建采购建议，却不把先前 recommendation **重新投入未来 supply calculation**，可能产生：

```
double counting
+
duplicate recommendation
```

因此当前版本**只生成**：

```
one baseline recommendation
  per plant_id + material_code
  per analysis run
```

#### 2.5.4 BasePurchaseNeed

定义：

```
BasePurchaseNeed
  = ShortageQty at FirstShortageDate
```

其中 `ShortageQty` 已由 **`BR-SHORTAGE-001`** 定义为：

```
ShortageQty
  = max(0, -ProjectedAvailable)
```

**不得重新计算 shortage。**

**不得**将 `BufferGap` 加入 `BasePurchaseNeed`。

即：

```
BasePurchaseNeed
  ≠ ShortageQty + BufferGap
```

当前 POC 的采购建议**只覆盖实际缺口**，**不自动恢复 Safety Stock buffer**。

#### 2.5.5 ApplicableMOQ Canonical Semantic

`ApplicableMOQ` 表示：

> 针对当前采购建议所适用的**最小采购数量约束**。

这是 **canonical business input**。

当前 Task **不决定**它真实来源于：

- Supplier-Material Master
- Contract
- Purchasing Info Record
- ERP proprietary field
- 其他采购主数据

真实 **source mapping** 留给后续 **Data Dictionary ＋ Adapter Design**。

#### 2.5.6 MOQ Zero vs Missing

必须**严格区分**：

```
ApplicableMOQ = 0
```

与：

```
ApplicableMOQ = missing
```

**A. `ApplicableMOQ = 0`**

表示业务**明确确认**：当前 recommendation **不存在**最小采购数量约束。

这是**合法值**。

**B. `ApplicableMOQ = missing`**

表示对于一个**已经触发 `SHORTAGE`** 的采购建议，必要的 MOQ 信息**无法可靠取得**。

**处理：** `DATA_INCOMPLETE`

**不得**：

- 默认成 0
- 猜测 MOQ
- 使用经验值
- 让 LLM 补值

#### 2.5.7 MOQ Validation

要求：

```
ApplicableMOQ >= 0
```

如果：

```
ApplicableMOQ < 0
```

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得**：

- `clamp`
- absolute value
- 自动改为 0

#### 2.5.8 RecommendedPurchaseQty

**只有在**：

```
Classification = SHORTAGE
```

**且所有必要输入可靠时**：

定义：

```
RecommendedPurchaseQty
  = max(
      BasePurchaseNeed,
      ApplicableMOQ
    )
```

同时定义：

```
MOQAdjustmentQty
  = RecommendedPurchaseQty - BasePurchaseNeed
```

要求：

```
MOQAdjustmentQty >= 0
```

#### 2.5.9 Meaning of MOQ Adjustment

必须明确：

**`MOQAdjustmentQty` 不是 `ShortageQty`。**

例如：

```
ShortageQty     = 30
ApplicableMOQ   = 100
```

则：

```
BasePurchaseNeed       = 30
RecommendedPurchaseQty = 100
MOQAdjustmentQty       = 70
```

其中：

- `30` = **实际计算缺口**
- `70` = **为满足 MOQ 而额外增加的采购数量**

**不得**将 `100` 描述为「**实际缺料 100**」。

解释必须保持：

```
business shortage
与
commercial purchasing constraint
```

**分离**。

#### 2.5.10 MOQ Does Not Mean Order Multiple

本规则中的 MOQ **只表示**：

```
Minimum Order Quantity
```

**不得**把它扩展解释为：

- pack size
- order multiple
- carton quantity
- pallet quantity
- integer rounding
- UOM conversion

因此本 Task **不定义**：

```
ceil(qty / multiple) × multiple
```

也**不定义** `round` / `ceil` / `floor` 或任何 packaging / quantity precision rule。

这些如果未来需要，**必须作为独立 Design Rule**。

#### 2.5.11 Quantity Precision Boundary

`BasePurchaseNeed` 与 `RecommendedPurchaseQty` 当前保持 **canonical quantity**。

例如：

```
BasePurchaseNeed = 10.5
ApplicableMOQ    = 8
```

则：

```
RecommendedPurchaseQty = 10.5
```

**不得自行**：

```
ceil → 11
```

除非未来有明确的 **UOM / precision / packaging rule**。

#### 2.5.12 Lead Time Boundary

`FROZEN` P0-2 要求采购建议中包含**供应周期 / Lead Time**。

但本规则当前**只定义** Purchase Recommendation Quantity。

因此：

`Lead Time` **可以**作为 recommendation 的**解释性 / planning input**，

但本 Task **不允许**用 Lead Time **偷偷修改** `RecommendedPurchaseQty`。

本 Task **不定义**：

- Order Date
- Release Date
- Expedite Date
- Late-order policy
- Dynamic Lead Time

如果 `Need Date` 与 `Lead Time` 显示正常采购**可能已经来不及**，后续**可以**形成：

```
risk / feasibility evidence
```

但**不得**在本 Task **自行改变采购数量算法**。

#### 2.5.13 Supplier Boundary

本 Task **不进行** Supplier Selection。

**不得**因为：

```
Supplier A MOQ = 50
Supplier B MOQ = 100
```

**自行选择** Supplier A。

因此：

`ApplicableMOQ` **必须**作为**已可靠确定**的 canonical input 提供给本规则。

如果 MOQ 取值**依赖尚未确定的 Supplier**，且**无法可靠确定**：

```
ApplicableMOQ = UNKNOWN / missing
```

则：

`DATA_INCOMPLETE`

**不得**让 LLM 选择 Supplier **只是为了得到一个 MOQ**。

Supplier selection / ranking 属于**其他 Design Scope**。

#### 2.5.14 Recommendation Output Semantics

采购建议至少必须能够区分：

- Material
- Plant
- `RecommendationNeedDate`
- `BasePurchaseNeed`
- `ShortageQty`
- `ApplicableMOQ`
- `MOQAdjustmentQty`
- `RecommendedPurchaseQty`

并保留以下 **P0-2 要求所需信息**的**引用能力**：

- Current Inventory
- Effective Inbound
- Lead Time
- Risk Evidence

**注意：** 本 Task **不设计最终 API / DB Schema**，这里只定义 **canonical business meaning**。

#### 2.5.15 Human-in-the-loop Boundary

`RecommendedPurchaseQty` **只是**：

```
Recommendation
```

**不是**：

```
ApprovedPurchaseQty
```

AI / Rule Engine **可以**生成 Procurement Recommendation。

AI **可以**据此生成 Procurement Request Draft。

但最终：

- 修改数量
- 批准
- 拒绝
- 正式提交

属于 **Human / Business Workflow**。

因此：

```
RecommendedPurchaseQty
  ≠ ApprovedPurchaseQty
  ≠ PurchaseOrderQty
```

#### 2.5.16 Deterministic Examples

以下为 **deterministic examples**。

**Example A — Shortage below MOQ**

| 字段 | 值 |
| --- | --- |
| Classification | `SHORTAGE` |
| ShortageQty | 30 |
| ApplicableMOQ | 100 |

**Expected：**

- `BasePurchaseNeed = 30`
- `RecommendedPurchaseQty = 100`
- `MOQAdjustmentQty = 70`

**Example B — Shortage above MOQ**

| 字段 | 值 |
| --- | --- |
| Classification | `SHORTAGE` |
| ShortageQty | 120 |
| ApplicableMOQ | 100 |

**Expected：**

- `BasePurchaseNeed = 120`
- `RecommendedPurchaseQty = 120`
- `MOQAdjustmentQty = 0`

**Example C — Explicit no MOQ**

| 字段 | 值 |
| --- | --- |
| Classification | `SHORTAGE` |
| ShortageQty | 40 |
| ApplicableMOQ | 0 |

**Expected：**

- `RecommendedPurchaseQty = 40`
- `MOQAdjustmentQty = 0`

**Example D — Missing MOQ**

| 字段 | 值 |
| --- | --- |
| Classification | `SHORTAGE` |
| ShortageQty | 40 |
| ApplicableMOQ | missing |

**Expected：**

- `DATA_INCOMPLETE`
- **No Numeric Recommendation**
- **不得默认 MOQ = 0**

**Example E — BUFFER_BREACH**

| 字段 | 值 |
| --- | --- |
| Classification | `BUFFER_BREACH` |
| ShortageQty | 0 |
| BufferGap | 20 |
| ApplicableMOQ | 100 |

**Expected：**

- **No Purchase Recommendation**

**不得**生成 `RecommendedPurchaseQty = 100`。

**不得**为了恢复 Safety Stock **自动创建采购建议**。

**Example F — NORMAL**

| 字段 | 值 |
| --- | --- |
| Classification | `NORMAL` |

**Expected：**

- **No Purchase Recommendation**

**Example G — DATA_INCOMPLETE**

| 字段 | 值 |
| --- | --- |
| Classification | `DATA_INCOMPLETE` |

**Expected：**

- **No Numeric Recommendation**

**Example H — First shortage only**

| 字段 | 值 |
| --- | --- |
| `FirstShortageDate` | `2026-10-10` |
| ShortageQty at `2026-10-10` | 30 |
| Later projected shortage at `2026-10-20` | 80 |
| ApplicableMOQ | 50 |

**Expected for current POC：**

- `BasePurchaseNeed = 30`
- `RecommendedPurchaseQty = 50`
- `RecommendationNeedDate = 2026-10-10`

**不得**在同一次分析中自动再生成第二条 `2026-10-20` recommendation。

**原因：** 完整 **time-phased replenishment loop** 尚未设计。

#### 2.5.17 AI Boundary

**数量规则必须由 deterministic logic 决定。**

LLM **不可以**：

- 猜 `ShortageQty`
- 猜 MOQ
- 把 `BUFFER_BREACH` 当 `SHORTAGE`
- 为了满足 MOQ 自行选择 Supplier
- 自行 round quantity
- 自行创建第二个未来采购建议
- 将 `MOQAdjustmentQty` 描述成真实缺口
- 自动批准 `RecommendedPurchaseQty`

LLM **可以**解释：

- 为什么建议采购
- `ShortageQty` 是多少
- MOQ 为什么放大了数量
- `MOQAdjustmentQty` 是多少
- 为什么没有生成采购建议
- 为什么返回 `DATA_INCOMPLETE`

#### 2.5.18 Integration with Existing Rules

本规则**必须引用** `BR-SHORTAGE-001`，而**不是重新定义**：

- `ProjectedAvailable`
- `ShortageQty`
- `FirstShortageDate`
- `Classification`

输入关系：

```
BR-SHORTAGE-001
        ↓
Classification
ShortageQty
FirstShortageDate
        ↓
BR-PROCUREMENT-001
        ↓
RecommendedPurchaseQty
```

**不得修改**以下规则的业务定义：

- `BR-INVENTORY-001`
- `BR-INBOUND-001`
- `BR-SUBSTITUTE-001`
- `BR-REQUIREMENT-001`

### 2.6 Effective Inbound

**Rule ID:** `BR-INBOUND-001`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。
>
> **本规则没有独立 `VB` 编号。** 它是 `POC Design v0.2` 中已经明确登记的设计项。**不得为了方便自行创建新的 `VB` ID。**

#### 2.6.1 Business Definition

**不是所有"未收货采购订单"都可以计入 `ProjectedAvailable` 的未来 Supply。**

某笔 inbound 只有**同时满足**以下四项：

1. PO / inbound status eligible
2. 存在正数 `RemainingInboundQty`
3. `effective_arrival_date` 可可靠取得
4. `effective_arrival_date <= required_date`

才可以计入：`CumulativeEffectiveInbound(<= required_date)`

#### 2.6.2 RemainingInboundQty

定义：

```
RemainingInboundQty = ordered_qty - received_qty
```

要求：

```
ordered_qty  >= 0
received_qty >= 0
RemainingInboundQty >= 0
```

如果：

```
received_qty > ordered_qty
```

**不得**：

- `clamp`
- 自动改成 0
- 猜测业务含义

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

#### 2.6.3 PO / Inbound Status Eligibility

当前 POC 使用以下**保守分类**：

**A. `OPEN`**

**Eligible: YES**

前提：`RemainingInboundQty > 0` 且 arrival date 满足 `required_date` 边界。

**B. `CONFIRMED`**

**Eligible: YES**

前提同上。

**C. `PARTIALLY_RECEIVED`**

**Eligible: YES**

但**只计入** `RemainingInboundQty`。

**不得再次计入已 received 的数量。**

**D. `CANCELLED`**

**Eligible: NO**

不得计入未来供给。

**E. `CLOSED` / `COMPLETED`**

**Eligible: NO**

作为未来 inbound **不再计入**。

**原因：** 如果已收货，其结果应体现在 **Inventory**，而不是继续作为未来 Supply **重复计算**。

**F. Unknown / Invalid Status**

**不得猜测。**

**处理：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

#### 2.6.4 `effective_arrival_date`

定义：

`effective_arrival_date` 是 POC 中用于判断：

> "该 inbound 是否能够在某 Required Date 前成为有效供给"

的**标准化业务日期**。

**当前只定义其业务语义。**

**不得在本 Task 决定**它具体来自：

- `promised_date`
- `confirmed_date`
- `planned_delivery_date`
- `ETA`
- ERP proprietary field

具体 **source-field mapping** 留给后续：**Data Dictionary ＋ Adapter Contract**。

#### 2.6.5 Date Boundary

对于 Required Date = `t`：

只有 `effective_arrival_date <= t` 的 **eligible** inbound 可以进入 `CumulativeEffectiveInbound(<= t)`。

如果 `effective_arrival_date > t`，则**不得计入该日期的 Supply**。

> 它可以在**更晚的 required_date 重新参与累计计算**。

如果 `effective_arrival_date` **missing / invalid**，则：**`DATA_INCOMPLETE`**。

**不得假设为** `today`、`required_date`、`PO creation date` 或**任何默认日期**。

#### 2.6.6 Deterministic Formula

```
EffectiveInboundQty(i, t) = RemainingInboundQty(i)
  only if status(i) is eligible
     AND effective_arrival_date(i) <= t
```

否则：

```
EffectiveInboundQty(i, t) = 0
```

随后：

```
CumulativeEffectiveInbound(<= t) = Σ EffectiveInboundQty(i, t)
```

**按以下粒度，与 `BR-SHORTAGE-001` 的计算粒度对齐：**

```
plant_id
+ material_code
+ required_date
```

#### 2.6.7 Plant / Material Boundary

Inbound **必须**能够可靠映射到：

```
plant_id
+ material_code
```

**不得**：

- 自动跨 Plant 使用 PO
- 将无法映射的 PO 归入当前 material
- 让 LLM 猜测 PO 对应哪个物料或 Plant

如果映射失败：`DATA_INCOMPLETE` ＋ **Data Quality Issue**。

#### 2.6.8 No Double Counting

必须防止**两类** double counting：

**A. Received quantity double counting**

已收货数量**不得同时存在于** `Inventory` ＋ `Future Inbound`。

因此：`PARTIALLY_RECEIVED` **只使用** `RemainingInboundQty`。

**B. `CLOSED` / `COMPLETED` double counting**

已完成 PO **不得继续作为未来 inbound 计入**。

#### 2.6.9 Acceptance Examples

以下为 **deterministic examples**。

**Example A — Eligible `OPEN` PO**

| 字段 | 值 |
| --- | --- |
| Required Date | `2026-10-15` |
| status | `OPEN` |
| ordered_qty | 100 |
| received_qty | 0 |
| effective_arrival_date | `2026-10-12` |

**Expected：**

- `RemainingInboundQty = 100`
- `EffectiveInboundQty(<= 2026-10-15) = 100`

**Example B — Arrival after requirement**

| 字段 | 值 |
| --- | --- |
| Required Date | `2026-10-15` |
| status | `CONFIRMED` |
| ordered_qty | 80 |
| received_qty | 0 |
| effective_arrival_date | `2026-10-20` |

**Expected：** `EffectiveInboundQty(<= 2026-10-15) = 0`

> 该 PO **可在更晚 required_date 重新参与计算**。

**Example C — Partial receipt**

| 字段 | 值 |
| --- | --- |
| status | `PARTIALLY_RECEIVED` |
| ordered_qty | 100 |
| received_qty | 40 |
| effective_arrival_date | `<= required_date` |

**Expected：**

- `RemainingInboundQty = 60`
- `EffectiveInboundQty = 60`

**不得计入 100。**

**Example D — Cancelled**

| 字段 | 值 |
| --- | --- |
| status | `CANCELLED` |
| ordered_qty | 100 |
| received_qty | 0 |
| effective_arrival_date | `<= required_date` |

**Expected：** `EffectiveInboundQty = 0`

**Example E — Missing arrival date**

| 字段 | 值 |
| --- | --- |
| status | `OPEN` |
| ordered_qty | 100 |
| received_qty | 0 |
| effective_arrival_date | `missing` |

**Expected：** `DATA_INCOMPLETE`

**不得自行给默认日期。**

**Example F — Invalid quantity**

`ordered_qty = 100`，`received_qty = 120`

**Expected：** `DATA_INCOMPLETE` ＋ **Data Quality Issue**

**不得**：`RemainingInboundQty = -20` 然后继续参与计算。

**Example G — Cumulative inbound**

Required dates：`2026-10-10`、`2026-10-20`

| PO | Remaining | arrival |
| --- | --- | --- |
| PO-001 | 50 | `2026-10-08` |
| PO-002 | 80 | `2026-10-15` |

**Expected：**

- `CumulativeEffectiveInbound(<= 2026-10-10) = 50`
- `CumulativeEffectiveInbound(<= 2026-10-20) = 130`

#### 2.6.10 AI Boundary

**Inbound eligibility 与 quantity 必须由 deterministic logic 决定。**

LLM **不可以**：

- 把 `CANCELLED` PO 当供给
- 猜 arrival date
- 猜 PO status
- 修改 `received_qty`
- 修改 `ordered_qty`
- 跨 Plant 借用 inbound
- 决定 source ERP 字段映射

LLM **可以**解释：

- 哪些 inbound 被计入
- 哪些被排除
- 为什么某 PO 晚于 `required_date`
- 为什么返回 `DATA_INCOMPLETE`

#### 2.6.11 Source-field Boundary

**本规则定义 business semantic，而不是 source schema。**

因此**不得创建**：

- ERP field mapping
- API Contract
- database column definition
- adapter implementation

例如 `effective_arrival_date` **只是 canonical business meaning**。

其 **source mapping** 进入后续 **Data Dictionary / Adapter Design**。

> 相关背景（属 FROZEN baseline，不重新解释）：`FROZEN` Discovery Brief §20 已将该口径划归 `POC Design v0.2`；`FROZEN` Discovery Validation v0.1 已在 `VR-005` 中确认 Purchase Order / Inbound 数据可得，但明确"**不得**在本阶段定义「有效在途」的最终业务算法"。

### 2.7 Supplier Risk / Evidence

**Rule ID:** `BR-SUPPLIER-RISK-001`

**Backlog:** `VB-27`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

**Validation Source:** `SC-RISK-001` / Human-approved `SIMULATED` design evidence

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED` **≠** `FROZEN` Discovery `H3` resolved。

> 关联的 FROZEN 原问题：风险判断是否依赖个人经验？（`HYPOTHESIS` / `TBD`；关联 `G-06`、`G-11`）

#### 2.7.0 Design Evidence Record — SC-RISK-001

| 字段 | 内容 |
| --- | --- |
| Scenario | `SC-RISK-001` — Supplier Risk Judgment |
| Evidence Type | `SIMULATED` |
| Evidence Source | Human-approved |
| Role | Simulated Procurement / Supply Chain Owner |
| Purpose | support design of deterministic Supplier Risk Evidence |

**必须声明**：该 Scenario

- **不是**云南 CY 集团真实供应商事实；
- **不是** `PUBLIC FACT`；
- **不是**对真实企业风险流程的确认；
- **不修改** `FROZEN` `H3` status；
- **只**作为模拟 POC 的 **downstream design input**。

**场景内容**：两个物料均 `ShortageQty = 50`，`RecommendationNeedDate` 距当前分析日 **20 days**。

```
Supplier A:
  StandardLeadTimeDays   = 10
  DeliveryPerformance    = 97%
  QualityPerformance     = 99%

Supplier B:
  StandardLeadTimeDays   = 35
  DeliveryPerformance    = 84%
  QualityPerformance     = 94%
```

**Human-approved simulated business judgment：** 虽然 `ShortageQty` 相同，两者业务风险**不应被视为相同**。Supplier B 因

- `Standard Lead Time` **超过剩余需求时间**；
- `Delivery Performance` **较差**；
- `Quality Performance` **较差**；

**需要更高关注**。

**POC 目标：** 将此类经验判断拆成

```
deterministic risk evidence
+
transparent policy
+
AI explanation
```

**不得让 LLM 自行生成风险事实。**

#### 2.7.1 Rule Purpose

本规则回答：

> 对于一个 `supplier_id` + `material_code`，当前已知的供应商事实，可以形成哪些 **deterministic ＋ explainable Risk Evidence**。

本规则**不得**回答：

> 「应该选择哪个 Supplier？」

**不得**进行：

- Supplier Ranking
- Automatic Supplier Selection

#### 2.7.2 Risk Evaluation Grain

风险评估**至少**按：

```
supplier_id
+ material_code
```

执行。

当 `Plant` context 对业务含义必要时，保留 `plant_id` 作为 **evaluation context**。

**不得**把多个 Supplier 的数据**合并成一个共同风险值**。

每个 Supplier **必须独立**形成自己的 **Supplier Risk Evidence Card**。

#### 2.7.3 Input Baseline

继承 `VR-006` 已确认可得的 **conceptual data**：

- `supplier_id`
- `material_code`
- `standard_lead_time_days`
- `delivery_performance`
- `quality_performance`
- `period`
- `updated_at`

并使用：

```
RecommendationNeedDate
```

作为 **Lead Time Feasibility** 的需求时间基准。

**必须保留 `period`** —— **不得只记录 performance value 而丢失 measurement period**。

因此：

```
delivery_performance
与
quality_performance
```

**必须对应一个可可靠识别的**：

```
PerformancePeriod
```

**不得自行定义真实**：

- ERP / SRM schema
- field mapping
- API contract

这些属于后续 **Data Dictionary / Adapter Design**。

> `period` 的完整性要求见 **§2.7.23 Performance Period Context**。
> Supplier-Material relationship eligibility 要求见 **§2.7.24 Supplier-Material Relationship Eligibility**。

#### 2.7.4 DaysUntilNeed

定义：

```
DaysUntilNeed
  = RecommendationNeedDate
  - AnalysisDate
```

要求：

```
DaysUntilNeed >= 0
```

如果出现以下任一情况：

- `RecommendationNeedDate` missing / invalid
- `AnalysisDate` missing / invalid
- `DaysUntilNeed < 0`

则：

```
LeadTimeRisk = DATA_INCOMPLETE
```

**不得自行猜日期。**

#### 2.7.5 Lead Time Feasibility Risk

第一版 **`SIMULATED` POC Policy**：

如果：

```
StandardLeadTimeDays > DaysUntilNeed
```

则：

```
LeadTimeRisk = HIGH
```

如果：

```
StandardLeadTimeDays <= DaysUntilNeed
```

则：

```
LeadTimeRisk = LOW
```

**注意：** 本版本**不定义** `MEDIUM` Lead Time Risk。**不得自行增加** buffer / grace period。

例如：

| DaysUntilNeed | StandardLeadTimeDays | Expected |
| --- | --- | --- |
| 20 | 35 | `LeadTimeRisk = HIGH` |
| 20 | 10 | `LeadTimeRisk = LOW` |

#### 2.7.6 Delivery Performance Risk

以下 threshold 是 **Human-approved `SIMULATED` POC policy**，**不是**真实 CY 企业 threshold。

```
DeliveryPerformance >= 95%                → LOW
90% <= DeliveryPerformance < 95%          → MEDIUM
DeliveryPerformance < 90%                 → HIGH
```

要求输入能够被**规范化**为 `0–100%` 或等价 canonical percentage。

本 Task **不设计** source-field normalization implementation。

#### 2.7.7 Quality Performance Risk

同样属于 **Human-approved `SIMULATED` POC policy**。

```
QualityPerformance >= 98%                 → LOW
95% <= QualityPerformance < 98%           → MEDIUM
QualityPerformance < 95%                  → HIGH
```

#### 2.7.8 OverallSupplierRisk

当前 POC **不使用 weighted score**。

**不得设计**：

```
0.4 × Lead Time
+ 0.35 × Delivery
+ 0.25 × Quality
```

或**任何未经验证的权重**。

定义：

```
OverallSupplierRisk
  = max severity
    of all reliable required dimensions
```

**Severity order：**

```
LOW < MEDIUM < HIGH
```

例如：

```
LeadTimeRisk = LOW
DeliveryRisk = MEDIUM
QualityRisk  = LOW
```

则：

```
OverallSupplierRisk = MEDIUM
```

例如：

```
LeadTimeRisk = HIGH
DeliveryRisk = LOW
QualityRisk  = LOW
```

则：

```
OverallSupplierRisk = HIGH
```

#### 2.7.9 Complete-data Requirement

第一版 POC **只有在三个维度**：

- `LeadTimeRisk`
- `DeliveryRisk`
- `QualityRisk`

**都能够可靠判定时**，才输出：

```
OverallSupplierRisk = LOW / MEDIUM / HIGH
```

如果**任一** required dimension：

- missing
- invalid
- unresolved

则：

```
OverallSupplierRisk = DATA_INCOMPLETE
```

**但**：已可靠取得的 **individual Risk Evidence 仍允许展示**。

**不得因为一项缺失而丢弃其他可靠事实。**

#### 2.7.10 Zero / Valid Extreme vs Missing

必须区分：

```
真实合法极值
```

与：

```
missing
```

例如：

```
DeliveryPerformance = 0%
```

如果数据**被可靠确认**，这是**合法但极差**的 performance：

```
DeliveryRisk = HIGH
```

而：

```
DeliveryPerformance = missing
```

表示**无法判断**：

```
DeliveryRisk = DATA_INCOMPLETE
```

`QualityPerformance` **同理**。

**不得将 missing 默认成 0。**

#### 2.7.11 Risk Evidence Card

每个 `supplier_id` + `material_code` 形成**独立 Risk Evidence Card**。

至少包含以下 **canonical meaning**：

- `supplier_id`
- `material_code`
- `RecommendationNeedDate`
- `AnalysisDate`
- `DaysUntilNeed`
- `StandardLeadTimeDays`
- `LeadTimeRisk`
- `PerformancePeriod`
- `PerformanceUpdatedAt`
- `DeliveryPerformance`
- `DeliveryRisk`
- `QualityPerformance`
- `QualityRisk`
- `OverallSupplierRisk`
- Evidence Status / completeness

本 Task **不定义**：

- API Schema
- DB Schema
- JSON format
- UI layout

这里**只定义业务语义**。

#### 2.7.12 Evidence Explainability

Risk Evidence **必须能够解释**：

> 为什么得到该 Risk Level。

例如：

```
OverallSupplierRisk = HIGH
```

**Evidence：**

- Need in 20 days
- Standard Lead Time = 35 days
- Lead Time gap = 15 days
- `LeadTimeRisk = HIGH`
- Delivery Performance = 84%
- `DeliveryRisk = HIGH`
- Quality Performance = 94%
- `QualityRisk = HIGH`

**不得只输出** `HIGH` 而**没有 evidence**。

#### 2.7.13 Deterministic Examples

以下为 **deterministic examples**（对应 `SC-RISK-001`）。

**Example A — Supplier A**

| 字段 | 值 |
| --- | --- |
| `DaysUntilNeed` | 20 |
| `StandardLeadTimeDays` | 10 |
| `DeliveryPerformance` | 97% |
| `QualityPerformance` | 99% |

**Expected：**

- `LeadTimeRisk = LOW`
- `DeliveryRisk = LOW`
- `QualityRisk = LOW`
- `OverallSupplierRisk = LOW`

**Example B — Supplier B**

| 字段 | 值 |
| --- | --- |
| `DaysUntilNeed` | 20 |
| `StandardLeadTimeDays` | 35 |
| `DeliveryPerformance` | 84% |
| `QualityPerformance` | 94% |

**Expected：**

- `LeadTimeRisk = HIGH`
- `DeliveryRisk = HIGH`
- `QualityRisk = HIGH`
- `OverallSupplierRisk = HIGH`

**注意：** 这两个结果**只表示**：

```
两张独立 Supplier Risk Evidence Cards
```

**不得自动输出**：

```
Supplier A should be selected
```

或：

```
Supplier A ranks #1
```

**Example C — Performance period missing**

| 字段 | 值 |
| --- | --- |
| `supplier_id` | `SUP-A` |
| `material_code` | `MAT-A` |
| `DeliveryPerformance` | 97% |
| `QualityPerformance` | 99% |
| `period` | missing |

**Expected：**

- `DeliveryRisk = DATA_INCOMPLETE`
- `QualityRisk = DATA_INCOMPLETE`
- `OverallSupplierRisk = DATA_INCOMPLETE`

**不得**因为 `97%` / `99%` 数值看起来很好就输出 `LOW`。

**Example D — Relationship unresolved**

Supplier exists；Material exists；但 **Supplier-Material Relationship 无法可靠确认**。

**Expected：**

- Risk Evidence Status = `DATA_INCOMPLETE`

**不得自动**把该 Supplier 视为此 Material 的候选供应商。

#### 2.7.14 Boundary with Supplier Selection

即使同一个 Material 存在多个 Supplier：

```
Supplier A → LOW
Supplier B → HIGH
```

系统当前**只能展示**：

- `Supplier A` Risk Evidence
- `Supplier B` Risk Evidence

**不得自动**：

- 排名
- 推荐 Winner
- 自动选择 Supplier
- 自动把 LOW Risk Supplier 绑定进采购建议
- 根据 Risk 修改 `RecommendedPurchaseQty`

Supplier comparison / ranking / advanced supplier intelligence **保持在**：

```
P1 / Future scope
```

除非后续**单独 Human-approved Design Change**。

#### 2.7.15 Boundary with Procurement Quantity

`BR-SUPPLIER-RISK-001` **不得改变** `BR-PROCUREMENT-001` 的 `RecommendedPurchaseQty`。

例如：

```
SupplierRisk = HIGH
```

**不得自动**：

- 增加采购数量
- 减少采购数量
- 拆单
- 改 MOQ
- 选备用供应商

`Risk Evidence` 是**决策支持输入**，**不是采购数量算法的一部分**。

#### 2.7.16 Missing / Invalid Input Fail-safe

以下情况应明确处理：

| 输入情况 | 对应维度 |
| --- | --- |
| `supplier_id` unresolved | `DATA_INCOMPLETE` |
| `material_code` unresolved | `DATA_INCOMPLETE` |
| `RecommendationNeedDate` missing / invalid | `LeadTimeRisk = DATA_INCOMPLETE` |
| `AnalysisDate` missing / invalid | `LeadTimeRisk = DATA_INCOMPLETE` |
| `StandardLeadTimeDays` missing / invalid | `LeadTimeRisk = DATA_INCOMPLETE` |
| `StandardLeadTimeDays < 0` | `LeadTimeRisk = DATA_INCOMPLETE` |
| `DeliveryPerformance` missing / invalid | `DeliveryRisk = DATA_INCOMPLETE` |
| `DeliveryPerformance < 0%` | `DeliveryRisk = DATA_INCOMPLETE` |
| `DeliveryPerformance > 100%` | `DeliveryRisk = DATA_INCOMPLETE` |
| `QualityPerformance` missing / invalid | `QualityRisk = DATA_INCOMPLETE` |
| `QualityPerformance < 0%` | `QualityRisk = DATA_INCOMPLETE` |
| `QualityPerformance > 100%` | `QualityRisk = DATA_INCOMPLETE` |
| `period` missing / invalid（而 performance value 存在） | `DeliveryRisk` / `QualityRisk` = `DATA_INCOMPLETE` |
| Supplier-Material Relationship 无法可靠确定 | Risk Evidence Status = `DATA_INCOMPLETE` |

`OverallSupplierRisk`：**`DATA_INCOMPLETE`**

**不得**：

- 猜测
- `clamp`
- 默认 `LOW`
- 默认 0
- 默认 100
- 让 LLM 补值

#### 2.7.17 Deterministic Logic Boundary

以下**必须由 deterministic logic 产生**：

- `DaysUntilNeed`
- `LeadTimeRisk`
- `DeliveryRisk`
- `QualityRisk`
- `OverallSupplierRisk`
- Evidence completeness

**LLM 不参与 risk classification。**

#### 2.7.18 AI Boundary

LLM **可以**：

- 解释为何风险是 `LOW` / `MEDIUM` / `HIGH`
- 将结构化 Risk Evidence 转成自然语言
- 说明哪些输入缺失
- 说明为什么 `OverallSupplierRisk = DATA_INCOMPLETE`
- 对比用户**明确指定**的两个 Risk Evidence Cards 的事实差异

LLM **不可以**：

- 猜 performance
- 猜 lead time
- 修改 thresholds
- 创建新的 threshold
- 自行生成权重
- 自动 Supplier Ranking
- 自动 Supplier Selection
- 把 simulated threshold 说成真实企业规则
- 把 Risk Level 当成事实来源

#### 2.7.19 Threshold Governance

必须明确：以下 thresholds

```
Delivery:  95 / 90
Quality:   98 / 95
```

是 **Human-approved `SIMULATED` POC policy**。

**不是**：

- `PUBLIC FACT`
- 真实客户政策
- 行业标准

未来如果改变 thresholds，属于 **Business Rule Change**，**必须**：

```
Human Approval
+
versioned / traceable change
```

**不得由 Agent / LLM 自行调整。**

#### 2.7.20 H3 / Validation Relationship

必须明确记录：`SC-RISK-001` 为 **Human-approved `SIMULATED` downstream design evidence**。

它支持：

> 「存在将经验型风险判断结构化为 deterministic risk evidence 的设计价值」

**但**：`FROZEN` Discovery Validation v0.1 中

```
H3 = TBD
```

**保持不变。**

**不得在本文件声称**：`FROZEN` `H3` 已被正式修改为 `PARTIALLY CONFIRMED`。

**可以记录**：如果未来 Human 决定正式更新 `H3` validation status，应通过：

```
新的 Validation Version / Addendum
```

完成。

> 即：本 Task **不修改** `FROZEN` Validation，**不把本 Task 的设计规则倒写成历史 Discovery 事实**。

#### 2.7.21 G-06 / G-11 Relationship

继承 `FROZEN` source：

```
G-06 = 部分 RESOLVED
G-11 = 部分 RESOLVED
```

本 Task **不修改 `FROZEN` 文档**。

设计层完成后，**可以**说明：`VB-27` 的 **Design Gap 已解决**。

但**不得**写成：`FROZEN` Discovery 中的 `G-06` / `G-11` 已经被回写成 `RESOLVED`。

保持以下**两个层级分离**：

```
Validation baseline
与
Design resolution
```

#### 2.7.22 Source-field Boundary

**本规则定义 business semantic，而不是 source schema。**

因此**不得创建**：

- ERP / SRM field mapping
- API Contract
- database column definition
- adapter implementation
- risk engine implementation
- ranking engine

例如 `delivery_performance`、`quality_performance`、`standard_lead_time_days`
**只是 canonical business meaning**。

其 **source mapping** 进入后续 **Data Dictionary / Adapter Design**。

#### 2.7.23 Performance Period Context

`VR-006` 的 Supplier Performance baseline 中已存在：

- `supplier_id`
- `period`
- `delivery_performance`
- `quality_performance`
- `updated_at`

因此 `delivery_performance` 与 `quality_performance` **必须对应一个可可靠识别的**：

```
PerformancePeriod
```

**它可能代表某个明确的统计窗口，但本 Task 不决定**：

- 30 days
- 90 days
- 12 months
- rolling window
- fiscal period

这些真实 **period policy** 留给后续 **Data Mapping / Business Rule refinement**。

**本 Task 不得自行发明固定统计周期。**

**Performance Evidence Completeness**

如果：

```
delivery_performance 有值
但对应 period 无法可靠确定
```

则：

```
DeliveryRisk = DATA_INCOMPLETE
```

如果：

```
quality_performance 有值
但对应 period 无法可靠确定
```

则：

```
QualityRisk = DATA_INCOMPLETE
```

**不得**把：

```
"97% but period unknown"
```

视为**完整可靠**的 Risk Evidence。

`updated_at` **不能替代** performance measurement period。

> 本 Task **不定义** performance freshness threshold / maximum age / rolling window。
> 这些仍属于后续 Design。

#### 2.7.24 Supplier-Material Relationship Eligibility

`VR-006` 已存在：

```
Supplier-Material Relationship
```

以及：

```
sourcing_status
```

因此补充一个 **eligibility boundary**：

Risk Evidence 的业务上下文**必须能够确认** `supplier_id` 与 `material_code` **存在可可靠识别的
Supplier-Material Relationship**。

**不得**因为 Supplier Master 中存在某 Supplier，就**自动认为**其可以供应任意 Material。

`sourcing_status` 用于判断该 relationship 是否属于**当前可评估的 candidate relationship**。

本 Task **不定义**具体 `sourcing_status` enum / vocabulary。

**不得自行发明** `APPROVED` / `ACTIVE` / `QUALIFIED` 等真实 source status。

只定义：如果 **relationship eligibility 无法可靠确定**：

```
Risk Evidence Status = DATA_INCOMPLETE
```

**不得由 LLM 猜测供应资格。**

**Important Boundary**

Relationship eligibility：

```
≠ Supplier Ranking
≠ Supplier Selection
≠ Supplier Recommendation
```

它**只回答**：

> 「这个 supplier-material relationship 是否具有足够可靠的业务上下文进入 Risk Evidence evaluation。」

即使**两个 relationship 都 eligible**：

```
Supplier A = LOW
Supplier B = HIGH
```

仍然：

- **不得自动排名**
- **不得自动选择**
- **不得绑定到采购建议**

> 本 Task **不定义** supplier qualification workflow。
> 这些仍属于后续 Design。

---

## 3. System Boundary

**Backlog:** `VB-29`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

**Validation Source:** `VR-007` / `SC-INT-001`（`FROZEN`，Human-approved `SIMULATED`）＋ `VB-29` Human Approval

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED`。
>
> 本节只定义 **conceptual boundary**；**不选择**技术组件 / deployment / API Gateway / database / framework。

**待说明项状态：**

| 待说明项 | Status |
| --- | --- |
| POC responsibility | **`DESIGN RESOLVED`** |
| external system boundary | **`DESIGN RESOLVED`** |
| write boundary | **`DESIGN RESOLVED`** |
| failure boundary | **`DESIGN RESOLVED`** |

> 继承约束（不重新定义）：Source-system write = `DENIED`；Production write-back = `OUT OF SCOPE`（见 §5 Design Principles → Integration）。

**VB-29 Design Decision：**

```
VB-29 = DESIGN RESOLVED

POC 可以且应采用：
  Read-only source integration
  +
  Draft-only business action

无需 Production system write permission。
```

> `YES` = **当前模拟 POC 的 Design Decision**，**不代表**真实 CY 生产系统已经验证。

#### 3.1 Source Baseline（FROZEN Reference）

引用 `FROZEN` Discovery Validation：**`VR-007`** / **`SC-INT-001`**。

其中已确认：

```
Integration Pattern = Controlled Export / Snapshot
```

**Source System Boundary：**

| 操作 | 边界 |
| --- | --- |
| `READ` | **allowed only through controlled exported snapshot** |
| `WRITE` | **`DENIED`** |

```
Production Write-back = OUT OF SCOPE
```

> **不得修改 `FROZEN` source。** 本节只引用其已确认结论，**不重新解释、不扩大**。

#### 3.2 POC Responsibility

POC **负责**：

- 只读地获取**已导出的**业务数据快照；
- 运行 deterministic business rules（§2）；
- 生成 **Explanation / Recommendation / Draft**（§5）；
- 支持 Human Review / Modify / Approve / Reject（**POC 内部**）。

POC **不负责**：

- 写入任何 source system；
- 执行正式业务动作；
- 替代企业系统的记录职责。

#### 3.3 External System Boundary

POC **不直接读取 Production DB**。

POC business data **只能**通过以下链路进入 POC：

```
Simulated Enterprise Sources
      ↓
Controlled Export
      ↓
POC Data Landing Zone
```

Agent / LLM **不得**：

- direct Production DB access
- free-form SQL to Production
- bypass Controlled Export
- 扩大 source access

#### 3.4 Read Boundary

**POC 不直接读取 Production DB。**

读取**只能**通过 **Controlled Export / Snapshot** 产物（`POC Data Landing Zone`）进行。

**不得**：

- 假设存在真实 Production API 或 direct DB access；
- 绕过 Controlled Export 直连源系统；
- 以「只读」为由扩大 source access 范围。

#### 3.5 Write Boundary

**Source-system write：**

```
DENIED
```

POC **不允许**：

- 修改 Inventory
- 修改 Production Plan
- 修改 Purchase Order
- 修改 Supplier Master
- 修改 BOM
- 创建真实 Purchase Requisition
- 创建真实 Purchase Order
- 调用 Production write API
- 直接写 ERP / WMS / PLM

#### 3.6 Draft Boundary

AI Copilot **可以**生成：

```
Procurement Request Draft
```

Draft **只存在**于：

```
POC / Draft Boundary
```

必须明确：

```
POC Draft
  ≠ ERP Purchase Request
  ≠ Purchase Order
```

Draft **不产生**真实业务系统副作用。

#### 3.7 Human Approval Boundary

Human **可以**在 POC 中：

- Review
- Modify
- Approve
- Reject

但必须明确：

```
Human Approval
  ≠ Production Execution
```

Human 在 POC 中 Approve 后：**允许**状态变为：

```
APPROVED
```

但**不得**因此：

- 自动写入 ERP
- 自动创建 PO
- 自动提交 Production workflow

真实业务执行仍：

```
OUTSIDE POC WRITE BOUNDARY
```

#### 3.8 POC State vs Enterprise State

必须区分：

```
POC internal state
与
Enterprise source-system state
```

例如：

```
POC Draft = APPROVED
```

**不意味着**：

```
ERP Purchase Request exists
```

也**不意味着**：

```
Purchase Order created
```

**不得**将 POC 状态变化描述为**企业系统写入成功**。

#### 3.9 Effective Permission Boundary

继承：

```
AI Effective Permission
  = User Permission
  ∩ Data Scope
  ∩ Tool Permission
  ∩ Workflow State
  ∩ POC Policy
```

即使 Human 本人拥有真实业务系统写权限：

```
Human Capability
  可以高于
Agent Capability
```

Agent **仍不得**获得 Production write capability。

#### 3.10 Failure / Safety Boundary

如果：

- Controlled Snapshot unavailable
- Data Landing Zone unavailable
- required Tool unavailable

则：**POC 应 fail closed。**

**不得**：

- 切换成 Production direct access
- 尝试 Production DB
- 尝试 write API
- 让 LLM 使用旧数据**伪装当前事实**

**只允许**：

- 报告 unavailable
- `DATA_INCOMPLETE`
- Tool failure

#### 3.11 Integration with §5 AI / Tool Boundary

保持：

```
LLM does not create business truth
```

以及：

```
Data Source
      ↓
Deterministic Data Tool
      ↓
Structured Result
      ↓
LLM
```

`VB-29` **不改变** §5 AI / Tool Boundary。

#### 3.12 Integration with §6 HITL Workflow

本 Task **只为未来 §6 建立硬边界**：

- Draft
- Review
- Modify
- Approve
- Reject

**都可以存在**于 POC 内。

但：

```
execution boundary = OUTSIDE POC
```

**不得本轮设计完整 HITL state machine。**

#### 3.13 Acceptance Examples

以下为 **conceptual examples**。

**Example A — Generate Draft**

AI generates Procurement Request Draft.

**Expected：**

- POC Draft created
- ERP / source system：**`UNCHANGED`**

**Example B — Human Approves**

Human approves POC Draft.

**Expected：**

- POC workflow state：`APPROVED`
- Production ERP：**`UNCHANGED`**
- **不得**自动创建 Purchase Order

**Example C — User asks AI to submit**

User：「直接帮我下单。」

**Expected：**

- AI **不执行** Production write
- **可以**说明：正式业务执行**超出当前 POC write boundary**

**Example D — Snapshot unavailable**

Controlled Snapshot unavailable.

**Expected：**

- **fail closed**
- **不得**切换到 direct DB / Production API
- **不得**使用旧 conversation data **伪装成当前企业事实**

**Example E — Human has production authority**

Human user 本身拥有 Production write 权限。

**Expected：**

- Agent Capability **仍受 POC Policy 限制**
- Agent **不因此**获得 Production write capability

#### 3.14 Status Boundary

本节 `DESIGN RESOLVED` **只代表**：

```
conceptual boundary 已定义
```

**不代表**：

- 真实 ERP write integration 已设计
- Adapter / Connector 已实现
- 技术组件 / deployment / API Gateway / database / framework 已选择
- tested / production-ready

> 本 Task **不得设计真实 ERP write integration**。

---

## 4. Data & Integration Design

> 本章节建立 POC 的 Data & Integration Design。**不得创建实际 Schema / Contract。**

| 子章节 | Status |
| --- | --- |
| Canonical Data Model | **`DESIGN RESOLVED`** |
| Data Dictionary | **`DESIGN RESOLVED`** |
| Snapshot / Import Contract | `DESIGN PENDING` |
| Data Validation | `DESIGN PENDING` |
| Master Data Mapping | `DESIGN PENDING` |
| Adapter Boundary | `DESIGN PENDING` |

> 继承约束（不重新定义）：Integration Pattern = **Controlled Export / Snapshot**。具体文件格式（CSV / JSON / Parquet）与 Adapter Contract 属本阶段待设计事项，**本轮未决定**。

> **注意**：`Canonical Data Model` 完成**仅**表示 **canonical business entities 与 relationships 已定义**；
> **不代表**整个 §4 完成。其余 4 项仍为 `DESIGN PENDING`。

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
| N | **BOM Component** | 物料需求展开来源 | `plant_id` + parent material + component `material_code` | §2.4.2、§2.4.3 |
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
  - `required_quantity`
  - `ProductionQty`
- **必要来源关系：** 必须能够**追溯到** `BOM relationship`（见 `N`）与 `loss_rate` 计算来源（见 §4.1.12）。
- **约束：** **不得跨 Plant 合并需求**。

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
- **Canonical identity / grain：** source substitute material ＋ target material ＋ effective demand context
- **Attributes：** 至少
  - source substitute material
  - target material
  - `AllocatedSubstituteQty`
  - effective demand context
- **用途：** 支撑 `RemainingUnallocatedSourceSupply` 与 **No Double Allocation**。
- **约束：** `Σ AllocatedSubstituteQty <= EligibleSubstituteSupply`（见 §2.3.10）。

**H. Supplier**

- **Purpose：** 只保留 Supplier identity。
- **Canonical identity：** `supplier_id`
- **不得扩展**为完整 Supplier Master。

**I. Supplier-Material Relationship**

- **Purpose：** 支撑 `BR-SUPPLIER-RISK-001`。
- **Canonical identity / grain：** `supplier_id` + `material_code`
- **Attributes：** 至少
  - supplier → `supplier_id`
  - material → `material_code`
  - relationship eligibility context → `sourcing_status`
- **约束：** **不得自行定义** `sourcing_status` enum / vocabulary。
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
- **Canonical identity / grain：** `plant_id` + parent material + component `material_code`
- **Attributes：** 至少 `BOMComponentQty`、`material_code`
- **DESIGN PENDING（本 Task 明确不设计）：**
  - BOM version selection
  - BOM validity selection
  - BOM explosion algorithm
  - ERP source-field mapping
- **约束：** 无法可靠确定适用 BOM → `DATA_INCOMPLETE`。

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
  → BOM Component（来源关系）

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
| `loss_rate` 的 canonical owner / grain | **`UNKNOWN`** | §2.4 只定义其语义与公式，**未定义**其归属实体与粒度 |
| Warehouse 是否为 canonical attribute | **`DESIGN PENDING`** | §2.2.1 的 grain **不含** warehouse；§2.2.4 只描述 Plant 内聚合 |
| BOM version / validity selection | **`DESIGN PENDING`** | §2.4.3 明确不由该规则设计 |
| `sourcing_status` enum / vocabulary | **`DESIGN PENDING`** | §2.7.24 明确不定义 |
| `effective_arrival_date` 的 source field | **`DESIGN PENDING`** | §2.6.4 留给 Data Dictionary |
| Allocation 与 demand window 的关联机制 | **`DESIGN PENDING`** | §2.3.12 明确不设计 timing engine |
| `ApplicableMOQ` 的来源 | **`DESIGN PENDING`** | §2.5.5 留给 Data Dictionary / Adapter Design |
| Provenance 的具体承载方式 | **`DESIGN PENDING`** | 见 §4.1.8 |

> 以上条目**不影响** `Canonical Data Model = DESIGN RESOLVED` ——
> 它们属于**后续 Master Data Mapping / Adapter Boundary** 的范围，
> 其**语义层面**已在 **§4.2 Data Dictionary** 中登记（见 §4.2.16）。

---

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
| analysis run identity | `ANALYSIS_RUN_ID` | `REQUIRED` | `CONTEXT` | 一次短缺分析运行的标识 | `NOT DEFINED`；**ID 生成方式未设计** | `DATA_INCOMPLETE` | `BR-SHORTAGE-001`、`BR-PROCUREMENT-001`、`BR-SUPPLIER-RISK-001` |
| `AnalysisDate` | `DATE` | `CONDITIONAL`（Lead Time Feasibility 时 `REQUIRED`） | `CONTEXT` | 分析运行日期（`DaysUntilNeed` 的减数） | `NOT DEFINED` | `LeadTimeRisk = DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |

#### 4.2.4 Requirement / BOM Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `required_date` | `DATE` | `REQUIRED` | `SOURCE` | 需求日期（累计计算的 `t`） | `NOT DEFINED` | `DATA_INCOMPLETE` | `BR-REQUIREMENT-001`、`BR-SHORTAGE-001` |
| `required_quantity` | `NON_NEGATIVE_QUANTITY` | **`DESIGN PENDING`** | **`DESIGN PENDING`** | **语义未定**（见下） | `NOT DEFINED` | `DESIGN PENDING` | — （**未被任何 Rule 使用**） |
| `ProductionQty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 生产数量 | `ProductionQty >= 0` | `DATA_INCOMPLETE` | `BR-REQUIREMENT-001` |
| `BOMComponentQty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 单位父项所需组件数量 | `BOMComponentQty >= 0`；必须来自**可靠解析的 applicable BOM relationship** | `DATA_INCOMPLETE` | `BR-REQUIREMENT-001` |
| `loss_rate` | `RATIO` | `REQUIRED`（for `BR-REQUIREMENT-001`） | `POLICY_INPUT` | 预计投入总量中发生损耗的比例 | `0 <= loss_rate < 1` | `DATA_INCOMPLETE` ＋ Data Quality Issue | `BR-REQUIREMENT-001` |

**`required_quantity` vs `ProductionQty` —— SEMANTIC AMBIGUITY（`DESIGN PENDING`）**

现有 Design **没有可靠说明** `required_quantity` 与 `ProductionQty` 究竟是：

- 同义
- 父子关系
- 还是**不同业务量**

**不得猜测。**

**明确：** `BR-REQUIREMENT-001` 当前确定使用的是：

```
ProductionQty × BOMComponentQty
```

**不得**因为 Data Dictionary 存在 `required_quantity` 就自动改用 `required_quantity`。

#### 4.2.5 Inventory Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `inventory_status` | `STATUS` | `REQUIRED` | `SOURCE` | 库存可用性状态 | 仅 `AVAILABLE` / `INSPECTION` / `FROZEN`（见 §4.2.14） | 未知 / 非法 → `DATA_INCOMPLETE`；**不得静默归类为 `AVAILABLE`** | `BR-INVENTORY-001` |
| `on_hand_qty` | `DECIMAL_QUANTITY` | `REQUIRED` | `SOURCE` | 观测到的在手库存数量 | **不得** `clamp to 0`；`on_hand_qty < 0` 为**非法输入**（见 §2.2.8） | `DATA_INCOMPLETE` ＋ Data Quality Issue | `BR-INVENTORY-001` |
| `inventory_snapshot_time` | `TIMESTAMP` | `REQUIRED` | `CONTEXT` | 库存观测时间点 | `NOT DEFINED` | `DATA_INCOMPLETE` | `BR-INVENTORY-001` |
| `SafetyStock` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `POLICY_INPUT` | 业务配置的安全库存（Configured Safety Stock） | `SafetyStock >= 0` | `DATA_INCOMPLETE`；**不得默认成 0** | `BR-INVENTORY-001`、`BR-SHORTAGE-001` |

> `warehouse ownership unresolved` 是 **Data Quality fail-safe 触发项**（见 §2.2.9）；
> 但 **Warehouse 的 canonical role 仍为 `DESIGN PENDING`**（见 §4.2.16）。

#### 4.2.6 Inbound Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ordered_qty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 已订购数量 | `ordered_qty >= 0` | `DATA_INCOMPLETE` | `BR-INBOUND-001` |
| `received_qty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 已收货数量 | `received_qty >= 0`；`received_qty > ordered_qty` 为**非法** | `DATA_INCOMPLETE` ＋ Data Quality Issue | `BR-INBOUND-001` |
| `effective_arrival_date` | `DATE` | `REQUIRED` | `SOURCE` | Inbound **真正可用于 shortage calculation** 的有效到货日 | `NOT DEFINED`；**source field `DESIGN PENDING`** | `DATA_INCOMPLETE` | `BR-INBOUND-001` |
| inbound status / eligibility context | `STATUS` | `REQUIRED` | `SOURCE` | 判断该 inbound 是否可计入未来供给的状态 | 见 §2.6.3 的保守分类；未知 / 非法 → **不得猜测** | `DATA_INCOMPLETE` ＋ Data Quality Issue | `BR-INBOUND-001` |

> `effective_arrival_date` 的 **source field 未决定**：**不得**自行认定它来自
> `promised_date` / `confirmed_date` / `planned_delivery_date` / `ETA` 或其他字段（见 §4.2.16）。

#### 4.2.7 Substitute Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `target_material_code` | `IDENTIFIER` | `REQUIRED` | `SOURCE` | 被覆盖的 Target Material | `NOT DEFINED` | `DATA_INCOMPLETE` | `BR-SUBSTITUTE-001` |
| `substitute_material_code` | `IDENTIFIER` | `REQUIRED` | `SOURCE` | 提供覆盖的 Substitute Material | `NOT DEFINED` | `DATA_INCOMPLETE` | `BR-SUBSTITUTE-001` |
| `substitution_ratio` | `RATIO` | `REQUIRED` | `SOURCE` | 1 unit Substitute 可覆盖多少 unit Target Requirement（**substitute → target**） | `substitution_ratio > 0` | `DATA_INCOMPLETE` ＋ Data Quality Issue；**不得默认成 `1.0`** | `BR-SUBSTITUTE-001` |
| `approval_status` | `STATUS` | `REQUIRED` | `SOURCE` | Substitute Relationship 的审批状态 | 仅 `APPROVED` 可参与计算（见 §4.2.14） | 缺失 / 无法判断 → `DATA_INCOMPLETE`；**不得由 LLM 自动批准** | `BR-SUBSTITUTE-001` |
| `AllocatedSubstituteQty` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 明确分配给某 Target 的替代数量 | `AllocatedSubstituteQty >= 0`；`Σ AllocatedSubstituteQty <= EligibleSubstituteSupply` | `DATA_INCOMPLETE` ＋ Data Quality Issue / Allocation Conflict；**不得默认成 0** | `BR-SUBSTITUTE-001` |
| effective demand context | `TEXT_CONTEXT` | `CONDITIONAL` | `CONTEXT` | allocation 对当前 `required_date` 有效的判定上下文 | `NOT DEFINED`；**关联机制 `DESIGN PENDING`** | `DATA_INCOMPLETE` | `BR-SUBSTITUTE-001` |

#### 4.2.8 Supplier Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `sourcing_status` | `STATUS` | `CONDITIONAL` | `SOURCE` | Supplier-Material relationship eligibility context | **vocabulary `DESIGN PENDING`** | 无法可靠确定 → Risk Evidence Status = `DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |
| `standard_lead_time_days` | `NON_NEGATIVE_QUANTITY` | `REQUIRED` | `SOURCE` | 标准供应周期（天） | `StandardLeadTimeDays >= 0` | `LeadTimeRisk = DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |
| `PerformancePeriod` | `TEXT_CONTEXT`（observation window） | `REQUIRED` | `CONTEXT` | performance 的**统计窗口** | `NOT DEFINED`（period policy `DESIGN PENDING`） | `DeliveryRisk` / `QualityRisk` = `DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |
| `PerformanceUpdatedAt` | `TIMESTAMP` | `CONDITIONAL` | `CONTEXT` | performance 记录更新时间 | `NOT DEFINED` | 不单独导致 `DATA_INCOMPLETE` | `BR-SUPPLIER-RISK-001` |
| `DeliveryPerformance` | `PERCENTAGE` | `REQUIRED` | `SOURCE` | 交付绩效 | `0% ～ 100%` | `DeliveryRisk = DATA_INCOMPLETE`；**不得默认成 0** | `BR-SUPPLIER-RISK-001` |
| `QualityPerformance` | `PERCENTAGE` | `REQUIRED` | `SOURCE` | 质量绩效 | `0% ～ 100%` | `QualityRisk = DATA_INCOMPLETE`；**不得默认成 0** | `BR-SUPPLIER-RISK-001` |

> **必须保持：** `PerformancePeriod`（measurement period）**≠** `PerformanceUpdatedAt`。
> `PerformanceUpdatedAt` **不能替代** measurement period。

#### 4.2.9 Procurement Fields

| Field | Logical Type | Requiredness | Class | Business Semantic | Valid / Invalid Boundary | Missing Behavior | Rule(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `RecommendationNeedDate` | `DATE` | `CONDITIONAL`（`Classification = SHORTAGE` 且 Procurement Recommendation applicable 时 `REQUIRED`） | `CONTEXT` | 采购建议所使用的 business need date | 当前 POC `= FirstShortageDate` | 见下方条件性说明 | `BR-PROCUREMENT-001` |
| `ApplicableMOQ` | `NON_NEGATIVE_QUANTITY` | `CONDITIONAL`（`Classification = SHORTAGE` 时 `REQUIRED`） | `POLICY_INPUT` | 当前采购建议所适用的最小采购数量约束 | `ApplicableMOQ >= 0` | `DATA_INCOMPLETE`；**不得默认成 0** | `BR-PROCUREMENT-001` |

> **`ApplicableMOQ` 的 Source Mapping = `DESIGN PENDING`。**
> **不得**自行绑定 Supplier / Contract / ERP Purchasing Info Record（见 §4.2.16）。

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
| Inbound status / eligibility context | 见 §2.6.3 的保守分类（含 `OPEN` / `CONFIRMED` / `PARTIALLY_RECEIVED` / `CANCELLED` / `CLOSED` / `COMPLETED`） | §2.6.3 |
| `Classification` | `NORMAL` / `BUFFER_BREACH` / `SHORTAGE` / `DATA_INCOMPLETE` | §2.1.4 |
| `approval_status` | 仅 `APPROVED` 可参与；`PENDING` / `REJECTED` / `UNKNOWN` 不得进入 | §2.3.5 |
| `LeadTimeRisk` | `LOW` / `HIGH` | §2.7.5 |
| `DeliveryRisk` / `QualityRisk` / `OverallSupplierRisk` | `LOW` / `MEDIUM` / `HIGH` / `DATA_INCOMPLETE` | §2.7.6 / §2.7.7 / §2.7.8 |
| `sourcing_status` | **vocabulary `DESIGN PENDING`** —— 只登记 logical meaning | §2.7.24 |

**特别注意 `sourcing_status`：**

```
logical meaning : Supplier-Material relationship eligibility context
vocabulary      : DESIGN PENDING
```

**不得自行创造** `ACTIVE` / `APPROVED` / `QUALIFIED` / `BLOCKED` 等 enum。

#### 4.2.15 Provenance Requirement

- 所有 `SOURCE` / `POLICY_INPUT` 字段都**需要未来能够追溯 source provenance**。
- 所有 `DERIVED` result 都**必须能追溯**：

```
input evidence
+ Rule ID
+ Analysis Run
```

**但本 Task 不设计**：provenance schema、`source_system_id`、lineage database、audit event format。

#### 4.2.16 Open Semantic / Mapping Items

以下项目**仍然开放**，**不得为了让 Data Dictionary 看起来「完整」而消灭**：

| 项 | 状态 |
| --- | --- |
| `loss_rate` canonical owner / grain | **`UNKNOWN`** |
| `required_quantity` vs `ProductionQty` | **`DESIGN PENDING` / SEMANTIC AMBIGUITY** |
| Warehouse canonical role | `DESIGN PENDING` |
| BOM version / validity selection | `DESIGN PENDING` |
| `sourcing_status` vocabulary | `DESIGN PENDING` |
| `effective_arrival_date` source field | `DESIGN PENDING` |
| Allocation demand-window mapping | `DESIGN PENDING` |
| `ApplicableMOQ` source | `DESIGN PENDING` |
| Provenance carrier | `DESIGN PENDING` |

> 以上条目**不影响** `Data Dictionary = DESIGN RESOLVED` ——
> 它们属于 **source mapping / Master Data Mapping / Adapter Boundary / Data Validation** 的范围。
>
> **本 Task 不定义任何 source table / column**，因此**未被偷渡**任何 source mapping。

#### 4.2.17 Status Semantics Boundary

`Data Dictionary = DESIGN RESOLVED` **仅**表示：

```
canonical field semantics defined
```

**不表示**：source mapping complete、physical schema complete、import contract complete、
data validated、implemented、tested。

---

### 4.3 Snapshot / Import Contract —— Package Envelope & Import Atomicity

> **子章节整体状态：仍为 `DESIGN PENDING`。**
>
> 本节只完成其**第一层**。

**层级状态登记：**

| 层 | Status |
| --- | --- |
| Package Envelope | **`DESIGN RESOLVED`** |
| Atomicity Boundary | **`DESIGN RESOLVED`** |
| Immutability Boundary | **`DESIGN RESOLVED`** |
| Analysis Run Linkage | **`DESIGN RESOLVED`** |
| Serialization Format | `DESIGN PENDING` |
| Physical Dataset Layout | `DESIGN PENDING` |
| Field Carrier Mapping | `DESIGN PENDING` |
| Final Import Contract | `DESIGN PENDING` |

> **不得**提前把整个 `Snapshot / Import Contract` 标记为 `DESIGN RESOLVED`。

#### 4.3.1 Purpose & Scope

本子章节定义：一次 **Controlled Export / Snapshot** 如何作为一个**不可变、可追溯、一致**的
数据输入单元进入 POC。

**本 Task 只定义：**

- Snapshot Package conceptual envelope
- package identity
- package immutability
- import atomicity
- cross-snapshot consistency
- Analysis Run 与 Snapshot Package 的关系
- package-level provenance requirement
- package acceptance / rejection boundary

**不得定义**：CSV / JSON / JSONL / Parquet / ZIP、database、directory layout、
concrete filenames、physical schema、API contract、Adapter implementation。

因此：

```
Serialization Format = DESIGN PENDING
```

#### 4.3.2 Snapshot Package Concept

定义：

> **Snapshot Package** 表示一次 **Controlled Export** 产生的、供 POC 读取的
> **immutable input evidence package**。

它是 **POC Data Landing Zone** 中的 **conceptual import unit**。

**必须明确：**

```
Snapshot Package  ≠ Analysis Run
Snapshot Package  ≠ Production System
Snapshot Package  ≠ Database Snapshot implementation
```

#### 4.3.3 Package Identity

定义 **transport-level concept**：

```
snapshot_package_id
```

**Purpose：** 唯一标识一次受控导出的 Snapshot Package。

**注意：** 它属于 **Import / Transport Context**，**不是** canonical business entity ID。

**不得规定**：UUID / hash / sequence / timestamp-based ID 等生成算法。

**只要求：** 同一 package identity **必须可稳定识别**。

> `snapshot_package_id` **不得**加入 `§4.2 Canonical Data Dictionary` 作为业务字段。

#### 4.3.4 Snapshot Package vs Analysis Run

```
Snapshot Package = immutable business evidence input

Analysis Run     = 使用某个已接受 Snapshot Package
                   执行 deterministic analysis 的运行上下文
```

**要求：**

```
每个 Analysis Run 必须能够追溯到 exactly one accepted Snapshot Package
```

当前 POC **不允许**一个 Analysis Run **静默拼接多个 Snapshot Package**。

**但：**

```
同一个 Snapshot Package 可以支持多次 Analysis Run
```

例如：

```
Snapshot Package S1
      ↓
Analysis Run R1

Snapshot Package S1
      ↓
Analysis Run R2
```

这允许**相同输入**在重新执行 / 回归验证时**保持可追溯**。

**不得假设：**

```
Snapshot Package ID  =  Analysis Run ID
```

#### 4.3.5 Immutability Boundary

一个**已经 Accepted** 的 Snapshot Package **必须视为 immutable**。

**不得：**

- 原地修改内容后继续使用同一个 package identity
- 部分覆盖 dataset
- silently replace records
- 用同一 ID 表示不同内容

如果业务数据发生变化：**必须形成新的 Snapshot Package identity**。

> 本 Task **不定义** storage implementation。

#### 4.3.6 Atomic Import Boundary

一次 Snapshot Package Import **必须具有 package-level atomic meaning**：

```
ACCEPTED
   或
REJECTED / UNUSABLE
```

**不得：**

```
部分 dataset 使用新 Snapshot，
部分 dataset 使用旧 Snapshot，
然后组成一个未明确声明的混合分析输入。
```

**例如禁止：**

```
Inventory   from Package P2
+ Requirement from Package P1
+ Inbound     from Package P3
```

在当前 POC 中被**静默合并**成 `Analysis Run R1`。

#### 4.3.7 Cross-Snapshot Mixing Prohibition

当前 POC 第一版：**默认禁止 silent cross-snapshot mixing**。

如果未来需要：

- multi-snapshot composition
- incremental refresh
- streaming updates
- delta ingestion

**必须作为独立 Design。**

**不得在本 Task 偷渡。**

#### 4.3.8 Logical Snapshot Manifest

定义 conceptual：**Snapshot Manifest**，用于描述 Package 自身。

**注意：** 这是 **logical manifest**。

本 Task **不决定**：`manifest.json` / `manifest.yaml` / database row / 其他物理实现。

Manifest **至少需要表达以下语义**：

- `snapshot_package_id`
- contract version
- export / package creation time
- environment / evidence classification
- included logical datasets
- dataset-level provenance reference
- dataset-level record count / integrity evidence
- package completeness state

这些属于 **transport / provenance metadata**。

**不得加入 Canonical Data Dictionary 作为业务字段。**

#### 4.3.9 SIMULATED Boundary

当前项目是**模拟企业 POC**。

Snapshot Package **必须能够明确标记**：

```
SIMULATED
```

**不得**让导入后的数据被描述成**真实 CY 企业生产数据**。

未来真实数据环境需要**新的 access / security / validation decision**。

#### 4.3.10 Logical Dataset Roles

Snapshot Package 可以包含支持 P0 的 **logical dataset roles**，例如来自 `§4.1` Canonical Model 的：

- Plant / Material identity context
- Production Requirement
- BOM Component
- Inventory Snapshot
- Configured Safety Stock
- Inbound Supply
- Substitute Relationship
- Substitute Allocation
- Supplier identity
- Supplier-Material Relationship
- Supplier Performance
- Procurement policy input

**注意：** 这里是 **logical dataset role**，**不是** physical filename / database table /
CSV sheet / JSON object name。

#### 4.3.11 Business Time vs Package Time

必须区分：

```
Package / export time
与
business time
```

Package creation / export time **不得替代**：

- `required_date`
- `effective_arrival_date`
- `inventory_snapshot_time`
- `PerformancePeriod`
- `PerformanceUpdatedAt`
- `AnalysisDate`

这些已有 canonical time semantics（见 §4.2.11）。

例如：一个 Package 在 `10:00` 导出，**不代表** Inventory Snapshot Time /
Supplier Performance Period / Requirement Date 都等于 `10:00`。

#### 4.3.12 Package Completeness vs Business DATA_INCOMPLETE

必须区分：

```
Package structural completeness
与
Business DATA_INCOMPLETE
```

**A. Package structural problem（Package Structural Inconsistency）**

**定义收紧：** 只有当 Snapshot Manifest **已声明**某 logical dataset 为 `included`，
但对应 dataset artifact：

- absent
- unreadable
- identity inconsistent
- 或 integrity unverifiable

才属于 **Package Structural Inconsistency**。

即：

```
Declared Included Dataset
+
Missing Corresponding Artifact
      ↓
Structural Failure
```

**而不是：**

```
Any Dataset Absent
      ↓
Structural Failure
```

其他结构性条件（例如 manifest unavailable、package identity inconsistent）
同样可能导致：**Package Import `REJECTED` / `UNUSABLE`**。

> **注意**：本 Task **不得**自行定义某个 logical dataset 永远 `REQUIRED` ——
> 完整 **capability-to-dataset requirement** 仍留给后续 **Data Validation Design**。

**B. Business data incomplete** —— Package 本身**结构合法**，但某业务字段
missing / invalid / unresolved：

则 Package **可以被 Accepted**，但对应业务 Rule 可能返回 **`DATA_INCOMPLETE`**。

**C. Dataset not declared / not included** ——

当前 Task **不决定**最终处理，**留给 capability-to-dataset validation**（见 §4.3.14）。

**不得把两个层级混为一谈。**

**三层对照：**

| # | 情形 | 结果 |
| --- | --- | --- |
| A | Manifest 声明 `Supplier Performance = included`，但 artifact missing | **Structural inconsistency** → Package may be **`REJECTED` / `UNUSABLE`** |
| B | Manifest 结构一致且 dataset 存在，但 `PerformancePeriod = missing` | Package may remain **`ACCEPTED`**；Supplier Risk capability may return **`DATA_INCOMPLETE`** |
| C | `Supplier Performance` dataset **根本未声明**为 included dataset | 当前 Task **不决定**最终处理 → 留给 capability-to-dataset validation |

#### 4.3.13 Valid Absence Preservation

继承 `§4.2`：

```
valid absence  ≠ missing required data
```

例如：没有产生 `RecommendedPurchaseQty`，因为 `Classification = NORMAL` ——
**不得**导致 Snapshot Package invalid。

同样：

```
FirstShortageDate = not present
```

如果**完整计算**证明没有 shortage，属于**正常业务结果**，**不是** package integrity error。

#### 4.3.14 Dataset Presence Boundary

**不得要求**每个 Snapshot Package **必须永远包含所有 logical datasets**。

Dataset 是否必须存在应取决于：**本 Analysis Capability 所需 evidence**。

例如：Supplier Performance 不存在，**不一定**使整个 Snapshot Package 结构非法。

但：运行 Supplier Risk capability 时可能导致 **`DATA_INCOMPLETE`** 或 **capability unavailable**。

**明确：**

```
Dataset not declared / not included
```

在本 Task **不得自动判定**：

- Package invalid
- 或 Business `DATA_INCOMPLETE`

具体结果留给后续 **capability validation**（见 §4.3.12 情形 C）。

> 完整 **capability-to-dataset requirement** 留给 **Data Validation Design**。

#### 4.3.15 Integrity Requirement

Snapshot Package **必须支持未来验证**：

- package identity integrity
- dataset identity
- dataset presence
- dataset completeness metadata
- content integrity

**但本 Task 不决定**：SHA256 / MD5 / digital signature / checksum implementation。

**只定义：**

```
integrity evidence is required
```

#### 4.3.16 Provenance Boundary

每个 imported dataset **必须能够追溯到**：

```
Snapshot Package
+
logical dataset role
+
controlled export provenance
```

**但本 Task 不设计**：`source_system_id` schema、lineage DB、audit DB、event format。

#### 4.3.17 Unresolved Carrier Boundary

以下项**仍未完全确定**（见 §4.2.16）：

- `loss_rate` owner / grain
- `required_quantity` vs `ProductionQty`
- Warehouse canonical role
- BOM version / validity
- `sourcing_status` vocabulary
- `effective_arrival_date` source mapping
- allocation demand-window mapping
- `ApplicableMOQ` source
- provenance carrier

因此本 Task **不得为了完成 Snapshot Contract** 擅自决定这些字段属于哪个
**physical dataset / file**。

**尤其 `loss_rate`：**

**不得**自行挂到 Production Requirement / Material / BOM Component / Plant-Material 之一。

这些**必须继续保持原状态**。

#### 4.3.18 Import Fail-Closed Principle

如果 Package identity / integrity / required structural metadata **无法可靠确定**：

**不得：**

- 猜测
- 自动修复成另一个 Package
- 使用旧 Package 补齐
- 从 Production 重新读取
- 让 LLM 决定如何拼接

**应 fail closed。**

> 具体 Data Quality taxonomy 留给后续 **Data Validation**。

#### 4.3.19 Read-only Boundary

Import 行为**仍必须遵守 `§3`**：

```
Controlled Export / Snapshot
      ↓
POC Data Landing Zone
      ↓
Read-only analysis
```

**Import 不得：**

- write back Production
- modify source system
- request Production DB fallback
- trigger ERP transaction

#### 4.3.20 Conceptual Import Lifecycle

只定义 **conceptual lifecycle**：

```
RECEIVED
   ↓
STRUCTURAL CHECK
   ↓
ACCEPTED
   or
REJECTED / UNUSABLE
   ↓
Accepted Package may be referenced by Analysis Run
```

**注意：** 这些**只描述 Import lifecycle**。

**不得**把它们加入：Shortage Classification / Supplier Risk Status / HITL Business Status。

**本 Task 不要求创建正式 enum。**

#### 4.3.21 Status Boundary

`Snapshot / Import Contract` **整体仍为 `DESIGN PENDING`**。

本 Task **仅**完成其第一层：Package Envelope、Import Atomicity、Immutability、Analysis Run linkage。

`DESIGN RESOLVED` 的四个层级**仅**表示其 **conceptual boundary 已定义**，
**不表示**：

- serialization format determined
- physical dataset layout determined
- field carrier mapping determined
- import implementation exists
- data validated
- tested

---

### 4.4 Data Validation —— Capability Readiness & Failure Semantics

> **子章节整体状态：仍为 `DESIGN PENDING`。**
>
> 本节已完成其中**两层**：Capability Readiness / Failure Semantics（`§4.4.1` ～ `§4.4.23`）
> 与 **Detailed Field Validation**（`§4.4.24` ～ `§4.4.44`）。

**层级状态登记：**

| 层 | Status |
| --- | --- |
| Validation Layer Model | **`DESIGN RESOLVED`** |
| Capability-to-Evidence Requirement | **`DESIGN RESOLVED`** |
| Failure Semantics | **`DESIGN RESOLVED`** |
| Dataset Absent vs Empty Semantics | **`DESIGN RESOLVED`** |
| Failure Isolation Principle | **`DESIGN RESOLVED`** |
| Detailed Field Validation | **`DESIGN RESOLVED`** |
| Cross-Dataset Consistency Rules | `DESIGN PENDING` |
| Validation Issue Taxonomy Finalization | `DESIGN PENDING` |
| Final Data Validation Design | `DESIGN PENDING` |

> **不得**提前将整个 `Data Validation` 标成 `DESIGN RESOLVED`。

#### 4.4.1 Purpose & Scope

本 Task 只回答：

1. 一个 **Accepted Snapshot Package** 是否具备运行某个 P0 capability 所需 evidence？
2. 数据缺失 / 非法时，应在**哪一层**失败？
3. 一个数据问题应影响**整个 package**、**某 capability**，还是**某个具体 business grain**？

**本 Task 不定义**：physical schema validation、JSON Schema、CSV parser、file parser、
implementation validator、testing framework、retry mechanism、logging technology、
database、API、adapter、source mapping。

#### 4.4.2 Validation Layer Model

定义四层 **conceptual validation**。

**Layer 1 — Package Structural Validation**

继承 `§4.3`。回答：Snapshot Package 自身是否**结构自洽**。

例如：manifest unavailable、package identity inconsistent、
declared included dataset artifact absent、artifact unreadable、integrity evidence unverifiable。

可能导致：

```
Package = REJECTED / UNUSABLE
```

**如果 Package 未 `Accepted`：不得创建依赖它的正常 Analysis Run。**

**Layer 2 — Canonical Evidence Validation**

回答：已导入 evidence 是否符合 `§4.1 Canonical Data Model` ＋ `§4.2 Data Dictionary`。

例如：logical type invalid、required field missing、quantity outside approved range、
invalid status、unresolved plant / material mapping、missing canonical business context。

这些**通常不自动使整个 Package structural invalid**，但可能使
**affected evidence** 或 **affected business grain** 不可可靠使用。

**Layer 3 — Capability Readiness Validation**

回答：当前 Accepted Package 是否包含运行某个 capability 所需的 **logical evidence**。

**注意：Capability Readiness 不是 Business Classification。**

**不得**把 `capability unavailable` 加入 `NORMAL` / `BUFFER_BREACH` / `SHORTAGE` / `DATA_INCOMPLETE`
等业务 enum。

**Layer 4 — Business Rule Validation**

在 capability 已拥有所需 evidence 后，由**既有 deterministic Business Rule** 执行业务判断。

例如 `SafetyStock` missing / `ApplicableMOQ` missing / `PerformancePeriod` missing
可导致既有 **`DATA_INCOMPLETE`**。

**不得由 Data Validation 重新定义这些 Business Rules。**

#### 4.4.3 Three Failure Meanings

必须明确区分：

**A. Package Structural Failure** —— Package 自身**不可信**。

例如：Manifest says dataset included but artifact absent。

结果：**Package may be `REJECTED` / `UNUSABLE`。**

**B. Capability Evidence Unavailable** —— Package 是 `Accepted`，
但**没有提供**运行某 capability 所需的 logical evidence role。

例如：Supplier Performance dataset 没有在 Package 中声明提供，用户却请求 Supplier Risk。

结果：**该 capability cannot execute reliably.**

可以描述为：`Capability unavailable due to unavailable evidence.`

**注意：这是 operational / capability condition，不是新的 Business Status enum。**

**C. Business `DATA_INCOMPLETE`** —— Capability 所需 evidence **在逻辑上存在**，
但当前 **business grain** 中的必要数据 missing / invalid / unresolved，
导致 deterministic rule **无法可靠形成结果**。

例如：Supplier Performance dataset 存在，但当前 supplier-material 的 `PerformancePeriod = missing`
→ Supplier Risk Rule → **`DATA_INCOMPLETE`**。

**Canonical Separation（不得互相提升或降级）**

```
Package Structural Failure
  ≠ Capability Evidence Unavailable
  ≠ Business DATA_INCOMPLETE
```

**Business Rule 返回 `DATA_INCOMPLETE` 仍说明：**

```
Business Rule execution reached a valid
business outcome state.
```

**它不是 Capability Readiness failure。**

反之：

```
Capability unavailable
```

表示 **Business Rule 没有获得足够的 logical evidence 进入可靠执行**。

#### 4.4.4 Dataset Absent vs Explicitly Empty

必须定义：

```
Dataset not included  ≠  Dataset included with zero records
```

**A. Dataset Not Included** —— Manifest **未声明**该 logical dataset role。

表示：当前 Snapshot Package **没有提供这类 evidence**。

**不得自动解释为**「业务上不存在任何记录」。

例如：Inbound Supply dataset not included **不得**解释为 `EffectiveInbound = 0`。

**B. Dataset Explicitly Included, Zero Records** —— Manifest 明确 `dataset included`，
且 `record_count = 0`。

表示：该 package 明确提供了一个 **structurally valid empty dataset**。

是否能解释为「当前不存在该类业务记录」，**必须依据对应 Business Rule / dataset semantics**。

**不得全局统一解释。**

#### 4.4.5 Explicit Empty Semantics（P0 情形）

**Inbound Supply** —— 如果 Inbound Supply dataset = `included` ＋ structurally valid ＋ 0 records，
则可以作为当前 Snapshot Package 中「**没有已提供 inbound records**」的明确 evidence。

对于对应 plant / material，**只有**在 dataset scope 与 mapping **能够可靠覆盖该分析范围**时，
才允许 `CumulativeEffectiveInbound = 0`。

**不得仅凭 `dataset absent` 得到 0。**

**Substitute Relationship** —— 如果 Substitute Relationship dataset = `included` ＋
structurally valid ＋ 0 applicable relationships，**且 scope 可可靠判断**，
则允许依据 `BR-SUBSTITUTE-001`：`ApprovedSubstituteSupply = 0`。

这是 **valid zero**，**不是** `DATA_INCOMPLETE`。

**Substitute Allocation** —— 如果存在 `APPROVED` Substitute Relationship，
则 allocation evidence **必须满足** `BR-SUBSTITUTE-001`。

**不得**把 `allocation record absent` 自动解释成 `AllocatedSubstituteQty = 0` ——
因为已有 Rule 明确 `0 ≠ missing`。

**Supplier Performance** —— `dataset included + 0 records` **不意味着** supplier performance = 0%。

对于被请求的 supplier-material：缺少 required performance evidence
→ Risk capability 对该 grain **不能形成完整风险结论**；
按既有 Rule，`OverallSupplierRisk` 可能为 **`DATA_INCOMPLETE`**。

#### 4.4.6 Capability-to-Evidence Requirement

**注意**：这里的 `REQUIRED` 表示**运行该 capability 所需的 logical evidence role**，
**不表示**某个 physical file 永远必须存在。**不得定义 physical dataset filename。**

**Capability A — Shortage Analysis**

| Evidence role | Requirement |
| --- | --- |
| Plant / Material identity context | `REQUIRED` |
| Production Requirement | `REQUIRED` |
| BOM Component evidence | `REQUIRED` |
| `loss_rate` evidence | `REQUIRED`（owner / grain 仍 `UNKNOWN`） |
| Inventory Snapshot | `REQUIRED` |
| Configured Safety Stock | `REQUIRED` |
| Inbound Supply evidence role | `REQUIRED` |
| Substitute Relationship evidence role | `REQUIRED` —— 必须能**可靠判断**：有 Approved Relationship，或**明确无** Approved Relationship |
| Substitute Allocation | `CONDITIONAL` —— 当存在 Approved Substitute Relationship 且该关系参与当前需求窗口时需要 |
| Supplier Performance | **不要求** |
| Supplier Ranking / Selection | **不要求** |

> `loss_rate` 为 `BR-REQUIREMENT-001` 所必需，但其 **owner / grain 仍 `UNKNOWN`** ——
> 本 Task **不得**因此猜其 carrier。

**Capability B — Procurement Recommendation**

| Evidence role | Requirement |
| --- | --- |
| **Completed Shortage Analysis Outcome** | `REQUIRED` upstream capability result |
| `ApplicableMOQ` | `CONDITIONAL` —— **仅当** `Classification = SHORTAGE` |

**必须区分两种 upstream 情形：**

**A. Shortage Analysis capability 无法运行** —— 例如 required logical evidence role **根本未提供**。

则：

```
Shortage Analysis = capability unavailable
        ↓
Procurement Recommendation 也无法继续执行
```

这是 **Capability Evidence Unavailable**。

**B. Shortage Analysis 已正常执行**，但 Business Rule 结果为 `Classification = DATA_INCOMPLETE`。

这**不是** capability unavailable —— 这是一个**合法的 structured Business Rule Result**。

Procurement Recommendation **必须继承** `BR-PROCUREMENT-001`：

```
Classification = DATA_INCOMPLETE
        ↓
No Numeric Recommendation
```

**不得**将其重新分类成 `Procurement Capability unavailable`。

**Procurement Outcome 对照：**

| `Classification` | 附加条件 | 结果 |
| --- | --- | --- |
| `NORMAL` | — | **not applicable by design** |
| `BUFFER_BREACH` | — | **not applicable by design** |
| `SHORTAGE` | `ApplicableMOQ` valid | **numeric recommendation** |
| `SHORTAGE` | `ApplicableMOQ` missing / invalid | **Business `DATA_INCOMPLETE`** → No Numeric Recommendation |
| `DATA_INCOMPLETE` | — | **Business `DATA_INCOMPLETE`** → No Numeric Recommendation |

**必须保持：**

```
not applicable  ≠  capability unavailable  ≠  DATA_INCOMPLETE
```

**不得**因为没有 `ApplicableMOQ` 把 `NORMAL` / `BUFFER_BREACH` 变成 `DATA_INCOMPLETE`。

**Capability C — Supplier Risk Evidence**

针对明确的 `supplier_id` + `material_code`，至少需要：

| Evidence role | Requirement |
| --- | --- |
| Supplier identity | `REQUIRED` |
| Material identity | `REQUIRED` |
| Supplier-Material Relationship | `REQUIRED` |
| relationship eligibility context | `REQUIRED` |
| `standard_lead_time_days` | `REQUIRED` |
| `PerformancePeriod` | `REQUIRED` |
| `DeliveryPerformance` | `REQUIRED` |
| `QualityPerformance` | `REQUIRED` |
| `RecommendationNeedDate` | `REQUIRED` |
| `AnalysisDate` | `REQUIRED` |
| `PerformanceUpdatedAt` | **不单独决定完整性** |
| Supplier Ranking / Selection | **不要求** |

> **不得**因为缺 `PerformanceUpdatedAt` 自动判 Overall `DATA_INCOMPLETE` ——
> 除非既有 Rule 已要求。

**Capability D — AI Explanation**

AI Explanation **不直接以 raw dataset 存在性替代上游 Business Capability**。

它需要：相关 **upstream structured deterministic result** ＋ **evidence** ＋ **uncertainty state**。

AI Explanation **可以解释两类 structured upstream outcome**：

**A. Business Capability Result** —— 例如 `SHORTAGE` / `BUFFER_BREACH` / `DATA_INCOMPLETE` /
Supplier Risk Result / Procurement Recommendation。

**B. Validation / Capability Readiness Result** —— 例如
`Supplier Risk capability unavailable because Supplier Performance evidence role was not provided.`

在这种情况下，AI **可以**解释：

- 哪个 capability unavailable
- 缺少哪类 logical evidence
- 为什么不能可靠形成业务结论

**但不得：**

- 从 raw data 自行重建缺失结果
- 猜业务事实
- 把 `capability unavailable` 改成 `DATA_INCOMPLETE`
- 把 `DATA_INCOMPLETE` 改成 `capability unavailable`

如果 Shortage Analysis 本身 unavailable，**LLM 不得绕过它**直接从 raw data 自行重建 shortage result。

**Capability E — Procurement Draft Generation**

**只有**存在 **valid Procurement Recommendation** 时，
才允许生成基于该 recommendation 的 Draft。

必须保持：

```
Draft  ≠ Approval  ≠ ERP Purchase Request  ≠ Purchase Order
```

> 本 Task **不设计**完整 HITL。

#### 4.4.7 Required Evidence vs Physical Carrier

Capability Matrix 定义的是 **logical evidence requirement**，**不是 physical file requirement**。

例如：Shortage Analysis requires `loss_rate` evidence，
但 `loss_rate` **physical carrier 仍 `UNKNOWN`**。

**不得**为了让 validation matrix 完整，把它强行放进某 dataset / file。

#### 4.4.8 Scope Coverage Requirement

一个 dataset **即使存在**，也**不自动意味着**它覆盖当前 Analysis Scope。

必须能够判断其 **evidence scope** 是否覆盖当前 `Plant` / `Material` / `Supplier-Material`
或其他相关 grain。

例如：Inbound dataset `included` 但**只覆盖 Plant-B**，
**不能**因此为 Plant-A 推断 `Inbound = 0`。

**如果 coverage 无法可靠判断**：**不得**把「没有匹配记录」解释为**明确的 zero**。

> 具体 physical scope metadata 留给后续 **Import Contract / Master Data Mapping**。

#### 4.4.9 No Silent Exclusion

定义：**Invalid evidence 不得为了让计算继续而被静默丢弃。**

例如：

- Inventory row `inventory_status = UNKNOWN` —— **不得**直接忽略该 row 然后继续输出 `NORMAL`
- Inbound row status invalid —— **不得**直接排除该 PO 并假装结果完整

**只有**已有 Rule 明确判定「该 record **合法但 ineligible**」时才允许正常排除。

例如：

```
Inbound status = CANCELLED  → 合法记录 → EffectiveInbound = 0
Inbound status = UNKNOWN    → 数据无法可靠判断 → DATA_INCOMPLETE
```

两者**必须区分**。

#### 4.4.10 Failure Isolation

Data Quality Issue **默认应尽可能限制 blast radius**。

例如：`Plant-A / MAT-001` 存在 invalid `SafetyStock`，
**不应**自动使 `Plant-B / MAT-999` 也无法分析。

因此 validation 应能够关联：

```
issue → affected evidence → affected business grain → affected capability
```

而**不是**一律 `one bad record → reject whole Package`。

**例外**：如果问题属于 **Package structural integrity**，仍可能 **reject entire Package**。

#### 4.4.11 Cross-Record / Mapping Validation Boundary

本 Task 只定义**原则**：dependent evidence **必须能够可靠解析**到其 canonical identity / grain。

例如：`material_code` unresolved、`plant_id` unresolved、`supplier_id` unresolved、
BOM component unresolved、substitute source / target unresolved、
Supplier-Material relationship unresolved。

**不得**：fuzzy match、LLM match、name similarity mapping、自动改编码。

**处理原则**：affected capability / grain **不得获得正常结果**。

> 详细 Master Data Mapping 留给后续章节。

#### 4.4.12 Grain Conflict Principle

**不得**仅因为出现多条记录就自动认为 duplicate。

是否允许多记录**必须参考对应 Business Rule 与 canonical grain**。

例如：同一 Plant 内多个 Inventory records 可能因**合法 aggregation** 而存在。

但：如果多个记录在 canonical grain 上产生**无法解释的 conflicting values**，
**且当前 Design 没有 aggregation / precedence rule**，**不得**：

- 随机取第一条
- last-write-wins
- sum
- average

应视为 **unresolved data quality issue**，并影响相应 grain 的可靠性。

#### 4.4.13 No Auto-Reconciliation

以下行为**禁止**：

- missing → 0
- invalid → clamp
- unknown status → `AVAILABLE`
- unknown Supplier relationship → eligible
- fuzzy Material mapping
- 自动选最新值
- 自动选最大值
- 自动覆盖 conflicting record

**除非既有 Business Rule 明确允许。**

#### 4.4.14 `required_quantity` Ambiguity Boundary

保持：

```
required_quantity  vs  ProductionQty
= DESIGN PENDING / SEMANTIC AMBIGUITY
```

Data Validation **不得**：判断两者同义、自动互相填充、比较不一致后选其中一个。

`BR-REQUIREMENT-001` **仍使用**：

```
ProductionQty × BOMComponentQty
```

在 ambiguity 正式解决前，`required_quantity` **不得成为替代 `ProductionQty` 的 fallback**。

#### 4.4.15 `loss_rate` Boundary

保持：

```
loss_rate semantic = defined
owner / grain      = UNKNOWN
```

Data Validation **可以**要求：`BR-REQUIREMENT-001` 执行时**必须存在可靠 `loss_rate` evidence**。

**但不得决定** `loss_rate` 来自哪个 Entity / Dataset / Source Field。

#### 4.4.16 Validation Issue Concept

定义 conceptual：**Validation Issue**，用于记录：

- issue category
- affected evidence
- affected canonical grain
- affected capability
- relevant field / relationship
- reason
- referenced Business Rule

**注意**：这只是 **conceptual output**。

**不得设计**：DB table、JSON schema、event schema、logging framework。

#### 4.4.17 Snapshot Validation Report Concept

允许定义 conceptual：**Snapshot Validation Report**。

它应能够回答：

- Package structural result
- 哪些 capabilities **可以可靠运行**
- 哪些 capabilities **evidence unavailable**
- 哪些 business grains **存在 Data Quality Issue**
- 哪些 issues **会导致 `DATA_INCOMPLETE`**
- validation **基于哪个 Snapshot Package**

**必须可追溯到 `snapshot_package_id`。**

**但本 Task 不定义**：report file format、storage、API。

#### 4.4.18 Package Accepted ≠ All Capabilities Ready

必须明确：

```
Package = ACCEPTED
```

**只表示**：Package structural boundary 已通过。

**不代表**：Shortage Analysis ready、Procurement Recommendation ready、
Supplier Risk ready、AI Explanation ready。

一个 Accepted Package **可以**出现：

```
Shortage Analysis = available
Supplier Risk     = unavailable
```

这是**合法状态**。

#### 4.4.19 Capability Unavailable ≠ Package Invalid

例如：Supplier Performance dataset **未包含**在 Package 中。

如果 Package manifest 与实际 artifact **完全一致**：

Package **可以 `ACCEPTED`**，但 Supplier Risk capability **可能 unavailable**。

**不得因此自动 `REJECT` package。**

#### 4.4.20 Business `DATA_INCOMPLETE` Granularity

`DATA_INCOMPLETE` **应尽可能作用于**对应 **business grain / result**。

例如：

```
MAT-A SafetyStock missing  →  MAT-A shortage result → DATA_INCOMPLETE
MAT-B 数据完整             →  仍允许正常计算
```

**不得默认**：一个 material 缺字段 → 整个 analysis run 全部失败。

**除非**共享 evidence 本身使**所有结果**都无法可靠解释。

#### 4.4.21 Valid Zero Preservation

继续继承：

```
0  ≠  missing
```

至少包括：`SafetyStock` / `loss_rate` / `AllocatedSubstituteQty` / `ApplicableMOQ` /
`DeliveryPerformance` / `QualityPerformance`。

**Validation Layer 不得把合法 `0` 转换成 missing / error。**

#### 4.4.22 Valid Absence Preservation

继续继承：

```
valid absence  ≠  missing required evidence
```

例如：

- `FirstShortageDate` not present because **no shortage** —— **不是** validation failure
- Procurement results not produced because `NORMAL` / `BUFFER_BREACH` —— **不是** validation failure

#### 4.4.23 Capability Outcome Examples

以下为 **conceptual examples**。

**Example A — Missing `SafetyStock` field（Business `DATA_INCOMPLETE`，非 capability unavailable）**

| 项 | 值 |
| --- | --- |
| Snapshot Package | `ACCEPTED` |
| Configured Safety Stock evidence role | `included` |
| `Plant-A / MAT-A` | `SafetyStock = missing` |

**Expected：**

- Shortage Analysis capability：**available to execute**
- `BR-SHORTAGE-001` result：**`DATA_INCOMPLETE`**

**不是** `Shortage capability unavailable`。

**Example B — Configured Safety Stock evidence role not provided（Capability Unavailable）**

| 项 | 值 |
| --- | --- |
| Snapshot Package | `ACCEPTED` |
| Configured Safety Stock evidence role | **not provided by Package** |

**Expected：**

- Shortage Analysis：**capability unavailable**

**不得**执行 Rule 之后**伪造** `DATA_INCOMPLETE`。

#### 4.4.24 Validation Scope & Core Principle

Field Validation **只能执行**已经由以下内容明确支持的约束：

```
§2 Business Rules
+
§4.2 Data Dictionary
```

**不得**为了让 validation 更「完整」而新增：

- 默认值
- 新范围
- 新 enum
- 新 requiredness
- source mapping
- aggregation rule
- precedence rule
- business assumption

**原则：**

```
Validate what is defined.
Do not invent what is undefined.
```

本 Task **不得**设计：Cross-Dataset Consistency Rules、Master Data Mapping、Adapter、
Physical Schema、Implementation Validator。

#### 4.4.25 Field-Level Outcome Boundary

Field-level validation issue **默认影响**：

```
affected evidence
+
affected business grain
+
affected capability
```

**不得自动** `reject entire Snapshot Package` ——
**除非**问题属于 **Package Structural Validation**（见 `§4.4.2` Layer 1）。

继续保持：

```
Structural Failure  ≠  Capability Unavailable  ≠  Business DATA_INCOMPLETE
```

#### 4.4.26 Identity Fields

至少覆盖 `plant_id` / `material_code` / `supplier_id`。

**Validation：**

- required when corresponding grain needs identity
- must be present
- must be non-empty as canonical identifier

**但不得定义**：regex、code length、prefix、numeric-only、case normalization、source-system format。

如果 identifier **missing / empty** → affected evidence **unresolved**。

**不得自动生成 ID。**

#### 4.4.27 Analysis Context Fields

**analysis run identity** —— 必须：

- reliably present for Analysis Run
- stable within the same run context

**不得设计**：UUID、generation algorithm、database key。

**`AnalysisDate`** —— 必须：

- be a valid `DATE` / `TIMESTAMP` logical value
- represent analysis context time

**不得自动使用** system current time 补齐 missing `AnalysisDate`。

#### 4.4.28 Requirement / BOM Fields

| Field | Logical Type | Validation |
| --- | --- | --- |
| `ProductionQty` | `NON_NEGATIVE_QUANTITY` | `ProductionQty >= 0` |
| `BOMComponentQty` | `NON_NEGATIVE_QUANTITY` | `BOMComponentQty >= 0` |
| `loss_rate` | `RATIO` | `0 <= loss_rate < 1` |
| `required_date` | `DATE` | valid `DATE` |
| `required_quantity` | — | **仅** parseability（见下） |

`ProductionQty` missing / invalid → `BR-REQUIREMENT-001` **不能形成可靠 result**。

`loss_rate` missing / invalid → Business Rule result → **`DATA_INCOMPLETE`**。

**必须继续保持：**

```
loss_rate owner / grain = UNKNOWN
```

**不得决定 carrier。**

**`required_date`** —— 本 Task **不定义**：planning horizon、past-date rejection、future-date maximum。

**`required_quantity`** —— 保持 `SEMANTIC AMBIGUITY / DESIGN PENDING`。

**不得**：

- 与 `ProductionQty` 比较
- 校验两者必须相等
- 用它 fallback `ProductionQty`
- 推导业务含义

**只允许**验证：如果存在，其 physical / logical parseability ——
且**不能改变其未决 semantic status**。

#### 4.4.29 Inventory Fields

| Field | Validation |
| --- | --- |
| `inventory_snapshot_time` | 必须是有效 temporal value；**不得**自动推断 `AnalysisDate = inventory_snapshot_time` |
| `inventory_status` | 只允许既有 vocabulary：`AVAILABLE` / `INSPECTION` / `FROZEN`；其他值为 invalid / unresolved；**不得** `unknown → AVAILABLE` |
| `on_hand_qty` | 按当前 Dictionary / Rule 已定义的范围校验；**如果当前 Design 未定义更严格范围，不得新增** |
| `SafetyStock` | `NON_NEGATIVE_QUANTITY`；`SafetyStock >= 0` |

**必须区分：**

```
SafetyStock = 0        → valid zero
SafetyStock missing    → DATA_INCOMPLETE
```

#### 4.4.30 Inbound Fields

| Field | Validation |
| --- | --- |
| `ordered_qty` | `>= 0` |
| `received_qty` | `>= 0` |
| `effective_arrival_date` | 必须为有效 `DATE` |
| inbound status | 只允许既有 Rule 已定义的合法 vocabulary |

**本 Task 不得新增：**

```
received_qty <= ordered_qty
```

因为真实业务可能存在 over-delivery / quantity adjustment / source-system semantics，
**且当前 Design 未批准该约束**。

这类关系属于 **Cross-Dataset / Cross-Field Consistency**，后续处理。

**`effective_arrival_date`** —— source field mapping **仍 `DESIGN PENDING`**。

**不得决定**它来自 `promised_date` / `confirmed_date` / `ETA` 等。

**Inbound status** —— 现有 Design 支持：`OPEN` / `CONFIRMED` / `PARTIALLY_RECEIVED` /
`CANCELLED` / `CLOSED` / `COMPLETED`。

如果出现**未定义 status** → invalid / unresolved；**不得 silent drop**。

#### 4.4.31 Substitute Relationship Fields

| Field | Validation |
| --- | --- |
| `target_material_code` | 必须为可靠 canonical identifier；**不得** fuzzy match |
| `substitute_material_code` | 同上 |
| `substitution_ratio` | `RATIO`；必须 `> 0`；missing / invalid 时**不得默认 `1.0`** |
| `approval_status` | 只有 `APPROVED` 可以参与 Approved Substitute Supply |

`PENDING` / `REJECTED` / `UNKNOWN` **不得参与**。

**不得新增**新的 approval status。

#### 4.4.32 Substitute Allocation Fields

`AllocatedSubstituteQty`：

```
NON_NEGATIVE_QUANTITY
>= 0
```

**必须区分：**

```
0        = valid explicit allocation
missing  = cannot assume zero
```

**effective demand context** —— 必须能够**可靠识别**，
但具体 carrier / mapping **仍 `DESIGN PENDING`**。

**不得自行定义**：`demand_window_id` / `requirement_id` / `allocation_period` 等新字段。

#### 4.4.33 Supplier Relationship Fields

`sourcing_status` —— semantic 已知：

```
Supplier-Material relationship eligibility context
```

但：

```
vocabulary = DESIGN PENDING
```

因此 Field Validation **不得建立 enum allowlist**。

如果值存在，**只能**确认：

```
value is present as unresolved source / canonical context
```

**不得判断** `ACTIVE` / `APPROVED` / `QUALIFIED` 等是否有效。

Relationship eligibility **仍需后续 Master Data Mapping / Design**。

#### 4.4.34 Supplier Performance Fields

| Field | Validation |
| --- | --- |
| `standard_lead_time_days` | `>= 0`；missing / invalid → `LeadTimeRisk` → `DATA_INCOMPLETE` |
| `PerformancePeriod` | `REQUIRED`；必须可可靠识别 measurement period |
| `PerformanceUpdatedAt` | valid temporal value when present |
| `DeliveryPerformance` | `PERCENTAGE`；`0% <= value <= 100%` |
| `QualityPerformance` | 同上 |

**本 Task 不定义** `PerformancePeriod` 的具体 vocabulary：`30d` / `90d` / rolling year / fiscal period。

继续保持：`PerformanceUpdatedAt` **不单独决定 `OverallSupplierRisk` completeness**。

**Valid extreme：**

```
DeliveryPerformance = 0%   → valid extreme → DeliveryRisk = HIGH
DeliveryPerformance missing → DATA_INCOMPLETE
```

`QualityPerformance` 同理。

#### 4.4.35 Procurement Input Fields

`ApplicableMOQ`：

```
NON_NEGATIVE_QUANTITY
>= 0
```

**必须：** 只有当 `Classification = SHORTAGE` 时才 `REQUIRED`。

| 情形 | 结果 |
| --- | --- |
| `ApplicableMOQ = 0` | **valid business configuration** |
| `ApplicableMOQ` missing ＋ `SHORTAGE` | **`DATA_INCOMPLETE`** |
| `ApplicableMOQ` 不存在 ＋ `NORMAL` / `BUFFER_BREACH` | **不是 validation failure** |

`RecommendationNeedDate` —— 仅当 **Procurement Recommendation applicable** 时 `CONDITIONAL REQUIRED`。

当前：

```
RecommendationNeedDate = FirstShortageDate
```

但**保持两个 canonical semantics 分离**。

#### 4.4.36 Derived Result Validation

对于 `DERIVED` values：**Validation 不重新计算第二套 business logic**。

**只允许**验证：

- logical type
- presence when applicable
- allowed existing status vocabulary
- traceability to `Rule ID` + `Analysis Run`

**不得**在 Data Validation 层重新定义公式或纠正 deterministic result。

例如：`ShortageQty` **不得**由 validator 自行用其他公式重算后覆盖。

#### 4.4.37 Classification & Risk Vocabulary Validation

**Shortage Classification 只允许：**

```
NORMAL / BUFFER_BREACH / SHORTAGE / DATA_INCOMPLETE
```

**不得新增** `UNKNOWN` / `ERROR` / `UNAVAILABLE` / `NOT_APPLICABLE` 作为 Business Classification。

**`LeadTimeRisk`：**

```
LOW / HIGH / DATA_INCOMPLETE（当既有 Rule semantics 要求时）
```

**不得新增 `MEDIUM`。**

**`DeliveryRisk` / `QualityRisk` / `OverallSupplierRisk`** —— 只允许现有：

```
LOW / MEDIUM / HIGH / DATA_INCOMPLETE
```

**不得新增**其他风险等级。

#### 4.4.38 Conditional Presence Rules

字段 requiredness **必须根据业务状态判断**。至少包括：

| 字段 | 业务状态 | 结论 |
| --- | --- | --- |
| `FirstShortageDate` | `NORMAL` / `BUFFER_BREACH` 且完整计算无 shortage | **valid absence** |
| `FirstShortageDate` | `SHORTAGE` | 必须存在**可靠** `FirstShortageDate` |
| Procurement fields | `NORMAL` / `BUFFER_BREACH` | **not produced by design** |
| Procurement fields | `SHORTAGE` | 按 `BR-PROCUREMENT-001` 判断 applicable inputs / outputs |
| `OverallSupplierRisk` | required dimensions reliable | `LOW` / `MEDIUM` / `HIGH` |
| `OverallSupplierRisk` | 任一 required dimension missing / invalid / unresolved | **`DATA_INCOMPLETE`** |

#### 4.4.39 Valid Zero Rules

统一 Field Validation 规则：以下**合法 `0`** **不得**被标记为 missing / invalid：

- `SafetyStock = 0`
- `loss_rate = 0`
- `AllocatedSubstituteQty = 0`
- `ApplicableMOQ = 0`
- `DeliveryPerformance = 0%`
- `QualityPerformance = 0%`

**注意：** `0` 的**业务后果**仍由对应 Business Rule 决定。

#### 4.4.40 Invalid vs Missing

必须区分：

```
missing
与
present but invalid
```

例如：

```
SafetyStock missing     vs     SafetyStock = -10
```

两者**都可能导致** `DATA_INCOMPLETE`，但 Validation Issue **reason 必须不同**。

**不得统一写成** `missing`。

#### 4.4.41 Unknown Semantic Items

以下项目**不得在本 Task 中推进**：

- `loss_rate` owner / grain
- `required_quantity` semantic
- Warehouse canonical role
- BOM version / validity
- `sourcing_status` vocabulary
- `effective_arrival_date` source mapping
- allocation demand-window mapping
- `ApplicableMOQ` source
- provenance carrier

**Field Validation 不能成为解决这些设计问题的后门。**

#### 4.4.42 No Stringency Inflation

**特别禁止**因为「企业系统通常如此」而新增：

- identifier regex
- date freshness threshold
- inventory age limit
- supplier performance age limit
- decimal precision
- currency
- unit-of-measure conversion
- timezone policy
- quantity rounding
- mandatory text length

如果现有 Design 未定义，写：`NOT DEFINED / DESIGN PENDING`。

#### 4.4.43 Interim Validation Issue Reasons

允许使用**非常有限**的 conceptual reason：

- `MISSING`
- `INVALID_TYPE`
- `OUT_OF_DEFINED_RANGE`
- `INVALID_DEFINED_STATUS`
- `UNRESOLVED_IDENTITY`
- `SEMANTIC_UNRESOLVED`

但**必须标记**为：

```
interim reason categories
```

**不是** Final Validation Issue Taxonomy。

**不得设计**：error code、numeric code、severity ranking、API error object。

#### 4.4.44 Field Validation Examples

以下为 **conceptual examples**。

| # | 输入 | Expected |
| --- | --- | --- |
| **A** | `SafetyStock = 0` | **valid** —— **不是** missing |
| **B** | `SafetyStock = -1` | **field invalid**；affected shortage grain **cannot form normal result** |
| **C** | `DeliveryPerformance = 0%` | **valid percentage**；`DeliveryRisk = HIGH` —— **不是** missing |
| **D** | `DeliveryPerformance = 120%` | **invalid field**；Supplier Risk result **cannot be normal** |
| **E** | `ApplicableMOQ` missing ＋ `Classification = NORMAL` | **valid absence / not applicable** —— **不是** `DATA_INCOMPLETE` |
| **F** | `ApplicableMOQ` missing ＋ `Classification = SHORTAGE` | **Business `DATA_INCOMPLETE`** ＋ **No Numeric Recommendation** |
| **G** | `required_quantity` exists | **不得用它替代 `ProductionQty`**；semantic ambiguity **remains** |

#### 4.4.45 Status Boundary

`Detailed Field Validation` = **`DESIGN RESOLVED`**。

保持：

| 层 | Status |
| --- | --- |
| Cross-Dataset Consistency Rules | `DESIGN PENDING` |
| Validation Issue Taxonomy Finalization | `DESIGN PENDING` |
| Final Data Validation Design | `DESIGN PENDING` |

因此：

```
Data Validation overall = DESIGN PENDING
```

`DESIGN RESOLVED` 的六个层级**仅**表示其 **conceptual boundary 已定义**，
**不表示**：

- cross-dataset consistency rules defined
- validation issue taxonomy finalized
- validator implemented
- data validated
- tested

---

## 5. AI / Tool Boundary

**Backlog:** `VB-28`

**Design Status:** `DESIGN RESOLVED`

**Approval:** Human-approved

**Implementation Status:** `NOT STARTED`

**Validation Source:** `SC-EXPLAIN-001` / Human-approved `SIMULATED` downstream design evidence

> **注意**：`DESIGN RESOLVED` **≠** `IMPLEMENTED` **≠** `TESTED` **≠** `FROZEN` Discovery `H4` resolved。
>
> 本节为 `VB-28` 的 **Canonical Design**。本 Task **未指派** `BR-*` Rule ID —— **不得为了方便自行创建**。

**职责边界状态：**

| 职责 | Status |
| --- | --- |
| LLM | **`DESIGN RESOLVED`** |
| deterministic business logic | **`DESIGN RESOLVED`** |
| Tool | **`DESIGN RESOLVED`** |
| Agent orchestration | **`DESIGN RESOLVED`** |

> 这里的 `DESIGN RESOLVED` **只代表 responsibility / behavioral boundary 已定义**。
>
> **不代表**：framework selected、tools implemented、orchestration implemented、
> prompts implemented、LLM selected、tested、production-ready。

**明确：LLM 不直接自由访问 Production Database。**

> 继承约束（不重新定义）：LLM 获取结构化业务事实必须通过 Controlled Tool（`Data Source → Deterministic Data Tool → Structured Result → LLM`）；不得采用 `LLM → Free-form SQL → Production Database`。

#### 5.0 Design Evidence Record — SC-EXPLAIN-001

| 字段 | 内容 |
| --- | --- |
| Scenario | `SC-EXPLAIN-001` — Shortage Analysis High-frequency Questions |
| Evidence Type | `SIMULATED` |
| Evidence Source | Human-approved |
| Role | Simulated Business Owner ＋ Simulated Procurement / Supply Chain User |
| Purpose | define P0 AI Explanation / User Question boundary |

**必须声明**：该场景

- **不是**云南 CY 集团真实用户访谈；
- **不是** `PUBLIC FACT`；
- **不证明**真实企业的信息解释成本；
- **不修改** `FROZEN` `H4 = TBD`；
- **只**作为模拟 POC 的 **downstream design input**。

该 Scenario 批准以下 **6 类 P0 User Questions** 作为 **`SIMULATED` high-frequency question baseline**。

**不得**描述为真实 CY 企业统计频率。

#### 5.1 Core AI Principle

正式定义：

```
LLM does not create business truth.
```

**LLM 的职责：**

- understand user intent
- request authorized structured facts
- explain deterministic results
- summarize evidence
- surface uncertainty
- generate clearly labeled **Draft** content when allowed

**Deterministic Logic / Controlled Tool 的职责：**

- business facts
- calculations
- classification
- business-rule results
- completeness / missing-data status

必须保持：

```
Facts / Calculation / Classification
  ≠ LLM-generated judgment
```

#### 5.2 Canonical Interaction Flow

定义**概念链路**：

```
User Question
      ↓
LLM / Agent understands intent
      ↓
Authorized Controlled Tool Request
      ↓
Structured Facts
      ↓
Deterministic Business Rules
      ↓
Structured Result + Evidence
      ↓
LLM Explanation
      ↓
Human
```

**禁止**：

```
User Question
      ↓
LLM guesses business facts
      ↓
Answer
```

继续继承：

```
Data Source
      ↓
Deterministic Data Tool
      ↓
Structured Result
      ↓
LLM
```

**不得采用**：

```
LLM
      ↓
Free-form SQL
      ↓
Production Database
```

#### 5.3 P0 Supported Question Baseline

**Q1 — Why is this material short?**

用户意图示例：「为什么这个物料会缺料？」

回答**必须来自** `BR-SHORTAGE-001` 及其**已解析 dependency results**。

可解释：

- `OpeningUsableInventory`
- Effective Inbound
- Approved Substitute Supply
- Gross Requirement
- Safety Stock
- `ProjectedAvailable`
- `FirstShortageDate`
- `ShortageQty`
- `Classification`

LLM **可以**解释计算结果。

**不得**：

- 重新发明计算公式
- 重新计算一套不同结果
- 篡改 deterministic result

**Q2 — Which materials need attention?**

用户意图示例：「现在有哪些物料需要处理？」

**必须基于明确状态过滤**：

- `SHORTAGE`
- `BUFFER_BREACH`
- `DATA_INCOMPLETE`
- `NORMAL`

例如用户明确问：「真正缺料的物料有哪些？」

**只能返回**：

```
Classification = SHORTAGE
```

**不得**将 `BUFFER_BREACH` 描述为**已经缺料**。

如果用户问：「哪些物料需要关注？」

**允许**展示多种状态，但**必须保留状态差异**，**不得**混成一个统一的「缺料」标签。

**Q3 — Why is the recommended purchase quantity X?**

用户意图示例：「为什么建议采购 100？」

**必须引用** `BR-PROCUREMENT-001`，并明确区分：

- `ShortageQty`
- `BasePurchaseNeed`
- `ApplicableMOQ`
- `MOQAdjustmentQty`
- `RecommendedPurchaseQty`

例如：

```
ShortageQty            = 30
RecommendedPurchaseQty = 100
MOQAdjustmentQty       = 70
```

**正确解释**：实际缺口为 `30`；由于 `MOQ = 100`，采购建议被调整为 `100`。

**禁止**：「实际缺料 100。」

**Q4 — Why is this supplier high risk?**

用户意图示例：「这个供应商为什么风险高？」

**必须引用** `BR-SUPPLIER-RISK-001`。

可解释：

- `DaysUntilNeed`
- `StandardLeadTimeDays`
- `LeadTimeRisk`
- `PerformancePeriod`
- `DeliveryPerformance`
- `DeliveryRisk`
- `QualityPerformance`
- `QualityRisk`
- `OverallSupplierRisk`
- Evidence completeness

**不得**进一步自动：

- Supplier Ranking
- Supplier Selection
- recommend a winner
- 修改 `RecommendedPurchaseQty`

**Q5 — Why can't the system give a conclusion?**

用户意图示例：「为什么现在不能给结果？」

当 deterministic result 为 `DATA_INCOMPLETE` 时，**必须展示具体 missing / invalid evidence**。

例如：

- `SafetyStock` missing
- `ApplicableMOQ` missing
- `PerformancePeriod` missing
- Material mapping unresolved
- Supplier-Material Relationship unresolved
- `substitution_ratio` missing

**不得**为了产生「完整回答」而**补值**。

**Q6 — Summarize this shortage case**

用户意图示例：「总结一下这个缺料案例，我接下来要看什么？」

LLM **可以**组织：

```
结论
  ↓
关键数量
  ↓
缺料原因
  ↓
Supplier Risk Evidence
  ↓
Data Quality / Missing Data
  ↓
Purchase Recommendation
  ↓
Human Decision Required
```

但**不得越过**：

- HITL
- Approval
- Write Boundary

#### 5.4 P0 Scope Boundary

必须明确：`VB-28` **并不实现**广义：

```
Natural Language Supply Chain Query
```

P0 **只支持**：围绕**已设计的 P0 deterministic outputs** 进行**受控查询与解释**。

以下仍属于 **P1 / Future scope**，例如：

- arbitrary cross-domain analytics
- unrestricted natural-language enterprise query
- advanced supplier comparison
- broad RAG-based business Q&A
- open-ended optimization

**不得**因为用户可以自然语言提问，就声称 P1 的 Natural Language Query 已完成。

#### 5.5 Standard Explanation Structure

当适用时，P0 Explanation 使用统一**语义结构**：

1. Answer
2. Evidence
3. Uncertainty / Missing Data
4. Human Decision Required

> **注意**：这是 **canonical response meaning**，**不是** API / JSON / UI schema。

**Answer** —— 回答用户的问题；**不得**与 deterministic result **冲突**。

**Evidence** —— 展示支持结论的结构化依据。包括适用的：

- business status
- quantities
- dates
- risk dimensions
- relevant rule result
- evidence completeness

**不得**添加 Tool 未提供、且 Repo 中无正式规则支持的业务事实。

**Uncertainty / Missing Data** —— **必须显式展示**：

- `UNKNOWN`
- missing
- invalid
- `DATA_INCOMPLETE`
- tool failure
- unresolved mapping

**不得隐藏。**

**Human Decision Required** —— 当结果涉及以下内容时：

- Procurement Recommendation
- Draft
- Supplier decision
- approval
- modify / reject / approve
- formal execution

**必须提醒用户**：哪些仍需要 Human 决策。

**不得**将 Recommendation 写成 Approved Decision。

#### 5.6 Evidence Fidelity Rule

定义：

```
LLM may paraphrase evidence,
but may not mutate evidence.
```

例如 Tool 返回 `ShortageQty = 30` —— LLM **不得**回答「约 50 件」。

Tool 返回 `Classification = BUFFER_BREACH` —— LLM **不得**回答「已经缺料」。

Tool 返回 `OverallSupplierRisk = DATA_INCOMPLETE` —— LLM **不得**根据部分 `LOW` evidence
自行宣布 `OverallSupplierRisk = LOW`。

#### 5.7 No Unsupported Fact Rule

核心 fail-safe：

**Tool / deterministic result 没有提供的业务事实，LLM 不得作为事实写入答案。**

**允许**明确说明：

> 「当前证据不足以判断。」

**禁止**以下内容替代缺失业务数据：

- reasonable guess
- likely
- probably
- industry-normal default
- model inference

#### 5.8 Partial Answer Rule

如果只有**部分可靠 evidence**：**允许**回答可靠部分。

**必须同时指出**：哪些结论无法形成。

例如：

```
LeadTimeRisk = HIGH
```

但：

```
PerformancePeriod missing
```

则**可以**解释：Lead Time 已显示 `HIGH` Risk。

但：`OverallSupplierRisk` 仍为 `DATA_INCOMPLETE`。

**不得**因为部分证据可靠就把整体结论**补全**。

#### 5.9 Tool Failure Boundary

如果：

- Controlled Tool unavailable
- timeout
- error
- invalid structured result

则：

**不得**使用模型记忆 / 旧回答代替当前业务事实。

应明确：

```
Current data unavailable
```

或

```
Tool failure
```

并说明：当前**不能可靠回答**哪些部分。

> 本 Task **不定义**：retry implementation、timeout value、circuit breaker、tool framework。
> 这些属于后续 **Architecture / Implementation**。

#### 5.10 Permission Boundary

继承：

```
AI Effective Permission
  = User Permission
  ∩ Data Scope
  ∩ Tool Permission
  ∩ Workflow State
  ∩ POC Policy
```

`VB-28` **不设计** RBAC implementation。

但**必须明确**：Agent / LLM **不得**因为用户自然语言请求**扩大**其 Data Scope 或 Tool Permission。

如果请求**超出当前权限**：**不得获取或泄露数据**。

> 本 Task **不定义**具体 `PERMISSION_DENIED` API contract。

#### 5.11 Out-of-Scope Question Handling

如果用户问题要求当前 P0 **未设计**的能力，例如：

- 「自动帮我选最优供应商」
- 「帮我给供应商排名」
- 「自动把订单下掉」
- 「跨所有企业数据自由分析」
- 「预测未来动态 Lead Time」

AI **不得临时创造规则**。

**必须说明**：该问题**超出当前 P0 已设计能力**，或需要 **Human-approved Future Design**。

#### 5.12 Deterministic / LLM Boundary

以下**不得由 LLM 决定**：

- `Classification`
- `ShortageQty`
- `FirstShortageDate`
- Safety Stock logic
- Substitute eligibility / quantity
- `GrossRequirement`
- `RecommendedPurchaseQty`
- MOQ adjustment
- `LeadTimeRisk`
- `DeliveryRisk`
- `QualityRisk`
- `OverallSupplierRisk`
- `DATA_INCOMPLETE` status
- permission
- approval status

这些来自：

```
deterministic rules
+
structured business facts
```

**LLM 负责**：

- intent understanding
- explanation
- summarization
- user-facing wording
- approved Draft generation

#### 5.13 Agent Orchestration Responsibility

只定义 **conceptual responsibility**，**不得选择 Agent Framework**。

**Agent 可以**：

- identify supported user intent
- determine which authorized business capability is needed
- request required structured result
- combine multiple authorized structured results
- pass structured evidence to LLM for explanation
- stop when required evidence is unavailable

**Agent 不可以**：

- invent Tool capability
- bypass Controlled Tool
- directly query Production DB
- bypass deterministic rule
- expand permissions
- convert missing evidence into facts

#### 5.14 Controlled Tool Responsibility

本 Task **不定义**实际 Tool names / API schema。只定义 **capability boundary**。

Controlled Tool **应负责提供**：

- structured business facts
- deterministic calculation results
- classifications
- relevant evidence
- missing / invalid state

而**不是**让 LLM 从自由文本数据中**自行重建业务计算**。

#### 5.15 Draft Generation Boundary

继承 P0：

**AI 可以**：Generate Procurement Request Draft。

但 Draft **必须基于**：**已取得的 structured deterministic result**。

Draft **必须明确**：

```
DRAFT
```

且：

```
RecommendedPurchaseQty
  ≠ ApprovedPurchaseQty
  ≠ PurchaseOrderQty
```

**LLM 不得**：

- Approve
- Formal Submit
- Create Purchase Order
- Override Human Approval

> 本 Task **不设计** §6 的完整 HITL 状态机。

#### 5.16 Acceptance Examples

以下为 **conceptual examples**。

**Example A — Shortage Explanation**

Structured result：

| 字段 | 值 |
| --- | --- |
| `Classification` | `SHORTAGE` |
| `OpeningUsableInventory` | 20 |
| `CumulativeEffectiveInbound` | 30 |
| `CumulativeApprovedSubstituteSupply` | 0 |
| `CumulativeGrossRequirement` | 80 |
| `ProjectedAvailable` | -30 |
| `FirstShortageDate` | `2026-10-10` |
| `ShortageQty` | 30 |

**Expected AI behavior：** 解释缺料由哪些 deterministic values 形成。

**不得改变** `ShortageQty = 30`。

**Example B — Buffer Breach**

```
Classification = BUFFER_BREACH
ShortageQty    = 0
```

User asks：「是不是已经缺料？」

**Expected：** 明确回答**尚未形成实际 shortage**，当前是 **Safety Stock buffer breach**。

**不得回答**：「是，已经缺料。」

**Example C — Purchase Recommendation**

```
ShortageQty            = 30
ApplicableMOQ          = 100
RecommendedPurchaseQty = 100
MOQAdjustmentQty       = 70
```

**Expected：** 解释**实际缺口 30**；**MOQ 导致建议采购量为 100**。

**不得说**：「实际缺料 100。」

**Example D — Partial Supplier Risk Evidence**

```
LeadTimeRisk        = HIGH
DeliveryRisk        = DATA_INCOMPLETE
QualityRisk         = DATA_INCOMPLETE
OverallSupplierRisk = DATA_INCOMPLETE
```

**Expected：** **允许**解释 Lead Time `HIGH` evidence。

**必须说明**：Overall Risk 尚**无法可靠确定**。

**不得**自动输出 `HIGH` Overall。

**Example E — Missing Data**

```
ApplicableMOQ = missing
```

**Expected：**

- **No Numeric Purchase Recommendation**
- 解释 **MOQ 信息缺失**

**不得**：`ApplicableMOQ = 0`。

**Example F — Unsupported Supplier Selection**

```
Supplier A Risk = LOW
Supplier B Risk = HIGH
```

User asks：「直接帮我选 A 下单。」

**Expected：** **可以**解释两者 Risk Evidence 差异。

**不得**：

- 自动选择 Supplier A
- 批准采购
- 正式下单

**Example G — Tool Failure**

Required controlled capability unavailable.

**Expected：** 明确说明当前**无法取得可靠实时结构化结果**。

**不得**引用旧聊天内容**伪装成当前事实**。

#### 5.17 H4 Relationship

必须记录：`SC-EXPLAIN-001` 提供的是

```
Human-approved SIMULATED
high-frequency question baseline
+
downstream design evidence
```

它支持当前 POC 设计 **AI Explanation capability**。

**但**：`FROZEN` Discovery Validation 中

```
H4 = TBD
```

**保持不变。**

**不得**写成 `H4 = PARTIALLY CONFIRMED`。

未来若正式更新 `H4`：**新的 Validation Version / Addendum ＋ Human Approval**。

> 即：本 Task **不修改** `FROZEN` Validation，**不把设计证据倒写成历史 Discovery 事实**。

#### 5.18 Status Semantics Boundary

本节各项 `DESIGN RESOLVED` **只代表**：

```
responsibility / behavioral boundary 已定义
```

**不代表**：

- framework selected
- tools implemented
- orchestration implemented
- prompts implemented
- LLM selected
- tested
- production-ready

#### 5.19 Source-field / Implementation Boundary

本 Task **只做 Design Boundary**。

因此**不得创建**：

- prompts / system prompts
- code
- tests / evals
- mock API
- tool implementation
- function schema
- JSON contract
- database schema
- UI
- agent graph
- workflow engine
- RAG
- vector DB
- ADR

本 Task **不选择**：

- Agent Framework
- LLM Provider / Model
- Vector Database / RAG Framework
- API Framework
- Tool Protocol / MCP implementation
- database
- deployment stack

---

## 6. HITL Workflow

> 本章节只建立未来需要设计的内容。**不得设计具体状态机。**

未来需要设计：

| 环节 | Status |
| --- | --- |
| Draft | `DESIGN PENDING` |
| Review | `DESIGN PENDING` |
| Modify | `DESIGN PENDING` |
| Approve | `DESIGN PENDING` |
| Reject | `DESIGN PENDING` |
| execution boundary | `DESIGN PENDING` |

> 继承约束（不重新定义）：AI 只能生成 Procurement Request Draft，**不得** Approve / Formal Submit / Create Purchase Order / Override Approval；审批后若 Supplier / Quantity / Price / Delivery Date 发生重大变更，须重新进入 Review / Approval。

> **`VB-29` 建立的硬边界（不改变上表 Status）**：
>
> `Draft` / `Review` / `Modify` / `Approve` / `Reject` **都可以存在**于 POC 内。
>
> 但：
>
> ```
> execution boundary = OUTSIDE POC
> ```
>
> 即 Human 在 POC 内 `Approve` **不等于** Production Execution；
> **不得**自动写入 ERP / 自动创建 PO / 自动提交 Production workflow。
>
> 本节**仍为 `DESIGN PENDING`** —— 完整 HITL state machine **不由 `VB-29` 设计**（见 §3.12）。

---

## 7. Permission & Security

> 本章节只建立未来需要设计的内容。**不得本轮设计实现方案。**

未来需要设计：

| 项 | Status |
| --- | --- |
| RBAC | `DESIGN PENDING` |
| Data Scope | `DESIGN PENDING` |
| Tool Permission | `DESIGN PENDING` |
| Read / Write Boundary | **`DESIGN RESOLVED`** |
| Secret Handling | `DESIGN PENDING` |

**继承：`Human Capability may be greater than Agent Capability`。**

> 继承约束（不重新定义）：`AI Effective Permission = User Permission ∩ Data Scope ∩ Tool Permission ∩ Workflow State ∩ POC Policy`；不得将真实企业 credentials 放入 Git，不得将 secrets 写入 prompt / logs。

> **`VB-29` 只解决 `Read / Write Boundary`（依据 `VR-007` ＋ `VB-29` Human Approval）** ——
> 见 §3 Read / Write / Draft / Failure Boundary。
>
> **其余项仍为 `DESIGN PENDING`**：RBAC / Data Scope / Tool Permission / Secret Handling。
>
> **不得因为 `VB-29` 完成就把整个 §7 标记为完成。**

---

## 8. Audit & Observability

> 本章节只建立未来需要覆盖的范围。

未来需要覆盖：

| 项 | Status |
| --- | --- |
| business decision trace | `DESIGN PENDING` |
| Tool invocation | `DESIGN PENDING` |
| rule version | `DESIGN PENDING` |
| Human approval | `DESIGN PENDING` |
| errors / failures | `DESIGN PENDING` |

---

## 9. Test & AI Eval

> 本章节只建立未来需要区分的测试层次。**不得创建测试代码。**

未来需要区分：

| 层次 | Status |
| --- | --- |
| deterministic unit tests | `DESIGN PENDING` |
| integration tests | `DESIGN PENDING` |
| AI Eval | `DESIGN PENDING` |
| HITL / business acceptance | `DESIGN PENDING` |

---

## 10. Architecture Decisions

重大 Architecture Decision **必须**经过：

```
Options
→ Trade-offs
→ Recommendation
→ Human Approval
→ ADR
```

**至少包含：** **Option 0 — keep current / do nothing**

**当前：`No ADR created yet.`**

---

## 11. Open Design Backlog

> 本节登记并**保留**以下条目。**未经 Human Approval 不得关闭**；`VB-14`、`VB-15`、`VB-16`、`VB-17`、`VB-18`、`VB-27`、`VB-28`、`VB-29` 已获得 Human Approval。

| Backlog ID | 归属 | Status |
| --- | --- | --- |
| `VB-14` | P0 Business Rules（见 §2.1 Shortage Definition）<br>→ **`BR-SHORTAGE-001` / §2.1** | **`DESIGN RESOLVED`** |
| `VB-15` | P0 Business Rules（见 §2.2 Available Inventory / Safety Stock）<br>→ **`BR-INVENTORY-001` / §2.2** | **`DESIGN RESOLVED`** |
| `VB-16` | P0 Business Rules（见 §2.3 Substitute Material）<br>→ **`BR-SUBSTITUTE-001` / §2.3** | **`DESIGN RESOLVED`** |
| `VB-17` | P0 Business Rules（见 §2.4 Scrap / Loss）<br>→ **`BR-REQUIREMENT-001` / §2.4** | **`DESIGN RESOLVED`** |
| `VB-18` | P0 Business Rules（见 §2.5 MOQ / Purchase Recommendation Quantity）<br>→ **`BR-PROCUREMENT-001` / §2.5** | **`DESIGN RESOLVED`** |
| `VB-27` | Supplier Risk / Risk Evidence（见 §2.7）<br>→ **`BR-SUPPLIER-RISK-001` / §2.7** | **`DESIGN RESOLVED`** |
| `VB-28` | AI Explanation / User Questions（见 §5 AI / Tool Boundary）<br>→ **`§5` ＋ `SC-EXPLAIN-001`** | **`DESIGN RESOLVED`** |
| `VB-29` | POC Integration Boundary（见 §3 System Boundary；§7 Read / Write Boundary）<br>→ **`§3` ＋ `§7` ＋ `VR-007` ＋ Human Approval** | **`DESIGN RESOLVED`** |

**已登记但不占用 `VB` 编号的设计项**（`POC Design v0.2` 内部的独立设计项）：

| Design Item | 归属 | Status |
| --- | --- | --- |
| `BR-INBOUND-001` | P0 Business Rules（见 §2.6 Effective Inbound） | **`DESIGN RESOLVED`** |

> **`§2.6 Effective Inbound` 没有独立 `VB` 编号** —— 它是 `POC Design v0.2` 中已经明确登记的设计项。
>
> **不得为了方便自行创建新的 `VB` ID。**

**归属说明：**

- `VB-14` ～ `VB-18` → **P0 Business Rules**
- `VB-27` → **Supplier Risk / Risk Evidence**
- `VB-28` → **AI Explanation / User Questions**
- `VB-29` → **POC Integration Boundary**；设计结论见 **§3 System Boundary** 与 **§7 Read / Write Boundary**；
  下方 `FROZEN` 原定义**仅作为历史 Validation baseline 引用**，**不修改其原始内容**。

> **`VB-29` 的 `FROZEN` 原定义（历史 Validation baseline，逐字引用，未改写）**：
>
> 以下引文**保持原始记录不变** —— 其中 `Current Evidence Status`（`HYPOTHESIS` / `H7`）与
> `Status`（`NOT STARTED`）**属于 `FROZEN` baseline 的历史状态**，
> **不得因为本 PR 已完成 Design Resolution 而改写**。
>
> `FROZEN` 源文件：`docs/discovery/discovery-validation-v0.1.md`
>
> | 字段 | 内容 |
> | --- | --- |
> | ID | `VB-29` |
> | Question | POC 是否可以只读 + 草稿方式接入，无需写入业务系统？ |
> | Current Evidence Status | `HYPOTHESIS`（H7） |
> | Why It Matters | §19 I3；安全边界 |
> | Evidence Needed | 接入边界确认 |
> | Suggested Validation Method | Interface / system assumption confirmation（Simulated） |
> | Owner | Human |
> | Status | `NOT STARTED` |
> | Blocks? | NO |
>
> 本文档**只引用其 ID 与 FROZEN source**，**不自行创造描述**。

---

## Explicit Non-Decisions

当前**明确尚未决定**：

- backend framework
- frontend framework
- Agent framework
- LangGraph usage
- database
- vector database
- cache
- message queue
- deployment platform
- cloud provider
- authentication implementation
- API style
- concrete file format
- Mock API design

**这些不是遗漏。**

它们需要在**后续 Design Task** 中，基于业务规则与实际 Architecture needs 决定。

---

## Document Control

**Document:** POC Design
**Version:** v0.2
**Status:** `DRAFT`
**Phase:** POC Design
**Entry Gate:** `READY`

**继承基线：**

- `docs/discovery/discovery-brief-v0.1.1.md`（`FROZEN`）
- `docs/discovery/discovery-validation-v0.1.md`（`FROZEN`）

- 本文档为 **POC Design 阶段的 Canonical Source**。
- 本文档**不修改、不重新解释**任何 `FROZEN` Discovery 内容。
- 本文档**不包含**任何技术栈选择；**尚未形成**正式的 Architecture Decision 或 ADR。
- 本文档当前**包含**已经 Human-approved、且状态为 `DESIGN RESOLVED` 的 P0 business rules。
- `DESIGN RESOLVED` **不代表** `IMPLEMENTED`，**不代表** `TESTED`，也**不代表** `APPROVED` 或 `FROZEN`。
- **尚未解决**的设计项继续保持 `DESIGN PENDING` / `NOT STARTED`，**不得视为已完成**。
- 本文档**仍未包含**任何 implementation code、Schema、Contract、Mock API 或 Mock Dataset。
- `POC Design v0.2` 当前**仍为 `DRAFT`**。
