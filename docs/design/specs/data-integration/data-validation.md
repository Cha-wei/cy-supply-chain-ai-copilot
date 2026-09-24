# Data Validation

**Document / Topic:** Data Validation
**Parent Design:** [POC Design v0.2](../../poc-design-v0.2.md)
**Legacy Section:** §4.4（§4.4.1 ～ §4.4.101 编号保留）
**Design Status:** `DESIGN RESOLVED`
**Implementation Status:** 原文未单独登记 implementation 状态；`DESIGN RESOLVED` 仅表示 conceptual validation design complete，不代表 implemented / data validated / tested / production-ready。
**Canonical Authority:** 本文件是 Data Validation concern 的唯一 current canonical source；parent design 保留 navigation/status 入口。
**Migration Base:** `5917cb2fa4b71d4a7379128447bc9e766d17e6da`

<!-- BEGIN MIGRATED LEGACY §4.4 BODY -->
### 4.4 Data Validation —— Capability Readiness & Failure Semantics

> **子章节整体状态：`DESIGN RESOLVED`。**
>
> 本节共 **8 个 design workstream**，经 **Closure Review（PASS）** 后**全部 `DESIGN RESOLVED`**：

| Design Workstream | 覆盖范围 |
| --- | --- |
| Validation Layer Model | `§4.4.1` ～ `§4.4.23` |
| Capability-to-Evidence Requirement | `§4.4.1` ～ `§4.4.23` |
| Failure Semantics | `§4.4.1` ～ `§4.4.23` |
| Dataset Absent vs Empty Semantics | `§4.4.1` ～ `§4.4.23` |
| Failure Isolation Principle | `§4.4.1` ～ `§4.4.23` |
| Detailed Field Validation | `§4.4.24` ～ `§4.4.44` |
| Cross-Dataset / Cross-Field Consistency Rules | `§4.4.45` ～ `§4.4.77` |
| Validation Issue Taxonomy | `§4.4.78` ～ `§4.4.100` |

> **必须区分两个不同概念：**
>
> - **`Validation execution` 是「四层模型」** —— Layer 1 Package Structural Validation /
>   Layer 2 Canonical Evidence Validation / Layer 3 Capability Readiness Validation /
>   Layer 4 Deterministic Business Rule（见 `§4.4.2`）
> - **设计工作流是「8 个 workstream」** —— 见上表
>
> **不得**把「four validation layers」与「8 design workstreams」混为一谈。

**层级状态登记：**

| 层 | Status |
| --- | --- |
| Validation Layer Model | **`DESIGN RESOLVED`** |
| Capability-to-Evidence Requirement | **`DESIGN RESOLVED`** |
| Failure Semantics | **`DESIGN RESOLVED`** |
| Dataset Absent vs Empty Semantics | **`DESIGN RESOLVED`** |
| Failure Isolation Principle | **`DESIGN RESOLVED`** |
| Detailed Field Validation | **`DESIGN RESOLVED`** |
| Cross-Dataset Consistency Rules | **`DESIGN RESOLVED`** |
| Validation Issue Taxonomy Finalization | **`DESIGN RESOLVED`** |
| Final Data Validation Design | **`DESIGN RESOLVED`** |

> **`Data Validation` overall = `DESIGN RESOLVED`。**
>
> `DESIGN RESOLVED` **只**表示 **conceptual validation design complete** ——
> **不代表** implemented / data validated / tested / production-ready。

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
| `loss_rate` evidence | `REQUIRED`（owner / grain = **`Requirement Calculation Context`**；**§4.5.22**） |
| Inventory Snapshot | `REQUIRED` |
| Configured Safety Stock | `REQUIRED` |
| Inbound Supply evidence role | `REQUIRED` |
| Substitute Relationship evidence role | `REQUIRED` —— 必须能**可靠判断**：有 Approved Relationship，或**明确无** Approved Relationship |
| Substitute Allocation | `CONDITIONAL` —— 当存在 Approved Substitute Relationship 且该关系参与当前需求窗口时需要 |
| Supplier Performance | **不要求** |
| Supplier Ranking / Selection | **不要求** |

> `loss_rate` 为 `BR-REQUIREMENT-001` 所必需；其 **canonical owner / grain 已为 `DESIGN RESOLVED`**
> （owner = **exact Requirement Calculation Context**；**§4.2.4** ／ **§4.5.22**）——
> 但 **physical carrier 仍 `SOURCE-SPECIFIC` / not yet defined**，**不得**因此猜其 carrier。

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
但 `loss_rate` **physical carrier 仍 `SOURCE-SPECIFIC` / not yet defined**。

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

#### 4.4.14 `required_quantity` Removal Boundary

```
required_quantity = REMOVED FROM CURRENT POC v0.2 CANONICAL MODEL
```

`required_quantity` **不属于**当前 canonical model，因此：

- **不是** Data Validation 的当前字段
- **不进入** `validate` / `map` / `missing` / `type` / semantic resolution 范围
- **不得**作为 `ProductionQty` 的 fallback 或 alias

`BR-REQUIREMENT-001` 继续只使用：

```
ProductionQty × BOMComponentQty
```

> 历史上针对该 ambiguous 字段的禁止性 wording 已随字段移除而**不再适用**；
> 移除依据见 **§4.2.4**（PR #38 Human Decision ＋ Human Decision Record ＋
> **Required Quantity Removal Implementation Record**）。

#### 4.4.15 `loss_rate` Boundary

现行状态（**Option E semantic synchronization 已实施**）：

```
loss_rate semantic             = defined
canonical owner / grain        = DESIGN RESOLVED
owner / applicability context  = Requirement Calculation Context
resolution contract            = exactly one applicable loss_rate or unresolved
physical carrier               = SOURCE-SPECIFIC / not yet defined
```

Data Validation **可以**要求：`BR-REQUIREMENT-001` 执行时**必须存在可靠 `loss_rate` evidence**。

**但不得决定** `loss_rate` 来自哪个 Entity / Dataset / Source Field ——
physical carrier **仍是独立设计问题**（**logical provenance carrier = `DESIGN RESOLVED`**；physical realization 仍属 **§4.3**）。

**必须区分 root condition：**

