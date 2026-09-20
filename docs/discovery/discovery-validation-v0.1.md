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

- 不改变任何 Evidence Status（不将 `HYPOTHESIS` / `UNKNOWN` / `TBD` 转为已确认）
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

| ID | 隐含假设 | 依据 | 是否阻塞 |
| --- | --- | --- | --- |
| **H5** | 存在可获取的生产计划 / BOM / 库存 / 在途 / 供应商数据 | Brief §19 Data Readiness | YES（Phase 1B） |
| **H6** | 关键主数据可以建立基本关联 | Brief §19 Data Readiness 末项 | YES（Phase 1B） |
| **H7** | POC 可以只读 + 草稿方式接入，无需写入生产业务系统 | Brief §10、§11 P0-3 | NO（但实现前必须确认） |

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

| ID | Unknown | Brief 状态 | 影响面 | 需确认方 | 阶段 |
| --- | --- | --- | --- | --- | --- |
| **E05** | 当前实际 ERP 品牌及版本 | `UNKNOWN` | Data Readiness、Integration、H1 判定 | Simulated Customer IT | Phase 1B |
| **E06** | 是否存在独立 WMS | `UNKNOWN` | Data Readiness（库存数据来源） | Simulated Customer IT | Phase 1B |
| **E07** | BOM 由哪个系统管理 | `UNKNOWN` | Data Readiness、P0-1 计算输入 | Simulated Customer IT | Phase 1B |
| **E08** | 当前真实缺料分析流程 | `UNKNOWN` | Problem Validation（H1/H2）、Baseline、HITL | Simulated Procurement / Supply Chain User | **Phase 1A** |
| **E10** | 供应商绩效数据是否已结构化记录 | `UNKNOWN` | P0-2「风险证据」深度、H3 | Simulated Procurement / Supply Chain User | Phase 1B |
| **E09** | 当前缺料分析存在 Excel 或人工二次处理 | `HYPOTHESIS` | H2 的核心内容 | Simulated Procurement / Supply Chain User | **Phase 1A** |

### 4.2 来自 Brief §18 Known Unknowns（按影响面聚类）

**（a）Data Readiness**

| ID | Unknown | 影响 | 阶段 |
| --- | --- | --- | --- |
| **K-DR-1** | 真实生产计划结构 | P0-1 输入契约 | Phase 1B |
| **K-DR-2** | BOM 版本机制 | P0-1 计算口径 | Phase 1B |
| **K-DR-3** | 物料编码规则 | 主数据关联（H6） | Phase 1B |
| **K-DR-4** | 库存状态 / 质检冻结库存 | P0-1「预计可用量」口径 | Phase 1B |
| **K-DR-5** | 有效在途定义 | P0-1「预计缺口」、P0-2「有效在途」 | Phase 1B |
| **K-DR-6** | 供应商 Lead Time | P0-2「供应周期」 | Phase 1B |

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
| **D1** | 生产计划数据可获取 | `NOT SATISFIED` | K-DR-1 未确认；E05–E07 为 `UNKNOWN` |
| **D2** | BOM 数据可获取 | `NOT SATISFIED` | E07 `UNKNOWN`；K-DR-2 未确认 |
| **D3** | 库存数据可获取 | `NOT SATISFIED` | E06 `UNKNOWN`；K-DR-4 未确认 |
| **D4** | 采购订单 / 在途数据可获取 | `NOT SATISFIED` | K-DR-5 未确认 |
| **D5** | 必要供应商信息可获取 | `NOT SATISFIED` | E10 `UNKNOWN`；K-DR-6 未确认 |
| **D6** | 关键主数据可以建立基本关联 | `NOT SATISFIED` | K-DR-3 未确认 |
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
| `SATISFIED` | **10** | P1–P3、S1–S3、B1–B4 |
| `PARTIALLY SATISFIED` | **0** | — |
| `NOT SATISFIED` | **9** | D1–D6、I1–I3 |
| `UNKNOWN` | **0** | — |

> **总数核对**：`0 + 3 + 16 + 0 = 19`（前一版本）→ 本次为 **`10 + 0 + 9 + 0 = 19`**。Entry Criteria 总数仍为 **19**，未增删任何条目。

> **状态升级的依据**：`SATISFIED` 的 10 条全部基于 Human-approved `SIMULATED` 证据（`VR-001` / `VR-002` / `VR-003` / `VR-004`），**仅代表本模拟项目的业务设定**，不得解释为云南 CY 集团真实业务事实。
>
> **`S1–S3` 的升级说明**：前一版本保持 `PARTIALLY SATISFIED` 的原因是"Brief 已有定义不等于 Stakeholder 已认可"。`VR-003`（SC-BIZ-001）已提供 Human-approved 的 Stakeholder 认可，**升级条件已满足**，故升为 `SATISFIED`。
>
> **`D1–D6` 与 `I1–I3` 保持 `NOT SATISFIED`**：`VR-004`（SC-GOV-001）确认的是**业务角色、业务 Data Scope 与业务 Permission Boundary** —— 这**不足以**满足 Integration 组的 `I1` / `I2` / `I3`。这三项需要 Phase 1B 确认实际 POC 数据访问路径、接入方式、技术身份 / Access mechanism、Read / Write boundary、数据安全边界与必要的环境与访问隔离。**不得在本阶段的证据中推断其已满足。**

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
> > Phase 1A 只覆盖 **Problem Validation** 与部分 **Baseline / Scope Validation**。进入 `POC Design v0.2` 仍需满足 **Phase 1B — Data & System Readiness**（Data Readiness 与 Integration 两组），该阶段**尚未开始**。
> >
> > 当前状态：`SATISFIED = 10` / `NOT SATISFIED = 9`（D1–D6、I1–I3）。

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

