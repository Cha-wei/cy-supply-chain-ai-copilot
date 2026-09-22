# CONTRIBUTING.md

**项目：** Yunnan CY Group Supply Chain AI Copilot
**文档版本：** v0.2
**文档状态：** `APPROVED`
**生效范围：** 本项目日常工程协作流程

> 本文档定义本项目日常工程协作的一般默认流程。
> 业务范围与业务事实以 `docs/discovery/discovery-brief-v0.1.1.md`（`FROZEN`）为准，Agent 行为受 `AGENTS.md` 约束。
> 本文档只规定流程，不定义业务范围、不定义技术栈、不包含具体实现设计。

---

## 1. General Principles

1. **仓库是项目事实源**：项目范围、业务事实、正式设计、Decision 和工程状态以 Git 仓库中的正式内容为准。Conversation、临时讨论与 Agent 输出不自动成为正式事实或 Decision。
2. **证据优先**：严格区分事实、公开陈述、`HYPOTHESIS`、`UNKNOWN`。不得将 `HYPOTHESIS`、`UNKNOWN`、`TBD` 转换为已确认事实，不得伪造 Discovery 证据。
3. **确定性优先**：可以由确定性逻辑可靠完成的问题，不交给 LLM 自由生成。
4. **人负责关键决策**：AI 提供信息、计算、解释与建议；关键业务决策由人负责。
5. **最小改动**：只做当前 Task 授权范围内的事，不做顺带重构、不提前引入没有当前证据支持的复杂度。
6. **能力感知**：对当前 Task 的**所有适用 Gate** 进行判定。已具备执行能力的 Required Gate 必须执行；尚未建立且不是 Required Gate 的能力可以标记 `NOT CONFIGURED`；尚未建立但属于 Required Gate 的能力**不得因此被豁免**。不得使用 `N/A` / `NOT CONFIGURED` 绕过 Required Gate（判定标准与状态词定义见第 6 节）。
7. **规则冲突必须显式报告**：正式规则之间存在冲突、歧义或无法同时满足时，不得静默选择其中一条。必须报告 `Conflict` / `Impact` / `Recommended Resolution`（见第 12 节）。
8. **治理受保护**：`AGENTS.md`、`CONTRIBUTING.md` 及其他正式治理规范，不得作为普通 Feature / Bug Task 的顺带实质修改（见第 10 节"Governance Protection"小节）。

### 规则优先级（Rule Precedence）

规则冲突时，按以下层级处理：

| 层级 | 内容 |
| --- | --- |
| 1 | 事实完整性、安全边界、`FROZEN` Baseline、已批准 Decision |
| 2 | `AGENTS.md` 中的 Hard Rules |
| 3 | 当前 Task 明确获得授权的特殊限制或批准 |
| 4 | 当前有效且适用于该 Concern 的专项正式规范 |
| 5 | `CONTRIBUTING.md` 的一般默认流程 |

关于层级 2 与层级 3 的关系：

- 当前 Task 的明确授权**可以满足** `AGENTS.md` 中要求 Human Approval 的事项 —— 即该授权本身就是所需的批准。
- 当前 Task **可以覆盖**默认 Workflow / 默认自治行为。
- 但当前 Task **不得覆盖** `AGENTS.md` 中不可豁免的 Hard Rules。
- 不得将本文档的优先级顺序解释为 `当前 Task > AGENTS.md Hard Rules`。
- 专项规范可以细化一般流程，但不得静默违反更高层级硬约束。
- 如果仍无法确定，按第 12 节 Rule Conflict Handling 升级 Human Attention。

### Task-specific Constraint 的边界

当前 Task 的明确限制可以覆盖默认 Workflow，例如 `no commit`、`no push`、`analysis only`、`modify only specified files`；但这类限制不得豁免 Rule Precedence 层级 1–2 的内容。

> 完整定义（含 Non-waivable Hard Constraints 清单、Required Gate 交互规则与状态标记要求）见第 6 节「Task 限制与 Required Gate 的交互」，该节为 Canonical Definition。Hard Constraints 清单本身见下方「与 AGENTS.md 的关系」。此处不重复。

### 与 AGENTS.md 的关系

> 本节是「`AGENTS.md` 与 `CONTRIBUTING.md` 层级关系」的 Canonical Definition。其他位置只做引用。