| Root condition | 判定 | 结果 |
| --- | --- | --- |
| **A** context 已可靠解析，但 required `loss_rate` value **missing** | `FIELD_VALUE` ／ `MISSING` | `DATA_INCOMPLETE` |
| **B** `loss_rate` evidence 存在，但**无法可靠确定哪个适用于当前 Requirement Calculation Context** | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE` |
| **C** applicable `loss_rate` 已可靠解析，但 `loss_rate < 0` 或 `loss_rate >= 1` | 继承既有 field / range invalid handling | `DATA_INCOMPLETE` |

**不得**把三者全部描述为 `loss_rate missing`。

> **Human Decision Record** 与 **Option E Implementation Record** 见 **§4.5.22**。

#### 4.4.16 Validation Issue Concept

定义 conceptual：**Validation Issue**，与 **Final Taxonomy**（`§4.4.78` ～ `§4.4.100`）**一致**，至少要求：

| Dimension | 说明 |
| --- | --- |
| Issue Category | 8 个 canonical category 之一（`§4.4.80`） |
| Reason | 12 个 canonical reason 之一（`§4.4.81`） |
| Affected Evidence | 受影响 evidence |
| Affected Grain | affected canonical grain |
| Affected Capability | affected capability |
| Relevant Field / Relationship | 相关 field / relationship |
| Source Rule / Design Reference | 来源 Rule / Design 引用 |
| Blast Radius / Affected Scope | 影响范围（**非** severity） |
| Consequence Context | 后果落在哪一层 |

如果 applicable，还应能够追溯 `Snapshot Package` 与 `Analysis Run`。

**注意**：这只是 **conceptual output**。

**不得设计**：DB table、JSON schema、event schema、logging framework。

**不得引入**：error code、severity ranking、owner、assignee、ticket status ——
这些属于后续 **implementation / operations**。

#### 4.4.17 Snapshot Validation Report Concept

允许定义 conceptual：**Snapshot Validation Report**，并**引用 Final Taxonomy**（`§4.4.78` ～ `§4.4.100`）。

它应能够回答：

- Package structural issues
- capability readiness issues
- data quality issues
- affected grains
- affected capabilities
- **reason category**（canonical category ＋ reason）
- **source Rule / Design reference**
- resulting **consequence context**

**必须可追溯到 `snapshot_package_id`。**

**但本 Task 不定义**：report schema / format、storage、API。

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

`ProductionQty` missing / invalid → `BR-REQUIREMENT-001` **不能形成可靠 result**。

`loss_rate` missing / invalid → Business Rule result → **`DATA_INCOMPLETE`**。

**现行状态（Option E 实施后）：**

```
loss_rate canonical owner / grain = DESIGN RESOLVED
owner / applicability context     = Requirement Calculation Context
resolution contract               = exactly one applicable loss_rate or unresolved
```

**不得决定 carrier** —— physical carrier 仍 **`SOURCE-SPECIFIC` / not yet defined**
（见 **§4.5.22 Option E Implementation Record**）。

**`required_date`** —— 本 Task **不定义**：planning horizon、past-date rejection、future-date maximum。

**`required_quantity`** —— **已从 current canonical model 移除**（**§4.4.14**）：
它**不是**本层的 validation target，**不得**与 `ProductionQty` 比较 / 校验相等 /
fallback / 推导业务含义（**§4.2.4**）。

历史上针对该字段的「仅 parseability」例外**已随字段移除而失效** ——
**不得**因为该字段名在历史 source 数据中出现就为其重建 semantic 或 validation 位置。

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

**跨字段关系（已由既有 Rule 定义，本层不重复实现）：**

```
received_qty <= ordered_qty
```

该约束**已经**由 **`BR-INBOUND-001` / `§2.6.2`** 明确定义：

```
RemainingInboundQty = ordered_qty - received_qty
要求 RemainingInboundQty >= 0
```

因此 `received_qty > ordered_qty` 已被既有 Business Rule 定义为
**`DATA_INCOMPLETE`** ＋ **Data Quality Issue**；`§4.2.6` Data Dictionary 也已同步记录。

但它是 **cross-field consistency rule** ——
本 **Detailed Field Validation** Task **不重复实现**其 validation enforcement；
将在后续 **Cross-Dataset / Cross-Field Consistency** 设计中**正式登记与执行**。

> **重要边界**：这是 **recognize existing approved rule ＋ defer its validation enforcement
> to the correct validation layer** —— **不是**新增 constraint。
>
> ```
> 已定义 Business Rule  ≠  本 Task 新增 constraint
> ```

**`effective_arrival_date`** —— **canonical mapping contract = `DESIGN RESOLVED`**
（见 **§4.2.6** ／ **§4.5.21**）；**source mapping = `SOURCE-SPECIFIC` / Adapter-defined**。

**不得**把 `promised_date` / `confirmed_date` / `ETA` 等中的**任何一个**声明为**全局 source**；
**不得**建立 global source-field precedence。

Field validation **只**要求：进入本 Rule 前 `effective_arrival_date` 已是
**exactly one resolved** 或 **unresolved**（见 **§4.4.49**）。

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

**effective demand context** —— **canonical demand-window mapping contract = `DESIGN RESOLVED`**
（**§4.5.9**）；必须能够**可靠识别**，且必须可靠回答两个 relation：

```
Target Applicability         （applicable / not applicable / unresolved）
Source Reservation Overlap   （overlaps / does not overlap / unresolved）
```

**具体 source evidence = `SOURCE-SPECIFIC` / Adapter-defined**。

**不得自行定义**：`demand_window_id` / `requirement_id` / `allocation_period` / `valid_from` / `valid_to`
等新字段；也**不得**创建 persisted applicability / overlap field。

#### 4.4.33 Supplier Relationship Fields

`sourcing_status` —— semantic 已知：

```
Supplier-Material relationship eligibility context
```

**当前状态（PR #33 实施后）：**

```
source vocabulary                      = SOURCE-SPECIFIC / Adapter-defined
canonical eligibility mapping contract = DESIGN RESOLVED
```

因此 Field Validation **不得建立 enum allowlist**。

如果值存在，**只能**确认：

```
value is present as source-specific eligibility evidence context
```

**不得判断** `ACTIVE` / `APPROVED` / `QUALIFIED` 等是否有效
（**不得**因为缺少全局 vocabulary 就判定无效）。

Relationship eligibility 由 **`source value → eligibility condition`** 的
**explicit deterministic mapping evidence** 决定；
若当前 capability 需要该 relationship 而该 mapping **无法可靠完成** →
`SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED`（见 **§4.4.62** / **§4.4.95**）。

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

以下项目**不得在本 Task 中推进**
（`Warehouse canonical role` 已于 **§4.5.12**、`BOM version / validity` 已于 **§4.5.7** ／ **§4.1.4 N**、
`sourcing_status` vocabulary 已于 **§4.5.11**、`effective_arrival_date` source mapping 已于 **§4.5.21**、
allocation demand-window mapping 已于 **§4.5.9** 解析，此处保留历史约束记录）：

- `loss_rate` owner / grain —— **已由 §4.5.22 Option E Implementation Record 解析**（当时本 Task 未推进；解析由后续 **Human-authorized Design Change** 实施）
- `required_quantity` semantic —— **已由 PR #38 Human Decision 认定为 `ORPHAN CANONICAL FIELD` 并移除该字段**（当时本 Task 未推进；移除由后续 **Human-authorized Design Change** 实施）
- Warehouse canonical role —— **已由 §4.5.12 解析**（本 Task 未推进）
- BOM version / validity —— **已由 §4.5.7 ／ §4.1.4 N 解析**（本 Task 未推进）
- `sourcing_status` vocabulary —— **已由 §4.5.11 解析**（本 Task 未推进）
- `effective_arrival_date` source mapping —— **已由 §4.5.21 解析**（本 Task 未推进）
- allocation demand-window mapping —— **已由 §4.5.9 解析**（本 Task 未推进）
- `ApplicableMOQ` source —— **已由 §4.5.22 Option D Implementation Record 解析**（当时本 Task 未推进；解析由后续 **Human-authorized Design Change** 实施）
- provenance carrier —— **logical provenance carrier 已由 §4.5.22 Option D Implementation Record 解析**（**Layered Logical Provenance Contract**，`DESIGN RESOLVED`；当时本 Task 未推进，解析由后续 **Human-authorized Design Change** 实施）；**physical carrier realization** 仍属 **§4.3** 后续 design（**`DESIGN PENDING`**）

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

#### 4.4.43 Validation Issue Reason Seed → Superseded by Final Taxonomy

> **状态：本小节原「interim reason categories」已被 `§4.4.81 Final Canonical Reason Set` 取代（superseded）。**

本 Task Finalize 后，**authoritative taxonomy 只有一个** ——
即 **`§4.4.78` ～ `§4.4.100`** 定义的 **POC Validation Issue Taxonomy**。

`§4.4.81` 的 12 个 canonical reason **包含并扩展**了本小节最初的 6 个 seed reason：

| 原 interim seed | 在 Final Taxonomy 中的归属 |
| --- | --- |
| `MISSING` | `FIELD_VALUE` / `MISSING` |
| `INVALID_TYPE` | `FIELD_VALUE` / `INVALID_TYPE` |
| `OUT_OF_DEFINED_RANGE` | `FIELD_VALUE` / `OUT_OF_DEFINED_RANGE` |
| `INVALID_DEFINED_STATUS` | `FIELD_VALUE` / `INVALID_DEFINED_STATUS` |
| `UNRESOLVED_IDENTITY` | `IDENTITY_RESOLUTION` / `UNRESOLVED_IDENTITY` |
| `SEMANTIC_UNRESOLVED` | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED` |

**新增**（seed 未覆盖）：`STRUCTURAL_INCONSISTENCY` / `EVIDENCE_ROLE_NOT_PROVIDED` /
`UNRESOLVED_SCOPE` / `CONSISTENCY_CONFLICT` / `PROVENANCE_MISMATCH` /
`PROVENANCE_UNRESOLVED`。

> **本小节不再构成第二套 canonical list。**
> 引用时应指向 **`§4.4.81`**，而**不是**本小节。

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
| **G** | `required_quantity` exists（**历史字段**） | **已由 PR #38 Human Decision 移除该字段**（**§4.2.4**）；**不得用它替代 `ProductionQty`** |

#### 4.4.45 Core Principle

定义：

```
一个字段通过 Field Validation，
不代表它与其他 evidence 一致。
```

例如：

```
ordered_qty  = 100
received_qty = 120
```

两个字段**分别**满足 `>= 0`，但**组合**违反 `BR-INBOUND-001` / `§2.6.2`。

因此 **Cross-Field Consistency 必须独立检查**。

但：**不得借此新增**现有 Design 不支持的新业务关系。

```
Field Valid  ≠  Business Evidence Consistent
```

#### 4.4.46 Existing Rule vs New Rule Boundary

本 Task **只能正式登记**已经由以下内容支持的 consistency invariant：

- `§2` Business Rules
- `§4.1` Canonical Data Model
- `§4.2` Data Dictionary
- `§4.3` Snapshot Boundary
- `§4.4` 已有 Validation Design

如果某关系**当前没有可靠 Design**，**必须标记** `DESIGN PENDING` 或 `SEMANTIC_UNRESOLVED`。

**不得自行补齐。**

#### 4.4.47 Inbound Quantity Consistency

正式登记既有规则 `BR-INBOUND-001` / `§2.6.2`：

```
RemainingInboundQty = ordered_qty - received_qty
要求 RemainingInboundQty >= 0
```

因此必须满足：

```
received_qty <= ordered_qty
```

如果 `received_qty > ordered_qty`：

**处理：** Business **`DATA_INCOMPLETE`** ＋ **Data Quality Issue**

**不得**：

- clamp to 0
- 自动解释为 over-delivery
- 修改 `ordered_qty`
- 修改 `received_qty`

> **注意**：这是**已有 Business Rule enforcement**，**不是**本 Task 新增 constraint。

#### 4.4.48 Inbound Identity Consistency

Inbound evidence 必须能够可靠关联到 `plant_id` ＋ `material_code`，
且必须与当前被分析的 **Plant / Material grain 一致**。

**不得**：

- 将 Plant-B inbound 用于 Plant-A
- 将 unresolved material 自动归给当前 material
- fuzzy match
- LLM guess

如果 mapping 无法可靠确定 → affected grain → **`DATA_INCOMPLETE` / Data Quality Issue**。

但具体 `source code → canonical code` 映射规则仍属于 **Master Data Mapping**，本 Task **不设计**。

#### 4.4.49 Inbound Date Relationship Boundary

必须区分：

```
valid but ineligible
与
inconsistent / invalid
```

例如：

```
effective_arrival_date > required_date
```

这是 **合法 Inbound record**，但当前 `required_date` 前**不可计入 supply**。

**不是** Data Quality Issue。

因此**不得**将其错误标记为 `invalid record`。

**只有** `effective_arrival_date` 本身不可用才按既有 Rule → **`DATA_INCOMPLETE`**。

**`effective_arrival_date` 在进入本 Rule 之前必须已经：**

```
exactly one resolved
    或
unresolved
```

（**source semantic resolution 发生在 deterministic business rule 之前** ——
见 **§4.5.21** 与 **§4.2.6**。）

**三类 root condition：**

| # | Root condition | Validation Reason | Business consequence |
| --- | --- | --- | --- |
| **A** | resolved 且为合法 `DATE` | 无 Issue | 正常参与 date boundary 判断 |
| **B** | approved mapping 已存在，但 mapped value **missing / invalid** | `MISSING` / `INVALID_TYPE` | `DATA_INCOMPLETE` |
| **C** | source date evidence 存在，但 **mapping 无法可靠完成** | `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE`（当该 inbound 为 capability 所需时） |

**Date Difference Boundary：**

```
promised_date  ≠  expected_arrival_date
```

**本身不是** `CONSISTENCY_CONFLICT`、**不是** Data Quality Issue，**也不是** invalid evidence ——
因为两者可能具有**不同 business semantic**。

**只有**未来某个 **approved source-specific mapping contract** 明确声明某 consistency relation，
且该 relation **被违反**时，才可以产生对应 Validation Issue。
**本 Task 不发明该 relation。**

#### 4.4.50 Inventory Plant / Scope Consistency

