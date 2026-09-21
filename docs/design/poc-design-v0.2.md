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
> **当前状态**（`DESIGN RESOLVED`）：`§2.1` `BR-SHORTAGE-001`；`§2.2` `BR-INVENTORY-001`；`§2.3` `BR-SUBSTITUTE-001`；`§2.4` `BR-REQUIREMENT-001`；`§2.5` `BR-PROCUREMENT-001`；`§2.6` `BR-INBOUND-001`（均 Human-approved）。
>
> **仍为 `DESIGN PENDING`**：`§2.7` Supplier Risk / Evidence。

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

**对应：** `VB-27`

**Status:** `DESIGN / VALIDATION PENDING`

`H3` 仍为 `TBD`。

> FROZEN source 中的原问题：风险判断是否依赖个人经验？（`HYPOTHESIS` / `TBD`；关联 `G-06`、`G-11`）

---

## 3. System Boundary

> 本章节只建立结构。**不填入具体技术组件。**

未来需要说明：

| 待说明项 | Status |
| --- | --- |
| POC responsibility | `DESIGN PENDING` |
| external system boundary | `DESIGN PENDING` |
| write boundary | `DESIGN PENDING` |
| failure boundary | `DESIGN PENDING` |

> 继承约束（不重新定义）：Source-system write = `DENIED`；Production write-back = `OUT OF SCOPE`（见 §5 Design Principles → Integration）。

---

## 4. Data & Integration Design

> 本章节只建立未来子章节。当前只写 `DESIGN PENDING`。**不得创建实际 Schema / Contract。**

| 子章节 | Status |
| --- | --- |
| Canonical Data Model | `DESIGN PENDING` |
| Data Dictionary | `DESIGN PENDING` |
| Snapshot / Import Contract | `DESIGN PENDING` |
| Data Validation | `DESIGN PENDING` |
| Master Data Mapping | `DESIGN PENDING` |
| Adapter Boundary | `DESIGN PENDING` |

> 继承约束（不重新定义）：Integration Pattern = **Controlled Export / Snapshot**。具体文件格式（CSV / JSON / Parquet）与 Adapter Contract 属本阶段待设计事项，**本轮未决定**。

---

## 5. AI / Tool Boundary

> 本章节只建立未来需要设计的职责。**不得选择 Agent Framework。**

未来需要设计的职责：

| 职责 | Status |
| --- | --- |
| LLM | `DESIGN PENDING` |
| deterministic business logic | `DESIGN PENDING` |
| Tool | `DESIGN PENDING` |
| Agent orchestration | `DESIGN PENDING` |

**明确：LLM 不直接自由访问 Production Database。**

> 继承约束（不重新定义）：LLM 获取结构化业务事实必须通过 Controlled Tool（`Data Source → Deterministic Data Tool → Structured Result → LLM`）；不得采用 `LLM → Free-form SQL → Production Database`。

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

---

## 7. Permission & Security

> 本章节只建立未来需要设计的内容。**不得本轮设计实现方案。**

未来需要设计：

| 项 | Status |
| --- | --- |
| RBAC | `DESIGN PENDING` |
| Data Scope | `DESIGN PENDING` |
| Tool Permission | `DESIGN PENDING` |
| Read / Write Boundary | `DESIGN PENDING` |
| Secret Handling | `DESIGN PENDING` |

**继承：`Human Capability may be greater than Agent Capability`。**

> 继承约束（不重新定义）：`AI Effective Permission = User Permission ∩ Data Scope ∩ Tool Permission ∩ Workflow State ∩ POC Policy`；不得将真实企业 credentials 放入 Git，不得将 secrets 写入 prompt / logs。

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

> 本节登记并**保留**以下条目。**未经 Human Approval 不得关闭**；`VB-14`、`VB-15`、`VB-16`、`VB-17`、`VB-18` 已获得 Human Approval。

| Backlog ID | 归属 | Status |
| --- | --- | --- |
| `VB-14` | P0 Business Rules（见 §2.1 Shortage Definition）<br>→ **`BR-SHORTAGE-001` / §2.1** | **`DESIGN RESOLVED`** |
| `VB-15` | P0 Business Rules（见 §2.2 Available Inventory / Safety Stock）<br>→ **`BR-INVENTORY-001` / §2.2** | **`DESIGN RESOLVED`** |
| `VB-16` | P0 Business Rules（见 §2.3 Substitute Material）<br>→ **`BR-SUBSTITUTE-001` / §2.3** | **`DESIGN RESOLVED`** |
| `VB-17` | P0 Business Rules（见 §2.4 Scrap / Loss）<br>→ **`BR-REQUIREMENT-001` / §2.4** | **`DESIGN RESOLVED`** |
| `VB-18` | P0 Business Rules（见 §2.5 MOQ / Purchase Recommendation Quantity）<br>→ **`BR-PROCUREMENT-001` / §2.5** | **`DESIGN RESOLVED`** |
| `VB-27` | Supplier Risk / Risk Evidence（见 §2.7） | `NOT STARTED` |
| `VB-28` | AI Explanation / User Questions | `NOT STARTED` |
| `VB-29` | 见下方说明 | `NOT STARTED` |

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
- `VB-29` → 后续根据 `FROZEN` Validation 中的**原定义**映射，**不得猜测或改写其含义**。

> **`VB-29` 的 FROZEN 原定义（逐字引用，未改写）**：
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