- `AGENTS.md` 是项目 **Hard Rules**，位于 Rule Precedence 层级 2，优先级高于本文档。
- 本文档是一般工程 **Workflow**，位于层级 5。
- Task-specific constraint 与专项规范均**不得豁免**以下 Non-waivable Hard Constraints：

  - 事实完整性（factual integrity）
  - 安全边界（security boundaries）
  - `FROZEN` Baseline
  - 已批准 Decision（approved Decisions）
  - 其他不可豁免的硬约束
  - Required Gates

- 专项规范可以细化本文档，但不得静默违反 `AGENTS.md` 或更高层硬约束。
- 本文档不得与 `AGENTS.md` 冲突，也不得通过修改本文档来改变其效力。

---

## 2. Development Workflow

标准流程：

```
Task 授权
  → Definition of Ready 检查（第 3 节）
  → 最小充分 Context 获取（第 4 节）
  → 方案与影响范围确认（必要时按第 10 节升级）
  → Implementation
  → Testing & Validation（第 6 节）
  → 文档同步（第 9 节）
  → 形成 Commit（第 5 节）
  → READY_FOR_REVIEW
  → Review / Acceptance
  → DONE（第 7 节）
```

要点：

- 已授权任务的默认自治范围见 `AGENTS.md` 第 3 条。
- **如果当前 Task 带有明确限制（例如不 commit、不 push、只修改指定文件、仅分析不实施），该限制优先于默认自治流程**（与 Required Gate 的交互见第 6 节）。
- Task 未 Ready 时不得强行开始，应按第 3 节输出缺口信息。

---

## 3. Definition of Ready

Task 进入 `READY` 前至少保证：

- [ ] **Objective 清楚**：目标可复述，无歧义。
- [ ] **Scope / Out of Scope 足够明确**：明确哪些文件、模块、范围为本次授权范围。
- [ ] **Acceptance Criteria 可验证**：验收条件客观、可判断，而非主观描述。
- [ ] **关键依赖可用**：所需数据、文档、工具、权限已存在或可获得。
- [ ] **不存在必须先解决的重大决策**：若存在，先走第 10 节决策流程。
- [ ] **最小充分 Context 可获得**：足以开始工作，不要求读取全仓库历史。

补充规则：

- 低风险、局部、可逆的普通实现细节**不构成 Blocker**。
- 未 Ready 时，必须说明：`Missing Information` / `Blocking Reason` / `Impact` / `Suggested Next Action`。
- 能够合理拆分继续推进时，应主动提出拆分方案，而不是整体阻塞。

---

## 4. Context & Delegation

### 事实来源与临时上下文

- Repository、正式文档、Task、ADR、Code、Tests、Evals 是项目长期事实来源。
- Conversation 是临时执行上下文，不自动成为 Decision。
- 使用 **Minimum Necessary Context**：不得无差别读取所有文档和全部历史聊天。

### 执行方式选择

根据任务性质选择合适方式：

| 方式 | 适用场景 |
| --- | --- |
| Current Context | 小范围、强依赖当前讨论的任务 |
| Subagent | 自包含、可独立描述的子任务 |
| Workflow / Parallel Workers | 大量独立同构工作（审计、批量检查、多角度验证） |
| Fresh Context | 上下文污染风险高、需要独立视角的任务 |

- 只有运行环境实际支持对应能力时才调用。
- 如果无法自动创建新的顶层 Session，但判断 Fresh Context 更合适，**应生成完整 Handoff Prompt**，而不是要求用户重新解释项目背景。
- **Implementation 与 Review 应尽可能使用独立 Context**，避免同一上下文自我确认。

### Multi-Agent Execution

> 本节补充**多 Agent ／ 多 Context 协作**所需的最小执行约束。
> 它**不**重新定义 Human Approval、DoR、DoD、Required Gate、Git / PR 规则或 Rule Precedence ——
> 相关内容**只引用**本文件其他章节（见第 1 节「规则优先级」）。

**设计原则：本治理不绑定具体 Agent ／ Model。** 角色按 **Role-based assignment** 分配，
**不得**写成 Agent-name-based；「哪个 Agent 扮演哪个 Role」属**动态执行状态**，
**不得**写入本文件作为硬依赖。

#### 角色（Role）

