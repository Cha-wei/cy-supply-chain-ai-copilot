# Discovery Validation v0.1

**项目：** Yunnan CY Group Supply Chain AI Copilot
**文档版本：** v0.1
**文档状态：** `DRAFT`
**文档性质：** Discovery Validation Phase 的 Canonical Source
**依据基线：** `docs/discovery/discovery-brief-v0.1.1.md`（v0.1.1，`FROZEN`）

> **层级关系**：业务基线以 `FROZEN` 的 Discovery Brief 为准。本文档**不修改** Brief 的任何内容，不新增 P0/P1 范围，不定义 POC Design 内容，只负责登记「需要验证什么」以及「已验证什么」。
>
> **本项目为模拟 FDE 项目。** 本文档中所有经 Human 提供或批准的验证输入，均标记为 `SIMULATED`。除 Brief 已登记的 `PUBLIC FACT` / `PUBLIC CLAIM` 外，本文档不引入任何新的外部事实。

---

## 1. Purpose

本文档的目的是在 Discovery 与 `POC Design v0.2` 之间建立一个**可追踪的验证台账**，回答三个问题：

1. 当前项目相对 Discovery Brief §19 的 Entry Criteria，**还缺哪些证据**？
2. 这些证据**如何获得**、由**谁负责**、以及**是否阻塞**进入 `POC Design v0.2`？
3. 已经获得的验证输入**是什么**，以及它们属于哪一类证据？

本文档**不做**以下事情：

- 不修改 `FROZEN` Discovery Brief 中的原始 **Evidence Classification / Evidence Status**；但可以基于 Human-approved Validation Evidence 记录后续 **Discovery Validation Current Status**
- 不编造 Stakeholder 回答、业务数据、系统信息或接口现状
- 不开始 POC Design，不定义缺料计算口径、RBAC、HITL 状态机、风险评分卡
- 不选择技术栈，不创建 ADR
- 不将模拟设定解释为云南 CY 集团的真实业务事实

### 1.1 分阶段 Validation 策略

本项目采用分阶段验证，**不一次性要求全部模拟输入**。

| 阶段 | 范围 | 说明 |
| --- | --- | --- |
| **Phase 1A** | **Problem Validation** | 优先验证 H1、H2、P0 核心业务闭环、当前人工流程痛点、Human-in-the-loop 业务边界 |
| **Phase 1B** | **Data & System Readiness** | 后续验证 Production Plan、BOM、Inventory、Purchase Order / Inbound、Data Readiness、Integration / Access assumptions |

Phase 1A 未取得进展前，不启动 Phase 1B。

---

## 2. Simulation Evidence Protocol

本项目是模拟 FDE 项目。本节定义模拟证据的**生成条件、标记要求与使用边界**。

### 2.1 角色

Human 可以明确以模拟 Stakeholder 角色提供或批准业务输入，例如：

- Simulated Sponsor
- Simulated Business Owner
- Simulated Procurement / Supply Chain User
- Simulated Customer IT

### 2.2 有效性条件

经 Human **明确提供或明确批准**的输入，可以作为本模拟项目 Discovery Validation 与 Entry Criteria 的有效证据。

**Agent 不得自行扮演 Stakeholder 并生成证据。** 只有 Human 提供或明确批准的内容，才可以形成模拟验证证据。

### 2.3 强制标记

所有模拟证据必须明确标记 `SIMULATED`，并且：

- 只代表本模拟项目中的业务设定；
- **不得**标记或解释为 `PUBLIC FACT`；
- **不得**声称来源于真实客户访谈；
- **不得**声称来源于真实企业内部系统；
- **不得**传播为云南 CY 集团真实业务事实。

### 2.4 与 Brief 证据分级的关系

Discovery Brief §3 定义四级：`PUBLIC FACT` / `PUBLIC CLAIM` / `HYPOTHESIS` / `UNKNOWN`。

`SIMULATED` 是本文档引入的**证据来源标记**，与上述四级**正交**：它描述"证据怎么来的"，不提升信息的真实性等级。因此：

> **`SIMULATED` 证据不得被记作 `PUBLIC FACT`，也不得在未标明来源的情况下与 `PUBLIC FACT` 混列。**

### 2.5 Entry Criteria 的模拟判定

在本模拟项目中，Brief §19 中的「客户认可」「主要业务 Owner 认可」「客户 IT 确认」**允许由 Human 以对应模拟 Stakeholder 角色完成**，满足条件时可用于判断 Entry Criteria。

每一条件必须记录以下字段（见第 9 节）：

```
Evidence Type: SIMULATED
Role:
Date:
Question / Decision:
Human-provided or Human-approved:
Result:
```

---

## 3. Core Hypotheses

Brief §7 提出 4 个假设。Brief §8 验证矩阵中的原始结论为 `TBD`；本文档根据 Human-approved `SIMULATED` 证据记录当前状态如下。

### 3.1 H1–H4 现状

| ID | 假设 | Brief 状态 | 当前状态 | 依据 | 是否阻塞进入 POC Design | 阶段 |
| --- | --- | --- | --- | --- | --- | --- |
| **H1** | 跨系统查询成本较高 | `HYPOTHESIS` / `TBD` | **`PARTIALLY CONFIRMED`** | `VR-001`（SC-ASIS-001）：建立跨多个业务数据源查询、核对，以及 60–120 分钟模拟分析基线 | **YES**（§19 Problem Validation） | **Phase 1A** |
| **H2** | 缺料判断存在人工汇总 | `HYPOTHESIS` / `TBD`（对应 E09） | **`PARTIALLY CONFIRMED`** | `VR-001`（SC-ASIS-001）：存在 Excel / 人工关联 / 二次计算 / 筛选过程 | **YES**（§19 Problem Validation） | **Phase 1A** |
| **H3** | 部分风险判断依赖业务经验 | `HYPOTHESIS` / `TBD` | `TBD`（本 Task 未扩大验证范围） | — | **NO** | Phase 1A（次级） |
| **H4** | 缺料处理存在较高的信息解释成本 | `HYPOTHESIS` / `TBD` | `TBD`（本 Task 未扩大验证范围） | — | **NO** | Phase 1A（次级） |

> **为什么 H1 / H2 只到 `PARTIALLY CONFIRMED`，不升级为 `CONFIRMED`**：
> 当前依据是 **Human-approved `SIMULATED` baseline**，尚未通过更完整的 Mock Case 或 POC measurement 进一步验证。因此本状态不代表已获独立核验的事实。
>
> **H3 / H4 保持 `TBD`**：即使现有场景中包含相关线索，本 Task 有意不扩大验证范围。它们仍须按"决策 5 的落实"进入 Validation Backlog（见 VB-27、VB-28）。

**决策 5 的落实**：H3 / H4 允许暂时保持未确认，但**必须**进入 Validation Backlog，明确 `Validation Method` / `Owner` / `Status` / `Blocking`（见 VB-27、VB-28），**不得长期作为无人处理的 `TBD`**。

### 3.2 其他影响 P0 成立的关键假设

以下未被 Brief 显式编号，但直接决定 P0 可行性，一并纳入验证范围。

| ID | 隐含假设 | 依据 | 当前 Validation Progress | 是否阻塞 |
| --- | --- | --- | --- | --- |
| **H5** | 存在可获取的生产计划 / BOM / 库存 / 在途 / 供应商数据 | Brief §19 Data Readiness | **`PARTIALLY CONFIRMED`**（`VR-005` ＋ `VR-006`） | YES（Phase 1B） |
| **H6** | 关键主数据可以建立基本关联 | Brief §19 Data Readiness 末项 | **`PARTIALLY CONFIRMED`**（`VR-006`） | YES（Phase 1B） |
| **H7** | POC 可以只读 + 草稿方式接入，无需写入生产业务系统 | Brief §10、§11 P0-3 | 保持现有状态（未变更） | NO（但实现前必须确认） |

> **`H5` / `H6` 的当前 Validation Progress**：基于 `VR-005`（SC-DATA-001）＋ `VR-006`（SC-DATA-002）两份 Human-approved `SIMULATED` evidence，Data Readiness baseline 已覆盖。因此：
>
> > **H5 = `PARTIALLY CONFIRMED`；H6 = `PARTIALLY CONFIRMED`.**
>
> **不得升级为 `CONFIRMED`** —— 依据仍为 Human-approved `SIMULATED` baseline，尚未经更完整 Mock Case / POC measurement 验证。
>
> **`H7` 保持现有状态**，本 Task 未变更。
>
> **`H1` / `H2` 保持 `PARTIALLY CONFIRMED`；`H3` / `H4` 保持 `TBD`。** 本 Task 未变更它们（见 §3.1）。
>
> **未修改 FROZEN Brief。** 本 Task **不引入新的假设编号**。

