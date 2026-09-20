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

Brief §7 提出 4 个假设，Brief §8 验证矩阵中**当前结论全部为 `TBD`**。

### 3.1 H1–H4 现状

| ID | 假设 | Brief 状态 | 是否阻塞进入 POC Design | 阶段 |
| --- | --- | --- | --- | --- |
| **H1** | 跨系统查询成本较高 | `HYPOTHESIS` / `TBD` | **YES**（§19 Problem Validation） | **Phase 1A** |
| **H2** | 缺料判断存在人工汇总 | `HYPOTHESIS` / `TBD`（对应 E09） | **YES**（§19 Problem Validation） | **Phase 1A** |
| **H3** | 部分风险判断依赖业务经验 | `HYPOTHESIS` / `TBD` | **NO** | Phase 1A（次级） |
| **H4** | 缺料处理存在较高的信息解释成本 | `HYPOTHESIS` / `TBD` | **NO** | Phase 1A（次级） |

**决策 5 的落实**：H3 / H4 允许暂时保持未确认，但**必须**进入 Validation Backlog，明确 `Validation Method` / `Owner` / `Status` / `Blocking`（见 VB-27、VB-28），**不得长期作为无人处理的 `TBD`**。

### 3.2 其他影响 P0 成立的关键假设

以下未被 Brief 显式编号，但直接决定 P0 可行性，一并纳入验证范围。

| ID | 隐含假设 | 依据 | 是否阻塞 |
| --- | --- | --- | --- |
| **H5** | 存在可获取的生产计划 / BOM / 库存 / 在途 / 供应商数据 | Brief §19 Data Readiness | YES（Phase 1B） |
| **H6** | 关键主数据可以建立基本关联 | Brief §19 Data Readiness 末项 | YES（Phase 1B） |
| **H7** | POC 可以只读 + 草稿方式接入，无需写入生产业务系统 | Brief §10、§11 P0-3 | NO（但实现前必须确认） |

> Brief §8 要求假设「不得长期停留在模糊状态」。当前 4/4 均为 `TBD`，该要求**尚未满足** —— 本文档的状态为 `DRAFT`，有待 Human 提供模拟输入后方可推进。

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
| **P1** | H1 / H2 中至少一项为 `CONFIRMED` 或 `PARTIALLY CONFIRMED` | `NOT SATISFIED` | 两者均为 `TBD`；尚无验证记录 |
| **P2** | 已识别至少一个具有明确业务价值的缺料分析问题 | `NOT SATISFIED` | Brief 定义了拟验证的问题，但业务价值与认可尚无记录 |
| **P3** | 主要业务 Owner 认可该问题值得进入 POC | `NOT SATISFIED` | 尚无 Simulated Business Owner / Sponsor 输入 |
| **S1** | 客户认可 P0 闭环：缺料分析 → 采购建议 → HITL | `PARTIALLY SATISFIED` | Brief §11 已单方定义，Stakeholder 认可记录缺失 |
| **S2** | P0 与 P1 边界已确认 | `PARTIALLY SATISFIED` | Brief §11/§12 已定义边界，Stakeholder 确认记录缺失 |
| **S3** | POC 不承担完整 ERP/MRP 替代职责 | `PARTIALLY SATISFIED` | Brief §10/§13/§19 已界定，Stakeholder 确认记录缺失 |
| **D1** | 生产计划数据可获取 | `NOT SATISFIED` | K-DR-1 未确认；E05–E07 为 `UNKNOWN` |
| **D2** | BOM 数据可获取 | `NOT SATISFIED` | E07 `UNKNOWN`；K-DR-2 未确认 |
| **D3** | 库存数据可获取 | `NOT SATISFIED` | E06 `UNKNOWN`；K-DR-4 未确认 |
| **D4** | 采购订单 / 在途数据可获取 | `NOT SATISFIED` | K-DR-5 未确认 |
| **D5** | 必要供应商信息可获取 | `NOT SATISFIED` | E10 `UNKNOWN`；K-DR-6 未确认 |
| **D6** | 关键主数据可以建立基本关联 | `NOT SATISFIED` | K-DR-3 未确认 |
| **B1** | 当前人工流程已经记录 | `NOT SATISFIED` | Brief §5 为通用流程假设，明确声明"不代表 CY 真实业务流程"；E08 `UNKNOWN` |
| **B2** | 当前流程主要步骤数量已经确认 | `NOT SATISFIED` | 无记录 |
| **B3** | 当前分析平均耗时已经测量或获得可靠估算 | `NOT SATISFIED` | 无测量或估算 |
| **B4** | 当前涉及角色已经确认 | `NOT SATISFIED` | Brief §6 为角色假设清单 |
| **I1** | POC 数据接入路径已确认 | `NOT SATISFIED` | K-INT-1 未确认 |
| **I2** | 已明确通过 API / 数据库 / 导出文件 / 模拟接口中的何种方式接入 | `NOT SATISFIED` | 尚无决定 |
| **I3** | 基础访问权限和数据安全边界已确认 | `NOT SATISFIED` | K-HITL-1/2 未确认 |