| Role | 职责 | 必需性 |
| --- | --- | --- |
| **Human** | Decision Authority；Human Approval boundary **不变**（见第 1 节与 `AGENTS.md`） | 按现有规则 |
| **Coordinator** | Task decomposition、dependency coordination、integration coordination、并行编排 | **OPTIONAL** |
| **Write Owner** | 某一 **Active Write Scope** 的**唯一**写入者 | 每个 active write scope 必需 |
| **Reviewer** | Independent Review ／ Acceptance Check；默认 **READ-ONLY** | 按现有 Required Gate 判断 |

**Coordinator 是 OPTIONAL ROLE。** 仅在 **complex task ／ dependency coordination ／
task decomposition ／ parallel execution ／ integration coordination** 场景需要。
**简单 Task 不得为了形式主义强制指定 Coordinator。**

**Reviewer 默认为 READ-ONLY**，**不应**在 Review 过程中顺手成为同一变更的 Write Owner。
如 Reviewer 必须实施修改，**必须显式发生 Ownership Transfer**（见下文）；
其修改部分是否需要新的 Independent Review，**按现有 Required Gate 规则判断**。
**不得建立无限 Review Chain。**

#### Write Ownership

**定义：** 每个 **Active Write Scope** 在同一时刻**必须有且只有一个明确的 Write Owner**。

```
Write Scope = file ／ directory ／ module ／ 明确授权的其他 repository area
Write 操作  = edit ／ create ／ delete ／ formatting ／ generated overwrite ／ bulk rewrite
```

**Write Ownership：**

- **不等于** Human Approval；
- **不等于** Merge Authority；
- **不自动**扩大 Task Scope。

**规则：**

1. 同一 Active Write Scope，同一时刻**只能有一个** Write Owner。
2. **不得**覆盖、删除或接管**来源无法确认**或 **Ownership 无法确认**的未完成工作。
3. 同一文件即使计划修改**不同 section**，**默认**也视为 **overlapping write scope**；
   除非明确证明并行修改安全，否则**串行**。
4. 发现 Scope 越界需求时：**不得自行扩大** Write Ownership；
   应由 **Coordinator（如存在）** 或 **Human ／ 当前 Task authority** 重新分配。

#### Parallel Eligibility

```
Parallel Execution = PERMITTED, NOT DEFAULT
```

**不得**为了使用多个 Agent 而人为制造并行。write task 只有**同时**满足以下条件才适合并行：

- Objective 可以独立描述；
- Acceptance Criteria 可以独立验证；
- 输入版本明确；
- 关键依赖已经稳定；
- 不依赖另一并行 Task 尚未决定的 Architecture ／ Contract ／ Schema ／ Design；
- **Write Scope 不重叠**；
- 没有未隔离的 **shared mutable resource**（见第 5 节）；
- 每个子任务可以独立验证；
- 有明确的 **Integration Responsibility**。

```
different files  ≠  automatically independent
```

**只读工作**（audit ／ analysis ／ review ／ multi-angle validation）通常可以更自由地并行。

#### Review Independence

保留现有原则：**Implementation 与 Review 应尽可能使用独立 Context**（见「执行方式选择」）。

在此基础上，**Independent Review** 至少要求：

- Reviewer **未参与**被审变更的主要实现；
- Review 使用 **independent Context**；
- Reviewer **直接检查实际 repository artifact**；
- 检查真实 **diff ／ commit ／ tests ／ validation evidence**；
- **Implementer summary 只能作为辅助信息**。

```
different model  ≠  automatically independent
```

**Independent Context ＋ 直接检查 evidence** 比 Agent 品牌更重要。

如果真正的 Independent Review **属于当前 Task 的 Required Gate 但无法获得**：
按第 6 节 Required Gate 规则处理（`NOT RUN` ／ `BLOCKED`），
**不得**用普通 self-check 伪装成 Independent Review。

#### Ownership Transfer ／ Handoff

**Ownership Transfer 必须显式**，并优先在
**clean ／ committed ／ otherwise recoverable Git boundary** 完成。

交接前**必须确认**：旧 Write Owner **已停止写入**。

接管方**必须从实际 Repository 状态恢复**：

```
current branch
working tree
relevant diff / commit
Validation state
Remaining Issues
```

**不得**仅依赖聊天中的「已经完成」。

**Handoff 优先复用现有载体** —— Current Task ／ Git branch ／ commit ／ PR ／
现有 Delivery Report ／ canonical docs。**不得**因为 Multi-Agent 而强制创建新的 Handoff document。