> **关于 Brief §8「假设不得长期停留在模糊状态」的当前状态**：
>
> 需区分两个层面，不得混为一谈：
>
> | 层面 | H1 / H2 | H3 / H4 |
> | --- | --- | --- |
> | **FROZEN Discovery Brief 中的原始状态** | `HYPOTHESIS` / `TBD` —— **未被修改** | `HYPOTHESIS` / `TBD` —— **未被修改** |
> | **本文档（Discovery Validation）记录的当前状态** | **`PARTIALLY CONFIRMED`**（依据 `VR-001`） | **`TBD`** |
>
> 即：Brief §8 矩阵中的原始 `TBD` 记录**保持不变**（FROZEN 文档不得修改）；假设的实际推进状态由本文档记录。当前 H1 / H2 已脱离模糊状态，**H3 / H4 仍为 `TBD`** —— 因此 Brief §8 的该要求**尚未完全满足**。本文档状态为 `DRAFT`。

---

## 4. Blocking UNKNOWNs

只列真正影响 P0 / Data Readiness / Integration / HITL / Business Rules / POC Design 的项目。已刻意避免机械罗列无关 Unknown。

### 4.1 来自 Brief §3 Evidence Register

> **⚠️ 层级区分说明（重要）**：下表的 `Brief 状态` 列记录的是 **FROZEN Discovery Brief 中的原始 Evidence Classification**，该列**未被修改**，也不得被修改。
>
> 本节**不是**当前验证状态的唯一来源。某一项在 Brief 中为 `UNKNOWN`，**不等于**其至今仍未被验证 —— 后续 Discovery Validation 的当前状态由本文档 §9 的 Validation Records 及相应章节记录。
>
> 例如：`E10` 在 Brief 中为 `UNKNOWN`（原始分类，保持不变），而对应的当前验证进展为 **resolved / supported by `VR-006`**（见 §9.2 `VR-006`、§6.1 `D5`、§7.2 `VB-12`）。**两者是不同层级，不得混为一谈。**
>
> `SIMULATED` Evidence **不得**写成 `PUBLIC FACT`。

| ID | Unknown | Brief 状态（原始分类，未修改） | 影响面 | 需确认方 | 阶段 | 当前 Discovery Validation |
| --- | --- | --- | --- | --- | --- | --- |
| **E05** | 当前实际 ERP 品牌及版本 | `UNKNOWN` | Data Readiness、Integration、H1 判定 | Simulated Customer IT | Phase 1B | 部分由 `VR-006` 支持（canonical 标识与关联）；**完整技术接入能力仍待 `VB-19`** |
| **E06** | 是否存在独立 WMS | `UNKNOWN` | Data Readiness（库存数据来源） | Simulated Customer IT | Phase 1B | 数据维度可得由 `VR-005` 支持；**系统归属未确认** |
| **E07** | BOM 由哪个系统管理 | `UNKNOWN` | Data Readiness、P0-1 计算输入 | Simulated Customer IT | Phase 1B | BOM 数据可得由 `VR-005` 支持；**系统归属未确认** |
| **E08** | 当前真实缺料分析流程 | `UNKNOWN` | Problem Validation（H1/H2）、Baseline、HITL | Simulated Procurement / Supply Chain User | **Phase 1A** | resolved / supported by `VR-001`（当前模拟场景 As-Is 流程） |
| **E10** | 供应商绩效数据是否已结构化记录 | `UNKNOWN` | P0-2「风险证据」深度、H3 | Simulated Procurement / Supply Chain User | Phase 1B | **resolved / supported by `VR-006`**（基础 Supplier Performance 数据可得且结构化） |
| **E09** | 当前缺料分析存在 Excel 或人工二次处理 | `HYPOTHESIS` | H2 的核心内容 | Simulated Procurement / Supply Chain User | **Phase 1A** | resolved / supported by `VR-001`（`H2` = `PARTIALLY CONFIRMED`） |

### 4.2 来自 Brief §18 Known Unknowns（按影响面聚类）

**（a）Data Readiness**

> **⚠️ 层级区分说明（重要）**：下表 `阶段` 列表示该项**归属的验证阶段**，**不代表当前状态**。`K-DR-*` 是 **Brief §18 的原始 Known Unknowns 列表**（原始分类保持不变）。其当前验证进展见"当前 Discovery Validation"列。
>
> `K-DR-*` 在原始 Brief 中为"未知事项"，与本文档记录的**当前验证状态**属不同层级。`SIMULATED` Evidence **不得**写成 `PUBLIC FACT`。

| ID | Unknown | 影响 | 阶段 | 当前 Discovery Validation |
| --- | --- | --- | --- | --- |
| **K-DR-1** | 真实生产计划结构 | P0-1 输入契约 | Phase 1B | resolved / supported by `VR-005`（§6.1 `D1`） |
| **K-DR-2** | BOM 版本机制 | P0-1 计算口径 | Phase 1B | 数据可得与 Revision / Effectivity 由 `VR-005` 支持（`D2`）；**版本选择规则属 POC Design v0.2，未定义** |
| **K-DR-3** | 物料编码规则 | 主数据关联（H6） | Phase 1B | **resolved / supported by `VR-006`**（canonical 标识基线与稳定 Mapping；§6.1 `D6`、§7.2 `VB-13`） |
| **K-DR-4** | 库存状态 / 质检冻结库存 | P0-1「预计可用量」口径 | Phase 1B | 库存状态数据可得由 `VR-005` 支持（`D3`）；**可用量口径属 POC Design v0.2，未定义** |
| **K-DR-5** | 有效在途定义 | P0-1「预计缺口」、P0-2「有效在途」 | Phase 1B | 采购 / 在途数据可得由 `VR-005` 支持（`D4`）；**"有效在途"算法属 POC Design v0.2，未定义** |
| **K-DR-6** | 供应商 Lead Time | P0-2「供应周期」 | Phase 1B | **resolved / supported by `VR-006`**（Standard Lead Time 可得；§6.1 `D5`、§7.2 `VB-12`） |

**（b）Business Rules**

| ID | Unknown | 影响 | 阶段 |
| --- | --- | --- | --- |
| **K-BR-1** | 「缺料」的定义 | P0-1 判定起点 | Phase 1A |
| **K-BR-2** | 安全库存逻辑 | P0-1「预计可用量」 | POC Design 内细化 |
| **K-BR-3** | 替代料规则 | 缺口是否可被替代料抵消 | POC Design 内细化 |
| **K-BR-4** | 损耗率规则 | 需求量计算 | POC Design 内细化 |
| **K-BR-5** | MOQ 规则 | P0-2「建议采购数量」 | POC Design 内细化 |

**（c）Integration**

| ID | Unknown | 影响 | 阶段 |
| --- | --- | --- | --- |
| **K-INT-1** | 业务系统接口能力 | §19 Integration 三项 | Phase 1B |
| **K-INT-2** | 现有 MRP 能力 | **H1 的证伪风险** | Phase 1A |
| **K-INT-3** | 现有缺料预警机制 | 决定 AI 层增量价值 | Phase 1A |

**（d）HITL / 权限**

| ID | Unknown | 影响 | 阶段 |
| --- | --- | --- | --- |
| **K-HITL-1** | 审批权限归属 | P0-3 HITL 边界、权限不得高于操作用户 | Phase 1A |
| **K-HITL-2** | 角色与权限矩阵现状 | Brief §6 七类角色的真实存在性 | Phase 1A |

### 4.3 明确排除

以下 Brief §18 项不影响上述六个面，故不逐条建单：与 P0 无关的 P1 能力（Brief §12）。此为有意取舍，非遗漏。

---

## 5. P0 Validation Gaps

Brief §11 已给出 P0 的**业务定义**；但几乎所有计算口径与数据契约仍依赖待验证事实。

### 5.1 已有正式定义的部分

| P0 部分 | Brief 依据 | 性质 |
| --- | --- | --- |
| P0-1 缺料分析的输入（生产计划 → 产品/数量/BOM/库存/有效在途/必要供应链数据） | §11 P0-1 | 业务定义已冻结 |
| P0-1 输出类别（物料需求 / 预计可用量 / 预计缺口 / 基础风险） | §11 P0-1 | 输出类别已冻结 |
| P0-2 采购建议字段清单（9 项） | §11 P0-2 | 字段清单已冻结 |
| P0-3 HITL 边界（AI 只能产出采购申请草稿） | §11 P0-3 | 硬边界已冻结 |
| AI / 确定性逻辑分工 | §13 | 边界已冻结 |
| 三要求：受控 / 可解释 / 可追溯 | §10 | 要求已冻结 |
| P0 目标流程 | §11 P0-3 | 流程已冻结 |

### 5.2 仍依赖待验证事实的部分（Validation Gaps）