### 6.2 汇总

| 状态 | 数量 | 条目 |
| --- | --- | --- |
| `SATISFIED` | **0** | — |
| `PARTIALLY SATISFIED` | **3** | S1、S2、S3 |
| `NOT SATISFIED` | **19** | P1、P2、P3、D1–D6、B1–B4、I1–I3 |
| `UNKNOWN` | **0** | — |

> **S1–S3 的处理（决策 4）**：继续保持 `PARTIALLY SATISFIED`。**Discovery Brief 中已有定义，不等于 Stakeholder 已认可。** 只有完成对应的模拟 Stakeholder Validation 后，才允许升级状态。
>
> `NOT SATISFIED` 的成因是**证据尚未采集**，而非"已知答案为否"。其中 `SATISFIED` 为 0 也属如实记录。

---

## 7. Validation Backlog

`Blocks POC Design?` 严格以 **Brief §19 Entry Criteria 是否为该条所必需** 为判据，不引入自创评分。

**Owner 约定**：所有 `Owner` 为 `Human`（提供或批准模拟输入）；`Agent` 只负责登记与整理，**不得自行生成证据**。`Status` 初始值一律为 `NOT STARTED`。

### 7.1 Phase 1A — Problem Validation（优先）

| ID | Question | Current Evidence Status | Why It Matters | Evidence Needed | Suggested Validation Method | Owner | Status | Blocks? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **VB-01** | 一次完整缺料分析是否需要跨多个系统/数据源查询？耗时多少？ | `HYPOTHESIS` / `TBD`（H1） | §19 P1 直接 Gate；不成立则 AI 价值需重估 | 操作流程、系统数量、单次耗时 | Process walkthrough（Simulated） | Human | NOT STARTED | **YES** |
| **VB-02** | 取数后是否仍需 Excel / 人工二次计算与汇总？ | `HYPOTHESIS` / `TBD`（H2、E09） | §19 P1 直接 Gate；AI 的收益锚点 | Excel 过程、手工计算、导出环节 | Process walkthrough（Simulated） | Human | NOT STARTED | **YES** |
| **VB-03** | 是否有一个具有明确业务价值的缺料分析问题？ | 无记录 | §19 P2 | 问题陈述 + 业务价值判断 | Simulated stakeholder interview input provided by Human | Human | NOT STARTED | **YES** |
| **VB-04** | 主要业务 Owner 是否认可该问题值得进入 POC？ | 无记录 | §19 P3 | Owner 明确表态 | Simulated Sponsor / Business Owner input provided by Human | Human | NOT STARTED | **YES** |
| **VB-05** | 现有 ERP / MRP 是否已能高效完成缺料分析？ | `UNKNOWN`（K-INT-2） | H1 的证伪风险；§17 失败条件 | 现有 MRP 能力说明 | Process walkthrough + Interface / system assumption confirmation（Simulated） | Human | NOT STARTED | **YES** |
| **VB-06** | 现有缺料预警机制是什么？与 AI 层的增量差异在哪？ | `UNKNOWN`（K-INT-3） | 决定 P0 增量价值；避免重复建设 | 预警规则、触发方式、覆盖范围 | Simulated stakeholder interview input provided by Human | Human | NOT STARTED | **YES** |
| **VB-07** | 客户是否认可 P0 闭环及其与 P1 的边界？ | Brief 已定义，Stakeholder 无记录（S1、S2、S3） | §19 S1–S3 | 对 Brief §11/§12 边界的确认 | Simulated Sponsor / Business Owner input provided by Human | Human | NOT STARTED | **YES** |
| **VB-14** | 「缺料」在业务上如何定义？ | `UNKNOWN`（K-BR-1） | P0-1 判定起点；G-07 | 缺料判定条件 | Simulated business decision provided by Human | Human | NOT STARTED | NO |
| **VB-21** | 谁有权查看采购价格 / 选择供应商 / 创建采购申请 / 修改数量 / 批准采购 / 正式下单？ | `UNKNOWN`（K-HITL-1） | §19 I3；P0-3 HITL 边界 | 权限矩阵 | Simulated stakeholder interview input provided by Human | Human | NOT STARTED | NO |
| **VB-22** | Brief §6 的七类角色是否真实存在？各自数据范围与权限？ | `HYPOTHESIS`（§6） | §19 B4、I3 | 真实角色清单与职责 | Simulated stakeholder interview input provided by Human | Human | NOT STARTED | NO |
| **VB-23** | 当前真实缺料分析流程是什么？ | `UNKNOWN`（E08；§5 明示不代表真实流程） | §19 B1；H1/H2 验证载体 | 真实流程步骤描述 | Process walkthrough（Simulated） | Human | NOT STARTED | **YES** |
| **VB-24** | 当前流程的主要步骤数量？ | 无记录 | §19 B2 | 步骤计数 | Process walkthrough（Simulated） | Human | NOT STARTED | NO |
| **VB-25** | 当前分析的平均耗时（实测或可靠估算）？ | 无记录 | §19 B3；§16 要求 KPI 基于真实基线 | 耗时测量或估算 | Process walkthrough（Simulated） | Human | NOT STARTED | NO |
| **VB-26** | 缺料分析多久发生一次？ | 无记录 | §17 失败条件「使用频率过低」 | 发生频率 | Simulated stakeholder interview input provided by Human | Human | NOT STARTED | NO |
| **VB-27** | 风险判断是否依赖个人经验？ | `HYPOTHESIS` / `TBD`（H3） | P0-1「基础风险」规则设计；G-06、G-11 | 历史缺料案例与判断依据 | 历史案例复盘（Simulated case provided by Human） | Human | NOT STARTED | NO |
| **VB-28** | 缺料处理的信息解释成本是否较高？高频问题是什么？ | `HYPOTHESIS` / `TBD`（H4） | AI 在 P0 中角色的正当性 | 高频问题清单 | Simulated stakeholder interview input provided by Human | Human | NOT STARTED | NO |