**跨 Agent ／ 跨 Context 恢复时**，至少应能确定：

| 信息 | 说明 |
| --- | --- |
| Task ／ Subtask | 当前授权范围 |
| Write Owner | 当前唯一写入者 |
| Input Version ／ Commit | 起始 baseline |
| Write Scope | 允许写入的区域 |
| Dependencies | 尚未稳定的依赖 |
| Acceptance Criteria | 验收条件 |
| Current Git State | branch ／ working tree ／ commit |
| Validation Result | 已执行的 Gate 与结果 |
| Remaining Work | 未完成事项 |

上述信息**已存在于** Task ／ Git ／ PR ／ Delivery Report ／ canonical docs 时，
**不得重复复制**（见第 9 节「Canonical Source」）。

#### Fallback Assignment

```
Agent unavailable  ≠  Task automatically BLOCKED
```

**Agent unavailable 只触发 Role Reassignment** ——
除非该 Agent **独有的某项能力本身是当前 Required Gate** 且**没有可用替代方案**
（此时按第 6 节处理为 `BLOCKED`）。

**Role Reassignment 不得改变：**

- Objective
- Scope
- Acceptance Criteria
- approved Decisions
- Human Approval boundary
- Required Gates

**默认：** 如果 Write Owner 无法继续，Ownership 回到 **Coordinator（如果存在）**，
否则回到 **当前 Task authority ／ Human** 重新分配。

**不要求**每个普通 Task 重复填写专门的 fallback owner。

---

## 5. Git & GitHub Workflow

### 分支

- `main` 是可信主线。
- 正式开发 Task 默认使用独立 Task Branch。
- 不得默认直接 Push 到受保护的 `main`。

### Workspace ／ Worktree Isolation

**同一个 writable working tree 不得有多个 concurrent Write Owner。**
（Write Ownership 定义见第 4 节「Multi-Agent Execution」。）

如果多个 Agent **同时**执行 repository write task，**必须**使用：

```
independent Task Branch
+
isolated workspace / Git worktree
```

并**记录或能够恢复**其 **input commit ／ common baseline**。

如果 worktree ／ isolated workspace **当前不可用**，则 fallback 为 **serial write execution**。

```
branch isolation  ≠  Write Ownership replacement
```

即使 branch 不同，**高重叠 ／ 高 dependency task 仍不得强行并行**
（见第 4 节「Parallel Eligibility」）。

**Shared Mutable Resource Boundary：**

Git worktree **只**隔离 repository working files，**不自动**隔离：

```
database
dev server
generated output directory
shared cache
external service
test environment
secrets
other mutable external state
```

存在共享 mutable resource 时：**必须独立分配或串行执行**。

```
separate branch  ≠  full environment isolation
```

**Integration Responsibility：** 并行 write task **必须**由明确 Role
（Coordinator，或当前 Task authority 指定的 Write Owner）负责整合，
并保证 integration 发生在**明确 baseline** 之上；
integration 后的变更仍按本节的 Commit ／ PR 规则与第 6 节的验证规则处理。

### Commit

一个 Commit 应是**可理解 + 可验证 + 可独立回滚**的逻辑变更单元。

- 不得将无关修改混入同一变更。
- Commit 前检查：`git status`、`git diff`。

### Push 与远端

- 远端已配置时，正式 Commit 默认 Push 到对应 Task Branch。
- 远端未配置时，`Push` 类 Gate 记为 `NOT CONFIGURED`（见第 6 节），不得记为 `PASS`。

### PR / CI

- PR / CI 已配置且适用于当前 Task 时，必须执行对应 Required Gates。
- 尚未配置时不阻塞当前 Task，但不得伪造成已执行。

### 明确禁止（未经明确授权）

- `force push`
- 改写共享历史
- 高风险 `reset`
- 删除 protected branch
- 绕过 branch protection

（上述操作同时受 `AGENTS.md` 第 4、6 条约束。）

---

## 6. Testing & Validation

### 基本原则

- 确定性问题优先使用**确定性验证**；不得使用 LLM Judge 替代精确测试。
- 任何影响系统行为的修改，都必须进行与其性质匹配的测试或验证（`AGENTS.md` 第 5 条）。
- 测试或验证失败时，不得宣称任务完成。
- 无法执行的验证，必须明确说明原因。