### 7.2 Phase 1B — Data & System Readiness（后续）

> **Phase 1B 尚未开始。** 本节全部条目状态为 `NOT STARTED`。

| ID | Question | Current Evidence Status | Why It Matters | Evidence Needed | Suggested Validation Method | Owner | Status | Blocks? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **VB-08** | 生产计划数据的结构与存放位置？ | `UNKNOWN`（K-DR-1） | §19 D1；P0-1 输入契约 | 字段清单、样例结构、拥有系统 | Data readiness check + Mock dataset definition（Simulated） | Human | NOT STARTED | **YES** |
| **VB-09** | BOM 由哪个系统管理？版本机制如何？ | `UNKNOWN`（E07、K-DR-2） | §19 D2；P0-1 计算口径 | 系统归属、版本规则 | Data readiness check + Interface / system assumption confirmation（Simulated） | Human | NOT STARTED | **YES** |
| **VB-10** | 库存数据来源与状态划分（含质检冻结）？是否存在独立 WMS？ | `UNKNOWN`（E06、K-DR-4） | §19 D3；P0-1「预计可用量」 | 来源系统、库存状态枚举、冻结规则 | Data readiness check + Simulated stakeholder input provided by Human | Human | NOT STARTED | **YES** |
| **VB-11** | 采购订单 / 在途数据的可得性？「有效在途」如何界定？ | `UNKNOWN`（K-DR-5） | §19 D4；P0-1「预计缺口」 | 订单数据结构、在途有效性判据 | Data readiness check + Simulated business decision provided by Human | Human | NOT STARTED | **YES** |
| **VB-12** | 必要供应商信息（含 Lead Time、绩效）是否可得且结构化？ | `UNKNOWN`（E10、K-DR-6） | §19 D5；P0-2「供应周期」「风险证据」 | 供应商主数据、Lead Time 来源、绩效记录 | Data readiness check（Simulated） | Human | NOT STARTED | **YES** |
| **VB-13** | 关键主数据能否建立基本关联（物料编码规则）？ | `UNKNOWN`（K-DR-3） | §19 D6（H6）；P0 全链连通性 | 物料编码规则及其与 BOM/库存/订单的对应 | Data readiness check + Mock dataset definition（Simulated） | Human | NOT STARTED | **YES** |
| **VB-19** | 实际 ERP 品牌与版本？系统是否提供 API 或只读访问方式？ | `UNKNOWN`（E05、K-INT-1） | §19 **I1、I2、I3** —— 除 ERP / 接口能力外，还需确认**可用访问能力及基础安全边界** | ERP 信息、接口能力清单、只读通道可行性、**可用访问能力与基础安全边界** | Interface / system assumption confirmation（Simulated） | Human | NOT STARTED | **YES** |
| **VB-20** | POC 数据接入路径采用 API / 数据库 / 导出文件 / 模拟接口中的哪种？ | 尚无决定 | §19 **I1、I2、I3** —— 除选择接入方式外，还需确认该接入路径的 **read / write 与 access boundary** | 明确的接入方式决定 + **该路径的 read / write 与 access boundary** | Simulated business decision provided by Human | Human | NOT STARTED | **YES** |
| **VB-29** | POC 是否可以只读 + 草稿方式接入，无需写入业务系统？ | `HYPOTHESIS`（H7） | §19 I3；安全边界 | 接入边界确认 | Interface / system assumption confirmation（Simulated） | Human | NOT STARTED | NO |

> **Integration Gate（I1 / I2 / I3）的 Validation Scope 归属（Phase 1B）**：
>
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
| `VALIDATED / COMPLETED` | **13** | VB-01、VB-02、VB-03、VB-04、VB-05、VB-06、VB-07、VB-21、VB-22、VB-23、VB-24、VB-25、VB-26 |
| `PARTIALLY VALIDATED` | **0** | — |
| `NOT STARTED` | **16** | VB-08～VB-20、VB-27、VB-28、VB-29、VB-14～VB-18 |

> **核对**：13 + 0 + 16 = **29**，与 Backlog 条目总数一致。
>
> 本次新增完成：`VB-21`、`VB-22`（依据 `VR-004`）。`PARTIALLY VALIDATED` 归零。

#### C. 剩余未解决的 Blocking（Remaining unresolved Blocking）