| ID | P0 部分 | 依赖的待验证事实 | 缺口性质 | 关联 Backlog |
| --- | --- | --- | --- | --- |
| **G-01** | P0-1 输入：生产计划结构 | K-DR-1 | 数据契约未定义 | VB-08 |
| **G-02** | P0-1 输入：BOM 版本机制 | K-DR-2、E07 | 数据契约未定义 | VB-09 |
| **G-03** | P0-1 计算：物料需求 | K-BR-4、K-DR-3 | 计算口径未定义 | VB-13、VB-17 |
| **G-04** | P0-1 计算：预计可用量 | K-BR-2、K-DR-4 | 计算口径未定义 | VB-10、VB-15 |
| **G-05** | P0-1 计算：预计缺口 | K-DR-5、K-BR-3 | 计算口径未定义 | VB-11、VB-16 |
| **G-06** | P0-1 计算：基础风险 | H3、E10、K-DR-6 | 风险规则未定义 | VB-27、VB-12 |
| **G-07** | P0-1 判定起点：「缺料」定义 | K-BR-1 | 判定标准未定义 | VB-14 |
| **G-08** | P0-2 字段：需求日期 | K-DR-1 | 依赖未验证输入 | VB-08 |
| **G-09** | P0-2 字段：供应周期 | K-DR-6 | 依赖未验证数据 | VB-12 |
| **G-10** | P0-2 字段：建议采购数量 | K-BR-5 | 计算口径未定义 | VB-18 |
| **G-11** | P0-2 字段：风险证据 | H3、E10 | 证据来源未确认 | VB-27、VB-12 |
| **G-12** | P0-3 HITL 权限归属 | K-HITL-1、K-HITL-2 | 权限模型未定义 | VB-21、VB-22 |
| **G-13** | P0 全部：数据从哪来 | K-INT-1、E05、E06 | 接入路径未确认 | VB-19、VB-20 |
| **G-14** | P0 是否值得做 | H1、H2、K-INT-2、K-INT-3 | 问题价值未验证 | VB-01～VB-06 |

> **边界声明**：本表只指出「哪些 P0 部分依赖未验证事实」。Brief §20 已将缺料计算完整口径、BOM 版本、损耗率、替代料、MOQ、库存状态、有效在途、风险评分卡、规则版本、数据字典、主数据编码、POC 测试集、RBAC 矩阵、HITL 状态机、审批矩阵、审计事件 Schema 等划归 `POC Design v0.2`。本文档**不得**代其定义。

---

## 6. Entry Criteria Status

判断依据仅限**现有仓库证据**。不得自行创造证据。

### 6.1 逐项状态

| # | Entry Criterion（Brief §19） | 状态 | 判断依据 |
| --- | --- | --- | --- |
| **P1** | H1 / H2 中至少一项为 `CONFIRMED` 或 `PARTIALLY CONFIRMED` | `SATISFIED` | `VR-001`：H1 / H2 均达 `PARTIALLY CONFIRMED`（两项均满足） |
| **P2** | 已识别至少一个具有明确业务价值的缺料分析问题 | `SATISFIED` | `VR-003`（SC-BIZ-001）：已明确识别具有业务价值的缺料分析问题 |
| **P3** | 主要业务 Owner 认可该问题值得进入 POC | `SATISFIED` | `VR-003`（SC-BIZ-001）：Simulated Business Owner / Sponsor 已 Human-approved |
| **S1** | 客户认可 P0 闭环：缺料分析 → 采购建议 → HITL | `SATISFIED` | `VR-003`（SC-BIZ-001）：已 Human-approved P0 闭环 |
| **S2** | P0 与 P1 边界已确认 | `SATISFIED` | `VR-003`（SC-BIZ-001）：已认可 P0 聚焦核心闭环，RAG / 高级查询 / 复杂供应商智能 / 扩展报告属 P1 / Future |
| **S3** | POC 不承担完整 ERP/MRP 替代职责 | `SATISFIED` | `VR-002`（SC-ASIS-002）＋ `VR-003`：已认可 AI Copilot 不替代 ERP / MRP，仅形成受控决策协同层 |
| **D1** | 生产计划数据可获取 | `SATISFIED` | `VR-005`（SC-DATA-001）Human-approved `SIMULATED` Data Readiness baseline：Production Plan 数据可得且具备最低必要结构 |
| **D2** | BOM 数据可获取 | `SATISFIED` | `VR-005`（SC-DATA-001）：BOM 数据可得，支持 multi-level，含 Revision / Effectivity 信息 |
| **D3** | 库存数据可获取 | `SATISFIED` | `VR-005`（SC-DATA-001）：Inventory 与 inventory status 数据可得 |
| **D4** | 采购订单 / 在途数据可获取 | `SATISFIED` | `VR-005`（SC-DATA-001）：Purchase Order / Inbound 数据可得，可表达 Ordered / Received / Open Qty 与 Promised / Expected Arrival Date |
| **D5** | 必要供应商信息可获取 | `SATISFIED` | `VR-006`（SC-DATA-002）Human-approved `SIMULATED`：Supplier Master、Supplier-Material Relationship、Standard Lead Time、基础 Supplier Performance 信息均可得且结构化 |
| **D6** | 关键主数据可以建立基本关联 | `SATISFIED` | `VR-006`（SC-DATA-002）：存在 canonical 标识基线与稳定、可追踪的基本映射关系（含 Local ID → Canonical ID mapping） |
| **B1** | 当前人工流程已经记录 | `SATISFIED` | `VR-001`（SC-ASIS-001）：已记录当前模拟场景 As-Is 流程 |
| **B2** | 当前流程主要步骤数量已经确认 | `SATISFIED` | `VR-001`（SC-ASIS-001）：已形成明确流程步骤 |
| **B3** | 当前分析平均耗时已经测量或获得可靠估算 | `SATISFIED` | `VR-001`：Human-approved simulated baseline，单次约 **60–120 分钟**（**`SIMULATED ESTIMATE`**，非真实测量数据） |
| **B4** | 当前涉及角色已经确认 | `SATISFIED` | `VR-001`（SC-ASIS-001）：当前流程主要涉及角色为计划员、采购员、供应链负责人 |
| **I1** | POC 数据接入路径已确认 | `NOT SATISFIED` | K-INT-1 未确认 |
| **I2** | 已明确通过 API / 数据库 / 导出文件 / 模拟接口中的何种方式接入 | `NOT SATISFIED` | 尚无决定 |
| **I3** | 基础访问权限和数据安全边界已确认 | `NOT SATISFIED` | **业务**角色、Data Scope 与 Permission Boundary 已由 `VR-004` Human-approved `SIMULATED` evidence 确认；但 `I3` 仍未满足，因为以下**技术访问与数据安全**事项尚未确认：实际 POC 数据访问路径、Access mechanism、Read / Write boundary、数据安全边界、环境与访问隔离。这些由 **Phase 1B 的 `VB-19` / `VB-20`** 继续验证 |

> **`B4 SATISFIED` ≠ `I3 SATISFIED`**：`B4` 由当前流程**主要角色**的确认而满足；`I3` 要求**基础访问权限与数据安全边界**确认，这是两个不同 Gate。
>
> 需注意：`VR-004`（SC-GOV-001）已确认**完整业务角色集合、业务 Data Scope 与业务 Permission Boundary**（因此 `VB-21` / `VB-22` 已完成），但该证据属**业务治理层面**，**不等于** `I3` 所要求的技术访问与数据安全边界（实际 POC 数据访问路径、Access mechanism、Read / Write boundary、数据安全边界、环境与访问隔离）。因此 `I3` 保持 `NOT SATISFIED`，由 Phase 1B 的 `VB-19` / `VB-20` 继续验证。

### 6.2 汇总

| 状态 | 数量 | 条目 |
| --- | --- | --- |
| `SATISFIED` | **16** | P1–P3、S1–S3、B1–B4、D1–D6 |
| `PARTIALLY SATISFIED` | **0** | — |
| `NOT SATISFIED` | **3** | I1、I2、I3 |
| `UNKNOWN` | **0** | — |

> **总数核对**：`16 + 0 + 3 + 0 = 19`。Entry Criteria 总数仍为 **19**，未增删任何条目，各具体条目的判定依据均已更新。

> **状态升级的依据**：`SATISFIED` 的 16 条全部基于 Human-approved `SIMULATED` 证据（`VR-001` / `VR-002` / `VR-003` / `VR-004` / `VR-005` / `VR-006`），**仅代表本模拟项目的业务设定**，不得解释为云南 CY 集团真实业务事实。
>
> **`S1–S3` 的升级说明**：前一版本保持 `PARTIALLY SATISFIED` 的原因是"Brief 已有定义不等于 Stakeholder 已认可"。`VR-003`（SC-BIZ-001）已提供 Human-approved 的 Stakeholder 认可，**升级条件已满足**，故升为 `SATISFIED`。
>
> **`D1–D4` 的升级说明**：`VR-005`（SC-DATA-001）已提供 Human-approved `SIMULATED` Data Readiness baseline，确认 Production Plan、BOM、Inventory、Purchase Order / Inbound 四类数据**可得且具备最低必要结构**。
>
> **`D5` / `D6` 的升级说明（本次）**：`VR-006`（SC-DATA-002）已提供 Human-approved `SIMULATED` 证据，确认**供应商数据**（Supplier Master、Supplier-Material Relationship、Standard Lead Time、基础 Performance）可得，以及**关键主数据可建立稳定、可追踪的基本映射关系**。
>
> > **`SATISFIED` 的准确含义**：仅表示**该数据域在本模拟项目中已被设定为可获取，足以继续 POC 设计**。
> > **不表示**真实 CY 系统已被检查或接入。
>
> > **`D5 SATISFIED` ≠ Supplier Risk / Ranking 规则已设计。** 供应商风险评分、排名、自动选择等仍属后续 `POC Design`。
> >
> > **`D6 SATISFIED` 只意味着关键主数据可以建立基本关联。** **不代表**所有企业主数据质量完美、不存在 Mapping Error、已设计 MDM 系统、或已实现数据清洗流程。
>
> **`I1` / `I2` / `I3` 保持 `NOT SATISFIED`**：属 **Integration** 组，需要确认实际 POC 数据访问路径、接入方式、技术身份 / Access mechanism、Read / Write boundary、数据安全边界与必要的环境与访问隔离。**不得在本阶段的证据中推断其已满足。** 这些由 `VB-19` / `VB-20` 继续验证。
>
> **`Data Readiness Gate`（`D1`–`D6`）：`COMPLETE`** ｜ **`Integration Gate`（`I1`–`I3`）：`NOT SATISFIED`**