### 验证类型

按变更性质选择：

- Unit
- Regression
- Boundary / Error
- Integration / Contract
- E2E
- AI Eval
- Permission / Failure validation

### Required Gate 判定

A Gate is Required when any of the following is true:

- 当前 Task 或 Acceptance Criteria 明确要求；
- 当前有效且适用的专项规范明确要求；
- 已配置的 CI / Protection Rule 将其定义为必须通过；
- 缺少该验证，就无法合理证明当前 Task 所声称实现的行为是正确的。

本判定不建立 Task 类型 Gate Matrix；Required Gate 按具体 Task 逐次判定。

### Capability-aware Workflow

项目能力逐步建立。对当前 Task 的所有适用 Gate 进行判定：

- 已具备执行能力的 Required Gate **必须执行**；
- 尚未建立且不是 Required Gate 的能力**可以**标记 `NOT CONFIGURED`；
- 尚未建立但属于 Required Gate 的能力**不得因此被豁免**；
- 不得使用 `N/A` 或 `NOT CONFIGURED` 绕过 Required Gate；
- Required Gate 无法完成时，按下方状态规则处理为 `NOT RUN` 或 `BLOCKED`。

统一状态词：

| 状态 | 含义 |
| --- | --- |
| `PASS` | 适用于当前 Task，已经执行并通过 |
| `N/A` | 对当前 Task 本身不适用 |
| `NOT CONFIGURED` | 项目尚未建立该能力，且它不是当前 Task 必须建立的 Gate |
| `NOT RUN` | 该验证适用于当前 Task，但尚未执行 |
| `BLOCKED` | Required Gate 无法完成，因此阻止进入下一交付状态 |

（不绕过 Required Gate 的规则见「Task 限制与 Required Gate 的交互」小节。）

### Task 限制与 Required Gate 的交互

> 本节是以下内容的 Canonical Definition：Required Gate 判定、状态词语义、Task-specific constraint 与 Required Gate 的交互规则。其他章节只做引用，不重复定义。
>
> Non-waivable Hard Constraints 的清单见第 1 节「与 AGENTS.md 的关系」。

情况与标记的对应：

| 情况 | 标记 |
| --- | --- |
| 该验证适用于当前 Task，但因 Task 明确限制而未执行 | `NOT RUN` + Reason |
| 项目尚未建立该能力，且它**不是**当前 Task 必须建立的 Gate | `NOT CONFIGURED` |
| 对当前 Task 本身不适用 | `N/A` |
| 适用且已执行并通过 | `PASS` |
| Required Gate 无法完成 | `BLOCKED` |

规则：

- Task-specific constraint **不得**使 Required Gate 变成 `PASS` 或 `N/A`；只能记为 `NOT RUN`。
- 不得使用 `NOT CONFIGURED` 或 `N/A` 绕过本来必须满足的 Required Gate。
- 如果被禁止执行的是**当前交付所必需的** Required Gate，则 Task 不得进入 `READY_FOR_REVIEW` / `DONE`，应保持 `IN_PROGRESS` 或 `BLOCKED`。
- 本小节处理"Task 限制**如何作用于** Required Gate"；"Task 授权与 `AGENTS.md` Hard Rules 之间的优先级"见第 1 节 Rule Precedence 层级 2–3。

### Bug 处理

默认顺序：

```
Reproduce → Failing Test → Fix → Passing Test → Regression
```

### Eval 触发

Agent / Prompt / Tool 行为变化触发相关 Eval。

### 禁止的"通过"手段

不得为了让 Test / CI / Eval 通过而：

- 删除有效测试
- 跳过有效测试
- 弱化 Assertion
- 修改 Expected Result 迁就错误实现

### Flaky Test

Flaky Test 必须如实标记，不得通过重跑掩盖。

### 数据真实性

模拟业务数据必须标记 `SIMULATED`，不得传播为真实企业事实。

---

## 7. Definition of Done

### `READY_FOR_REVIEW`

Agent 已完成当前 Task 的全部自主执行工作，并满足所有**适用**的 Required Gates。

### `DONE`

当前 Task 所要求的最终 Review / Acceptance Gates 已全部完成。

- 如果项目已经启用 PR / Merge Workflow，且该流程适用于当前 Task，则 **Merge 到 `main` 是 `DONE` 的必要条件**。
- 尚未建立的非 Required 能力**不得阻止**当前阶段 Task 完成。