继承 `BR-INVENTORY-001`。

- **同 Plant 内**：允许聚合被纳入当前 POC Inventory Scope 且符合状态要求的 inventory records
- **不同 Plant**：**不得自动聚合**

如果存在 Warehouse context，必须能够可靠判断：`warehouse ownership` ＋ 所属 `Plant` ＋
是否位于当前 POC Inventory Scope。

如果无法可靠判断 → affected inventory grain → **`DATA_INCOMPLETE` / Data Quality Issue**。

**并保持既有结论（`Warehouse canonical role` 已由 §4.5.12 解析）：**

```
Warehouse canonical role = source / mapping / scope context
```

**不得**创建新的 Warehouse canonical entity 或 physical key；
也**不得**因为 consistency validation 改变既有 Plant-level calculation grain。

#### 4.4.51 Configured Safety Stock Grain Consistency

Configured Safety Stock 的既有 grain：

```
plant_id + material_code
```

因此用于 Shortage Analysis 的 `SafetyStock` 必须与当前 **Plant ＋ Material** 分析 grain 一致。

**不得**：

- 跨 Plant 使用 `SafetyStock`
- 用 MAT-B `SafetyStock` 代替 MAT-A
- 自动使用其他记录 fallback

如果在**同一 canonical grain** 出现多个**互相冲突**的 `SafetyStock` 值，
**且没有既有 precedence rule**，**不得**：

- first wins
- latest wins
- max
- min
- average

应视为 **unresolved data quality conflict**，并影响该 grain 的可靠性。

#### 4.4.52 Production Requirement / BOM Consistency

继承 `BR-REQUIREMENT-001`。

Production Requirement 必须能够追溯到：

```
Production Requirement
+
reliably resolved applicable BOM relationship
```

用于计算的 BOM Component relationships **必须属于同一个 Production Requirement context**，
且 applicability anchor **`required_date` 必须一致**。

```
Production Requirement context
  = plant_id
  + parent / requirement material_code
  + required_date
```

**不得**：requirement `R1` 使用 `R2` 的 BOM Component relationship。

如果出现以下任一情况：

- BOM relationship unresolved
- component Material unresolved
- Plant context inconsistent
- **BOM Component relationship 不属于当前 Production Requirement context**
- **applicability anchor `required_date` 不一致**
- **applicable BOM definition 不唯一（zero 或多个）且无 approved applicability evidence**

则：`Gross Requirement` → **`DATA_INCOMPLETE`**。

**不得**：

- 猜 BOM
- 选任意 BOM
- 自动选最新 BOM
- fuzzy match component
- first wins / latest wins / highest version / lowest version / newest update / LLM choose
  （多个 applicable definition 竞争时）

**已解析（Human-authorized Canonical Model Amendment，PR #30 ／ Option A）：**

```
BOM version / validity selection = DESIGN RESOLVED
  → requirement-scoped BOM applicability（见 §4.1.4 N / §4.5.7）
```

**Cross-Requirement Reuse Boundary：**

即使 `Plant` / `Parent Material` / `Component Material` **完全相同**，
不同 `required_date` 的 Production Requirement context **不得默认共享** `BOMComponentQty`。

只有 mapping evidence **独立证明**相同 BOM definition 对两个 requirement context **均 applicable**，
才能得到相同 quantity。**不得**通过 `copy previous` / `latest wins` / `cache reuse` 自行推导。

**Applicability anchor（`SIMULATED POC Design Policy` ＋ `Human-approved`）：**

```
Production Requirement.required_date
```

**不得**用 Snapshot creation time / Package export time / `AnalysisDate` /
system current time **替代**。

#### 4.4.53 `required_quantity` Removal Boundary

```
required_quantity = REMOVED FROM CURRENT POC v0.2 CANONICAL MODEL
```

该字段**不再存在**于当前 canonical model，因此本层**不再**：

- 对其做 cross-field consistency
- 创建 cross-field mismatch rule
- 把它作为 `ProductionQty` 的比较对象

`BR-REQUIREMENT-001` 继续只使用：

```
ProductionQty × BOMComponentQty
```

> 移除依据（**`ORPHAN CANONICAL FIELD`**）见 **§4.2.4** ——
> **PR #38** Review Finding ＋ Human Decision Record ＋ **Required Quantity Removal Implementation Record**。

#### 4.4.54 `loss_rate` Boundary

Cross-Dataset Consistency **要求**：
`BR-REQUIREMENT-001` 所使用的 `loss_rate` evidence 必须能够**可靠关联到当前计算上下文**。

现行状态（**Option E semantic synchronization 已实施**）：

```
loss_rate canonical owner / applicability context = Requirement Calculation Context
resolution contract                              = exactly one applicable loss_rate
                                                   or unresolved
physical carrier                                 = still DESIGN PENDING / source-specific
```

`Requirement Calculation Context` 的 **applicability grain** **至少**区分：

```
plant_id
+ parent / requirement material_code
+ required_date
+ component material_code
```

因此**不得定义**它必须来自 `Material` / `BOM Component` / `Plant-Material` /
`Production Requirement` 中的**任何一种 persisted entity** ——
它**不是**上述任何 entity 的 attribute。

**必须区分 root condition（不得统一写成 `loss_rate missing`）：**

| Root condition | 判定 | 结果 |
| --- | --- | --- |
| **A** context 已可靠解析，但 required `loss_rate` value **missing** | `FIELD_VALUE` ／ `MISSING` | `DATA_INCOMPLETE` |
| **B** evidence 存在，但**无法可靠确定哪个适用于当前 Requirement Calculation Context** | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE` |
| **C** applicable `loss_rate` 已解析，但 `loss_rate < 0` 或 `loss_rate >= 1` | 继承既有 field / range invalid handling | `DATA_INCOMPLETE` |

**无法可靠关联 → `DATA_INCOMPLETE`**；**不创建任何 precedence** ——
多 candidate 无法唯一解析时结果为 **`unresolved`**，而**不是**自动选择。

> **Human Decision Record** 与 **Option E Implementation Record** 见 **§4.5.22**；
> physical carrier 仍由 **`provenance carrier`** 独立承担。

#### 4.4.55 Substitute Relationship Consistency

Substitute Allocation 必须对应一个**可可靠识别的 Substitute Relationship**。

参与 Approved Substitute Supply 时，该 Relationship 必须满足既有：

```
approval_status = APPROVED
```

**不得**出现 `Allocation exists but no corresponding relationship` 然后仍然计入 Supply。

如果 relationship unresolved → affected substitute calculation → **`DATA_INCOMPLETE`**。

**不得自动创建 relationship。**

#### 4.4.56 Substitute Source / Target Identity

每个 Substitute Relationship / Allocation 必须能够可靠解析：`target material` /
`substitute material` / `plant context`，并保持：

```
substitute → target
```

方向。

**不得反转** `target → substitute`。

**不得**因为两个 Material 都存在就推断它们可替代。

#### 4.4.57 Substitute Same-Plant Consistency

继承 `BR-SUBSTITUTE-001`：Target Material 与 Substitute Supply 当前 POC 必须 **same plant**。

如果：

```
Target             = Plant-A
Substitute Inventory = Plant-B
```

**不得直接计入。**

这不表示 Plant-B data **invalid**。

它表示：**该 supply 对当前 Plant-A substitute calculation 不可作为有效供给**。

**不得自动设计** cross-plant transfer。

#### 4.4.58 Substitute Allocation vs Eligible Supply

继承 `BR-SUBSTITUTE-001` / **No Double Allocation**。必须满足：

```
Σ AllocatedSubstituteQty <= EligibleSubstituteSupply
```

并保持：

```
RemainingUnallocatedSourceSupply = EligibleSubstituteSupply - Σ AllocatedSubstituteQty
RemainingUnallocatedSourceSupply >= 0
```

如果违反：**`DATA_INCOMPLETE`** ＋ **Allocation Conflict**

**不得**：

- silently over-allocate
- clamp
- priority resolve
- 自动减少某 allocation

**Same Effective Reservation Context（PR #36 Human-approved clarification）**

```
Σ AllocatedSubstituteQty <= EligibleSubstituteSupply
```

的 approved interpretation 是 **within the same effective reservation context** ——
**不是** all historical allocations **forever accumulated**。

> 这是 **Human-approved clarification**，**不是** Business Rule semantic change；
> `§2.3.10` 正文**未修改**（见 **PR #36 Human Decision**）。

**三条 Validation 路径：**

| # | 情形 | 处理 |
| --- | --- | --- |
| **A** | explicit allocation ＋ mapping **resolved** ＋ applicable / overlap relation **reliable** | **正常继续计算** —— 在**同一有效 reservation context** 内判断 conservation |
| **B** | allocation **exists**，但 demand-window semantic mapping **unresolved** | `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED` → capability 需要时 `DATA_INCOMPLETE` |
| **C** | mapping **已可靠解析**，且在同一 effective reservation context **真实发生** over-allocation | `CONSISTENCY` / `CONSISTENCY_CONFLICT` → `DATA_INCOMPLETE` |

**Multiple Contexts Example：**

```
Eligible MAT-B Supply = 100
  Allocation A1：60 → MAT-A    （Reservation Context W1）
  Allocation A2：50 → MAT-C    （Reservation Context W2）