---

## 7. Validation Backlog

`Blocks POC Design?` 严格以 **Brief §19 Entry Criteria 是否为该条所必需** 为判据，不引入自创评分。

**Owner 约定**：所有 `Owner` 为 `Human`（提供或批准模拟输入）；`Agent` 只负责登记与整理，**不得自行生成证据**。`Status` 初始值一律为 `NOT STARTED`。

### 7.1 Phase 1A — Problem Validation（优先）

> ## Phase 1A — Problem Validation：`COMPLETE`
>
> `VR-001` / `VR-002` / `VR-003` / `VR-004` 四份 Human-approved `SIMULATED` 记录已登记。
>
> Phase 1A 的 **Blocking items 共 10 项，现已全部 `VALIDATED / COMPLETED`**：
>
> | 状态 | 数量 | ID |
> | --- | --- | --- |
> | ✅ 已完成 Blocking | **10** | VB-01、VB-02、VB-03、VB-04、VB-05、VB-06、VB-07、VB-21、VB-22、VB-23 |
> | ⛔ 仍未完成 Blocking | **0** | — |
>
> `VB-24` / `VB-25` / `VB-26` 同样为 `VALIDATED / COMPLETED`，但它们属 **NON-BLOCKING** Validation Items，**不计入「已完成 Blocking items」数量**。
>
> > ### ⚠️ 关键边界：Phase 1A `COMPLETE` ≠ POC Design v0.2 Entry Gate `COMPLETE`
> >
> > Phase 1A 只覆盖 **Problem Validation** 与部分 **Baseline / Scope Validation**。进入 `POC Design v0.2` 仍需完成 **Phase 1B — Data & System Readiness**（Data Readiness 与 Integration 两组）。
> >
> > **当前阶段状态**：
> >
> > | 阶段 | 状态 |
> > | --- | --- |
> > | Phase 1A — Problem Validation | `COMPLETE` |
> > | Phase 1B — Data & System Readiness | `IN PROGRESS` |
> > | `POC Design v0.2` | `NOT READY` |
> >
> > **当前 Entry Criteria**：`SATISFIED = 16` / `PARTIALLY SATISFIED = 0` / `NOT SATISFIED = 3` / `UNKNOWN = 0`。
> >
> > **剩余未满足项**：`I1`、`I2`、`I3`（Integration Gate）。
> >
> > `Data Readiness Gate`（`D1`–`D6`）：`COMPLETE`。

| ID | Question | Current Evidence Status | Why It Matters | Evidence Needed | Suggested Validation Method | Owner | Status | Blocks? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **VB-01** | 一次完整缺料分析是否需要跨多个系统/数据源查询？耗时多少？ | `HYPOTHESIS` / **`PARTIALLY CONFIRMED`**（H1） | §19 P1 直接 Gate；不成立则 AI 价值需重估 | 操作流程、系统数量、单次耗时 | Process walkthrough（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-001`） | **YES** |
| **VB-02** | 取数后是否仍需 Excel / 人工二次计算与汇总？ | `HYPOTHESIS` / **`PARTIALLY CONFIRMED`**（H2、E09） | §19 P1 直接 Gate；AI 的收益锚点 | Excel 过程、手工计算、导出环节 | Process walkthrough（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-001`） | **YES** |
| **VB-03** | 是否有一个具有明确业务价值的缺料分析问题？ | **Human-approved**（`VR-003`） | §19 P2 | 问题陈述 + 业务价值判断 | Simulated stakeholder interview input provided by Human | Human | **VALIDATED / COMPLETED**（`VR-003`） | **YES** |
| **VB-04** | 主要业务 Owner 是否认可该问题值得进入 POC？ | **Human-approved**（`VR-003`） | §19 P3 | Owner 明确表态 | Simulated Sponsor / Business Owner input provided by Human | Human | **VALIDATED / COMPLETED**（`VR-003`） | **YES** |
| **VB-05** | 现有 ERP / MRP 是否已能高效完成缺料分析？ | **Human-approved**（`VR-002`） | H1 的证伪风险；§17 失败条件 | 现有 MRP 能力说明 | Process walkthrough + Interface / system assumption confirmation（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-002`） | **YES** |
| **VB-06** | 现有缺料预警机制是什么？与 AI 层的增量差异在哪？ | **Human-approved**（`VR-002`） | 决定 P0 增量价值；避免重复建设 | 预警规则、触发方式、覆盖范围 | Simulated stakeholder interview input provided by Human | Human | **VALIDATED / COMPLETED**（`VR-002`） | **YES** |
| **VB-07** | 客户是否认可 P0 闭环及其与 P1 的边界？ | **Human-approved**（`VR-003`，S1、S2、S3） | §19 S1–S3 | 对 Brief §11/§12 边界的确认 | Simulated Sponsor / Business Owner input provided by Human | Human | **VALIDATED / COMPLETED**（`VR-003`） | **YES** |
| **VB-14** | 「缺料」在业务上如何定义？ | `UNKNOWN`（K-BR-1） | P0-1 判定起点；G-07 | 缺料判定条件 | Simulated business decision provided by Human | Human | NOT STARTED | NO |
| **VB-21** | 谁有权查看采购价格 / 选择供应商 / 创建采购申请 / 修改数量 / 批准采购 / 正式下单？ | **Human-approved**（`VR-004`） | §19 I3 直接 Gate（业务操作权限边界）；P0-3 HITL 边界 | 权限矩阵 | Simulated stakeholder interview input provided by Human | Human | **VALIDATED / COMPLETED**（`VR-004`：已确认关键采购操作的角色权限边界） | **YES** |
| **VB-22** | Brief §6 的七类角色是否真实存在？各自数据范围与权限？ | **Human-approved**（`VR-004`） | §19 B4、I3 直接 Gate（角色、数据范围及权限确认） | 真实角色清单与职责 | Simulated stakeholder interview input provided by Human | Human | **VALIDATED / COMPLETED**（`VR-004`：已确认完整角色集合、Data Scope 原则、Permission Boundary） | **YES** |
| **VB-23** | 当前模拟场景中的缺料分析流程是什么？ | **Human-approved**（`VR-001`；对应 Brief E08「当前真实缺料分析流程」） | §19 B1；H1/H2 验证载体 | 当前模拟场景中的流程步骤描述 | Process walkthrough（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-001`） | **YES** |
| **VB-24** | 当前模拟场景中流程的主要步骤数量？ | **Human-approved**（`VR-001`） | §19 B2 | 步骤计数 | Process walkthrough（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-001`） | NO |
| **VB-25** | 当前模拟场景中单次缺料分析的平均耗时（实测或可靠估算）？ | **Human-approved**（`VR-001`，**`SIMULATED ESTIMATE`** 60–120 分钟） | §19 B3；§16 要求 KPI 基于真实基线 | 耗时测量或估算 | Process walkthrough（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-001`） | NO |
| **VB-26** | 缺料分析多久发生一次？ | **Human-approved**（`VR-001`：每个工作日至少一次，生产计划重大变更时追加） | §17 失败条件「使用频率过低」 | 发生频率 | Simulated stakeholder interview input provided by Human | Human | **VALIDATED / COMPLETED**（`VR-001`） | NO |
| **VB-27** | 风险判断是否依赖个人经验？ | `HYPOTHESIS` / `TBD`（H3） | P0-1「基础风险」规则设计；G-06、G-11 | 历史缺料案例与判断依据 | 历史案例复盘（Simulated case provided by Human） | Human | NOT STARTED | NO |
| **VB-28** | 缺料处理的信息解释成本是否较高？高频问题是什么？ | `HYPOTHESIS` / `TBD`（H4） | AI 在 P0 中角色的正当性 | 高频问题清单 | Simulated stakeholder interview input provided by Human | Human | NOT STARTED | NO |

### 7.2 Phase 1B — Data & System Readiness

> ## Phase 1B — Data & System Readiness：`IN PROGRESS`
>
> 阶段状态总览：
>
> | 阶段 | 状态 |
> | --- | --- |
> | Phase 1A — Problem Validation | `COMPLETE` |
> | **Phase 1B — Data & System Readiness** | **`IN PROGRESS`** |
> | `POC Design v0.2` | **`NOT READY`** |
>
> Phase 1B 共 **8 项 Blocking**。累计由 `VR-005`（SC-DATA-001）＋ `VR-006`（SC-DATA-002）完成 **6 / 8**：
>
> | 状态 | 数量 | ID |
> | --- | --- | --- |
> | ✅ 已完成 Blocking | **6** | VB-08、VB-09、VB-10、VB-11、VB-12、VB-13 |
> | ⛔ 仍未完成 Blocking | **2** | VB-19、VB-20 |
>
> > **Gate 进度**：
> >
> > - **Data Readiness Gate（`D1`–`D6`）：`COMPLETE`**
> > - **Integration Gate（`I1`–`I3`）：`NOT SATISFIED`**（待 `VB-19` / `VB-20`）
>
> **`Phase 1B` 不得标记为 `COMPLETE`。**