---

## 8. Code Quality

### 优先

清晰、简单、局部、低耦合、可测试、可替换、可回滚。

### 避免

- 过早抽象
- 无关重构
- 循环依赖
- 穿透模块内部实现
- 无必要全局共享状态
- 为"企业级"提前增加复杂基础设施

### 注释

关键注释解释 **WHY**，而不是重复代码。可使用以下前缀：

- `BUSINESS RULE:`
- `WHY:`
- `SECURITY:`
- `COMPATIBILITY:`
- `TODO(TASK-xxx):`

### 约束

- `TODO` 必须可追踪。
- 不得保留大段注释掉的旧代码。
- 不得静默吞掉重要错误。
- 优先控制 Blast Radius；故障影响范围应尽量局部化。

### Dependencies

- 新增第三方依赖必须具有明确价值。
- 标准库或现有依赖能够简单满足需求时，不应仅为了便利增加新的长期依赖。
- 核心或高影响依赖按 Architecture & Decision Escalation 处理。

---

## 9. Documentation Guidelines

### 语言

- 内部正式文档默认中文。
- 工程命名和必要技术术语保留英文（如 Git、PR、CI、Eval、`READY_FOR_REVIEW`、`FROZEN`、`UNKNOWN`）。

### Canonical Source

一个 Concern 原则上只有一个 Canonical Source，避免同一规则在多处各写一份并产生分歧。

### 生命周期

正式文档按需使用：

```
DRAFT → REVIEW → APPROVED → FROZEN → DEPRECATED
```

- Git 管理细粒度历史；`Document Version` 表示有意义的正式 Baseline。
- 文档状态需在文档头部显式标注。

### 事实与决策

- 讨论不自动成为正式 Decision。
- 正式 Requirement / Decision / Business Rule / Engineering Standard 应进入对应项目文档。

### 目录与文件

- 不要为了未来可能需要而提前创建大量空文档或目录。
- 文档命名使用小写英文与连字符（如 `discovery-brief-v0.1.1.md`）。

### Synchronization

- 正式行为、API、业务规则、配置、Architecture 或使用方式发生变化时，应检查并同步相关文档。
- 纯内部实现变化不制造无意义的文档更新。

---

## 10. Architecture & Decision Escalation

### 分层处理

- 局部、低风险、可逆的设计由 Agent 自主处理。
- 重大、长期、难回滚或 Blast Radius 较大的决策，必须先进行方案分析并请求 Human Approval（`AGENTS.md` 第 4 条）。

### 概念区分

| 概念 | 含义 |
| --- | --- |
| `IDEA` | 未经验证的想法，不构成承诺 |
| `PREFERENCE` | 倾向性选择，可调整 |
| `DECISION` | 已经批准的正式决定，构成约束 |

### 重大决策分析至少包含

- Problem
- Constraints
- Options
- Trade-offs
- Recommendation

原则上考虑 **Option 0 — Keep Current / Do Nothing**，并优先 **Reversible First**。

### ADR

- 重大 Architecture Decision 在 Human Approval 后形成 ADR，**再**进入正式 Implementation。
- **不得先实施，再用 ADR 事后合理化。**
- 必要时记录 `Revisit Conditions`。

（本文档不包含 ADR Template 细节，模板在需要时另行定义。）

### Governance Protection

- `AGENTS.md`、`CONTRIBUTING.md` 和其他正式治理规范，**不得作为普通 Feature / Bug Task 的顺带实质修改**。
- 治理规则的实质修改必须属于**明确授权的 Governance Task**。
- 纯 typo、坏链接、格式等非实质修正不需要扩大成架构决策。

---

## 11. Delivery Report

正式 Task 交付至少包含以下字段：

| 字段 | 内容要求 |
| --- | --- |
| `Status` | Task 当前生命周期状态；取值为 `IN_PROGRESS` / `BLOCKED` / `READY_FOR_REVIEW` / `DONE`，不得用 `PASS` / `N/A` / `NOT RUN` 描述整个 Task |
| `Changes` | 新建 / 修改 / 删除的文件与范围 |
| `Validation` | 执行了哪些验证，结果如何 |
| `Git` | 分支、commit、是否 push |
| `PR` | PR 状态或 `N/A` / `NOT CONFIGURED` |
| `Known Risks` | 已知风险 |
| `Remaining Issues` | 未解决事项 |
| `Human Attention` | 需要人决策或确认的点 |
| `Write Owner` | **仅当当前 Task 涉及多个 Agent ／ Context 时**：列出各 Active Write Scope 的 Write Owner（定义见第 4 节「Multi-Agent Execution」）；单一 Agent Task 可省略 |