```

| Case | 情形 | Expected |
| --- | --- | --- |
| **A** | `W1` overlaps `W2` | `60 + 50 = 110 > 100` → `CONSISTENCY` / `CONSISTENCY_CONFLICT` → `DATA_INCOMPLETE` |
| **B** | `W1` does not overlap `W2` | **不得**仅因 `60 + 50 > 100` 就宣布 over-allocation；必须**分别**在各自有效 reservation context 内判断 conservation |
| **C** | `W1` vs `W2` overlap **unresolved** | `SEMANTIC_UNRESOLVED` → `DATA_INCOMPLETE`；**不得**自动视为 overlap，也**不得**自动视为 not overlap |

**Example G 的 downstream 解释（`§2.3.13` 正文未修改）：**

`§2.3.13` Example G（`60 → MAT-A` ＋ `50 → MAT-C`，`110 > 100` → `INVALID`）
应理解为：这些 allocations **处于同一 effective reservation context**，
或 **overlap 已可靠成立** 的情况。

**不得**把 Example G 解释为「任何不同时间 context 的 `60 + 50` 都自动 conflict」。
这是 **PR #36 已批准的 `§2.3.10` clarification**，**不是修改 `§2`**。

本 Task **不设计** allocation algorithm / timing engine / consumption engine。

#### 4.4.59 Substitute Supply Eligibility Consistency

Allocated substitute source supply 只能来自：

```
same Plant
+
BR-INVENTORY-001 判定为 AVAILABLE 的 Substitute Inventory
```

**不得自动使用**：`INSPECTION` / `FROZEN` / Future Substitute Inbound / Cross-Plant Inventory。

**不得**因为 source inventory record 存在就认为它 **automatically eligible**。

#### 4.4.60 Allocation Demand-Window Consistency

已有 Rule 要求：allocation 必须能够**可靠关联当前需求窗口**。

**当前状态（PR #36 Human-approved Option B）：**

```
canonical demand-window mapping contract = DESIGN RESOLVED
concrete source evidence                 = SOURCE-SPECIFIC / Adapter-defined
```

**必须形成三条清晰路径（不得创建新的 Validation Reason）：**

**A. mapping resolved 且 applicable / overlap relation reliable**

```
正常继续计算
```

**B. allocation exists，但 demand-window semantic mapping unresolved**

```
SEMANTIC_RESOLUTION / SEMANTIC_UNRESOLVED
→ DATA_INCOMPLETE        （当 capability 需要该 allocation / 该 supply 判断时）
```

**C. mapping 已可靠解析，且在同一 effective reservation context 发生真实 over-allocation**

```
CONSISTENCY / CONSISTENCY_CONFLICT
→ DATA_INCOMPLETE
```

**不得**把这三种情形合并成一个笼统的 `Allocation Conflict`。

**不得创建** `demand_window_id` / `requirement_id` / `allocation_period` / `valid_from` / `valid_to`
等新字段；也**不得**创建新的 Validation Reason。

#### 4.4.61 Supplier-Material Relationship Consistency

Supplier Performance / Risk Evidence **不得只依据** `Supplier exists` ＋ `Material exists` 就直接关联。

**必须存在**可可靠识别的 **Supplier-Material Relationship**。

如果 relationship 无法解析 → Risk Evidence → **`DATA_INCOMPLETE`**。

**不得**：Supplier Master 中存在 Supplier → 自动认为它能供应所有 Materials。

#### 4.4.62 `sourcing_status` Boundary

Relationship eligibility 必须能够**可靠判断**。

```
source vocabulary             = source-specific
eligibility mapping contract  = DESIGN RESOLVED
```

（**PR #32 Human-approved Option B** —— 见 **§4.1.4 I** / **§4.2.8** / **§4.5.11**。）

因此**不得创建**全局 `APPROVED` / `ACTIVE` / `QUALIFIED` / `BLOCKED` / `INACTIVE` 等 source enum。

**三条 canonical 路径：**

**A. `eligible`**

```
valid relationship
→ eligible for Supplier Risk evaluation
→ NO Validation Issue
```

**B. explicitly `ineligible`**

```
valid but ineligible
→ excluded from candidate evaluation
→ NO Validation Issue
→ NO DATA_INCOMPLETE
```

**C. `unresolved`**

```
SEMANTIC_RESOLUTION / SEMANTIC_UNRESOLVED
```

当 Supplier Risk capability **需要该 relationship** 时：

```
Risk Evidence Status → DATA_INCOMPLETE
```

**必须保持：**

```
explicitly ineligible  ≠  semantic unresolved
```

**不得由 LLM 猜测资格**；也**不得**默认 eligible ／ 默认 ineligible。

#### 4.4.63 Supplier Performance Relationship Consistency

Supplier Performance evidence 必须与被评估的 `supplier_id` ＋ `material_code`
**Supplier-Material Relationship 一致**。

**不得**：

```
Supplier-A / MAT-X 的 performance
用于
Supplier-A / MAT-Y
```

**除非**未来存在明确 aggregation / shared-performance Design。

**当前没有该规则**，因此**不得自动共享**。

#### 4.4.64 Performance Period Consistency

`DeliveryPerformance` 与 `QualityPerformance` **必须各自存在可靠 `PerformancePeriod` context**。

必须保持：

```
PerformancePeriod  ≠  PerformanceUpdatedAt
```

`updated_at` **不得替代** measurement period。

如果 performance value exists 但 period unreliable：

对应 `DeliveryRisk` / `QualityRisk` → **`DATA_INCOMPLETE`**。

> 这属于**既有 Rule enforcement**。

#### 4.4.65 Procurement Recommendation ↔ Shortage Result

Procurement Recommendation 必须与产生它的 **Analysis Run ＋ Shortage Result** 保持一致。

当前：

```
RecommendationNeedDate = FirstShortageDate
```

因此当 `Classification = SHORTAGE` 且生成 numeric recommendation 时：
`RecommendationNeedDate` **必须对应同一 Analysis Run 的 `FirstShortageDate`**。

**不得**使用另一 Analysis Run 或另一 Material 的 `FirstShortageDate`。

本 Task **不重算**采购公式。

#### 4.4.66 Procurement Recommendation Grain

必须保持：

```
Analysis Run + plant_id + material_code + RecommendationNeedDate
```

context 一致。

**不得**：

- MAT-A Shortage Result → 生成 MAT-B recommendation
- Plant-A Shortage Result → 生成 Plant-B recommendation

#### 4.4.67 `ApplicableMOQ` Boundary

`ApplicableMOQ` 必须属于当前 Procurement Recommendation 的**可靠业务上下文**。

现行状态（**Option D semantic synchronization 已实施**）：

```
ApplicableMOQ canonical applicability resolution = DESIGN RESOLVED
Canonical Applicability Context = exact Procurement Recommendation Context
                                  （plant_id + material_code + RecommendationNeedDate）
Resolution Contract             = exactly one applicable ApplicableMOQ
                                  或 unresolved
Physical Carrier                = NOT YET DEFINED（logical provenance carrier = DESIGN RESOLVED；physical realization 仍属 §4.3）
```

因此**不得自行决定** `Supplier` / `Contract` / `Purchasing Info Record` / `Material Master`
谁是它的**真实来源** —— 这些只能是 **possible source forms**。

如果 `SHORTAGE` 但当前 recommendation 无法可靠取得适用 MOQ，继承：

```
BR-PROCUREMENT-001
    → DATA_INCOMPLETE
    → No Numeric Recommendation