| ID | Question | Current Evidence Status | Why It Matters | Evidence Needed | Suggested Validation Method | Owner | Status | Blocks? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **VB-08** | 生产计划数据是否**可得**，且具备最低必要结构？ | **Human-approved**（`VR-005`） | §19 D1；P0-1 输入契约 | 数据可得性确认 + Conceptual Minimum Data Attributes | Data readiness check（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-005`） | **YES** |
| **VB-09** | BOM 数据是否**可得**，且具备最低必要结构（含层级 / Revision / Effectivity）？ | **Human-approved**（`VR-005`） | §19 D2；P0-1 输入契约 | 数据可得性确认 + Conceptual Minimum Data Attributes | Data readiness check（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-005`） | **YES** |
| **VB-10** | 库存数据与库存状态数据是否**可得**，且具备最低必要结构？ | **Human-approved**（`VR-005`） | §19 D3；P0-1 输入契约 | 数据可得性确认 + Conceptual Minimum Data Attributes | Data readiness check（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-005`） | **YES** |
| **VB-11** | 采购订单 / 在途数据是否**可得**，且可表达数量、日期与状态？ | **Human-approved**（`VR-005`） | §19 D4；P0-1 输入契约 | 数据可得性确认 + Conceptual Minimum Data Attributes | Data readiness check（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-005`） | **YES** |
| **VB-12** | 必要供应商信息（含 Lead Time、绩效）是否可得且结构化？ | **Human-approved**（`VR-006`；对应 Brief 原始 `E10` / `K-DR-6` 的 `UNKNOWN`） | §19 D5；P0-2「供应周期」「风险证据」 | Supplier Master、Supplier-Material Relationship、Standard Lead Time、基础 Performance | Data readiness check（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-006`） | **YES** |
| **VB-13** | 关键主数据能否建立基本关联（物料编码规则）？ | **Human-approved**（`VR-006`；对应 Brief 原始 `K-DR-3` 的 `UNKNOWN`） | §19 D6（H6）；P0 全链连通性 | canonical 标识基线与稳定、可追踪的基本映射关系 | Data readiness check（Simulated） | Human | **VALIDATED / COMPLETED**（`VR-006`） | **YES** |
| **VB-19** | 实际 ERP 品牌与版本？系统是否提供 API 或只读访问方式？ | `UNKNOWN`（E05、K-INT-1） | §19 **I1、I2、I3** —— 除 ERP / 接口能力外，还需确认**可用访问能力及基础安全边界** | ERP 信息、接口能力清单、只读通道可行性、**可用访问能力与基础安全边界** | Interface / system assumption confirmation（Simulated） | Human | NOT STARTED | **YES** |
| **VB-20** | POC 数据接入路径采用 API / 数据库 / 导出文件 / 模拟接口中的哪种？ | 尚无决定 | §19 **I1、I2、I3** —— 除选择接入方式外，还需确认该接入路径的 **read / write 与 access boundary** | 明确的接入方式决定 + **该路径的 read / write 与 access boundary** | Simulated business decision provided by Human | Human | NOT STARTED | **YES** |
| **VB-29** | POC 是否可以只读 + 草稿方式接入，无需写入业务系统？ | `HYPOTHESIS`（H7） | §19 I3；安全边界 | 接入边界确认 | Interface / system assumption confirmation（Simulated） | Human | NOT STARTED | NO |

> **Data Readiness Gate（`D1`–`D6`）与 Design Rule 的边界**：
>
> Phase 1B 当前的 Gate 只验证：
>
> > **"数据是否存在、是否可获得、是否具备最低必要结构（含可建立基本关联）"**
>
> 以下内容**属于 `POC Design v0.2`，不在本阶段验证范围**，因此**不得**因为其尚未定义而把 `D1`–`D6` 判为 `NOT SATISFIED`：
>
> - BOM version selection
> - Inventory usability calculation
> - Effective inbound rule
> - Safety stock
> - Substitute material
> - Scrap / loss
> - MOQ
> - detailed calculation logic
> - Supplier Ranking / Supplier Risk Score / Supplier Selection Rule
> - Dynamic / Predicted Lead Time
> - Data Cleaning Algorithm / MDM Architecture
>
> 同理，本阶段**不得**提前设计上述任何规则。
>
> > **`Data Readiness Gate`（`D1`–`D6`）：`COMPLETE`。**

> **Integration Gate（I1 / I2 / I3）的 Validation Scope 归属（Phase 1B）**：
> `I1`（POC 数据接入路径已确认）、`I2`（已明确 API / 数据库 / 导出文件 / 模拟接口中的何种方式接入）、`I3`（基础访问权限和数据安全边界已确认）**均由 Phase 1B 的 `VB-19` 与 `VB-20` 支撑**，并由 `VB-08`～`VB-13` 提供数据可得性前提。
>
> 需在 Phase 1B 确认的内容（**属 Validation Scope，不属于本阶段设计**）：
>
> - 实际 POC 数据访问路径
> - API / Database / Export / Mock interface 的选择
> - 技术身份 / Access mechanism
> - Read / Write boundary
> - 数据安全边界
> - 必要的环境与访问隔离
>
> > **边界声明**：本节只更新 Validation Scope / Mapping。**不得**在此设计 Auth implementation、RBAC implementation、Secret architecture、API Gateway 或 production deployment —— 这些属于后续 Design 阶段，不在 Discovery Validation 范围内。

### 7.3 其余 Business Rules 项（POC Design 内细化）

以下均 `UNKNOWN`，状态 `NOT STARTED`，Owner `Human`，**Blocking = NO**（Brief §20 已将其划归 POC Design v0.2，不阻碍**进入** v0.2，但是 v0.2 的必填内容）。

| ID | Question | 关联 Gap | 建议方法 |
| --- | --- | --- | --- |
| **VB-15** | 安全库存如何计算？ | G-04 | Simulated business decision provided by Human |
| **VB-16** | 替代料如何处理？ | G-05 | Simulated business decision provided by Human |
| **VB-17** | 损耗率规则？ | G-03 | Simulated business decision provided by Human |
| **VB-18** | 采购最小批量（MOQ）是否影响采购建议？ | G-10 | Simulated business decision provided by Human |

### 7.4 Backlog 汇总

#### A. 静态分类（`Blocks POC Design?`）

`Blocks POC Design?` 是每个 Validation Item 的**静态属性**，由 Brief §19 是否为该条所必需决定。**该分类不因条目已完成而改变** —— 已完成的 Blocking item 仍是 Blocking item。

| 分类 | 数量 | ID |
| --- | --- | --- |
| **BLOCKING** | **18** | **Phase 1A（10）**：VB-01、VB-02、VB-03、VB-04、VB-05、VB-06、VB-07、VB-21、VB-22、VB-23<br>**Phase 1B（8）**：VB-08、VB-09、VB-10、VB-11、VB-12、VB-13、VB-19、VB-20 |
| **NON-BLOCKING** | **11** | VB-14～VB-18（5）、VB-24～VB-29（6） |
| 合计 | 29 | — |

> **注意**：`VB-24` / `VB-25` / `VB-26` 属 **NON-BLOCKING**，它们**不计入** Blocking 数量。18 + 11 = **29**。

#### B. 执行状态

| Status | 数量 | ID |
| --- | --- | --- |
| `VALIDATED / COMPLETED` | **19** | VB-01、VB-02、VB-03、VB-04、VB-05、VB-06、VB-07、VB-08、VB-09、VB-10、VB-11、VB-12、VB-13、VB-21、VB-22、VB-23、VB-24、VB-25、VB-26 |
| `PARTIALLY VALIDATED` | **0** | — |
| `NOT STARTED` | **10** | VB-14～VB-20、VB-27、VB-28、VB-29 |

> **核对**：19 + 0 + 10 = **29**，与 Backlog 条目总数一致。
>
> 本次新增完成：`VB-12`、`VB-13`（依据 `VR-006`）。`PARTIALLY VALIDATED` 保持为 0。

#### C. 剩余未解决的 Blocking（Remaining unresolved Blocking）

`Blocking` 与「已完成」是两个维度。**仍未解决**的 Blocking items 数量为：

| 分组 | 数量 | ID |
| --- | --- | --- |
| **Remaining unresolved Blocking** | **2** | — |
| Phase 1A | **0** | — （Phase 1A Blocking 10 项已全部完成） |
| Phase 1B | **2** | VB-19、VB-20 |

> **`Remaining = 2` 的推导**：Blocking 共 **18** 项；其中已完成的 Blocking 为 **16** 项（Phase 1A 全部 10 项 ＋ Phase 1B 的 VB-08～VB-13）。18 − 16 = **2**，全部属 Phase 1B（Integration Gate）。

---

## 8. Minimum Validation Set Before POC Design

按 Brief §19 的五组 Required Gate，**最少必须先解决下列 BLOCKING items** 才能进入 `POC Design v0.2`。

### 8.1 Problem Validation（Phase 1A）—— `COMPLETE`

| 项 | 要求 | 状态 |
| --- | --- | --- |
| VB-01 | 确认 H1 —— 跨系统查询成本确实较高（附系统数量与耗时） | ✅ `VALIDATED / COMPLETED`（`VR-001`） |
| VB-02 | 确认 H2 —— 确实存在人工二次汇总 | ✅ `VALIDATED / COMPLETED`（`VR-001`） |
| — | 使 **H1 或 H2 至少一项** 达到 `PARTIALLY CONFIRMED` 或以上（§19 P1） | ✅ 达成（H1、H2 均为 `PARTIALLY CONFIRMED`） |
| VB-03、VB-04 | 识别具有明确业务价值的缺料分析问题，并获得 Owner 认可 | ✅ `VALIDATED / COMPLETED`（`VR-003`） |
| VB-05、VB-06 | 确认现有 MRP 与预警机制的能力边界（H1 证伪防线） | ✅ `VALIDATED / COMPLETED`（`VR-002`） |
| VB-07 | 获得对 P0 闭环与 P0/P1 边界（S1、S2、S3）的认可 | ✅ `VALIDATED / COMPLETED`（`VR-003`） |
| VB-23 | 完成当前模拟场景中的缺料分析流程记录（同时承载 B1–B4） | ✅ `VALIDATED / COMPLETED`（`VR-001`） |
| VB-21、VB-22 | 确认业务操作权限边界与完整角色集合 / Data Scope / Permission Boundary | ✅ `VALIDATED / COMPLETED`（`VR-004`） |

> **Phase 1A 全部 10 项 Blocking items 已完成。**

### 8.2 Data & System Readiness（Phase 1B）—— `IN PROGRESS`

> **Phase 1B 状态：`IN PROGRESS`**（6 / 8 Blocking 已完成）。剩余 2 项仍为 Blocking，且均为 `NOT STARTED`。

| 项 | 要求 | 状态 |
| --- | --- | --- |
| VB-08 | Production Plan 数据可得与最低必要结构（§19 D1） | ✅ `VALIDATED / COMPLETED`（`VR-005`） |
| VB-09 | BOM 数据可得与最低必要结构（§19 D2） | ✅ `VALIDATED / COMPLETED`（`VR-005`） |
| VB-10 | Inventory / Inventory Status 数据可得（§19 D3） | ✅ `VALIDATED / COMPLETED`（`VR-005`） |
| VB-11 | Purchase Order / Inbound 数据可得（§19 D4） | ✅ `VALIDATED / COMPLETED`（`VR-005`） |
| VB-12 | 必要供应商信息是否可得且结构化（§19 D5） | ✅ `VALIDATED / COMPLETED`（`VR-006`） |
| VB-13 | 关键主数据能否建立基本关联（§19 D6） | ✅ `VALIDATED / COMPLETED`（`VR-006`） |
| VB-19 | 确认 ERP 及业务系统接口能力，**以及可用访问能力与基础安全边界**（支撑 I1 / I2 / I3） | ⛔ `NOT STARTED` |
| VB-20 | 明确接入方式（API / 数据库 / 导出文件 / 模拟接口），**以及该路径的 read / write 与 access boundary**（支撑 I1 / I2 / I3） | ⛔ `NOT STARTED` |

> **Gate 状态**：**`Data Readiness Gate`（`D1`–`D6`）：`COMPLETE`** ｜ **`Integration Gate`（`I1`–`I3`）：`NOT SATISFIED`**

### 8.3 结论

> **Blocking 分类（静态）共 18 项**：Phase 1A 10 项 ＋ Phase 1B 8 项。**该分类不因条目完成而改变。**
>
> | 阶段 | 状态 |
> | --- | --- |
> | Phase 1A — Problem Validation | **`COMPLETE`**（10 / 10 Blocking 完成） |
> | Phase 1B — Data & System Readiness | **`IN PROGRESS`**（6 / 8 Blocking 完成） |
> | `POC Design v0.2` | **`NOT READY`** |
>
> | Gate | 状态 |
> | --- | --- |
> | `Data Readiness Gate`（`D1`–`D6`） | **`COMPLETE`** |
> | `Integration Gate`（`I1`–`I3`） | **`NOT SATISFIED`** |
>
> **剩余未解决的 Blocking = 2 项**，即进入 `POC Design v0.2` 前仍需解决的最小集合：
>
> - **Phase 1A（0 项）**：—
> - **Phase 1B（2 项）**：`VB-19`、`VB-20`（Integration Gate）
>
> 推导核对：Blocking 18 − 已完成 Blocking 16 = **剩余 2**。
>
> > ### ⚠️ `Phase 1A COMPLETE` ≠ `POC Design v0.2 Entry Gate COMPLETE`
> >
> > Phase 1A 完成只代表 **Problem Validation、Scope Validation 与 Baseline** 已充分。进入 `POC Design v0.2` 还必须完成 **Phase 1B — Data & System Readiness**（当前 `IN PROGRESS`，尚有 2 项 Blocking）。
> >
> > 当前 Entry Criteria 为 `SATISFIED = 16` / `NOT SATISFIED = 3`（`I1`、`I2`、`I3`）。
>
> **`VB-24` / `VB-25` / `VB-26` 虽为 `VALIDATED / COMPLETED`，但属 NON-BLOCKING，不计入「已完成 Blocking items」。** 它们作为 B2 / B3 / B4 的载体一并得出，属附带成果。
>
> **`D6` / `VB-13`（主数据关联）：`SATISFIED` / `VALIDATED / COMPLETED`（依据 `VR-006`）**。`VR-006` 确认存在 **canonical 标识基线**与**稳定、可追踪的基本映射关系**（允许 `Local ID → Canonical ID` mapping）。`D6` 所要求的是"关键主数据能够建立稳定、可追踪的基本映射关系"，**而不是**所有系统原始编码字符串完全一致。**仍不代表**企业主数据质量完美、不存在 Mapping Error、已设计 MDM 系统或已实现数据清洗流程。
>
> **`D5` / `VB-12`（供应商信息）：`SATISFIED` / `VALIDATED / COMPLETED`（依据 `VR-006`）**。**`D5 SATISFIED` 不等于 Supplier Risk / Ranking 规则已经设计** —— 供应商风险评分、排名与自动选择仍属后续 `POC Design`。
>
> **`I3`（基础访问权限和数据安全边界已确认）保持 `NOT SATISFIED`**：`VR-004` 确认的是**业务**角色、Data Scope 与业务 Permission Boundary，**不等于**技术访问与数据安全边界。`I3` 的确认由 Phase 1B 的 `VB-19` / `VB-20` 承担（见 §7.2 的 Integration Validation Scope 说明）。
>
> **NON-BLOCKING 的 11 项** 可在 Phase 1A/1B 期间或 POC Design 内并行细化，但它们是 v0.2 的必填内容。

---

## 9. Validation Records

本节登记**已获得的**验证输入。每条记录必须符合第 2 节的 Simulation Evidence Protocol。

> **当前状态：已登记 6 条记录（`VR-001` / `VR-002` / `VR-003` / `VR-004` / `VR-005` / `VR-006`），全部为 Human-approved `SIMULATED`。**
> 除已登记的记录外，Agent 不得自行生成或补齐任何记录。
>
> **证据性质声明**：以下全部记录均为 `Evidence Type: SIMULATED`、`Evidence Source: Human-approved`。它们**只代表本模拟项目中的业务设定**，不得解释为云南 CY 集团真实业务事实，不得声称来源于真实客户访谈或真实企业内部系统。

### 9.1 记录模板

```
Evidence Type: SIMULATED
Role:
Date:
Question / Decision:
Human-provided or Human-approved:
Result:
Related Backlog ID:
Impact on Entry Criteria:
```

### 9.2 已登记记录

| # | Evidence Type | Role | Human-provided / approved | Backlog ID | Entry Criteria Impact |
| --- | --- | --- | --- | --- | --- |
| `VR-001` | `SIMULATED` | Simulated Procurement / Supply Chain User | **Human-approved** | VB-01、VB-02、VB-23、VB-24、VB-25、VB-26 | P1、B1–B4 |
| `VR-002` | `SIMULATED` | Simulated Customer IT ＋ Simulated Business Owner | **Human-approved** | VB-05、VB-06 | S3 |
| `VR-003` | `SIMULATED` | Simulated Business Owner / Sponsor | **Human-approved** | VB-03、VB-04、VB-07 | P2、P3、S1、S2、S3 |
| `VR-004` | `SIMULATED` | Simulated Business Owner ＋ Simulated Customer IT | **Human-approved** | VB-21、VB-22 | （业务权限边界；不改变 Entry Criteria 计数） |
| `VR-005` | `SIMULATED` | Simulated Supply Chain User ＋ Simulated Customer IT | **Human-approved** | VB-08、VB-09、VB-10、VB-11 | D1、D2、D3、D4 |
| `VR-006` | `SIMULATED` | Simulated Procurement / Supply Chain User ＋ Simulated Customer IT | **Human-approved** | VB-12、VB-13 | D5、D6 |

#### `VR-001`

| 字段 | 内容 |
| --- | --- |
| **Scenario** | `SC-ASIS-001` —— 当前模拟场景中的缺料分析 As-Is 流程 |
| **Evidence Type** | `SIMULATED` |
| **Evidence Source** | **Human-approved** |
| **Role** | Simulated Procurement / Supply Chain User |
| **Related Backlog** | VB-01、VB-02、VB-23、VB-24、VB-25、VB-26 |

**核心批准内容（Human-approved，仅代表本模拟项目）：**

- 模拟企业为**离散装备制造**场景；
- 缺料分析涉及**生产计划、BOM、库存、采购 / 在途、仓库状态及供应商相关信息**；
- 现有流程存在**跨系统 / 数据源查询与核对**；
- 数据需要**导出或进入 Excel 进行人工关联、筛选与二次计算**；
- 单次缺料分析模拟基线约 **60–120 分钟**（**`SIMULATED ESTIMATE`**，非真实测量数据）；
- 单次涉及约 **100–500 个相关物料**；
- **每个工作日至少进行一次分析**，生产计划重大变更时追加；
- 主要参与角色包括**计划员、采购员、供应链负责人**；
- **最终采购决策仍由 Human 完成**。

> **数值性质警示**：上述 60–120 分钟、100–500 个物料、每日一次等数值均为 **`SIMULATED ESTIMATE`**，是 Human 批准的模拟基线，**不得描述为真实 CY 数据或实测结果**。
>
> **关于 `B3`（当前分析平均耗时已经测量或获得可靠估算）**：在本模拟项目的 Simulation Evidence Protocol 下，上述经 Human-approved 的 **`SIMULATED ESTIMATE`（60–120 分钟）**满足 Brief §19 的"已经测量**或获得可靠估算**"。因此 `B3 = SATISFIED`。该判定**继续明确**：证据性质为 `SIMULATED`、来源为 Human-approved、**非真实 CY 实测数据**。

#### `VR-002`

| 字段 | 内容 |
| --- | --- |
| **Scenario** | `SC-ASIS-002` —— 现有 ERP / MRP / 缺料预警能力边界 |
| **Evidence Type** | `SIMULATED` |
| **Evidence Source** | **Human-approved** |
| **Role** | Simulated Customer IT ＋ Simulated Business Owner |
| **Related Backlog** | VB-05、VB-06 |

**核心批准内容（Human-approved，仅代表本模拟项目）：**

现有 ERP / MRP 已具备**基础能力**，例如：

- BOM 展开
- 物料需求计算
- 账面库存查询
- 基础采购订单参与计算
- 基础缺料清单
- 基础异常 / 延期预警

**但现有系统不能独立完成完整缺料决策闭环。** 仍需要人工完成或补充：

- 跨数据源核对
- 有效在途判断
- 冻结 / 待检库存判断
- 风险优先级判断
- 缺料原因解释
- 供应商 / Lead Time 等上下文核对
- 采购行动建议

**项目定位**：MRP / ERP 继续负责基础业务与确定性数据能力；AI Copilot **不替代** ERP / MRP，而是在其上形成**受控的决策协同层**。

#### `VR-003`

| 字段 | 内容 |
| --- | --- |
| **Scenario** | `SC-BIZ-001` —— Business Owner 对业务价值、POC 和 P0/P1 边界的批准 |
| **Evidence Type** | `SIMULATED` |
| **Evidence Source** | **Human-approved** |
| **Role** | Simulated Business Owner / Sponsor |
| **Related Backlog** | VB-03、VB-04、VB-07 |

**核心批准内容（Human-approved，仅代表本模拟项目）：**

Business Owner 认可**存在值得验证的业务问题**：大量系统数据和基础预警仍需要人工转化为：

- 真正需要处理的**关键缺料**
- **风险优先级**
- **原因解释**
- **采购行动建议**

认可通过**受控 POC** 验证业务价值。

认可当前 **P0**：

```
缺料分析
→ 风险解释
→ 采购建议
→ 采购申请草稿
→ Human Review / Modify
→ Approve / Reject
→ 正式业务系统执行
```

明确 AI **可以**：分析、计算、解释、建议、生成 Draft。

明确 AI **不可以**：最终批准、正式下单、绕过审批、越权修改业务系统。

认可 **P0 聚焦核心缺料分析与采购建议闭环**；RAG、高级自然语言查询、复杂供应商智能、扩展报告等继续属于 **P1 / Future**。

#### `VR-004`

| 字段 | 内容 |
| --- | --- |
| **Scenario** | `SC-GOV-001` —— Role / Permission / Data Scope Boundary |
| **Evidence Type** | `SIMULATED` |
| **Evidence Source** | **Human-approved** |
| **Role** | Simulated Business Owner ＋ Simulated Customer IT |
| **Related Backlog** | VB-21、VB-22 |

> **声明**：本记录**只代表本模拟 FDE 项目**，**不得解释为云南 CY 集团真实权限体系**，不得声称来源于真实企业内部系统。

**核心批准内容（Human-approved，仅代表本模拟项目）：**

**完整业务角色集合沿用 Discovery Brief §6：**

1. 生产计划员
2. 采购员
3. 仓库人员
4. 供应商管理人员
5. 供应链负责人
6. 审批管理人员
7. IT / 数字化团队

**权限模型原则：**

```
Effective Permission =
  Role