### 语言要求

不得使用"基本完成""应该没问题""看起来可以"等模糊语言代替客观状态。

### Task Status 与 Gate / Validation Status

两者必须区分，不得混用。

**Task Status** —— 描述整个 Task 当前处于生命周期哪一步：

- `IN_PROGRESS`
- `BLOCKED`
- `READY_FOR_REVIEW`
- `DONE`

**Gate / Validation Status** —— 描述单项 Gate 或 Validation 的执行情况：

- `PASS`
- `N/A`
- `NOT CONFIGURED`
- `NOT RUN`
- `BLOCKED`

要点：

- 第 6 节的状态词主要用于具体的 Gate / Validation，不用于描述整个 Task。
- Gate `BLOCKED` 可以导致 Task `BLOCKED`，但两者语义不同：前者指某个 Required Gate 无法完成，后者指整个 Task 因此无法进入下一交付状态。
- Delivery Report 中，`Status` 字段填 Task Status；各单项 Gate / Validation 的结论填在 `Validation` 字段。

### 状态标注（Gate / Validation）

以下为 Gate / Validation 层面的标注方式（状态词语义以第 6 节为准）：

- 未执行但适用：`NOT RUN` + Reason
- 因 Task 明确限制而未执行的适用验证：`NOT RUN` + Reason（**不得**改标为 `PASS` / `N/A`）
- 不适用：`N/A`
- 尚未建立且不是 Required Gate：`NOT CONFIGURED`
- Required Gate 无法完成：`BLOCKED`
- 被禁止执行的必需 Gate 导致 Task 无法交付：Task Status 保持 `IN_PROGRESS` 或 `BLOCKED`

### 详细程度

详细日志留在 Test / Eval / CI / PR 中，Delivery Report 只提供必要摘要。

### Scope 外问题

- 如果正式 Task / Issue Tracker 已配置，Scope 外问题进入对应 Tracker。
- 如果 Tracker 尚未配置：**不得自行创建新的项目管理体系或治理文件**；暂时记录在 Delivery Report 的 `Known Risks` / `Remaining Issues`，以后再迁移至正式 Tracker。

---

## 12. Rule Conflict Handling

如果正式规则之间存在冲突、歧义或无法同时满足：

1. **不得静默选择其中一条。**
2. 必须报告：

   - `Conflict`
   - `Impact`
   - `Recommended Resolution`

3. 治理规则的实质修改**需要 Human Approval**。
4. 无法确定时，升级 Human Attention；必要时暂停相关部分，而不是自行裁量。

---

## Document Control

**Document:** CONTRIBUTING
**Version:** v0.2
**Status:** `APPROVED`

本文档当前为 `APPROVED`，**未** `FROZEN`。

- 本文档已完成实际文件 Review 并获 `APPROVAL`，构成本项目已批准的工程协作基线；但**尚未** `FROZEN`，因此仍可通过治理 Task 修订。
- 实质修改需通过明确授权的 Governance Task，并按第 12 节处理冲突。
- **v0.2（明确授权的 Governance Task）：** 新增第 4 节 `### Multi-Agent Execution` 与第 5 节 `### Workspace ／ Worktree Isolation`，并在第 11 节增加一个**条件性** `Write Owner` 字段。**未**修改 Human Approval、DoR、DoD、Required Gate、Git / PR 规则、Rule Precedence 或 Governance Protection；**未**新增 governance artifact；`AGENTS.md` **未修改**。
- 非实质修正（typo、坏链接、格式）可直接修正，无需扩大为架构决策。
- 本文档不包含：完整 Testing Strategy、Security Policy、ADR Template、Deployment Policy。相关内容在项目实际需要时再单独定义，以避免提前引入无证据支持的规范负担。

### 与 AGENTS.md 的层级关系

`AGENTS.md` 为项目 Hard Rules，优先级高于本文档；本文档为一般工程 Workflow。完整定义见第 1 节「与 AGENTS.md 的关系」，此处不重复。