```

**必须区分 root condition（不得统一写成「MOQ 不可用」）：**

| # | Root condition | 判定 | 结果 |
| --- | --- | --- | --- |
| **A** | applicability mapping 已可靠确定，但 required MOQ value **missing** | `FIELD_VALUE` ／ `MISSING` | `DATA_INCOMPLETE` |
| **B** | MOQ evidence **存在**，但**无法可靠判断哪个适用于当前 Procurement Recommendation Context** | `SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED` | `DATA_INCOMPLETE` |
| **C** | applicable MOQ 已解析，但 `ApplicableMOQ < 0` | 继承既有 `FIELD_VALUE` ／ `OUT_OF_DEFINED_RANGE` | `DATA_INCOMPLETE` |
| **D** | `ApplicableMOQ = 0` | **VALID explicit no MOQ constraint** | 正常参与 `max(BasePurchaseNeed, 0)` |

**不得**把 **A ／ B** 默认成 **D**。

**Supplier-Dependent Validation Path：**

- 若 supplier-dependent MOQ evidence 的 Supplier **已被独立可靠确定**
  （且该 determination **不是**为了拿到 MOQ 而执行的隐藏 Supplier Selection），
  则**可以**继续解析 `ApplicableMOQ`。
- 若 Supplier **尚未**被独立可靠确定，且唯一性**只能靠从 eligible Supplier 中挑一个**达成，
  则 → **`SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED`** → **`DATA_INCOMPLETE`**。

**必须明确：这不是 Supplier Risk Issue，也不是 Supplier Eligibility Issue ——
这是 `ApplicableMOQ` applicability resolution failure。**

**不得**为了拿到 MOQ 而**反向实现** Supplier Selection。

**Multiple Policy Source Validation：**

```
Contract MOQ = 80
PIR      MOQ = 100
```

同时存在且冲突、且**没有 approved precedence** 时 →
**`SEMANTIC_RESOLUTION` ／ `SEMANTIC_UNRESOLVED`**。

**不得**自动归类为 `CONSISTENCY_CONFLICT` —— 除非既有语义明确说明这些 records
在**同一 canonical policy context** 本应一致；**当前没有该 Rule**。

**不得**：`Contract wins` ／ `PIR wins` ／ `latest wins` ／ `most specific wins` ／
`min` ／ `max` ／ `average` ／ `first wins`。

**未新增**任何 Validation Reason（本项**未**扩展 `§4.4.81` canonical reason set；该 set 现为 **12 个**）。

**Valid Absence Boundary：** `Classification = NORMAL` 或 `BUFFER_BREACH` 时
**No Purchase Recommendation**，因此 `ApplicableMOQ` **not present by design**
是 **valid absence**，**不是** validation failure。

> **Human Decision Record** 与 **Option D Implementation Record** 见 **§4.5.22**。

#### 4.4.68 Analysis Run ↔ Snapshot Package Consistency

继承 `§4.3`：每个 Analysis Run 必须追溯到 **exactly one accepted Snapshot Package**。

一个 Snapshot Package **可以支持多个** Analysis Run。

**但**一个 Analysis Run **不得静默组合多个 Package 的 source evidence**。

必须保证：所有用于某 Analysis Run 的 imported source evidence，
均可追溯到**该 Run 所绑定的同一个 accepted Snapshot Package**。

**不得**：

```
Inventory   from P2
+ Requirement from P1
+ Inbound     from P3
```

静默形成**同一个** Analysis Run。

#### 4.4.69 Derived Result Run Consistency

所有 deterministic derived results（例如 Shortage Result / Supplier Risk Result /
Procurement Recommendation）必须能够追溯到**其 Analysis Run**，
且**不得静默引用其他 Run 的 source result**。

例如：

```
Run-R2 Procurement Recommendation  不得引用  Run-R1 ShortageQty
```

**即使** `plant_id` / `material_code` / `date` 恰好相同。

#### 4.4.70 AI Explanation Evidence Consistency

AI Explanation 使用的 `structured result` ＋ `evidence` ＋ `uncertainty`
必须属于**同一个被解释的 business outcome context**。

**不得**：

```
当前 Run 的 Shortage Result
+
旧 Run 的 Supplier Risk Evidence
```

拼成一个**未声明的当前事实**。

如果跨 Run 信息被未来允许比较，**必须**作为明确的 **comparison capability Design**。

**当前不设计。**

#### 4.4.71 Duplicate vs Conflict

继续继承 **Grain Conflict Principle**：

```
multiple records  ≠  automatically duplicate
```

**只有当**多个 records 在**同一个 canonical grain / context** 产生**互相冲突**
且**现有 Rule 没有 aggregation / precedence 规则**时，
才属于 **unresolved consistency conflict**。

**不得**：

- first wins
- latest wins
- arbitrary sum
- average
- random selection

#### 4.4.72 Valid but Ineligible vs Invalid

必须集中区分「**合法记录但业务上不 eligible**」与「**数据 inconsistency / invalid**」。

| 情形 | 判定 |
| --- | --- |
| Inbound `CANCELLED` | valid record → **ineligible supply** → **不是** Data Quality Issue |
| Inbound `effective_arrival_date > required_date` | valid record → 当前 `required_date` 前不计入 → **不是** Data Quality Issue |
| Inventory `INSPECTION` | valid record → **0% eligible** → **不是** Data Quality Issue |
| Substitute Relationship `PENDING` | valid known relationship state → 不参与 Approved Substitute Supply → **不是** Data Quality Issue |

与以下必须区分：

- unknown / invalid status
- unresolved identity
- conflicting grain

#### 4.4.73 No Auto-Reconciliation

Consistency conflict **不得**通过以下方式自动修复：

- last-write-wins
- first-write-wins
- newest timestamp wins
- largest quantity wins
- smallest quantity wins
- fuzzy matching
- LLM judgment
- cross-package fallback
- fallback to previous Analysis Run
- default relationship creation
- automatic allocation rebalance

**除非已有 Rule 明确授权。**

#### 4.4.74 Blast Radius

Consistency Issue **默认限制到**：

```
affected evidence → affected grain → affected capability
```

**不得自动** `one relationship conflict → entire Package rejected`，
**除非**它同时构成 **Package Structural Failure**。

例如：`MAT-A` substitute allocation conflict **不应**使 `MAT-B` unrelated shortage analysis 自动不可用。

#### 4.4.75 Consistency Rule Registry Concept

允许建立 conceptual table：

| Consistency Requirement | Source Rule / Design | Evidence Involved | Expected Relationship | Failure Meaning | Blast Radius |
| --- | --- | --- | --- | --- | --- |

**但不得创建**新的 `CR-*` / `VR-*` / `BR-*` ID —— 除非现有治理已经明确授权。

**本 Task 不需要新 Rule ID。**

#### 4.4.76 Do Not Resolve Pending Design Through Validation

必须继续保持以下未决项：

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

> 表中 `Warehouse canonical role`（**§4.5.12**）、`BOM version / validity`（**§4.5.7** ／ **§4.1.4 N**）、
> `sourcing_status` vocabulary（**§4.5.11**）、`effective_arrival_date` source mapping（**§4.5.21**）
> 与 allocation demand-window mapping（**§4.5.9**）
> 已由后续 Human-approved Design 解析，保留登记以便追溯。
>
> `required_quantity` semantic **已从本表移出** —— 该字段已由 **PR #38 Human Decision**
> 认定为 **`ORPHAN CANONICAL FIELD`** 并从 current canonical model **移除**（**§4.2.4**）。
>
> `loss_rate` owner / grain **已由 §4.5.22 Option E Implementation Record 解析**
> （owner = **exact Requirement Calculation Context**），**保留登记以便追溯**。
>
> `ApplicableMOQ` source **已由 §4.5.22 Option D Implementation Record 解析**
> （owner = **exact Procurement Recommendation Context**），**保留登记以便追溯**。

**Consistency Validation 不得成为解决这些问题的后门。**

#### 4.4.77 Cross-Dataset Consistency Examples

以下为 **conceptual examples**。

| # | 情形 | Expected |
| --- | --- | --- |
| **A** | `ordered_qty = 100`、`received_qty = 120` | **`DATA_INCOMPLETE`** ＋ **Data Quality Issue**；**不得** clamp |
| **B** | `required_date = 2026-10-10`、`effective_arrival_date = 2026-10-15` | record **valid** 但 `2026-10-10` 前**不计入**；**不是** Data Quality Issue |
| **C** | Eligible Substitute Supply = 100；`60 → MAT-A`、`50 → MAT-C` —— **且两者处于同一 effective reservation context / overlap 已可靠成立** | **`CONSISTENCY_CONFLICT`** ＋ **`DATA_INCOMPLETE`**；**不得**自动调成 60 / 40；**若 overlap 无法可靠判断 → `SEMANTIC_UNRESOLVED`**（见 **§4.4.58** / **§4.4.60**） |
| **D** | Target `Plant-A / MAT-A`；Source `Plant-B / MAT-B` | **不得直接计入** Approved Substitute Supply；**不得**自动设计 transfer |
| **E** | Performance `Supplier-A / MAT-X`；Risk request `Supplier-A / MAT-Y` | **不得直接复用** MAT-X performance；Risk Evidence **不能形成可靠正常结论** |
| **F** | Run R1 bound to Package P1；Inventory from P1 ＋ Requirement from P1 ＋ Inbound from **P2** | **不得静默执行 R1** —— Analysis Run / Snapshot consistency violation |
| **G** | Run R2 Recommendation 引用 Run R1 `ShortageQty` | **invalid provenance / consistency**；**不得**当作 R2 的 recommendation evidence |
| **H** | `inventory_status = INSPECTION` | record **valid**；`OpeningUsableInventory` contribution = **0**；**不是** Data Quality Issue |

#### 4.4.78 Canonical Separation

正式定义：

```
Validation Issue
  = 导致 evidence / context / capability / business result
    无法可靠使用或解释的具体 validation condition