+ Organization / Plant Scope
+ Material / Supplier Scope
+ Workflow State
```

**业务权限边界：**

| 角色 | 可做 | 不可做 |
| --- | --- | --- |
| **生产计划员** | 查看授权范围生产计划、BOM 需求、缺料结果；发起分析 | 不查看采购价格；不批准采购；不正式下单 |
| **采购员** | 查看授权范围采购、在途、价格、Lead Time；提出候选供应商；创建采购申请草稿；在审批前修改采购数量 | 不拥有最终批准权 |
| **仓库人员** | 查看和确认库存、冻结、待检、可用状态 | 无采购价格、供应商选择、审批或正式下单权限 |
| **供应商管理人员** | 查看 / 维护授权供应商的交付、质量、绩效与风险信息 | 默认无正式采购审批或下单权限 |
| **供应链负责人** | 在授权组织范围跨域查看、Review、风险排序 | 不因负责人身份自动获得正式下单或系统管理员权限 |
| **审批管理人员** | 在自身审批范围 Approve / Reject | 不允许绕过审批流程 |
| **IT / 数字化团队** | 管理接口、身份、日志、技术配置 | 技术管理员权限不自动等于业务采购决策权限；业务数据访问遵循最小权限 |

**具体操作权限原则：**

- **查看采购价格**：采购员、授权供应链负责人、相关审批人员
- **提出 / 选择候选供应商**：采购员；供应商管理人员可提供建议
- **创建采购申请草稿**：采购员
- **审批前修改采购数量**：采购员
- **Approve / Reject**：具有正式审批授权的审批角色
- **正式采购订单**：只能在正式审批完成后由现有采购业务流程执行

**关键控制：**

若审批后发生对以下字段的重大变更：

- Supplier
- Quantity
- Price
- Delivery Date

需要根据审批规则**重新进入 Review / Approval**，**不得利用已有批准绕过 HITL**。

**AI Copilot 权限：**

```
AI Effective Permission =
  User Permission