### 7.2 Phase 1B — Data & System Readiness（后续）

| ID | Question | Current Evidence Status | Why It Matters | Evidence Needed | Suggested Validation Method | Owner | Status | Blocks? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **VB-08** | 生产计划数据的结构与存放位置？ | `UNKNOWN`（K-DR-1） | §19 D1；P0-1 输入契约 | 字段清单、样例结构、拥有系统 | Data readiness check + Mock dataset definition（Simulated） | Human | NOT STARTED | **YES** |
| **VB-09** | BOM 由哪个系统管理？版本机制如何？ | `UNKNOWN`（E07、K-DR-2） | §19 D2；P0-1 计算口径 | 系统归属、版本规则 | Data readiness check + Interface / system assumption confirmation（Simulated） | Human | NOT STARTED | **YES** |
| **VB-10** | 库存数据来源与状态划分（含质检冻结）？是否存在独立 WMS？ | `UNKNOWN`（E06、K-DR-4） | §19 D3；P0-1「预计可用量」 | 来源系统、库存状态枚举、冻结规则 | Data readiness check + Simulated stakeholder input provided by Human | Human | NOT STARTED | **YES** |
| **VB-11** | 采购订单 / 在途数据的可得性？「有效在途」如何界定？ | `UNKNOWN`（K-DR-5） | §19 D4；P0-1「预计缺口」 | 订单数据结构、在途有效性判据 | Data readiness check + Simulated business decision provided by Human | Human | NOT STARTED | **YES** |
| **VB-12** | 必要供应商信息（含 Lead Time、绩效）是否可得且结构化？ | `UNKNOWN`（E10、K-DR-6） | §19 D5；P0-2「供应周期」「风险证据」 | 供应商主数据、Lead Time 来源、绩效记录 | Data readiness check（Simulated） | Human | NOT STARTED | **YES** |
| **VB-13** | 关键主数据能否建立基本关联（物料编码规则）？ | `UNKNOWN`（K-DR-3） | §19 D6（H6）；P0 全链连通性 | 物料编码规则及其与 BOM/库存/订单的对应 | Data readiness check + Mock dataset definition（Simulated） | Human | NOT STARTED | **YES** |
| **VB-19** | 实际 ERP 品牌与版本？系统是否提供 API 或只读访问方式？ | `UNKNOWN`（E05、K-INT-1） | §19 I1、I2 | ERP 信息、接口能力清单、只读通道可行性 | Interface / system assumption confirmation（Simulated） | Human | NOT STARTED | **YES** |
| **VB-20** | POC 数据接入路径采用 API / 数据库 / 导出文件 / 模拟接口中的哪种？ | 尚无决定 | §19 I2 | 明确的接入方式决定 | Simulated business decision provided by Human | Human | NOT STARTED | **YES** |
| **VB-29** | POC 是否可以只读 + 草稿方式接入，无需写入业务系统？ | `HYPOTHESIS`（H7） | §19 I3；安全边界 | 接入边界确认 | Interface / system assumption confirmation（Simulated） | Human | NOT STARTED | NO |

### 7.3 其余 Business Rules 项（POC Design 内细化）

以下均 `UNKNOWN`，状态 `NOT STARTED`，Owner `Human`，**Blocking = NO**（Brief §20 已将其划归 POC Design v0.2，不阻碍**进入** v0.2，但是 v0.2 的必填内容）。