```

必须严格区分以下**四个概念**：

| # | 概念 | 含义 |
| --- | --- | --- |
| **A** | **Validation Issue** | 问题本身 / **root condition** |
| **B** | **Package Disposition** | Package 是否可以 `ACCEPTED` / `REJECTED` / `UNUSABLE` |
| **C** | **Capability Readiness** | 某 capability 是否拥有足够 logical evidence 进入可靠执行 |
| **D** | **Business Outcome** | Business Rule 执行后形成的业务结果（`NORMAL` / `BUFFER_BREACH` / `SHORTAGE` / `DATA_INCOMPLETE`） |

必须明确：

```
Validation Issue  ≠  Package Status  ≠  Capability Status  ≠  Business Status
```

**不得创建**统一的 `ERROR` 来取代它们。

#### 4.4.79 Taxonomy Dimensions

Validation Issue **至少**需要表达以下 conceptual dimensions：

- Validation Layer
- Issue Category
- Reason
- Affected Evidence
- Affected Canonical Grain
- Affected Capability
- Relevant Field / Relationship
- Source Rule / Design Reference
- Blast Radius / Affected Scope
- Consequence Context
- Human-readable Detail

如果适用，还应能够追溯：`Snapshot Package` / `Analysis Run`。

**注意**：这里只定义 **conceptual information**。

**不得设计**：JSON Schema、DB Table、API Object、Python Class、event schema。

#### 4.4.80 Canonical Issue Categories

**8 个正式 conceptual categories。** 它们是 **documentation-level taxonomy labels**，
**不是** implementation enum / error code / API contract。

| # | Category | 含义 | Canonical Reason |
| --- | --- | --- | --- |
| **1** | `PACKAGE_STRUCTURE` | Package 自身结构 / integrity 无法可靠确认（manifest unavailable、package identity inconsistent、declared dataset artifact absent、artifact unreadable、integrity evidence unverifiable） | `STRUCTURAL_INCONSISTENCY` |
| **2** | `EVIDENCE_AVAILABILITY` | Accepted Package 未提供某 capability 所需的 logical evidence role | `EVIDENCE_ROLE_NOT_PROVIDED` |
| **3** | `FIELD_VALUE` | evidence 已存在，但单字段值不符合已定义的 Data Dictionary / Business Rule | `MISSING` / `INVALID_TYPE` / `OUT_OF_DEFINED_RANGE` / `INVALID_DEFINED_STATUS` |
| **4** | `IDENTITY_RESOLUTION` | evidence identity 无法可靠解析到 canonical identity | `UNRESOLVED_IDENTITY` |
| **5** | `SCOPE_COVERAGE` | dataset / evidence 存在，但无法可靠确认 coverage 是否覆盖当前分析范围 | `UNRESOLVED_SCOPE` |
| **6** | `SEMANTIC_RESOLUTION` | value / relationship 存在，但当前 Design 无法可靠解释其业务语义 | `SEMANTIC_UNRESOLVED` |
| **7** | `CONSISTENCY` | 多个 individually valid evidence 组合后违反既有 consistency invariant | `CONSISTENCY_CONFLICT` |
| **8** | `PROVENANCE` | required **package-scoped provenance linkage** **无法可靠建立 ／ 解析**，或**已建立**但与当前 Analysis Context 不一致 | `PROVENANCE_UNRESOLVED` / `PROVENANCE_MISMATCH` |

**关于 `MISSING` 的限制：**

```
MISSING = 字段本应存在，但不存在
```

**不得**用于描述：valid absence / not applicable / dataset role not provided。

**关于 `SEMANTIC_RESOLUTION` 的限制：**

一个 **Design Backlog 项存在**本身**不自动产生** runtime Validation Issue。

**只有当**当前 capability **确实需要**该 semantic **且无法可靠解释**时，才形成 Validation Issue。

**关于 `PROVENANCE` 的限制：**

该 category **只**覆盖 **required package-scoped provenance linkage** 的两种 root condition：

```
PROVENANCE_UNRESOLVED = required linkage 无法可靠建立 ／ 无法可靠解析
PROVENANCE_MISMATCH   = required linkage 已建立，但指向错误 ／ incompatible Analysis Context
```

**不得**扩展解释为：artifact missing ／ logical evidence role 未提供 ／
canonical business field value 缺失 ／ business semantic unresolved ／
entity identity unresolved ／ business scope coverage unresolved。

#### 4.4.81 Final Canonical Reason Set

本 POC 当前**正式**的 canonical reason set（共 **12 个**）：

| # | Reason | 所属 Category |
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
| 12 | `PROVENANCE_UNRESOLVED` | `PROVENANCE` |

**变更记录：** 第 **12** 项 `PROVENANCE_UNRESOLVED` 由 **PR #46 Human Decision**
（**`APPROVED FOR IMPLEMENTATION`**）授权并已实施 ——
见 **§4.5.22 Validation Taxonomy Implementation Record**。
既有 `1` ～ `11` 的编号与语义**未变**；`PROVENANCE_MISMATCH` **未**重命名、**未**修改。

**不得新增** `UNKNOWN_ERROR` / `GENERIC_ERROR` / `VALIDATION_FAILED` / `BAD_DATA` / `OTHER`
等 **catch-all reason** —— 除非未来经过正式 **Design Change**。

**但**：`human-readable detail` **可以**描述具体问题。

#### 4.4.82 Reason ≠ Outcome

必须明确：

- **Issue Reason** 描述：**为什么** evidence 不可靠
- **Outcome** 描述：该问题**对哪个层级**产生**什么后果**

**不得**将 `DATA_INCOMPLETE` 放进 Validation Issue Reason taxonomy ——
因为它是 **Business Outcome**，**不是** root validation reason。

同样：

- `CAPABILITY_UNAVAILABLE` **不得**作为 Validation Issue Reason
  （它是 Capability Readiness **consequence**）
- `REJECTED` / `UNUSABLE` **也不是** Issue Reason
  （它们属于 Package **consequence / disposition**）

#### 4.4.83 Category Mapping — Package Structure

例如：Manifest declares `Inventory dataset included`，但 Inventory artifact **absent**。

```
Category:            PACKAGE_STRUCTURE
Reason:              STRUCTURAL_INCONSISTENCY
Consequence context: Package may become REJECTED / UNUSABLE
```

**不得生成** `Shortage Classification = DATA_INCOMPLETE` 来**掩盖** Package structural failure。

#### 4.4.84 Category Mapping — Capability Evidence

例如：Package = `ACCEPTED`；Supplier Performance evidence role **not provided**；
用户请求 **Supplier Risk**。

```
Category:    EVIDENCE_AVAILABILITY
Reason:      EVIDENCE_ROLE_NOT_PROVIDED
Consequence: Supplier Risk capability unavailable
```

**不得生成** `OverallSupplierRisk = DATA_INCOMPLETE` ——
因为 Business Rule **尚未获得条件进入可靠执行**。

#### 4.4.85 Category Mapping — Business DATA_INCOMPLETE

例如：Supplier Performance evidence role **已经提供**，但 `PerformancePeriod = missing`。

```
Category:    FIELD_VALUE
Reason:      MISSING
Consequence: Delivery / Quality Risk evidence 无法完整形成
最终:        OverallSupplierRisk = DATA_INCOMPLETE
```

这里 `DATA_INCOMPLETE` 是 **Business Outcome**，**不是** issue category / reason。

#### 4.4.86 Invalid vs Missing Preservation

必须继续保持：

```
missing  ≠  present but invalid
```

| 输入 | Issue Reason |
| --- | --- |
| `SafetyStock` missing | `MISSING` |
| `SafetyStock = -10` | `OUT_OF_DEFINED_RANGE` |

**不得**把两者统一成 `MISSING` —— 虽然二者最终都可能使 `Shortage Result = DATA_INCOMPLETE`。

#### 4.4.87 Valid Absence（不生成 Issue）

以下**不生成** Validation Issue：

- `FirstShortageDate` not present because **no shortage**
- Procurement Recommendation not produced because `NORMAL`
- Procurement Recommendation not produced because `BUFFER_BREACH`
- `ApplicableMOQ` absent when Procurement Recommendation **not applicable**

这些属于 **valid absence / not applicable**，**不是** `MISSING`。

#### 4.4.88 Valid Zero（不生成 Issue）

以下合法值**不得创建** issue：

- `SafetyStock = 0`
- `loss_rate = 0`
- `AllocatedSubstituteQty = 0`
- `ApplicableMOQ = 0`
- `DeliveryPerformance = 0%`
- `QualityPerformance = 0%`

**不得** `0 → MISSING`；**不得** `0 → OUT_OF_DEFINED_RANGE` ——
除非对应已有 Rule 明确如此。

#### 4.4.89 Valid but Ineligible（默认不生成 Issue）

| 情形 | 判定 |
| --- | --- |
| `inventory_status = INSPECTION` | valid record → ineligible for usable inventory |
| `inventory_status = FROZEN` | valid record → ineligible |
| inbound status `CANCELLED` | valid record → ineligible supply |
| `effective_arrival_date > required_date` | valid record → not eligible before that need date |
| Substitute Relationship `PENDING` | valid known state → not Approved Substitute Supply |
| Supplier-Material Relationship `sourcing_status` → **`ineligible`** | valid record ＋ evidence 可可靠解释 → **not eligible for Supplier Risk candidate evaluation** |
| Substitute Allocation → Target Applicability = **`not applicable`** | valid allocation ＋ mapping 可靠 → **不计入**当前 Target `CumulativeApprovedSubstituteSupply`；**不是** Data Quality Issue |
| Substitute Allocation ↔ Source Demand Context = **`does not overlap`** | valid state ＋ mapping 可靠 → 不构成 reservation；**不是** Data Quality Issue |

**不得**把 **business ineligible** 错误分类成 `INVALID_DEFINED_STATUS` / `CONSISTENCY_CONFLICT`
或 **Data Quality Issue**。

> **不得**机械声称上述各情形是**同一种业务状态** ——
> 它们的**共同点只是**：`record valid` ＋ `not eligible for current calculation / evaluation`。
>
> **特别注意**：Supplier-Material Relationship 的 `ineligible` **不得**被压平为 `unresolved`，
> 反之亦然（见 **§4.4.62**）。
>
> **同理**：Substitute Allocation 的 **`not applicable`** / **`does not overlap`**
> **不得**被压平为 **`unresolved`** ——
> **只有「无法判断」才是 semantic unresolved**（见 **§4.4.60** / **§4.5.9**）。

#### 4.4.90 Data Quality Issue Boundary

正式限定现有术语 **`Data Quality Issue`**：

```
human-readable umbrella term
```

表示：已提供 business evidence 因为 missing / invalid / unresolved / conflicting / mismatched
而**无法可靠用于业务判断**。

它**不是** formal Business Status，也**不是**独立 canonical reason。

正式记录时**应落到**具体 **Validation Issue Category + Reason**。例如：

- `FIELD_VALUE` / `OUT_OF_DEFINED_RANGE`
- `IDENTITY_RESOLUTION` / `UNRESOLVED_IDENTITY`
- `CONSISTENCY` / `CONSISTENCY_CONFLICT`

**不得只记录** `Data Quality Issue` 而**没有具体 reason**。

#### 4.4.91 Allocation Conflict Boundary

现有术语 **`Allocation Conflict`** **保留**。

但将其定位为 **domain-specific human-readable detail**，对应 canonical taxonomy：

```
Category: CONSISTENCY
Reason:   CONSISTENCY_CONFLICT
```

例如 `Eligible Supply = 100`，Allocation `60 + 50 = 110`：

```
Issue:  CONSISTENCY / CONSISTENCY_CONFLICT
Detail: Allocation Conflict: allocated supply exceeds eligible supply.
Business consequence: BR-SUBSTITUTE-001 → DATA_INCOMPLETE
```

**不得创建** `ALLOCATION_CONFLICT` 作为**新的 Business Status**。

#### 4.4.92 Other Consistency Conflicts

以下也属于 `CONSISTENCY` ＋ `CONSISTENCY_CONFLICT`（**当已有 Design 支持时**）：

- `received_qty > ordered_qty`
- conflicting `SafetyStock` at same grain
- Allocation > Eligible Supply
- Supplier Performance associated with **wrong Material**
- conflicting canonical values **without approved precedence**

**但**：`valid but ineligible` **不得**放入该 category。

#### 4.4.93 Provenance Boundary

以下**必须**使用 `PROVENANCE` ＋ `PROVENANCE_MISMATCH`：

- Analysis Run R1 bound to Package P1，但使用 **Inbound from Package P2**
- Run R2 Recommendation **引用 Run R1 `ShortageQty`**
- 当前 AI Explanation 将**旧 Run Risk Evidence** 作为**当前 Run 事实**

**不得**把这些问题**仅**写成 `CONSISTENCY_CONFLICT` ——
因为其核心问题是 **evidence provenance / analysis context 不一致**。

**Missing vs Unresolved vs Mismatch（概念区分）**

| 情形 | Taxonomy |
| --- | --- |
| **A** required **logical evidence role 本身未提供** | `EVIDENCE_AVAILABILITY` ／ `EVIDENCE_ROLE_NOT_PROVIDED` |
| **B** required **canonical business field value 缺失** | `FIELD_VALUE` ／ `MISSING` |
| **C** evidence ／ business value **存在**，但 required **package-scoped provenance linkage 缺失 ／ 无法可靠解析 ／ 无法可靠建立** | **`PROVENANCE` ／ `PROVENANCE_UNRESOLVED`** |
| **D** provenance linkage **可以建立**，但指向**错误 Package / Analysis Context** | **`PROVENANCE` ／ `PROVENANCE_MISMATCH`** |

> **Validation Taxonomy Limitation —— `DESIGN RESOLVED`：**
> 「evidence **存在**，但其 **required package-scoped provenance linkage 缺失 ／ 无法可靠解析 ／
> 无法可靠建立**」这一情形，**已**由 **`PROVENANCE_UNRESOLVED`**（`PROVENANCE` category）精确表达；
> 该 taxonomy gap **不再 `OPEN`**（见 **§4.5.22 Validation Taxonomy Implementation Record**）。
>
> **演进链（保留以便追溯）：**
> - **PR #44 Human Decision：** **DO NOT EXTEND** `PROVENANCE_MISMATCH` 覆盖此情形；
>   **不新增** `PROVENANCE_MISSING` ／ `LINEAGE_MISSING` 等 reason
>   （见 **§4.5.22 Human Decision Record** 决定 13 ／ 14）。
> - **PR #46 Review Finding ＋ Human Decision Record：** `Current Taxonomy Compatibility = INSUFFICIENT`；
>   **`PROVENANCE_UNRESOLVED` = `APPROVED FOR IMPLEMENTATION`**（见 **§4.5.22**）。
> - **Validation Taxonomy Implementation：** `Canonical Reasons` `11 → 12`；
>   **`Validation Taxonomy Limitation` `OPEN` → `DESIGN RESOLVED`**
>   （见 **§4.5.22 Validation Taxonomy Implementation Record**）。
>
> **`PROVENANCE_MISMATCH` 语义保持不变**；
> 该情形**不得**被误分类为 `PACKAGE_STRUCTURE`；
> **`PROVENANCE_UNRESOLVED` 不得**作为 **catch-all reason**。
>
> **`DESIGN RESOLVED` 边界：** 只表示 **canonical validation taxonomy 概念设计已完成**，
> **不表示** runtime validator implemented ／ API implemented ／ enum implemented ／
> schema implemented ／ Adapter implemented ／ tested production behavior。

**Structural vs Business Provenance（不得误分类）**

```
Snapshot Manifest / artifact integrity                                  → PACKAGE_STRUCTURE
canonical fact / derived result 引用非当前 Analysis Context 的 evidence  → PROVENANCE
required package-scoped provenance linkage 无法可靠建立 / 无法可靠解析   → PROVENANCE_UNRESOLVED
```

**不得**把 **artifact missing** 错误归到 `PROVENANCE_MISMATCH`。

#### 4.4.94 Scope vs Identity

必须区分 `UNRESOLVED_IDENTITY` 与 `UNRESOLVED_SCOPE`：

| 情形 | Taxonomy |
| --- | --- |
| `material_code` 无法解析 | `IDENTITY_RESOLUTION` / `UNRESOLVED_IDENTITY` |
| Inbound dataset 可以解析 Material，但无法确认是否覆盖 Plant-A 当前分析范围 | `SCOPE_COVERAGE` / `UNRESOLVED_SCOPE` |

**不得**合并成一个模糊的 `mapping error`。

#### 4.4.95 Semantic Unresolved Boundary

`SEMANTIC_UNRESOLVED` **仅在**以下条件**同时成立**时使用：

- 当前 capability **确实需要**解释一个 business value / relationship；
- 但当前 **approved Design** 无法可靠解释其 semantic。

例如 `sourcing_status` source evidence **存在**，
但 `source value → conceptual eligibility condition`
**缺少足够可靠的 explicit deterministic mapping evidence**，
且当前 Supplier Risk **确实需要**该 relationship：
→ `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED`。

> **必须明确**：「**没有全局 source vocabulary**」**本身不是** Validation Issue ——
> 按 Human-approved **Option B**，source vocabulary **本来就是 `SOURCE-SPECIFIC`**。
> 真正的问题是 **eligibility mapping 无法可靠完成**（见 **§4.4.62** / **§4.5.11**）。

如果当前 Supplier Risk capability **确实需要**该 relationship：

```
Risk Evidence → DATA_INCOMPLETE
```

**另一个例子 —— inbound arrival date：** source date evidence **存在**，
但 `source value / semantics` **无法通过 approved source-specific mapping** 解析成
**唯一的 `effective_arrival_date`**：

→ `SEMANTIC_RESOLUTION` / `SEMANTIC_UNRESOLVED`。

> **必须明确**：「**没有 global source-field precedence**」**本身不是错误** ——
> 这是 **Human-approved 正式设计选择**（**Global Source-Field Precedence = `NOT ADOPTED`**）。
> 真正的问题是：**某个具体 source context 缺少足够 mapping evidence**
> （见 **§4.4.49** / **§4.5.21**）。

**但**：`required_quantity` **已从 current canonical model 移除**（**§4.2.4**）——
因此它**不产生** runtime issue；
**不得**仅因为该历史字段的存在或移除就让 Shortage Analysis 失败。

```
Open Design Item  ≠  automatic Validation Issue
```

#### 4.4.96 Issue Impact / Blast Radius

每个 Validation Issue **必须能够说明 affected scope**。至少从 conceptual level 能够表达：

- Package
- Dataset
- Record / Field
- Relationship
- Canonical Grain
- Analysis Run
- Capability

**不得设计**：numeric severity、`HIGH` / `MEDIUM` / `LOW` issue severity、priority score。

```
Blast Radius  ≠  Severity
```

继续保持**最小影响范围原则**。

#### 4.4.97 One Issue ≠ One Global Failure

例如：

```
Plant-A / MAT-A  SafetyStock = missing
Issue:              FIELD_VALUE / MISSING
Affected Grain:     Plant-A / MAT-A
Affected Capability: Shortage Analysis
Business Outcome:   MAT-A → DATA_INCOMPLETE
```

但：`Plant-B / MAT-B` 数据完整，**仍允许正常分析**。

**不得** `one Validation Issue → entire package failed` ——
**除非**该问题属于 `PACKAGE_STRUCTURE` **且确实使 Package 不可信**。

#### 4.4.98 Final Taxonomy — Explicit Prohibitions

**不得创建 issue ID / error code**：`DQ-001` / `VAL-001` / `ERR-001` / `STRUCT-001` 等；
**不得创建** numeric status code / HTTP status mapping / API error type。
（这些属于未来 **implementation design**。）

**不得创建 Validation Issue Severity**：`CRITICAL` / `HIGH` / `MEDIUM` / `LOW` ——
因为目前已有 Design 只定义 **blast radius / affected scope / business consequence**，
**没有批准 issue priority model**。

> **Supplier Risk 的 `LOW` / `MEDIUM` / `HIGH` 与 Validation Issue severity 完全无关，不得混淆。**

**不得将以下加入 Business Classification**：`CAPABILITY_UNAVAILABLE` / `VALIDATION_ERROR` /
`STRUCTURAL_ERROR` / `CONSISTENCY_ERROR` / `PROVENANCE_ERROR` / `NOT_APPLICABLE`。

Shortage Classification **仍只有** `NORMAL` / `BUFFER_BREACH` / `SHORTAGE` / `DATA_INCOMPLETE`；
Risk vocabulary **保持现有定义**。

**本 Task 也不要求创建正式 Capability enum**（`AVAILABLE` / `UNAVAILABLE` / `DEGRADED`）。

可以继续使用 `capability available` / `capability unavailable` 作为 **conceptual readiness description**。

#### 4.4.99 Pending Design Preservation

必须继续保持以下未决项（`Warehouse canonical role` **已由 §4.5.12 解析**、`BOM version / validity` **已由 §4.5.7 ／ §4.1.4 N 解析**、`sourcing_status` vocabulary **已由 §4.5.11 解析**、`effective_arrival_date` source mapping **已由 §4.5.21 解析**、allocation demand-window mapping **已由 §4.5.9 解析**、`loss_rate` owner / grain **已由 §4.5.22 Option E Implementation Record 解析**、`ApplicableMOQ` source **已由 §4.5.22 Option D Implementation Record 解析**；`required_quantity` semantic 则已由 **PR #38 Human Decision** **移除该字段**，保留登记以便追溯）：

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

**Validation Issue Taxonomy 不得解决这些问题。**

#### 4.4.100 Canonical Examples

以下为 **conceptual examples**。

**Example A — Missing Required Field**

Package `ACCEPTED`；`SafetyStock` evidence role **provided**；`SafetyStock` missing。

```
Category:        FIELD_VALUE
Reason:          MISSING
Affected Grain:  Plant-A / MAT-A
Consequence:     BR-SHORTAGE-001 → DATA_INCOMPLETE
```

**Example B — Dataset Role Not Provided**

Package `ACCEPTED`；Supplier Performance role **not provided**；请求 Supplier Risk。

```
Category:    EVIDENCE_AVAILABILITY
Reason:      EVIDENCE_ROLE_NOT_PROVIDED
Consequence: Supplier Risk capability unavailable
```

**不得** `OverallSupplierRisk = DATA_INCOMPLETE`。

**Example C — Declared Artifact Missing**

Manifest `Inventory included`；Artifact **missing**。

```
Category:    PACKAGE_STRUCTURE
Reason:      STRUCTURAL_INCONSISTENCY
Consequence: Package may be REJECTED / UNUSABLE
```

**Example D — Invalid Range**

`DeliveryPerformance = 120%`

```
Category:    FIELD_VALUE / OUT_OF_DEFINED_RANGE
Consequence: DeliveryRisk → DATA_INCOMPLETE
```

**Example E — Unresolved Material**

`material_code` cannot be reliably mapped。

```
Category: IDENTITY_RESOLUTION / UNRESOLVED_IDENTITY
```

**不得** fuzzy match。

**Example F — Unresolved Coverage**

Inbound dataset exists，但 scope coverage for `Plant-A` cannot be reliably determined。

```
Category: SCOPE_COVERAGE / UNRESOLVED_SCOPE
```

**不得** `no matched records → EffectiveInbound = 0`。

**Example G — Allocation Conflict**

`EligibleSupply = 100`；`Allocated = 110`。

```
Category:     CONSISTENCY / CONSISTENCY_CONFLICT
Human Detail: Allocation Conflict
Consequence:  BR-SUBSTITUTE-001 → DATA_INCOMPLETE
```

**Example H — Cross Run Provenance**

Run R2 Recommendation uses Run R1 `ShortageQty`。

```
Category: PROVENANCE / PROVENANCE_MISMATCH
```

**不得**静默复用。

**Example I — Valid Absence**

`Classification = NORMAL`；`FirstShortageDate` not present。

```
Expected: NO Validation Issue
```

**Example J — Valid Ineligible**

`inventory_status = INSPECTION`。

```
Expected: record valid；not eligible for OpeningUsableInventory
          NO Validation Issue