∩ Data Scope
∩ Tool Permission
∩ Workflow State
∩ POC Policy
```

AI **可以**：

- 读取授权范围数据
- 分析
- 确定性计算
- 风险解释
- 建议
- 推荐候选供应商
- 生成采购申请 Draft

AI **不可以**：

- Approve
- Formal Submit
- Create Purchase Order
- Override Approval
- Expand Data Scope
- 越权修改业务系统

即使当前 Human User 自身拥有更高权限，**POC 中 Agent Capability 仍可以低于 Human Capability**。

#### `VR-005`

| 字段 | 内容 |
| --- | --- |
| **Scenario** | `SC-DATA-001` —— Core Supply Chain Data Readiness |
| **Evidence Type** | `SIMULATED` |
| **Evidence Source** | **Human-approved** |
| **Role** | Simulated Supply Chain User ＋ Simulated Customer IT |
| **Related Backlog** | VB-08、VB-09、VB-10、VB-11 |
| **Entry Criteria Impact** | D1、D2、D3、D4 |

> **声明**：本记录**只代表模拟 FDE 项目的数据基线**，**不得**解释为：
>
> - 云南 CY 集团真实数据结构
> - 真实 ERP / WMS Schema
> - 真实企业内部系统信息
> - 真实接口能力

> **字段性质**：以下字段均为 **Conceptual Minimum Data Attributes**，**不是**最终数据库 Schema。本记录**不创建**任何 CSV / JSON / SQL Schema / Mock database / Dataset fixture / API contract / Data dictionary —— 真正的数据字典与 Mock Dataset 进入后续 `POC Design` / Data Fixture Task。

**A. Production Plan**

模拟企业存在**结构化滚动生产计划**。

业务特征：

- 存在周 / 月滚动计划
- 日常可能发生计划调整或插单
- POC 关注**已发布或有效**的生产需求
- 计划变化具有时间或版本信息

最低概念数据属性：

- `plan_id`
- `plant_id`
- `product_code`
- `planned_quantity`
- `required_date`
- `plan_status`
- `plan_version`
- `updated_at`

> **确认**：Production Plan data is available for the simulated POC scenario.
>
> **Related**：`VB-08`、`D1`

**B. BOM**

模拟企业存在**结构化多层 BOM**，支持：

```
Finished Product
→ Assembly
→ Component / Purchased Material
```

最低概念数据属性：

- `parent_material`
- `component_material`
- `qty_per`
- `uom`
- `bom_revision`
- `effective_from`
- `effective_to`
- `status`

确认：

- BOM 数据可获取
- 支持 multi-level BOM
- 存在 Revision / Effectivity 信息

> **但不得定义**（这些属于 `POC Design v0.2`）：
>
> - 最终 BOM Version Selection Rule
> - Engineering Change handling
> - Substitute material logic
> - Scrap / loss calculation
>
> **确认**：BOM data is available for the simulated POC scenario.
>
> **Related**：`VB-09`、`D2`

**C. Inventory**

模拟企业存在**结构化库存数据**。库存至少按照以下维度表达：

```
Plant
+ Warehouse
+ Material
+ Inventory Status
```

最低概念数据属性：

- `material_code`
- `plant_id`
- `warehouse_id`
- `on_hand_qty`
- `inventory_status`
- `snapshot_time`

模拟数据允许存在例如：`AVAILABLE`、`INSPECTION`、`FROZEN`。

其目的只是确认：**账面库存 ≠ 必然全部可用库存**。

> **不得在本 Task 定义**（这些属于后续 Design）：
>
> - `INSPECTION` 是否计入可用量
> - `FROZEN` 是否允许释放
> - 跨仓调拨算法
> - Safety Stock deduction rule
>
> **确认**：Inventory data and inventory status data are available for the simulated POC scenario.
>
> **Related**：`VB-10`、`D3`

**D. Purchase Order / Inbound**

模拟企业存在**结构化采购订单与在途信息**。

最低概念数据属性：

- `po_number`
- `po_line`
- `supplier_id`
- `material_code`
- `ordered_qty`
- `received_qty`
- `open_qty`
- `promised_date`
- `expected_arrival_date`
- `po_status`
- `updated_at`

确认数据能够表达：Ordered Quantity、Received Quantity、Open Quantity、Promised Date、Expected Arrival Date、PO Status。

> **确认**：Purchase Order / Inbound data is available for the simulated POC scenario.
>
> **但是**：**不得在本 Task 定义「有效在途」的最终业务算法。**
>
> 例如：
>
> ```
> 需求日期 = 10 月 15 日
> 预计到货 = 10 月 16 日
> ```
>
> 是否算有效在途，属于 `POC Design v0.2` 的**确定性业务规则**。
>
> **Related**：`VB-11`、`D4`

#### `VR-006`

| 字段 | 内容 |
| --- | --- |
| **Scenario** | `SC-DATA-002` —— Supplier & Master Data Readiness |
| **Evidence Type** | `SIMULATED` |
| **Evidence Source** | **Human-approved** |
| **Role** | Simulated Procurement / Supply Chain User ＋ Simulated Customer IT |
| **Related Backlog** | VB-12、VB-13 |
| **Entry Criteria Impact** | D5、D6 |

> **声明**：本记录**只代表模拟 FDE 项目的数据基线**，**不得**解释为：
>
> - 云南 CY 集团真实供应商数据
> - 真实企业 Supplier Master
> - 真实 ERP / SRM 数据结构
> - 真实主数据治理现状

> **字段性质**：以下字段均为 **Conceptual Minimum Data Attributes**，**不是**最终数据库 Schema。本记录**不创建**任何 CSV / JSON / SQL / Mock Dataset / Database / API Schema / Data Dictionary。

**A. Supplier Data Baseline**

确认模拟企业存在**结构化 Supplier Data**。

**A-1. Supplier Master**

Conceptual Minimum Data Attributes：

- `supplier_id`
- `supplier_name`
- `supplier_status`

**A-2. Supplier-Material Relationship**

Conceptual Minimum Data Attributes：

- `supplier_id`
- `material_code`
- `sourcing_status`
- `standard_lead_time_days`
- `updated_at`

允许**一个 Material 对应多个已批准 Supplier**。

**A-3. Lead Time**

确认：供应商 ＋ 物料维度存在**结构化 Standard Lead Time** 信息。其作用是提供**基础供应周期事实**。

> **不得在本 Task 定义**：
>
> - historical average lead time algorithm
> - emergency lead time
> - dynamic lead time prediction
> - transportation lead time calculation
> - outlier handling
>
> 只确认：**Lead Time data = `AVAILABLE`**

**A-4. Supplier Performance**

确认存在**结构化的基础交付 / 质量历史信息**。

Conceptual Minimum Data Attributes 可以记录为：

- `supplier_id`
- `period`
- `delivery_performance`
- `quality_performance`
- `updated_at`

也可以说明底层数据能够支撑：

- planned arrival date
- actual arrival date
- delivery completion
- quality issue records
- return / rejection records

> 但**不得**自行扩展为完整数据库字段清单。
>
> 只确认：**Raw / Basic Supplier Performance Data = `AVAILABLE`**
>
> **不得在本阶段定义**（这些属于后续 `POC Design`）：
>
> - Supplier Risk Score
> - High / Medium / Low Risk
> - Supplier Ranking
> - Automatic Supplier Selection

**B. Master Data Linkage Baseline**

确认模拟项目存在稳定的 **Canonical Identifier 基线**。核心业务标识包括：

- `material_code`
- `product_code`
- `supplier_id`
- `plant_id`
- `warehouse_id`

确认以下**基本关联可以建立**：

```
Production Plan  product_code
  → BOM parent material