`Blocking` 与「已完成」是两个维度。**仍未解决**的 Blocking items 数量为：

| 分组 | 数量 | ID |
| --- | --- | --- |
| **Remaining unresolved Blocking** | **8** | — |
| Phase 1A | **0** | — （Phase 1A Blocking 10 项已全部完成） |
| Phase 1B | **8** | VB-08、VB-09、VB-10、VB-11、VB-12、VB-13、VB-19、VB-20 |

> **`Remaining = 8` 的推导**：Blocking 共 **18** 项；其中已完成的 Blocking 为 **10** 项（Phase 1A 全部：VB-01～VB-07、VB-21、VB-22、VB-23）。18 − 10 = **8**，全部属 Phase 1B。

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

### 8.2 Data & System Readiness（Phase 1B）—— `NOT STARTED`

> **Phase 1B 尚未开始**，本节 8 项条目**全部仍为 Blocking，且全部 `NOT STARTED`**。

| 项 | 要求 |
| --- | --- |
| VB-08～VB-13 | 生产计划、BOM、库存、采购/在途、供应商信息、主数据关联（§19 D1–D6） |
| VB-19 | 确认 ERP 及业务系统接口能力，**以及可用访问能力与基础安全边界**（支撑 I1 / I2 / I3） |
| VB-20 | 明确接入方式（API / 数据库 / 导出文件 / 模拟接口），**以及该路径的 read / write 与 access boundary**（支撑 I1 / I2 / I3） |

### 8.3 结论

> **Blocking 分类（静态）共 18 项**：Phase 1A 10 项 ＋ Phase 1B 8 项。**该分类不因条目完成而改变。**
>
> **Phase 1A — Problem Validation：`COMPLETE`**（10 项 Blocking 全部 `VALIDATED / COMPLETED`）。
>
> **剩余未解决的 Blocking = 8 项**，即进入 `POC Design v0.2` 前仍需解决的最小集合：
>
> - **Phase 1A（0 项）**：—
> - **Phase 1B（8 项）**：`VB-08`、`VB-09`、`VB-10`、`VB-11`、`VB-12`、`VB-13`、`VB-19`、`VB-20`
>
> 推导核对：Blocking 18 − 已完成 Blocking 10 = **剩余 8**。
>
> > ### ⚠️ `Phase 1A COMPLETE` ≠ `POC Design v0.2 Entry Gate COMPLETE`
> >
> > Phase 1A 完成只代表 **Problem Validation、Scope Validation 与 Baseline** 已充分。进入 `POC Design v0.2` 还必须完成 **Phase 1B — Data & System Readiness**（Data Readiness 与 Integration 两组，共 8 项 Blocking）。
> >
> > 当前 Entry Criteria 仍为 `SATISFIED = 10` / `NOT SATISFIED = 9`（`D1–D6`、`I1–I3`）。
>
> **`VB-24` / `VB-25` / `VB-26` 虽为 `VALIDATED / COMPLETED`，但属 NON-BLOCKING，不计入「已完成 Blocking items」。** 它们作为 B2 / B3 / B4 的载体一并得出，属附带成果。
>
> **`I3`（基础访问权限和数据安全边界已确认）保持 `NOT SATISFIED`**：`VR-004` 确认的是**业务**角色、Data Scope 与业务 Permission Boundary，**不等于**技术访问与数据安全边界。`I3` 的确认由 Phase 1B 的 `VB-19` / `VB-20` 承担（见 §7.2 的 Integration Validation Scope 说明）。
>
> **NON-BLOCKING 的 11 项** 可在 Phase 1A/1B 期间或 POC Design 内并行细化，但它们是 v0.2 的必填内容。

---

## 9. Validation Records

本节登记**已获得的**验证输入。每条记录必须符合第 2 节的 Simulation Evidence Protocol。

> **当前状态：已登记 4 条记录（`VR-001` / `VR-002` / `VR-003` / `VR-004`），全部为 Human-approved `SIMULATED`。**
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

### 9.3 待输入清单（Phase 1A 已完成）

> **Phase 1A 的 Blocking items 已全部完成**（`VR-001`～`VR-004`）。以下为非 Blocking 的剩余项，以及 Phase 1B 的待输入项。

| Backlog ID | 需要的模拟输入 | 建议角色 |
| --- | --- | --- |
| VB-14 | 「缺料」业务定义 | Simulated Procurement / Supply Chain User |
| VB-27 | 历史缺料案例与判断依据 | Simulated Procurement / Supply Chain User |
| VB-28 | 高频问题清单 | Simulated Business Owner |

> **Phase 1B（Data & System Readiness）尚未开始**，其待输入清单待该阶段启动时另行登记：`VB-08`～`VB-13`、`VB-19`、`VB-20`、`VB-29`、`VB-15`～`VB-18`。
>
> 其中 `VB-19` / `VB-20` 需一并覆盖 Integration Gate 的 `I1` / `I2` / `I3`（见 §7.2 的 Validation Scope 说明）。

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