| ID | Question | 关联 Gap | 建议方法 |
| --- | --- | --- | --- |
| **VB-15** | 安全库存如何计算？ | G-04 | Simulated business decision provided by Human |
| **VB-16** | 替代料如何处理？ | G-05 | Simulated business decision provided by Human |
| **VB-17** | 损耗率规则？ | G-03 | Simulated business decision provided by Human |
| **VB-18** | 采购最小批量（MOQ）是否影响采购建议？ | G-10 | Simulated business decision provided by Human |

### 7.4 Backlog 汇总

| 分类 | 数量 | ID |
| --- | --- | --- |
| **BLOCKING** | **16** | Phase 1A（8）：VB-01～VB-07、VB-23<br>Phase 1B（8）：VB-08～VB-13、VB-19、VB-20 |
| **NON-BLOCKING** | **13** | VB-14～VB-18（5）、VB-21、VB-22（2）、VB-24～VB-29（6） |
| 合计 | 29 | — |

| Status | 数量 |
| --- | --- |
| `NOT STARTED` | **29** |
| 其他 | 0 |

---

## 8. Minimum Validation Set Before POC Design

按 Brief §19 的五组 Required Gate，**最少必须先解决下列 BLOCKING items** 才能进入 `POC Design v0.2`。

### 8.1 Problem Validation（Phase 1A）

| 项 | 要求 |
| --- | --- |
| VB-01 | 确认 H1 —— 跨系统查询成本确实较高（附系统数量与耗时） |
| VB-02 | 确认 H2 —— 确实存在人工二次汇总 |
| — | 使 **H1 或 H2 至少一项** 达到 `PARTIALLY CONFIRMED` 或以上（§19 P1） |
| VB-03、VB-04 | 识别具有明确业务价值的缺料分析问题，并获得 Owner 认可 |
| VB-05、VB-06 | 确认现有 MRP 与预警机制的能力边界（H1 证伪防线） |
| VB-07 | 获得对 P0 闭环与 P0/P1 边界（S1、S2、S3）的认可 |
| VB-23 | 完成真实流程记录（同时承载 B1–B4） |

### 8.2 Data & System Readiness（Phase 1B）

| 项 | 要求 |
| --- | --- |
| VB-08～VB-13 | 生产计划、BOM、库存、采购/在途、供应商信息、主数据关联（§19 D1–D6） |
| VB-19 | 确认 ERP 及业务系统接口能力 |
| VB-20 | 明确接入方式（API / 数据库 / 导出文件 / 模拟接口） |

### 8.3 结论

> **进入 `POC Design v0.2` 前，最少必须先解决 16 项 BLOCKING items：**
>
> **Phase 1A（8 项）**：`VB-01`、`VB-02`、`VB-03`、`VB-04`、`VB-05`、`VB-06`、`VB-07`、`VB-23`
> **Phase 1B（8 项）**：`VB-08`、`VB-09`、`VB-10`、`VB-11`、`VB-12`、`VB-13`、`VB-19`、`VB-20`
>
> **最高杠杆项：`VB-23`（真实流程走查）** —— 一次执行可同时承载 H1、H2、E08 与 B1–B4。
>
> **NON-BLOCKING 的 13 项** 可在 Phase 1A/1B 期间或 POC Design 内并行细化，但它们是 v0.2 的必填内容。

---

## 9. Validation Records

本节登记**已获得的**验证输入。每条记录必须符合第 2 节的 Simulation Evidence Protocol。

> **当前状态：本节为空。**
> 尚无任何经 Human 提供或批准的模拟输入。Agent 不得自行生成或补齐任何记录。

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

| # | Evidence Type | Role | Date | Question / Decision | Human-provided / approved | Result | Backlog ID | Entry Criteria Impact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| — | — | — | — | *（尚无记录）* | — | — | — | — |

### 9.3 待输入清单（Phase 1A）

| Backlog ID | 需要的模拟输入 | 建议角色 |
| --- | --- | --- |
| VB-01、VB-02、VB-23、VB-24、VB-25、VB-26 | 当前缺料分析流程走查（含系统、步骤、耗时、频率） | Simulated Procurement / Supply Chain User |
| VB-03、VB-04、VB-07 | 问题价值认可、P0 闭环与边界认可 | Simulated Sponsor / Business Owner |
| VB-05、VB-06 | 现有 MRP 与预警机制能力 | Simulated Customer IT ＋ Simulated Business Owner |
| VB-14 | 「缺料」业务定义 | Simulated Procurement / Supply Chain User |
| VB-21、VB-22 | 权限与角色 | Simulated Business Owner ＋ Simulated Customer IT |
| VB-27 | 历史缺料案例与判断依据 | Simulated Procurement / Supply Chain User |
| VB-28 | 高频问题清单 | Simulated Business Owner |

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