```

**Example K — Removed Field Is Not a Runtime Issue**

`required_quantity` **已从 current canonical model 移除**（**§4.2.4**）；
`BR-REQUIREMENT-001` uses `ProductionQty`, not `required_quantity`。

```
Expected: 不得仅因为该历史字段的存在或移除
          让当前 Shortage Analysis 失败
```

#### 4.4.101 Final Data Validation Design Closure + Status Boundary

**Closure Review Result: `PASS`**

`Final Data Validation Design` = **`DESIGN RESOLVED`**

```
Data Validation overall = DESIGN RESOLVED
```

**Closure Review Scope**

本轮是 **Closure Review**，**不是** new Design Task。**未新增任何** validation rule / constraint /
reason / category / enum / mapping rule / source field / data field / reconciliation rule /
physical schema / architecture / technology / ADR。

**Closure Review Checklist（8 个 workstream）**

| # | Workstream | Status | 复核结论 |
| --- | --- | --- | --- |
| 1 | Validation Layer Model | `DESIGN RESOLVED` | 四层 execution model 一致；无互相矛盾的 canonical definition |
| 2 | Capability-to-Evidence Requirement | `DESIGN RESOLVED` | capability-to-evidence matrix（A–E）与 `§4.1` / `§4.2` 一致 |
| 3 | Failure Semantics | `DESIGN RESOLVED` | 三层失败含义保持分离，未被重新合并 |
| 4 | Dataset Absent vs Empty Semantics | `DESIGN RESOLVED` | `not included ≠ included with zero records` 保持 |
| 5 | Failure Isolation Principle | `DESIGN RESOLVED` | blast radius 限制到 `evidence → grain → capability` |
| 6 | Detailed Field Validation | `DESIGN RESOLVED` | 只验证已批准项；未新增 range / enum / default / regex / rounding / freshness threshold / precedence |
| 7 | Cross-Dataset Consistency Rules | `DESIGN RESOLVED` | 8 项关系一致；未新增 reconciliation algorithm |
| 8 | Validation Issue Taxonomy Finalization | `DESIGN RESOLVED` | 唯一 canonical taxonomy；8 categories ＋ 12 reasons |

**Design DoD**

| # | Item | Result |
| --- | --- | --- |
| 1 | validation layers defined | ✅ |
| 2 | structural / capability / business failure meanings separated | ✅ |
| 3 | capability evidence requirements defined | ✅ |
| 4 | dataset absent vs empty semantics defined | ✅ |
| 5 | field validation policy defined | ✅ |
| 6 | cross-field / cross-dataset consistency defined | ✅ |
| 7 | failure isolation defined | ✅ |
| 8 | no silent exclusion defined | ✅ |
| 9 | valid zero / absence / ineligible semantics defined | ✅ |
| 10 | canonical issue taxonomy defined | ✅ |
| 11 | issue → affected scope / consequence 可表达 | ✅ |
| 12 | provenance consistency defined | ✅ |
| 13 | unresolved design explicitly preserved | ✅ |
| 14 | no duplicate canonical taxonomy | ✅ |
| 15 | no known internal contradiction | ✅ |
| 16 | no unauthorized Business Rule created | ✅ |
| 17 | conceptual Validation Report requirements defined | ✅ |

```
Design DoD = PASS（17 / 17）
```

**Upstream Design Items（0 项未决 ＋ 8 项已解析 ＋ 1 项已移除）—— 不阻塞本 closure**

这 9 项**阻止的是**「某些 capability 当前能够实际运行」，
**不是**「Data Validation conceptual design 已经定义清楚」。

原因：每一项目前都已有**明确的 fail-safe 分类路径与 blast radius 限制** ——
即 Validation **知道如何判断 / 如何分类 / 如何限制影响范围**：

| # | Unresolved Item | 状态 | Validation 的处理路径 |
| --- | --- | --- | --- |
| 1 | `loss_rate` owner / grain | **`DESIGN RESOLVED`** | 已由 **§4.5.22 Option E Implementation Record** 解析为 **Requirement Calculation Context ＋ exactly-one-or-unresolved**；physical carrier 仍 `SOURCE-SPECIFIC` / not yet defined（`§4.4.54`） |
| 2 | `required_quantity` semantic | **`REMOVED`** | 已由 **PR #38 Human Decision** 认定为 **`ORPHAN CANONICAL FIELD`** 并从 current canonical model 移除（`§4.2.4` / `§4.4.53`） |
| 3 | Warehouse canonical role | **`DESIGN RESOLVED`** | 已由 **§4.5.12** 解析为 source / mapping / scope context（`§4.4.50`） |
| 4 | BOM version / validity | **`DESIGN RESOLVED`** | 已由 **§4.5.7** ／ **§4.1.4 N** 解析为 requirement-scoped BOM applicability（`§4.4.52`） |
| 5 | `sourcing_status` vocabulary | **`DESIGN RESOLVED`** | 已由 **§4.5.11** 解析为 source-specific → canonical eligibility condition mapping contract（`§4.4.62`） |
| 6 | `effective_arrival_date` source mapping | **`DESIGN RESOLVED`** | 已由 **§4.5.21** 解析为 source-specific → canonical mapping contract（`§4.4.49`） |
| 7 | allocation demand-window mapping | **`DESIGN RESOLVED`** | 已由 **§4.5.9** 解析为 canonical allocation applicability mapping contract（`§4.4.58` / `§4.4.60`） |
| 8 | `ApplicableMOQ` source | **`DESIGN RESOLVED`** | 已由 **§4.5.22 Option D Implementation Record** 解析为 **Procurement Recommendation Context ＋ exactly-one-or-unresolved**；physical carrier 仍 `SOURCE-SPECIFIC` / not yet defined（`§4.4.67`） |
| 9 | provenance carrier | **`DESIGN RESOLVED`** | 已由 **§4.5.22 Option D Implementation Record** 实施为 **Layered Logical Provenance Contract**；physical carrier 仍属 `§4.3` 后续设计（`§4.4.93`） |

> 第 3 项 `Warehouse canonical role` 已由 **§4.5.12 Warehouse Role Resolution**
> 解析为 **source / mapping / scope context**；
> 第 4 项 `BOM version / validity` 已由 **§4.5.7** ／ **§4.1.4 N** 解析为
> **requirement-scoped BOM applicability**
> （**Human-authorized Canonical Model Amendment**，PR #30 ／ Option A）；
> 第 5 项 `sourcing_status` vocabulary 已由 **§4.5.11** 解析为
> **source-specific → canonical eligibility condition** 的 mapping contract
> （**Human-authorized Design Change**，PR #32 ／ Option B）；
> 第 6 项 `effective_arrival_date` source mapping 已由 **§4.5.21** 解析为
> **source-specific → canonical effective_arrival_date** 的 mapping contract
> （**Human-authorized Design Change**，PR #34 ／ Option D）；
> 第 7 项 allocation demand-window mapping 已由 **§4.5.9** 解析为
> **canonical allocation applicability mapping contract**
> （**Target Applicability** ＋ **Source Reservation Overlap**，
> **Human-authorized Design Change**，PR #36 ／ Option B）。
> 五者均**不再属于未决项**；对应行保留登记以便追溯。
>
> 第 2 项 `required_quantity` semantic 已由 **PR #38 Human Decision** 认定为
> **`ORPHAN CANONICAL FIELD`** 并从 current POC v0.2 canonical model **移除**
> （**Human-authorized Canonical Model Amendment**，见 **§4.2.4**）。
> 该字段**不再存在**，因此**不计入 unresolved**。
>
> 第 1 项 `loss_rate` owner / grain 已由 **Human-authorized Design Change** 解析
> （**Option E**：`Requirement Calculation Context` ＋ **exactly-one-or-unresolved**，
> 见 **§4.5.22 Option E Implementation Record**）；该行**保留登记以便追溯**。
> 第 8 项 `ApplicableMOQ` source 已由 **Human-authorized Design Change** 解析
> （**Option D**：`Procurement Recommendation Context` ＋ **exactly-one-or-unresolved**，
> 见 **§4.5.22 Option D Implementation Record**）；该行**保留登记以便追溯**。
> 第 9 项 `provenance carrier` 已由 **Human-authorized Design Change** 解析
> （**Option D**：**Layered Logical Provenance Contract**，
> 见 **§4.5.22 Option D Implementation Record**）；该行**保留登记以便追溯**。
> 剩余 **0 项**未决。

> 三者均明确禁止 Validation 反向解决这些设计问题：
> `Consistency Validation 不得成为解决这些问题的后门。` /
> `Field Validation 不能成为解决这些设计问题的后门。` /
> `Validation Issue Taxonomy 不得解决这些问题。`

**Dependency Boundary（不得被误解为已完成）**

| 依赖领域 | Status |
| --- | --- |
| Snapshot / Import Contract | `DESIGN PENDING` |
| Master Data Mapping | **`DESIGN RESOLVED`** |
| Adapter Boundary | `DESIGN PENDING` |

> **时点说明 ／ supersede：** 本表为 **`§4.4 Data Validation` closure 时点**的 dependency snapshot
> （历史值**保留不回写**，**不**代表 latest current state）—— 其中 `Snapshot / Import Contract` 已由
> **Issue #66 Closure**、`Adapter Boundary` 已由 **Issue #90 Closure Validation = `PASS`** 分别 supersede；
> 最新状态见 **§4.3.29** ／ **§4.6.22**。

`Data Validation = DESIGN RESOLVED` **不要求**且**不表示**：

- serialization format / physical file layout / field carrier mapping 已完成
- Master Data Mapping algorithm 已设计
- Adapter implementation 已完成

**必读限定：**

```
Data Validation DESIGN RESOLVED
  ≠ Snapshot / Import Contract DESIGN RESOLVED
  ≠ Master Data Mapping DESIGN RESOLVED
  ≠ Adapter Boundary DESIGN RESOLVED
```

**`DESIGN RESOLVED` 的语义边界**

`DESIGN RESOLVED` **只**表示：

```
conceptual validation design complete
```

**不表示**：implemented / data validated / tested / production-ready。

以下**均不构成** closure blocker（`DESIGN RESOLVED` ≠ `IMPLEMENTED` ≠ `TESTED`）：

- no validator implementation
- no tests yet
- no JSON Schema / API schema / database schema
- no error code / severity model
- no UI / monitoring implementation
- no physical import format

---

<!-- END MIGRATED LEGACY §4.4 BODY -->