BOM component   material_code
  → Material Master

Material Master material_code
  → Inventory

Material Master material_code
  → Purchase Order

Purchase Order  supplier_id
  → Supplier Master

Supplier Master + material_code
  → Supplier-Material Relationship

Supplier
  → Supplier Performance
```

> **重要**：**不得声称所有系统中的编码天然完全一致。**
>
> 模拟企业允许存在 `Local ID → Canonical ID` 的 **Master Data Mapping**。
>
> `D6` 所要求的是：**关键主数据能够建立稳定、可追踪的基本映射关系** —— **而不是**所有系统原始编码字符串必须完全一致。

**C. Data Quality Boundary**

允许存在以下异常：

- Missing Mapping
- Duplicate Mapping
- Inactive Material
- Inactive Supplier

但：**Agent / AI 不得自行猜测映射。**

例如：`Local Material ID` 无法映射 `Canonical material_code`，则**必须**视为 **Data Quality / Mapping Issue**。

实际错误码、异常流程、UI 行为留待 `POC Design`。

本 Task 只确认：**Unknown / Missing Mapping 不得被模型静默补齐。**

### 9.3 待输入清单

> **Phase 1A 的 Blocking items 已全部完成**（`VR-001`～`VR-004`）。以下为非 Blocking 的剩余项，以及 Phase 1B 的待输入项。

| Backlog ID | 需要的模拟输入 | 建议角色 |
| --- | --- | --- |
| VB-14 | 「缺料」业务定义 | Simulated Procurement / Supply Chain User |
| VB-27 | 历史缺料案例与判断依据 | Simulated Procurement / Supply Chain User |
| VB-28 | 高频问题清单 | Simulated Business Owner |

> **Phase 1B（Data & System Readiness）状态为 `IN PROGRESS`**（**6 / 8** Blocking 完成）。`VB-08`～`VB-13` 已由 `VR-005` / `VR-006` 完成；剩余待输入项：**`VB-19`、`VB-20`**（Integration Gate），以及非 Blocking 的 `VB-29`、`VB-15`～`VB-18`。
>
> **`Data Readiness Gate`（`D1`–`D6`）：`COMPLETE`** ｜ **`Integration Gate`（`I1`–`I3`）：`NOT SATISFIED`**
>
> `VB-19` / `VB-20` 需一并覆盖 Integration Gate 的 `I1` / `I2` / `I3`（见 §7.2 的 Validation Scope 说明）。

---

## Document Control

**Document:** Discovery Validation
**Version:** v0.1
**Status:** `DRAFT`

- 本文档为 Discovery Validation Phase 的 Canonical Source，但**不替代** `FROZEN` 的 Discovery Brief。
- 本文档当前为 `DRAFT`，尚未进入 `REVIEW` / `APPROVED` / `FROZEN`。
- 实质修改需通过明确授权的 Governance / Discovery Validation Task。
- 本文档**不包含**：缺料计算口径、BOM 版本规则、损耗率、替代料、MOQ、库存状态、有效在途、风险评分卡、规则版本、数据字典、主数据编码方案、POC 测试集、RBAC 矩阵、HITL 状态机、审批矩阵、审计事件 Schema。以上均属 `POC Design v0.2`。
- 本文档**不包含**任何技术栈选择、Architecture 决策或 ADR。
