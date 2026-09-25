# Snapshot / Import Contract

**Document / Topic:** Snapshot / Import Contract
**Parent Design:** [POC Design v0.2](../../poc-design-v0.2.md)
**Legacy Section:** §4.3（§4.3.1 ～ §4.3.31 编号保留）
**Design Status:** `DESIGN RESOLVED`
**Implementation Status:** 原文未单独登记本专题的 implementation 状态；`DESIGN RESOLVED` 不表示 import implementation exists / data validated / tested。
**Canonical Authority:** 本文件是 Snapshot / Import Contract concern 的唯一 current canonical source；parent design 保留 navigation/status 入口。
**Migration Base:** `5917cb2fa4b71d4a7379128447bc9e766d17e6da`

<!-- BEGIN MIGRATED LEGACY §4.3 BODY -->
### 4.3 Snapshot / Import Contract —— Package Envelope & Import Atomicity

> **子章节整体状态：现为 `DESIGN RESOLVED`。**
>
> 本节已完成**第一层**（Package Envelope ／ Atomicity Boundary ／ Immutability Boundary ／
> Analysis Run Linkage）、**`Serialization Format`**（**PR #51 Human Decision** ＋
> **PR #52 Closure Re-run = `PASS`**，见 **§4.3.22**）、**`Physical Dataset Layout`**
> （**PR #53 Human Decision** ＋ **本层 Closure Validation = `PASS`**，见 **§4.3.23**）、
> **`Field Carrier Mapping`**（**PR #63 Human Decision ＋ Supplementary Human Naming Decision** ＋
> **本层 Closure Re-run = `PASS`**，见 **§4.3.25** ／ **§4.3.27**）与
> **`Final Import Contract`**（**Issue #66 Human Decision Bundle 1 ～ 6** ＋
> **本层 Closure Validation = `PASS`**，见 **§4.3.28** ／ **§4.3.29**）；
> 因此 **`Snapshot / Import Contract` overall 现为 `DESIGN RESOLVED`**。

**层级状态登记：**

| 层 | Status |
| --- | --- |
| Package Envelope | **`DESIGN RESOLVED`** |
| Atomicity Boundary | **`DESIGN RESOLVED`** |
| Immutability Boundary | **`DESIGN RESOLVED`** |
| Analysis Run Linkage | **`DESIGN RESOLVED`** |
| Serialization Format | **`DESIGN RESOLVED`** |
| Physical Dataset Layout | **`DESIGN RESOLVED`** |
| Field Carrier Mapping | **`DESIGN RESOLVED`** |
| Final Import Contract | **`DESIGN RESOLVED`** |

> **本节 overall `DESIGN RESOLVED` 仅**表示其 **conceptual boundary 已定义**，
> **不表示**：import implementation exists、data validated、tested。
> `Adapter Boundary` 为**独立子领域**，其 **conceptual design 已由 Issue #90 Closure Validation = `PASS`** 登记为 **`DESIGN RESOLVED`**（见 **§4.6.21** ／ **§4.6.22**）；其 **runtime ／ source-specific realization 仍为 `NOT IMPLEMENTED`** —— **design 状态与实现状态必须分开解读**。

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

> **范围说明（历史 ＋ current-state）：** 上述「不得定义」是**本 Task 当时**的 scope restriction ——
> 当时**尚未授权**决定 serialization format。
> **PR #51 Human Decision** 现已授权并登记 **JSON** strategy（见 **§4.3.22**），
> 因此「不得定义 **JSON**」**不再**构成 current restriction；
> 但 `CSV` ／ `JSONL` ／ `Parquet` ／ `ZIP` 仍为 `NOT SELECTED`。
> **PR #53 Human Decision ＋ 本层 Closure Validation** 现已登记 `directory layout` ／ `concrete filenames`
> （见 **§4.3.23**，**`DESIGN RESOLVED`**）；
> `physical schema` 继续属于 **`Field Carrier Mapping`** —— 现为 **`DESIGN RESOLVED`**
> （**PR #63 Human Decision** ＋ **Closure Re-run = `PASS`**，见 **§4.3.25** ／ **§4.3.27**）。

**当时状态（保留以便追溯）：**

```
Serialization Format = DESIGN PENDING
```

**current status：`Serialization Format` 现为 `DESIGN RESOLVED`** ——
**PR #51 Human Decision** 登记 JSON strategy；**PR #52 Closure Re-run** = **`PASS`**
（见 **§4.3.22** ／ **Serialization Format Closure Re-run Record**）。

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

**Dataset-Level Provenance Reference vs Stable Source Evidence Locator（两层，不得混合）**

| 层 | 负责回答 |
| --- | --- |
| **dataset-level provenance reference**（本节已要求） | 「**这整个 logical dataset** 来自哪里 / 哪份 evidence artifact」 |
| **Stable Source Evidence Locator**（**§4.5.22** Review 提出） | 「**dataset 内哪一份具体 evidence** 支撑当前 canonical value / relationship」 |

**不得把两者混为一层** —— dataset-level reference **不足以**定位单条 source evidence
（见 **§4.5.22** Critical Scenario A）。

**Logical Provenance Carrier Contract（**§4.5.22 Option D Implementation Record**）：**

```
Package Identity
+ Logical Dataset Role
+ Stable Source Evidence Locator
+ Mapping / Resolution Basis（when applicable）
```

上述四者之间的 conceptual relation **已定义**（**§4.5.22**）。

**当时状态（保留以便追溯）：`Field Carrier Mapping` ／ `Final Import Contract` 仍为 `DESIGN PENDING`** ——
**logical carrier resolved ≠ physical serialization resolved**。

> **current-state 更新：** 二者现均为 **`DESIGN RESOLVED`** ——
> `Field Carrier Mapping` 见 **§4.3.25** ／ **§4.3.27**；
> `Final Import Contract` 见 **§4.3.28** ／ **§4.3.29**。
> 「logical carrier ≠ physical carrier」的**区分**仍然成立（只是 physical carrier 现已设计）。

> **PR #51 Human Decision（manifest 部分）：** Snapshot Manifest =
> **independent artifact ＋ JSON serialization**；business datasets = **JSON**（见 **§4.3.22**）；
> **`Snapshot Manifest ≠ business dataset`** 保持。
> `manifest filename` ／ `path` ／ `directory` ／ `package container` **已由 `Physical Dataset Layout` 登记**
> （见 **§4.3.23**）；`archive` = **`NOT SELECTED`**。
> `Serialization Format` 本身**现为 `DESIGN RESOLVED`**（**PR #52 Closure Re-run = `PASS`**，见 **§4.3.22**）。
> `Physical Dataset Layout` 本身**现为 `DESIGN RESOLVED`**（**PR #53 Human Decision** ＋
> **本层 Closure Validation = `PASS`**，见 **§4.3.23**）。

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

> **current-state clarification（**不**回写上述时点边界）：** integrity algorithm 已由
> **Issue #66 Human Decision（Bundle 4）** 登记、并写为 authoritative current policy
> （见 **§4.3.28 D.1** ／ **D.2**，closure 见 **§4.3.29**）：
>
> ```
> current design policy = SHA-256（IG-alg-1）＋ IG-raw（digest exact raw artifact bytes）
>                       ＋ "integrity_evidence" = 64-character lowercase hexadecimal SHA-256 digest
> ```
>
> 上文「本 Task 不决定 **implementation**」的**原时点边界仍然成立** ——
> **仍未完成的是 runtime implementation**（hash computation ／ validator ／ importer），
> **不是** algorithm 的 design decision。

#### 4.3.16 Provenance Boundary

每个 imported dataset **必须能够追溯到**：

```
Snapshot Package
+
logical dataset role
+
controlled export provenance
```

**但本 Task 不设计**：source_system_id schema、lineage DB、audit DB、event format。

**logical provenance carrier contract 已定义**（**§4.5.22 Option D Implementation Record**）：

```
Snapshot Package
+ logical dataset role
+ Stable Source Evidence Locator
+ Mapping / Resolution Basis（when applicable）
```

**logical carrier resolved** **不表示** physical serialization 已完成 ——
后者属 **§4.3 `Field Carrier Mapping` ／ `Final Import Contract`**（**当时**为后续设计；
**current-state：** 现均已 **`DESIGN RESOLVED`**，见下方 boundary）。

**current-state boundary（**不**回写历史时点语义）：**

```
Logical Provenance Contract             = DESIGN RESOLVED
Physical Carrier ／ Import-contract Design = DESIGN RESOLVED
  （Field Carrier Mapping 见 §4.3.25 ／ §4.3.27；Final Import Contract 见 §4.3.28 ／ §4.3.29）
Runtime ／ Source-specific ／ Adapter Realization = NOT IMPLEMENTED
  （其设计归属 Adapter Boundary；Adapter Boundary design = DESIGN RESOLVED，见 §4.6.21；realization 未实现）

logical contract  ≠  physical design  ≠  runtime realization
```

> **controlled export provenance** 的 **logical carrier contract** 已由 **§4.5.22** Review 提出
> （**Option D**）；该 Review **未改变**本边界。
> **当时状态（保留以便追溯）：** `physical serialization` 属后续设计、**尚未完成**。
> **current-state 更新：** physical carrier ／ import-contract **design** 已由 **§4.3** 关闭
> （**`DESIGN RESOLVED`**；见 **§4.3.25** ／ **§4.3.27** ／ **§4.3.28** ／ **§4.3.29**，**Issue #66 Closure**）；
> **仍未实现**的是 runtime ／ source-specific ／ **Adapter realization** —— 该 realization 属 **`Adapter Boundary`** 的范围，而 **`Adapter Boundary` 的 conceptual design 已由 Issue #90 Closure Validation = `PASS` 登记为 `DESIGN RESOLVED`**（见 **§4.6.21**）；**实现状态（`NOT IMPLEMENTED`）与 design 状态必须分开解读**，**不得**因 design closure 而声称已实现。

#### 4.3.17 Unresolved Carrier Boundary

以下项在**本 Task 时点**「仍未完全确定」（见 §4.2.16）——
其中 `Warehouse canonical role`（**§4.5.12**）、`BOM version / validity`（**§4.5.7** ／ **§4.1.4 N**）、
`sourcing_status` vocabulary（**§4.5.11**）、`effective_arrival_date` source mapping（**§4.5.21**）
与 allocation demand-window mapping（**§4.5.9**）**已被解析**，**不再属于未决项**；
`required_quantity` vs `ProductionQty` 则已由 **PR #38 Human Decision** 认定为
**`ORPHAN CANONICAL FIELD`** 并从 current canonical model **移除**（**§4.2.4**）：

- `loss_rate` owner / grain —— **已由 §4.5.22 Option E Implementation Record 解析**（Requirement Calculation Context ＋ exactly-one-or-unresolved resolution contract）
- Warehouse canonical role —— **已由 §4.5.12 解析**（source / mapping / scope context）
- BOM version / validity —— **已由 §4.5.7 ／ §4.1.4 N 解析**（requirement-scoped BOM applicability）
- `sourcing_status` vocabulary —— **已由 §4.5.11 解析**（source-specific → canonical eligibility condition）
- `effective_arrival_date` source mapping —— **已由 §4.5.21 解析**（source-specific → canonical mapping contract）
- allocation demand-window mapping —— **已由 §4.5.9 解析**（Target Applicability ＋ Source Reservation Overlap）
- `ApplicableMOQ` source —— **已由 §4.5.22 Option D Implementation Record 解析**（Procurement Recommendation Context ＋ exactly-one-or-unresolved resolution contract）
- provenance carrier —— **logical carrier 已由 §4.5.22 Option D Implementation Record 解析**
  （**Layered Logical Provenance Contract**，`DESIGN RESOLVED`）；
  **physical carrier design** 已由 **§4.3** 关闭
  （`Field Carrier Mapping` 见 **§4.3.25** ／ **§4.3.27**；
  `Final Import Contract` 见 **§4.3.28** ／ **§4.3.29**，**Issue #66 Closure**）

**因此（current-state boundary）：**

```
Logical Provenance Carrier          = DESIGN RESOLVED
Physical Carrier Design             = DESIGN RESOLVED
  （Field Carrier Mapping ／ Final Import Contract，见 §4.3.25 ／ §4.3.27 ／ §4.3.28 ／ §4.3.29）
Source-Specific ／ Adapter Realization = NOT IMPLEMENTED
  （属 Adapter Boundary 范围；Adapter Boundary design = DESIGN RESOLVED，见 §4.6.21；realization 未实现）

logical provenance contract  ≠  physical carrier design  ≠  runtime / source-specific realization
```

`provenance carrier` **不再**是未分类的 unresolved item ——
它是 **logical provenance contract（`DESIGN RESOLVED`）**、
**physical carrier design（`DESIGN RESOLVED`）** 与
**runtime ／ source-specific Adapter realization（仍未实现）** 的合称，三者**必须分开解读**。

因此本 Task **不得为了完成 Snapshot Contract** 擅自决定这些字段属于哪个
**physical dataset / file**。

**尤其 `loss_rate`：**

**不得**自行挂到 Production Requirement / Material / BOM Component / Plant-Material 之一。

这些**已由 physical carrier design 决定**（`physical dataset / file / field representation`
属 **`§4.3 Field Carrier Mapping` ＋ `Final Import Contract`**，现均为 **`DESIGN RESOLVED`**；
**`Snapshot / Import Contract` overall 亦为 `DESIGN RESOLVED`**，见 **§4.3.29**）——
**但** actual **source-specific extraction ／ Adapter realization 仍未实现**，
**不得**据此声称已完成。

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

**Serialization Format Design Review（Review Finding）**

**Review Authority / Scope**

```
Snapshot / Import Contract 层级状态：
  Package Envelope       = DESIGN RESOLVED
  Atomicity Boundary     = DESIGN RESOLVED
  Immutability Boundary  = DESIGN RESOLVED
  Analysis Run Linkage   = DESIGN RESOLVED
  Serialization Format   = DESIGN PENDING   ← 本 Review 对象
  Physical Dataset Layout = DESIGN PENDING
  Field Carrier Mapping   = DESIGN PENDING
  Final Import Contract   = DESIGN PENDING
```

本 Review **只**产出 Review Finding：

- **不**实施 Serialization Format；
- **不**选择最终格式；
- **不**推进 `Physical Dataset Layout` ／ `Field Carrier Mapping` ／ `Final Import Contract`；
- **不**设计 Adapter ／ parser ／ schema；
- **不**写 Human Decision。

**Review Question**

```
1.  POC 的 physical Serialization Format 最低需要解决哪些问题？
2.  是否需要单一 serialization format，或不同 logical dataset 可以使用不同 format？
3.  Snapshot Manifest 与 business dataset 是否应该使用相同 serialization format？
4.  CSV ／ JSON ／ JSONL ／ Parquet 分别有什么 trade-off？
5.  是否需要 package container 概念（directory ／ archive），
    还是该问题应留给 Physical Dataset Layout？
6.  如何保证 deterministic parsing ／ stable field representation ／ reproducibility ／
    human inspectability ／ version compatibility？
7.  serialization 层需要定义哪些 cross-cutting rules
    （text encoding ／ null ／ date ／ datetime ／ decimal ／ boolean ／ enum ／
     empty dataset ／ escaping）？
8.  哪些内容属于 Serialization Format，哪些必须留给
    Physical Dataset Layout ／ Field Carrier Mapping ／ Final Import Contract？
9.  当前 repository evidence 是否足以做最终 format decision？
10. 需要 Human Decision 的具体问题是什么？
```

**Existing Constraints（从 Repository 已存在的正式设计恢复；不得重新设计）**

**Integration Pattern（`§3`）：**

```
Controlled Export / Snapshot
      ↓
POC Data Landing Zone
      ↓
Read-only analysis
```

读取**只能**通过 **Controlled Export / Snapshot** 产物进行；**不得**绕过 Controlled Export 直连源系统（`§3`）。
`§4` 已记录的继承约束：**具体文件格式（CSV ／ JSON ／ Parquet）与 Adapter Contract 属本阶段待设计事项**。

**Snapshot Package 约束（`§4.3`）：**

| 约束 | 位置 |
| --- | --- |
| Snapshot Package = **immutable input evidence package** | `§4.3.2` |
| `Snapshot Package ≠ Analysis Run`；`Snapshot Package ID ≠ Analysis Run ID` | `§4.3.2` ／ `§4.3.4` |
| 每个 Analysis Run **必须能够追溯到 exactly one accepted Snapshot Package** | `§4.3.4` |
| **禁止** silent cross-snapshot mixing（multi-snapshot ／ incremental ／ streaming ／ delta 须另开 Design） | `§4.3.6` ／ `§4.3.7` |
| 已 Accepted 的 package **不得**原地修改 ／ 部分覆盖 ／ silently replace ／ 同 ID 表示不同内容 | `§4.3.5` |
| Import 必须是 package-level atomic：`ACCEPTED` 或 `REJECTED` ／ `UNUSABLE` | `§4.3.6` |
| Package identity ／ integrity ／ required structural metadata 无法可靠确定 → **fail closed** | `§4.3.18` |
| Import **不得** write back Production ／ modify source ／ request Production DB fallback | `§4.3.19` |

**Logical Snapshot Manifest 必须至少表达（`§4.3.8`）—— 语义层，非物理层：**

```
snapshot_package_id
contract version
export / package creation time
environment / evidence classification
included logical datasets
dataset-level provenance reference
dataset-level record count / integrity evidence
package completeness state
```

> `§4.3.8` 明确：这是 **logical manifest**；**不决定** `manifest.json` ／ `manifest.yaml` ／
> database row ／ 其他物理实现。

**Integrity Requirement（`§4.3.15`）—— 必须支持未来验证：**

```
package identity integrity
dataset identity
dataset presence
dataset completeness metadata
content integrity
```

> **只定义** `integrity evidence is required`；**不决定** SHA256 ／ MD5 ／ digital signature ／ checksum implementation。

**Provenance 两层（`§4.3.8` ／ `§4.3.16` ／ `§4.5.22 Option D Implementation Record`）：**

```
dataset-level provenance reference  ≠  Stable Source Evidence Locator

Logical Provenance Carrier   = DESIGN RESOLVED
Physical Carrier Realization = DESIGN PENDING
```

**Canonical 类型系统（`§4.2.2`）—— technology-neutral logical types：**

```
IDENTIFIER ／ ANALYSIS_RUN_ID ／ DATE ／ TIMESTAMP ／
DECIMAL_QUANTITY ／ NON_NEGATIVE_QUANTITY ／ RATIO ／ PERCENTAGE ／
STATUS ／ TEXT_CONTEXT
```

> `§4.2.2` 明确：**不得映射成** `VARCHAR` ／ `DECIMAL(18,2)` ／ `UUID` ／ `BIGINT` ／ `JSONB` 等数据库类型；
> `§4.2.1` 明确 Data Dictionary **不等于** JSON Schema ／ CSV layout ／ serialization format。

**Field-level 既有语义（不得被 serialization 改变）：**

| 约束 | 位置 |
| --- | --- |
| `Zero ≠ Missing`；`missing` **不得**等同于 `0` ／ `false` ／ empty string ／ `UNKNOWN` | `§4.2.2` ／ `§4.2.12` |
| valid absence ／ not applicable **≠** missing required data | `§4.2.12` ／ `§4.3.13` |
| **不得**在无现有 Design 支持时新增 `decimal precision` ／ date freshness threshold ／ identifier regex ／ unit-of-measure conversion ／ timezone policy ／ quantity rounding；**未定义就写 `NOT DEFINED`** | `§4.4.42` ／ `§4.2.13` |
| 具体 quantity precision ／ rounding 由**后续明确 Design Rule** 决定 | `§2.4.8` ／ `§2.5.11` |

**Dataset presence（`§4.3.12` ／ `§4.3.14` ／ `§4.4.4`）：**

```
Dataset not included  ≠  Dataset included with zero records
```

- **A**：Manifest **未声明** → **不得**自动解释为「业务上不存在任何记录」；
- **B**：Manifest 声明 `included` ＋ `record_count = 0` → **structurally valid empty dataset**；
- **C**：`dataset not declared / not included` 的最终处理**留给 capability validation**。

**Required Serialization Properties**

下表区分 **既有 Design 要求**（`既有`）与 **POC 适用性判断**（`POC`）——
二者**不得混淆**：`POC` 项**不构成**对最终 format 的强制约束。

| # | Property | 类别 | 依据 |
| --- | --- | --- | --- |
| **R-1** | **Deterministic parsing** —— 同一 package 的同一 dataset 在任意合规读取器上产生**同一** canonical 值序列；**不得**依赖启发式 ／ locale ／ 隐式推断 | 既有 | `§4.3.6` ／ `§4.5.2` ／ `§4.3.18` |
| **R-2** | **Stable field representation** —— 同一 canonical field 的表示跨 dataset ／ 跨 package **一致** | 既有 | `§4.2.2` ／ `§4.5.2` |
| **R-3** | **Logical type 无损** —— `DATE` vs `TIMESTAMP` ／ `RATIO` vs `PERCENTAGE` ／ `DECIMAL_QUANTITY` vs `NON_NEGATIVE_QUANTITY` 不得因 physical representation 而模糊 | 既有 | `§4.2.2` ／ `§4.2.13` |
| **R-4** | **Missing ≠ present-with-default** —— 必须能区分「字段不存在」与「存在且为 `0` ／ `false` ／ 空字符串 ／ `UNKNOWN`」 | 既有 | `§4.2.12` ／ `§4.3.13` |
| **R-5** | **Dataset-level absence 可表达** —— `not included` 与 `included with zero records` 必须可区分 | 既有 | `§4.4.4` ／ `§4.3.12` |
| **R-6** | **Manifest metadata 可承载** —— `§4.3.8` 的 8 项语义可被承载，且 manifest **不得**与 business dataset 混淆 | 既有 | `§4.3.8` |
| **R-7** | **Integrity evidence 可承载** —— `§4.3.15` 的 5 项 integrity 证据可被承载（**不**规定算法） | 既有 | `§4.3.15` |
| **R-8** | **Reproducibility** —— 同一 package 可被多次 Analysis Run 引用并产生一致结果 | 既有 | `§4.3.4` |
| **R-9** | **Version compatibility** —— `contract version` 可表达且未来可演进 | 既有 | `§4.3.8` |
| **R-10** | **Adapter 中立** —— serialization **不得**要求 POC 直连源系统或实现 Adapter | 既有 | `§4.3.19` ／ `§3` |
| **R-11** | **Human inspectability** —— source evidence 必须可被稳定重新定位与检视 | POC | `§4.5.22 Option D`（`Stable Source Evidence Locator`）／ `§4.3.16` |
| **R-12** | **Implementation simplicity** —— 最小化 POC 实现面与验证面 | POC | `CONTRIBUTING` §8（清晰、简单、局部）／ `§4.4.42` 精神 |

**10 Questions Assessment**

**Q1 —— physical Serialization Format 最低需要解决哪些问题？**

最低必须解决 **R-1 ～ R-10**（全部为既有 Design 要求）：

```
deterministic parsing
stable field representation
logical type 无损
missing ≠ present-with-default
dataset-level absence 可表达
manifest metadata 可承载
integrity evidence 可承载
reproducibility
contract version 可表达
Adapter 中立
```

**明确不需要**由 Serialization Format 解决（属其他层）：

```
directory tree ／ exact filename ／ file-per-dataset rule ／ dataset grouping
folder naming ／ manifest filename ／ archive filename
source field → file column mapping
```

**Q2 —— 单一 format，还是不同 logical dataset 可用不同 format？**

- 现有 Design **既没有**要求「全 package 单一 format」，**也没有**要求「按 dataset 允许不同 format」。
- **技术可行性判定：** 两种做法在**技术上都不违反**现有 Design 的文字约束。
- **但**：多 format 会**放大** R-2 的实现面 —— 「同一 canonical field 在不同 dataset 中的表示一致性」规则
  **当前并不存在**，若选择多 format，**必须**同时定义该规则（否则 R-2 无法验证）。
- **POC 适用性判断（非强制）：** 单一 format 的验证面与实现面更小（R-12）。
- **本 Review 不作出该选择** —— 属 **Human Decision**。

**Q3 —— Snapshot Manifest 与 business dataset 是否应该使用相同 serialization format？**

- `§4.3.8` 只要求 manifest 表达 8 项**语义**，**没有**要求 manifest 与 business dataset **同格式**，
  也**没有**授权把 manifest 与 business dataset **混为一体**。
- **该问题不可以留到 `Field Carrier Mapping`** —— 它决定 manifest 的**承载方式**，
  因此落在 **`Serialization Format`（承载）＋ `Physical Dataset Layout`（位置 ／ 命名）** 的交界。
- **必须保持（无论选择如何）：**

```
Snapshot Manifest  ≠  business dataset
```

- **本 Review 不作出该选择** —— 属 **Human Decision**（含「manifest 是否为独立 artifact」）。

**Q4 —— CSV ／ JSON ／ JSONL ／ Parquet 的 trade-off？**

见 **Option Review** 与 **Option Comparison**。

**Q5 —— 是否需要 package container 概念（directory ／ archive）？**

- `§4.3.1` 明确**不得定义** directory layout ／ ZIP；`§4.3.8` 明确**不决定** manifest 物理实现。
- 因此 **「package container 是否为单一 archive」属于 `Physical Dataset Layout`** —— 本 Review **不决定**。
- **但必须记录 dependency：**

```
若 Serialization Format 选择「多 artifact ／ file-per-dataset」形态，
  则 Physical Dataset Layout 必须定义 package container；
若 Serialization Format 可选择「单 artifact 承载全部 logical dataset」，
  则 container 可能不需要。

⇒ 该 dependency 由 Human Decision 在 Q2 ／ Q3 一并对齐，本 Review 不自行解决。
```

**Q6 —— 如何保证 deterministic parsing ／ stable field representation ／ reproducibility ／
human inspectability ／ version compatibility？**

| 目标 | Serialization 层可控手段 | 必须依赖其他层（本 Review 不解决） |
| --- | --- | --- |
| deterministic parsing | 明确规定 encoding ／ 分隔 ／ 引号 ／ escaping ／ null token ／ 数值与日期字面量规则；**禁止**任何「可省略 ／ 可推断」表达 | `Field Carrier Mapping`（source field → carrier） |
| stable field representation | 明确规定每个 logical type 的唯一表示；禁止同一 type 多表示 | `Field Carrier Mapping` |
| reproducibility | 与 `§4.3.5` immutability ＋ `§4.3.4` exactly-one-package 一致；serialization **不得**含非确定性成分（时间戳 ／ 顺序依赖 ／ 随机 ／ locale） | `Final Import Contract` |
| human inspectability | 与 `Stable Source Evidence Locator` 的可定位性一致；不得要求专用二进制工具才能检视 | `Field Carrier Mapping`（locator 的物理承载） |
| version compatibility | `contract version` 必须可在 package 层表达并可演进；**不得**要求向后兼容的实际实现 | `Final Import Contract` |

**Q7 —— serialization 层需要定义哪些 cross-cutting rules？**

| # | Rule | 现有 Design 状态 | 判定 |
| --- | --- | --- | --- |
| **C-1** | **text encoding** | `§4.2.2` 未定义 encoding 政策 | **必须由 Human Decision 确定**或记为 `NOT DEFINED` |
| **C-2** | **null representation** | `§4.2.12` 要求 `missing ≠ 0 ／ false ／ empty string ／ UNKNOWN`，但**未**规定 null 的物理表示 | **必须**确定；**不得**用 `0` ／ `""` ／ `UNKNOWN` 代替 null |
| **C-3** | **date representation** | logical type `DATE` 已定义；**物理表示未定义** | **必须**确定（**不得**引入 freshness threshold） |
| **C-4** | **datetime representation** | logical type `TIMESTAMP` 已定义；**时区政策未定义** | **必须**确定或记为 `NOT DEFINED`（`§4.4.42` **禁止**无依据新增 timezone policy） |
| **C-5** | **decimal representation** | `DECIMAL_QUANTITY` ／ `RATIO` ／ `PERCENTAGE` 已定义；**精度未定义**，且 `§2.4.8` ／ `§2.5.11` 明确 precision ／ rounding 由后续 Design Rule 决定 | **必须由 Human-approved Design Decision 确定**，**不得**在本 Review 自行决定（`§4.4.42`） |
| **C-6** | **boolean representation** | Canonical model **没有** `BOOLEAN` logical type（`§4.2.2` 十种类型无 boolean） | **可能 `NOT APPLICABLE`**；如未来出现，**必须**单独 Design |
| **C-7** | **enum ／ status representation** | `§4.2.14` 定义 status vocabulary；`sourcing_status` = `SOURCE-SPECIFIC` ／ Adapter-defined | **必须**区分「canonical vocabulary」与「source-specific vocabulary」；**不得**把 source value 当 canonical |
| **C-8** | **empty dataset representation** | `§4.4.4` 要求区分 `not included` 与 `included with zero records` | **必须**可表达 `record_count = 0` 且与「未声明」不同 |
| **C-9** | **character escaping** | 未定义 | **必须**由 format 决定，且**不得**引入 silent normalization（`§4.5.18`） |

**关键判定：** `C-1` ～ `C-5` ／ `C-9` 中**任何一项的取值都属于新的 representation 决定**；
`§4.4.42` 明确**禁止**在无现有 Design 支持时新增 `decimal precision` ／ `timezone policy` ／
`quantity rounding` 等。因此：

```
Serialization Format 的最终选择
  ⇒ 必然同时确定 C-1 ～ C-9 中若干项
  ⇒ 因此必须由 Human Decision 一次性授权
```

**Q8 —— 哪些属于 Serialization Format，哪些留给其他层？**

| 内容 | 归属 |
| --- | --- |
| text encoding ／ null ／ date ／ datetime ／ decimal ／ enum ／ empty dataset ／ escaping 的**表示规则** | **Serialization Format** |
| manifest 的**语义**（8 项） | `§4.3.8`（已 `DESIGN RESOLVED`） |
| manifest 的**承载方式**（是否独立 artifact ／ 是否与 dataset 同格式） | **Serialization Format ＋ Physical Dataset Layout（交界，需 Human Decision）** |
| directory tree ／ exact filename ／ file-per-dataset rule ／ dataset grouping ／ folder naming ／ manifest filename ／ archive filename | **Physical Dataset Layout** |
| source field → file column／carrier 的映射；`Stable Source Evidence Locator` 的物理承载 | **Field Carrier Mapping** |
| contract version 的演进与兼容规则；import 验收的最终合同条款 | **Final Import Contract** |
| integrity 证据的**算法**（SHA256 ／ MD5 ／ signature ／ checksum） | **Final Import Contract**（`§4.3.15` 只要求「evidence is required」） |

**Q9 —— 当前 repository evidence 是否足以做最终 format decision？**

**不足以作出最终选择；但足以界定 required properties 与 option trade-off。**

支持「不足以」的证据：

| # | 证据 | 影响 |
| --- | --- | --- |
| 1 | 当前为 **`SIMULATED` POC**，**没有真实** ERP vendor ／ version ／ schema ／ field list（`E05` ／ `E06` ／ `E07` = `UNKNOWN`） | 无法据真实 source artifact 形态选型 |
| 2 | `§4.4.42` **禁止**在无现有 Design 支持时新增 `decimal precision` ／ `timezone policy` ／ `quantity rounding` 等 | 最终选型**必然**触碰这些，**必须**有 Human Decision |
| 3 | `§4.3.1` 明确**不得定义** CSV ／ JSON ／ JSONL ／ Parquet ／ ZIP | 该决定属 **Human Decision** 层级，Agent **不得**自行落定 |
| 4 | `Physical Dataset Layout` 与 `Field Carrier Mapping` 仍 `DESIGN PENDING` | 选型的部分依据（carrier 形态、dataset 切分）**尚不存在** |
| 5 | Q2 ／ Q3 尚未裁定 | 单 ／ 多 format 与 manifest 承载会**改变** option 的可行性判定 |

支持「足以界定」的证据：

- `§4.3` 已给出全部**必须满足**的语义约束（R-1 ～ R-10）；
- `§4.2.2` 已给出 technology-neutral logical type 集合，option 与 type 的兼容性**可判定**；
- `§4.4.4` ／ `§4.2.12` 已给出 `missing` ／ empty ／ zero 的语义边界，`R-4` ／ `R-5` **可判定**。

**Q10 —— 需要 Human Decision 的具体问题是什么？**

见 **Human Decision Required**。

**Option Review**

> **判定约定：** 每个 Option 分别给出 **`技术上可行`** 与 **`当前 POC 最适合`** 两个独立判定。
> **不得**以 industry best practice ／ enterprise 惯例 ／ modern data stack 偏好作为选择依据。

**Option 0 —— Keep `Serialization Format = DESIGN PENDING`（Do Nothing）**

- **技术上可行：** 是 —— 与当前状态一致。
- **代价：** `Snapshot / Import Contract overall` 将**长期**保持 `DESIGN PENDING`；
  `Physical Dataset Layout` ／ `Field Carrier Mapping` ／ `Final Import Contract` **无法**在不选定
  承载方式前完成（三者均需要 dataset artifact 的表示前提）。
- **是否可接受为终点：** **不可接受为终点** —— 它不产生错误结果（fail-closed 保持），
  但会长期阻塞 Import Contract 的 closure，与 `§4.3.21` 的「不得提前标记完成」并不矛盾，
  却也**不构成** Design 进展。

**Option A —— CSV-oriented controlled export**

- 以 delimited text 承载 tabular logical dataset；manifest 另行承载。
- **优势：** human inspectability 最高（R-11）；工具链最少（R-12）；与「controlled export」语义直观一致。
- **风险：**
  - **R-3**：CSV **本身不含类型信息** —— `DATE` vs `TIMESTAMP`、`RATIO` vs `PERCENTAGE`、
    `DECIMAL_QUANTITY` vs `NON_NEGATIVE_QUANTITY` 的区分**必须**由外部 schema 提供，
    否则类型信息丢失 → **必须**同时定义 field-level 类型声明（属 `Field Carrier Mapping` 范围）。
  - **R-4**：CSV 对「空单元格」的语义**不唯一**（`missing` vs empty string）→ **必须**显式定义 null token。
  - **C-5**：`DECIMAL_QUANTITY` 的文本表示会引入**精度取舍** → 触发 `§4.4.42` 限制 → **需 Human Decision**。
  - **R-5**：`included with zero records` 只能通过 header-only 文件 ＋ manifest `record_count` 表达 → 可行但需显式规则。
- **技术上可行：** 是。
- **当前 POC 最适合：** **未判定**（本 Review 不选择）。

**Option B —— JSON ／ JSONL-oriented controlled export**

- **B-1 JSON（单文档）：** 可承载 nested ／ relationship 结构；类型自描述（`null` 原生支持 → R-4 友好）。
- **B-2 JSONL（逐行对象）：** 保留 JSON 的类型表达能力，同时**接近** tabular ／ 流式处理形态。
- **优势：**
  - `null` 原生 → **R-4** ／ **R-5** 表达力最强；
  - 类型可显式标注（R-3）；
  - human inspectability 高（R-11）；
  - 工具链常见（R-12）。
- **风险：**
  - **数字精度**：JSON number 在不同实现中的 decimal 处理**不一致** → **C-5** **必须**显式规定
    （字符串化 decimal 或明确精度）→ 触发 `§4.4.42` → **需 Human Decision**。
  - **date ／ datetime**：JSON **无** date 类型 → **C-3** ／ **C-4** **必须**显式规定（含 timezone 政策）→ 同上。
  - **R-1**：JSON 允许重复 key ／ 顺序无关 ／ 数字格式多样 → **必须**显式收紧（否则无法保证 deterministic parsing）。
  - **R-2**：若同时使用 JSON 与 JSONL，**同一 field 的表示一致性规则**必须定义。
- **技术上可行：** 是。
- **当前 POC 最适合：** **未判定**。

**Option C —— Parquet-oriented controlled export**

- 以 columnar binary 承载 tabular dataset；schema 内嵌。
- **优势：**
  - **R-3** 最强：类型由 schema 承载（含 decimal ／ timestamp）；
  - 大 dataset 适用性最好；压缩与 IO 效率高；
  - 与 future Adapter ／ analytics 生态兼容性高。
- **风险：**
  - **R-3 的另一面：** schema 内嵌意味着**必须**在本层确定 `DECIMAL(p,s)` ／ timestamp unit ／ timezone 等
    **物理类型参数** → **直接触发** `§4.4.42` 的禁止项 → **必须** Human-approved Design Decision；
    且 `§4.2.2` 明确**不得**把 logical type 映射成 `DECIMAL(18,2)` 等数据库类型 ——
    该映射本身**需要**新的 Design 授权。
  - **R-11**：human inspectability 最低（需专用工具）；
  - **R-12**：工具链复杂度与实现面最高；
  - **R-1**：需显式规定 writer 参数（否则同一数据的 bytes 不稳定；但**语义**层仍可 deterministic）。
- **技术上可行：** 是（但**必须**先获得 physical type 映射的 Human-approved Design 授权）。
- **当前 POC 最适合：** **未判定**。

**Option D —— Hybrid serialization strategy**

- 例如：manifest ＋ 部分 dataset 用 tabular text，部分 dataset 用 JSONL；或 text 为对外形态 ＋ 内部转换为 columnar。
- **优势：** 可按 dataset 特性选择（如大 dataset 用 columnar，小 dataset 用 text）；
  在某些 dataset 上同时取得 inspectability 与效率。
- **风险（决定性）：**
  - **R-2 被直接削弱** —— 「同一 canonical field 在不同 dataset 中的表示一致性」**必须**新增规则，
    而该规则**当前不存在**；
  - **R-1 ／ R-12 复杂化** —— 需要多套 reader ／ writer 与跨 format 验证；
  - **Q2 ／ Q3 未裁定** → hybrid 的边界**无法**在现有 Design 下确定；
  - 与 `§4.3.6` package-level atomicity **不冲突**，但要求 import 侧对**全部** format 一致地执行 fail-closed。
- **技术上可行：** 是（**前提**是 Q2 ／ Q3 已裁定且 R-2 一致性规则已定义）。
- **当前 POC 最适合：** **未判定**；**POC 适用性判断**倾向于**降低 format 数量**（R-12）。

**Option Comparison**

`既有` = 受既有 Design 约束；`⚠` = 需要新的 Human-approved representation 决定；
`—` = 不适用。判定针对**生产可用**形态，**不**代表本 Review 的选择。

| 维度 | Option 0（Keep PENDING） | Option A（CSV） | Option B（JSON ／ JSONL） | Option C（Parquet） | Option D（Hybrid） |
| --- | --- | --- | --- | --- | --- |
| deterministic parsing | — （未选型） | 中 —— 需显式 null ／ escaping ／ decimal 规则 | 中高 —— 需显式收紧 JSON 宽松性 | 高 —— schema 驱动，但需固定 writer 参数 | 低 —— 跨 format 一致性成本最高 |
| schema clarity | — | 低 —— **无内嵌类型**，须外部声明 | 中 —— 可自描述，但需显式约束 | 高 —— 内嵌 schema | 中 —— 依组合而定 |
| human inspectability | — | **最高** | **高** | **最低** | 中高 |
| tooling complexity | 最低（不选型） | **低** | 低中 | **高** | **高** |
| nested ／ relationship representation | — | **弱** —— 需扁平化 ／ 关联键 | **强**（JSON）／ 中（JSONL） | 中 —— 需重复 ／ 嵌套类型 | 强 |
| decimal ／ date fidelity | — | **⚠ 需 Human Decision**（文本精度 ／ 日期字面量） | **⚠ 需 Human Decision**（number 精度 ／ 日期 ／ timezone） | **⚠ 需 Human Decision**（physical type 映射，`§4.2.2` 禁止直接映射） | **⚠ 同上，且需跨 format 一致** |
| large dataset suitability | — | 低中 | 中 | **最高** | 高 |
| manifest compatibility | — | 需另行承载 manifest（Q3 未裁定） | 可同格式（Q3 未裁定） | 需另行承载 manifest（schema 不同） | 依组合而定 |
| implementation complexity | — | **低** | 低中 | **高** | **最高** |
| POC suitability（判断，非约束） | 不构成进展 | 高（若接受外部类型声明） | 高（若接受显式收紧） | 低（当前 `SIMULATED` POC 无真实 schema 依据） | 低中 |
| future Adapter compatibility | — | 中 —— 依赖 source 侧导出能力 | 中高 | **高** | 高 |

**关键观察（基于上表）：**

1. **没有任何 Option 可以「零新增 representation 决定」落地** —— A ／ B ／ C ／ D 均触发 **`⚠`**；
   这是 `§4.4.42` 的直接后果，**不是**某一 option 的缺陷。
2. **Option C 的 `⚠` 最重** —— 它要求的 physical type 映射与 `§4.2.2`「不得映射成数据库类型」**直接相邻**，
   需要**明确**的 Human Design 授权才能成立。
3. **Option A 的 `⚠` 最集中** —— 只需外部类型声明 ＋ null token ＋ decimal ／ date 字面量规则。
4. **Option D 的 `⚠` 数量最多** —— 且额外要求当前**不存在**的 R-2 跨 format 一致性规则。
5. **R-11 ／ R-12（`POC` 类）** 在 A ／ B 上更优，在 C 上最弱 —— 但**二者不构成**对最终选择的强制约束。

**本 Review 不选择任何 Option。** 选择属 **Human Decision**。

**Critical Semantic Boundaries**

Serialization Format **不得**改变以下区分。若某一 format **无法**表达某一行，
则该 format 在**该维度上不可接受**（无论其他维度多优）：

| # | 必须保持的区分 | Serialization 义务 | 依据 |
| --- | --- | --- | --- |
| **B-1** | `Zero ≠ Missing` | 必须能表达「字段不存在」且**不**等同于 `0` | `§4.2.12` |
| **B-2** | valid absence ≠ missing required data | 「不适用 ／ 不产生」必须可与「缺失」区分 | `§4.2.12` ／ `§4.3.13` |
| **B-3** | not applicable ≠ unresolved | 两者**不得**共用同一表示 | `§4.2.12` ／ `§4.4` |
| **B-4** | Package structural failure ≠ Business `DATA_INCOMPLETE` | import 层结构判定**不得**由 serialization 推断业务完整性 | `§4.3.12` |
| **B-5** | dataset not included ≠ empty dataset | `record_count = 0` 必须与「未声明」不同 | `§4.3.12` ／ `§4.4.4` |
| **B-6** | logical dataset role ≠ physical filename | serialization **不得**把 role 绑定为文件名 | `§4.3.10` ／ `§4.5.22` |
| **B-7** | dataset-level provenance reference ≠ `Stable Source Evidence Locator` | 两层**不得**合并为同一字段 | `§4.3.8` ／ `§4.3.16` |
| **B-8** | Snapshot Package identity ≠ Analysis Run identity | 两者**不得**共用同一字段 ／ 命名空间 | `§4.3.2` ／ `§4.3.4` |

**Physical Layout Boundary**

本 Review **不得**定义（且**未**定义）：

```
directory tree
exact filename
file-per-dataset rule
dataset grouping
folder naming
manifest filename
archive filename
source field → file column mapping
```

**记录的 dependency（不自行解决）：**

| # | Dependency | 状态 |
| --- | --- | --- |
| **D-1** | 若选择「多 artifact」形态（含 Option A 的 file-per-dataset、Option C），则 `Physical Dataset Layout` **必须**定义 package container（directory 或 archive） | **待 Human Decision（Q2 ／ Q5）** |
| **D-2** | `Field Carrier Mapping` 必须提供 **field-level 类型声明**（Option A 必需；B ／ C 加强） | 依赖 Serialization 选择 |
| **D-3** | `Field Carrier Mapping` 必须定义 `Stable Source Evidence Locator` 的**物理承载** | 与 `§4.3.17` 一致（physical 层面仍未决定） |
| **D-4** | `Final Import Contract` 必须定义 integrity **算法**与 version 兼容规则 | `§4.3.15` 只要求 evidence 存在 |
| **D-5** | Q2 ／ Q3 未裁定前，Option A ／ B ／ C ／ D 的**可行性判定都可能改变** | **阻塞最终选择** |

**Known Risks**

| # | Risk | 说明 |
| --- | --- | --- |
| **K-1** | **以 industry practice 代替 Design 依据** | 例如「现代数据栈用 Parquet」／「企业导出通常用 CSV」。`§4.4.42` 明确禁止此类理由；本 Review 已按证据约束评估 |
| **K-2** | **把 logical type 直接映射为物理类型** | `§4.2.2` 明确禁止；若选 Option C ／ B 的 typed 形态，**必须**另有 Human-approved 授权 |
| **K-3** | **silent normalization 通过 serialization 回流** | trim ／ case ／ prefix 去除等会使 `§4.5.18` 的禁止失效 |
| **K-4** | **用 `0` ／ 空字符串代替 null** | 直接破坏 B-1 ／ B-2；CSV 尤其高风险 |
| **K-5** | **`record_count = 0` 与「未声明」不可区分** | 破坏 B-5；若 manifest 与 dataset 混为一体，风险显著上升 |
| **K-6** | **serialization 隐含 physical precision 决策** | `C-5`（decimal）／ `C-1`（encoding）／ `C-4`（timezone）在本 Review 中**未**决定；若实现阶段自行取值，等于绕过 `§4.4.42` |
| **K-7** | **本 Review 结论被误读为 format 已选定** | 本 Review **未**选择任何 Option |
| **K-8** | **`§4.3.1` 的「不得定义 CSV ／ JSON ／ JSONL ／ Parquet ／ ZIP」被误读为永久禁止** | 该限制约束的是**当时**的 Task；后续决定**必须**由 **Human Decision 明确授权**，而非 Agent 自行解禁 |
| **K-9** | **多 format 引入未定义的 R-2 一致性规则** | Option D 的直接风险 |

**Review Conclusion**

基于 Repository 中已存在的正式设计事实：

1. **Serialization Format 的最低要求已可明确界定**：**R-1 ～ R-10**（全部来自既有 Design），
   加上 **R-11 ／ R-12**（`POC` 类判断）。这构成后续 closure 的可验证基础。
2. **10 个 Review Question 中**：`Q1` ／ `Q4` ／ `Q5` ／ `Q6` ／ `Q7` ／ `Q8` 已获**证据性回答**；
   `Q2` ／ `Q3` 属 **Human Decision**；`Q9` = **evidence 不足以作最终选择**；`Q10` 已列出具体决策点。
3. **四个候选 Option（A ／ B ／ C ／ D）与 Option 0 均已评估**：
   **没有任何 Option 可以「零新增 representation 决定」落地** —— 这是 `§4.4.42` 的直接后果。
4. **本 Review 不选择最终 format**，也**不**推荐某一个 Option 作为「已定方案」。
   **`Serialization Format` 保持 `DESIGN PENDING`。**
5. **不推进** `Physical Dataset Layout` ／ `Field Carrier Mapping` ／ `Final Import Contract`；
   dependency **D-1** ～ **D-5** 已记录，未自行解决。
6. **未**修改任何 canonical entity ／ field ／ `BR-*` ／ Validation Taxonomy ／ Master Data Mapping ／
   Adapter Boundary；**未**创建 JSON Schema ／ CSV ／ Parquet ／ parser ／ runtime enum。

**Current Status（本 Review 时点）**

```
Snapshot / Import Contract overall = DESIGN PENDING
  Package Envelope                 = DESIGN RESOLVED
  Atomicity Boundary               = DESIGN RESOLVED
  Immutability Boundary            = DESIGN RESOLVED
  Analysis Run Linkage             = DESIGN RESOLVED
  Serialization Format             = DESIGN PENDING   ← 本 Review 未关闭
  Physical Dataset Layout          = DESIGN PENDING
  Field Carrier Mapping            = DESIGN PENDING
  Final Import Contract            = DESIGN PENDING

Master Data Mapping overall        = DESIGN RESOLVED
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

**Human Decision Required**

| # | 问题 | 性质 |
| --- | --- | --- |
| 1 | 是否授权在 POC 中**确定** `Serialization Format`（即明确解禁 `§4.3.1` 的「不得定义 CSV ／ JSON ／ JSONL ／ Parquet ／ ZIP」）？ | authorization |
| 2 | **单一 format**，还是**允许不同 logical dataset 使用不同 format**？（若允许混合，**必须**同时裁定 R-2 跨 format 一致性规则） | 选型前提 |
| 3 | **Snapshot Manifest 的承载**：是否为**独立 artifact**？是否与 business dataset **同格式**？（`Snapshot Manifest ≠ business dataset` 必须保持） | 选型前提 |
| 4 | 是否接受 **R-1 ～ R-12** 作为 `Serialization Format` 的 minimum required properties ／ closure criteria？ | criteria |
| 5 | **Cross-cutting rules 的取值**（`C-1` ～ `C-9`）：哪些本轮决定，哪些记为 `NOT DEFINED`？（`§4.4.42` 要求无依据即 `NOT DEFINED`） | representation |
| 6 | 是否接受 **decimal 精度（`C-5`）／ timezone（`C-4`）／ quantity rounding** 属于**必须由 Human-approved Design Decision** 决定的项目，**不得**由 Agent 或实现阶段自行取值？ | `§4.4.42` 边界 |
| 7 | 是否接受 **package container（directory ／ archive）属于 `Physical Dataset Layout`**，本 Review 只记录 dependency（`D-1`）？ | boundary |
| 8 | 是否接受**选项裁定顺序**：先裁 `Q2` ／ `Q3`，再裁 format（因 `D-5` 会使可行性判定改变）？ | 决策结构 |
| 9 | 是否授权后续**独立 Serialization Format Implementation PR**（登记选择 ＋ cross-cutting rules ＋ 同步 current-state），并在满足 `R-1` ～ `R-12` 时允许 `Serialization Format` `DESIGN PENDING → DESIGN RESOLVED`？ | follow-up |
| 10 | 是否确认 `Snapshot / Import Contract overall` 在 `Physical Dataset Layout` ／ `Field Carrier Mapping` ／ `Final Import Contract` 完成前**保持 `DESIGN PENDING`**？ | boundary |

**本 Review 不作出上述任何决定。** 后续必须由 **Human Decision** 裁定；
**不得**由 Agent 自行选择最终 format。

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

> 本节是对**上方 Review Finding**
> （**Serialization Format Design Review（Review Finding）**）的 **Human Decision**。
>
> 上方 Review Finding 的 **Review Authority / Scope** ／ **Review Question** ／ **Existing Constraints** ／
> **Required Serialization Properties** ／ **10 Questions Assessment** ／ **Option Review** ／
> **Option Comparison** ／ **Critical Semantic Boundaries** ／ **Physical Layout Boundary** ／
> **Known Risks** ／ **Review Conclusion** ／ **Current Status（本 Review 时点）** ／
> **Human Decision Required**
> **全部保留，未删除、未改写** —— 其中包括 Review 时点的
> `Q9 = evidence insufficient` 与 **Option A ／ B ／ C ／ D 的完整比较**。

**决定 1 —— PR #51 Review Finding = ACCEPTED**

正式接受 Review Finding 的主要事实判断：

```
Controlled Export / Snapshot            = 仍为 Integration Pattern
Snapshot Package                        = immutable input evidence package
Snapshot Package ≠ Analysis Run         = 保持
silent cross-snapshot mixing            = 禁止
Logical Provenance Carrier              = DESIGN RESOLVED
Physical Carrier Realization            = DESIGN PENDING
R-1 ～ R-10                             = 既有 Design 强约束
CSV ／ JSON ／ JSONL ／ Parquet ／ Hybrid = 均技术可行，
                                          但都需要新的 physical representation decision
Physical Dataset Layout                 = DESIGN PENDING
Field Carrier Mapping                   = DESIGN PENDING
Final Import Contract                   = DESIGN PENDING
```

并接受：**当前必须由 Human Decision 明确 `Serialization Format`。**

**决定 2 —— Serialization Strategy = `Option B`（JSON-oriented controlled export）**

正式选择：

```
Option B
  = JSON-oriented controlled export

POC v0.2 的 Serialization Strategy
  = single JSON serialization strategy
```

具体：

```
Snapshot Manifest        = 独立 artifact ＋ JSON serialization
Business dataset         = JSON serialization
```

本版本**不采用**：

```
JSONL
CSV
Parquet
Hybrid multi-format strategy
```

**决定 3 —— Option Decisions（正式记录）**

```
Option A  CSV           = NOT SELECTED
Option B  JSON          = SELECTED
JSONL                   = NOT SELECTED FOR POC v0.2
Option C  Parquet       = NOT SELECTED
Option D  Hybrid        = NOT SELECTED
Option 0  Keep Pending  = NOT SELECTED
```

**决定 4 —— Single-Format Boundary = CONFIRMED**

POC v0.2 使用**单一** serialization format：**JSON**。

**不得**允许不同 logical dataset 自行选择不同 format。因此：

```
R-2 cross-format consistency problem = NOT INTRODUCED
```

同一 canonical logical type **必须**在所有 JSON serialized dataset 中保持**同一 representation rule**。

**决定 5 —— Manifest Decision = CONFIRMED**

```
Snapshot Manifest                   = independent artifact
Snapshot Manifest serialization     = JSON
Business dataset serialization      = JSON
```

**必须保持：**

```
Snapshot Manifest  ≠  business dataset
```

**但二者使用同一 serialization format family。**

本决定**不定义**：

```
manifest filename
directory
package container
archive
business dataset filename
file-per-dataset layout
```

以上继续留给 **`Physical Dataset Layout`**。

**决定 6 —— Required Properties Decision = AMENDED ＋ APPROVED**

```
R-1 ～ R-10 = MANDATORY SERIALIZATION CLOSURE CRITERIA
R-11        = POC DESIGN OBJECTIVE（human inspectability）
R-12        = POC DESIGN OBJECTIVE（implementation simplicity）
```

`R-11` ／ `R-12` **必须评估**，但**不作为**单独的 hard closure blocker。

**不得**把主观的「够不够简单」／「够不够容易人工查看」变成**不可验证**的 closure Gate。

**决定 7 —— `C-1` Text Encoding = APPROVED**

```
UTF-8
UTF-8 without BOM
```

**不得依赖**：system locale ／ platform default encoding。

**决定 8 —— `C-2` Missing / Null = APPROVED**

```
JSON null = explicit missing / unavailable serialized value
```

**不得**把以下当作 missing 的替代：

```
0
false
""
"UNKNOWN"
```

```
字段 property omission = field 未 serialized
```

其业务含义**必须**根据 **canonical requiredness ＋ business applicability** 判断。因此：

```
omitted field  可以是 valid absence
               也可以是 missing required data
```

具体结果由**既有 Business ／ Validation semantic**判断，**不得**由 serializer 自行猜测。

对于 **valid absence ／ not produced by design**：**优先允许 property omission**。

**不得**为了「字段完整」强制写 `null` ／ `0` ／ `""` ／ `"N/A"`。

**决定 9 —— `C-3` DATE = APPROVED**

Canonical `DATE` 使用：

```
YYYY-MM-DD
```

**不得**：locale-specific date ／ `MM/DD/YYYY` ／ `DD/MM/YYYY` ／ 自然语言日期。

**决定 10 —— `C-4` TIMESTAMP ／ Timezone = APPROVED**

Canonical ／ transport `TIMESTAMP` 使用：

```
ISO 8601 / RFC 3339 compatible representation
+ explicit UTC offset 或 Z
```

**不得**：silent timezone inference ／ system-local timezone assumption ／ timezone guessing。

本决定**只定义 serialization representation**，**不定义**新的：

```
business timezone policy
freshness policy
```

**不得**通过 serialization 偷偷改变既有 business time semantic。

**决定 11 —— `C-5` Decimal ／ Quantity Representation = APPROVED**

对 `DECIMAL_QUANTITY` ／ `NON_NEGATIVE_QUANTITY` ／ `RATIO` ／ `PERCENTAGE` 采用：

```
base-10 decimal string representation
```

**不得**使用 **binary floating-point** 作为 canonical serialization contract。

允许的 conceptual lexical form（示例）：

```
"125.5"
"0"
"0.035"
```

**不得**使用：locale comma ／ thousands separator ／ scientific notation 作为 canonical representation。

本决定：

```
不新增 decimal precision
不新增 fixed scale
不新增 quantity rounding rule
```

serializer **必须**：

```
不得自行 round
不得自行 quantize
不得自行 truncate
```

因此保持既有 Design Boundary：

```
decimal precision   = NOT DEFINED
quantity rounding   = NOT DEFINED
```

**决定 12 —— `C-6` Boolean = CONFIRMED**

当前 Canonical Data Model **没有** `BOOLEAN` logical type。因此：

```
BOOLEAN canonical representation = NOT APPLICABLE FOR CURRENT POC
```

**不得**为了 serialization 新增 boolean canonical field。

**决定 13 —— `C-7` Enum ／ Status = APPROVED**

Canonical enum ／ status 使用**既有 canonical literal 的 exact string representation**。必须：

```
case-sensitive
no silent normalization
no trim-based semantic conversion
no synonym mapping
```

**source-specific vocabulary 仍保持 source-specific。**

尤其：

```
sourcing_status 不得被 serializer 自动变成 canonical status
```

**决定 14 —— `C-8` Empty Dataset = CONFIRMED**

**必须保持：**

```
dataset not included  ≠  dataset included with zero records
```

`Manifest` 是 **dataset presence 的 authoritative package-level evidence**。

```
included dataset + record_count = 0
  = structurally valid empty dataset
```

其 **exact physical JSON dataset envelope** 留给：

```
Physical Dataset Layout / Field Carrier Mapping
```

**本 Human Decision 不定义。**

**决定 15 —— `C-9` JSON Parsing ／ Escaping = APPROVED**

JSON **必须 strict parse**。**禁止接受**：

```
duplicate object keys
comments
trailing comma
NaN
Infinity
implementation-specific extension
```

Character escaping **遵守标准 JSON escaping**。

**Object member order 不得具有 business semantic。**

**不得**把以下作为 import fix-up：

```
silent trim
silent case conversion
silent Unicode normalization
silent numeric coercion
```

**决定 16 —— Determinism Boundary = CONFIRMED**

```
Deterministic Parsing  ≠  Byte-for-byte Canonical JSON Encoding
```

本阶段要求：

```
同一 compliant JSON input 必须产生相同 canonical semantic value
```

**不要求**：

```
object key 固定排序
canonical byte ordering
JSON canonicalization algorithm
```

如果后续 **integrity contract** 需要 **byte-level hash ／ canonicalization**：
由 **`Final Import Contract`** 单独决定。

**决定 17 —— Physical Layout Boundary = CONFIRMED**

以下**全部属于** `Physical Dataset Layout`：

```
package container
directory / archive
directory tree
filename
file-per-dataset rule
dataset grouping
manifest filename
```

**本 Human Decision 不作上述决定。**

**决定 18 —— Field Carrier Boundary = CONFIRMED**

本决定**不定义**：

```
source field → JSON property mapping
canonical field → concrete JSON property name
Stable Source Evidence Locator 的 physical JSON carrier
dataset envelope structure
```

以上属于 **`Field Carrier Mapping`** 或 **`Physical Dataset Layout`**，后续独立处理。

**决定 19 —— Final Import Contract Boundary = CONFIRMED**

以下继续留给 **`Final Import Contract`**：

```
integrity algorithm
hash algorithm
signature policy
contract version evolution rules
backward / forward compatibility
final import acceptance contract
byte-level canonicalization（如未来需要）
```

**决定 20 —— Follow-up Implementation Authorization = AUTHORIZED**

授权后续**独立** `Serialization Format` Design Change ／ Implementation PR 实施：

```
1. 正式登记 JSON serialization strategy
2. 正式登记 C-1 ～ C-9
3. 正式登记 R-1 ～ R-10 = mandatory closure criteria
4. 正式登记 R-11 ／ R-12 = POC design objectives
5. 同步 current-state references
6. 执行 serialization closure validation
```

**如果**：

```
R-1 ～ R-10 = ALL PASS
并且 JSON representation rules 已完整登记
并且没有发现新的 blocking contradiction
```

**则授权**：

```
Serialization Format   DESIGN PENDING → DESIGN RESOLVED
```

**本 PR 不执行上述任何一项。**

**决定 21 —— Historical Record Preservation = CONFIRMED**

**PR #51 Review Finding 必须完整保留**，尤其**不得回写**：

```
Q9 evidence insufficient
Option A ／ B ／ C ／ D comparison
Current Status（本 Review 时点）
Human Decision Required
```

本节的 **Human Decision Record** 是对其的**最终裁定**，通过**新增记录**表达，
**不修改** Review Finding 原文。

**决定 22 —— Explicit Non-Authorization**

本 Human Decision **不授权**：

```
directory tree
filename
archive format
ZIP
file-per-dataset rule
source field mapping
JSON Schema
concrete dataset envelope
parser implementation
Adapter
database schema
real ERP mapping
integrity hash algorithm
new canonical entity
new canonical field
BR-* changes
Validation Taxonomy changes
decimal precision
quantity rounding rule
business timezone policy
```

**执行状态（PR #51 Human Decision 时点）**

```
PR #51 Review Finding                = ACCEPTED
Serialization Strategy               = Option B（JSON-oriented controlled export）
Single-Format Boundary               = JSON only（R-2 cross-format problem = NOT INTRODUCED）
Snapshot Manifest                    = independent artifact ＋ JSON
Business dataset serialization       = JSON
R-1 ～ R-10                          = MANDATORY SERIALIZATION CLOSURE CRITERIA
R-11 ／ R-12                         = POC DESIGN OBJECTIVES
C-1 ～ C-9                           = APPROVED（JSON representation policy）
decimal precision                    = NOT DEFINED
quantity rounding                    = NOT DEFINED
business timezone policy             = NOT DEFINED
Option A ／ JSONL ／ C ／ D ／ Option 0 = NOT SELECTED
Follow-up conditional closure        = AUTHORIZED

Serialization Format                 = DESIGN PENDING   ← 未关闭（implementation 尚未执行）
Physical Dataset Layout              = DESIGN PENDING
Field Carrier Mapping                = DESIGN PENDING
Final Import Contract                = DESIGN PENDING
Snapshot / Import Contract overall   = DESIGN PENDING
Adapter Boundary                     = DESIGN PENDING
POC Design v0.2                      = DRAFT
```

**本 PR 只记录 Human Decision。** **未**实施 JSON serialization，
**未**修改 `Serialization Format` status，**未**推进 `Physical Dataset Layout` ／
`Field Carrier Mapping` ／ `Final Import Contract`。

**Serialization Format Implementation Record（Human-authorized Design Change）**

**Human Authorization Source**

```
PR #51 Human Decision — Human-approved
  → 决定 2：Serialization Strategy   = Option B（JSON-oriented controlled export）
  → 决定 3：Option Decisions         = B SELECTED；A ／ JSONL ／ C ／ D ／ Option 0 NOT SELECTED
  → 决定 4：Single-Format Boundary   = CONFIRMED
  → 决定 5：Manifest Decision        = independent artifact ＋ JSON
  → 决定 6：R-1 ～ R-10 = mandatory；R-11 ／ R-12 = objectives
  → 决定 7 ～ 15：C-1 ～ C-9          = APPROVED
  → 决定 16：Determinism Boundary    = CONFIRMED
  → 决定 17 ～ 19：下三层 boundary     = CONFIRMED
  → 决定 20：registration ＋ conditional closure = AUTHORIZED
  → 决定 21 ／ 22：Historical Preservation ／ Explicit Non-Authorization
```

**Registered Strategy ／ Criteria ／ Policy**

| 项 | 登记位置 |
| --- | --- |
| JSON strategy（single JSON；manifest = independent artifact ＋ JSON；datasets = JSON） | **`§4.3.22 A`** |
| `R-1` ～ `R-10` = MANDATORY SERIALIZATION CLOSURE CRITERIA | **`§4.3.22 B`** |
| `R-11` ／ `R-12` = POC DESIGN OBJECTIVES | **`§4.3.22 B`** |
| `C-1` ～ `C-9` JSON representation policy | **`§4.3.22 C`** |
| Determinism Boundary | **`§4.3.22 D`** |

**Representation Completeness Audit（逐 logical type）**

| Logical type | 已登记的 representation rule | 判定 |
| --- | --- | --- |
| `DATE` | `C-3`：`YYYY-MM-DD` | **COVERED** |
| `TIMESTAMP` | `C-4`：RFC 3339 compatible ＋ explicit offset ／ `Z` | **COVERED** |
| `DECIMAL_QUANTITY` | `C-5`：base-10 decimal string | **COVERED** |
| `NON_NEGATIVE_QUANTITY` | `C-5`：base-10 decimal string | **COVERED** |
| `RATIO` | `C-5`：base-10 decimal string | **COVERED** |
| `PERCENTAGE` | `C-5`：base-10 decimal string | **COVERED** |
| `STATUS` | `C-7`：exact canonical literal string | **COVERED** |
| `BOOLEAN` | `C-6`：`NOT APPLICABLE`（canonical model 无此 logical type） | **N/A** |
| `TEXT_CONTEXT` | 无显式规则；但 JSON 对文本**只有唯一**标量形式（string），**不存在**竞争表示 | **COVERED（observation）** |
| **`IDENTIFIER`** | **无任何经 Human Decision 批准的 representation rule** | **NOT COVERED** |
| **`ANALYSIS_RUN_ID`** | **无任何经 Human Decision 批准的 representation rule** | **NOT COVERED** |

**Gap `G-S1`（BLOCKING）**

| 项 | 内容 |
| --- | --- |
| **Gap** | `IDENTIFIER` 与 `ANALYSIS_RUN_ID` 的 **JSON 标量表示形式未被任何已批准规则固定** —— string（`"1001"`）与 number（`1001`）两种形式**都未被排除** |
| **证据** | `§4.2.2` 只声明 logical type 语义，并**禁止**把 logical type 映射成 `VARCHAR` ／ `DECIMAL(18,2)` ／ `UUID` ／ `BIGINT` ／ `JSONB` 等**数据库类型** —— 该约束针对 canonical type 声明，**未**给出 JSON 标量表示规则；`§4.4.26` **明确不得定义** identifier 的 `regex` ／ `code length` ／ `prefix` ／ **`numeric-only`** ／ case normalization ／ source-system format；`§4.3.3` 又**不规定** `snapshot_package_id` 的生成算法（UUID ／ hash ／ sequence ／ timestamp-based 均可能）。PR #51 Human Decision 的 `C-1` ～ `C-9` **未包含** identifier ／ analysis run id 的表示规则 |
| **Impact** | 同一 canonical field 的 JSON 形式**未被固定** ⇒ **`R-2`** 无法保证「跨 dataset ／ package 表示一致」；**`R-3`** 无法保证 logical type 无损；`snapshot_package_id` 的形式歧义**实际存在** |
| **Why it blocks** | `R-2` ／ `R-3` 均为 **mandatory closure criteria**；表示未固定即**无法判定 PASS** |
| **不得自行填补** | 新增 identifier 的 JSON 表示规则属**新的 representation 决定**；PR #51 Human Decision **未授权**；`§4.4.42` 亦**禁止**在无现有 Design 支持时新增 identifier 约束。**本 Record 不填补该 Gap。** |

**R-1 ～ R-10 Validation Result**

| # | Criterion | Result | 依据 |
| --- | --- | --- | --- |
| **R-1** | Deterministic Parsing | **PASS** | `C-9` strict parse ＋ `C-1` ／ `C-3` ／ `C-4` ／ `C-5` ／ `C-7` 的 lexical 规则 |
| **R-2** | Stable Field Representation | **FAIL** | `G-S1`（`IDENTIFIER` ／ `ANALYSIS_RUN_ID` 形式未固定） |
| **R-3** | Logical Type Preservation | **FAIL** | `G-S1`（与 `R-2` **同一根因**） |
| **R-4** | Missing ≠ Present-with-Default | **PASS** | `C-2` |
| **R-5** | Dataset-Level Absence Expressible | **PASS** | `C-8` ＋ Manifest authoritative package-level evidence |
| **R-6** | Manifest Metadata Carriage | **PASS** | Manifest = independent artifact ＋ JSON；`§4.3.8` 的 8 项语义可由 JSON string ／ array ／ object 承载 |
| **R-7** | Integrity Evidence Carriage | **PASS** | `§4.3.15` 只要求 integrity evidence **可承载**；算法归 `Final Import Contract` |
| **R-8** | Reproducibility | **PASS** | `§4.3.4` ／ `§4.3.5` ＋ 决定 16（member order 无 business semantic） |
| **R-9** | Contract Version Expressibility | **PASS** | `§4.3.8` 的 `contract version` 可在 manifest 承载 |
| **R-10** | Adapter Neutrality | **PASS** | 不要求 Adapter ／ 直连源系统（`§4.3.19`） |

```
R-1 ～ R-10 = NOT ALL PASS（R-2 ／ R-3 = FAIL）
```

**R-11 ／ R-12 Assessment（POC DESIGN OBJECTIVES，非 hard blocker）**

| # | Objective | Assessment |
| --- | --- | --- |
| **R-11** | Human Inspectability | **SATISFIED** —— JSON text ＋ `C-1` UTF-8 no BOM ＋ `C-9` standard escaping，可由人工直接阅读 |
| **R-12** | Implementation Simplicity | **SATISFIED** —— single format；不需外部 schema 定义；不引入 columnar 工具链 |

**New Blocking Contradiction Audit**

```
G-S1（IDENTIFIER ／ ANALYSIS_RUN_ID representation 未固定）  = BLOCKING
其他新增 blocking contradiction                                = NONE
```

同时确认：本次 registration **未**在 `§4.3` 内部产生 contradiction；
`§4.3.21` 的 `serialization format determined`（false）与 `§4.3` 层级表
`Serialization Format = DESIGN PENDING` 与 **Gate FAIL** 结果**一致** —— 无需同步。

**Conditional Closure Result**

```
R-1 ～ R-10                  = NOT ALL PASS（R-2 ／ R-3 = FAIL）
C-1 ～ C-9                   = FULLY REGISTERED
New Blocking Contradiction   = G-S1
  → conditional closure gate  = FAIL
```

因此**不执行** closure：

```
Serialization Format   = DESIGN PENDING   ← 保持不变
```

**不得**由 Agent 自行填补 `G-S1`；必须重新进入 **Human Attention**。

**Historical Preservation（未回写）**

- **PR #51 Serialization Format Review Finding** —— 含 `Q9 = evidence insufficient` ／
  Option A ／ B ／ C ／ D 完整比较 ／ `Current Status（本 Review 时点）` ／ `Human Decision Required`
- **PR #51 Human Decision Record** —— 含 `Serialization Format = DESIGN PENDING`
  （implementation 尚未执行）与 `执行状态（PR #51 Human Decision 时点）`

**Downstream Boundary（保持）**

```
Physical Dataset Layout  = DESIGN PENDING
  （package container ／ directory ／ archive ／ directory tree ／ filename ／
    file-per-dataset rule ／ dataset grouping ／ manifest filename ／ exact dataset envelope）

Field Carrier Mapping    = DESIGN PENDING
  （source field → JSON property mapping ／ canonical field → concrete JSON property name ／
    Stable Source Evidence Locator 的 physical JSON carrier ／ physical provenance carrier ／
    dataset envelope structure）

Final Import Contract    = DESIGN PENDING
  （integrity algorithm ／ hash algorithm ／ signature policy ／ byte-level canonicalization ／
    contract version evolution rules ／ backward-forward compatibility ／ final import acceptance contract）
```

**Final Current State（本 Task 完成时点）**

```
Package Envelope                    = DESIGN RESOLVED
Atomicity Boundary                  = DESIGN RESOLVED
Immutability Boundary               = DESIGN RESOLVED
Analysis Run Linkage                = DESIGN RESOLVED
Serialization Format                = DESIGN PENDING   ← conditional closure gate = FAIL
Physical Dataset Layout             = DESIGN PENDING
Field Carrier Mapping               = DESIGN PENDING
Final Import Contract               = DESIGN PENDING
Snapshot / Import Contract overall  = DESIGN PENDING
Adapter Boundary                    = DESIGN PENDING
POC Design v0.2                     = DRAFT
```

**Human Attention Required**

| # | 需要 Human Decision 的问题 |
| --- | --- |
| 1 | 是否授权 **`IDENTIFIER` 与 `ANALYSIS_RUN_ID`** 的 JSON 标量表示为 **JSON string**（exact ／ 无 trim ／ 无 case 转换 ／ 无 numeric coercion）？ |
| 2 | 是否接受 **`TEXT_CONTEXT`** 由「JSON 唯一文本标量形式」直接确定为 string（**不新增**规则），或要求显式登记该规则？ |
| 3 | 是否确认 **`G-S1` 为 blocking**，因而 `Serialization Format` **保持 `DESIGN PENDING`**？ |
| 4 | 是否授权在补充 `IDENTIFIER` ／ `ANALYSIS_RUN_ID` representation rule 后，**重新执行** conditional closure gate？ |

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`（`G-S1` 补充决定）**

> 本节是对 **PR #52 第一次 Serialization Format Closure Gate `FAIL`**（`G-S1`）的 **Human Decision**。
>
> 上方 **Serialization Format Implementation Record** 中的
> `G-S1 = BLOCKING` ／ `R-2 = FAIL` ／ `R-3 = FAIL` ／
> `Conditional Closure Gate = FAIL` ／ `Serialization Format = DESIGN PENDING`
> **全部保留，未删除、未改写** —— 它们属于 **first closure attempt time-point record**。

**决定 1 —— `G-S1` = VALID BLOCKING GAP（CONFIRMED）**

正式确认 `G-S1` 为**有效 blocking gap**；

```
第一次 conditional closure Gate = FAIL   ← 历史结果，保持
```

该历史结果**不得修改**。

**决定 2 —— `IDENTIFIER` ／ `ANALYSIS_RUN_ID` Representation = `JSON string`（APPROVED）**

正式授权：

```
IDENTIFIER       = JSON string
ANALYSIS_RUN_ID  = JSON string
```

其 representation semantic = **exact opaque string** —— **必须保持原始 identity value**。

**禁止：**

```
numeric coercion
trim
case conversion
Unicode normalization used as semantic fix-up
leading-zero removal
numeric interpretation
synonym conversion
```

例如：

```
"00123"  ≠  "123"
"A01"    ≠  "a01"
```

**不得**把 `1001` 作为 canonical `IDENTIFIER` ／ `ANALYSIS_RUN_ID` 的 JSON representation。

**决定 3 —— `snapshot_package_id` = `JSON string`（CONFIRMED）**

`snapshot_package_id` 属于 **transport-level identity concept**（**不是** canonical business field），
但**必须**具有**稳定、opaque** 的 identity representation：

```
snapshot_package_id = JSON string
```

同样要求 **exact string**；**禁止**：

```
numeric coercion
trim
case conversion
leading-zero removal
```

本决定**不定义** `snapshot_package_id` 的**生成算法**；仍**不得规定**：

```
UUID
hash
sequence
timestamp-based ID
regex
length
prefix
```

**决定 4 —— `TEXT_CONTEXT` = `JSON string`（APPROVED，显式登记）**

正式授权显式登记：

```
TEXT_CONTEXT = JSON string
```

**必须**保持 **exact textual value**，使用 **standard JSON string escaping**。

**不得：**

```
silent trim
silent case conversion
silent Unicode normalization
numeric coercion
```

本决定**仅**固定 **JSON scalar representation**，**不新增**任何 business semantic。

**决定 5 —— 新增 `C-10` = Identity ／ Text Scalar Representation（REGISTERED）**

`C-10` 已在 **`§4.3.22 C`** 正式登记。`C-1` ～ `C-9` 的 semantic **未修改**。

**决定 6 —— Historical Preservation = CONFIRMED**

**不得回写**：

```
PR #51 Serialization Format Review Finding
PR #51 Human Decision Record
PR #52 第一次 Serialization Format Implementation Record
```

**决定 7 —— Explicit Non-Authorization**

本 Human Decision **不授权**：

```
identifier regex
identifier length
identifier prefix
numeric-only identifier constraint
UUID requirement
identifier generation algorithm
source-system identifier format
JSON Schema
parser
sample JSON
dataset envelope
concrete JSON property name
directory ／ filename
decimal precision
quantity rounding policy
business timezone policy
```

**执行状态（`G-S1` 补充决定时点）**

```
G-S1                            = RESOLVED BY HUMAN DECISION
IDENTIFIER                      = JSON string（exact opaque）
ANALYSIS_RUN_ID                 = JSON string（exact opaque）
TEXT_CONTEXT                    = JSON string（exact textual）
snapshot_package_id             = JSON string（transport-level，exact）
C-10                            = REGISTERED
C-1 ～ C-9                       = UNCHANGED
Serialization Format            = DESIGN PENDING   ← 待重新执行 conditional closure Gate
```

**Serialization Format Closure Re-run Record（Human-authorized Conditional Closure Gate Re-run）**

**Authorization Source**

```
PR #52 第一次 conditional closure Gate = FAIL（G-S1 = BLOCKING）
  → G-S1 补充 Human Decision（决定 1 ～ 7）
  → 决定 5：C-10 = REGISTERED
  → 重新执行 conditional closure Gate
```

**Representation Completeness Re-Audit（逐 logical type ＋ transport identity）**

| 项 | Representation rule | 判定 |
| --- | --- | --- |
| **`IDENTIFIER`** | **`C-10`**：JSON string（exact opaque） | **COVERED** |
| **`ANALYSIS_RUN_ID`** | **`C-10`**：JSON string（exact opaque） | **COVERED** |
| **`TEXT_CONTEXT`** | **`C-10`**：JSON string（exact textual） | **COVERED** |
| `DATE` | `C-3`：`YYYY-MM-DD` | **COVERED** |
| `TIMESTAMP` | `C-4`：RFC 3339 compatible ＋ explicit offset ／ `Z` | **COVERED** |
| `DECIMAL_QUANTITY` | `C-5`：base-10 decimal string | **COVERED** |
| `NON_NEGATIVE_QUANTITY` | `C-5`：base-10 decimal string | **COVERED** |
| `RATIO` | `C-5`：base-10 decimal string | **COVERED** |
| `PERCENTAGE` | `C-5`：base-10 decimal string | **COVERED** |
| `STATUS` | `C-7`：exact canonical literal string | **COVERED** |
| `BOOLEAN` | `C-6`：`NOT APPLICABLE`（canonical model 无此 logical type） | **N/A** |
| **transport identity**：`snapshot_package_id` | **`C-10`**：JSON string（transport-level，exact opaque） | **COVERED** |

```
representation gap remaining = NONE
```

**不得**为达成 `PASS` 新增任何其他未授权 representation rule —— 本次**未**新增。

**R-1 ～ R-10 Re-run Result**

| # | Criterion | First Run | Re-run |
| --- | --- | --- | --- |
| **R-1** | Deterministic Parsing | PASS | **PASS** |
| **R-2** | Stable Field Representation | **FAIL** | **PASS**（`C-10`） |
| **R-3** | Logical Type Preservation | **FAIL** | **PASS**（`C-10`） |
| **R-4** | Missing ≠ Present-with-Default | PASS | **PASS** |
| **R-5** | Dataset-Level Absence Expressible | PASS | **PASS** |
| **R-6** | Manifest Metadata Carriage | PASS | **PASS** |
| **R-7** | Integrity Evidence Carriage | PASS | **PASS** |
| **R-8** | Reproducibility | PASS | **PASS** |
| **R-9** | Contract Version Expressibility | PASS | **PASS** |
| **R-10** | Adapter Neutrality | PASS | **PASS** |

```
R-1 ～ R-10（re-run） = ALL PASS
```

**R-11 ／ R-12 Assessment（POC DESIGN OBJECTIVES，非 hard blocker）**

```
R-11 Human Inspectability       = SATISFIED
R-12 Implementation Simplicity  = SATISFIED
```

**New Blocking Contradiction Audit**

```
G-S1（first run）               = RESOLVED BY HUMAN DECISION（historical record 保留）
其他新增 blocking contradiction   = NONE
downstream contradiction         = NONE
```

**Conditional Closure Result（re-run）**

```
R-1 ～ R-10                  = ALL PASS
C-1 ～ C-10                  = FULLY REGISTERED
New Blocking Contradiction   = NONE
  → conditional closure gate  = PASS
```

因此执行 conditional closure：

```
Serialization Format   DESIGN PENDING → DESIGN RESOLVED
```

**Current-State Synchronization**

| 位置 | 同步内容 |
| --- | --- |
| `§4` 子领域表 | `Snapshot / Import Contract` **仍为 `DESIGN PENDING`**（未整体关闭） |
| `§4` 继承约束 current-state 注 | `Serialization Format` → `DESIGN RESOLVED` |
| `§4.3` 子章节状态块 | 已完成层加入 `Serialization Format`；子章节整体**仍为 `DESIGN PENDING`** |
| `§4.3` 层级状态登记表 | `Serialization Format` → **`DESIGN RESOLVED`** |
| `§4.3.1` | current status → **`DESIGN RESOLVED`** |
| `§4.3.8` | manifest 部分 current-state 注 → **`DESIGN RESOLVED`** |
| `§4.3.21` | `四个层级` → **`五个层级`**；`serialization format determined` 移出「不表示」清单 |
| `§4.3.22` | 新增 **`C-10`**；`C-1` ～ `C-10` = **`REGISTERED`** |

**Historical Preservation（未回写）**

- **PR #51 Serialization Format Review Finding**
- **PR #51 Human Decision Record**
- **PR #52 第一次 Serialization Format Implementation Record** —— 其中
  `G-S1 = BLOCKING` ／ `R-2 = FAIL` ／ `R-3 = FAIL` ／
  `Conditional Closure Gate = FAIL` ／ `Serialization Format = DESIGN PENDING` **全部保留**

**Downstream Boundary（保持）**

```
Physical Dataset Layout            = DESIGN PENDING
Field Carrier Mapping              = DESIGN PENDING
Final Import Contract              = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
```

**Final Current State（Closure Re-run 完成时点）**

```
Package Envelope                    = DESIGN RESOLVED
Atomicity Boundary                  = DESIGN RESOLVED
Immutability Boundary               = DESIGN RESOLVED
Analysis Run Linkage                = DESIGN RESOLVED
Serialization Format                = DESIGN RESOLVED   ← re-run Gate = PASS
Physical Dataset Layout             = DESIGN PENDING
Field Carrier Mapping               = DESIGN PENDING
Final Import Contract               = DESIGN PENDING
Snapshot / Import Contract overall  = DESIGN PENDING
Adapter Boundary                    = DESIGN PENDING
POC Design v0.2                     = DRAFT
```

**Physical Dataset Layout Design Review（Review Finding）**

**Review Authority / Scope**

```
Snapshot / Import Contract 层级状态：
  Package Envelope        = DESIGN RESOLVED
  Atomicity Boundary      = DESIGN RESOLVED
  Immutability Boundary   = DESIGN RESOLVED
  Analysis Run Linkage    = DESIGN RESOLVED
  Serialization Format    = DESIGN RESOLVED   ← 已关闭（PR #51 HD ＋ PR #52 Closure Re-run = PASS）
  Physical Dataset Layout = DESIGN PENDING    ← 本 Review 对象
  Field Carrier Mapping   = DESIGN PENDING
  Final Import Contract   = DESIGN PENDING
```

本 Review **只**产出 Review Finding：

- **不**实施 `Physical Dataset Layout`；
- **不**选择最终 package layout；
- **不**推进 `Field Carrier Mapping` ／ `Final Import Contract`；
- **不**设计 Adapter；
- **不**创建任何 physical artifact（directory ／ JSON ／ ZIP ／ sample package）；
- **不**写 Human Decision。

**Fixed Upstream Decisions（已关闭；不得重新打开）**

| 项 | 已确定 | 来源 |
| --- | --- | --- |
| Serialization Strategy | **single JSON serialization strategy** | PR #51 Human Decision 决定 2 |
| Snapshot Manifest | **independent artifact ＋ JSON serialization** | PR #51 Human Decision 决定 5 |
| Business datasets | **JSON serialization** | PR #51 Human Decision 决定 5 |
| `JSONL` ／ `CSV` ／ `Parquet` ／ `Hybrid` | **`NOT SELECTED`** | PR #51 Human Decision 决定 3 |
| 单一 format 边界 | **不得**由 logical dataset 自选 format | PR #51 Human Decision 决定 4 |
| Representation policy | **`C-1` ～ `C-10` = `REGISTERED`** | PR #51 HD ＋ PR #52 `G-S1` HD ／ Re-run |
| Determinism boundary | `Deterministic Parsing ≠ Byte-for-byte Canonical JSON Encoding` | PR #51 Human Decision 决定 16 |
| `Serialization Format` | **`DESIGN RESOLVED`** | PR #52 Closure Re-run = `PASS` |

**必须保持的上游语义（不得被 layout 破坏）：**

```
Snapshot Manifest                  ≠  business dataset
Snapshot Package                   ≠  Analysis Run
snapshot_package_id                =  transport-level identity ＋ JSON string ＋ exact opaque
logical dataset role               ≠  physical filename
dataset-level provenance reference ≠  Stable Source Evidence Locator
dataset not included               ≠  dataset included with zero records
```

**Review Questions**

**Q1 —— package container 应采用什么 conceptual form（directory ／ archive ／ 其他）？**

- `§4.3.1` 明确本子章节**当时不得定义** `directory layout`；`§4.3.8` 明确**不决定** manifest 物理实现。
- **判定：** `directory` 与 `archive` 两种 conceptual form **在技术上都不违反**现有 Design；
  第三类（例如以单一 JSON document 兼作 container）**不足以**满足 L-1 ／ L-5（见 Q2 ／ Q8 分析）。
- **本 Review 不选择** —— 属 **Human Decision**。

**Q2 —— `one logical dataset = one JSON artifact`，还是允许多个 logical dataset 聚合到同一 business data artifact？**

- `§4.3.10` 定义 **logical dataset role**；`§4.3.8` 要求 manifest 表达
  `included logical datasets` 与 **`dataset-level record count / integrity evidence`**；
  `§4.4.4` 要求区分 `not included` 与 `included with zero records`。
- **判定（技术可行性）：** 两种方案**都技术可行**。
  - **one-per-artifact**：`dataset-level` 语义与 artifact 边界**一一对应**；blast radius 天然局部化；
    但 artifact 数量随 dataset 数增长。
  - **aggregated**：artifact 数量少；但 `dataset-level` 语义**必须**改由 artifact **内部结构**承载 ——
    而该内部结构（dataset envelope ／ record envelope ／ property 结构）属 **`Field Carrier Mapping`**。
    在 FCM 尚未设计的情况下采用 aggregated，会**提前依赖**未设计的下游层（见 L-10）。
- **本 Review 不选择** —— 属 **Human Decision**。

**Q3 —— Snapshot Manifest 应位于 package root、固定 subdirectory，还是只要求可由 package entry point 定位？**

- `§4.3.8` 只要求 manifest 表达 8 项**语义**，**未**要求位置模型。
- **判定：** 「**必须能够 deterministic locate**」是**必须**的（`L-2`）；
  **具体位置模型**（root ／ 固定 subdirectory ／ entry-point 可定位）属**本层可决定范围** ——
  但**本 Review 不选择**，属 **Human Decision**。
- **注意：** 若采用「固定 subdirectory」，则该 subdirectory 名称本身**不得**承载 business semantic（`L-4`）。

**Q4 —— 是否需要固定 manifest filename？**

- 现有 Design **未**要求固定 filename。
- **判定：** deterministic discovery 需要**某种**确定性定位方式 ——
  **固定 filename** 与 **manifest-locator 规则**都能满足 `L-2`。
  若引入固定 filename，它**不得**成为 business semantic source（`L-4`）。
- **本 Review 不选择** —— 属 **Human Decision**。

**Q5 —— business dataset artifact 是否需要固定 naming convention？**

- `§4.3.10` 明确：**logical dataset role ≠ physical filename**。
- **判定：** naming convention **可以**存在（便于定位），但**不得**成为 role 的
  **authoritative 来源**；`role → artifact` 的权威关联**必须**由 manifest 显式建立（见 Q7 ／ `L-3`）。
- **本 Review 不选择** —— 属 **Human Decision**。

**Q6 —— physical filename 应否直接由 logical dataset role 推导？如何避免 filename 成为隐式 semantic source？**

- **风险：** 由 role 直接推导 filename，会使 filename 事实上承担 role 语义 ——
  与 `§4.3.10`（role ≠ filename）及 `§4.5.18`（no silent canonicalization）的**精神冲突**。
- **判定：**
  ```
  filename 可以 deterministic，但不得成为 role 的唯一 / authoritative 来源
  authoritative 关联 = manifest 的显式声明（Q7）
  ```
- 若采用推导（作为便利），**必须**同时保持 manifest 显式声明；
  且文件名**不得**被解释为 business status ／ scope ／ provenance（`L-4` ／ `L-10`）。
- **本 Review 不选择** —— 属 **Human Decision**。

**Q7 —— Manifest 是否必须显式建立 `logical dataset role → physical artifact reference`？该问题属哪一层？**

- **必须**（`L-3`）：否则 `included dataset` 无法 deterministic locate，`§4.3.8` 的
  `included logical datasets` 与 `dataset-level record count` 无法被验证。
- **Layer ownership（明确划界）：**

| 内容 | 归属 |
| --- | --- |
| **要求** manifest 显式建立 `role → physical artifact reference` | **`Physical Dataset Layout`**（本层） |
| 该 reference 的**具体字段名 / JSON property 结构 / 表达形式** | **`Field Carrier Mapping`** |
| 该 reference 的**校验 / 拒绝规则** | **`Final Import Contract`** |

**本 Review 只登记要求，不定义字段。**

**Q8 —— `included` 且 `record_count = 0` 时，是否必须仍存在 physical JSON artifact？**

- **必须存在。** 否则 `included with zero records` 与 `not included` 在**物理层不可区分**，
  直接破坏 `§4.4.4` ／ `§4.3.12` 的 `dataset not included ≠ dataset included with zero records`（`L-5`）。
- **豁免：** 若某 logical dataset 为 `not included`，则**不得**要求其 artifact 存在。
- 「如何表达 0 条记录」的 envelope 形式属 **`Field Carrier Mapping`**，本 Review **不定义**。

**Q9 —— `dataset not included` 时，是否禁止出现对应 business artifact？**

- **不得**建立隐式规则「出现 artifact 即视为 `included`」——
  authoritative 来源**必须**是 **Manifest**（`§4.3.8` ／ `L-5`）。
- 若物理上**出现**未被 manifest 声明的 artifact，其处理（ignore ／ reject ／ 报告）属
  **`Final Import Contract`** 的 acceptance 规则。
- **本 Review 记录 dependency，不决定。**

**Q10 —— 是否允许 nested directory？**

- 现有 Design **未**禁止；技术可行。
- **判定：** 允许与否属 **Human Decision**；若允许，**必须**保持 `L-4`（role ≠ path）与
  `L-11`（path 不得逃出 package root）。
- **POC 适用性判断（非约束）：** nested 会提高 discovery 与 path 校验复杂度。

**Q11 —— package 内 artifact path 是否需要 deterministic ／ unique ／ relative-to-package-root？**

- **需要**：
  ```
  deterministic            （同一 accepted package 可被重新定位；L-8）
  unique                   （避免 artifact 歧义；L-3）
  relative-to-package-root （保持 package 自包含；L-1 ／ L-7）
  ```
- **absolute path 不可**作为 accepted package 的 artifact path（`L-7` ／ `L-11`）。

**Q12 —— 是否允许 absolute path ／ external path ／ path traversal ／ symbolic link ／ package 外部引用？**

- **不得**作为 accepted package 的组成部分 —— 它们破坏：
  ```
  L-1  Package Boundary Unambiguous
  L-7  Package Immutability Compatibility（依赖 package 外部 mutable artifact）
  L-11 Path Scope Integrity
  ```
- **具体 acceptance ／ security 强制方式**（拒绝规则、校验时机、symlink 解析策略）属
  **`Final Import Contract`**；本 Review **只记录 dependency**。

**Q13 —— directory package 与 archive package 对各约束的影响？**

| 约束 | Directory package | Archive package |
| --- | --- | --- |
| **atomicity**（`§4.3.6`） | **弱** —— 目录级 transfer 无内在原子性，需外部约定 | **强** —— 单 artifact 天然接近 package-level atomic 单位 |
| **immutability**（`§4.3.5`） | 需外部约定（只读 / 冻结）；易被部分覆盖 | 单 artifact 更易整体冻结；但**重打包**可产生同 ID 不同内容风险，须靠 identity 规则约束 |
| **inspectability**（`R-11`） | **高** —— 可直接浏览 | **中** —— 需归档工具；但**不得**要求专用业务工具（`R-11` 精神） |
| **reproducibility**（`§4.3.4`） | 高（路径稳定） | 高（artifact 稳定）；但**归档内部条目顺序 / 元数据**可能引入非确定性 —— 若要求 byte-level，属 `Final Import Contract` |
| **integrity verification**（`§4.3.15`） | 需逐个 artifact（或整体约定） | 可整体校验；**算法**属 `Final Import Contract` |
| **implementation complexity** | **低** | 中（需归档读写） |

**Q14 —— `Physical Dataset Layout` 的 minimum closure criteria 应是什么？**

- 见 **Required Layout Properties**（`L-1` ～ `L-11`）。
- **注意：** 这些编号是 **Review working set**；`L-1` ～ `L-10` 中大部分**直接来自既有 Design**，
  `L-11` 为**本 Review 提出**。**是否将其全部登记为正式 closure criteria 属 Human Decision** ——
  本 Review **不自行宣布**。

**Q15 —— 哪些问题必须留给 `Field Carrier Mapping` ／ `Final Import Contract` ／ `Adapter Boundary`？**

- 见 **Downstream Ownership Matrix**。

**Required Layout Properties**

| # | Property | 类别 | 依据 |
| --- | --- | --- | --- |
| **L-1** | **Package Boundary Unambiguous** —— 一个 Snapshot Package 的物理边界必须能够明确识别 | 既有 | `§4.3.2` ／ `§4.3.5` ／ `§4.3.6` |
| **L-2** | **Manifest Discoverability** —— Manifest 必须能够 deterministic locate | 既有 | `§4.3.8` ／ `§4.3.6` |
| **L-3** | **Dataset Artifact Discoverability** —— `included` logical dataset 必须能够 deterministic locate 到对应 artifact | 既有 | `§4.3.8` ／ `§4.4.4` |
| **L-4** | **Logical ／ Physical Separation** —— `logical dataset role` **不得**等同或依赖 physical filename 语义 | 既有 | `§4.3.10` ／ `§4.5.18` |
| **L-5** | **Presence Semantics Preservation** —— `not included ≠ included with zero records` 必须可在物理层区分 | 既有 | `§4.3.12` ／ `§4.3.14` ／ `§4.4.4` |
| **L-6** | **Package Atomicity Compatibility** —— layout 不得要求跨 package 拼接或 silent mixing | 既有 | `§4.3.6` ／ `§4.3.7` |
| **L-7** | **Package Immutability Compatibility** —— accepted package 不得依赖 package 外部 mutable artifact | 既有 | `§4.3.5` |
| **L-8** | **Reproducibility** —— 同一 accepted package 必须能被重新定位并解释其 artifact set | 既有 | `§4.3.4` ／ `§4.3.5` |
| **L-9** | **Serialization Compatibility** —— 所有 serialized artifact 必须服从已关闭的 single JSON strategy | 既有 | PR #51 HD 决定 2 ／ 4 |
| **L-10** | **Downstream Neutrality** —— layout 不得偷偷完成 `Field Carrier Mapping` 或 `Final Import Contract` | 既有 | `§4.3.1` ／ PR #51 HD 决定 17 ～ 19 |
| **L-11** | **Path Scope Integrity** —— artifact path 必须 relative-to-package-root，且不得使用 absolute ／ external ／ traversal ／ symlink 逃出 package | **本 Review 提出** | `§4.3.5` ／ `§4.3.6` ／ `§4.3.15` 延伸 |

**Option Review**

**Option 0 —— Keep `Physical Dataset Layout = DESIGN PENDING`（Do Nothing）**

- **技术安全性：** **安全** —— 不产生错误结果；fail-closed 与既有 boundary 全部保持。
- **阻塞影响：** `Field Carrier Mapping` 与 `Final Import Contract` **无法**完成 ——
  二者都需要 artifact 的存在性、粒度与定位前提；`Snapshot / Import Contract overall` 将长期 `DESIGN PENDING`。
- **是否可接受为终点：** **不可接受为终点**（不构成 Design 进展）。

**Option A —— Structured Directory Package**

- 概念形态：`package root` ＋ `independent manifest` ＋ `dataset artifact area`。
- **优势：** human inspectability 最高；deterministic discovery 容易（固定区域 ＋ manifest）；
  package copy 行为直观（目录复制即迁移）。
- **风险：**
  - **atomic transfer limitation** —— 目录级 transfer **无内在原子性**，需外部约定才能满足 `§4.3.6`；
  - **immutability** 需外部约定（只读 ／ 冻结），易被部分覆盖；
  - 若引入固定 subdirectory 名，需保证该名称**不承载** business semantic（`L-4`）。
- **技术可行性：** **是**（`L-6` 的满足方式需额外设计，属 `Final Import Contract` 例外 —— 见下）。
- **当前 POC 最适合：** **未判定**。

**Option B —— Flat Directory Package**

- Manifest 与 business dataset artifact 位于同一级 package root。
- **优势：** simplicity 最高；实现与 inspectability 都最轻。
- **风险：**
  - **naming collision** —— manifest 与 dataset artifact ／ artifact 之间共享同一命名空间；
  - **role ／ filename coupling risk** —— 平坦结构下「文件名即角色」的诱惑最大，直接违反 `L-4`；
  - **future expansion** —— 若未来需要 nested 或分组，迁移成本较高。
- **技术可行性：** **是**。
- **当前 POC 最适合：** **未判定**。

**Option C —— Archive Package**

- 单一 archive container 内含 `independent manifest` ＋ JSON business artifacts。
- **候选归档格式可讨论（例如 ZIP），但本 Review 不选择任何归档格式。**
- **优势：**
  - **package-level atomicity** 最强 —— 单一 artifact 接近 package-level atomic 单位（`§4.3.6`）；
  - **immutability** 较易整体冻结；**integrity** 可整体校验；
  - transfer 为单文件，跨环境一致性较好。
- **风险：**
  - **extraction semantics** —— 若要求「先解包再导入」，会引入额外状态与中间产物，
    与 `§4.3.5` 的 immutability 边界需要额外约定；
  - **archive-specific risk** —— 归档内部条目顺序 ／ 元数据 ／ 时间戳可能**非确定性**；
    若 integrity contract 要求 byte-level 稳定，需**另行**决定（属 `Final Import Contract`）；
  - **inspectability** 与 **tooling** 成本高于目录形态；
  - **ZIP-specific** 细节（例如路径分隔符、符号链接、压缩方法）**不得**在本层决定。
- **技术可行性：** **是**。
- **当前 POC 最适合：** **未判定**。

**Option D —— Aggregated Business Data Artifact**

- Manifest 保持独立 artifact；多个 logical dataset **聚合**在一个 JSON business artifact 中。
- **优势：** artifact 数量少；单文件便于整体处理。
- **风险：**
  - **logical dataset isolation** 下降 —— dataset 边界由 artifact **内部结构**表达；
  - **absent ／ empty semantics** —— `not included` ／ `included with 0 records` ／ `> 0 records`
    三者必须在同一 artifact 内部结构中被区分，**提高** `L-5` 的实现依赖；
  - **dataset-level provenance** 与 **dataset-level record count** 必须由内部结构承载 →
    属 **`Field Carrier Mapping`**（本层**不得**设计）；
  - **blast radius** —— 单 artifact 内任一 dataset 结构问题会牵动整个 artifact；
  - **future field carrier mapping** —— 提前绑定内部结构，降低后续自由度；
  - **human inspection** —— 大 artifact 的可读性下降。
- **技术可行性：** **是**（但**必须**先有 `Field Carrier Mapping` 才能完整定义 `dataset-level` 语义 ⇒ 与 `L-10` 冲突）。
- **当前 POC 最适合：** **未判定**；`L-10` 视角下**风险最高**。

**Option Comparison**

`既有` = 受既有 Design 约束；`⚠` = 需新增未授权设计；`—` = 不适用。判定针对**生产可用**形态，
**不**代表本 Review 的选择。

| 维度 | Option 0 | A（Structured Dir） | B（Flat Dir） | C（Archive） | D（Aggregated） |
| --- | --- | --- | --- | --- | --- |
| deterministic discovery（L-2 ／ L-3） | — | **强** | 中（命名空间拥挤） | 强（需归档读取） | 中 |
| human inspectability | — | **最高** | **高** | 中 | 低中 |
| package atomicity（L-6） | — | 需**额外约定** | 需**额外约定** | **最强** | 同目录形态 |
| immutability（L-7） | — | 需外部约定 | 需外部约定 | 较易整体冻结 | 同目录形态 |
| integrity verification（`§4.3.15`） | — | 逐 artifact | 逐 artifact | 可整体 | 逐 artifact |
| logical ／ physical separation（L-4） | — | 中高（有区域划分） | **风险最高** | 中高 | 中 |
| absent ／ empty semantics（L-5） | — | 依赖 manifest | 依赖 manifest | 依赖 manifest | **依赖 FCM 内部结构** ⚠ |
| blast radius | — | 局部 | 局部 | 局部 | **大** |
| implementation complexity | 最低（不选型） | 低 | **最低** | 中 | 中 |
| future FCM compatibility | — | 高 | 中 | 高 | **低**（提前绑定内部结构）⚠ |
| POC suitability（判断，非约束） | 不构成进展 | 高 | 高 | 中高 | 低中 |

**选项组合说明：** A ／ B 与 C 在**容器形态**上互斥；A ／ B ／ C 均可与
「`one logical dataset = one artifact`」组合；**D** 与 A ／ B ／ C **正交**
（D 改变的是 **artifact 粒度**，而非容器形态）。因此 Q1 与 Q2 是**两个独立裁定**。

**本 Review 不选择任何 Option。**

**Manifest Boundary**

**已固定（不得重新设计）：**

```
Snapshot Manifest = independent artifact
Snapshot Manifest serialization = JSON
Snapshot Manifest 的 8 项 logical semantic requirement（§4.3.8）不得修改
Snapshot Manifest ≠ business dataset
```

**本 Review 可以分析（并在 Q3 ／ Q4 中给出 evidence）：**

```
manifest physical placement
manifest discoverability
manifest 与 package root 的关系
manifest 与 dataset artifact 的关系
```

**本 Review 不得定义：**

```
具体 Manifest JSON Schema
具体 property name
具体 nested object structure
```

（以上属 **`Field Carrier Mapping`**。）

**Empty / Absent Dataset Boundary**

| Case | Manifest 状态 | 物理层要求（本层） | envelope 形式归属 |
| --- | --- | --- | --- |
| **A** | dataset **not included** | **不得**要求对应 artifact 存在；**不得**由「artifact 缺失」推断任何业务结论 | `Field Carrier Mapping` |
| **B** | dataset **included** ＋ `record_count = 0` | **必须**存在对应 artifact（`L-5`） | `Field Carrier Mapping` |
| **C** | dataset **included** ＋ `record_count > 0` | **必须**存在对应 artifact，并可 deterministic locate（`L-3`） | `Field Carrier Mapping` |

**禁止的隐式规则：**

```
「找不到文件 = 没有业务数据」
「出现文件 = dataset included」
```

authoritative 来源**必须**是 **Manifest**（`§4.3.8` ／ `§4.4.4`）。

**Provenance Boundary**

**必须保持：**

```
dataset-level provenance reference  ≠  Stable Source Evidence Locator
```

**本层不得**把以下自动等同于 provenance semantic 或 `Stable Source Evidence Locator`：

```
artifact path
filename
archive entry path
```

**compatibility requirement（仅记录）：** 若未来的 `Stable Source Evidence Locator`
需要包含 **artifact-relative position**（例如「某 artifact 内的第 N 条记录」），
则物理布局必须**至少**保证 artifact 的 **deterministic 定位**（`L-3` ／ `L-8` ／ `L-11`）——
使这种 future locator **可表达**。**具体 carrier 留给 `Field Carrier Mapping`。**

**Atomicity / Immutability Boundary**

对每个 Option 与以下约束的兼容性已逐项检查（见 Q13 与 Option Comparison）：

```
package-level atomic ACCEPT ／ REJECT   （§4.3.6）
accepted package immutable              （§4.3.5）
no partial overwrite
no silent replace
no cross-snapshot mixing                （§4.3.7）
```

**本 Review 不设计：**

```
transaction mechanism
file locking
storage engine
object storage
database transaction
upload protocol
```

**Final Import Contract Boundary（记录 dependency，不决定）**

以下**不得**由本层决定，且若某 layout 方案依赖其中某项，**只记录 dependency**：

```
hash algorithm
checksum algorithm
signature policy
canonical byte ordering
archive integrity algorithm
contract version evolution
backward compatibility
forward compatibility
final acceptance algorithm
runtime import validator
artifact-presence / extra-artifact acceptance rule（见 Q9）
path traversal ／ symlink 拒绝规则（见 Q12）
```

**Downstream Ownership Matrix**

| 问题 | 归属层 |
| --- | --- |
| package container 形态（directory ／ archive） | **`Physical Dataset Layout`** |
| artifact 粒度（one-per-dataset ／ aggregated） | **`Physical Dataset Layout`** |
| manifest 位置模型 ／ discoverability | **`Physical Dataset Layout`** |
| artifact path 必须 deterministic ／ unique ／ relative-to-root | **`Physical Dataset Layout`** |
| `role → artifact reference` 的**存在要求** | **`Physical Dataset Layout`** |
| `role → artifact reference` 的**字段 ／ JSON 结构** | **`Field Carrier Mapping`** |
| dataset envelope ／ record envelope ／ business record 结构 | **`Field Carrier Mapping`** |
| `canonical field → concrete JSON property name` | **`Field Carrier Mapping`** |
| `Stable Source Evidence Locator` 的 physical carrier ／ artifact-relative position | **`Field Carrier Mapping`** |
| 0-record dataset 的物理表达形式 | **`Field Carrier Mapping`** |
| integrity ／ hash ／ signature ／ byte-level canonicalization | **`Final Import Contract`** |
| extra-artifact ／ traversal ／ symlink 的 acceptance 与拒绝规则 | **`Final Import Contract`** |
| contract version evolution ／ 兼容性规则 | **`Final Import Contract`** |
| Adapter 实现 ／ 连接器 ／ 传输协议 | **`Adapter Boundary`** |

**Known Risks**

| # | Risk | 说明 |
| --- | --- | --- |
| **P-1** | **文件名成为隐式 semantic source** | Flat directory（Option B）与「role 推导 filename」最容易诱发；直接破坏 `§4.3.10` 与 `L-4` |
| **P-2** | **`not included` 与 `included with zero records` 物理不可区分** | 若靠「文件是否存在」推断 presence；破坏 `§4.4.4` ／ `L-5` |
| **P-3** | **目录形态的 atomicity 依赖外部约定** | `§4.3.6` 的 package-level atomic 语义在目录形态下**没有内在保证** |
| **P-4** | **归档形态的重打包风险** | 同一 `snapshot_package_id` 对应不同 archive 内容会破坏 `§4.3.5` |
| **P-5** | **归档内部非确定性** | 条目顺序 ／ 时间戳 ／ 元数据可能使同一内容产生不同 bytes；若 integrity 要求 byte-level，需 `Final Import Contract` 单独决定 |
| **P-6** | **提前依赖 `Field Carrier Mapping`** | Option D 需要 dataset envelope ／ record envelope 才能成立 —— 与 `L-10` 冲突 |
| **P-7** | **path 逃出 package** | absolute ／ external ／ traversal ／ symlink 破坏 `L-1` ／ `L-7` ／ `L-11` |
| **P-8** | **本 Review 结论被误读为 layout 已选定** | 本 Review **未**选择任何 Option |
| **P-9** | **物理路径被误当作 provenance 语义** | 破坏 `dataset-level provenance reference ≠ Stable Source Evidence Locator` |
| **P-10** | **`§4.3.1` 的「不得定义 directory layout ／ concrete filenames」被误读为永久禁止** | 该限制约束的是**当时**的 Task；本层决定**必须**由 Human Decision 明确授权 |

**Review Conclusion**

基于 Repository 中已存在的正式设计事实：

1. **`Physical Dataset Layout` 必须满足的性质已可界定**：`L-1` ～ `L-10` **直接来自既有 Design**，
   `L-11` 为**本 Review 提出**。这构成后续 closure 的可验证基础 ——
   但**是否全部登记为正式 closure criteria 属 Human Decision**。
2. **15 个 Review Question 中**：`Q1` ～ `Q6` ／ `Q10` 属 **Human Decision**；
   `Q7` ／ `Q8` ／ `Q11` ／ `Q12` 已获**证据性回答**（含 layer ownership 归属）；
   `Q9` ／ `Q13` 已给出判定与 dependency；`Q14` ／ `Q15` 已给出 candidate criteria 与 ownership matrix。
3. **五个 Option（0 ／ A ／ B ／ C ／ D）均已评估**：
   `A` ／ `B` ／ `C` 与 `D` 在**不同维度**上取舍（容器形态 vs artifact 粒度）；
   **Option D 与 `L-10` 存在实质张力**（需先有 FCM）。
4. **本 Review 不选择最终 layout**；`Physical Dataset Layout` **保持 `DESIGN PENDING`**。
5. **不推进** `Field Carrier Mapping` ／ `Final Import Contract` ／ `Adapter Boundary`；
   dependency 已记录，未自行解决。
6. **未**修改任何 canonical entity ／ field ／ `BR-*` ／ Validation Taxonomy ／ Master Data Mapping ／
   Serialization Format policy；**未**创建任何 physical artifact。

**Current Status（本 Review 时点）**

```
Snapshot / Import Contract overall = DESIGN PENDING
  Package Envelope                 = DESIGN RESOLVED
  Atomicity Boundary               = DESIGN RESOLVED
  Immutability Boundary            = DESIGN RESOLVED
  Analysis Run Linkage             = DESIGN RESOLVED
  Serialization Format             = DESIGN RESOLVED
  Physical Dataset Layout          = DESIGN PENDING   ← 本 Review 未关闭
  Field Carrier Mapping            = DESIGN PENDING
  Final Import Contract            = DESIGN PENDING

Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

**Human Decision Required**

| # | 问题 | 性质 |
| --- | --- | --- |
| 1 | **package container**：`directory` ／ `archive` ／ 其他明确方案？ | Q1 |
| 2 | **artifact 粒度**：`one logical dataset = one artifact` ／ aggregated business data artifact？ | Q2 |
| 3 | **manifest placement model**：package root ／ 固定 subdirectory ／ 仅要求 entry-point 可定位？ | Q3 |
| 4 | **manifest filename 是否固定**？ | Q4 |
| 5 | **dataset artifact naming strategy**：是否固定 naming convention？ | Q5 |
| 6 | **`logical dataset role` 如何关联到 physical artifact**：是否要求 manifest 显式声明（本 Review 判定为**必须**，请确认）？是否**禁止**以 filename 作为 authoritative 来源？ | Q6 ／ Q7 |
| 7 | **included-empty dataset 是否必须存在 artifact**（本 Review 判定为**必须**，请确认）？ | Q8 |
| 8 | **nested directory 是否允许 ／ 是否需要**？ | Q10 |
| 9 | 是否接受 **`L-1` ～ `L-11`** 作为 `Physical Dataset Layout` 的 minimum closure criteria？ | Q14 |
| 10 | 是否授权后续**独立 `Physical Dataset Layout` Implementation PR**（登记选择 ＋ 同步 current-state），并在满足 closure criteria 时允许 `DESIGN PENDING → DESIGN RESOLVED`？ | follow-up |

**本 Review 不作出上述任何决定。** 后续必须由 **Human Decision** 裁定；
**不得**由 Agent 自行选择最终 layout。

**Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Human Authority**

```
Human = Decision Authority
  （针对 PR #53 `Human Decision Required` #1 ～ #10 的 Decision Analysis 已由 Human 完成）
```

**Decision Source**

Human 已审阅：

- **PR #53 Physical Dataset Layout Design Review（Review Finding）** —— 含 Review Questions `Q1` ～ `Q15`、
  Required Layout Properties `L-1` ～ `L-11`、Option Review（Option 0 ／ A ／ B ／ C ／ D）、
  Option Comparison、Review Conclusion 与 `Human Decision Required` #1 ～ #10；
- 针对 `Human Decision Required` #1 ～ #10 的**独立 Decision Analysis**。

以下为**正式 Human Decision**，但**不是** `Physical Dataset Layout` implementation。
**本 Record 不修改** PR #53 Review Finding 的任何一个字 ——
Review 当时**未选择任何 Option**；**Flat Directory 是本 Human Decision 之后才作出的选择。**

**决定 1 —— Package Container = Flat Directory Package（APPROVED）**

正式选择：

```
Package Container = Flat Directory Package
```

定义：一个 Snapshot Package 以**单个 package root** 作为当前 POC 的**物理边界**。

**不选择**：

```
Structured Directory Package
Archive Package
其他特殊 container
```

**理由：** 当前 POC **不存在**必须引入额外目录层级或 archive tooling 的证据；
`Flat Directory` 在 **fixed manifest entry ＋ explicit `role → artifact` association** 成立时，
**可以**满足 deterministic discovery，且保持当前 implementation complexity 最低。

**必须明确：** `Flat Directory` **本身不保证**：

```
runtime atomicity
runtime immutability
integrity verification
```

这些**不得**被本决定偷偷实现。

**决定 2 —— Artifact Granularity = one included logical dataset → one independent JSON artifact（APPROVED）**

```
one included logical dataset = one independent JSON artifact
```

**不采用** aggregated business data artifact；**不引入** dataset sharding。

**原因：**

- 保持 dataset boundary 清晰；
- 避免跨 dataset internal addressing；
- **不提前依赖** dataset envelope；
- **不提前推进** `Field Carrier Mapping`；
- 降低 blast radius；
- 保持 inspectability。

**必须明确：**

```
one artifact per logical dataset  ≠  partial package acceptance
```

任何**单个** artifact 的问题是否导致**整个** package reject，
**仍由后续 `Final Import Contract` 定义**。

**决定 3 —— Manifest Placement = package root（APPROVED）**

```
Snapshot Manifest = package root
```

即 Manifest 与 business dataset artifacts **均位于同一个 package root**。

**不得**放入 fixed manifest subdirectory；**也不采用** external entry-point locator 作为当前 POC 方案。

**决定 4 —— Manifest Filename = `manifest.json`（APPROVED）**

```
Snapshot Manifest filename = manifest.json
```

该名称**仅**表示 **technical package entry point**；**不得**承载：

```
business identity
business status
dataset role
scope semantic
provenance semantic
snapshot_package_id semantic
```

因此：

```
manifest.json = technical filename contract
              ≠ business semantic source
```

**决定 5 —— Dataset Artifact Naming = 最低 physical naming requirements（APPROVED）**

**不定义**：

```
role-derived mandatory filename template
opaque filename generation algorithm
dataset ID generation rule
```

当前 POC **最低 physical naming requirements**：

- business dataset artifact 位于 **package root**；
- filename **必须在当前 package 内唯一**；
- serialization extension = **`.json`**；
- **不得**使用保留名称 **`manifest.json`**。

具体 filename **可以**是可读名称，也**可以**是 technical name，
但 **filename 本身不得成为 `logical dataset role` 的 authoritative source**。

正式确认：

```
Manifest-declared artifact reference = authoritative physical association
filename                             = physical convenience only
```

**决定 6 —— `logical dataset role` → physical artifact association = REQUIRED（APPROVED）**

`Snapshot Manifest` **必须显式建立**：

```
logical dataset role → physical artifact reference
```

该关联 **REQUIRED**。**不得**依赖：

```
filename inference
directory name inference
file ordering
filesystem discovery heuristic
```

来判断 `logical dataset role`。

同时确认：`filename` ／ `artifact path` **不得**作为以下内容的 authoritative source：

```
logical dataset role
business status
scope
provenance
Stable Source Evidence Locator semantic
```

**本层只决定 association MUST EXIST**；**不得定义** Manifest 中具体 JSON property name ／
nested structure ／ schema representation —— 这些属于 **`Field Carrier Mapping`**。

**决定 7 —— Included Empty Dataset = artifact REQUIRED（APPROVED）**

```
dataset = included 且 record_count = 0  →  对应 JSON artifact REQUIRED
dataset = not included                  →  对应 artifact NOT REQUIRED
```

**必须保持：**

```
not included  ≠  included with zero records
```

**本决定不定义** empty dataset 的 JSON body；**不得决定** `[]` ／ `{}` ／ `{"records":[]}`
或任何其他 dataset envelope —— 这些属于 **`Field Carrier Mapping`**。

**决定 8 —— Nested Directories = NOT ALLOWED（POC v0.2）（APPROVED）**

POC v0.2 Snapshot Package 内部：

```
nested directories = NOT ALLOWED
```

因此当前 package layout：

```
single package root
+ manifest.json
+ root-level business JSON artifacts
```

**此限制只针对 Snapshot Package 内部的 physical layout**；
**不限制** Snapshot Package 在**宿主 filesystem 中的外部存放位置**。

未来如果出现**真实需求**：**可以**通过**新的明确 Design Decision** 重新评估 nested directory。

**决定 9 —— `L-1` ～ `L-11` = minimum closure criteria（APPROVED）**

正式批准 `L-1` ～ `L-11` 作为 `Physical Dataset Layout` 的 **minimum closure criteria**：

```
L-1   Package Boundary Unambiguous
L-2   Manifest Discoverability
L-3   Dataset Artifact Discoverability
L-4   Logical / Physical Separation
L-5   Presence Semantics Preservation
L-6   Package Atomicity Compatibility
L-7   Package Immutability Compatibility
L-8   Reproducibility
L-9   Serialization Compatibility
L-10  Downstream Neutrality
L-11  Path Scope Integrity
```

**`L-6` ／ `L-7` Boundary —— 只验证 DESIGN COMPATIBILITY**

`L-6` ／ `L-7` 在 `Physical Dataset Layout` 层验证的是 **DESIGN COMPATIBILITY**，
**不是** runtime mechanism completion。即 layout **不得**：

```
要求 cross-package composition
要求 silent mixing
依赖 package 外 mutable artifact
要求 partial overwrite
破坏 accepted-package immutability semantic
```

但本层**不得实现**：

```
transaction
locking
atomic filesystem move
storage engine
object storage semantics
upload protocol
runtime immutability enforcement
```

—— 这些属于**后续层**。

**`L-11` Boundary —— 只定义合法 path scope**

正式定义：**`L-11` Path Scope Integrity** —— 所有 physical artifact reference **必须**：

```
relative to package root
```

且其 **logical resolved target** **必须**位于**当前 Snapshot Package boundary 内**。

因此合法 layout **不得**依赖：

```
absolute path
external path / URI
package-external artifact
```

**同时：** `Physical Dataset Layout` **只定义合法 boundary**。以下**仍属于 `Final Import Contract`**，
**不得**在本 Human Decision 实现：

```
path normalization algorithm
traversal detection algorithm
`..` rejection mechanism
symlink resolution algorithm
symlink rejection timing
platform-specific path parser
runtime rejection behavior
```

即：

```
Layout                = defines valid path scope
Final Import Contract = validates / rejects violations
```

**不得**让 `L-11` 演变成 **Security Implementation**。

**决定 10 —— Follow-up Implementation Authorization = AUTHORIZED（条件性）**

正式授权后续**独立** `Physical Dataset Layout` Design Change ／ Implementation PR，
其任务**可以**：

- 正式登记本 Human Decision；
- 建立 authoritative current design；
- 同步 current-state references；
- 正式登记 `L-1` ～ `L-11`；
- 执行 `Physical Dataset Layout` closure validation。

**只有当**：

```
Human-approved layout decisions = fully registered
且 L-1 ～ L-11 = ALL PASS
且 New Blocking Contradiction = NONE
```

**才允许**：

```
Physical Dataset Layout   DESIGN PENDING → DESIGN RESOLVED
```

**本 PR 不执行上述任何一项。**

**Explicit Non-Authorization**

本 Human Decision **不授权**：

```
创建真实 package directory
创建 JSON sample
创建 manifest.json 实际文件
创建 dataset artifact 实际文件
创建 ZIP / archive
创建 JSON Schema
创建 parser
创建 runtime validator
创建 Adapter
```

**不授权定义**：

```
Manifest JSON property name
dataset envelope
record envelope
business record structure
source field → JSON property mapping
canonical field → JSON property mapping
Stable Source Evidence Locator physical carrier
hash algorithm
checksum algorithm
signature algorithm
byte-level canonicalization
archive algorithm
runtime acceptance algorithm
contract compatibility policy
path validation implementation
```

**不得修改**：canonical entity ／ canonical field ／ `BR-*` ／ Validation Taxonomy ／
Master Data Mapping ／ Serialization Format policy。

**Downstream Boundary（保持）**

```
Field Carrier Mapping              = DESIGN PENDING
Final Import Contract              = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

**Historical Preservation**

**PR #53 Physical Dataset Layout Design Review（Review Finding）必须完整保留**，尤其**不得回写**：

```
Option Review
Option Comparison
Review Conclusion
Current Status（Review time-point）
Human Decision Required
L-1 ～ L-11 Review working-set history
```

**不得**把历史表述「**本 Review 不选择任何 Option。**」改写成「Review 选择 Flat Directory」——
**Review 没有选；Human 后来才选。**

**执行状态（PR #53 Human Decision 时点）**

```
Physical Dataset Layout            = DESIGN PENDING
Human Decision                     = RECORDED
Selected Container                 = Flat Directory
Artifact Granularity               = one included logical dataset → one JSON artifact
Manifest Placement                 = package root
Manifest Filename                  = manifest.json
Nested Directories                 = NOT ALLOWED FOR POC v0.2
L-1 ～ L-11                         = HUMAN APPROVED FOR IMPLEMENTATION
Implementation                     = NOT YET EXECUTED
Physical Dataset Layout Closure    = NOT YET EXECUTED

Field Carrier Mapping              = DESIGN PENDING
Final Import Contract              = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
```

**本 PR 只记录 Human Decision。** **未**实施 `Physical Dataset Layout`，
**未**修改 `Physical Dataset Layout` status，**未**推进下游三层。

---

**Field Carrier Mapping Design Review（Review Finding）**

**Review Authority / Scope**

```
Review Type    = 独立 Design Review（只产出 Review Finding）
Review Object  = Field Carrier Mapping（§4.3 层级之一）
Decision Power = NONE —— 本 Review 不作出任何 Human Decision
Write Scope    = 仅 docs/design/poc-design-v0.2.md
Status Change  = NONE
```

本 Review **不选择**任何 carrier model，**不登记**任何 property name ／ envelope 作为 current design，
**不修改**任何 status，**不创建**任何 runtime artifact。

> **本节所有结构示意均为 illustrative（非 authoritative）。** 任何具体 property name ／ nested structure
> **只有在后续 Human Decision ＋ 独立 registration 之后**才可能成为 current design。

---

**Existing Canonical Constraints（固定 —— 不被本 Review 重新打开）**

| # | Constraint | Source |
| --- | --- | --- |
| `K-1` | `Serialization Format = JSON`；`C-1` ～ `C-10` = `REGISTERED` | `§4.3.22` |
| `K-2` | Package Container = Flat Directory Package；one included logical dataset = one independent JSON artifact；Manifest = package root ＋ `manifest.json`；root-level 唯一 filename ＋ `.json`；nested directories = `NOT ALLOWED`（POC v0.2） | `§4.3.23` |
| `K-3` | Manifest **必须显式**建立 `logical dataset role → physical artifact reference`；**不得**依赖 filename inference ／ file ordering ／ discovery heuristic | `§4.3.23` E ／ `§4.3.10` |
| `K-4` | `included ＋ record_count = 0` → 对应 artifact `REQUIRED`；`not included` → artifact `NOT REQUIRED` | `§4.3.23` F ／ `§4.3.13` |
| `K-5` | `Snapshot Manifest ≠ business dataset`；Manifest 承载 transport ／ provenance metadata，**不得**作为 business field 进入 Canonical Data Dictionary | `§4.3.8` |
| `K-6` | Logical Manifest **至少**表达：`snapshot_package_id` ／ contract version ／ export ／ package creation time ／ environment ／ evidence classification ／ included logical datasets ／ dataset-level provenance reference ／ dataset-level record count ／ integrity evidence ／ package completeness state | `§4.3.8` |
| `K-7` | **两层 provenance 不得混合**：dataset-level provenance reference **≠** `Stable Source Evidence Locator` | `§4.3.8` ／ `§4.3.16` ／ `§4.5.22` |
| `K-8` | **Layered Logical Provenance Contract** = `Snapshot Package Identity` ＋ `Logical Dataset Role` ＋ `Stable Source Evidence Locator` ＋ `Mapping / Resolution Basis`（when applicable）＋ `Analysis Run linkage`；`logical carrier ≠ physical carrier` | `§4.5.22` Option D ／ `§4.3.16` |
| `K-9` | `valid absence ≠ missing required data`；`dataset not included ≠ dataset included with zero records` | `§4.3.13` ／ `§4.3.14` ／ `§4.3.22` `C-2` ／ `C-8` |
| `K-10` | Logical Types（`IDENTIFIER` ／ `ANALYSIS_RUN_ID` ／ `DATE` ／ `TIMESTAMP` ／ `DECIMAL_QUANTITY` ／ `NON_NEGATIVE_QUANTITY` ／ `RATIO` ／ `PERCENTAGE` ／ `STATUS` ／ `TEXT_CONTEXT`）**不得**映射成 database type | `§4.2.2` |
| `K-11` | Requiredness = `REQUIRED` ／ `CONDITIONAL` ／ `DERIVED` ／ `CONTEXT`；`missing` **不得**等同于 `0` ／ `false` ／ empty string ／ `UNKNOWN` | `§4.2.2` ／ `§4.2.12` |
| `K-12` | `IDENTIFIER` ／ `ANALYSIS_RUN_ID` ／ `TEXT_CONTEXT` ／ transport `snapshot_package_id` = JSON string，**exact opaque**，**禁止** semantic coercion ／ normalization | `§4.3.22` `C-10` |
| `K-13` | **不得**要求每个 Snapshot Package 包含所有 logical datasets | `§4.3.14` |
| `K-14` | integrity evidence **required**；**算法**（hash ／ checksum ／ signature）属 `Final Import Contract` | `§4.3.15` |
| `K-15` | `Physical Dataset Layout` 已关闭：`L-1` ～ `L-11` = **ALL `PASS`** | `§4.3.24` |
| `K-16` | **已批准的 provenance cardinality 与 completeness（不得收窄）**：**必须**支持 `multiple source evidence → one canonical fact` 与 `one source evidence → multiple canonical outputs`；**不得**强制 `one canonical fact = exactly one source evidence`，**不得**假定 `one source row = one canonical field`；`Stable Source Evidence Locator` **必须**支撑**具体 canonical observation ／ context**；`Mapping / Resolution Basis` **必须** identifiable and reproducible —— **`when applicable`**：**仅当发生 semantic mapping ／ resolution 时**才需要回答（与 `K-8` 一致）；provenance complete **至少**可回答 Snapshot Package ／ logical dataset role ／ 具体 source evidence ／ **（若发生 semantic mapping）** mapping ／ resolution basis ／ Analysis ／ business context | `§4.5.22`（决定 10 ／ 11）／ `§4.3.16` |

---

**Exact Review Scope**

**In scope（仅以下问题）：**

1. Manifest 的 physical JSON carrier model —— package-level metadata 的 property 集合与 grouping boundary
   （**含 `K-6` 的 dataset-level `record count` ／ integrity evidence 的 carrier 位置与 grouping boundary**）
2. `logical dataset role → artifact reference` 的 concrete carrier model
3. business dataset artifact 的 top-level carrier ／ envelope boundary
4. record carrier boundary
5. canonical field → JSON property carrier policy
6. `Stable Source Evidence Locator` 的 physical carrier
7. `Mapping / Resolution Basis` 的 physical carrier
8. `missing` ／ `null` ／ omission 与 `included-empty` 在 carrier 层的 semantics 保持
9. carrier 与 `Serialization Format` ／ `Physical Dataset Layout` ／ Logical Provenance Contract 的 compatibility
10. `Field Carrier Mapping` 的 minimum closure criteria 候选

**Out of scope（属其他层，本 Review 只记录 dependency）：**

- integrity ／ hash ／ checksum ／ signature **algorithm** ／ byte-level canonicalization → `Final Import Contract`（**integrity evidence 的 carrier 位置**属本层，见 `CS-12a` ／ `RF-X5`）
- runtime acceptance ／ rejection ／ path validation ／ traversal ／ symlink → `Final Import Contract`
- Adapter ／ 连接器 ／ 传输协议 ／ 真实 source field → `Adapter Boundary`
- canonical entity ／ field ／ enum ／ Validation Reason 的新增或修改 → 非本 Task 授权范围

---

**Critical Scenarios**

| # | Scenario | 既有约束要求的行为 | 本层必须保证的性质 |
| --- | --- | --- | --- |
| `CS-1` | dataset `not included` | artifact `NOT REQUIRED`（`K-4`） | **不得**由「artifact 缺失」推断业务结论 |
| `CS-2` | dataset `included` 且 `record_count = 0` | artifact `REQUIRED`（`K-4`） | 必须存在可 deterministic locate 的 artifact，且与 `CS-1` **可区分** |
| `CS-3` | canonical value 属 **valid absence**（例：`Classification = NORMAL` ⇒ 未产生 `RecommendedPurchaseQty`） | **不得**导致 package invalid（`K-9`） | carrier 必须能表达「按设计未产生」，**不等于** `missing` |
| `CS-4` | canonical field 在 source 侧确实缺失 | `missing ≠ 0 ／ false ／ ""`（`K-11`） | carrier 层必须有**唯一确定**的 missing representation |
| `CS-5` | 某 canonical value 由**一条具体 source evidence** 支撑 | 需要 `Stable Source Evidence Locator`（`K-7` ／ `K-8`） | dataset-level reference **不足以**替代 evidence-level locator |
| `CS-13` | **多个** source evidence 共同支撑**一个** canonical fact；或**一份** source evidence 支撑**多个** canonical outputs；且同一 record 内不同 canonical input 使用**不同** mapping ／ resolution basis | **必须**支持该 cardinality（`K-16`）；locator **必须**支撑具体 canonical observation ／ context；basis **必须** identifiable and reproducible | carrier **必须**能**确定性表达** evidence ↔ canonical observation ／ context 的关联与 cardinality；**不得**仅凭「存在一个 locator ／ basis」即视为满足。**注意：** record identity **不得**未经论证即等同于 source evidence identity |
| `CS-6` | mapping 结果为 `unresolved` | 需要 `Mapping / Resolution Basis`（`K-8`） | **不得**因此新增 business field semantic |
| `CS-7` | `IDENTIFIER` = `"00123"` | exact opaque；**禁止** leading-zero removal（`K-12`） | carrier **不得**诱发 numeric interpretation |
| `CS-8` | `DECIMAL_QUANTITY` = `"12.50"` | base-10 decimal string；**禁止** round ／ quantize ／ truncate（`C-5`） | carrier **不得**要求 numeric type |
| `CS-9` | `sourcing_status` 携带 source-specific literal | **禁止** silent canonicalization（`C-7`） | property carrier **不得**暗示 canonical enum |
| `CS-10` | Manifest 声明 `included` 但 artifact missing | Structural inconsistency（`§4.3.12` 情形 A） | carrier **必须**使该不一致**可判定** |
| `CS-11` | package 只包含当前 capability 所需的**部分** datasets | 允许（`K-13`） | carrier **不得**暗示「完整 = 全部 dataset」 |
| `CS-12a` | **已批准 carrier metadata**（如 integrity evidence ／ dataset-level provenance ／ mapping basis）**是否存在**、以及放在 envelope ／ record sibling ／ nested namespace 的**哪里** | 既有 Design **未决定** | 属 **`Field Carrier Mapping`** —— **必须**由本层裁定（见 `RF-X5`）；**不得**推给 `Final Import Contract` |
| `CS-12b` | 输入出现**未在已批准 carrier contract 中声明**的 unknown property 时，runtime 的 reject ／ ignore ／ tolerate 行为及验证方式 | 既有 Design **未定义** | 属 **`Final Import Contract`** —— 本层**不**裁定 runtime policy |

---

**Candidate Carrier Models（illustrative —— 非 authoritative）**

以下片段**仅为结构示意**，以 `<...>` 表示 placeholder，**不得**被引用为 current design。

**A. Manifest Carrier Model（`Q1`）**

`M-0` —— 维持 `Field Carrier Mapping = DESIGN PENDING`（Do Nothing）
- 不构成进展；仅作为对照基线。

`M-A` —— Flat manifest object（package-level metadata 与 dataset entries **同层**）

```
{
  "<package-level property>": "<value>",
  "<dataset entry property>": "<entry>"
}
```

- 优点：结构最浅、human inspectability 最高、implementation complexity 最低；
- 风险：package-level 与 dataset-level 的 property 命名空间**无物理分离**，
  层次区分只能依赖命名约定（`K-5` 的 `manifest ≠ business dataset` 仍成立，但层次边界弱化）。

`M-B` —— Grouped nested manifest object（package block ＋ dataset collection）

```
{
  "<package block>": { "<property>": "<value>" },
  "<dataset collection>": [ "<entry>" ]
}
```

- 优点：transport ／ dataset 两个层次**物理分组**，层次边界显式；
- 风险：结构更深；collection 形态需另行裁定（见 `D-*`）；inspectability 略降。

`M-C` —— Package header ＋ 独立 dataset index（或独立 integrity 区段）
- 当前 **无证据**要求该形态；**不建议**在 POC v0.2 引入。

**integrity evidence carrier（`K-6` ／ `K-14`）：** Logical Manifest **必须**表达 dataset-level
**integrity evidence**；其 **physical carrier 的位置与 grouping boundary**
（package-level carrier ／ dataset-entry-level carrier ／ 与 business field 的分离方式）
**必须**由本层裁定（见 `CS-12a` ／ `RF-X5`）—— **是否存在**与**放在哪里**属本层；
**算法**（hash ／ checksum ／ signature）属 `Final Import Contract`。

**B. Dataset Entry Model（`Q2`）**

`D-A` —— array of dataset entry objects

```
[ { "<logical dataset role>": "<role>", "<artifact reference>": "<artifact>", "<record count>": 0 } ]
```

- 优点：条目同构、易于 validate、易表达「无 entry」；
- **必须保持的 design invariant（`RF-2` ／ `F-2`）：** 同一个 included logical role
  **只**建立 **一个** authoritative artifact association —— 由 `K-2`（one included logical dataset =
  one independent JSON artifact）＋ `K-3`（Manifest 显式建立 `role → artifact reference`）共同要求；
- 风险：array 形态**不会自动**保证该 invariant，**必须**由 carrier contract 明确其 cardinality ／
  uniqueness 规则；runtime **如何检测 ／ reject** duplicate 或 conflicting entry 属 `Final Import Contract`。

`D-B` —— object keyed by logical dataset role

```
{ "<logical dataset role>": { "<artifact reference>": "<artifact>", "<record count>": 0 } }
```

- 优点：`role → entry` 天然唯一，查表直接；
- **design invariant（`RF-2` ／ `F-2`）：** 与 `D-A` **同一** logical invariant ——
  一个 included logical role **只**对应一个 authoritative artifact association；
- 风险：canonical role 字面量被固化为 JSON property name，与 `K-12` 的 exact-string 要求叠加时，
  **必须**先明确 role 字面量的 case ／ escaping 规则（见 `RF-X2`）。

`D-C` —— dataset entry 以 flat property 组合表达（无 collection 结构）
- 仅在 `M-A` 下可行；role 集合的扩展性最差。

**共同要求（无论 `D-*`）：** entry **必须**携带 artifact reference（`K-3`）与 presence metadata（`K-4`），
且二者与 logical role 之间**必须**存在**确定、唯一、可判定**的关联 ——
**物理同组**（同一 entry ／ object ／ group）属**候选简化方案**，**不是**强制条件（见 `RF-2`）；
且 dataset-level provenance reference（`K-6`）、**integrity evidence**（`K-6` ／ `K-14`）
与 evidence-level locator（`K-7`）**必须可分别承载**。
**integrity evidence 的 carrier 位置与 grouping boundary** 属本层裁定（`CS-12a` ／ `RF-X5`），
但 **hash ／ checksum ／ signature 算法**仍属 `Final Import Contract`。

**C. Business Dataset Top-Level Carrier（`Q3`）**

`B-A` —— bare record array

```
[ { "<canonical field>": "<value>" } ]
```

- 优点：结构最简、record 边界明确；`included ＋ 0 records` 可用空数组自然表达；
- 风险：**dataset-level metadata 无处安放**；若未来需要 dataset-level 信息落在 artifact 内，则需重新设计。

`B-B` —— object envelope（dataset metadata ＋ records）

```
{ "<dataset metadata>": "<value>", "<records>": [ { "<canonical field>": "<value>" } ] }
```

- 优点：dataset-level metadata 与 records 同 artifact，dataset boundary 自包含；
- 风险：引入 envelope 结构 —— **该结构本身即属本层设计责任**；
  `included ＋ 0 records` 的表达依赖 envelope 内 records 为空，**必须**与 `CS-1` 仍可区分。

`B-C` —— object envelope **仅**含 metadata，records 以 sidecar 表达
- 与 `K-2`（one included logical dataset = **one independent JSON artifact**）**直接冲突**
  → **`NOT COMPATIBLE`**，不予保留。

**D. Record Carrier（`Q4`）**

`R-A` —— 每个 record = JSON object，property name 由 canonical field carrier policy 决定
- 与 `C-9`（object member order **不得**具有 business semantic）一致。

`R-B` —— 每个 record = 位置数组（positional）
- **技术上与 `C-9` 兼容** —— `C-9` 只规定 JSON **object member order** 不得具有 business semantic，
  **并未**禁止 JSON array 的位置语义，**也未**建立「必须 property-addressed object」的 canonical rule；
- 但若采用，**必须**另行显式登记 **deterministic positional mapping ／ field order contract**；
  否则字段顺序变化会静默改变语义，**复杂度与可维护性更差**、human inspectability 更低；
- 因此这是**需要权衡的 trade-off**，**不是 canonical prohibition** → **`NOT RECOMMENDED`**。

`R-C` —— record = JSON object，且**允许**非 canonical 的 carrier-level 属性混入
- 风险：混淆 business record 与 carrier metadata；
  **必须**先由 Human 明确是否允许及允许范围（见 `Q4-6`）。

**E. Canonical Field Carrier（`Q5`）**

`F-A` / `F-B` / `F-C` 属 **object-record branch**（`R-A` ／ `R-C`）：canonical field → **JSON property name**。
- `F-A` —— canonical identifier **直接**且稳定地作为 JSON property name
- `F-B` —— canonical identifier 作为 property name，＋ manifest 内**显式** mapping table
- `F-C` —— source-specific property name，＋ 每个 dataset 的**显式** mapping

`F-P` —— **positional-record branch（仅当 Human 选择 `R-B` 时适用）**：canonical field → **position**
- **必须**同期登记 **deterministic field-position ／ order contract**（position ↔ canonical field 完整对应）；
- **必须**明确 optional ／ omitted value 在该 branch 下如何保持 `C-2`
  （`null` = explicit missing；position 缺失 ／ 不可区分 **不得**自动等同于 valid absence）；
- **必须**明确该 branch 下**可用**的 provenance ／ basis carrier 组合（见 **`RF-X6`** branch dependency ／ compatibility）。

**共同硬约束（含 `F-P`）：** **不得**改变 canonical field semantic；
**不得**因 naming ／ position 引入 numeric ／ case ／ trim coercion（`K-10` ／ `K-12`）。
`F-A` ／ `F-B` ／ `F-C` 的差异在于 **stability vs flexibility**。
**本 Review 不选择是否保留或排除 `R-B`，也不定义任何实际顺序或 property name。**

**F. Evidence-Level Provenance Carrier（`Q6` ／ `Q7`）**

`P-A` —— record-level **nested** provenance object
`P-B` —— record-level **flat** 属性（保留命名空间）
`P-C` —— 与 records **平行**的 provenance 结构，以 record identity 关联
`P-D` —— dataset-level provenance object 内以**数组**承载 per-record locator

**共同硬约束：** dataset-level reference **≠** evidence-level locator（`K-7`）；
locator **不得**退化为 artifact path ／ filename（`K-3` ／ `§4.3.16`）；
physical carrier **不得**等同于 `Stable Source Evidence Locator` 的 semantic 本身（`K-8`）。
**且（`K-16`）：** carrier **必须**能确定性表达 **evidence ↔ canonical observation ／ context** 的关联与
**cardinality**（多对一 ／ 一对多）；`P-A` ～ `P-D` 的兼容性**以**满足该条件为前提 ——
仅「存在一个 record-level locator」**不构成**兼容（见 `CS-13`）。

**G. Mapping / Resolution Basis Carrier（`Q8`）**

`MB-A` —— 与 provenance carrier **同一** nested 结构
`MB-B` —— record-level **sibling** property
`MB-C` —— manifest-declared **resolution basis table**

**共同硬约束：** `when applicable` —— **不得**要求所有 record 普遍携带；
**不得**新增 business field semantic（`K-8`）。
**且（`K-16`）：** 若同一 record 内不同 canonical input 使用**不同** basis，
carrier **必须**能确定性表达 **basis ↔ canonical input** 的关联；
`MB-A` ～ `MB-C` 的兼容性**以**满足该条件为前提。

**H. Missing / Omission Policy（`Q9`）**

`N-A` —— **即已登记的 `C-2` policy**：`null` = **explicit missing ／ unavailable serialized value**；
**property omission** = field **not serialized**，其业务语义**必须**由
**canonical requiredness ＋ business applicability ＋ existing validation semantic** 共同判断；
`valid absence ／ not produced by design` **允许** omission，
但 **`omission` 本身不自动等于 `valid absence`**。

`N-B` —— 始终发出所有 property，统一用 `null` 表示
- 把 `valid absence` 与 `missing` **压平**，与 `K-9` 直接冲突 → **`NOT COMPATIBLE`**

`N-C` —— 以 sentinel 字符串（如 `"UNKNOWN"`）表达 missing
- 与 `C-2` ／ `K-11` 直接冲突 → **`NOT COMPATIBLE`**

---

**Option Comparison**

`—` = 不适用。判定针对与**既有 canonical 约束**的兼容性，**不代表**本 Review 的选择。

| Model | `C-1` ～ `C-10` | Flat Directory Layout（`K-2`） | Logical Provenance Contract（`K-7` ／ `K-8`） | 备注 |
| --- | --- | --- | --- | --- |
| `M-A` | 兼容 | 兼容 | 兼容（层次仅靠命名约定） | 最浅结构 |
| `M-B` | 兼容 | 兼容 | 兼容（层次显式） | 结构更深 |
| `M-C` | 兼容 | 兼容 | 兼容 | 当前证据不足 |
| `D-A` | 兼容 | 兼容 | 兼容 | **须**登记 role-entry cardinality ／ uniqueness invariant（`F-2`）；**不要求**物理同组 |
| `D-B` | 兼容 | 兼容 | 兼容 | 需先定 role 字面量规则 |
| `D-C` | 兼容 | 兼容 | 兼容 | 扩展性最差 |
| `B-A` | 兼容 | 兼容 | **条件兼容** —— 若 dataset-level metadata 由 **Manifest** 承载（`§4.3.8` 已如此要求），bare array **不违反** Logical Provenance Contract；仅在「dataset-level metadata **必须**与 records 同 artifact 顶层」时才构成张力 | 待 Human 裁定（见 `RF-X1`） |
| `B-B` | 兼容 | 兼容 | 兼容 | 引入 envelope 结构 |
| `B-C` | 兼容 | **`NOT COMPATIBLE`** | — | 与 one-artifact 规则冲突 |
| `R-A` | 兼容 | 兼容 | 兼容 | 与 `C-9` 一致 |
| `R-B` | 兼容（`C-9` 未禁止 array 位置语义） | 兼容 | 兼容 | 需显式 positional ／ field order contract；trade-off，不建议 |
| `R-C` | 兼容 | 兼容 | 兼容 | **record-level** 作用域；需先明确允许范围；与 dataset-level metadata placement **不是**同一轴（见 `RF-X1`） |
| `F-A` | 兼容 | 兼容 | 兼容 | 稳定性最高；**仅**适用 object-record branch |
| `F-B` | 兼容 | 兼容 | 兼容 | 允许将来改名；**仅**适用 object-record branch |
| `F-C` | 兼容 | 兼容 | 兼容 | 需显式 deterministic mapping；**仅**适用 object-record branch |
| `P-A` | 兼容 | 兼容 | **兼容（以 `K-16` 关联 ／ cardinality 可判定为前提）** | 需能表达 evidence ↔ observation cardinality |
| `P-B` | 兼容 | 兼容 | **兼容（以 `K-16` 关联 ／ cardinality 可判定为前提）** | 命名空间冲突风险 |
| `P-C` | 兼容 | 兼容 | **兼容（以 `K-16` 关联 ／ cardinality 可判定为前提）** | 需 record identity linkage；**不得**假定 record identity = evidence identity |
| `P-D` | 兼容 | 兼容 | **兼容（以 `K-16` 关联 ／ cardinality 可判定为前提）** | 需 locator 数组结构 |
| `MB-A` | 兼容 | 兼容 | **兼容（以 basis ↔ canonical input 关联可判定为前提）** | — |
| `MB-B` | 兼容 | 兼容 | **兼容（以 basis ↔ canonical input 关联可判定为前提）** | — |
| `MB-C` | 兼容 | 兼容 | **兼容（以 basis ↔ canonical input 关联可判定为前提）** | — |
| `N-A` | **兼容（即已登记的 `C-2` policy 本身）** | 兼容 | 兼容 | 与 `K-9` 一致；不新增 token |
| `N-B` | **`NOT COMPATIBLE`** | — | — | 压平 absence ／ missing |
| `N-C` | **`NOT COMPATIBLE`** | — | — | 违反 `C-2` ／ `K-11` |

---

**Review Findings**

**`RF-1`（`Q1` Manifest Carrier Model）**
本层**必须**给出 package-level metadata 的 property 集合（`K-6` 的 8 项）与 dataset entries 的
grouping boundary。`M-A` 与 `M-B` 均可满足既有约束，差异在**层次显式性与结构深度**；
`M-C` 当前**无证据支持**。**本 Review 不选择。**

**`RF-2`（`Q2` Dataset Entry Carrier）**
`role → artifact reference` 的**存在性要求**已由 `§4.3.23` E 关闭；本层只决定其 **carrier 形态**。
**本 Review 判定（本层必须保持的 design invariant）：**
① presence ／ record count 与 `role → artifact` association **必须**对**同一 logical dataset scope**
   存在**确定、唯一、可判定**的关联；**是否**物理同组（同一 entry ／ object ／ group）
   属**候选结构 trade-off**，由 Human 决定 —— `§4.3.8` ／ `§4.3.23` 只要求**明确且可判定**，
   **未**要求同一对象；
② **同一个 included logical role 只建立一个 authoritative artifact association**
（cardinality ／ uniqueness invariant）—— 由 `K-2` ＋ `K-3` 共同要求，**不是**可选项；
`D-A` ／ `D-B` ／ `D-C` **均必须**满足同一 logical invariant；
runtime **如何检测 ／ reject** duplicate 或 conflicting entry 属 `Final Import Contract`。
`D-A` ／ `D-B` ／ `D-C` 的具体取舍属 Human Decision。

**`RF-3`（`Q3` Business Dataset Top-Level Carrier）**
`B-C` 与 `K-2` **不兼容**，予以排除。`B-A` 与 `B-B` 的取舍取决于
**「dataset-level metadata 是否必须落在 business dataset artifact 内」** ——
该问题**当前无 canonical 证据**可自动裁定，属 Human Decision（见 `RF-X1`）。

**`RF-4`（`Q4` Record Carrier）**
既有约束**并未**要求 property addressing —— `C-9` 只约束 **object member order 不得具有 business semantic**，
**未**禁止 array 位置语义，**也未**建立「必须 property-addressed object」的规则。
因此 `R-B`（positional）属**可选 trade-off**：若采用，**必须**显式登记
**deterministic positional mapping ／ field order contract**，并接受更差的复杂度与 inspectability。
**本 Review 判定 `R-A` 与既有约束一致，`R-B` 技术上可兼容但需额外契约**；
「是否**强制**每个 record 为 JSON object」与「是否允许 carrier-level 属性混入（`R-C`）」属 Human Decision。

**`RF-5`（`Q5` Canonical Field Carrier）**
**不得**改变 canonical field semantic（硬约束）。`F-A` ／ `F-B` ／ `F-C` 均可满足 compatibility。
**本 Review 判定：** 若采用 `F-C`，则 mapping **必须**显式且 deterministic，
**不得**依赖 Adapter 的隐式行为；否则 `CS-7` ／ `CS-9` 不可保。

**`RF-6`（`Q6` Logical Type Compatibility）**
`C-1` ～ `C-10` **已经**固定 representation；本层只需保证 carrier **不引入**违反它们的结构
（例如以 numeric type 承载 `DECIMAL_QUANTITY`、或 property name 触发 coercion）。
**兼容性可判定，无需新 decision** —— `N-*` policy 实际上**已由 `C-2` 固定**（`N-A` = `C-2` 本身）；`N-B` ／ `N-C` 已判定不可兼容。

**`RF-7`（`Q7` Evidence-Level Provenance Carrier）**
`K-7` ／ `K-8` ／ **`K-16`** 要求 locator **可被稳定重新定位**，且能支撑**具体 canonical observation ／
context**，并**确定性表达** `multiple evidence → one canonical fact` 与
`one evidence → multiple canonical outputs` 的 cardinality。
`P-A` ～ `P-D` 均**可**兼容，但**前提是**满足 `K-16`（见 `CS-13`）——
仅登记一个 record-level locator **不足**。
**不可让步项：** dataset-level reference **不得**被当作 locator 使用；
locator **不得**以 artifact path ／ filename 表达；
record identity **不得**未经论证即等同于 source evidence identity。

**`RF-8`（`Q8` Mapping / Resolution Basis Carrier）**
`when applicable` 是硬约束：**不得**要求普遍存在。`MB-A` ／ `MB-B` ／ `MB-C` 均**可**兼容，
但**前提是**当同一 record 内不同 canonical input 使用**不同** basis 时，
carrier 能**确定性表达** `basis ↔ canonical input` 的关联（`K-16`）。
**不得**因此新增 business field semantic。

**`RF-9`（`Q9` Carrier Requiredness）**
本层**必须**区分三层 requiredness：
**package-level required**（`K-6`）／ **dataset-entry required**（`K-3` ／ `K-4`）／
**record-level conditional**（`§4.2.2` requiredness）。
**不得**把 `valid absence` ／ `missing` ／ `not applicable` 的语义**压平**（`CS-3` ／ `CS-4`）。
**本 Review 判定：** 本层**不要求** carrier 为三者各自定义独立 token；**要求**的是
**omission 的语义推断链不被压平** —— `property omission` **不自动等于** `valid absence`，
且 `null` **不得**被 `0` ／ `false` ／ `""` ／ sentinel string 替代（`C-2` ／ `K-11`）。

**`RF-10`（`Q10` Closure Criteria）**
见下方候选 `F-1` ～ `F-17`；**是否登记为正式 criteria 属 Human Decision** —— 本 Review **不自行宣布**。

**`RF-X1`（三个独立轴 —— 不得耦合裁定）**
以下为**三个不同粒度**的独立决定轴；**选择其一不自动决定其他**：

| 轴 | 问题 | 关联 option |
| --- | --- | --- |
| **X1-A** | **dataset-level** metadata 是否**还**需要与 records 同 artifact 顶层承载（`§4.3.8` **已要求** **Manifest** 承载 dataset-level provenance，**未**要求其在 business artifact 中重复） | `B-A` ／ `B-B` |
| **X1-B** | **record-level** carrier metadata 是否允许混入 business record | `R-C` |
| **X1-C** | evidence ／ mapping basis 如何**确定性关联**到具体 record ／ canonical observation | `P-*` ／ `MB-*` ／ `K-16` |

**反例（说明不可耦合）：** `B-A` bare array 的每个 object record **可以**携带 evidence-level provenance，
而 dataset-level metadata 由 **Manifest** 承载 —— 此组合**不需要** dataset envelope；
`B-B` **可以**在 envelope 放 dataset metadata，同时 records 保持**纯** business properties ——
此组合**不必**允许 `R-C`。

**若**同一 metadata 同时出现在 **Manifest** 与 business artifact，
**FCM 必须**定义二者之间的 **design association ／ consistency relation**；
其 runtime 冲突行为**仍属** `Final Import Contract`。
本 Review **不替 Human 选择**其中任何组合。

**`RF-X2`（跨层风险）**
若采用 `D-B`（role 作为 JSON property name），canonical role 字面量的
**case ／ escaping 规则**必须在 closure 前显式定义；否则同一 logical role 的不同写法
会产生两个 entry，直接破坏 `K-3` 的唯一性。

**`RF-X3`（边界发现 —— 明确不属于本层）**
integrity **algorithm** ／ byte-level canonicalization ／ runtime acceptance ／ rejection ／
**unknown ／ undeclared property 的 runtime 行为** ／ path validation ／ version compatibility policy ／
schema validation implementation **全部**留给 **`Final Import Contract`**。
（**注意：** integrity evidence 的 **carrier 位置与 grouping boundary** **不属于**此类 —— 见 `RF-X5` ／ `CS-12a`。）

**`RF-X4`（一致性风险）**
若各 option 被**独立**裁定而缺少跨选择一致性检查，可能出现**组合冲突** —— 例如：

- Human **#4** 要求 dataset-level metadata **必须存在于 business artifact 顶层**，但 **#3** 同时选择
  `B-A` bare record array（**无** envelope 可承载）；
- **#5** 选择 `R-B` positional，但 **#7** 只登记 property-addressed policy（**未**登记 `F-P`）；
- positional branch 下选择按 **`RF-X6`** 判定**不成立**的 record-level carrier（如 `P-B` ／ `MB-B`）。

**注意：** 「同一 metadata 同时存在于 Manifest 与 business artifact」**本身不是**冲突 ——
它**可以**通过 duplication ＋ 显式 association ／ consistency relation 成立（见 `RF-X1`）；
其 runtime 冲突处理**仍属** `Final Import Contract`。

**建议** Human 以**组合**方式裁定，并**要求** `F-14` 实际检查 `RF-X1` 三轴、`RF-X6` branch dependency
与 `R-*` ／ `F-*` 的登记组合约束。

**`RF-X5`（carrier structure vs runtime policy —— 层级划分）**
必须区分两个问题：

1. **FCM 设计问题** —— **已批准 carrier metadata**（含 **integrity evidence**、dataset-level provenance、
   `Mapping / Resolution Basis`）**是否存在**、以及位于 envelope ／ record sibling ／ nested namespace 的**哪里**；
   这属 **`Field Carrier Mapping`**，**必须**由本层裁定。
2. **FIC runtime contract 问题** —— 输入出现**未在已批准 carrier contract 中声明**的 unknown property 时，
   runtime 的 reject ／ ignore ／ tolerate 行为及验证方式；这属 **`Final Import Contract`**。

**不得**把第 1 类问题推给 `Final Import Contract`；**也不得**由本层擅自裁定第 2 类问题。

**`RF-X6`（branch dependency ／ compatibility —— 供 Human 组合裁定）**

下表**只**登记**已知**的 branch dependency 与**可判定性**，**不选择** object vs positional，
**不新增** carrier family。判定基于**当前候选定义**（`R-*` ／ `F-*` ／ `P-*` ／ `MB-*`），
**不得**被解读为对 `R-A` ／ `R-B` 的取舍。

| option | object-record branch（`R-A` ／ `R-C`） | positional-record branch（`R-B`，**须** `F-P`） |
| --- | --- | --- |
| `F-A` ／ `F-B` ／ `F-C` | **可用** —— canonical field → JSON **property name** | **不适用** —— 其定义即为 property name；该 branch 由 `F-P` 承担 |
| `P-A`（record-level nested provenance object） | **可用** | **需 wrapper** —— 须先由 `F-P` 保留一个 position 承载该 sub-object；否则**不成立** |
| `P-B`（record-level flat 属性） | **可用** | **不成立** —— 「flat 属性」以 property name 为前提，positional record **无** property name。若欲成立**必须新增**候选形态（本 Review **不新增**） |
| `P-C`（以 record identity 关联的 parallel structure） | **可用**（需稳定 record identity） | **可用**，**前提**是 `F-P` 显式指定 identity position；否则属**需 Human 子裁定** |
| `P-D`（dataset-level object ＋ per-record locator 数组） | **可用** | **可用** —— linkage 以 deterministic positional index（受 `F-P` 约束）表达 |
| `MB-A`（与 provenance 同一 nested 结构） | **可用**（跟随所选 `P-*`） | **跟随 `P-*`** —— 所选为 `P-A` 则**需 wrapper**；为 `P-B` 则**不成立** |
| `MB-B`（record-level sibling property） | **可用** | **不成立** —— 同 `P-B` 理由 |
| `MB-C`（manifest-declared basis table） | **可用** | **可用** —— 不依赖 record 形态；linkage 经 role ＋ position ／ identity |

**`C-2` 在 positional branch 下的可判定性**

| 语义 | object-record branch | positional-record branch |
| --- | --- | --- |
| **explicit missing** | `null` | **可表达** —— 该 position 存在且值为 `null` |
| **field not serialized ／ omission**（`valid absence` **允许** omission） | **可表达** —— property omission（语义仍由 requiredness ＋ applicability ＋ validation semantic 判断） | **`UNRESOLVED` —— requires Human sub-decision** |

**`UNRESOLVED` 的理由：** positional array **不能**省略中间 field 而不改变其后所有 position；
而 current candidate set 内的替代方案**均不成立** ——
① 全部 position 均发出并统一用 `null` → **压平** absence ／ missing（违反 `K-9` ／ `F-12`）；
② 以 sentinel token 表达「未产生」→ 须**新增** carrier 形态，且**不得**使用 `0` ／ `false` ／ `""` ／ `"UNKNOWN"`（`C-2`）；
③ out-of-band presence 结构 → 属**未枚举**的 carrier 形态。

**因此：** `R-B` **仅**在「可表达 explicit missing，且**不需要** field-not-serialized 语义」的场景下可**安全组合**；
若 Human 需要完整 `C-2` 语义，现行候选集**不足以**表达 —— 必须作为 **positional branch 的 Human 子裁定**处理，
或改为选择 object-record branch。**本 Review 不代替 Human 作出该选择。**

---

**Proposed Minimum Closure Criteria（candidate —— 待 Human 批准）**

| # | Criterion | 类别 |
| --- | --- | --- |
| `F-1` | Manifest carrier model 已显式登记（含 package-level property 集合与 grouping boundary） | MANDATORY CLOSURE CRITERION |
| `F-2` | `logical dataset role → artifact reference` 的 carrier 形态已登记，满足 `K-3`，**并保持 role-entry cardinality ／ uniqueness invariant**（一个 included logical role → 一个 authoritative artifact association；`D-A` ／ `D-B` ／ `D-C` 均须满足） | MANDATORY CLOSURE CRITERION |
| `F-3` | presence metadata（record count ／ presence state）与 `role → artifact` association 对同一 logical dataset scope **可确定、唯一、可判定地关联**，使 `CS-1` 与 `CS-2` 可判定（**不要求**物理同组） | MANDATORY CLOSURE CRITERION |
| `F-4` | business dataset top-level carrier 形态已登记，且与 Flat Directory Layout（`K-2`）兼容 | MANDATORY CLOSURE CRITERION |
| `F-5` | `included ＋ record_count = 0` 与 `not included` 在 physical carrier 层**可区分** | MANDATORY CLOSURE CRITERION |
| `F-6` | record carrier 形态已登记（含是否强制 JSON object ／ 是否允许 carrier-level 属性） | MANDATORY CLOSURE CRITERION |
| `F-7` | canonical field carrier policy 已登记，且**不改变** canonical field semantic：object-record branch 登记 property-addressed policy；**若**保留 positional-record branch，则**同期**登记 deterministic field-position ／ order contract 及其 `C-2` 保持规则（`F-P`） | MANDATORY CLOSURE CRITERION |
| `F-8` | carrier **不违反** `C-1` ～ `C-10`（尤其 `C-2` ／ `C-5` ／ `C-7` ／ `C-9` ／ `C-10`） | MANDATORY CLOSURE CRITERION |
| `F-9` | dataset-level provenance reference 的 carrier 已登记 | MANDATORY CLOSURE CRITERION |
| `F-10` | `Stable Source Evidence Locator` 的 carrier 已登记，与 dataset-level reference **分层不混合**，**并能确定性表达 evidence ↔ canonical observation ／ context 的关联与 `K-16` cardinality**（多对一 ／ 一对多） | MANDATORY CLOSURE CRITERION |
| `F-11` | `Mapping / Resolution Basis` 的 carrier 已登记（when applicable），**且能确定性表达 basis ↔ canonical input 的关联**（同一 record 内多 basis 时） | MANDATORY CLOSURE CRITERION |
| `F-12` | carrier 层**不压平** `valid absence` ／ `missing` ／ `not applicable` 的语义：`property omission` **不自动等于** `valid absence`，且 `null` **不得**被 `0` ／ `false` ／ `""` ／ sentinel string 替代（`C-2` ／ `K-11`；`N-B` ／ `N-C` 类方案被排除） | MANDATORY CLOSURE CRITERION |
| `F-13` | carrier 层**无** silent fix-up（trim ／ case conversion ／ numeric coercion ／ Unicode normalization） | MANDATORY CLOSURE CRITERION |
| `F-14` | **已知** option combination 的 dependency ／ incompatibility **已显式登记**（含 positional-record branch 下**可用**的 field ／ provenance ／ basis 组合，以及 `RF-X1` 三轴 X1-A ／ X1-B ／ X1-C 的组合约束），且**无未登记的跨选择冲突**（见 `RF-X4` ／ **`RF-X6`**） | MANDATORY CLOSURE CRITERION |
| `F-15` | Human Inspectability（carrier 可被人直接检视） | POC DESIGN OBJECTIVE |
| `F-16` | Implementation Simplicity（carrier 结构最小化） | POC DESIGN OBJECTIVE |
| `F-17` | **integrity evidence** 的 physical carrier（package-level ／ dataset-entry-level 的位置与 grouping boundary）已登记，且不与 business field 混淆（**算法**仍属 `Final Import Contract`） | MANDATORY CLOSURE CRITERION |

`F-15` ／ `F-16` **必须评估**，但**不作为**独立 hard closure blocker；
**不得**把主观判断变成不可验证的 closure Gate。

**Closure Boundary（本层 vs `Final Import Contract`）**

| 问题 | 归属层 |
| --- | --- |
| Manifest ／ dataset entry ／ business dataset envelope ／ record ／ property carrier 形态 | **`Field Carrier Mapping`** |
| `missing` ／ valid absence ／ omission 的 representation policy | **`Field Carrier Mapping`** |
| evidence-level locator 与 mapping ／ resolution basis 的 carrier 形态 | **`Field Carrier Mapping`** |
| 已批准 carrier metadata（**integrity evidence** ／ dataset-level provenance ／ `Mapping / Resolution Basis`）的**位置与 grouping boundary** | **`Field Carrier Mapping`** |
| integrity ／ hash ／ checksum ／ signature **algorithm** | **`Final Import Contract`** |
| 未在已批准 carrier contract 中声明的 **unknown property** 的 runtime 行为（reject ／ ignore ／ tolerate）与验证 | **`Final Import Contract`** |
| byte-level canonicalization ／ canonical byte ordering | **`Final Import Contract`** |
| runtime acceptance ／ rejection algorithm ／ partial package 处理 | **`Final Import Contract`** |
| path normalization ／ traversal ／ symlink ／ path validation 实现 | **`Final Import Contract`** |
| contract version compatibility policy | **`Final Import Contract`** |
| JSON Schema ／ parser ／ serializer ／ validator 实现 | **`Final Import Contract`**（实现，非本层设计） |
| Adapter ／ 连接器 ／ 传输协议 ／ 真实 source field | **`Adapter Boundary`** |

---

**Human Decision Required**

| # | 问题 | 关联 |
| --- | --- | --- |
| 1 | **Manifest carrier model**：`M-A` flat ／ `M-B` grouped nested ／ 其他明确方案？（**并须裁定 integrity evidence 的 carrier 位置与 grouping boundary**，见 `F-17`） | `Q1` ／ `RF-1` ／ `RF-X5` |
| 2 | **dataset entries 的 collection 形态**：`D-A` array ／ `D-B` role-keyed object ／ `D-C` flat？（须保持 **role-entry cardinality ／ uniqueness invariant**，见 `F-2`） | `Q2` ／ `RF-X2` ／ `RF-2` |
| 3 | **business dataset top-level carrier**：`B-A` bare record array ／ `B-B` object envelope？ | `Q3` ／ `RF-X1` |
| 4 | **【轴 X1-A】** dataset-level metadata **是否还**需要与 records 同 artifact 顶层承载？（`§4.3.8` 已要求 Manifest 承载 dataset-level provenance；若两处并存，FCM **须**定义 association ／ consistency relation） | `Q3` ／ `RF-X1` |
| 5 | **record carrier**：是否**强制**每个 record 为 JSON object（`R-A` ／ `R-C`），还是保留 positional（`R-B`）？**（本项与 #7 属同一组依赖裁定；组合可判定性见 `RF-X6`）** | `Q4` ／ `RF-4` ／ `RF-X6` |
| 6 | **【轴 X1-B】** **record-level** carrier metadata 是否允许混入 business record？（**独立于** #4；作用域为 **record**，**不是**整个 business artifact） | `Q4` ／ `RF-X1` |
| 7 | **canonical field carrier**：object-record branch → `F-A` 直接 ／ `F-B` ＋ mapping table ／ `F-C` source-specific ＋ mapping？**若** #5 保留 positional record，则**须同期**裁定 field-position ／ order contract（`F-P`），其 dependency ／ `C-2` 可判定性见 `RF-X6` —— **#5 与 #7 属同一组依赖裁定** | `Q5` ／ `RF-5` ／ `RF-X6` |
| 8 | **【轴 X1-C】** **`Stable Source Evidence Locator` 的 carrier 形态**：`P-A` ／ `P-B` ／ `P-C` ／ `P-D`？（**须满足 `K-16`** 的 evidence ↔ canonical observation ／ context 关联与 cardinality；**须与 #5 的 branch 选择相容**，见 `RF-X6`） | `Q7` ／ `RF-7` ／ `CS-13` ／ `RF-X6` |
| 9 | **【轴 X1-C】** **`Mapping / Resolution Basis` 的 carrier 形态**：`MB-A` ／ `MB-B` ／ `MB-C`？（**须满足** basis ↔ canonical input 的确定性关联；**须与 #5 的 branch 选择相容**，见 `RF-X6`） | `Q8` ／ `RF-8` ／ `RF-X6` |
| 10 | **missing ／ omission policy**：是否确认**沿用已登记的 `C-2`**（`null` = explicit missing；`property omission` = field not serialized，语义由 requiredness ＋ applicability ＋ validation semantic 判断，**不自动等于** valid absence）？ | `Q9` ／ `F-12` |
| 11 | 是否接受 **`F-1` ～ `F-14` ＋ `F-17`** 作为 `Field Carrier Mapping` 的 minimum closure criteria？ | `Q10` ／ `RF-10` |
| 12 | 是否授权后续**独立** `Field Carrier Mapping` Design Change ／ Implementation PR（登记选择 ＋ 同步 current-state），并在满足 closure criteria 时允许 `DESIGN PENDING → DESIGN RESOLVED`？ | follow-up |

**本 Review 不作出上述任何决定。** 后续必须由 **Human Decision** 裁定；
**不得**由 Agent 自行选择最终 carrier model。

---

**Explicit Non-Decisions**

本 Review **不创建**：

```
JSON Schema
sample package ／ real manifest.json ／ dataset artifact
parser ／ serializer ／ validator
Adapter
runtime acceptance ／ rejection logic
path normalization ／ traversal ／ symlink handling
hash ／ checksum ／ signature algorithm
byte-level canonicalization
version compatibility policy
source-system real table ／ column mapping
new canonical business entity ／ field ／ enum
new Validation Reason
```

**Current Status（本 Review 时点）**

```
Snapshot / Import Contract overall = DESIGN PENDING
  Package Envelope ／ Atomicity Boundary ／ Immutability Boundary ／ Analysis Run Linkage = DESIGN RESOLVED
  Serialization Format             = DESIGN RESOLVED
  Physical Dataset Layout          = DESIGN RESOLVED
  Field Carrier Mapping            = DESIGN PENDING   ← 本 Review 对象；未关闭
  Final Import Contract            = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT

本 Review 不选择任何 Option。
本 Review 未创建任何 runtime artifact。
```

**Field Carrier Mapping Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Human Authority**

```
Human = Decision Authority
  （针对 PR #61 `Human Decision Required` #1 ～ #12 的 Decision Analysis 已由 Human 完成）
```

**Decision Source**

```
PR #61 Field Carrier Mapping Design Review（Review Finding）
  → Human Decision #1  ～ #12 = DECIDED
```

本记录**不重写** PR #61 `Field Carrier Mapping Design Review（Review Finding）`；
该 Review Finding（含 `RF-X1` ～ `RF-X6` 与 illustrative 声明）作为 **review evidence** **完整保留**。

---

**决定 1 —— Manifest Carrier = `M-B` Grouped Nested Manifest（APPROVED）**

```
Manifest Carrier Model = M-B Grouped Nested Manifest
  package-level metadata group  ≠  dataset collection group   （物理分组）
```

- package-level metadata 与 dataset collection **物理分组**；
- dataset-level `record_count` ／ dataset provenance ／ **integrity evidence** 与**对应 logical dataset entry** 关联；
- **对具体 dataset artifact 的 integrity evidence 放在 dataset-entry scope**，**不是** package block；
- integrity **algorithm**（hash ／ checksum ／ signature）**仍属 `Final Import Contract`**。

**exact property name ／ grouping name：** 本决定**未**提供任何字面名称。
依本决定：若不能从既有 approved terminology **唯一确定**，则**不得自行发明** → 见 **Decision Gap `G-1`**。

**决定 2 —— Dataset Entry Carrier = `D-A` array of dataset entry objects（APPROVED）**

```
Dataset Entry Model = D-A array of dataset entry objects
one included logical role → one authoritative artifact association   （invariant，必须保持）
```

- role ／ artifact reference ／ presence metadata 对**同一 logical dataset scope** 必须**确定、唯一、可判定**地关联；
- **不得**依赖 filename inference ／ ordering ／ discovery heuristic。

**决定 3 —— Business Dataset Top-Level Carrier = `B-A` bare record array（APPROVED）**

```
business dataset artifact top-level carrier = B-A bare record array
included ＋ record_count = 0  →  artifact 存在，payload 为可判定的 empty records representation
not included                  ≠  included-empty
```

**决定 4 —— Dataset-Level Metadata Placement = Manifest（authoritative）（APPROVED）**

- dataset-level metadata 的 **authoritative physical carrier = `Snapshot Manifest`**；
- **不**在 business dataset artifact 中**重复** dataset-level metadata；
- 因此 business dataset artifact **不**因 dataset metadata 引入 envelope；
- record ／ observation-level provenance **不属于**本决定 → 见 **决定 8** ／ **决定 9**。

**决定 5 —— Record Carrier = 强制 JSON object（APPROVED）**

- POC v0.2 **强制 JSON object record**；
- `R-B` positional record **不采用**；
- PR #61 的 `RF-X6` 作为 **review evidence** 保留，但 **positional branch 不进入 current POC v0.2 design**。

**决定 6 —— Record-Level Carrier Metadata = ALLOWED（受控 reserved metadata namespace）（APPROVED）**

- **允许** record-level technical ／ carrier metadata；
- technical metadata **必须**进入一个**受控的 reserved metadata namespace**；
- **不允许** technical metadata 与 canonical business fields **任意混杂**。

**exact property name：** 本决定**未**提供 reserved namespace 的字面名称。
依本决定：若不能从既有 approved terminology **唯一推出**，则**不得自行选择名称** → 见 **Decision Gap `G-2`**。

**决定 7 —— Canonical Field Carrier = `F-A`（APPROVED）**

```
canonical field identifier  →  JSON property name（直接、稳定）
```

- **不新增**第二层 field-name mapping；
- **不改变** canonical field semantic；
- **不允许** trim ／ case conversion ／ numeric coercion ／ Unicode normalization 等 **silent fix-up**。

**决定 8 —— Stable Source Evidence Locator Carrier = `P-A`（APPROVED）**

```
Evidence-Level Provenance Carrier = P-A record-level nested provenance structure
```

- provenance **必须**关联到**具体 canonical observation ／ context**，**不能**仅绑定整条 record；
- **必须**支持：

```
multiple source evidence → one canonical fact
one source evidence      → multiple canonical outputs
```

- `dataset-level provenance reference` **≠** `Stable Source Evidence Locator`；
- `record identity` **≠** `source evidence identity`；
- **不要求** locator 是 ERP PK ／ row ID ／ filename ／ JSON line ／ globally unique ID。

**决定 9 —— Mapping ／ Resolution Basis Carrier = `MB-A`（APPROVED）**

- 与 **provenance association 位于同一 nested structure**；
- **`when applicable`** —— **仅**在发生 semantic mapping ／ resolution 时要求；
- **必须**能**确定性关联**到具体 canonical input ／ observation；
- `mapping ／ resolution basis` **≠** `business rule`；**不得**新增 business field semantic。

**决定 10 —— Missing ／ Omission = 沿用 `C-2`（APPROVED）**

```
JSON null          = explicit missing ／ unavailable serialized value
property omission  = field not serialized
omission 语义      = canonical requiredness ＋ business applicability ＋ existing validation semantic
omission           ≠ 自动等于 valid absence
禁止               = 以 0 ／ false ／ "" ／ "UNKNOWN" 等 sentinel 代替 missing
```

**决定 11 —— Minimum Closure Criteria（APPROVED）**

```
F-1 ～ F-14 ＋ F-17 = MANDATORY MINIMUM CLOSURE CRITERIA
F-15 Human Inspectability ／ F-16 Implementation Simplicity
                    = POC DESIGN OBJECTIVES（必须评估；非独立 hard blocker）
```

**决定 12 —— Follow-up Authorization（AUTHORIZED，条件性）**

授权本 Task：正式登记本 Human Decision；将 approved carrier policy 写成 **authoritative current design**；
同步直接相关 current-state；执行 `F-1 ～ F-14 ＋ F-17` closure validation。

**只有当**：

```
Human decisions fully registered = PASS
且 F-1 ～ F-14 ＋ F-17 = ALL PASS
且 Blocking Contradiction = NONE
```

**才允许**：

```
Field Carrier Mapping   DESIGN PENDING → DESIGN RESOLVED
```

**若**任何 criterion 因**未授权**的 exact property naming ／ carrier detail 或其他 design gap **无法 PASS**：

- **不得**代替 Human 决定；
- **保持 `DESIGN PENDING`**；
- 输出**最小 Decision Gap** 后**停止**。

**Explicit Non-Authorization**

本 Human Decision **不授权**创建或定义：

```
real package directory
JSON sample ／ real manifest.json ／ dataset artifact
ZIP ／ archive
JSON Schema
parser ／ serializer ／ validator
Adapter ／ connector
runtime acceptance ／ rejection logic
unknown-property runtime policy
path normalization ／ traversal ／ symlink handling
hash ／ checksum ／ signature algorithm
byte-level canonicalization
version compatibility policy
source-system real table ／ column mapping
new canonical business entity ／ field ／ enum
new Validation Reason
```

**不得修改**：canonical entity ／ canonical field semantic ／ `BR-*` ／ Validation Taxonomy ／
Master Data Mapping ／ `Serialization Format` registered policy ／ `Physical Dataset Layout` registered policy。

**Decision Gap（`HD-1` ／ `HD-6` 触发）**

```
G-1  Manifest 的 exact property name ／ grouping name
     = NOT DETERMINABLE FROM APPROVED TERMINOLOGY
G-2  record-level reserved carrier-metadata namespace 的 exact property name
     = NOT DETERMINABLE FROM APPROVED TERMINOLOGY
```

依 **决定 1** ／ **决定 6**：**不得自行发明** ／ **不得自行选择名称** → **记录 Decision Gap 并停止 closure**。
详细判定与最小解除条件见 **§4.3.26**。

> **后续状态：** `G-1` ／ `G-2` 已由下方 **Supplementary Human Naming Decision（`G-1` ／ `G-2`）** 解除。
> 本块保留为 **Human Decision 时点**的 gap 记录；closure 复跑结果见 **§4.3.27**。

**Supplementary Human Naming Decision（`G-1` ／ `G-2`）—— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Decision Authority：** Human
**Purpose：** **仅**解除 **Decision Gap `G-1` ／ `G-2`**（naming only）。

**`G-1` —— Manifest naming（approved literal JSON names）**

```
top-level grouping
  package-level block                  = "package"
  dataset collection                   = "datasets"

package-scoped properties
  snapshot package identity            = "snapshot_package_id"
  contract version                     = "contract_version"
  export ／ package creation timestamp  = "created_at"
  environment                          = "environment"
  evidence classification              = "evidence_classification"
  package completeness                 = "completeness_state"

dataset-entry properties
  logical dataset role                 = "role"
  artifact reference                   = "artifact"
  record count                         = "record_count"
  dataset provenance ref               = "provenance_ref"
  integrity evidence                   = "integrity_evidence"
```

**Included logical datasets：** 该 logical dataset role 的 entry **出现在 `"datasets"` collection 内**
即为 **Manifest carrier 层 inclusion 的物理表示**。

- **不引入**独立的 `"included"` boolean；
- `not included` **仍**由既有 **Presence Semantics**（对应 artifact `NOT REQUIRED`）治理，
  **不**引入 MUST-NOT-EXIST 规则。

**`G-2` —— Reserved record metadata namespace**

```
reserved record carrier metadata namespace = "_meta"
```

`"_meta"` **保留**给已批准的 record-level technical ／ carrier metadata，
**不得**被视为 canonical business field。

**Boundaries（保持）**

本补充决定**仅**解决 **naming**，**不授权**：

```
new carrier family
JSON Schema ／ parser ／ serializer ／ validator implementation
integrity algorithm（hash ／ checksum ／ signature）policy
unknown-property runtime behavior
Adapter ／ source-system field mapping
canonical business semantic 的任何变更
```

**执行状态（Supplementary Human Naming Decision 时点）**

```
G-1                                = RESOLVED
G-2                                = RESOLVED
Field Carrier Mapping              = DESIGN PENDING   ← closure 需复跑
Closure                            = NOT YET RE-RUN
```

**执行状态（Field Carrier Mapping Human Decision 时点）**

```
Field Carrier Mapping              = DESIGN PENDING
Human Decision                     = RECORDED
Closure                            = BLOCKED（G-1 ／ G-2）
State Transition                   = NOT EXECUTED
Final Import Contract              = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

**本 Task 只登记 Human Decision 与 current design，并执行 closure validation。**
**未**实施 `Field Carrier Mapping`，**未**修改其 status，**未**推进下游两层。

---

**Final Import Contract Design Review（Review Finding）**

**Review Authority / Scope**

```
Review Type    = 独立 Design Review（只产出 Review Finding）
Review Object  = Final Import Contract（Snapshot / Import Contract 最后一个 DESIGN PENDING 层级）
Decision Power = NONE —— 本 Review 不作出任何 Human Decision
Write Scope    = 仅 docs/design/poc-design-v0.2.md
Status Change  = NONE
```

本 Review **不选择** acceptance model ／ integrity algorithm ／ compatibility policy，
**不新增** status enum 或 Validation Reason，**不发明**任何 JSON property name，
**不实现** importer ／ validator，**不登记** final policy。

> **Inherited Constraint 标注约定：** 若某行为已由既有 canonical constraint **唯一确定**，
> 本 Review 标记为 **`Inherited Constraint`**，**不**伪装成新的 Human Decision。
> 若仍有多个合理方案，则**只**呈现 trade-off 与 dependency。
> **`Inherited Constraint` 不得被实现为可选项。**

---

**1. Existing Canonical Constraints（Inherited —— 不得重新打开）**

| # | Constraint | Source |
| --- | --- | --- |
| `IC-1` | Package = **Flat Directory Package**；Manifest = package-root `manifest.json`；**one included logical dataset → one independent** root-level JSON artifact；nested directories = `NOT ALLOWED`（POC v0.2） | `§4.3.23` |
| `IC-2` | artifact reference **必须** relative to package root，且 logical resolved target **必须**在当前 package boundary 内；absolute path ／ external path ／ URI **不属于**合法 package layout | `§4.3.23` H |
| `IC-3` | Manifest **必须**显式建立 `role → artifact reference`；**不得**依赖 filename ／ ordering ／ discovery heuristic | `§4.3.23` E |
| `IC-4` | `included ＋ record_count = 0` → 对应 artifact `REQUIRED`，payload = **空 record array**；`not included` → 对应 artifact `NOT REQUIRED` | `§4.3.23` F ／ `§4.3.25` D ／ `§4.3.13` |
| `IC-5` | Manifest = **grouped nested** carrier，`"package"` ／ `"datasets"`；approved literal 集合已登记；**membership in `"datasets"` = inclusion 的物理表示**；**不引入**独立的 inclusion boolean | `§4.3.25` A ／ B ／ D |
| `IC-6` | business dataset top-level = **bare record array**；record = **JSON object**；canonical field identifier **直接**作 JSON property name | `§4.3.25` D ／ E ／ G |
| `IC-7` | reserved record carrier metadata namespace = `"_meta"`；`P-A` provenance structure 与 `MB-A` basis **位于其中**；**其内部 member 名称未获批准**（non-blocking residual） | `§4.3.25` F ／ H ／ I ／ `§4.3.27` D |
| `IC-8` | JSON ／ UTF-8 **without BOM**；**strict parse**；**禁止** duplicate object keys ／ comments ／ trailing comma ／ `NaN` ／ `Infinity`；object member order **不得**具有 business semantic | `§4.3.22` `C-1` ／ `C-9` |
| `IC-9` | JSON `null` = **explicit missing ／ unavailable**；**property omission** = field **not serialized**，语义由 requiredness ＋ applicability ＋ validation semantic 判断；**omission 不自动等于 valid absence** | `§4.3.22` `C-2` |
| `IC-10` | decimal = base-10 **string**；**禁止** round ／ quantize ／ truncate；date ／ timestamp ／ identifier 依 `C-1` ～ `C-10`；**禁止** silent trim ／ case conversion ／ Unicode normalization ／ numeric coercion | `§4.3.22` |
| `IC-11` | **`Deterministic Parsing ≠ Byte-for-byte Canonical JSON Encoding`**；byte-level canonicalization 若需要，属本层 | `§4.3.22` D |
| `IC-12` | 已 **`Accepted`** 的 Snapshot Package **必须视为 immutable**；**不得**原地修改 ／ 部分覆盖 ／ silently replace ／ 同 ID 不同内容；业务数据变化 **必须**形成新 identity | `§4.3.5` |
| `IC-13` | Import **必须**具有 **package-level atomic meaning**：`ACCEPTED` 或 `REJECTED` ／ `UNUSABLE`；**禁止** silent cross-snapshot mixing | `§4.3.6` ／ `§4.3.7` |
| `IC-14` | Structural failure **定义收紧**：**只有** Manifest **已声明** `included` 但对应 artifact absent ／ unreadable ／ identity inconsistent ／ integrity unverifiable 才属 Package Structural Inconsistency；**不得**推广为 `Any Dataset Absent → Structural Failure` | `§4.3.12` |
| `IC-15` | integrity evidence **required**；具体 **algorithm**（hash ／ checksum ／ signature）**未**决定，属本层 | `§4.3.15` |
| `IC-16` | **Fail-closed**：identity ／ integrity ／ required structural metadata **无法可靠确定**时，**不得**猜测 ／ 自动修复 ／ 用旧 package 补齐 ／ 重读 Production ／ 让 LLM 拼接 | `§4.3.18` |
| `IC-17` | 三层语义 **不得互相提升或降级**：`Package Structural Failure` ≠ `Capability Evidence Unavailable` ≠ `Business DATA_INCOMPLETE` | `§4.4.3` ／ `§4.3.12` |
| `IC-18` | 四层 validation model；**Layer 1 = Package Structural Validation 继承 `§4.3`**；**Package 未 `Accepted` → 不得创建依赖它的正常 Analysis Run** | `§4.4.2` |
| `IC-19` | conceptual import lifecycle：`RECEIVED` → `STRUCTURAL CHECK` → `ACCEPTED` ／ `REJECTED` ／ `UNUSABLE` → Accepted Package may be referenced by Analysis Run；**本层不要求正式 enum** | `§4.3.20` |
| `IC-20` | Validation Issue Taxonomy = **8 categories ＋ 12 reasons**（`REGISTERED`）；**Package Structural Failure 已有 canonical root-issue 表示**：Category **`PACKAGE_STRUCTURE`** → Reason **`STRUCTURAL_INCONSISTENCY`**，且 `§4.4.80` 已把 manifest unavailable ／ package identity inconsistent ／ declared artifact absent ／ artifact unreadable ／ integrity evidence unverifiable 列入该 category | `§4.4.79` ～ `§4.4.83` ／ `§4.4.101` |
| `IC-21` | **`REJECTED` ／ `UNUSABLE` 是 Package consequence ／ disposition，不是 Issue Reason**；Validation Issue ≠ Package Status ≠ Capability Status ≠ Business Status | `§4.4.78` ／ `§4.4.82` |
| `IC-22` | **integrity verification 为 mandatory，且不可验证即 fail closed**：`integrity evidence is required`（`§4.3.15`）＋ declared artifact 的 `integrity unverifiable` 属 Structural Inconsistency（`§4.3.12`）＋ identity ／ integrity 无法可靠确定时 fail closed（`§4.3.18`）⇒ **advisory-but-still-accept 与既有约束不兼容** | `§4.3.15` ＋ `§4.3.12` ＋ `§4.3.18` |
| `IC-23` | **已关闭层**：Package Envelope ／ Atomicity ／ Immutability ／ Analysis Run Linkage ／ Serialization Format ／ Physical Dataset Layout ／ **Field Carrier Mapping** ／ Data Validation = **`DESIGN RESOLVED`** | `§4.3.21` ／ `§4.3.24` ／ `§4.3.27` ／ `§4.4.101` |

---

**2. Exact Review Scope**

**In scope（仅以下问题）：**

1. Import acceptance boundary ／ lifecycle 的 **contract 细节**（`IC-19` 之上）
2. validation ／ acceptance **partial order 与 prerequisite**
3. Manifest ↔ artifact consistency 的**未继承部分**与 disposition 表述
4. unknown ／ undeclared content policy
5. path resolution ／ package boundary enforcement 的 **contract semantics**
6. integrity contract 的**未继承部分**（algorithm strategy ／ evidence representation ／ digest 目标 ／ Manifest 自身）
7. `contract_version` compatibility model
8. partial package ／ failure isolation ／ atomicity 边界
9. `completeness_state` 与 finality ／ immutability 的 acceptance 角色（**含 acceptance-time 一致输入视图**，`IS-24`）
10. deterministic failure reporting 的 **shape**（reason taxonomy 已 inherited）
11. **`REJECTED` ／ `UNUSABLE` 的 contract-level usage**
12. Final Import Contract 的 minimum closure criteria 候选

**Out of scope（属其他层或实现）：**

- parser ／ serializer ／ validator **实现**、JSON Schema、sample package
- hash ／ checksum ／ signature **实现**与 signing infrastructure
- filesystem security implementation ／ transaction ／ locking ／ atomic filesystem move
- Adapter ／ connector ／ source extraction ／ source → canonical mapping
- canonical entity ／ field ／ enum、`BR-*`、Layer 2 ～ Layer 4 validation semantics 的重定义
- 新 status enum；**新增 Validation Reason**（**除非**能指出一个具体 root condition 无法落入既有
  `8 categories ／ 12 reasons` 并给出不可表达的证据 —— 本 Review **未发现**此类条件）

---

**3. Critical Scenarios**

`性质` 列标注该情景的归属：**`IC`** = behavioural outcome 已被 inherited；
**`IC + open`** = outcome inherited、**表述 ／ 报告细节**仍开放；**`open`** = 真正待 Human Decide。

| # | Scenario | 既有约束要求的行为 | 性质 |
| --- | --- | --- | --- |
| `IS-1` | `manifest.json` missing ／ unreadable | `REJECTED` ／ `UNUSABLE`（`IC-14` 明示 manifest unavailable） | **`IC`** |
| `IS-2` | `manifest.json` malformed ／ strict-parse 失败（duplicate key 等） | 违反 `IC-8` ⇒ required manifest structure **无法可靠确定** ⇒ fail closed（`IC-16`） | **`IC + open`**（structural 归属 inherited；disposition wording ／ reporting detail 开放） |
| `IS-3` | **duplicate logical dataset role** | 破坏 `IC-3` 唯一性 ＋ `IC-1` 粒度 | **`IC`** |
| `IS-4` | **多个 role 引用同一 artifact** | 违反 `IC-1`（`one included logical dataset → one **independent** artifact`）：同一 artifact 服务多个 logical dataset 即非 independent | **`IC`** |
| `IS-5` | Manifest 声明 `included` 但 artifact **missing** | `IC-14` 明示属 structural | **`IC`** |
| `IS-6` | artifact **unreadable** | `IC-14` 明示属 structural | **`IC`** |
| `IS-7` | `record_count` 与 artifact 实际记录数 **不一致** | `"record_count"` 是 Manifest 的 **authoritative presence metadata**（`IC-4` ／ `IC-5`）；与 artifact 内容不一致 ⇒ required structural metadata 不可靠确定 ⇒ fail closed（`IC-16`） | **`IC + open`**（disposition wording ／ reporting detail 开放） |
| `IS-8` | 目录中存在**未被 Manifest include ／ reference** 的额外 root-level JSON artifact | `IC-4` 明示 `not included` **不**要求 artifact，且既有 Design **明确未**引入 MUST-NOT-EXIST 规则 | **`open`** |
| `IS-9` | `included` role 的 artifact 与另一 entry 的 artifact **相同** | 同 `IS-4` | **`IC`** |
| `IS-10` | `included ＋ record_count = 0` 但 artifact 内容**非空数组** | `IC-4` ／ `IC-6`：empty 的 payload **必须**是空 record array | **`IC + open`**（disposition wording 开放） |
| `IS-11` | package identity ／ contract metadata **inconsistent** | `IC-14` 明示 package identity inconsistent 属 structural ⇒ fail closed（`IC-16`） | **`IC`** |
| `IS-12` | **unknown Manifest property** | 既有 Design **未决定** | **`open`** |
| `IS-13` | **unknown dataset-entry property** | 既有 Design **未决定** | **`open`** |
| `IS-14` | **unknown canonical record property** | `IC-6`：canonical field identifier 即 property name；`IC-9` ／ `IC-10` 禁止 silent fix-up —— 但「未知 property 是否 reject」**未**决定 | **`open`** |
| `IS-15` | **unknown `"_meta"` member** | `IC-7`：`"_meta"` 为 reserved namespace；**内部 member 名称未批准** ⇒ **known member set 尚未存在**，无法在缺该集合时判定「unknown」 | **`open`＋ prerequisite**（见 `DEP-8`） |
| `IS-16` | artifact reference 含 `.` ／ `..` ／ 平台分隔符 ／ 指向 boundary 之外 | `IC-2`：resolved target **必须**在 boundary 内 —— boundary 结论 inherited；**normalization 是否存在**未决定 | **`IC + open`** |
| `IS-17a` | reference 的 **target-equivalence 识别规则**（字面量 ／ normalization ／ separator ／ case ／ symlink ／ alias）**尚未登记** | `IC-2`（boundary 不可让步）；**识别规则本身**既有 Design 未决定 | **`open`** |
| `IS-17b` | 两个 reference 在**已选定且允许的**解析规则下**已确认指向同一 artifact**，字面量不同 | **`IC`**：`IC-1` 要求每个 included logical dataset 对应 **independent** artifact；**target identity 一旦确定为同一 artifact，即不构成第二个 independent artifact** ⇒ 适用与 `IS-4` ／ `IS-9` 相同的违反结论。normalization ／ case ／ symlink ／ alias policy 决定的是**如何建立 target identity**，**不得**在该 identity 已确定相同时再用作绕过 `IC-1` 的自由选项 | **`IC`** |
| `IS-18` | `"integrity_evidence"` **missing ／ malformed ／ 无法验证** | **`IC-22`**：integrity 无法可靠确定 ⇒ structural ＋ fail closed | **`IC`** |
| `IS-19` | `"contract_version"` 为**不受支持**的版本 | 既有 Design **未决定** compatibility model；**不得** silent interpretation | **`open`** |
| `IS-20` | `"completeness_state"` 表示 **incomplete ／ in-progress** 的 package 被提交 | `IC-12` ／ `§4.3.12` A ／ B | **`open`** |
| `IS-21` | Package 同时存在**多个** structural defect | 既有 Design **未决定** reporting 形态（reason taxonomy 已 inherited，`IC-20`） | **`open`**（reporting shape only） |
| `IS-22` | Accepted 后 artifact bytes 发生变化 | `IC-12`：accepted = immutable，同 ID 不得不同内容 ⇒ **该 identity 不再可信 ⇒ fail closed**；**如何检测**未决定 | **`IC + open`**（detection ／ re-verification ／ binding 开放） |
| `IS-23` | 同一 Package 被描述为 `REJECTED` 或 `UNUSABLE` | `IC-21`：二者是 **Package disposition**，不是 reason；**但二者之间的 contract-level 差异在 repository 中未被定义** | **`open`**（见 `RIF-1` ／ Decision 3） |
| `IS-24` | **acceptance 期间「验证对象 ≠ 接受对象」**：某次验证所依据的 artifact ／ Manifest 内容视图，与最终被接受、随后供 Analysis Run 使用的 package 内容视图**不属同一稳定输入版本**（或在 acceptance 过程中发生变更 ／ 前后读取结果不一致） | **`IC`**：`IC-12` ／ `IC-13`（源 `§4.3.5` ／ `§4.3.6`）的 immutable ／ package-level atomic meaning 要求一个 package 内容视图成立；**「分别成功」不等于「同一次 acceptance 内一致」** ⇒ 无法建立一致性时**不可判定为通过**（`IC-16`） | **`IC + open`**（**inherited**：必须绑定同一稳定内容视图、无法建立即 fail closed；**open**：contract-level **guarantee ／ detection boundary** 与报告表述 —— **Decision path = `Decision 10A`**；锁 ／ 事务 ／ 原子移动 ／ 存储技术属 implementation） |
| `IS-25` | 已关闭层的 residual（例如 `IC-7` 的 `"_meta"` 内部 member 名称未批准）被**直接**视为对本层某候选分支 non-blocking | 已关闭层的 non-blocking 结论**只**在其自身 closure 范围内成立（`§4.3.27` D）；**是否**对本层某候选分支 non-blocking **必须**在本层按其自身 contract 依赖**重新评估** | **`open`＋ prerequisite**（见 `DEP-10`） |

---

**4. Candidate Contract Models / Options**

> 以下仅为**候选模型**，**不代表**本 Review 的选择；亦**不**引入任何未批准的 property name。
> **已被 inherited constraints 排除的模型不再列为可选方案**，而显式标注 `NOT COMPATIBLE`。

**A. Acceptance Model（Q1 ／ Q8）**

- `AM-1` —— **Package-level single gate（atomic accept / reject）**
- `AM-2` —— Package gate ＋ **dataset-level quarantine**
- `AM-3` —— **staged ／ partial acceptance**

**`Inherited Constraint`：** `IC-13`（源 `§4.3.6` ／ `§4.3.7`）要求 import 具有 **package-level atomic meaning**。
因此 `AM-2` ／ `AM-3` **与 `IC-13` 不兼容** → **`NOT COMPATIBLE`**，**不属开放选项**。
**真正开放的问题**是「**哪些条件触发 package-level rejection**」（已由 `IS-*` 逐项标注）
与「是否需要**超出既有术语**的 sub-state」—— 后者受 `IC-19`（不要求正式 enum）约束。

**B. Unknown ／ Undeclared Content Policy（Q4）**

| 载体 | 状态 | 候选策略 |
| --- | --- | --- |
| unknown **Manifest** property（`IS-12`） | **`open`** | `UX-A` reject ／ `UX-B` ignore ／ `UX-C` preserve-but-not-interpret |
| unknown **dataset-entry** property（`IS-13`） | **`open`** | 同上 |
| unknown **canonical record** property（`IS-14`） | **`open`** | 同上（须与 `IC-6` canonical field boundary 一致） |
| unknown **`"_meta"` member**（`IS-15`） | **`open`＋ prerequisite** | 同上，**但**在 known member set 存在前**无法判定**（`DEP-8`） |
| **unreferenced root-level artifact**（`IS-8`） | **`open`** | 同上 |

**共同 trade-off 维度：**

```
POC simplicity
forward compatibility
typo ／ silent data loss risk
与 canonical field ／ reserved namespace boundary 的一致性
```

**C. Path Resolution ／ Boundary Enforcement（Q5）**

- `PN-1` —— **字面量严格匹配**（**不**做 normalization）
- `PN-2` —— **确定性 normalization 后**再做 boundary check（`.` ／ `..` ／ separator）
- `PN-3` —— `PN-2` ＋ **平台相关** case ／ symlink ／ junction 处理

**`Inherited Constraint`（不可让步）：** resolved target **必须**在当前 package boundary 内；absolute ／
external ／ URI **不属于**合法 layout（`IC-2`）。
**`Inherited Constraint`（不可让步，与 normalization 选择无关）：** **不同 included roles 的 reference 一旦按已选定且允许的
解析规则确认解析到同一 artifact**，即**不再**构成两个 independent artifact（`IC-1`，同 `IS-4` ／ `IS-9`）。
`PN-1` ／ `PN-2` ／ `PN-3` **共享同一适用前提**：**必须**同时定义 **alias ／ link（symlink ／ junction）的拒绝或安全解析边界**；
**不得**以「选择低成本项」为由豁免 package boundary（`IC-2`）与 artifact independence（`IC-1`）。
`PN-1` 只表示**不做**普通化处理，**不表示**可以跳过 boundary ／ alias 约束。
**开放：** normalization **是否存在**、separator ／ case ／ symlink ／ junction ／ alias 语义、
以及 **target-equivalence 识别规则**本身（`IS-17a`）。

**D. Integrity Contract（Q6）**

**D.1 mandatory 性 —— `Inherited Constraint`（非选项）**

```
Integrity verification = MANDATORY
integrity unverifiable  ⇒ Package Structural Inconsistency ⇒ fail closed
```

依据 **`IC-22`**（`§4.3.15` ＋ `§4.3.12` ＋ `§4.3.18`）。
**`IG-3`（advisory-but-still-accept）与 `IC-22` 不兼容 → `NOT COMPATIBLE`**，**不是**开放选项。

**D.2 algorithm strategy（`open` —— 本 Review 不选算法）**

**算法族**（仅列类别，**不**在任何层选定具体算法）：cryptographic hash ／ non-cryptographic checksum ／
digital signature ／ 混合（例如 hash ＋ 可选 signature）。

> **algorithm family 的可行性分级（`open` 选择，但不得隐含前提）：**
> **hash ／ checksum 分支**只把 **content integrity** 作为目标，其 verification input 为
> （algorithm ＋ 被覆盖内容 ＋ evidence value）—— 本层可达 deterministic。
> **digital signature ／ 混合分支为条件性可行（conditionally viable）**：除 algorithm 与 covered content 之外，
> verification **还依赖 verification key**。若把 signature 用来建立 **Manifest ／ 来源可信性（authenticity）**，
> **必须同时**确定 ① **verification key 的信任来源与选择边界**（由谁提供、如何绑定到 contract、
> 缺失或与 evidence 不一致时如何处理），② 与 **evidence representation**（`IG-rep-*`）及
> **Manifest 自身 integrity**（`IG-self-*` ／ `DEP-9`）的依赖，③ 达到 deterministic verification 的**完成条件**。
> **不得**接受 package 自带但**未经任何信任约束**的 key，却把「数学验证成功」当作来源可信。
> 若该分支需要新的 security ／ key-management design，**必须**按治理标记为
> **requires separate Human-authorized design change**，并**明确**其是否阻塞所选分支的 closure（`DEP-11`）。
> **不变式：** **content integrity 目标 ≠ identity ／ authenticity 目标**；
> hash ／ checksum 的「内容完整性」**不得**被当作来源认证（`IC-15` 的 integrity evidence 不等于既有
> `PROVENANCE` 层语义）。
> **本 Review 不要求**选择 signature、不要求引入 PKI、不要求设计 signing infrastructure、不要求获取任何 secrets。

**deterministic verification 的候选 shape（`open`）：**

- `IG-alg-1` —— **fixed algorithm**（本层固定单一算法）
- `IG-alg-2` —— **explicit supported algorithm set**（本层登记受支持算法集合；集合外 ⇒ 不可接受）
- `IG-alg-3` —— **algorithm-tagged evidence**（evidence 自携 algorithm identifier；本层定义 **identifier 语义**
  与「未知 algorithm identifier」的处置边界）

**要求（仍不选具体算法）：** 无论采用哪一 shape，本层**必须**达到
**deterministic verification contract** —— 即「给定 evidence 与 artifact，
verification 结果**不依赖 implementation 选择**」。
`IG-alg-3` 的「未知 algorithm identifier」属 unknown-content 语义，**不得** silent accept。

**D.3 evidence representation ／ ownership（`open`）**

- `IG-rep-A` —— evidence 的 contract-level 表示与 **algorithm identifier 语义**归属**由本层定义**
- `IG-rep-B` —— 本层**只**要求「可验证」，表示细节留给实现

> **closure 边界：** `IG-rep-B` **可能不足以满足本层 closure** —— 若 algorithm identifier 语义与 evidence
> 表示完全留给实现，则**两个 conforming importer 可以用不同算法 ／ 不同 interpretation**，
> verification contract 仍**未真正定义**（`§4.3.15` 已把 integrity algorithm 留给本层）。
> 本 Review **不**无条件称其「均兼容」；若 Human 选择 `IG-rep-B`，
> **必须**同时说明**怎样达到 deterministic verification**（见 **`I-18`**）。

**D.4 digest 目标（`open`）**

- `IG-raw` —— **raw artifact bytes**
- `IG-canon` —— **canonicalized bytes**（依赖 `IC-11` 的 byte-level canonicalization；**触发**该设计）

**D.5 Manifest 自身 integrity（`open` —— **cross-layer dependency**，见 `RIF-X5`）**

| 候选 | 含义 | 是否需要触碰其他层 |
| --- | --- | --- |
| `IG-self-A` | Manifest 自身**单独**处理（detached evidence ／ sidecar） | **需要** —— `IC-5` ／ `IC-7` 未提供 Manifest-self-integrity carrier；新增 carrier ／ sidecar 即触碰 **Field Carrier Mapping ／ Physical Dataset Layout**，属 **requires separate Human-authorized design change** |
| `IG-self-B` | 与 artifact **同一机制**处理 | **需要** —— 同样缺 carrier；且需定义**自引用排除规则**（hash 是否覆盖承载 evidence 的字段）→ 仍触发 carrier ／ canonicalization 问题 |
| `IG-self-C` | 本层**只**要求「Manifest 自身可信性必须可建立」，**不**规定 mechanism ／ carrier | **不需要**新增 carrier；但**必须**说明**可审计的信任前提 ／ 输入边界**，且**不得**由 Agent 自行新增 literal（见下方前提条件） |

> **`IG-self-C` 的前提条件与 closure 边界（不得省略 —— 目标陈述 ≠ 可判定前提）：**
> 若采纳 `IG-self-C`，本层**必须**同时登记：
>
> 1. **可审计的信任前提 ／ 输入边界** —— 即「Manifest 自身可信性可建立」**依据什么输入**、
>    **由谁提供**、以及**哪些输入缺失即视为不可建立**（否则该表述只是目标陈述，**不可判定**）；
> 2. **后续动作的归类与完成状态** —— 规定 mechanism ／ carrier（例如 Manifest-self carrier ／ sidecar ／
>    自引用排除规则）的**后续动作**必须具名，并明确归入
>    **(a)** **不影响 acceptance semantics 的 implementation detail residual**
>    ⇒ 标为 **non-blocking implementation residual（outside the FIC acceptance criterion）**，
>    **既不是 `CL-2`，也不作为本层 closure 依据**（依 `§7.1` 强制规则 2），**或**
>    **(b)** 影响 acceptance 判定的 contract prerequisite（**未完成即 `CL-3`**，见 `§7.1`）；
>    **归类后，其「完成状态」必须已满足 —— 仅登记 gate 不足。**
> 3. **对选中分支的重新评估** —— 已关闭层（`§4.3.27` D）记录的 FCM non-blocking residual
>    **不得**被**直接**沿用来证明本层候选分支 non-blocking（`DEP-10` ／ `IS-25`）；
> 4. **closure claim 范围** —— `CL-2` **只**在**属 `§7.1` 类别 ①**（contract 已闭合：
>    可信性的建立依据不依赖任何**未完成设计**，且同一输入下 conforming importers 结果唯一）时可用；
>    **若仍依赖未定义 trust mechanism ／ 新 carrier ／ literal 等未完成设计，则 `CL-3`。**
>    **不得**无条件声称 `IG-self-C` 已「低成本解决」Manifest 自身可信性。
>
> **`IG-self-A` ／ `IG-self-B`（依 `§7.1` 类别 ②）：** 二者都需要**新 carrier ／ sidecar ／
> layout ／ naming contract**；在该 cross-layer design change **实际完成前**，
> 受其影响的 `I-10` **一律 `CL-3`** —— 仅「已标记为 requires separate design change」
> 或「已登记 completion gate」**均不构成 PASS**。

**E. Contract Version Compatibility（Q7）**

- `VC-1` —— **exact-match only**
- `VC-2` —— **explicit supported-version set**
- `VC-3` —— **major ／ minor** compatibility model

**`Inherited Constraint`：** **不得**对不受支持版本做 silent interpretation。
**依赖：** 与 unknown-content policy（`UX-*`）**互为依赖**（`DEP-1`）。

**F. Failure Reporting（Q10）**

**F.1 root-issue taxonomy —— `Inherited Constraint`（非选项）**

```
Category = PACKAGE_STRUCTURE
Reason   = STRUCTURAL_INCONSISTENCY
```

依据 **`IC-20`**（`§4.4.79` ～ `§4.4.83`）：`§4.4.80` 已把 manifest unavailable ／ package identity inconsistent ／
declared artifact absent ／ artifact unreadable ／ integrity evidence unverifiable 列入 `PACKAGE_STRUCTURE`；
`§4.4.83` 给出 canonical mapping 样例；`§4.4.79` 已定义 auditable issue 的 conceptual dimensions。
**`REJECTED` ／ `UNUSABLE` 不是 Issue Reason**（`IC-21` ／ `§4.4.82`），而是 **Package disposition**。
**本 Review 未发现**任何 Final Import root condition 无法落入既有 `8 categories ／ 12 reasons`
→ **故不存在 taxonomy gap，不提出新增 Validation Reason**。

**F.2 reporting shape（`open`）**

- `FR-1` —— **fail-fast**（遇首个 defect 即终止）
- `FR-2` —— **collect-all** —— **限定语义**：收集 **在 prerequisite 边界之内可确定性发现 ／ 可达的 defect**，
  **不是**承诺「整个 package 的全部 defect」
- `FR-3` —— 同上 ＋ **deterministic ordering**（**仅**对本次**能够可靠收集**到的 issue set 生效）
- 另需裁定：auditable 最小内容（在 `§4.4.79` dimensions 之内）

**prerequisite boundary（与 `RIF-2` 一致）：** 若某 prerequisite 失败
（例：`manifest.json` 无法 strict-parse ⇒ declared artifacts **不可知**），
则其 downstream check **not evaluable** —— 这**不是**「漏报」，而是**在该前提下不可判定**。
reporting **必须**区分 `not evaluable due to prerequisite` 与 `evaluated and passed`。

**G. Completeness ／ Finality（Q9）**

- `CF-1` —— `"completeness_state"` 仅作 **Manifest-declared metadata**，**不**直接参与 acceptance gate
- `CF-2` —— 参与 acceptance gate（incomplete 状态不可 accepted）
- `CF-3` —— acceptance **要求** final 状态 ＋ 与 `IC-12` immutability 绑定

**H. Accepted-then-mutation（Q9）**

**`Inherited Constraint`：** accepted package immutable；同 ID 不得不同内容；检测到 post-accept mutation
⇒ **该 identity 不再可信 ⇒ fail closed**（`IC-12` ＋ `IC-16`）。
**开放（仅限 mechanism）：**

- `MG-1` —— **不规定 proactive detection mechanism**（**不得**解释为 mutation 后仍可继续作为同一 Accepted package 使用）
- `MG-2` —— contract 要求 **re-verification**（bytes 变化即不可信）
- `MG-3` —— contract 要求 **identity ／ content binding**

**I. `REJECTED` vs `UNUSABLE` 的 contract-level usage（Q1 —— **`open`**）**

**repository 核查结论：** 既有 Design **只**把二者并列表述为 Package disposition
（`§4.3.6` ／ `§4.3.12` ／ `§4.3.20` ／ `§4.4.78` ／ `§4.4.82`），**从未定义二者差异**。
因此这是**真实开放问题**（`IC-21` 只确定「它们是 disposition 不是 reason」，**未**区分二者）：

- `RD-A` —— 二者是**同一** negative disposition 的两种写法（**同义**）
- `RD-B` —— `REJECTED` = import-time 结构拒绝；`UNUSABLE` = **此前已 accepted** 的 package 之后变为不可用
- `RD-C` —— 其他有 evidence 支持的区分（须先给出依据）

**不得新增 enum**；本项**只**决定**现有两个术语**的 contract-level usage。

---

**5. Option Comparison**

`—` = 不适用。判定针对**既有 canonical 约束兼容性**与 **POC implementation cost**，**不代表**本 Review 的选择。

| Model | 与既有约束兼容 | POC cost | 备注 |
| --- | --- | --- | --- |
| `AM-1` | **`Inherited Constraint`** | 最低 | `IC-13` 已要求 package-level atomic |
| `AM-2` ／ `AM-3` | **`NOT COMPATIBLE`（`IC-13`）** | — | 已被既有约束排除，非开放选项 |
| `IG-3` advisory | **`NOT COMPATIBLE`（`IC-22`）** | — | 与 mandatory ＋ fail-closed 冲突 |
| D.2 algorithm strategy | 兼容 | 取决于选择 | 本 Review **不选**算法 |
| `IG-alg-1` ／ `IG-alg-2` ／ `IG-alg-3` | 均兼容（`IC-22` 的 mandatory 性不受影响） | 低 ／ 低 ／ 中 | 三者**均可达** deterministic verification；差异在演进成本与未知 algorithm 的处置 |
| `IG-rep-A` ／ `IG-rep-B` | `IG-rep-A` 兼容；**`IG-rep-B` 可能不足以满足 closure** | 中 ／ 低 | `IG-rep-A` 使 `IC-15` 更可判定；`IG-rep-B` 需补 deterministic verification 说明 |
| `IG-raw` | 兼容（不触发 `IC-11` 的 canonicalization） | 低 | 与 `IC-11` 的区分得以保持 |
| `IG-canon` | 兼容（须定义 byte-level canonicalization） | 高 | **触发** `IC-11` 的 byte-level 设计 |
| `IG-self-A` ／ `IG-self-B` | **需 cross-layer 变更** | 高 | **requires separate Human-authorized design change**（触 FCM ／ Layout） |
| `IG-self-C` | 兼容 | 低 | 不新增 carrier；不规定 mechanism |
| `UX-A` reject | 兼容 | 低 | forward compatibility 最差 |
| `UX-B` ignore | 兼容 | 最低 | **silent semantic loss** 风险（与 `IC-8` strict parse **无关**） |
| `UX-C` preserve-but-not-interpret | 兼容 | 中高 | forward compatible；不解释 |
| `PN-1` ／ `PN-2` ／ `PN-3` | 均兼容（`IC-2` 为不可让步项） | 低 ／ 中 ／ 中高 | 差异在可预期性 |
| `VC-1` ／ `VC-2` ／ `VC-3` | 均兼容 | 低 ／ 低 ／ 中 | 差异在演进成本 |
| `FR-1` ／ `FR-2` ／ `FR-3` | 均兼容（reason taxonomy 已 inherited） | 低 ／ 中 ／ 中 | shape only；`FR-2` ／ `FR-3` **受 prerequisite 边界限定** |
| `CF-1` ／ `CF-2` ／ `CF-3` | 均兼容 | 低 ／ 低 ／ 中 | `CF-2` ／ `CF-3` 改变 acceptance 判定 |
| `MG-1` ／ `MG-2` ／ `MG-3` | 均兼容（immutability 已 inherited） | 低 ／ 中 ／ 中高 | 差异在 detection 强度 |
| `RD-A` ／ `RD-B` ／ `RD-C` | 均兼容（`IC-21` 只定 disposition 属性） | 低 ／ 低 ／ 中 | 仅涉 terminology usage |

---

**6. Cross-Decision Dependencies**

| # | Dependency | 说明 |
| --- | --- | --- |
| `DEP-1` | **unknown-content policy ↔ version compatibility** | **正确形式：** 先按**受支持版本 ／ 兼容规则**确定所适用的 contract 与**该 contract 的 known member set**，**再**对该 version 的 payload 应用该 contract 的 unknown policy。**version-token 匹配 ≠ field policy**：版本是否**被支持**，与 payload 是否符合**所选版本**，是两件事。`VC-*` 与 `UX-*` **必须**组合裁定，但**不得**写成「reject unknown ⇒ 任何新增字段必然版本不兼容」 |
| `DEP-2` | **integrity digest 目标 ↔ byte-level canonicalization（`IC-11`）** | `IG-canon` **触发** byte-level canonicalization 设计；`IG-raw` **不**触发 |
| `DEP-3` | **integrity mandatory 性 —— 已 inherited，不再依赖其他选择** | mandatory ＋ unverifiable → structural ＋ fail closed 由 `IC-22` 唯一确定；**剩余依赖**为 `IG-rep-*`（evidence 表示）↔ `IC-7` 的 carrier ownership 边界 |
| `DEP-4` | **`completeness_state` 角色 ↔ acceptance gate** | `CF-2` ／ `CF-3` 会**新增** acceptance 拒绝条件 ⇒ 须与 `IS-*` 的 structural 集合一致 |
| `DEP-5` | **path ／ alias 解析 ↔ target identity ＋ uniqueness ＋ boundary 判定** | target-equivalence 识别规则（`IS-17a`）决定**如何建立 target identity**；该 identity 一旦确定相同（`IS-17b`），**同时**影响 ① artifact presence、② artifact **uniqueness ／ independence**（`IC-1`）、③ boundary 判定（`IC-2`）—— **不**只影响 presence |
| `DEP-6` | **failure reporting ↔ `IC-20`（taxonomy）** | reason taxonomy 已 inherited（`PACKAGE_STRUCTURE` ／ `STRUCTURAL_INCONSISTENCY`）；**报告 shape** 开放，但**不得**引入新的 root reason |
| `DEP-7` | **`AM-1`（`IC`）↔ 全部 rejection 条件** | 任何 rejection 条件都在 package-level atomic 语义下生效，**不得**被实现为 dataset-level partial outcome |
| `DEP-8` | **unknown `"_meta"` member policy ↔ known member set 的存在性** | 在 `IC-7` 的 P-A ／ MB-A 内部 member literal 获批**之前**，**known member set 不存在**，故 unknown-`"_meta"` policy **无法判定**（`IS-15`）。须先裁定：**是否**把 member set 升为**独立 naming decision**，或**允许**先登记 abstract policy（implementation 前再定 literal）。**若**选择后者，**必须**证明其属 `§7.1` **类别 ①**：authoritative parameter（member set）的**来源**、**版本 ／ 绑定关系**、**缺失时的确定性行为**（fail closed ／ not evaluable）、**同一输入下结果唯一**、**可声称 closure 范围**全部由 contract 完整规定 ⇒ 方可 `CL-2`；**否则（类别 ② 未完成 design prerequisite）一律 `CL-3`，仅登记 completion gate 不构成 PASS** |
| `DEP-9` | **Manifest 自身 integrity ↔ Field Carrier Mapping ／ Physical Dataset Layout** | `IG-self-A` ／ `IG-self-B` 需要新 carrier ／ sidecar（`IC-5` ／ `IC-7` 未提供）⇒ **cross-layer**，须 **separate Human-authorized design change**；**该 design change 实际完成前，受影响的 `I-10` 为 `CL-3`**（`§7.1` 类别 ②）。`IG-self-C` **不**新增 carrier，但**仍受** `D.5` 前提条件与 `DEP-10` 约束 |
| `DEP-10` | **已关闭层 residual ↔ 本层候选分支（cross-layer 再评估）** | `IC-7` 的 `"_meta"` 内部 member 名称未批准，在 **FCM closure（`§4.3.27` D）** 范围内**不构成** blocking gap。该结论**只**对 FCM closure 成立，**不自动**证明其对本层任何候选分支 non-blocking：若所选分支要求 known member set 作为**接受判定**的 prerequisite（例如 unknown-`"_meta"` policy ／ 含 `"_meta"` 的 digest 覆盖范围），则**必须**在本层**重新评估**，登记缺失时的确定性行为，并按 `§7.1` 判定 `CL-2` ／ `CL-3`（`IS-15` ／ `IS-25`） |
| `DEP-11` | **signature 分支 ↔ verification key 信任源 ＋ evidence representation ＋ Manifest self-integrity** | 若所选 integrity 分支包含 digital signature（或以 signature 主张**来源可信性**），其 verification input **不**止于 algorithm ＋ covered content：**必须**确定 verification key 的**信任来源 ／ 配置边界 ／ 选择规则**、key 与 contract 的**绑定**、以及 key 不可用或不一致时的处置。该分支与 `IG-rep-*`（evidence representation）及 `DEP-9`（Manifest self-integrity）**耦合**；任何新的 security ／ key-management 设计**必须**标记为 **requires separate Human-authorized design change**。**若 deterministic verification 仍依赖该未完成的 security ／ trust contract，则 `I-18` 的相关分支为 `CL-3`** —— 相关 contract 的 semantics **必须已完整**（`§7.1` 类别 ①）才可 `CL-2`；**不得**以「已登记 future gate」判 PASS |

---

**7. Review Findings**

**`RIF-1`（Q1 Acceptance Boundary ／ Lifecycle ／ `REJECTED` vs `UNUSABLE`）**
`IC-13` ／ `IC-19` 已确定 **package-level atomic outcome** 与 lifecycle 术语 —— **`Inherited Constraint`**。
**但 `REJECTED` 与 `UNUSABLE` 的 contract-level 差异在 repository 中未被定义**
（`IC-21` 只确定「二者是 disposition，不是 reason」）→ **必须**由 Human Decision 裁定其 usage（`I-2`），
**不得**新增 enum，**不得**由 Agent 推定二者同义或不同义。

**`RIF-2`（Q2 Validation ／ Acceptance Ordering —— **partial order**）**
既有约束**未**规定线性顺序；本 Review **只**固定**确实 inherited** 的 prerequisite 边，
其余为**依赖选择**的边：

```
【inherited 前置边】
  manifest 可读（IS-1）
    → manifest strict-parse 成功（IC-8）
      → manifest 结构 ／ identity 可确定（IC-14 ／ IC-16）
        → artifact reference 可解析且 resolved target 在 boundary 内（IC-2 ／ IC-3）
          → artifact 可读
            → artifact JSON strict-parse 成功（IC-8）
              → record 结构 ／ canonical field 可判定（IC-6）

【依赖 Decision 6 的边（不得提前固定）】
  integrity verification 的位置取决于 digest 目标：
    · digest = raw artifact bytes（IG-raw） ⇒ 可在 JSON parse ／ record_count 检查**之前**完成
    · digest = canonicalized bytes（IG-canon） ⇒ 需要 parse ／ canonicalization 作为 prerequisite

【与 reporting shape 相关，不决定语义】
  fail-fast ／ collect-all ／ parallel execution ∈ FR-*
```

**本 Review 判定：** 只有上表**第一组**边是 inherited；**`record_count` → integrity 的顺序不得提前固定**。
**不写 parser algorithm。**

**新增 inherited obligation（`IS-24` ／ `RIF-13`）：** 上述 partial order **不得**被解释为
「各项检查各自成功即可接受」。**必须**额外要求：**同一次 acceptance 所依据的 Manifest ／ artifact set ／
parse 结果 ／ record-count 结果 ／ integrity 结果，属于同一稳定 package 内容视图**，
且该视图即**被接受**、随后供 Analysis Run 使用的视图。
**prerequisite 不可判定**（例如 `manifest.json` 无法 strict-parse）时，其 downstream check
**not evaluable**，**不得**记为 passed（与 `F.2` 一致）。

**`RIF-3`（Q3 Manifest ↔ Artifact Consistency）**
**Inherited（structural，`IC`）—— 附依据：** `IS-1` ／ `IS-5` ／ `IS-6` ／ `IS-11`（`IC-14` 字数列出）；
`IS-3`（`IC-3` 唯一性 ＋ `IC-1` 粒度）；`IS-4` ／ `IS-9` ／ `IS-17b`（`IC-1` 要求 artifact 对每个 included
logical dataset **independent**，多 role 共用**同一 target identity** 的 artifact 即违反，
**无论其 reference 字面量是否相同**）；`IS-2`（`IC-8` strict-parse 失败 ⇒
`IC-16` fail closed）；`IS-7`（`"record_count"` 为 Manifest **authoritative presence metadata**，
与 artifact 内容不一致 ⇒ required structural metadata 不可靠确定 ⇒ `IC-16` fail closed）；
`IS-10`（`IC-4` ／ `IC-6` 要求 empty payload = 空 record array）。
**开放（`open`）—— 仅剩：** `IS-8`（未引用 artifact，归 Decision 1）；
`IS-17a` 的 target-equivalence 识别规则（归 Decision 4 ／ `RIF-5`）；
以及上述各 `IC` 情景的 **disposition wording ／ reporting detail**（归 Decision 8）。
**本 Review 不再把上述**任何一种列为「structural ／ allowed ／ deferred」三选一。

**`RIF-4`（Q4 Unknown ／ Undeclared Content）**
**`IS-12` ～ `IS-14` ＋ `IS-8`** —— 既有 canonical 决定**未**覆盖 → 属 Human Decision。
**`IS-15`（unknown `"_meta"` member）另有前置依赖 `DEP-8`。**
**不可让步项：** 任何策略**不得**使 unknown content 被**当作** canonical business field
（尤其 `IC-6` ／ `IC-7`）；**不得**引入 silent fix-up（`IC-10`）；
**不得**借 unknown policy 扩展 canonical field 集合。
**另须区分（与 `IS-15` 直接相关）：** 某一载体**是否允许**选择 abstract ／ parameterized policy
（参数在 implementation 前再定），与**该 policy 是否已可判定**是两件事。若允许前者，
登记内容**必须**包含参数来源、版本 ／ 绑定、缺失时行为与 closure 范围（`DEP-8` ／ `I-17`）。

**`RIF-5`（Q5 Path ／ Boundary Enforcement）**
`IC-2` 的 **boundary 结论**为 **`Inherited Constraint`**。
**`Inherited Constraint`（另附）：** 不同 included roles 的 reference **一旦确认解析到同一 artifact**，
其行为结论与 `IS-4` ／ `IS-9` 相同（`IS-17b`）—— 该部分**不**开放。
**开放：** target-equivalence 识别规则本身（`IS-17a`）：normalization 是否存在、
separator ／ case ／ symlink ／ junction ／ alias 语义；且 `PN-1` ／ `PN-2` ／ `PN-3`
**均须**定义 alias ／ link 的拒绝或安全解析边界，**不得**以低成本为由豁免 boundary 与 independence。
**这是 contract ／ validation semantics，不是 security implementation。**

**`RIF-6`（Q6 Integrity Contract）**
**`Inherited Constraint`：** integrity verification **mandatory**；`integrity unverifiable` ⇒
**Package Structural Inconsistency ⇒ fail closed**（**`IC-22`**）。
**因此 `IG-3`（advisory-but-still-accept）为 `NOT COMPATIBLE`，不是开放选项。**
**开放：** ① algorithm strategy ＋ shape（`IG-alg-*`，**本 Review 不选算法**）；
② evidence representation ／ ownership ＋ **algorithm identifier 语义**（`IG-rep-*`）；
③ digest 目标（`IG-raw` vs `IG-canon`，触发／不触发 `IC-11`）；
④ Manifest 自身 integrity（**cross-layer**，`DEP-9` ／ `DEP-10` ／ `RIF-X5`）；
⑤ **verification key ／ trust input**（仅当所选分支包含 signature 或以 signature 主张来源可信性时，`DEP-11`）。
**closure 要求：** algorithm contract **必须**达到 **deterministic 可判定**（**`I-18`**），
即其 semantics **已完整到「conforming importers 对同一 evidence 与 artifact 得出相同结果」**（`§7.1` 类别 ①）。
**若** 该状态仍依赖**未完成的 security ／ trust contract**（类别 ②），则相关分支为 **`CL-3`**，
**不得**以「已登记 future gate」判 PASS。
**不得**把「内容完整性」目标与「身份 ／ 来源可信性」目标混同 —— signature 分支的确定性前提
**包含 verification key 的信任边界**，仅登记 algorithm identifier **不足**。

**`RIF-7`（Q7 Contract Version Compatibility）**
既有 Design **未**决定 compatibility model。**`Inherited Constraint`：** **不得**对不受支持版本做
silent interpretation。`VC-*` 与 `UX-*` **互为依赖**（`DEP-1`），**必须**组合裁定。
**不得**把 version-token 匹配等同于 payload field policy：**被支持版本**与
**payload 是否符合所选版本的 contract** 是**两个不同判定**；
`VC-2` 下某版本**显式新增**的字段是该版本的 **known field**，**不**自动构成不兼容；
`VC-1` 下额外 property 的结果**由该 version 的 unknown policy（`UX-*`）决定**，
**不能**仅由 exact-match 推出 reject（详见 `Decision 2` 的更正 trade-off）。

**`RIF-8`（Q8 Partial Package ／ Failure Isolation）**
`AM-2` ／ `AM-3`（dataset-level partial acceptance）**与 `IC-13`（源 `§4.3.6` ／ `§4.3.7`）不兼容** ——
**`NOT COMPATIBLE`，不是开放选项**。
artifact parse failure ／ integrity failure ／ missing declared artifact **同属 Layer 1 structural**
（`IC-14` ／ `IC-18`），**不得**与 `Capability Evidence Unavailable` 混为一层（`IC-17`）。

**`RIF-9`（Q9 Completeness ／ Finality）**
`IC-12` 的 **immutability 语义**为 **`Inherited Constraint`**；
**检测到 post-accept mutation ⇒ 该 identity 不再可信 ⇒ fail closed**（`IC-12` ＋ `IC-16`）。
**开放：** `"completeness_state"` 是否参与 acceptance gate（`CF-*`）；
以及 detection ／ re-verification ／ binding 的 **mechanism**（`MG-*`，**不得**重新打开 immutability）。
**不实现** transaction ／ locking ／ atomic filesystem move。

> **范围更正（`IS-24` ／ `RIF-13`）：** `IS-22` ／ `MG-*` ／ `I-14` 只覆盖
> **post-accept** mutation。**acceptance 期间**的「**验证对象 ≠ 接受对象**」窗口
> **不**由此覆盖，须由 **`RIF-13`** 的 **acceptance-time 一致输入视图**义务处理。
> `CF-*` 只决定 `"completeness_state"` 是否参与 gate，**不**替代该一致输入义务。
> **本 Review 不裁定** `CF-*` 的选择，但任何 `CF-*` 选择**均不得**削弱 `IS-24` 的不可判定结论。

**`RIF-10`（Q10 Deterministic Failure Reporting）**
**`Inherited Constraint`：** Package Structural Failure 的 root-issue taxonomy 已存在 ——
**`PACKAGE_STRUCTURE` ／ `STRUCTURAL_INCONSISTENCY`**（`IC-20`）；
`REJECTED` ／ `UNUSABLE` **不是** reason 而是 **Package disposition**（`IC-21`）。
**本 Review 未发现**任何 Final Import root condition 无法落入既有 `8 categories ／ 12 reasons`
→ **不提 taxonomy gap，不新增 Validation Reason。**
**开放（`open`）：** fail-fast vs collect-all、ordering 是否 deterministic、auditable 最小内容（`FR-*`）。

**`RIF-11`（Q11 Runtime Ownership Boundary）**
**Final Import Contract owns：** acceptance ／ rejection contract、runtime structural checks、
version compatibility、path validation semantics、unknown ／ undeclared content behavior、
integrity verification contract、package atomic acceptance semantics、parser ／ validator 的 contract-level requirements。
**FCM owns：** carrier shapes ／ approved literals ／ metadata placement。
**Data Validation owns：** Layer 2 ～ Layer 4 conceptual semantics ＋ existing failure taxonomy。
**Adapter Boundary owns：** source extraction ／ source → canonical mapping ／ connector ／ source protocol。
**本 Review 未发现** ownership 冲突；**但** Manifest-self-integrity 存在 **cross-layer dependency**（`DEP-9`）。

**`RIF-12`（Q12 Minimum Closure Criteria）**
见下方候选 **`I-1` ～ `I-18` ＋ `I-21`**（MANDATORY CLOSURE CRITERION，**共 19 项**）
＋ **`I-19` ／ `I-20`**（POC DESIGN OBJECTIVE，**共 2 项**）；
**`I-21` 为 mandatory（编号位于 objectives 之后，属编号顺序而非类别差异）**；
**是否登记为正式 criteria 属 Human Decision**。

**`RIF-13`（acceptance-time 一致输入视图 —— `IS-24`，**新增 closure obligation**）**
**问题：** `IS-22` ／ `MG-*` ／ `I-14` 只处理 **accepted 之后**的变化；`CF-*` 只决定
`"completeness_state"` 是否参与 gate。二者**都未**规定：
**一次 acceptance 所依据的 Manifest、artifact set、JSON parse result、record-count result
与 integrity result，必须来自同一稳定 package 内容视图**。

**反例（reproducible 语义层面）：** importer 先对 artifact A 完成 count ／ integrity 验证；
**在 package 正式 `Accepted` 之前** A 被替换（或目录内容变化、或后续步骤重新读取到另一内容）；
其余检查随后通过，最终**被接受**的是变化后的目录 ／ 后续读取到的 A。
**所有独立检查可以分别成功，却没有任何一次验证覆盖实际 accepted 的输入。**
仅规定「`Accepted` 之后 immutable」或「检测到 post-accept mutation ⇒ fail closed」
**不能**处理该窗口。

**`Inherited Constraint`（结论）：** `IC-12` ／ `IC-13`（源 `§4.3.5` ／ `§4.3.6`）的 immutable ／
package-level atomic meaning ⇒ **验证结果必须绑定实际被接受、随后供 Analysis Run 使用的同一 package
内容视图**；**无法建立该一致性时，不得据此宣称通过**（`IC-16`，`not evaluable ≠ passed`）。

**归属（`IC + open` → Human Decision path = `Decision 10A`）：** 上述结论为 **inherited，不重新开放**；
**未决**的**仅**为 **contract-level guarantee ／ detection boundary 与报告表述**，
由 **`Decision 10A`（acceptance-time stable view ／ binding guarantee）** 裁定 ——
**本项因此不是「无 Human choice 的纯 inherited 项」**（`I-14` 的 10A 子项即映射到此）。
**若** Human 判定该 boundary 亦已被 inherited 唯一确定，则 `IS-24` 改标 **`IC`**、`Decision 10A` **折叠**
（二选一规则见下方「Human Decision path」）。

**closure obligation（`I-14` 扩展项，MANDATORY）：**
acceptance contract **必须**显式登记 「acceptance-time 一致输入视图」要求，至少覆盖：
① 判定所依据的 Manifest ／ artifact set 与**最终被接受**的视图相同；
② **一次 acceptance 内**对同一 artifact 的重复读取**不得**产生不同内容视图；
③ 无法建立 ① ／ ② 时的处置为 **fail closed ／ not evaluable**，**不得**记为 passed。

**依赖：** `RIF-2`（ordering ／ prerequisite 可达性，`not evaluable` 语义）、
`DEP-4`（completeness ／ finality，`CF-*`）、`DEP-2`（digest 目标 ⇒ 验证所覆盖的内容视图）、
`I-14`（post-accept binding）、`IC-13`（package-level atomic outcome）。

**边界（本 Review 不替 Human 选择实现机制）：** **contract-level guarantee ／ detection boundary** 属 **contract**；
**锁 ／ 事务 ／ 原子移动 ／ 存储技术**仍属 **implementation**，本 Review **不**要求实现它们，
**不**创建 sidecar ／ validator，**不**新增 carrier ／ literal。
本项**继承** `§4.3.5` ／ `§4.3.6` 的 immutable ／ package-level atomic meaning，
**不**重新打开 immutability。

**Human Decision path（**不得省略 —— `I-14` 必须可映射**）：** 本项**不**是「无 Human choice 的纯 inherited 项」：
inherited 部分为 **必须绑定同一稳定内容视图 ＋ 无法建立即 fail closed**；
**未决**部分为 **contract-level guarantee ／ detection boundary 与报告表述**，
由 **`Decision 10A`（acceptance-time stable view ／ binding guarantee）** 裁定（`Decision 10B` 继续负责 post-accept）。
`I-14` 的 PASS **必须**同时映射 **10A** 与 **10B**。

> **二选一规则（显式，避免 `IC + open` 与「已 inherited 唯一确定」并存）：**
> **若** Human 判定 acceptance-time guarantee 已被 inherited constraints **唯一确定**、不存在任何 Human choice，
> **则** `IS-24` **必须**改标为 **`IC`**，并**删除**本项中「guarantee ／ detection boundary open」的表述，
> `Decision 10A` 相应**折叠**为无待决项。
> **若** 认为 guarantee ／ detection boundary 仍需 Human 裁定，**则**保留 **`IC + open`** 与 `Decision 10A`。
> **本 Review 不代替 Human 作此二选一**；两种表述**不得**同时成立。

**`RIF-X1`（正交维度 —— syntax validity vs semantic recognition）**
必须把两个**正交**维度分开，**不得**互相推导：

| 维度 | 判定对象 | 归属 |
| --- | --- | --- |
| **JSON syntax ／ lexical validity** | 文档是否符合 JSON grammar（`IC-8` strict parse：禁 duplicate key ／ comments ／ trailing comma ／ `NaN` ／ `Infinity`） | `IC-8`（**syntax 层**） |
| **contract semantic recognition** | **已成功 parse** 的文档中，某 property 是否属 contract 已识别的集合 | unknown-content policy（**语义层**） |

**一个 JSON 文档完全可以同时**：① 严格符合 JSON grammar；② 含 contract 未识别的 property；
③ 再由 Final Import Contract 决定 reject ／ ignore ／ preserve。
**因此 `UX-A` ／ `UX-B` ／ `UX-C` 对 `IC-8` 的 strict parse 均兼容** ——
本 Review **不**主张 `UX-B` 削弱 strict parse；真正的 trade-off 是
**typo detection ／ forward compatibility ／ silent semantic loss**。
**本 Review 不因此偏向任何 `UX-*`。**

**`RIF-X2`（跨层风险）**
`IS-7` 的判定**同时**触及 `IC-4`（presence metadata）、`IC-15` ／ `IC-22`（integrity 覆盖对象）、
`IC-14`（structural 定义）—— 本 Review 已将其归入 **`IC`**，但**其 disposition wording 仍开放**。

**`RIF-X3`（边界发现）**
`IS-14`（unknown canonical record property）与 `IS-15`（unknown `"_meta"` member）**物理同层**、
语义归属**不同**（business vs reserved carrier metadata）；若采用**同一** unknown policy，
**必须**确认不会把 `"_meta"` 内容误读为 business field（`IC-6` ／ `IC-7`）。
且 `IS-15` 受 `DEP-8` 前置约束。

**`RIF-X4`（依赖发现）**
**不得**制造不存在的共同耦合。三项的依赖**分别**为：

| 项 | 准确依赖 |
| --- | --- |
| unknown-content policy（`IS-12` ～ `IS-14` ／ `IS-8`） | **`DEP-1`** —— 与 `VC-*`（version compatibility）**组合**裁定（**先**由版本确定 applicable contract ／ known member set，**再**应用该 contract 的 unknown policy） |
| unknown `"_meta"` member policy（`IS-15`） | **`IC-7`** ＋ **`DEP-8`**（known member set 前置）＋ **`DEP-10`**（FCM residual 的 non-blocking 结论**不得**直接沿用） |
| Manifest self-integrity（`IG-self-*`） | **`IC-5` ／ `IC-7`** ＋ **`DEP-9`** ／ **`DEP-10`**；若采用 **canonicalized bytes** 则另涉 **`IC-11`** |
| signature ／ authenticity 分支（若被选择） | **`DEP-11`** —— verification key 信任源 ＋ evidence representation ＋ Manifest self-integrity |
| acceptance-time 一致输入视图（`IS-24` ／ `RIF-13`） | **`DEP-2`** ＋ **`DEP-4`** ＋ `RIF-2` 的 prerequisite 边界（**不**依赖 `MG-*` 的具体 mechanism 选择） |

**`IC-20` 是 Validation Taxonomy**，与上述三项**不构成**共同依赖。
**建议** Human 以**组合**方式裁定**相关**项，而非逐项独立裁定。

**`RIF-X5`（cross-layer finding —— Manifest 自身 integrity）**
`IC-5` ／ `IC-7` **未**提供 Manifest-self-integrity carrier；因此任何要求 Manifest 自身被
hash ／ sign 的方案都可能需要 **detached evidence ／ sidecar ／ package-level 新 carrier ／
自引用排除规则 ／ canonicalization 规则** —— 其中**新增 carrier ／ sidecar ／ literal**
已**越出** Final Import Contract 的 Write Scope（触碰 **Field Carrier Mapping ／ Physical Dataset Layout**）。
**处置：** `IG-self-A` ／ `IG-self-B` **必须**标为 **requires separate Human-authorized design change**；
**在该 cross-layer design change 实际完成前，受影响的 `I-10` 为 `CL-3`**（`§7.1` 类别 ②）。
本层**可**采纳 `IG-self-C`（只要求可信性可建立，不规定 mechanism ／ carrier），
且**不得**由 Agent 自行新增任何 literal。
**但 `IG-self-C` 不是无条件 closure：** 「只要求可信性可建立」若**未**说明
**可审计的信任前提 ／ 输入边界**，则仅是**目标陈述**，**不可判定**；
**且**其 PASS **必须**证明属 **`§7.1` 类别 ①**（contract 已闭合、不依赖未完成设计、同一输入结果唯一）——
否则为 **`CL-3`**。须按上方 **`D.5` 的前提条件与 closure 边界**登记
（并见 **`§7.1`** 的 closure 强度分级 ／ **`DEP-10`**）。
已关闭层（`§4.3.27` D）记录的 FCM non-blocking residual **不**自动对本层候选分支成立，
**必须**在本层按其自身 contract 依赖**重新评估**（`DEP-10`）。

---

**7.1 Claimable Design-Closure Levels（`closure claim` 强度分级）**

本层各候选 `I-*` criterion 的 **PASS 强度必须可判定** —— 否则「已登记」会被误读为「已满足」。
因此定义**三个** closure level；**每一项 closure claim 必须归入其一**：

| Level | 名称 | 含义（可作为本层 closure 结论的条件） |
| --- | --- | --- |
| **`CL-1`** | **unconditional** | 该 criterion 的行为**已由 inherited constraint 或已登记的 contract 语义唯一确定**；**不**依赖任何未决选择或未提供输入，**无**后续前置条件（**contract semantics 已完整且无未决输入的 design criterion 亦属此级**） |
| **`CL-2`** | **conditional（仅限 parameterized external input contract）** | 该 criterion 的 **contract semantics 本身已完整**：对同一输入，**所有 conforming importer 必须得到相同 disposition**。**此时唯一仍未定的只能是运行时可缺失的 external parameter 的值**，且**必须**同时登记：① **authoritative parameter ／ input 的来源**、② **版本 ／ 绑定关系**、③ **缺失或不可用时的确定性行为**（fail closed ／ `not evaluable`）、④ **同一输入下结果唯一**（conformance determinism）、⑤ **可声称的 closure 范围**。**①～⑤ 全部满足**才可记为 **PASS（conditional）** —— 因为此时 **contract 已闭合**，缺的只是运行时取值 |
| **`CL-3`** | **not claimable** | 该 criterion 的**接受判定**依赖一个**尚未完成的 design prerequisite**（其 contract semantics 尚未定义到「conforming importers 会得出相同 disposition」）⇒ **不可记为 PASS**；只能记为 **`BLOCKED` ／ 不可判定**，并标记所需跨层变更，直至该 prerequisite **实际完成** |

> **`CL-2` 与 `CL-3` 的分界（**必须以「contract 是否已闭合」判定，不得以「是否登记了 completion gate」判定**）：**
>
> | 类别 | 判别依据 | 结论 |
> | --- | --- | --- |
> | **① Parameterized external input contract** | contract **已完整规定** parameter 的 authoritative source、version ／ binding、missing ／ unavailable 时的 deterministic fail-closed 行为，且**同一输入下 conforming importers 必须得到同一结果**。运行时该 parameter 可能缺失，**但 contract 本身已闭合** | **可 claim 的 `CL-2`（conditional contract）** |
> | **② Unfinished design prerequisite** | 例如：**新 carrier ／ sidecar ／ literal**、**未定义的 trust mechanism**、**未完成的 key-management ／ security contract**，或**任何尚未定义到足以使 conforming importers 得出相同 disposition 的跨层 contract** | **`CL-3` ／ `BLOCKED`**；**仅登记 completion gate 不等于 prerequisite 已满足** —— 在该设计**实际完成**前 **不得 PASS** |
>
> **判定测试（必须显式执行并记录）：** 「若今天有两份独立实现，仅依据当前已登记的 contract，它们对同一 package 是否必然得出同一 disposition？」
> 答案为**是** ⇒ `CL-2` 可用（①）；答案为**否** ⇒ 属 ②，**只能 `CL-3`**。

**强制规则：**

1. **不得**把 `CL-2` 表述为 `CL-1`：**「记录依赖」≠「满足依赖」**。
   `CL-2` **只**适用于**类别 ①**（contract 已闭合、仅运行时 external parameter 待定）；
   凡属**类别 ②（未完成的 design prerequisite）**，**无论** completion gate 登记得多完整，
   在 prerequisite **实际完成前**一律为 **`CL-3`**，**不得**记为 PASS。
2. **implementation residual 不得归入 `CL-2`（依 `CL-2` 的「only」定义）：**
   `CL-2` **只**适用于**类别 ① parameterized external input contract**。
   三项必须分开处理，**不得**互相泛化：
   - **不影响 acceptance semantics 的 implementation detail residual**（例如内部命名、
     不影响判定结果的表示细节）⇒ **明确标为 non-blocking implementation residual，
     即 outside the FIC acceptance criterion** —— 它**既不是** `CL-2`，**也不**作为本层 closure 依据；
   - **contract semantics 已完整且无未决输入的 design criterion** ⇒ 记为 **`CL-1`**
     （**不**因附带 implementation residual 而降级为有条件 PASS）；
   - **影响 acceptance semantics 的 contract prerequisite**（例如 known member set、
     verification key 信任源、acceptance-time 一致输入视图、新 carrier ／ sidecar ／ literal）
     ⇒ 按类别 ① ／ ② 判定：**contract 已闭合**者 `CL-2`，**尚未完成者 `CL-3`**。
   判断归属的依据是 **「该项缺失时，acceptance 结果是否仍可唯一确定」**；
   同时须回答 **「它是否参与 FIC acceptance criterion 本身」**。
3. **跨层变更的 gate：** 对选中方案必需的跨层变更（`DEP-9` ／ `DEP-10` ／ `DEP-11`）
   **不得**写成「已标记为 separate change ⇒ 本 criterion PASS」，**亦不得**写成
   「已登记 completion gate ⇒ 本 criterion PASS」；
   **必须**同时明确**该 separate change 的完成是否是本层 closure 的前提**，
   以及在其**完成前**本层**可声称的范围**（`CL-1` ／ `CL-2`）与**不可声称的部分**（`CL-3`）。
   **凡未完成者，受其影响的 criterion 记为 `CL-3`。**
4. **`IG-self-C` 与 abstract `"_meta"` policy 的门禁：**
   允许参数化 ／ 抽象 policy 作为设计关闭结果，**但**该允许**本身不构成** `CL-1`，
   也**不自动构成** `CL-2`；其 PASS 记录**必须**证明其属**类别 ①**：
   参数来源、版本 ／ 绑定、缺失时**确定性**行为、**同一输入结果唯一**、closure 范围，
   并**明确排除**其仍依赖任何**未完成的设计**（新 carrier ／ literal ／ trust mechanism ／
   key-management contract）；**依赖未完成设计者为 `CL-3`**。
   **不得**一面承认 acceptance policy 在该前提下**不可判定**，一面无条件宣称本层 resolved。
5. **本分级不改变任何状态：** 本节**只**约束 **closure claim 的强度与可判定性**；
   **不**新增 decision、**不**选择 option、**不**改变 `Final Import Contract = DESIGN PENDING`。

---

**8. Proposed Minimum Closure Criteria（candidate —— 待 Human 批准）**

> **closure 强度约定（`§7.1` 强制适用）：** 每项 criterion 的最终 PASS **必须**标注
> closure level（`CL-1` ／ `CL-2` ／ `CL-3`）。
> **`CL-2` 只**适用于**类别 ① parameterized external input contract**，并**必须**同时登记
> 「参数来源 ／ 版本绑定 ／ 缺失时确定性行为 ／ 同一输入结果唯一 ／ 可声称范围」。
> **`CL-2` 缺少上述任一项 → `CL-3`**；**依赖未完成 design prerequisite（类别 ②，
> 含新 carrier ／ sidecar ／ literal、未定义 trust mechanism、未完成 key-management ／ security contract）
> → 一律 `CL-3`，且「已登记 completion gate」不改变该结论，直至 prerequisite 实际完成。**
> **不影响 acceptance semantics 的 implementation detail residual 标为
> non-blocking implementation residual（outside the FIC acceptance criterion）——
> 既不归入 `CL-2`，也不作为 closure 依据；contract semantics 已完整且无未决输入者记为 `CL-1`。**
> 本表**不**预先判定任何选项，**不**改变任何 status。

| # | Criterion | 类别 |
| --- | --- | --- |
| `I-1` | acceptance boundary 已登记：哪些检查完成后 package 才可 `Accepted` | MANDATORY CLOSURE CRITERION |
| `I-2` | `REJECTED` ／ `UNUSABLE` 的 **contract-level usage** 已由 Human Decision 登记（**不新增** enum） | MANDATORY CLOSURE CRITERION |
| `I-3` | acceptance **partial order** 已登记：inherited 前置边已固定，且 integrity 位置**显式**依赖 digest 目标选择 | MANDATORY CLOSURE CRITERION |
| `I-4` | `IS-*` 的 structural 集合已登记，且**未**被重新打开为自由 trade-off；`IC + open` 项的 **disposition wording** 已登记 | MANDATORY CLOSURE CRITERION |
| `I-5` | unknown ／ undeclared content policy 已逐类登记（含 `IS-8`）；**且**登记时**显式**给出 applicable contract ／ known member set 的确定前提（先定 version ／ contract，**再**应用 unknown policy） | MANDATORY CLOSURE CRITERION |
| `I-6` | path resolution ／ boundary enforcement semantics 已登记（含 normalization 与 case ／ symlink 语义）；**且** `PN-1` ／ `PN-2` ／ `PN-3` 均定义了 alias ／ link 的拒绝或安全解析边界 | MANDATORY CLOSURE CRITERION |
| `I-7` | normalized ／ aliased **target identity** 的判定语义已登记，且**明确**：target identity 一旦确定为同一 artifact，即适用 `IC-1`（同 `IS-4` ／ `IS-9`，**不**作为自由选项） | MANDATORY CLOSURE CRITERION |
| `I-8` | integrity **evidence representation ／ ownership** 已登记（**mandatory 性与 fail-closed 属 inherited，不重开**）；**若**所选分支主张 **signature ／ authenticity**，则 verification key 的**信任来源 ／ 配置边界 ／ 绑定** 与 key 不可用时的行为**一并**登记 | MANDATORY CLOSURE CRITERION |
| `I-9` | integrity 覆盖对象 ＋ digest 目标（raw vs canonical）已登记，且与 `IC-11` 一致 | MANDATORY CLOSURE CRITERION |
| `I-10` | Manifest 自身 integrity 的处置已登记，**且达到相应 closure level**：**或** `IG-self-C` 并登记其**可审计信任前提 ／ 输入边界 ＋ 是否影响 acceptance 判定 ＋ 可声称 closure 范围**，且证明其属 `§7.1` **类别 ①**（contract 已闭合；manifest 自身可信性的建立依据**不**再依赖任何**未完成设计**）⇒ `CL-2`；**或** 明确标记为 **requires separate Human-authorized design change**。**若选中 `IG-self-A` ／ `IG-self-B`（需要新 carrier ／ sidecar ／ layout ／ naming contract），或 `IG-self-C` 的可信性建立仍依赖未定义 trust mechanism，则该 design change 完成前一律 `CL-3`：仅声明「已标记为 separate change」或「已登记完成 gate」均不构成 PASS** | MANDATORY CLOSURE CRITERION |
| `I-11` | `contract_version` compatibility model 已登记，且**禁止** unsupported version 的 silent interpretation；**且**区分「版本被支持」与「payload 符合所选版本 contract」，**不**把 version-token 匹配等同于 unknown-field policy | MANDATORY CLOSURE CRITERION |
| `I-12` | package-level atomic acceptance 语义已登记（**无** dataset-level partial outcome） | MANDATORY CLOSURE CRITERION |
| `I-13` | `"completeness_state"` 在 acceptance gate 中的角色已登记 | MANDATORY CLOSURE CRITERION |
| `I-14` | **双向**登记（均**不得**重开 immutability）：**(10A)** acceptance-time **一致输入视图 ／ binding guarantee** —— 验证结果绑定实际被接受、随后供 Analysis Run 使用的同一 package 内容视图，无法建立一致性时为 **fail closed ／ not evaluable**（`IS-24` ／ `RIF-13`），其 **contract-level guarantee ／ detection boundary** 由 **Decision 10A** 裁定；**(10B)** **post-accept** mutation 的 **detection ／ re-verification ／ binding** 要求（**Decision 10B**）。**`I-14` 的 PASS 必须显式映射到这两条 Decision path**（10A ／ 10B）；任一子项为 `CL-3` 时，`I-14` 整体**不得**记为 PASS | MANDATORY CLOSURE CRITERION |
| `I-15` | failure reporting 的 **shape**（fail-fast ／ collect-all **受 prerequisite 边界限定**、ordering、auditable 最小内容、`not evaluable due to prerequisite` 与 `evaluated` 的区分）已登记，且 root-issue 沿用 inherited `PACKAGE_STRUCTURE` ／ `STRUCTURAL_INCONSISTENCY` | MANDATORY CLOSURE CRITERION |
| `I-16` | layer ownership boundary 已登记，且**不**把 Layer 2 ～ Layer 4 问题提升为 structural failure（`IC-17`） | MANDATORY CLOSURE CRITERION |
| `I-17` | unknown-`"_meta"` member policy 的**前置条件**已处置，**且按 prerequisite 是否已实际满足取级**：**(i)** Human 在当前 ／ 补充决定中**实际登记 authoritative known member set（或 literal set）并完成 binding** ⇒ `CL-1`；**(ii)** 仅决定「后续另开 naming decision」⇒ 在**该 naming decision 实际完成前为 `CL-3`** —— **「另开 naming decision」本身不产生 known member set，不构成 PASS**；**(iii)** 登记 **parameterized external member-set contract**，且**证明其属 `§7.1` 类别 ①**（authoritative member set 的来源 ／ 版本绑定 ／ 缺失时确定性行为（fail closed ／ not evaluable）／ 同一输入下结果唯一 ／ 可声称 closure 范围**全部**已登记，且不依赖任何未完成设计）⇒ `CL-2`。**若 member set 缺失使 policy 在该前提下不可判定（类别 ②），一律 `CL-3`** | MANDATORY CLOSURE CRITERION |
| `I-18` | **integrity verification algorithm contract** 已达 **deterministic 可判定**状态：algorithm strategy ／ supported algorithm contract ／ **algorithm identifier 语义**已登记（`IG-alg-*` 之一，必要时含 evidence 表示）；**若**含 signature ／ authenticity 分支，则 **verification key ／ trust input 的确定方式**（来源、绑定、不一致时的处置）**必须已完整定义到「conforming importers 得出相同 disposition」**（`§7.1` 类别 ①）才可 PASS。**若 deterministic verification 仍依赖未完成的 security ／ trust contract（类别 ②），则该分支为 `CL-3`，不得以「已登记 future gate」判 PASS** | MANDATORY CLOSURE CRITERION |
| `I-21` | 跨选择无阻塞矛盾已显式核验：对**已选**的 option 组合，逐项确认不存在 `IC` 冲突（`NOT COMPATIBLE` 项未被隐式选中）；**且**逐项确认**没有**任何拟记为 `CL-2` 的 criterion 实际依赖**未完成的 design prerequisite**（`§7.1` 类别 ②），并已记录每项 `CL-2` 的「同一输入结果唯一」判定测试结果 | MANDATORY CLOSURE CRITERION |
| `I-19` | Human Inspectability（acceptance outcome 与 defect 可被人工检视） | POC DESIGN OBJECTIVE |
| `I-20` | Implementation Simplicity（contract 结构最小化） | POC DESIGN OBJECTIVE |

`I-19` ／ `I-20` **必须评估**，但**不作为**独立 hard closure blocker；
**不得**把主观判断变成不可验证的 closure Gate。

---

**9. Human Decision Required**

**Decision 1 —— Unknown content policy（4 类载体）**
- **Question：** `IS-12`（Manifest property）／ `IS-13`（dataset-entry property）／ `IS-14`（canonical record property）／ `IS-8`（unreferenced artifact）各自采用 `UX-A` reject ／ `UX-B` ignore ／ `UX-C` preserve-but-not-interpret？
- **Options：** 三选一，按载体分别裁定。
- **Trade-offs：** reject = forward compatibility 最差但 typo 最安全；ignore = 成本最低但有 **silent data loss** 风险；preserve = forward compatible 但需明确「不解释」。
- **前提（**必须先确定，否则选项不可判定**）：** unknown policy **只**对**已确定适用的 contract** 生效 —— **先**由 version ／ compatibility 规则确定 **applicable contract 与 known member set**，**再**应用该 contract 的 unknown policy。
  **不得**把「unsupported version 的 rejection」与「supported version 下 payload 的 unknown property 处置」混为一谈（更正后见 `DEP-1` ／ `Decision 2`）。
- **Dependencies：** `DEP-1`（与 `VC-*` **组合**裁定）、`RIF-X1`、`IC-6`；`IS-15` 另受 `DEP-8` ／ `DEP-10` 前置约束，**不**在本 Decision 内裁定（见 Decision 11）。
- **What changes：** `I-4` ／ `I-5` 的最终分类；版本演进策略。

**Decision 2 —— Contract version compatibility model**
- **Question：** `VC-1` exact-match ／ `VC-2` explicit supported set ／ `VC-3` major-minor？
- **Options：** 三选一。
- **Trade-offs（更正）：** `VC-1` 只接受**一个** version token，成本最低，**但**「额外 property 是否被接受」**由该 version 的 unknown policy 决定**，**不能**仅由 exact-match 推出 reject；`VC-2` 可对**每个受支持版本**定义各自的 known field set，某版本**显式新增**的字段是该版本的 **known field**，**不**自动构成不兼容；`VC-3` 灵活但引入演进体系成本。**选择 `VC-*` 不代替** `UX-*` 的选择。
- **Dependencies：** `DEP-1`（与 Decision 1 **必须**组合裁定）。
- **What changes：** unsupported version 的 acceptance 结果；**以及**「supported version 内 payload 是否符合该版本 contract」这一独立判定的归属（归 `UX-*` ／ 该版本的 known member set）。

**Decision 3 —— `REJECTED` vs `UNUSABLE` 的 contract-level usage**
- **Question：** 二者是同一 negative disposition 的两种写法（`RD-A`）／ 分别表示 import-time reject 与 previously-accepted-then-unusable（`RD-B`）／ 其他有 evidence 支持的区分（`RD-C`）？
- **Options：** `RD-A` ／ `RD-B` ／ `RD-C`（须先给出依据）。
- **Trade-offs：** `RD-A` 最简且与现状一致；`RD-B` 语义更丰富但需定义「何时从 accepted 变为 unusable」并与 `IC-12` ／ `IC-16` 一致。
- **Dependencies：** `IC-21`（二者**不是** reason）；`IC-19`（lifecycle）；`I-2`。
- **What changes：** `I-2` 的可判定性；disposition 在 reporting 中的表述。
- **注意：** **不新增 enum**；**只**决定**现有两个术语**的 usage。

**Decision 4 —— Path resolution ／ normalization semantics**
- **Question：** `PN-1` 严格字面量 ／ `PN-2` 确定性 normalization ／ `PN-3` ＋ 平台语义？另需裁定 separator ／ case ／ symlink ／ junction ／ alias 与 normalized duplicate（`IS-17`）。
- **Options：** 同上；`IC-2` 为**不可让步**项。
- **Trade-offs：** `PN-1` 可预期性最高但不处理平台差异；`PN-3` 覆盖最全但引入非确定性风险。
- **Dependencies：** `DEP-5`。
- **What changes：** 哪些 reference 被判非法；`IS-16` ／ `IS-17a` 的判定结果（`IS-17b` 的结论**已 inherited，不**随本 Decision 变化）。

**Decision 5 —— Integrity algorithm strategy ／ evidence representation ／ ownership**
- **Question：** algorithm strategy 取哪一族（cryptographic hash ／ checksum ／ signature ／ 混合）与哪一 shape（`IG-alg-1` fixed ／ `IG-alg-2` supported set ／ `IG-alg-3` algorithm-tagged）？evidence 表示与 **algorithm identifier 语义**归属由本层定义（`IG-rep-A`）还是留给实现（`IG-rep-B`）？
- **Options：** algorithm 族（**本 Review 不选**）；`IG-rep-A` ／ `IG-rep-B`。
- **Trade-offs：** `IG-rep-A` 使 `IC-15` 更可判定但更接近实现；`IG-rep-B` 更轻，但**可能不足以满足本层 closure**（verification 将依赖 implementation 选择）—— 若选则**必须**说明如何达到 deterministic verification。
- **Dependencies：** `DEP-3`（mandatory 性已 inherited，**不再**是选项）；`DEP-11`（仅当选择 signature ／ 主张 authenticity 时）；与 `IC-7` 的 carrier ownership 边界。
- **What changes：** `I-8` ／ **`I-18`** 的可判定性；verification 是否**不依赖** implementation 选择。
- **注意（更正 —— signature 分支为条件性可行）：** **mandatory 性与 fail-closed 属 inherited（`IC-22`），本 Decision 不重新打开。**
  若选择 **digital signature ／ 混合**，则**必须**同时登记：**verification key 的信任来源 ／ 配置边界 ／ 选择规则**、
  key 与 contract 的**绑定**、key 不可用或不一致时的处置，以及与 **evidence representation**（`IG-rep-*`）／
  **Manifest self-integrity** 的依赖（`DEP-11`）；**仅登记 algorithm identifier 不构成 deterministic verification**。
  **content integrity（hash ／ checksum）目标 ≠ identity ／ authenticity 目标** ——
  「数学验证成功」**不得**被当作来源可信。**本 Decision 不要求**引入 PKI ／ secrets ／ signing infrastructure；
  若该分支需要新的 security ／ key-management design，**必须**按治理登记 **requires separate Human-authorized design change**，
  并**明确**其完成是否阻塞所选分支 closure。**本 Review 不选任何算法族。**

**Decision 6 —— Integrity 覆盖对象与 digest 目标**
- **Question：** digest 针对 **raw artifact bytes**（`IG-raw`）还是 **canonicalized bytes**（`IG-canon`）？覆盖哪些对象？
- **Options：** `IG-raw` ／ `IG-canon`。
- **Trade-offs：** `IG-raw` 成本低且与 `IC-11` 的区分保持；`IG-canon` 允许跨序列化比较但**触发** byte-level canonicalization 设计。
- **Dependencies：** `DEP-2`；与 Decision 5 一致。
- **What changes：** 是否需要在 `§4.3.22` D 之外新增 byte-level canonicalization 设计；`I-9`。

**Decision 7 —— Manifest 自身 integrity 的 cross-layer 处置**
- **Question：** 采纳 `IG-self-C`（只要求可信性可建立、不规定 mechanism ／ carrier），还是采纳 `IG-self-A` ／ `IG-self-B`（需要新 carrier ／ sidecar）？
- **Options：** `IG-self-C` ／ `IG-self-A` ／ `IG-self-B`。
- **Trade-offs：** `IG-self-C` 在本层 scope 内且不新增 naming；`IG-self-A` ／ `IG-self-B` 语义更强但**越出**本层 Write Scope。
- **Dependencies：** `DEP-9` ／ `DEP-10` ／ `RIF-X5`；`IC-5` ／ `IC-7`。
- **What changes：** `I-10` 的处置方式**与可声称的 closure 强度**（`§7.1` `CL-2` ／ `CL-3`）。
- **注意（依 `§7.1` 收紧）：** 任何需要**新增 carrier ／ sidecar ／ literal** 的方案**必须**标记为
  **requires separate Human-authorized design change**；**在该 design change 实际完成前，
  受其影响的 criterion（`I-10`）一律 `CL-3`** —— **不得**以「已标记 separate change」**或**
  「已登记 completion gate」作为本层 closure 依据。**completion gate 必须已满足，而非仅已登记。**
- **额外要求（`IG-self-C` 不得省略）：** 若选择 `IG-self-C`，**必须**登记**可审计的信任前提 ／ 输入边界**
  （见上方 `D.5` 的前提条件），**并证明其属 `§7.1` 类别 ①**：
  manifest 自身可信性的建立依据**不**再依赖任何**未完成设计**（新 carrier ／ sidecar ／ literal、
  未定义 trust mechanism、未完成 key-management ／ security contract）⇒ 方可 `CL-2`。
  **若仍依赖上述未完成设计，则 `CL-3`。**
  仅声明「可信性必须可建立」是**目标陈述**，**不可判定**，**不构成** PASS。
  同时**不得**直接沿用已关闭层（`§4.3.27` D）的 FCM non-blocking residual 结论来证明本分支 non-blocking（`DEP-10` ／ `IS-25`）。

**Decision 8 —— Failure reporting shape**
- **Question：** `FR-1` fail-fast ／ `FR-2` collect-all（**受 prerequisite 边界限定**）／ `FR-3` ＋ deterministic ordering？auditable 最小内容如何界定（在 `§4.4.79` dimensions 之内）？
- **Options：** 三选一 ＋ audit 内容范围。
- **Trade-offs：** fail-fast 成本低但多 defect 信息不全；collect-all 更完整，但**只能**覆盖 prerequisite **可达**的 defect，且需 ordering 保证；`not evaluable due to prerequisite` **必须**与「已评估通过」显式区分。
- **Dependencies：** `DEP-6`；root-issue taxonomy **已 inherited**，**不在**本 Decision 范围。
- **What changes：** `I-15`；reporting 的 auditable 内容。

**Decision 9 —— `"completeness_state"` 的 acceptance 角色**
- **Question：** `CF-1` 纯 metadata ／ `CF-2` 参与 gate ／ `CF-3` 要求 final 状态？
- **Options：** 三选一。
- **Trade-offs：** `CF-1` 不改变判定、成本最低；`CF-2` ／ `CF-3` 会新增拒绝条件。
- **Dependencies：** `DEP-4`；**`RIF-13`**（`IS-24` 的 acceptance-time 一致输入视图义务**不**因选择 `CF-1` 而消失）。
- **What changes：** incomplete ／ in-progress package 是否可被读取或 accepted；`I-13`。
- **注意：** 本 Decision **只**决定 `"completeness_state"` 的角色，**不**决定 acceptance-time 一致性要求；
  任一 `CF-*` 选择**均不得**被解释为已满足 `I-14` 的 `RIF-13` 义务。

**Decision 10 —— Acceptance-time ／ post-accept mutation 的 detection ／ re-verification ／ binding**

> 本 Decision **拆为两个子边界**（`10A` ／ `10B`），用于给 `I-14` 提供完整、可映射的 Human Decision path。
> **子边界仅划分 Human 的裁定范围**，**不**新增 status enum ／ Validation Reason ／ carrier ／ 实现机制。

**Decision 10A —— acceptance-time stable view ／ binding guarantee**
- **Question：** acceptance 期间「验证对象 ≠ 接受对象」窗口（`IS-24`）所需建立的
  **contract-level guarantee ／ detection boundary** 如何界定 ——
  即：验证结果绑定「实际被接受、随后供 Analysis Run 使用的同一 package 内容视图」这一要求的
  **保证边界**（在哪一步之前必须已建立、跨哪些读取必须一致）与**报告表述**如何？
- **Options：** 由 Human 就 **guarantee ／ detection boundary 的 contract 表述**裁定
  （**不**选择锁 ／ 事务 ／ 原子移动 ／ 存储技术）。
  备选表述方向（**本 Review 不选**）：最小保证（仅规定「不得据不同视图宣称通过」）／
  显式视图绑定要求（规定 acceptance 内读取必须属于同一视图并需要可审计引用）。
- **inherited（不重新开放）：** 必须绑定同一稳定内容视图；无法建立一致性 ⇒ **fail closed ／ not evaluable**（`IC-12` ／ `IC-13` ／ `IC-16`）。
- **Trade-offs：** 最小保证成本最低，但可审计性弱；显式视图绑定更可判定，但更接近实现边界。
- **Dependencies：** `RIF-13` ／ `RIF-2`（prerequisite 边界）；`DEP-2`（digest 目标 ⇒ 覆盖的内容视图）；`DEP-4`（`CF-*`，**不**替代本项）；`IC-13`。
- **What changes：** `I-14` 的 **10A 子项**是否可 PASS；`IS-24` 的 `open` 部分能否收敛
  （**若** Human 判定其已被 inherited 唯一确定，则 `IS-24` 改标 `IC`、本子项**折叠**，见 `RIF-13` 的二选一规则）。
- **注意：** `Decision 9`（`CF-*`）**不**处理本项；`Decision 10B` **不**处理本项。

**Decision 10B —— post-accept mutation detection ／ re-verification ／ binding**
- **Question：** `MG-1` 不规定 proactive detection ／ `MG-2` 要求 re-verification ／ `MG-3` 要求 identity ／ content binding？
- **Options：** 三选一。
- **Trade-offs：** `MG-1` 最简（**但不得**被解释为 mutation 后仍可作为同一 Accepted package 使用）；`MG-2` ／ `MG-3` stronger but closer to storage implementation。
- **Dependencies：** `IC-12` ＋ `IC-16`（**immutability 与 fail-closed 已 inherited**）。
- **What changes：** `IS-22` 的 detection 要求；`I-14` 的 **10B 子项**。
- **注意：** **不重新打开 immutability。** 本子项**只**覆盖 **post-accept** mutation；
  **acceptance 期间**「验证对象 ≠ 接受对象」的窗口（`IS-24`）属 **`10A`**，
  **不**由本子项处理。

**Decision 11 —— unknown `"_meta"` member policy 的前置条件**
- **Question：** 是否把 P-A ／ MB-A 的 **known member set** 升为**独立 naming decision**，还是**允许**先登记 **abstract unknown-member policy**（implementation 前再定 literal）？
- **Options：** 独立 naming decision ／ abstract policy now ＋ literal later。
- **Trade-offs（更正 —— 依 `§7.1` 的类别 ① ／ ② 判定；关键在 prerequisite 是否已实际满足）：**
  - **(i) 本次即实际登记 authoritative known member set（或 literal set）并完成 binding** ⇒ `IS-15` 立即可判定，**`CL-1`**；
  - **(ii) 仅决定「后续另开 naming decision」** ⇒ **在该 naming decision 实际完成前为 `CL-3`** ——
    **「另开 naming decision」本身不产生 known member set，「已登记 future gate」不构成 PASS**；
  - **(iii) 登记 parameterized external member-set contract 并证明属类别 ①** ⇒ `CL-2` ——
    即 member set 的 **来源**、**版本 ／ 绑定**、**缺失时确定性行为（fail closed ／ `not evaluable`）**、
    **同一输入下结果唯一**、**可声称 closure 范围**全部已由 contract 完整规定，
    **且不依赖任何未完成设计**。
  **若** member set 缺失使 policy 在该前提下**不可判定**（属 **类别 ② 未完成 design prerequisite**），
  则**一律 `CL-3`**。
  **不得**一面承认 policy 在 known member set 未定时不可判定，一面无条件宣称本层已处理该依赖。
  **不得**把 (ii) 表述为 `CL-1`。
- **Dependencies：** `DEP-8` ／ `DEP-10`；`IC-7`（内部 member 名称未批准）；`§7.1`。
- **What changes：** `I-17` 的处置**与 closure 强度**；是否需要在 `Final Import Contract` 之外新增 naming task
  （**新增 naming task 本身不等于 prerequisite 已满足**）。
- **注意：** **不得**由 Agent 自行发明 provenance ／ basis 内部 property name。

**Decision 12 —— Minimum closure criteria 接受与 follow-up 授权**
- **Question：** 是否接受 **`I-1` ～ `I-18` ＋ `I-21`**（MANDATORY CLOSURE CRITERION，**共 19 项**）作为 minimum closure criteria（`I-19` ／ `I-20` 为 design objectives，**共 2 项**）？是否授权后续独立
  `Final Import Contract` Design Change ／ Implementation PR（登记选择 ＋ 同步 current-state），
  并在满足 closure criteria 时允许 `DESIGN PENDING → DESIGN RESOLVED`？
- **Options：** 接受 ／ 调整 ／ 拒绝；授权 ／ 不授权。
- **Trade-offs：** 授权推进 closure；不授权保持 `DESIGN PENDING`。
- **Dependencies：** Decision 1 ～ 11；**`§7.1` 的 closure 强度规则**（每项 PASS 必须标注 `CL-1` ／ `CL-2` ／ `CL-3`，
  且 `CL-2` 须满足 ①～⑤）。
- **What changes：** 本层是否可进入 closure；**以及**哪些 criterion 可以 `CL-1` ／ `CL-2` 声称、
  哪些必须在跨层变更完成后才可声称。

**本 Review 不作出上述任何决定。** 后续必须由 **Human Decision** 裁定；
**不得**由 Agent 自行选择最终 acceptance model ／ integrity algorithm ／ compatibility policy。

---

**10. Explicit Non-Decisions**

本 Review **不创建**：

```
JSON Schema
sample package ／ real manifest.json
parser ／ serializer ／ runtime validator
import service
database schema
Adapter ／ connector
filesystem security implementation
hash ／ checksum ／ signature algorithm 实现
signing infrastructure
retry ／ queue ／ logging implementation
source-system mapping
new canonical field ／ entity ／ enum
```

**未**新增 status enum，**未**新增 Validation Reason，**未**发明任何 JSON property name，
**未**把任何 illustrative placeholder 当作 authoritative property name，
**未**把任何 `Inherited Constraint` 重新包装成 Human option。

---

**11. Current Status（本 Review 时点）**

```
Snapshot / Import Contract overall = DESIGN PENDING
  Package Envelope ／ Atomicity Boundary ／ Immutability Boundary ／ Analysis Run Linkage = DESIGN RESOLVED
  Serialization Format             = DESIGN RESOLVED
  Physical Dataset Layout          = DESIGN RESOLVED
  Field Carrier Mapping            = DESIGN RESOLVED
  Final Import Contract            = DESIGN PENDING   ← 本 Review 对象；未关闭
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT

Package Structural Failure
  ≠ Capability Evidence Unavailable
  ≠ Business DATA_INCOMPLETE

本 Review 不选择任何 Option。
本 Review 未创建任何 runtime artifact。
```

---

**12. Revision Log（本 Review 的独立复核修正 —— review-only）**

> 本节记录**review-only 修正**，用于说明「候选 ／ 依赖 ／ closure 判定前提」表达层面的更正。
> 分两批：**`IR-65-01` ～ `IR-65-05`**（Independent Review）与
> **`FIC-13` ～ `FIC-15`**（Coordinator Re-Review）。
> **仍不选择任何方案**，**不**登记 final policy，**不**改变任何 status，**不**创建 runtime artifact，
> **不**新增 Validation Reason ／ property name ／ carrier。

| 修正项 | 主题 | 本次变更 |
| --- | --- | --- |
| `IR-65-01` | 依赖 ／ closure 判定 | 新增 **`§7.1 Claimable Design-Closure Levels`**（`CL-1` ／ `CL-2` ／ `CL-3` 与「记录依赖 ≠ 满足依赖」）；重写 `I-10` ／ `I-17`；扩展 `I-5` ／ `I-8` ／ `I-11` ／ `I-14` ／ `I-18`；新增 `I-21`（跨选择无阻塞矛盾核验）；补齐 `IG-self-C` 的**可审计信任前提 ／ 输入边界 ＋ closure claim 范围**（`D.5` ／ `Decision 7`）；新增 `DEP-10`（FCM residual 只在其自身 closure 范围内成立）与 `IS-25` |
| `IR-65-02` | acceptance-time 一致性 | 新增 **`IS-24`** 与 **`RIF-13`**：验证结果**必须**绑定实际被接受、随后供 Analysis Run 使用的**同一 package 内容视图**，无法建立一致性时 **fail closed ／ not evaluable**；纳入 `I-14`；`RIF-2` ／ `RIF-9` ／ `Decision 9` ／ `Decision 10` 补齐边界（`MG-*` 只覆盖 **post-accept**；`CF-*` **不**替代该义务） |
| `IR-65-03` | alias ／ target identity | `IS-17` **拆为** `IS-17a`（target-equivalence **识别规则** = `open`）与 `IS-17b`（已确认同一 target identity ⇒ 适用 `IC-1`，**`Inherited Constraint`**）；Section 4-C 为 `PN-1` ／ `PN-2` ／ `PN-3` 增加**共同适用前提**（alias ／ link 的拒绝或安全解析边界；**不得**因低成本豁免 boundary 与 independence）；更正 `DEP-5`（target identity ＋ uniqueness ＋ boundary，**不**只 presence）与 `I-7` |
| `IR-65-04` | version ↔ unknown property | 更正 **`DEP-1`**：**先**由受支持版本 ／ 兼容规则确定 applicable contract 与 known member set，**再**应用该 contract 的 unknown policy；**version-token 匹配 ≠ field policy**；更正 `Decision 2` trade-off 与 `Decision 1` 前提；同步 `RIF-7` ／ `I-5` ／ `I-11`。**未**制定新的演进方案、**未**偏向任何 `VC-*` ／ `UX-*` |
| `IR-65-05` | signature ／ trust input | `D.2` 标注 **digital signature ／ 混合为条件性可行**：**必须**确定 verification key 的信任来源 ／ 配置边界 ／ 绑定、与 evidence representation 及 Manifest self-integrity 的依赖、以及 deterministic verification 的完成条件；新增 **`DEP-11`**；扩展 `Decision 5` ／ `RIF-6` ／ `I-8` ／ `I-18`；明确 **content integrity ≠ identity ／ authenticity**。**未**选择 signature、**未**引入 PKI ／ secrets ／ signing infrastructure |
| `FIC-13` | `CL-2` ／ `CL-3` 收紧 | `§7.1` 重写 **`CL-2`**（**仅限 category ① parameterized external input contract**：contract semantics 已完整、同一输入下 conforming importers 结果唯一；运行时 external parameter 可缺失且缺失行为已确定）与 **`CL-3`**（**category ② unfinished design prerequisite**：新 carrier ／ sidecar ／ literal、未定义 trust mechanism、未完成 key-management ／ security contract ⇒ **completion gate 必须已满足，仅已登记不构成 PASS**）；新增**判别表**、**判定测试**与 5 条强制规则；同步 `D.5`、`DEP-8` ／ `DEP-9` ／ `DEP-11`、`RIF-6`、`I-10` ／ `I-17` ／ `I-18` ／ `I-21`、`Decision 7` ／ `Decision 11` |
| `FIC-14` | acceptance-time Human Decision path | `IS-24` 明确 **`IC + open` 的归属**（inherited = 必须绑定同一稳定视图 ＋ fail closed；open = contract-level guarantee ／ detection boundary 与报告表述）；新增 **`Decision 10A`（acceptance-time stable view ／ binding guarantee）** 与 **`Decision 10B`（post-accept mutation）** 双子边界；`I-14` **必须**显式映射 10A ＋ 10B；`RIF-13` 增加 **二选一规则**（若 Human 判定已被 inherited 唯一确定 ⇒ `IS-24` 改标 `IC`、`10A` 折叠；二者**不得**同时成立）。**未**设计 lock ／ transaction ／ atomic rename，**未**新增体系 |
| `FIC-15` | closure-count consistency | 统一 Review 内所有 closure-count 表述为 **`I-1` ～ `I-18` ＋ `I-21`（MANDATORY，共 19 项）＋ `I-19` ／ `I-20`（objectives，共 2 项）**，并注明 `I-21` 为 mandatory（编号位于 objectives 之后，属编号顺序而非类别差异）；同步 `RIF-12` 与 `Decision 12` |
| `FIC-16` | `CL-2` 「only」语义统一 | **删除**「implementation detail residual 可作为 `CL-2`」表述：`§7.1` 强制规则 2 改为**三分**——不影响 acceptance semantics 的 residual ⇒ **non-blocking implementation residual（outside the FIC acceptance criterion）**，**既不归入 `CL-2` 也不作为 closure 依据**；contract semantics 已完整且无未决输入的 design criterion ⇒ **`CL-1`**；影响 acceptance semantics 的 contract prerequisite ⇒ 按类别 ① ／ ② 判 `CL-2` ／ `CL-3`。同步 `CL-1` 定义、`§8` closure 强度约定与 **`D.5`** 第 2 项。**`I-17` ／ `Decision 11` 更正**：**(i)** 本次实际登记 authoritative known member set（或 literal set）并完成 binding ⇒ `CL-1`；**(ii)** 仅决定「后续另开 naming decision」⇒ 该 naming decision **实际完成前为 `CL-3`**（「另开 naming decision」本身不产生 known member set）；**(iii)** parameterized external member-set contract 满足类别 ① ⇒ `CL-2` |
| `PR-META-01` | PR metadata cleanup | 更新 PR body 的 **current summary ／ Validation ／ Next gate**，使其反映 latest HEAD（coverage 改为 `IS-* 25` ／ `RIF-* 13` ／ `DEP-* 11` ／ `I-* 21`；Next gate 改为 Coordinator final check → Human Decision，**Codex independent review 已完成**）。**未**修改任何历史 review comment |

**本次修正的 review-only 边界（自我核验）：**

```
未选择任何 Human option（acceptance model ／ algorithm ／ compatibility ／ path policy ／ status usage）
未登记任何 final policy
未新增 Validation Reason ／ status enum ／ JSON property name ／ carrier ／ sidecar
未修改已注册 policy、历史 Review ／ Human Decision ／ Closure 记录
未修改 §4.3.* ／ §4.4.* 任何已注册 policy 的实质内容（本次改动仅位于本 Review 段落之内）
未创建 runtime code ／ schema ／ sample package
未改变任何 status、未选择 merge、未准备 Human Decision 结论
```

`Final Import Contract` **仍为 `DESIGN PENDING`**；`Snapshot / Import Contract overall` **仍为 `DESIGN PENDING`**；
`Adapter Boundary` **仍为 `DESIGN PENDING`**；`POC Design v0.2` **仍为 `DRAFT`**。

---

#### 4.3.21 Status Boundary

`Snapshot / Import Contract` **整体现为 `DESIGN RESOLVED`** ——
**八层全部 `DESIGN RESOLVED`**（见 **§4.3.29** 的 overall re-check）。

**历史（原 `Package Envelope` Task 时点）：** 该 Task **仅**完成其第一层：Package Envelope、
Import Atomicity、Immutability、Analysis Run linkage。

`DESIGN RESOLVED` 的层级**仅**表示其 **conceptual boundary 已定义**，
**不表示**：

- import implementation exists
- data validated
- tested

> **current-state 更新：** `Serialization Format` 已由 **PR #51 Human Decision** 登记 JSON strategy、
> 并经 **PR #52 Closure Re-run = `PASS`** 后为 **`DESIGN RESOLVED`**（见 **§4.3.22**），
> 因此 `serialization format determined` 已**移出**上述「不表示」清单。
>
> **current-state 更新（本层 Closure）：** `Physical Dataset Layout` 已由 **PR #53 Human Decision** 登记、
> 并经 **本层 Closure Validation = `PASS`** 后为 **`DESIGN RESOLVED`**（见 **§4.3.23** ／ **§4.3.24**），
> 因此 `physical dataset layout determined` 已**移出**上述「不表示」清单。
>
> **current-state 更新（Field Carrier Mapping）：** `Field Carrier Mapping` 的 **Human Decision 已登记**
> （见 **§4.3.25**）；**Decision Gap `G-1` ／ `G-2`** 已由 **Supplementary Human Naming Decision** 解除
> （approved literal names 已登记），**Closure Re-run = `PASS`**（见 **§4.3.27**），
> 因此现为 **`DESIGN RESOLVED`** —— `field carrier mapping determined` 已**移出**上述「不表示」清单。
>
> **current-state 更新（Final Import Contract ＋ overall）：** `Final Import Contract` 已由
> **Issue #66 Human Decision（Bundle 1 ～ 6）** 登记（见 **§4.3.28**），并经
> **本层 Closure Validation = `PASS`**（`I-1` ～ `I-18` ＋ `I-21` = ALL `PASS`；`CL-3` = 0；
> Blocking Contradiction = NONE）后为 **`DESIGN RESOLVED`**（见 **§4.3.29**）；
> 因此 **`Snapshot / Import Contract` overall 现为 `DESIGN RESOLVED`**
> —— `import contract determined` 已**移出**上述「不表示」清单。
> `Adapter Boundary` 为**独立子领域**，**不在本 closure 范围**；其 **conceptual design 已由 Issue #90 Closure Validation = `PASS`** 登记为 **`DESIGN RESOLVED`**（见 **§4.6.21** ／ **§4.6.22**），其 **runtime ／ source-specific realization 仍为 `NOT IMPLEMENTED`**。

#### 4.3.22 Serialization Format Design（Registered Strategy & Representation Policy）

**Registration Status：`REGISTERED`** ——
依据 **PR #51 Human Decision**（决定 2 ／ 4 ／ 5 ／ 6 ／ 7 ～ 15），见上方 **Human Decision Record**。

**补充登记（`C-10`）：** 依据 **`G-S1` 补充 Human Decision**（决定 5），见上方
**Human Decision Record（`G-S1` 补充决定）** 与 **Serialization Format Closure Re-run Record**。

**current representation policy：**

```
C-1 ～ C-10 = REGISTERED
```

**A. Serialization Strategy（正式登记）**

```
Serialization Format  = JSON
POC v0.2 Strategy     = single JSON serialization strategy
Snapshot Manifest     = independent artifact ＋ JSON serialization
Business datasets     = JSON serialization
```

**NOT SELECTED：**

```
JSONL    = NOT SELECTED FOR POC v0.2
CSV      = NOT SELECTED
Parquet  = NOT SELECTED
Hybrid   = NOT SELECTED
```

**Single-Format Boundary：** **不得**允许任何 logical dataset 自行选择其他 serialization format。
⇒ `R-2` 的 **cross-format 一致性问题 `NOT INTRODUCED`**；同一 canonical logical type
**必须**在所有 JSON serialized dataset 中保持**同一 representation rule**。

**Manifest Boundary（保持）：**

```
Snapshot Manifest  ≠  business dataset
```

二者使用**同一 serialization format family**（JSON）。本小节**不定义**：
manifest filename ／ path ／ directory ／ package container ／ archive ／
business dataset filename ／ file-per-dataset layout。

**B. Required Properties（正式登记）**

```
R-1   Deterministic Parsing               = MANDATORY SERIALIZATION CLOSURE CRITERION
R-2   Stable Field Representation         = MANDATORY SERIALIZATION CLOSURE CRITERION
R-3   Logical Type Preservation           = MANDATORY SERIALIZATION CLOSURE CRITERION
R-4   Missing ≠ Present-with-Default      = MANDATORY SERIALIZATION CLOSURE CRITERION
R-5   Dataset-Level Absence Expressible   = MANDATORY SERIALIZATION CLOSURE CRITERION
R-6   Manifest Metadata Carriage          = MANDATORY SERIALIZATION CLOSURE CRITERION
R-7   Integrity Evidence Carriage         = MANDATORY SERIALIZATION CLOSURE CRITERION
R-8   Reproducibility                     = MANDATORY SERIALIZATION CLOSURE CRITERION
R-9   Contract Version Expressibility     = MANDATORY SERIALIZATION CLOSURE CRITERION
R-10  Adapter Neutrality                  = MANDATORY SERIALIZATION CLOSURE CRITERION

R-11  Human Inspectability                = POC DESIGN OBJECTIVE
R-12  Implementation Simplicity           = POC DESIGN OBJECTIVE
```

`R-11` ／ `R-12` **必须评估**，但**不作为**独立 hard closure blocker；
**不得**把主观判断变成不可验证的 closure Gate。

**C. `C-1` ～ `C-9` JSON Representation Policy（正式登记）**

| # | Rule | Registered policy |
| --- | --- | --- |
| **C-1** | Text encoding | `UTF-8`；**without BOM**；**不得**依赖 system locale ／ platform default encoding |
| **C-2** | Missing ／ null | JSON `null` = **explicit missing ／ unavailable serialized value**；**不得**用 `0` ／ `false` ／ `""` ／ `"UNKNOWN"` 代替 missing；`property omission` = field **not serialized**，其业务语义**必须**由 **canonical requiredness ＋ business applicability ＋ existing validation semantic** 判断；**valid absence ／ not produced by design 允许 property omission**；serializer **不得**猜业务语义 |
| **C-3** | `DATE` | `YYYY-MM-DD`；**禁止** locale-specific date ／ `MM/DD/YYYY` ／ `DD/MM/YYYY` ／ 自然语言日期 |
| **C-4** | `TIMESTAMP` | ISO 8601 ／ RFC 3339 compatible；**必须**携带 **explicit UTC offset 或 `Z`**；**禁止** silent timezone inference ／ system-local timezone assumption ／ timezone guessing；**business timezone policy = `NOT DEFINED`**；**不得新增** freshness policy |
| **C-5** | `DECIMAL_QUANTITY` ／ `NON_NEGATIVE_QUANTITY` ／ `RATIO` ／ `PERCENTAGE` | **base-10 decimal string**；**禁止** binary floating-point ／ locale comma ／ thousands separator ／ scientific notation；serializer **不得** round ／ quantize ／ truncate；**decimal precision = `NOT DEFINED`**；**fixed scale = `NOT DEFINED`**；**quantity rounding = `NOT DEFINED`** |
| **C-6** | Boolean | `BOOLEAN` canonical representation = **`NOT APPLICABLE FOR CURRENT POC`**（canonical model 无 `BOOLEAN` logical type）；**不得**据此新增 BOOLEAN canonical field |
| **C-7** | Canonical enum ／ status | 既有 canonical literal 的 **exact string representation**；**case-sensitive**；无 silent normalization ／ trim-based semantic conversion ／ synonym mapping；source-specific vocabulary **仍保持 source-specific**；尤其 `sourcing_status` **不得**被 serializer 自动 canonical 化 |
| **C-8** | Empty dataset | `dataset not included` **≠** `dataset included with zero records`；Manifest 是 dataset presence 的 **authoritative package-level evidence**；`included ＋ record_count = 0` = **structurally valid empty dataset**；**exact dataset envelope 不由本小节定义** |
| **C-9** | JSON parsing ／ escaping | **strict parse**；**禁止** duplicate object keys ／ comments ／ trailing comma ／ `NaN` ／ `Infinity` ／ implementation-specific extension；standard JSON escaping；**object member order 不得具有 business semantic**；**禁止** import fix-up：silent trim ／ silent case conversion ／ silent Unicode normalization ／ silent numeric coercion |
| **C-10** | Identity ／ text scalar representation | `IDENTIFIER` = **JSON string**；`ANALYSIS_RUN_ID` = **JSON string**；`TEXT_CONTEXT` = **JSON string**；transport-level `snapshot_package_id` = **JSON string**；**所有 identity value treated as opaque string**；**必须保持原始 identity value**；**禁止** semantic coercion ／ normalization（numeric coercion ／ trim ／ case conversion ／ leading-zero removal ／ numeric interpretation ／ synonym conversion ／ 作为 semantic fix-up 的 Unicode normalization）；`TEXT_CONTEXT` **必须**保持 **exact textual value** 并使用 standard JSON string escaping；**不得定义** identifier `regex` ／ `length` ／ `prefix` ／ numeric-only 约束 ／ UUID 要求 ／ generation algorithm ／ source-system identifier format |

> **`C-10`（Identity ／ Text Scalar Representation）** 由 **`G-S1` 补充 Human Decision**（决定 5）授权登记，
> 用于关闭 PR #52 第一次 Closure Gate 的 `G-S1`；**`C-1` ～ `C-9` 的 semantic 未修改**。
> `C-10` **仅**固定 JSON scalar representation，**不新增**任何 business semantic，
> 也**不**新增任何 identifier business constraint。

```
C-1 ～ C-10 = REGISTERED
```

**D. Determinism Boundary（正式登记）**

```
Deterministic Parsing  ≠  Byte-for-byte Canonical JSON Encoding
```

要求：**同一 compliant JSON input 必须产生相同 canonical semantic value**。

**不要求**（且本小节**不定义**）：object key canonical order ／ canonical byte ordering ／
JSON canonicalization algorithm。若未来 **integrity contract** 需要 **byte-level hash ／ canonicalization**，
归 **`Final Import Contract`**。

**E. Registration Boundary**

- 本小节**不新增** canonical entity ／ canonical business field，**不修改** `BR-*`。
- 本小节**不代表** implementation：**未**创建 JSON Schema ／ sample JSON ／ parser ／ runtime validation。
- 本小节**不定义**：directory tree ／ filename ／ container ／ archive ／ field ／ property mapping ／
  dataset envelope ／ integrity algorithm ／ contract version evolution policy。
- `Serialization Format` 的 **status 变更**由 **Serialization Format Implementation Record** 的
  **conditional closure gate** 结果决定。

---

#### 4.3.23 Physical Dataset Layout Design（Registered Layout Policy）

**Registration Status：`REGISTERED`** ——
依据 **PR #53 Human Decision**（决定 1 ～ 9），见上方 **Human Decision Record**。

**current layout policy：**

```
Package Container    = Flat Directory Package
Artifact Granularity = one included logical dataset → one independent JSON artifact
Manifest Placement   = package root
Manifest Filename    = manifest.json
Nested Directories   = NOT ALLOWED FOR POC v0.2
```

**A. Package Container（正式登记）**

```
Package Container = Flat Directory Package
Package root      = 当前 POC Snapshot Package 的物理边界
```

**NOT SELECTED：**

```
Structured Directory Package = NOT SELECTED
Archive Package              = NOT SELECTED
其他特殊 container            = NOT SELECTED
```

**Flat Directory Boundary：** `Flat Directory` **本身不保证** runtime atomicity ／ runtime immutability ／
integrity verification；**不得**由本层实现这些 mechanism。

**B. Artifact Granularity（正式登记）**

```
one included logical dataset = one independent JSON artifact
```

**NOT SELECTED：** aggregated business data artifact；dataset sharding。

```
one artifact per logical dataset  ≠  partial package acceptance
```

单个 artifact 的问题是否导致**整个** package reject，**仍由 `Final Import Contract` 定义**。

**C. Manifest Placement ／ Filename（正式登记）**

```
Snapshot Manifest placement = package root
Snapshot Manifest filename  = manifest.json
manifest.json               = technical filename contract
                            ≠ business semantic source
```

`manifest.json` **不得**承载 business identity ／ business status ／ dataset role ／ scope semantic ／
provenance semantic ／ `snapshot_package_id` semantic。

**NOT SELECTED：** fixed manifest subdirectory；external entry-point locator。

**D. Dataset Artifact Naming（正式登记 —— 最低 physical naming requirements）**

```
artifact 位于 package root
filename 在当前 package 内唯一
serialization extension = .json
不得使用保留名称 manifest.json
```

```
Manifest-declared artifact reference = authoritative physical association
filename                             = physical convenience only
```

**不得定义**：role-derived mandatory filename template ／ opaque filename generation algorithm ／
dataset ID generation rule。**不得**让 filename 成为 `logical dataset role` 的 authoritative source。

**E. `logical dataset role` → physical artifact association（正式登记）**

```
logical dataset role → physical artifact reference = REQUIRED
```

该关联**必须**由 **Snapshot Manifest 显式建立**。**禁止**依赖：

```
filename inference
directory name inference
file ordering
filesystem discovery heuristic
```

**本层只决定 association MUST EXIST**；具体 Manifest JSON property name ／ nested structure ／
schema representation 属 **`Field Carrier Mapping`**。

**F. Presence Semantics（正式登记）**

```
included 且 record_count = 0  →  对应 JSON artifact REQUIRED
not included                  →  对应 artifact NOT REQUIRED
not included  ≠  included with zero records
```

**不定义** empty dataset 的 JSON body（`[]` ／ `{}` ／ 其他 dataset envelope）—— 属 **`Field Carrier Mapping`**。

**G. Nested Directory Boundary（正式登记）**

```
current package layout = single package root
                       + manifest.json
                       + root-level business JSON artifacts
nested directories     = NOT ALLOWED FOR POC v0.2
```

该限制**只**约束 Snapshot Package **内部** physical layout；**不限制**其在宿主 filesystem 的**外部存放位置**。
未来出现**真实需求**时，**可以**通过**新的明确 Design Decision** 重新评估 nested directory。

**H. Path Scope Boundary（正式登记 —— `L-11`）**

所有 physical artifact reference **必须**：

```
relative to package root
```

且其 **logical resolved target** **必须**位于**当前 Snapshot Package boundary 内**。
合法 layout **不得**依赖：

```
absolute path
external path / URI
package-external artifact
```

```
Layout                = defines valid path scope
Final Import Contract = validates / rejects violations
```

**不得**在本层实现：path normalization algorithm ／ traversal detection algorithm ／
`..` rejection mechanism ／ symlink resolution algorithm ／ symlink rejection timing ／
platform-specific path parser ／ runtime rejection behavior。

**I. Required Layout Properties（正式登记 —— `L-1` ～ `L-11`）**

```
L-1   Package Boundary Unambiguous        = MANDATORY CLOSURE CRITERION
L-2   Manifest Discoverability            = MANDATORY CLOSURE CRITERION
L-3   Dataset Artifact Discoverability    = MANDATORY CLOSURE CRITERION
L-4   Logical / Physical Separation       = MANDATORY CLOSURE CRITERION
L-5   Presence Semantics Preservation     = MANDATORY CLOSURE CRITERION
L-6   Package Atomicity Compatibility     = MANDATORY CLOSURE CRITERION（DESIGN COMPATIBILITY ONLY）
L-7   Package Immutability Compatibility  = MANDATORY CLOSURE CRITERION（DESIGN COMPATIBILITY ONLY）
L-8   Reproducibility                     = MANDATORY CLOSURE CRITERION
L-9   Serialization Compatibility         = MANDATORY CLOSURE CRITERION
L-10  Downstream Neutrality               = MANDATORY CLOSURE CRITERION
L-11  Path Scope Integrity                = MANDATORY CLOSURE CRITERION（PATH SCOPE ONLY）
```

`L-6` ／ `L-7` **只**验证 **DESIGN COMPATIBILITY**，**不是** runtime mechanism completion：
layout **不得**要求 cross-package composition ／ silent mixing ／ 依赖 package 外 mutable artifact ／
partial overwrite ／ 破坏 accepted-package immutability semantic；但本层**不得实现** transaction ／
locking ／ atomic filesystem move ／ storage engine ／ object storage semantics ／ upload protocol ／
runtime immutability enforcement。

`L-11` **只**定义合法 path scope；**不得**演变成 **Security Implementation**。

**J. Registration Boundary**

- 本小节**不新增** canonical entity ／ canonical business field；**不修改** `BR-*` ／ Validation Taxonomy ／
  Master Data Mapping ／ `Serialization Format` policy。
- 本小节**不代表** implementation：**未**创建 package directory ／ JSON sample ／ `manifest.json` 实际文件 ／
  dataset artifact ／ ZIP ／ archive ／ JSON Schema ／ parser ／ runtime validator ／ Adapter。
- 本小节**不定义**：Manifest JSON property name ／ dataset envelope ／ record envelope ／
  business record structure ／ source field → JSON property mapping ／
  canonical field → JSON property mapping ／ Stable Source Evidence Locator physical carrier ／
  hash ／ checksum ／ signature algorithm ／ byte-level canonicalization ／
  runtime acceptance ／ rejection algorithm ／ contract compatibility policy。
- `Physical Dataset Layout` 的 **status 变更**由 **Physical Dataset Layout Closure Validation Record**
  的 conditional closure gate 结果决定。

---

#### 4.3.24 Physical Dataset Layout Closure Validation Record

**Closure Validation Result：`PASS`**

**State Transition：`Physical Dataset Layout` = `DESIGN PENDING` → `DESIGN RESOLVED`**

**A. Conditional Closure Gate（PR #53 Human Decision 决定 10）**

| # | 条件 | 结果 |
| --- | --- | --- |
| 1 | Human-approved layout decisions = fully registered | **`PASS`**（见 **§4.3.23** A ～ J） |
| 2 | `L-1` ～ `L-11` = ALL PASS | **`PASS`**（见下方 B） |
| 3 | New Blocking Contradiction = NONE | **`PASS`** |

**B. `L-1` ～ `L-11` 逐项验证**

| # | Property | 验证依据 | 结果 |
| --- | --- | --- | --- |
| `L-1` | Package Boundary Unambiguous | single package root（**§4.3.23** A ／ G）；`Snapshot Package ≠ Analysis Run`（**§4.3.4**）；cross-snapshot mixing prohibition（**§4.3.7**） | **`PASS`** |
| `L-2` | Manifest Discoverability | Manifest = package root ＋ 保留名称 `manifest.json`（**§4.3.23** C） | **`PASS`** |
| `L-3` | Dataset Artifact Discoverability | artifact 位于 package root ＋ filename package 内唯一 ＋ Manifest 显式 `role → artifact`（**§4.3.23** D ／ E） | **`PASS`** |
| `L-4` | Logical ／ Physical Separation | filename ／ artifact path **不得**作为 logical dataset role ／ business status ／ scope ／ provenance 的 authoritative source（**§4.3.23** D ／ E） | **`PASS`** |
| `L-5` | Presence Semantics Preservation | `included ＋ record_count = 0` → artifact REQUIRED；`not included` → NOT REQUIRED；Manifest 为 authoritative presence evidence（**§4.3.23** F；**§4.3.13** ／ **§4.3.14**） | **`PASS`** |
| `L-6` | Package Atomicity Compatibility | **DESIGN COMPATIBILITY ONLY** —— layout 不要求 cross-package composition ／ silent mixing ／ partial overwrite；**未**实现 runtime mechanism（**§4.3.23** I；**§4.3.6**） | **`PASS`** |
| `L-7` | Package Immutability Compatibility | **DESIGN COMPATIBILITY ONLY** —— layout 不依赖 package 外 mutable artifact、不破坏 accepted-package immutability semantic；**未**实现 runtime enforcement（**§4.3.23** I；**§4.3.5**） | **`PASS`** |
| `L-8` | Reproducibility | deterministic discovery（fixed manifest entry ＋ explicit association）＋ relative-to-package-root reference（**§4.3.23** B ／ C ／ D ／ H） | **`PASS`** |
| `L-9` | Serialization Compatibility | layout 只引用 `.json` artifact；**未**改变 `C-1` ～ `C-10`、**未**选择其他 format（**§4.3.23** D ／ J；**§4.3.22**） | **`PASS`** |
| `L-10` | Downstream Neutrality | **未**采用 aggregated artifact；**未**定义 dataset ／ record envelope；`Field Carrier Mapping` ／ `Final Import Contract` boundary 保持开放（**§4.3.23** B ／ E ／ F ／ J） | **`PASS`** |
| `L-11` | Path Scope Integrity | **PATH SCOPE ONLY** —— artifact reference **必须** relative to package root 且 resolved target 位于 package boundary 内；absolute ／ external path ／ URI **不得**作为 accepted package 组成部分（**§4.3.23** H） | **`PASS`** |

**C. Non-Implementation Confirmation**

**未**创建 package directory ／ JSON sample ／ `manifest.json` 实际文件 ／ dataset artifact ／
ZIP ／ archive ／ JSON Schema ／ parser ／ runtime validator ／ Adapter；
**未**定义 Manifest property name ／ dataset envelope ／ record envelope ／
source field → JSON property mapping ／ canonical field → JSON property mapping ／
hash ／ checksum ／ signature algorithm ／ byte-level canonicalization ／
runtime acceptance ／ rejection algorithm ／ path validation implementation ／ contract compatibility policy。

**D. Downstream Boundary（保持）**

```
Field Carrier Mapping              = DESIGN PENDING
Final Import Contract              = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

**E. Historical Preservation**

PR #53 `Physical Dataset Layout Design Review（Review Finding）` 与 `Human Decision Record`
**完整保留**，包括 **`执行状态（PR #53 Human Decision 时点）`** 中的
`Physical Dataset Layout = DESIGN PENDING` —— 该值时点语义**未被回写**；
**未**把「**本 Review 不选择任何 Option。**」改写为 Review 已选择 layout。

**执行状态（本 Closure Validation 时点）**

```
Physical Dataset Layout                     = DESIGN RESOLVED
Human Decision                              = RECORDED
Physical Dataset Layout Design Registration = REGISTERED
Physical Dataset Layout Closure             = PASS
Runtime Implementation                      = NOT YET EXECUTED

Field Carrier Mapping                       = DESIGN PENDING
Final Import Contract                       = DESIGN PENDING
Snapshot / Import Contract overall          = DESIGN PENDING
Adapter Boundary                            = DESIGN PENDING
POC Design v0.2                             = DRAFT
```

`Physical Dataset Layout Design Registration` ／ `Physical Dataset Layout Closure` 属 **design 层**结果；
`Runtime Implementation` 指 **runtime artifact**（package directory ／ dataset artifact ／ parser ／
validator 等），本层**未**创建 —— **design registration ≠ runtime implementation**。

---

#### 4.3.25 Field Carrier Mapping Design（Registered Carrier Policy）

**Registration Status：`REGISTERED`** ——
依据 **Field Carrier Mapping Human Decision Record**（决定 1 ～ 12）与
**Supplementary Human Naming Decision（`G-1` ／ `G-2`）**，见上方。

本小节登记 **authoritative current policy**；**`Field Carrier Mapping` 现为 `DESIGN RESOLVED`** ——
closure gate 已由 **Closure Re-run = `PASS`** 满足（见 **§4.3.27**）。

> **命名边界：** 本小节登记的 literal 名称**仅限** Human 已批准者
> （见 **Supplementary Human Naming Decision**）；**不得**由 Agent 扩展、推断或新增其他
> property ／ grouping ／ namespace 名称。

**A. Manifest Carrier Policy（正式登记）**

```
Manifest Carrier Model = M-B Grouped Nested Manifest
  package-level metadata group  ≠  dataset collection group   （物理分组，boundary 已固定）
```

**（1）Manifest must express —— 总体 semantic set（依 `§4.3.8`）：**
`snapshot_package_id` ／ contract version ／ export ／ package creation time ／
environment ／ evidence classification ／ included logical datasets ／ dataset-level provenance reference ／
dataset-level record count ／ integrity evidence ／ package completeness state。

> `§4.3.8` 的**总体 semantic set** **不等于** `M-B` 的 **package-level group** —— 二者**必须**分开解读。

**（2）package-level group —— package-scoped concepts（literal 名称由 Human 批准）：**

| concept | approved literal |
| --- | --- |
| grouping（package-level block） | `"package"` |
| snapshot package identity | `"snapshot_package_id"` |
| contract version | `"contract_version"` |
| export ／ package creation timestamp | `"created_at"` |
| environment | `"environment"` |
| evidence classification | `"evidence_classification"` |
| package completeness | `"completeness_state"` |

**（3）dataset collection ／ dataset-entry scope（literal 名称由 Human 批准）：**

| concept | approved literal |
| --- | --- |
| grouping（dataset collection） | `"datasets"` |
| logical dataset role | `"role"` |
| artifact reference | `"artifact"` |
| record count | `"record_count"` |
| dataset provenance reference | `"provenance_ref"` |
| integrity evidence（dataset-artifact scope） | `"integrity_evidence"` |

```
dataset-artifact integrity evidence  →  "integrity_evidence"（dataset-entry scope，NOT package block）
integrity algorithm                  →  Final Import Contract
```

**分组 boundary（已固定）：** `"package"` 与 `"datasets"` 为**物理上不同**的 group；
dataset-scoped concept **必须**与**对应 logical dataset entry** 关联，**不得**上提到 `"package"`。

**本小节登记的 literal 名称仅限上表**（`G-1` 已由 **Supplementary Human Naming Decision** 解除）；
**不得**由 Agent 扩展、推断或新增其他名称。

**B. Dataset Entry Policy（正式登记）**

```
Dataset Entry Model   = D-A array of dataset entry objects
  collection literal  = "datasets"
  entry  properties   = "role" ／ "artifact" ／ "record_count" ／ "provenance_ref" ／ "integrity_evidence"
one included logical role → one authoritative artifact association   （INVARIANT）
```

- role ／ artifact reference ／ presence metadata 对**同一 logical dataset scope** **必须** **确定、唯一、可判定** 地关联；
- **不得**依赖 filename inference ／ ordering ／ discovery heuristic；
- **inclusion 的物理表示** = 该 logical dataset role 的 entry **出现在 `"datasets"` collection 内**；
  **不引入**独立的 `"included"` boolean；
- runtime 如何检测 ／ reject duplicate 或 conflicting entry 属 **`Final Import Contract`**。

**C. Dataset-Level Metadata Authority（正式登记）**

```
dataset-level metadata authoritative carrier = Snapshot Manifest
business dataset artifact 中 不得 重复 dataset-level metadata
⇒ business dataset artifact 不因 dataset metadata 引入 envelope
```

**D. Business Dataset Top-Level Carrier（正式登记）**

```
top-level carrier = B-A bare record array
included ＋ record_count = 0  →  对应 artifact REQUIRED，payload = 空 record array
                                 （可判定的 empty records representation）
not included                  →  对应 artifact NOT REQUIRED
not included                  ≠  included with zero records
inclusion 的物理表示           = 该 role 的 entry 出现在 Manifest "datasets" collection 内
                                 （不引入独立的 "included" boolean）
```

**Presence boundary（恢复既有 `§4.3.23` F policy）：** `not included` **只**表示**不要求**对应 artifact 存在；
本层**不**断言该 artifact **不得存在**，也**不**定义「目录中存在未被 Manifest include ／ reference 的
额外 JSON artifact」时的处理 —— 其 acceptance ／ rejection 属 **`Final Import Contract`**。

**E. Record Carrier（正式登记）**

```
record = JSON object（POC v0.2 强制）
R-B positional record = NOT ADOPTED
```

PR #61 的 `RF-X6` **作为 review evidence 保留**；**positional branch 不进入 current POC v0.2 design**。

**F. Record-Level Carrier Metadata Boundary（正式登记）**

```
record-level technical ／ carrier metadata = ALLOWED
必须进入受控 reserved metadata namespace
不得与 canonical business fields 任意混杂
```

**reserved namespace 名称（Human 批准）= `"_meta"`** ——
`"_meta"` **仅**用于已批准的 record-level technical ／ carrier metadata，
**不得**被视为 canonical business field，**不得**与 canonical business fields 任意混杂。

`P-A` nested provenance structure 与 `MB-A` basis（与其同一 nested structure）**位于 `"_meta"` 之内**。

**G. Canonical Field Carrier（正式登记）**

```
canonical field identifier  →  JSON property name（直接、稳定）= F-A
不新增 第二层 field-name mapping
```

- **不改变** canonical field semantic；
- **禁止** trim ／ case conversion ／ numeric coercion ／ Unicode normalization 等 **silent fix-up**。

**H. Evidence-Level Provenance Carrier（正式登记）**

```
Evidence-Level Provenance Carrier = P-A record-level nested provenance structure
```

- **必须**关联到**具体 canonical observation ／ context**（**不得**仅绑定整条 record）；
- **必须**支持 `multiple source evidence → one canonical fact` 与
  `one source evidence → multiple canonical outputs`（`K-16`）；
- `dataset-level provenance reference` **≠** `Stable Source Evidence Locator`；
- `record identity` **≠** `source evidence identity`；
- **不要求** locator 为 ERP PK ／ row ID ／ filename ／ JSON line ／ globally unique ID。

**I. Mapping ／ Resolution Basis Carrier（正式登记）**

```
Mapping ／ Resolution Basis Carrier = MB-A（与 provenance association 同一 nested structure）
when applicable —— 仅在发生 semantic mapping ／ resolution 时要求
```

- **必须**能**确定性关联**到具体 canonical input ／ observation；
- `mapping ／ resolution basis` **≠** `business rule`；**不得**新增 business field semantic。

**J. Missing ／ Omission Policy（正式登记）**

```
沿用已登记 C-2：
  JSON null         = explicit missing ／ unavailable serialized value
  property omission = field not serialized
  omission 语义     = canonical requiredness ＋ business applicability ＋ existing validation semantic
  omission          ≠ 自动等于 valid absence
  禁止 sentinel     = 0 ／ false ／ "" ／ "UNKNOWN"
```

**K. Integrity Evidence Carrier（正式登记）**

```
dataset-artifact integrity evidence placement = dataset-entry scope（NOT package block）
integrity evidence 是否 requirement           = 属本层（已登记）
integrity algorithm（hash ／ checksum ／ signature）= Final Import Contract
```

**L. FCM ／ FIC ／ Adapter Boundary**

| 问题 | 归属层 |
| --- | --- |
| Manifest ／ dataset entry ／ business artifact top-level ／ record ／ canonical field carrier | **`Field Carrier Mapping`** |
| record-level carrier metadata namespace boundary | **`Field Carrier Mapping`** |
| dataset-level metadata authority | **`Field Carrier Mapping`** |
| evidence-level locator 与 mapping ／ resolution basis 的 carrier 形态 | **`Field Carrier Mapping`** |
| missing ／ valid absence ／ omission representation policy | **`Field Carrier Mapping`** |
| integrity evidence **放置位置** | **`Field Carrier Mapping`** |
| integrity ／ hash ／ checksum ／ signature **algorithm** | **`Final Import Contract`** |
| unknown ／ undeclared property 的 runtime 行为与验证 | **`Final Import Contract`** |
| runtime acceptance ／ rejection algorithm ／ partial package 处理 | **`Final Import Contract`** |
| byte-level canonicalization ／ canonical byte ordering | **`Final Import Contract`** |
| path normalization ／ traversal ／ symlink ／ path validation 实现 | **`Final Import Contract`** |
| contract version compatibility policy | **`Final Import Contract`** |
| JSON Schema ／ parser ／ serializer ／ validator 实现 | **`Final Import Contract`**（实现，非本层设计） |
| Adapter ／ connector ／ 传输协议 ／ 真实 source field | **`Adapter Boundary`** |

**M. Registration Boundary**

- 本小节**不新增** canonical entity ／ canonical business field；**不修改** `BR-*` ／ Validation Taxonomy ／
  Master Data Mapping ／ `Serialization Format` policy ／ `Physical Dataset Layout` policy。
- 本小节**不代表** implementation：**未**创建 package directory ／ JSON sample ／ `manifest.json` 实际文件 ／
  dataset artifact ／ ZIP ／ archive ／ JSON Schema ／ parser ／ serializer ／ validator ／ Adapter。
- 本小节**仅登记** **Supplementary Human Naming Decision** 明确批准的 literal
  （package-level grouping `"package"` ／ dataset collection `"datasets"` ／ package-scoped properties ／
  dataset-entry properties ／ reserved namespace `"_meta"`）；
  **不得**自行扩展、推断或新增其他 property ／ grouping ／ namespace 名称。
- `Field Carrier Mapping` 的 **status** 由 **latest authoritative closure** ——
  **Field Carrier Mapping Closure Re-run Record**（**§4.3.27**，`PASS`）—— 决定；
  **§4.3.26** 为**首次 failed closure attempt**，**保留为历史时点记录**。

---

#### 4.3.26 Field Carrier Mapping Closure Validation Record

**Closure Validation Result：`NOT SATISFIED`（closure `BLOCKED`）**

**State Transition：`NOT EXECUTED`** ——
`Field Carrier Mapping` **保持 `DESIGN PENDING`**（**未**发生 `DESIGN PENDING → DESIGN RESOLVED`）。

**A. Conditional Closure Gate（Human Decision 决定 12）**

| # | 条件 | 结果 |
| --- | --- | --- |
| 1 | Human decisions fully registered | **`PASS`**（决定 1 ～ 12 已登记，见上方 **Human Decision Record** ／ **§4.3.25**） |
| 2 | `F-1` ～ `F-14` ＋ `F-17` = ALL PASS | **`NOT SATISFIED`** —— **`F-1` = `BLOCKED`**（见 B） |
| 3 | Blocking Contradiction = NONE | **`PASS`**（见 C） |

**B. `F-1` ～ `F-14` ＋ `F-17` 逐项验证**

| # | Criterion | 验证依据 | 结果 |
| --- | --- | --- | --- |
| `F-1` | Manifest carrier model 已显式登记（含 package-level property 集合与 grouping boundary） | `M-B` 的**分组 boundary** 已由决定 1 固定；但 package-level property 与 grouping 的 **authoritative literal 名称**未获授权，且**不能**从既有 approved terminology 唯一确定 | **`BLOCKED`** —— `G-1` |
| `F-2` | `logical dataset role → artifact reference` carrier 形态已登记 ＋ cardinality ／ uniqueness invariant | 决定 2（`D-A` ＋ invariant） | **`PASS`** |
| `F-3` | presence metadata 与 `role → artifact` 可确定、唯一、可判定地关联 | 决定 2 | **`PASS`** |
| `F-4` | business dataset top-level carrier 形态已登记，且与 `K-2` 兼容 | 决定 3（`B-A` bare record array；与 one-artifact-per-dataset 兼容） | **`PASS`** |
| `F-5` | `included ＋ record_count = 0` 与 `not included` 可区分 | 决定 3 ＋ `C-8`（**不**需要新增 MUST-NOT-EXIST 规则） | **`PASS`** |
| `F-6` | record carrier 形态已登记（含是否强制 JSON object ／ 是否允许 carrier-level 属性） | 决定 5（强制 JSON object）＋ 决定 6（carrier-level technical metadata **允许**，须受控 namespace）。**permission 与 boundary 已登记**；namespace **literal 名称**属 `G-2`，不影响本 criterion 的**形态**判定 | **`PASS`** |
| `F-7` | canonical field carrier policy 已登记，且不改变 canonical field semantic | 决定 7（`F-A`；无第二层 mapping；无 silent fix-up） | **`PASS`** |
| `F-8` | carrier 不违反 `C-1` ～ `C-10` | 决定 3 ／ 5 ／ 7 ／ 10（含 `C-2` ／ `C-9` ／ `C-10`） | **`PASS`** |
| `F-9` | dataset-level provenance reference 的 carrier 已登记 | 决定 4（authoritative carrier = `Snapshot Manifest`） | **`PASS`** |
| `F-10` | `Stable Source Evidence Locator` carrier ＋ 与 dataset-level reference 分层不混合 ＋ `K-16` 关联 ／ cardinality | 决定 8（`P-A`；observation-level association；双向 cardinality；record identity ≠ evidence identity） | **`PASS`** |
| `F-11` | `Mapping ／ Resolution Basis` carrier ＋ 确定性关联 | 决定 9（`MB-A`；`when applicable`） | **`PASS`** |
| `F-12` | carrier 层不压平 `valid absence` ／ `missing` ／ `not applicable` 的语义 | 决定 10（沿用 `C-2`；禁止 sentinel） | **`PASS`** |
| `F-13` | carrier 层无 silent fix-up | 决定 7 | **`PASS`** |
| `F-14` | 已知 option combination 的 dependency ／ incompatibility 已显式登记，且无未登记的跨选择冲突 | 见 C（决定 1 ～ 12 组合一致性检查） | **`PASS`** |
| `F-17` | integrity evidence 的 physical carrier（package-level ／ dataset-entry-level 位置与 grouping boundary）已登记，且不与 business field 混淆 | 决定 1（dataset-artifact integrity evidence = **dataset-entry scope**，**NOT** package block；algorithm 未进入本层） | **`PASS`** |

**C. Combination Consistency（决定 1 ～ 12）**

| 检查 | 结果 |
| --- | --- |
| `B-A` ＋ Manifest-authoritative dataset metadata | **一致** —— dataset-level metadata **不**在 artifact 中重复，bare array **无** envelope 需求（决定 3 ＋ 决定 4，无冲突） |
| JSON object record ＋ `F-A` | **一致** —— object record 以 canonical identifier 作 JSON property name（决定 5 ＋ 决定 7） |
| reserved metadata namespace 与 canonical business fields 边界 | **明确** —— 受控 namespace，**不得**任意混杂（决定 6）；**literal 名称**未定（`G-2`） |
| `P-A` ／ `MB-A` 与 `K-16` | **一致** —— observation-level association ＋ 双向 cardinality ＋ basis 与 provenance 同一 nested structure（决定 8 ＋ 决定 9） |
| `C-2` semantics | **未压平** —— omission ≠ 自动 valid absence；无 sentinel（决定 10） |
| integrity carrier | **已定位**（dataset-entry scope）；**algorithm 未越权进入 FCM**（决定 1） |
| Final Import Contract ／ Adapter Boundary | **未被提前设计**（见 **§4.3.25** L） |
| positional branch 相关组合约束 | 决定 5 **不采用** `R-B` → PR #61 `RF-X6` 中的**跨分支**组合约束**不再适用**；`RF-X6` 作为 **review evidence** 保留 |

**D. Design-Objective Evaluation（`F-15` ／ `F-16` —— 非独立 hard blocker）**

| Objective | 评估 |
| --- | --- |
| `F-15` Human Inspectability | **有利** —— grouped nested manifest ＋ bare record array ＋ canonical-identifier property naming，均可直接人工检视 |
| `F-16` Implementation Simplicity | **有利** —— 无 envelope ／ 无第二层 mapping ／ 无 positional contract，结构最小 |

**E. Decision Gap（minimal —— 未授权命名，不得自行决定）**

```
G-1  Manifest 的 exact property name ／ grouping name
     = NOT DETERMINABLE FROM APPROVED TERMINOLOGY
G-2  record-level reserved carrier-metadata namespace 的 exact property name
     = NOT DETERMINABLE FROM APPROVED TERMINOLOGY
```

**判定依据（事实核对）：**

- `§4.3.23` J 与 PR #53 Human Decision Record **明确将 Manifest JSON property name 分配给
  `Field Carrier Mapping`** —— 即本层**本应**定义这些名称；
- 但 **决定 1** ／ **决定 6** **未**提供任何字面名称，且**要求**：若不能从既有 approved terminology
  **唯一确定**，则**不得自行发明** ／ **不得自行选择名称**；
- 既有 approved terminology 中**不存在**可用于唯一推导的名称：
  `§4.3.8` 仅以**语义**列举 Manifest 内容（如 contract version ／ export ／ package creation time ／
  environment ／ evidence classification 均**非** literal identifier）；已登记的 literal 仅有
  `snapshot_package_id` 与 `record_count`；
  **不存在**任何 package-level block ／ dataset collection ／ record-level reserved namespace 的已批准名称。

**最小解除条件（供 Human）：**

1. 授权 Manifest 的 **package-level block 名称**、**dataset collection 名称**，以及 `§4.3.8` 各项对应的
   **JSON property name**；
2. 授权 record-level **reserved carrier-metadata namespace** 的 **JSON property name**。

**Human Decision 后：** 仅需补登上述名称 —— **不需要**新增 carrier family，**不需要**改变
`F-2` ～ `F-17` 的判定，**不需要**新增 architecture decision —— 即可**重新执行 closure**。

**不得**由 Agent 自行补全上述名称，**不得**以 illustrative placeholder 代替。

**F. Downstream Boundary（保持）**

```
Field Carrier Mapping              = DESIGN PENDING
Final Import Contract              = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

**G. Historical Preservation**

PR #61 `Field Carrier Mapping Design Review（Review Finding）` **完整保留**（含 `RF-X1` ～ `RF-X6`
与 illustrative 声明）；**未**把该 Review Finding 改写成最终设计；
**未**回写任何历史 Review ／ Human Decision ／ Implementation 记录的时点语义。

**执行状态（本 Closure Validation 时点）**

```
Field Carrier Mapping              = DESIGN PENDING
Human Decision                     = RECORDED
Closure                            = BLOCKED
State Transition                   = NOT EXECUTED
Blocking Gap                       = G-1 ／ G-2

Final Import Contract              = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```
> **后续状态：** 本记录保留为**首次 closure attempt 的时点记录**（`NOT SATISFIED`）。
> `G-1` ／ `G-2` 解除后已执行 **Closure Re-run**（见 **§4.3.27**），结果 **`PASS`** 并已发生状态转换。

---

#### 4.3.27 Field Carrier Mapping Closure Re-run Record

**Closure Re-run Result：`PASS`**

**State Transition：`Field Carrier Mapping` = `DESIGN PENDING` → `DESIGN RESOLVED`**

**A. Precondition —— Decision Gap 解除**

```
G-1  Manifest 的 exact property name ／ grouping name                      = RESOLVED（Human 批准 literal names）
G-2  record-level reserved carrier-metadata namespace 的 exact property name = RESOLVED（"_meta"）
```

依据 **Supplementary Human Naming Decision（`G-1` ／ `G-2`）**，见上方 **Human Decision Record**。
该补充决定**仅**解决 naming —— **未**新增 carrier family，**未**改变 layer ownership，
**未**修改任何 canonical business semantic。

**B. Conditional Closure Gate（决定 12 复跑）**

| # | 条件 | 结果 |
| --- | --- | --- |
| 1 | Human decisions fully registered | **`PASS`**（决定 1 ～ 12 ＋ **Supplementary Human Naming Decision**） |
| 2 | `F-1` ～ `F-14` ＋ `F-17` = ALL PASS | **`PASS`** |
| 3 | New Blocking Contradiction = NONE | **`PASS`** |

**C. `F-1` ～ `F-14` ＋ `F-17` 复跑逐项**

| # | Criterion | 复跑依据 | 结果 |
| --- | --- | --- | --- |
| `F-1` | Manifest carrier model 已显式登记（含 package-level property 集合与 grouping boundary） | **`G-1` 解除** —— `"package"` ／ `"datasets"` grouping literal 与 package-scoped ／ dataset-entry property literal 已登记（**§4.3.25** A ／ B） | **`PASS`**（原 `BLOCKED`） |
| `F-2` | `role → artifact` carrier 形态 ＋ cardinality ／ uniqueness invariant | 决定 2；entry literal `"role"` ／ `"artifact"` 已登记 | **`PASS`** |
| `F-3` | presence metadata 与 `role → artifact` 可确定、唯一、可判定地关联 | 决定 2；`"record_count"` ＋ `"datasets"` membership 为 inclusion 的物理表示 | **`PASS`** |
| `F-4` | business dataset top-level carrier 形态 ＋ `K-2` 兼容 | 决定 3（`B-A` bare record array） | **`PASS`** |
| `F-5` | `included ＋ record_count = 0` 与 `not included` 可区分 | 决定 3 ＋ `C-8`；membership 表示 inclusion；**不**引入 MUST-NOT-EXIST 规则 | **`PASS`** |
| `F-6` | record carrier 形态（含是否强制 JSON object ／ 是否允许 carrier-level 属性） | 决定 5（强制 JSON object）＋ 决定 6；**`G-2` 解除** —— reserved namespace literal `"_meta"` 已登记（**§4.3.25** F） | **`PASS`** |
| `F-7` | canonical field carrier policy ＋ 不改变 canonical field semantic | 决定 7（`F-A`） | **`PASS`** |
| `F-8` | carrier 不违反 `C-1` ～ `C-10` | 决定 3 ／ 5 ／ 7 ／ 10 | **`PASS`** |
| `F-9` | dataset-level provenance reference 的 carrier 已登记 | 决定 4（Manifest 为 authoritative）＋ `"provenance_ref"` | **`PASS`** |
| `F-10` | locator carrier ＋ 分层不混合 ＋ `K-16` 关联 ／ cardinality | 决定 8（`P-A`，位于 `"_meta"` 内；observation-level；双向 cardinality） | **`PASS`** |
| `F-11` | `Mapping ／ Resolution Basis` carrier ＋ 确定性关联 | 决定 9（`MB-A`，与 `P-A` 同一 nested structure，位于 `"_meta"` 内） | **`PASS`** |
| `F-12` | carrier 层不压平 `valid absence` ／ `missing` ／ `not applicable` 的语义 | 决定 10（沿用 `C-2`） | **`PASS`** |
| `F-13` | carrier 层无 silent fix-up | 决定 7 | **`PASS`** |
| `F-14` | 已知 option combination 的 dependency ／ incompatibility 已显式登记，且无未登记的跨选择冲突 | **§4.3.26** C（决定 1 ～ 12 组合一致性）＋ naming 决定**未**引入新组合约束 | **`PASS`** |
| `F-17` | integrity evidence 的 physical carrier（位置与 grouping boundary）已登记，且不与 business field 混淆 | 决定 1 ＋ `"integrity_evidence"`（**dataset-entry scope**）；algorithm 仍属 `Final Import Contract` | **`PASS`** |

**Gate 2 结论：`F-1` ～ `F-14` ＋ `F-17` = **ALL `PASS`**。

**D. Residual（非 blocking —— 透明记录）**

`P-A` nested provenance structure 与 `MB-A` basis 的**位置**已固定（位于 `"_meta"` 内，见 **§4.3.25** F）；
其**内部 member 名称**不在 `G-1` ／ `G-2` 的授权范围内，且**无**任何 mandatory criterion
（`F-1` ～ `F-14` ＋ `F-17`）要求其内部 property 集合 —— 因此**不构成** blocking gap。
若后续 implementation 需要固定这些内部名称，属**独立 naming decision**，**不得**由 Agent 自行推断。

**E. Non-Implementation Confirmation**

**未**创建 package directory ／ JSON sample ／ `manifest.json` 实际文件 ／ dataset artifact ／ ZIP ／ archive ／
JSON Schema ／ parser ／ serializer ／ validator ／ Adapter；
**未**定义 integrity algorithm ／ unknown-property runtime behavior ／ path validation implementation。
本记录**仅**完成 design registration 与 closure validation —— **design resolution ≠ runtime implementation**。

**F. Downstream Boundary（保持 —— 未越界）**

```
Final Import Contract              = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

**G. Historical Preservation**

`§4.3.26`（首次 closure attempt = `NOT SATISFIED`）与其中记录的 **Decision Gap `G-1` ／ `G-2`**
**保留**为**时点记录**，**未**回写；PR #61 `Field Carrier Mapping Design Review（Review Finding）`
**完整保留**（含 `RF-X1` ～ `RF-X6` 与 illustrative 声明）。

**执行状态（本 Closure Re-run 时点）**

```
Field Carrier Mapping              = DESIGN RESOLVED
Human Decision                     = RECORDED
Naming Decision（G-1 ／ G-2）       = RECORDED
Closure                            = PASS
State Transition                   = EXECUTED

Final Import Contract              = DESIGN PENDING
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

---

#### 4.3.28 Final Import Contract Human Decision Record（Registered Contract Policy）

**Final Import Contract Human Decision Record —— `SIMULATED POC Design Policy` ＋ `Human-approved`**

**Registration Status：`REGISTERED`**

依据 **Issue #66 Human Decision（Bundle 1 ～ 6）**。本记录**只**登记已批准的 contract 选择、
把其写成 authoritative current design，并执行 closure validation ——
**不**新增 Human choice、**不**创建 runtime artifact、**不**实现 importer ／ validator。

```
Review Object      = Final Import Contract（§4.3 Review Finding 的 Design Review 对象）
Review Basis       = PR #65 Final Import Contract Design Review（Review Finding，review-only）
Decision Authority = Human（Issue #66，Bundle 1 ～ 6）
Write Scope        = docs/design/poc-design-v0.2.md（＋ closure 成功时 docs/project-index.md）
```

> **Historical Preservation：** PR #65 的 **Final Import Contract Design Review（Review Finding）**
> （含 `IC-1` ～ `IC-23`、`IS-*`、`RIF-*`、`RIF-X*`、`DEP-*`、`§7.1` closure levels、
> `§8` criteria、`§9` Decisions、`§12` Revision Log）**完整保留**，**未**回写、**未**改写。
> 本节是对其的**最终裁定**，不是对 Review 记录的修改。

#### A. Bundle 1 —— Contract Version ＋ Unknown Content

**A.1 Contract Version Compatibility（Decision 2）**

```
VC-1 exact-match only                              = SELECTED
exact supported "contract_version" token           = "v0.2"
unsupported ／ unknown version                     = 不 silent interpretation；import-time rejection
```

**Version dispatch 先于 unknown-content validation** ——
即「版本是否被支持」与「payload 是否符合所选版本 contract」是**两个不同判定**（同 `RIF-7` ／ `DEP-1`）。
POC v0.2 **不**引入 major ／ minor 演进体系。

**A.2 Unknown ／ Undeclared Content Policy（Decision 1）**

```
unknown Manifest property            = UX-A reject
unknown dataset-entry property       = UX-A reject
unknown canonical record property    = UX-A reject
unreferenced root-level JSON artifact = UX-A reject
```

**边界（保持）：**

- unknown policy **只**对**已由 version dispatch 确定**的 applicable contract（`"v0.2"`）生效；
- 本策略**不得**使 unknown content 被当作 canonical business field（`IC-6` ／ `IC-7`）；
- **不得**引入 silent fix-up（`IC-10`）；
- **不得**借 unknown policy 扩展 canonical field 集合；
- reserved record carrier namespace `"_meta"` 的 unknown member 策略**由 Bundle 5 单独治理**，
  不并入本节无差别处理。

#### B. Bundle 2 —— Disposition ＋ Failure Reporting ＋ Completeness

**B.1 `REJECTED` vs `UNUSABLE` 的 contract-level usage（Decision 3）**

```
RD-B = SELECTED

REJECTED  = import-time ／ structural acceptance failure；package 从不成为 Accepted
UNUSABLE  = 此前已被 Accepted 的 package，在 accepted-package contract 下之后变为不可信 ／ 不可用
```

`REJECTED` ／ `UNUSABLE` **仍为 Package disposition（consequence），不是 Issue Reason**（`IC-21`）。
**未**新增 status enum。

**B.2 Failure Reporting（Decision 8）**

```
FR-3 = SELECTED
```

- **collect all** deterministically discoverable ／ reachable defects，**受 prerequisite 边界限定**；
- **deterministic ordering**（仅对本次能够可靠收集到的 issue set 生效）；
- prerequisite 受阻的 downstream check = **`not evaluable due to prerequisite`**，**不是** passed；
- **沿用既有 Validation Taxonomy 与 conceptual issue dimensions**（`IC-20` ／ `§4.4.79` ～ `§4.4.83`）；
- **不新增** root Validation Reason；
- **auditable 最小内容**仍受 `§4.4.79` dimensions 约束。

**B.3 Completeness（Decision 9）**

```
CF-1 = SELECTED
```

`"completeness_state"` = **Manifest-declared metadata only**；**不直接**参与 Layer 1 structural acceptance gate。
`CF-1` **不**削弱 `IS-24` 的 acceptance-time 一致输入视图义务（见 D.2）。

#### C. Bundle 3 —— Path ＋ Acceptance-time Stable View ＋ Post-accept Re-verification

**C.1 Path Resolution ／ Boundary Enforcement（Decision 4）**

```
PN-1 strict literal path semantics = SELECTED
```

| # | 已登记语义 |
| --- | --- |
| 1 | artifact reference = **single package-root-level filename** |
| 2 | **exact filename match** |
| 3 | **无** path normalization ／ case folding ／ Unicode normalization |
| 4 | **无** `.` ／ `..` segment |
| 5 | **无** absolute ／ external ／ URI reference |
| 6 | **无** symlink ／ junction ／ filesystem alias indirection |
| 7 | 不同 included roles 若**确认为同一 physical target** ⇒ 违反 inherited **independent-artifact invariant**（`IC-1`，同 `IS-4` ／ `IS-9` ／ `IS-17b`） |

`PN-1` **只**表示不做普通化处理，**不表示**可以跳过 boundary（`IC-2`）与 alias ／ independence 约束。
**未**定义 path validation 的 runtime implementation。

**C.2 Acceptance-time Stable View Binding Guarantee（Decision 10A）**

```
Decision 10A = explicit acceptance-time stable-view binding guarantee = SELECTED
```

- 所有导致 `Accepted` 的检查**必须**绑定到**同一 package content view** ——
  即**实际被接受**、且**随后被 Analysis Run 引用**的那一份内容视图；
- **无法建立**该一致性 ⇒ **`not evaluable` ／ fail closed**（不得据此宣称通过）；
- **implementation mechanism 保持 open**（锁 ／ 事务 ／ 原子移动 ／ 存储技术属 implementation，本层不设计）；
- **未**新增 carrier ／ sidecar ／ literal。

**C.3 Post-accept Mutation（Decision 10B）**

```
MG-2 re-verification = SELECTED
```

- 在**后续 trusted reuse 之前**，integrity **必须保持可重新验证**；
- **检测到 mutation** ／ **无法重新建立 required integrity** ⇒ **`UNUSABLE`**（依 `RD-B`）；
- **不引入** content-derived package-ID requirement；
- **不**重新打开 immutability（`IC-12` 已 inherited）。

#### D. Bundle 4 —— Integrity Contract

**D.1 Algorithm ／ Evidence Representation（Decision 5）**

```
integrity family                    = cryptographic hash
fixed POC v0.2 algorithm            = SHA-256（IG-alg-1）
evidence representation             = contract-level（IG-rep-A）
"integrity_evidence" value          = 64-character lowercase hexadecimal SHA-256 digest
checksum-only ／ signature ／ hybrid = 不进入 POC v0.2
```

- **deterministic verification**：algorithm 固定、identifier 语义固定、value representation 固定 ⇒
  「给定 evidence 与 artifact，verification 结果不依赖 implementation 选择」；
- **signature ／ authenticity 分支在本层不启用** ⇒ `DEP-11` 的 verification key ／ trust input
  **不构成本层未完成的 security ／ key-management prerequisite**；
- **content integrity ≠ identity ／ authenticity**（不变式保持）；
- **未**引入 PKI ／ signing infrastructure ／ secrets。

**D.2 Integrity 覆盖对象与 digest 目标（Decision 6）**

```
IG-raw = SELECTED
```

digest 针对 **raw artifact bytes**（exact bytes），
**不做** byte-level JSON canonicalization ⇒ **不触发** `IC-11` 的 byte-level canonicalization 设计。

**D.3 Manifest 自身 Integrity（Decision 7）**

```
IG-self-C = SELECTED（parameterized trust contract）＝ HUMAN-APPROVED
```

- authoritative **configured trusted package-input boundary** = trust input；
- 该 trust input **必须**提供与 acceptance **相同的 stable package content view**；
- trust premise **绑定到该次 acceptance-attempt 的 exact content view**；
- trusted input boundary **缺失 ／ 不可验证** ⇒ **`not evaluable` ／ fail closed**；
- **不主张 sender-authenticity**；
- **无** sidecar ／ **无** new carrier ／ **无** signature ／ **无** PKI ／ **无** secret-management。

**closure-level 判定（依 `§7.1`）：** 本项属 **category ① parameterized external input contract** ——
contract semantics 已完整（authoritative source、binding、missing 行为、conformance determinism、
可声称范围齐备），且**不依赖**任何未完成设计（无新 carrier ／ literal ／ trust mechanism ／
key-management contract）⇒ 满足 `CL-2`；`I-10` 的 PASS 依据即本项。

#### D4. Acceptance Boundary ＋ Validation Partial Order（authoritative current policy）

> 本小节是 **`I-1`（acceptance boundary）** 与 **`I-3`（acceptance partial order）** 的
> **authoritative registered basis**。
> 它**只**合成**既有 inherited constraints ＋ 本记录 Bundle 1 ～ 5 的已批准选择**，
> **不新增**任何 Human choice、**不**新增 status enum、**不**规定线性 parser algorithm。
> PR #65 `RIF-2` 保留为 **review evidence**，但**不**作为本 policy 的唯一依据。

**D4.1 Acceptance gate（package 何时成为 `Accepted`）**

```
manifest readable
  → strict JSON parse（IC-8）
  → required manifest structure ／ identity ／ contract_version 可判定（IC-14 ／ IC-16）
  → version exact-match gate（VC-1；supported token = "v0.2"）
  → applicable contract ／ known member set 已确定
  → Manifest ／ dataset-entry unknown-content checks（UX-A reject）
  → role ／ cardinality ／ artifact reference ／ path checks（IC-1 ／ IC-3 ／ IC-2 ／ PN-1）
  → declared artifact existence ／ readability（IC-14）
  → artifact-level checks（见 D4.2 ／ D4.3）

all acceptance-producing results
  → 必须绑定同一 stable package content view（Decision 10A）
  → 所有 required 且 prerequisite-reachable 的 Layer-1 gate 均通过
  → Accepted
```

- Package 只有在**全部** applicable Layer-1 gate 均对**同一 stable content view** 成立后才可 `Accepted`；
- **失败**结果按 **`RD-B`** 表达：import-time ／ structural acceptance failure ⇒ `REJECTED`；
  此前已 `Accepted` 而之后不可信 ／ 不可用 ⇒ `UNUSABLE`；
- `"completeness_state"` **不**参与本 gate（**`CF-1`**）；
- Package **未** `Accepted` ⇒ **不得**创建依赖它的正常 Analysis Run（`IC-18`）。

**D4.2 Artifact raw-byte integrity（位置为 partial-order edge，不是固定序号）**

```
artifact raw-byte SHA-256:
  - 在 raw bytes 可读取后即可执行
  - 不依赖 JSON parse ／ record_count
```

- 依据 **Bundle 4 `IG-raw`**（digest = exact raw artifact bytes）与 **`IC-22`**（mandatory ＋
  不可验证 ⇒ structural ＋ fail closed）；
- 因而**不**存在「必须先完成 `record_count` 检查才能验证 integrity」的约束；
- **不得**把 `record_count → integrity` 的顺序当作已登记 policy（同 PR #65 `RIF-2` 的结论）。

**D4.3 Artifact JSON parse 之后的结构检查**

```
artifact JSON parse（IC-8）
  → record carrier ／ canonical-field ／ "_meta" shape checks（IC-6 ／ IC-7 ＋ Bundle 5）
  → record_count consistency（Manifest authoritative presence metadata；IC-4 ／ IC-16）
```

**D4.4 Partial order 性质（显式声明）**

- 上述流程登记为 **partial order（prerequisite edges）**，**不是**线性 parser algorithm；
  同一 prerequisite 层内不要求固定执行顺序；
- **inherited prerequisite edges**（D4.1 ／ D4.3）**不得**被实现为「各项独立成功即可接受」；
- `FR-3` 的 **collect-all** 可在 **prerequisite 可达范围**内执行：
  prerequisite 受阻的 downstream check 记 **`not evaluable due to prerequisite`**，**不是** passed；
- **已知** edge：`Manifest 不可 strict-parse` ⇒ declared artifact set **不可知** ⇒
  其 downstream artifact-level checks **not evaluable**（不是「漏报」）；
- Manifest 自身可信性由 **D.3（`IG-self-C`）** 提供；**Manifest self-integrity 不在此处新增 carrier**。

#### E. Bundle 5 —— `"_meta"` Known Member Set（Decision 11）

**E.1 已登记的 controlled member shape（authoritative）**

```
_meta
└── provenance_associations
    └── association[]
        ├── observation
        ├── evidence
        └── mapping_basis   (optional, when applicable)
```

**E.2 已登记的 approved literals**

```
"provenance_associations"
"observation"
"evidence"
"mapping_basis"
```

**E.3 语义（as registered）**

- `"provenance_associations"` = 当前 record 的 array；
- `"observation"` = 具体 canonical observation ／ context reference；
  对 ordinary canonical fields，使用 **FCM 已登记的 canonical JSON property name**；
- `"evidence"` = **一个或多个** opaque JSON-string **Stable Source Evidence Locator** 值的 array；
- **重复 locator** 跨 association 出现 ⇒ 保持 **one-evidence → multiple-canonical-outputs**；
- **同一 association 内多个 locator string** ⇒ 保持 **multiple-evidence → one-canonical-fact**；
- `"mapping_basis"` = optional **exact JSON string**，**仅**在发生 semantic mapping ／ resolution 时要求，
  与相关 association **colocated**；
- **无** trim ／ case conversion ／ Unicode normalization ／ numeric coercion ／
  locator 或 mapping-basis string 的 heuristic interpretation；
- **unknown direct member under `"_meta"` ⇒ reject**；
- **unknown member inside an association object ⇒ reject**；
- **无**其他 `_meta` member 在 POC v0.2 获批。

**E.4 与已关闭层的边界**

本 Bundle **仅**在本层授权范围内固定 `"_meta"` 的 **known member set 与 literal**。
它**不**新增 carrier family、**不**改变 layer ownership、**不**修改 canonical business semantic，
也**不**改变 `P-*` ↔ canonical observation 的 cardinality 语义（`F-10` ／ `F-11` 保持）。
`§4.3.27` D 记录的 FCM non-blocking residual 由此在本层**重新评估并解除**（`DEP-10` ／ `IS-25`）：
本层所需 authoritative member set **已实际登记**，不是 future naming task。

**E.5 `I-17` 取级依据（依 `§7.1`）**

本项属 `§7.1` 的 **(i) 本次实际登记 authoritative known member set（或 literal set）并完成 binding** ⇒ **`CL-1`**；
**不是** (ii)（仅另开 naming decision —— 该情形在实际完成前为 `CL-3`），**亦**不是 (iii)（parameterized contract）。
**未**由 Agent 发明任何 provenance ／ basis 内部 property name —— 以上 literal 均为 Human-approved。

#### F. Bundle 6 —— Closure Authorization

```
mandatory closure criteria = I-1 ～ I-18 + I-21（共 19 项）
design objectives          = I-19 ／ I-20（必须评估；不作为独立 hard blocker）
每项 mandatory criterion   = 必须分类 ／ 佐证为 CL-1 ／ CL-2 ／ CL-3
FIC closure 前置条件       = 无任何 mandatory criterion 停留在 CL-3
selected-decision composition check = MANDATORY
状态推进条件               = 全部 mandatory PASS ＋ 无 CL-3 ＋ Blocking Contradiction = NONE
```

#### G. Registration Boundary

- 本记录**不**创建：JSON Schema、sample package ／ real `manifest.json`、parser ／ serializer ／
  runtime validator、import service、database schema、Adapter ／ connector、
  filesystem transaction ／ locking implementation、PKI ／ signing infrastructure；
- **未**新增 canonical entity ／ business field ／ enum、**未**修改 `BR-*`、
  **未**修改 Validation Taxonomy、**未**新增 Validation Reason；
- **未**修改 `AGENTS.md` ／ `CONTRIBUTING.md` ／ Discovery `FROZEN` docs；
- **`D4` 只**合成依既有 inherited constraints 与本记录 Bundle 1 ～ 5 已批准选择而**唯一确定**的
  acceptance boundary ／ partial order —— **未**新增 Human choice、**未**新增 status enum ／
  Validation Reason ／ carrier ／ literal、**未**规定线性 parser algorithm；
- 本层 **design resolution ≠ runtime implementation**。

**执行状态（本 Registration 时点）**

```
Final Import Contract              = DESIGN PENDING → 待 Closure Validation
Human Decision（Bundle 1 ～ 6）     = RECORDED
Snapshot / Import Contract overall = DESIGN PENDING
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

---

#### 4.3.29 Final Import Contract Closure Validation Record

**Final Import Contract Closure Validation Record**

**Closure Result：`PASS`**

**State Transition：`Final Import Contract` = `DESIGN PENDING` → `DESIGN RESOLVED`**

**current-state（本 Closure 之后 —— authoritative）：**

```
Snapshot / Import Contract overall = DESIGN RESOLVED
  Package Envelope ／ Atomicity Boundary ／ Immutability Boundary ／ Analysis Run Linkage = DESIGN RESOLVED
  Serialization Format             = DESIGN RESOLVED
  Physical Dataset Layout          = DESIGN RESOLVED
  Field Carrier Mapping            = DESIGN RESOLVED
  Final Import Contract            = DESIGN RESOLVED   ← 本 Closure
Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT
```

> 本状态块为 **current-state**；其下 A ～ I 各节中的 `DESIGN PENDING` 表述
> （例如 A.4 的首次 `Decision Gap` 判定输入、以及上文 Registration 的时点状态块）
> 属**本 Closure 过程内的时点记录**，**未**回写。
>
> **时点说明 ／ supersede（Issue #90）：** 本状态块是 **Issue #66 ／ `Final Import Contract` closure 时点**的
> status snapshot；其 `Adapter Boundary = DESIGN PENDING` 为**当时值**，**保留不回写**，
> 但**不再代表 latest repository-wide current state** —— 该值**已被 Issue #90 Closure Validation = `PASS` supersede**：
> `Adapter Boundary` 现为 **`DESIGN RESOLVED`**（conceptual closure；runtime ／ source-specific realization 仍 `NOT IMPLEMENTED`）。
> 最新 Adapter status 见 **§4.6.21** ／ **§4.6.22**。（本节其余 `Adapter Boundary = DESIGN PENDING` 表述同属当时值，保留不回写。）

**A. Precondition**

| # | 条件 | 结果 |
| --- | --- | --- |
| 1 | Human decisions fully registered | **`PASS`**（Bundle 1 ～ 6 已登记，见上方 Human Decision Record） |
| 2 | 无未登记的 naming ／ carrier ／ trust prerequisite | **`PASS`** —— `"_meta"` known member set 已实际登记（Bundle 5）；Manifest trust input 属 category ① 参数化契约（Bundle 4） |
| 3 | selected-decision composition check 已执行 | **`PASS`**（见下方 D） |
| 4 | FIC 首个 mandatory `CL-3` | **无** |

**B. Decision Gap 判定**

```
Decision Gap（新增） = NONE
```

**C. `I-1` ～ `I-18` ＋ `I-21` 逐项 Closure Validation（MANDATORY，共 19 项）**

`CL` 列依 **`§7.1`** 的 closure level；`结果` 只允许 `PASS` ／ `FAIL` ／ `BLOCKED`。

| # | Criterion | 满足依据（registered decision ／ inherited constraint） | `CL` | 结果 |
| --- | --- | --- | --- | --- |
| `I-1` | acceptance boundary 已登记 | **`§4.3.28 D4.1`**（authoritative acceptance gate：manifest readable → strict parse → structure ／ identity ／ `contract_version` 可判定 → version exact-match → applicable contract ／ known member set → unknown-content checks → role ／ cardinality ／ reference ／ path checks → declared artifact existence ／ readability → artifact-level checks → 同一 stable content view ＋ 全部 applicable Layer-1 gate 通过 ⇒ `Accepted`）＋ **`§4.3.28 D4.4`**（partial order 性质）＋ Bundle 2（`RD-B` 失败表达 ／ `CF-1` 非 gate）＋ Bundle 3 `10A` ＋ Bundle 4（`IC-22`）＋ `IC-18` ／ `IC-19` | **`CL-1`** | **`PASS`** |
| `I-2` | `REJECTED` ／ `UNUSABLE` contract-level usage 已登记（不新增 enum） | Bundle 2 `RD-B`：`REJECTED` = import-time ／ structural acceptance failure（从未 Accepted）；`UNUSABLE` = 此前 Accepted、之后不可信 ／ 不可用；`IC-21` 保持 disposition ≠ reason | **`CL-1`** | **`PASS`** |
| `I-3` | acceptance partial order 已登记（含 integrity 位置依 digest 目标） | **`§4.3.28 D4.2` ＋ `D4.3` ＋ `D4.4`**（authoritative partial order：artifact raw-byte SHA-256 在 raw bytes 可读取后即可执行、**不依赖** JSON parse ／ `record_count`；artifact JSON parse ⇒ record carrier ／ canonical-field ／ `"_meta"` shape ⇒ `record_count` consistency；显式声明为 partial order、`FR-3` collect-all 受 prerequisite 可达范围限定、`not evaluable` 不等于 passed）；`RIF-2` **保留为 review evidence**，**非**唯一依据 | **`CL-1`** | **`PASS`** |
| `I-4` | `IS-*` structural 集合已登记，且 `IC + open` 项 disposition wording 已登记 | Bundle 1（`UX-A`）／ Bundle 2（`RD-B` ＋ `FR-3`）／ Bundle 3（`PN-1` ＋ `10A` ＋ `MG-2`）／ Bundle 4（`IG-raw` ＋ SHA-256 ＋ `IG-self-C`）；`IS-2` ／ `IS-7` ／ `IS-10` ／ `IS-24` 的 wording 由 Bundle 2 ／ 3 收敛；`IC` 结论未被重开 | **`CL-1`** | **`PASS`** |
| `I-5` | unknown ／ undeclared content policy 已逐类登记，且 applicable contract ／ known member set 的确定前提已给出 | Bundle 1：version dispatch（`"v0.2"` exact-match）**先**确定 applicable contract 与 known member set，**再**应用 `UX-A reject`（Manifest ／ dataset-entry ／ canonical record ／ unreferenced artifact 四类）；`"_meta"` 归 Bundle 5 | **`CL-1`** | **`PASS`** |
| `I-6` | path resolution ／ boundary enforcement semantics 已登记（含 alias ／ link 边界） | Bundle 3 `PN-1` 七项语义（single package-root-level filename ／ exact match ／ 无 normalization ／ 无 `.` ／ `..` ／ 无 absolute ／ external ／ URI ／ 无 symlink ／ junction ／ alias indirection）；`IC-2` invariant 保持 | **`CL-1`** | **`PASS`** |
| `I-7` | target identity 判定语义已登记，且确认同一 target ⇒ 适用 `IC-1` | Bundle 3 `PN-1` 第 7 项 ＋ Bundle 1 的 unreferenced artifact reject；`IS-17b` 的 inherited invariant 未被重开；`PN-1` 下不存在 normalization 语义 ⇒ target identity 由 **exact filename** 唯一确定 | **`CL-1`** | **`PASS`** |
| `I-8` | integrity evidence representation ／ ownership 已登记 | Bundle 4：mandatory（`IC-22`）＋ `IG-rep-A` contract-level representation ＋ `"integrity_evidence"` value = 64-char lowercase hex SHA-256 digest；**signature ／ authenticity 分支未启用** ⇒ 无 verification key ／ trust input 待定项 | **`CL-1`** | **`PASS`** |
| `I-9` | integrity 覆盖对象 ＋ digest 目标已登记，且与 `IC-11` 一致 | Bundle 4 `IG-raw`：digest = **raw artifact bytes**，**无** byte-level canonicalization ⇒ `IC-11` 的 `Deterministic Parsing ≠ Byte-for-byte Canonical JSON Encoding` 区分保持，且**未**触发 canonicalization 设计 | **`CL-1`** | **`PASS`** |
| `I-10` | Manifest 自身 integrity 处置已登记，且达相应 closure level | Bundle 4 `IG-self-C`：authoritative configured trusted package-input boundary = trust input；须提供与 acceptance 相同的 stable content view；trust premise 绑定该次 acceptance-attempt 视图；缺失 ／ 不可验证 ⇒ `not evaluable` ／ fail closed；无 authenticity 主张；**无**新 carrier ／ sidecar ／ literal ／ trust mechanism ／ key-management contract ⇒ 属 `§7.1` **category ①**（contract 已闭合）⇒ `CL-2`（非 `CL-3`） | **`CL-2`** | **`PASS`** |
| `I-11` | `contract_version` compatibility model 已登记，且禁止 unsupported version 的 silent interpretation；区分版本支持与 payload 符合 | Bundle 1：`VC-1` exact-match ＋ supported token `"v0.2"`；unsupported ／ unknown ⇒ **no silent interpretation**、import-time rejection；version dispatch **先于** unknown-content validation | **`CL-1`** | **`PASS`** |
| `I-12` | package-level atomic acceptance 语义已登记（无 dataset-level partial outcome） | `IC-13` inherited（`§4.3.6` ／ `§4.3.7`）；`AM-2` ／ `AM-3` 保持 `NOT COMPATIBLE`；Bundle 2 `RD-B` 的 `REJECTED` = 整个 package 未成为 Accepted | **`CL-1`** | **`PASS`** |
| `I-13` | `"completeness_state"` 在 acceptance gate 中的角色已登记 | Bundle 2 `CF-1`：**metadata only**，**不直接** gate Layer 1 structural acceptance | **`CL-1`** | **`PASS`** |
| `I-14` | 10A 一致输入视图义务 ＋ 10B post-accept detection ／ re-verification ／ binding 要求均已登记（不得重开 immutability） | Bundle 3 `10A`（explicit stable-view binding guarantee；无法建立 ⇒ `not evaluable` ／ fail closed）＋ `10B` `MG-2`（trusted reuse 前 integrity 必须保持可重新验证；mutation ／ 无法重建 ⇒ `UNUSABLE`）；`IC-12` immutability 保持未重开 | **`CL-1`** | **`PASS`** |
| `I-15` | failure reporting shape 已登记，root-issue 沿用 inherited taxonomy | Bundle 2 `FR-3`：collect-all（受 prerequisite 边界限定）＋ deterministic ordering ＋ `not evaluable due to prerequisite` 与 `evaluated` 显式区分；沿用 `IC-20` `PACKAGE_STRUCTURE` ／ `STRUCTURAL_INCONSISTENCY`；**未**新增 Validation Reason | **`CL-1`** | **`PASS`** |
| `I-16` | layer ownership boundary 已登记，且未把 Layer 2 ～ Layer 4 提升为 structural failure | `RIF-11` 划分保持；Bundle 1 ～ 5 均未触碰 Layer 2 ～ Layer 4 semantics；`IC-17` 三层语义保持 | **`CL-1`** | **`PASS`** |
| `I-17` | unknown-`"_meta"` member policy 前置条件已处置，且按 prerequisite 是否实际满足取级 | Bundle 5：**已实际登记** authoritative known member set（`"provenance_associations"` ／ `"observation"` ／ `"evidence"` ／ `"mapping_basis"`）＋ controlled shape ＋ unknown member（direct 与 association 内）**reject** ⇒ `§7.1` **(i)** ⇒ `CL-1`；**不是** future naming task | **`CL-1`** | **`PASS`** |
| `I-18` | integrity algorithm contract 已达 deterministic 可判定 | Bundle 4：fixed **SHA-256**（`IG-alg-1`）＋ contract-level representation（`IG-rep-A`）＋ 64-char lowercase hex value ＋ `IG-raw` 覆盖对象 ⇒ deterministic verification 不依赖 implementation 选择；**signature ／ authenticity 分支未启用** ⇒ 不依赖未完成 security ／ trust contract | **`CL-1`** | **`PASS`** |
| `I-21` | 跨选择无阻塞矛盾已显式核验；无拟记 `CL-2` 的 criterion 依赖未完成 design prerequisite | 见下方 **D**（组合核验表）＝ **Blocking Contradiction: NONE**；唯一 `CL-2`（`I-10`）经核验属 category ①；其余 18 项为 `CL-1` | **`CL-1`** | **`PASS`** |

**Gate 结论：**

```
I-1 ～ I-18 ＋ I-21 = ALL PASS（19 / 19）
CL distribution     = CL-1 × 18 ／ CL-2 × 1（I-10）／ CL-3 × 0
Blocking Contradiction = NONE
```

**D. Selected-Decision Composition Check（`I-21`）**

| # | 组合对 | 核验 | 结果 |
| --- | --- | --- | --- |
| 1 | version dispatch → applicable contract → unknown policy | `"contract_version" = "v0.2"` exact-match 先确定 applicable contract，再应用 `UX-A reject`；unsupported version 不被 silent interpretation | **`NO CONTRADICTION`** |
| 2 | `UX-A` ↔ `CF-1` | unknown property reject 属 structural 判定；`CF-1` 仅声明 `"completeness_state"` 为非 gate metadata —— **不**产生新的拒绝条件，也不掩盖 structural 判定 | **`NO CONTRADICTION`** |
| 3 | `PN-1` path identity ↔ artifact independence（`IC-1`） | exact filename ＋ 无 alias indirection ⇒ 不同 included roles 只能通过**同一 literal filename** 指向同一 artifact ⇒ 该情形直接违反 independence 并被拒绝 | **`NO CONTRADICTION`** |
| 4 | `PN-1` ↔ `IG-raw` | exact raw bytes 在无 normalization ／ 无 alias 的 single-filename 语义下**不产生歧义 target** | **`NO CONTRADICTION`** |
| 5 | `10A` stable view ↔ `IG-raw` | raw-byte digest 直接绑定被接受视图的字节，**无需** JSON canonicalization 即可跨读取比较 | **`NO CONTRADICTION`** |
| 6 | `IG-self-C` trust input ↔ `10A` | trust input 必须提供与 acceptance **相同的** stable content view ⇒ 两者**同源**，不产生第二个视图 | **`NO CONTRADICTION`** |
| 7 | `RD-B` ↔ `MG-2` | import-time 结构失败 = `REJECTED`；trusted reuse 前重新验证失败 = `UNUSABLE`；**两者不混用**，且均不产生 dataset-level partial outcome（`IC-13`） | **`NO CONTRADICTION`** |
| 8 | `FR-3` collect-all ↔ `IC-14` / `IC-16` | collect-all 只收集 prerequisite **可达**的 defect；不可达者记 `not evaluable`，**不得**记为 passed | **`NO CONTRADICTION`** |
| 9 | `IC-14` structural 定义 ↔ `UX-A` reject | `UX-A` 的 reject 属 root condition 可落入既有 `PACKAGE_STRUCTURE` ／ `STRUCTURAL_INCONSISTENCY`，**不**把 `Any Dataset Absent` 泛化为 structural failure | **`NO CONTRADICTION`** |
| 10 | Bundle 5 `_meta` known member set ↔ Bundle 1 unknown record property policy | `"_meta"` 由 Bundle 5 单独治理；canonical record property unknown 仍 `UX-A reject`；两者**不重叠**，且 `"_meta"` 内容**不得**被当作 business field（`IC-6` ／ `IC-7`） | **`NO CONTRADICTION`** |
| 11 | Bundle 5 literals ↔ FCM registered policy（未回写已关闭层） | Bundle 5 只在其自身授权范围内固定 `"_meta"` member set；`P-A` ／ `MB-A` 位置与 `K-16` cardinality 语义**未变**；`§4.3.25` ／ `§4.3.27` 记录**未回写** | **`NO CONTRADICTION`** |
| 12 | `CF-1` ↔ `I-14` `10A` | `CF-1` 不 gate acceptance；`10A` 的一致视图义务**独立**成立（`Decision 9` 的既有边界保持） | **`NO CONTRADICTION`** |
| 13 | `IC-22` integrity mandatory ↔ Bundle 4 fixed SHA-256 | mandatory ＋ unverifiable ⇒ structural ＋ fail closed 未变；固定算法只确定 verification contract，**不**降级 mandatory 性 | **`NO CONTRADICTION`** |
| 14 | `IC-17` 三层语义 ↔ Bundle 2 ／ 4 | Bundle 2 ／ 4 的判定均属 Layer 1 structural ／ integrity，**未**提升 Layer 2 ～ Layer 4 问题 | **`NO CONTRADICTION`** |
| 15 | `D4` acceptance gate ／ partial order ↔ `IC-2` ／ `IC-3` ／ `IC-8` ／ `IC-14` ／ `IC-16` ／ `IC-18` ／ `IC-22` | `D4` 只排列**已 inherited** 的 prerequisite edges，并嵌入 Bundle 1 ／ 3 ／ 4 的已批准 gate；**未**新增条件、**未**固定线性顺序、**未**引入 dataset-level partial outcome（`IC-13`） | **`NO CONTRADICTION`** |
| 16 | `D4.2`（raw-byte SHA-256 早于 parse 可执行）↔ `D4.3`（`record_count` 在 parse 之后） | 两者是**不同**的 prerequisite 分支，**不**构成 `record_count → integrity` 的顺序约束；`IG-raw` 无需 canonicalization | **`NO CONTRADICTION`** |

**`I-21` 结论：`Blocking Contradiction = NONE`；无 hidden cross-decision conflict。**

**E. Objectives Evaluation（`I-19` ／ `I-20` —— 不作为独立 hard blocker）**

| # | Objective | 评估 |
| --- | --- | --- |
| `I-19` | Human Inspectability | **满足** —— acceptance outcome 与 defect 可由 `FR-3` 的 deterministic ordering ＋ 既有 taxonomy dimensions（`§4.4.79`）人工检视；`RD-B` 使 disposition 可区分 |
| `I-20` | Implementation Simplicity | **满足** —— `VC-1` exact-match、`UX-A` reject、`PN-1` strict literal、`IG-alg-1` 固定 SHA-256、`IG-raw`、`CF-1` 均为最小结构选择；**未**引入 normalization ／ canonicalization ／ 演进体系 |

**F. Residual（非 blocking —— 透明记录）**

以下 residual **均为 implementation-only ／ outside the FIC acceptance criterion**，
依 **`§7.1` 强制规则 2** **不**归入 `CL-2`、**不**作为本层 closure 依据，
**未**被当作 `CL-3`：

1. `10A` 的 exact detection timing ／ guaranteed boundary 的 implementation mechanism
   （锁 ／ 事务 ／ 原子移动 ／ 存储技术）—— contract 语义已完整，机制属 implementation；
2. `10B` 的 proactive detection 策略（何时 ／ 以何种频率重新验证）—— disposition 语义已完整；
3. trusted package-input boundary 的 physical 取得方式（配置载体 ／ 部署方式）——
   contract 只规定其**语义与绑定**，不规定实现；
4. `FR-3` 的 report 物理载体（日志 ／ 文件 ／ 服务）—— 属 implementation；
5. `"integrity_evidence"` value 的生成方（export 侧工具）—— 本层只定义 contract-level representation。

**G. Non-Implementation Confirmation**

**未**创建 package directory ／ JSON sample ／ `manifest.json` 实际文件 ／ dataset artifact ／
JSON Schema ／ parser ／ serializer ／ validator ／ import service ／ Adapter ／ connector；
**未**实现任何 acceptance ／ rejection runtime logic、path validation、hash computation、
transaction ／ locking ／ atomic move、PKI ／ signing infrastructure。
本记录**仅**完成 design registration 与 closure validation —— **design resolution ≠ runtime implementation**。

**H. Historical Preservation**

PR #65 `Final Import Contract Design Review（Review Finding）` **完整保留**，
含其 `§9` Decisions、`§11` 时点状态块 与 `§12` Revision Log 中的
`Final Import Contract = DESIGN PENDING` 表述 —— 该等表述为**时点记录**，**未**回写。
`§4.3.21` ／ `§4.3.22` ～ `§4.3.27` 中**此前各层** closure 记录内的
`Final Import Contract = DESIGN PENDING` 亦为**时点记录**，**未**回写。

**I. Snapshot / Import Contract Overall Re-check**

| # | 层级 | 状态 |
| --- | --- | --- |
| 1 | Package Envelope ／ Atomicity Boundary ／ Immutability Boundary ／ Analysis Run Linkage | **`DESIGN RESOLVED`** |
| 2 | Serialization Format | **`DESIGN RESOLVED`** |
| 3 | Physical Dataset Layout | **`DESIGN RESOLVED`** |
| 4 | Field Carrier Mapping | **`DESIGN RESOLVED`** |
| 5 | Final Import Contract | **`DESIGN RESOLVED`**（本记录） |

**剩余 blocking Snapshot / Import design item：** **无**。

⇒ 本 PR **已授权**执行：

```
Snapshot / Import Contract overall = DESIGN PENDING → DESIGN RESOLVED
```

**边界：** `Adapter Boundary` **保持 `DESIGN PENDING`**，**不在**本 closure 范围内；
`POC Design v0.2` **保持 `DRAFT`**。

**执行状态（本 Closure 时点）**

```
Final Import Contract              = DESIGN RESOLVED
Human Decision（Bundle 1 ～ 6）     = RECORDED
Closure                            = PASS
State Transition（FIC）             = EXECUTED
State Transition（Snapshot overall）= EXECUTED

Adapter Boundary                   = DESIGN PENDING
POC Design v0.2                    = DRAFT

Package Structural Failure
  ≠ Capability Evidence Unavailable
  ≠ Business DATA_INCOMPLETE
```

---

#### 4.3.30 v0.2 Record-Level Wire Binding（Issue #118 Human Decision Record）

**Registration Status：`REGISTERED`** —— 依据 **Issue #118 Human Decision**（Decision 1 ～ 8）。

本小节**只**登记该 Human Decision 已批准的 **record-level wire binding**：
**v0.2 已知 canonical record property 的 exact literal 集合**、
该集合在 **Layer 1** 的**唯一职责与明确非职责**、以及 **Manifest `"role"` value contract**。

- 本小节**不**重开 `§4.3.1` ～ `§4.3.29`，**不**回写任何历史时点记录；
- 本小节**不**新增 carrier ／ enum ／ Validation Reason ／ canonical field；
- 本小节**不**创建 JSON Schema ／ parser ／ serializer ／ validator；
- **design registration ≠ runtime implementation**。

**A. Registered Decision（approved model）**

```
Model A1（经收缩后）= global contract-level known canonical record property set
                    + Manifest "role" value = exact opaque JSON string
Per-role whitelist（logical dataset role → permitted canonical properties）
                    = NOT ADOPTED for Layer 1
```

**B. The set（authoritative — explicit, closed, version-bound）**

```
applicable contract_version = "v0.2"（VC-1；见 §4.3.28 A.1）
set kind                    = explicit closed literal enumeration
dynamic derivation          = 禁止（不得在 runtime 依 Data Dictionary 自动生成）
```

**B.1 Frozen v0.2 canonical record property literals（30 项 —— Data Dictionary 现存
canonical field identifiers ＋ 本次两项 naming clarification）：**

```
plant_id
material_code
supplier_id
analysis_run_id
AnalysisDate
required_date
ProductionQty
BOMComponentQty
loss_rate
inventory_status
on_hand_qty
inventory_snapshot_time
SafetyStock
ordered_qty
received_qty
effective_arrival_date
inbound_status
target_material_code
substitute_material_code
substitution_ratio
approval_status
AllocatedSubstituteQty
sourcing_status
standard_lead_time_days
PerformancePeriod
PerformanceUpdatedAt
DeliveryPerformance
QualityPerformance
RecommendationNeedDate
ApplicableMOQ
```

**B.2 明确排除（`NOT canonical record properties`）：**

```
effective demand context   —— 既有 authority 已声明其为 conceptual context，
                              不是 canonical physical field（§4.1.4 G ／ §4.2.7）
snapshot_package_id        —— 保持 transport ／ Manifest identity，
                              不成为 business-record canonical property（§4.3.3）
"_meta"                    —— 由既有独立 known-member contract 管理（§4.3.25 F ／ §4.3.28 E），
                              不作为 ordinary canonical property
```

**本集合为 closed enumeration：** 只有 **B.1** 逐项列出的 literal（＋ `"_meta"`）属于
v0.2 known canonical record property set。任何未列出的 literal —— 无论其 Class、
Requiredness 或语义 —— 都**不在**本集合内，除非经正式 Human Decision 显式加入。

```
"未被列出" ⇒ 不属于本集合（本层依 UX-A reject）
"未被列出" ≠ 已被批准为 wire property
"未被列出" ≠ 本层对其业务语义作出判断
```

> **§4.2.10 derived result fields：** 该表中的 derived result identifiers
> （例如 `BaseRequirement` ／ `RecommendedPurchaseQty` ／ `Classification`）**未**出现在
> B.1 的逐项列示中 ⇒ 依上述 closed-enumeration 规则，它们**不在**本集合内。
> 本层**不**对 derived result 是否应出现在任何 artifact 中作出判断 ——
> 该问题由 **Decision 6** 明确 deferred。本小节只登记 literal 集合，
> **不**为 derived results 新增或排除任何 literal。

**B.3 集合可以包含不同 Class ／ Requiredness 的 canonical fields，Layer 1 对这些类别
不做语义合法性判断：**

```
property known at Layer 1 ≠ field permitted as Snapshot business evidence
```

字段是否适合作为 source ／ runtime ／ context ／ derived evidence，
留给对应 downstream validation ／ implementation gate（Layer 2 ～ Layer 4）。

**C. Layer-1 职责与明确非职责**

**C.1 Layer-1 known-property check 的**唯一**职责：**

```
direct record property ∈ B.1 的 approved set（或为 "_meta"）
      ⇒ Layer-1 视为 known property
不在 approved set 中
      ⇒ 依现有 UX-A（§4.3.28 A.2）reject
```

**C.2 该 check **不得同时判断**：**

```
field requiredness
logical value validity
business applicability
field 是否应该属于某 logical dataset role
capability readiness
semantic resolution
source ／ runtime ／ derived legitimacy
```

```
known property ≠ valid evidence ≠ applicable field ≠ required field
```

**C.3 边界说明：** 上述 concern 保持属于 **Layer 2 ～ Layer 4**（`§4.4.2`）；
**不得**因本决定被提升为 package structural rejection（同 `IC-17` ／ `§4.3.28` `I-16`）。

**D. Manifest `"role"` value contract（Decision 5）**

```
Manifest "role" value = exact opaque JSON string
POC v0.2 Layer-1       = 不建立 exhaustive role enum
```

Layer 1 使用 **exact string equality** 执行**既有** structural invariants：

```
same role 不得有 duplicate ／ conflicting authoritative association
one included role → one authoritative artifact
different included roles 不得（被确认为）指向同一 physical artifact
filename 不得成为 role 的 authoritative source
不做 trim ／ case conversion ／ Unicode normalization ／ synonym conversion
```

```
"role" value 未出现在 §4.3.10 示例列表
      ⇒ 本身**不构成** Layer-1 unknown-content rejection
```

`§4.3.10` 的 logical role list **继续保持 illustrative**（本小节**未**修改该小节文本，
**未**把其升级为 exhaustive wire vocabulary）。
Role semantic recognition、capability-to-role requirement 与 role availability
属后续 validation ／ **Capability Readiness**。

**D.1 Manifest semantic-set carrier presence（Human Decision：presence = REQUIRED）**

`§4.3.8` ／ `§4.3.25 A` 要求 Manifest **实际承载**已批准的 semantic set。
本次 Human Decision 只批准 **carrier ／ property presence ＋ approved carrier location**，
并据此登记：

```
POC v0.2 Layer-1 carrier presence = REQUIRED
```

**`"package"` block 必须包含：**

```
snapshot_package_id
contract_version
created_at
environment
evidence_classification
completeness_state
```

**每个 included dataset entry 必须包含：**

```
role
artifact
record_count
provenance_ref
integrity_evidence
```

**`provenance_ref` 不设 value 约束** —— current canonical authority **未**为其登记任何
representation（URI ／ schema ／ 格式），因此本层**只**要求其存在，**不得**新增格式约束。

**本次**未**授权**新增以下规则（保持 `NOT DEFINED`）：

```
created_at 的新 timestamp format ／ timezone policy
environment 的新 enum
evidence_classification 的新 enum
provenance_ref 的新 URI ／ schema ／ 格式约束
completeness_state 的新 vocabulary 或 final-state gate
任何新的 business validation ／ capability rule
```

**`CF-1` 保持（`§4.3.28` B.3）：**

```
"completeness_state" = Manifest-declared metadata only
value 不直接参与 Layer-1 acceptance gate
```

**但 presence 是 REQUIRED：**

```
property presence = REQUIRED
presence required ≠ semantic value gates acceptance
```

**Layer 边界（不得越过）：**

Layer 1 只负责：

```
required carrier exists
carrier 在 approved group ／ entry 中
existing structural shape 可判定
```

以下 concern **不**因本登记而被拉入 Layer 1：

```
business requiredness（超出 presence 的部分）
capability readiness
semantic resolution
provenance sufficiency
business data completeness
per-role field applicability
downstream derived result policy
```

**E. Decision 6 明确 deferred 的问题（本层**未**决定，且**不**构成 Layer-1 blocker）**

```
POLICY_INPUT 最终通过 Snapshot 还是 runtime ／ analysis channel 提供
AnalysisDate ／ RecommendationNeedDate 等 CONTEXT field 的最终 input channel
derived results 是否应出现在某种 downstream artifact
per-role field applicability
capability-specific dataset requirements
```

这些问题**不得**借本次 known-member binding 被静默决定。

**F. Decision 7 —— `inbound record identity`（DEFER ／ ESCALATE）**

`§4.1.3` `E` ／ `§4.1.4` `E` 的 **Inbound Supply grain** 含 `inbound record identity`，
而 current canonical authority **未**为其登记任何 canonical field identifier。

```
本层不创建新 canonical field
本层不修改 Inbound grain
本层不把 Stable Source Evidence Locator 当作 inbound identity
```

⇒ 记录为**后续 canonical-object ／ `BR-INBOUND-001` implementation 前必须重新评估**的 item
（canonical-model completeness，非本层 wire binding）。
它**不**阻塞 Layer-1 loader。

**G. Registration Boundary（本小节）**

- 本小节**不**新增 canonical entity ／ business field ／ enum ／ status ／
  Validation Reason ／ Validation Category ／ carrier ／ sidecar；
- 本小节**不**修改 `BR-*` ／ Validation Taxonomy ／ Master Data Mapping ／ Data Dictionary 的
  business semantic、Class、Requiredness 或 vocabulary；
- 本小节**不**修改 `FROZEN` docs ／ `AGENTS.md` ／ `CONTRIBUTING.md`；
- 本小节**不**代表 implementation：**未**创建 JSON Schema ／ sample JSON ／ package directory ／
  `manifest.json` ／ dataset artifact ／ parser ／ serializer ／ validator ／ import service；
- 本小节**不**改变 `§4.3.10` ／ `§4.3.25` ／ `§4.3.28` ／ `§4.3.29` 的既有文本与结论。

**H. Referenced supporting clarification（不同文件，不在本小节）**

```
analysis run identity → analysis_run_id
inbound status / eligibility context → inbound_status
```

两项 **canonical field identifier naming clarification** 登记于
`data-dictionary.md`（`§4.2.3` ／ `§4.2.6`）；**只**固定 identifier 命名，
**未**改变 business semantic、Class、Requiredness 与 vocabulary。

**执行状态（本 Registration 时点）**

```
v0.2 record-level wire binding = REGISTERED（Issue #118 Human Decision）
Snapshot / Import Contract     = DESIGN RESOLVED（§4.3.1 ～ §4.3.29 结论未变）
Runtime implementation         = NOT STARTED（本登记不产生 runtime artifact）
POC Design v0.2                = DRAFT
POC success                    = NOT CLAIMED
```

#### 4.3.31 First-Tranche Wire → Canonical Object Construction Contract（Issue #125 Human Decision Record）

**Registration Status：`REGISTERED`** —— 依据 **Issue #125 Human Decision**（**D-1 ～ D-10 全部 `APPROVED`**）。

本小节**只**登记 first deterministic tranche 的 **downstream canonicalization** 与 wire contract 的边界：
**Layer-1 wire binding 完全不改**，只登记「已通过 Layer-1 acceptance ／ Layer-2 validation 的
record 如何被 downstream canonicalization 指派到 canonical target」，以及 `POLICY_INPUT` ／ `CONTEXT`
的注入边界。本小节**不**重开 `§4.3.1` ～ `§4.3.30`，**不**回写历史时点记录。

**A. Layer-1 opacity（本登记不得削弱）**

```
Layer-1 role             = exact opaque JSON string（不 trim ／ 不 case fold ／ 不 normalize）
Layer-1 role enum        = 不建立 exhaustive enum
§4.3.10 logical role list = 在 Layer 1 仍保持 illustrative
unknown ／ unrecognized role ≠ Layer-1 structural rejection
known property ≠ valid evidence ≠ applicable field ≠ required field（§4.3.30 C.2 未变）
```

**B. First-tranche recognized canonicalization role set（12 个 exact literal）**

以下集合**只服务 downstream canonicalization**；它不是 Layer-1 wire vocabulary，也不改变 `§4.3.10`
的 illustrative 状态。

| # | exact role literal | canonicalization target | role kind | assignment outcome |
| --- | --- | --- | --- | --- |
| 1 | `Plant / Material identity context` | entity **Plant** ＋ entity **Material**（§4.1.3 ／ §4.1.4 A ／ B） | identity context | assigned |
| 2 | `Production Requirement` | entity **Production Requirement**（§4.1.4 C） | entity（source） | assigned |
| 3 | `BOM Component` | entity **BOM Component**（§4.1.4 N） | relationship | assigned |
| 4 | `Inventory Snapshot` | entity **Inventory Snapshot**（§4.1.4 D） | entity（source） | assigned |
| 5 | `Configured Safety Stock` | entity **Configured Safety Stock**（§4.1.4 O） | entity（policy input） | assigned |
| 6 | `Inbound Supply` | entity **Inbound Supply**（§4.1.4 E） | entity（source） | assigned |
| 7 | `Substitute Relationship` | entity **Substitute Relationship**（§4.1.4 F） | relationship | assigned |
| 8 | `Substitute Allocation` | entity **Substitute Allocation**（§4.1.4 G） | relationship | assigned |
| 9 | `Supplier identity` | entity **Supplier**（§4.1.4 H） | identity | assigned |
| 10 | `Supplier-Material Relationship` | entity **Supplier-Material Relationship**（§4.1.4 I） | relationship | assigned |
| 11 | `Supplier Performance` | entity **Supplier Performance**（§4.1.4 J） | entity（source） | assigned |
| 12 | `Procurement policy input` | `ApplicableMOQ` 的 `POLICY_INPUT` channel（owner = Procurement Recommendation Context） | policy-input channel | assigned（**仅 Phase B**） |

本表**只**回答「该 role 的 evidence 被指派到哪个 canonical target」。
field-level validation ／ missing ／ type ／ status ／ semantic ／ provenance reason **一律委托既有
canonical taxonomy**（见 **§4.4.102**），不在本小节重定义。

**C. Unrecognized role behavior（D-9）**

```
unrecognized role = not_evaluable only at canonicalization stage
no automatic Validation Issue
no Layer-1 rejection
```

`§4.4.95` 要求只有「当前 capability 确实需要解释该 semantic」时才产生 `SEMANTIC_UNRESOLVED`；
本 tranche 的 canonicalization **不做** capability-specific readiness，因此**不得**把 unrecognized role
自动映射为该 Validation Issue。**不新增** Validation Category ／ Reason ／ status ／ enum。

**D. Inbound Supply identity representation（G3-A，D-4）**

```
first-tranche Inbound Supply identity representation
  = AcceptedPackage-scoped deterministic technical record reference
```

由以下三者共同确定：

```
- current AcceptedPackage identity
- exact recognized logical dataset role = `Inbound Supply`
- dataset-internal record ordinal over the accepted stable content view
```

**严格限定：**

```
只服务 first deterministic tranche 的 in-memory canonical-object identity ／ reference
deterministic for the same immutable AcceptedPackage accepted content view
能区分内容完全相同但位置不同的两条 inbound records
不进行 content-derived deduplication
不进行 cross-package identity matching
不创建 canonical business field
不创建 wire property
不创建 "_meta" member
不等于 Stable Source Evidence Locator
不等于真实 ERP PO ／ inbound line identity
不声称 production identity 已解决
```

**`G3-B` = `NOT SELECTED`。** 本登记**不批准** `inbound_record_id`；本 tranche 没有合法 carrier ／
source 可提供该 value（30-property closed set 不含它、不新增 wire property、不新增 `"_meta"` member、
external runtime business value 已被 **E** 禁止、injection 必须由 same AcceptedPackage evidence 支撑），
若采用将造成「approved canonical identity 但 current tranche 无法实例化」的 contract contradiction。

**`§4.3.30 F` 状态登记：**

```
first-tranche implementation representation
      = RESOLVED by G3-A
source-specific ／ real Adapter inbound business identity
      = OPEN ／ revisit before real Adapter or production integration
```

```
"implementation blocker 已解除"  ≠  "production identity design fully resolved"
```

`§4.3.30 F` 的 source-specific ／ real Adapter item **不得**被声称已最终关闭。

**E. Injection Boundary（D-10）—— in-process logical handoff only**

```
canonicalization injection = in-process logical handoff interface
```

它本身：

```
不是新的 external evidence source
不是新的 transport carrier
不是第二个 Snapshot Package
不允许绕过 AcceptedPackage
不允许 caller 任意提供新的 business fact
canonicalization API 参数 ≠ new top-level input carrier
```

对 `SOURCE` ／ `POLICY_INPUT` semantic（`loss_rate`、`SafetyStock`、effective demand context mapping
evidence、其他 source-derived ／ policy-derived canonical input）：若通过 injection 进入 canonicalization，
该 value ／ context **必须**已经由当前 Analysis Run 所绑定的 **same AcceptedPackage** evidence 可靠解析，
并保持既有 provenance：

```
Snapshot Package Identity
+ Logical Dataset Role
+ Stable Source Evidence Locator
+ Mapping / Resolution Basis（when applicable）
```

如果当前 AcceptedPackage 内**没有**可支撑该 semantic 的 evidence：

```
不得通过 external caller value 补齐
不得默认
不得 synthetic fallback
保持 unresolved ／ 既有 fail-safe 语义
```

特别登记：`SafetyStock` 在 `Configured Safety Stock` dataset absent 时，**仅当** same AcceptedPackage 内
存在另一份经 approved mapping 可可靠解析为 `SafetyStock` 的 policy evidence 时，才允许 internal
handoff；否则保持 unresolved。**不得**因此定义新的 capability requirement。

`analysis_run_id` ／ `AnalysisDate` 属 Analysis Run ／ CONTEXT，**不是** logical dataset source evidence：
其 provenance ／ binding = **Analysis Run identity ＋ exactly-one AcceptedPackage linkage**，
**不得**为其伪造 logical dataset role ／ Stable Source Evidence Locator；
而任何 source-derived value 被注入时仍**必须**遵守完整 package-scoped source provenance contract。

**本登记不修改 ADR-001**，**不新增 input carrier**。若未来需要支持
`Snapshot Package` ＋ `external runtime business ／ policy evidence` 作为同一个 Analysis Run 的业务输入，
**必须**重新进入：

```
Architecture Decision
→ Human Approval
→ ADR ／ provenance contract synchronization
```

**不得**由本登记静默授权。

**F. Phase ordering（D-7）**

```
Phase A — pre-rule canonicalization（Canonical data objects module）
  包含：Analysis Run context；source canonical entities ／ relationships（role 1 ～ 11）；
        loss_rate ＋ Requirement Calculation Context；SafetyStock；
        Inbound Supply technical record reference（G3-A）；BOM parent ／ requirement context；
        effective demand context relation outcomes
  不要求：RecommendationNeedDate；ApplicableMOQ Procurement Recommendation Context

Phase B — post-shortage procurement-context resolution
  Deterministic shortage rules → Classification ／ FirstShortageDate
  仅当 Procurement Recommendation applicable：
    RecommendationNeedDate = FirstShortageDate
      → 建立 Procurement Recommendation Context
      → 再执行 ApplicableMOQ resolution
```

```
RecommendationNeedDate = FirstShortageDate（§4.4.65）
RecommendationNeedDate ≠ 任意 runtime injected date；caller 不得覆盖 FirstShortageDate semantic
ApplicableMOQ 仅在 Phase B 的 Procurement Recommendation Context 中解析（§4.4.67）
Phase B 不得阻塞 Phase A
```

**G. Injection contract（D-7）**

| # | injected semantic | phase | binding key ／ target grain | value | provenance | resolution basis | cardinality | unresolved behavior | multi-applicable ／ conflict behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I-1 | Analysis Run context：`analysis_run_id` ＋ `AnalysisDate` | A | canonicalization invocation | `ANALYSIS_RUN_ID` ＋ `DATE` | Analysis Run identity ＋ exactly-one AcceptedPackage linkage（**不**要求 logical dataset role ／ Stable Source Evidence Locator） | n/a | exactly one | linkage 不可建立 → `not_evaluable`；`AnalysisDate` 保持 unresolved | **Stage B**（§4.4.68 ／ §4.4.93）→ `PROVENANCE` ／ `PROVENANCE_MISMATCH` |
| I-2 | `loss_rate` ＋ Requirement Calculation Context | A | `plant_id` ＋ parent/requirement `material_code` ＋ `required_date` ＋ component `material_code` | `RATIO` | required（same AcceptedPackage-scoped source provenance） | required | exactly one applicable or unresolved | §4.4.15 root **B** → `SEMANTIC_UNRESOLVED`；root **A** → `FIELD_VALUE` ／ `MISSING` | **Stage A** → `SEMANTIC_UNRESOLVED`；不得同值去重；不得自动 `CONSISTENCY_CONFLICT` |
| I-3 | `ApplicableMOQ` ＋ Procurement Recommendation Context | **B** | `plant_id` ＋ `material_code` ＋ `RecommendationNeedDate` | `NON_NEGATIVE_QUANTITY` | required（same AcceptedPackage-scoped source provenance） | required | exactly one applicable or unresolved | 无法识别 applicable → `SEMANTIC_UNRESOLVED`；applicable 但缺值 → `FIELD_VALUE` ／ `MISSING` | **Stage A**（§4.4.67）→ `SEMANTIC_UNRESOLVED` |
| I-4 | `RecommendationNeedDate` | **B** | Procurement Recommendation Context | `DATE`（= `FirstShortageDate`；caller 不得覆盖） | required | when applicable | exactly one | 保持 unresolved；`NORMAL` ／ `BUFFER_BREACH` ⇒ valid absence（§4.4.87） | **Stage B**（§4.4.65）→ `CONSISTENCY` ／ `CONSISTENCY_CONFLICT` |
| I-5 | `SafetyStock`（internal handoff） | A | `plant_id` ＋ `material_code` | `NON_NEGATIVE_QUANTITY` | required（same AcceptedPackage-scoped source provenance） | when mapping 发生 | exactly one applicable or unresolved | 保持 unresolved（不得默认 0） | **Stage B**（§4.4.92）→ `CONSISTENCY_CONFLICT` |
| I-6 | Inbound Supply technical record reference（G3-A）—— **非** injected business value | A | current AcceptedPackage identity ＋ recognized role `Inbound Supply` ＋ dataset-internal record ordinal | technical record reference（**不是** canonical ／ wire property ／ `"_meta"` member） | required（绑定 same AcceptedPackage ／ accepted content view） | n/a | exactly one reference per accepted inbound record | 无法形成 → `UNRESOLVED_IDENTITY` | **Stage A**（§4.5.3 condition **C**）→ `UNRESOLVED_IDENTITY` |
| I-7 | BOM parent ／ requirement context（G4-A） | A | `BOM Component` evidence → resolved Production Requirement context | context reference | required | n/a | exactly one context per evidence set | `UNRESOLVED_IDENTITY` | **Stage A**（§4.4.11）→ `UNRESOLVED_IDENTITY` |
| I-8 | effective demand context relation outcomes（G5-A） | A | source substitute material ＋ target material ＋ allocation record | two independent relation outcomes（references） | required（same AcceptedPackage-scoped source provenance） | required | exactly one pair or unresolved | `SEMANTIC_UNRESOLVED` | **Stage A**（§4.4.60 path **B**）→ `SEMANTIC_UNRESOLVED` |
| I-9 | Inventory ownership ／ POC Inventory Scope resolution（A′） | A | exact `Inventory Snapshot` evidence citation | runtime Inventory scope context（ownership ＋ scope membership），derived by the approved deterministic basis registry | required（same AcceptedPackage-scoped source provenance） | required（exact association `mapping_basis`） | exactly one applicable resolution per Inventory evidence or unresolved | ownership → `IDENTITY_RESOLUTION` ／ `UNRESOLVED_IDENTITY`；scope → `SCOPE_COVERAGE` ／ `UNRESOLVED_SCOPE` | **Stage A**（§4.4.102 C）→ unresolved；不得 first ／ last wins、不得同值去重、不得跨 association 借用 basis |

injection **不**决定任何真实 ERP ／ source file ／ ERP field physical carrier；`loss_rate` 的
Entity ／ Dataset ／ Source Field 归属仍**不得**决定（§4.4.15）。

**I-9 —— Inventory ownership ／ POC Inventory Scope resolution（A′，Issue #136 Human Decision）**

**Registration Status：`REGISTERED`** —— 依据 **Issue #136 Human Decision**（**Inventory Runtime
Seam Decision `A′` = `APPROVED`**，2026-09-25）。

```text
Phase                     = A
binding key               = exact Inventory Snapshot evidence citation
input authority           = same AcceptedPackage evidence only
association               = exact existing canonical observation
                            + exact Stable Source Evidence Locator
                            + exact mapping_basis
outcome                   = runtime Inventory scope context
                            derived by approved deterministic basis registry
caller-provided outcome   = FORBIDDEN
cardinality               = exactly one applicable resolution per Inventory evidence, or unresolved
unresolved ownership      = IDENTITY_RESOLUTION / UNRESOLVED_IDENTITY
unresolved scope          = SCOPE_COVERAGE / UNRESOLVED_SCOPE
```

**严格限定：**

```text
not a new external evidence source
not a transport carrier
not a second Snapshot Package
not a canonical field
not a Warehouse entity
not a new calculation grain
```

caller **只能**引用 exact AcceptedPackage evidence ＋ exact existing canonical observation
association ＋ exact evidence locator ＋ exact `mapping_basis` registered on that association；
**不得**提供 `in_scope` ／ scope membership value ／ `warehouse_id` ／ Plant ownership value 等任何
outcome 值。scope outcome **必须**由已经登记的 deterministic SIMULATED mapping registry 导出：

```text
exact association + exact registered mapping_basis + approved inventory-scope mapping rule
  → deterministic scope outcome
```

**注意（不得混淆）：**

```text
mapping_basis ≠ mapping outcome
```

仅仅存在 `mapping_basis` **不足以**证明 scope membership；Plant ownership 始终来自 accepted
canonical evidence（该 record 自身的 `plant_id`），**不得**来自 caller、**不得**默认成 current
Plant、**不得**由 Warehouse 名称 ／ description 推断。`§4.5.12` 登记 Shape A ／ Shape B 的
basis literal → semantic（`IN_SCOPE` ／ `OUT_OF_SCOPE`）；`OUT_OF_SCOPE` 是**合法 exclusion**，
**不是** `DATA_INCOMPLETE`、**不是** Data Quality defect。

**本登记不修改 D-10，不新增 wire property ／ `"_meta"` member ／ canonical business field ／
canonical entity，也不新增 Validation Category ／ Reason ／ status ／ enum。**

**H. Registration Boundary ／ status**

- 本小节**不**新增 wire property ／ `"_meta"` member ／ canonical business field ／ canonical entity；
- 本小节**不**新增 Validation Category ／ Reason ／ status ／ enum；
- 本小节**不**修改 `BR-*` ／ Data Dictionary 的 Class ／ Requiredness ／ vocabulary；
- 本小节**不**修改 `FROZEN` docs ／ `AGENTS.md` ／ `CONTRIBUTING.md` ／ `adr-001-deterministic-core.md`；
- 本小节**不**代表 implementation：**未**创建 parser ／ serializer ／ validator ／ canonical object。

```
first-tranche wire → canonical object construction contract = REGISTERED（Issue #125 Human Decision）
Layer-1 wire binding                                        = 未改变
Snapshot / Import Contract                                  = DESIGN RESOLVED（§4.3.1 ～ §4.3.30 结论未变）
Runtime implementation                                      = NOT STARTED
POC success                                                 = NOT CLAIMED
```

---

<!-- END MIGRATED LEGACY §4.3 BODY -->
