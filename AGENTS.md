# AGENTS.md

## Project Context

**项目身份：** Yunnan CY Group Supply Chain AI Copilot

**继承的 FROZEN business baseline：**

`docs/discovery/discovery-brief-v0.1.1.md`（`FROZEN`）

该 baseline 是**已冻结的继承事实**，**不是**本项目唯一的「当前工作文档」，也不代表当前项目阶段。

### 动态状态不得硬编码

以下内容属于**动态项目状态**，会随项目演进而变化：

- 当前项目阶段
- active design document 与其他 canonical documents
- 当前 backlog 及其状态
- open PR / branch / CI 状态
- implementation state

这些**不得**作为长期 Agent instruction 硬编码在本文件中。

本文件只保留**稳定**内容：项目身份、继承的 `FROZEN` baseline、治理规则。

动态状态必须由 Agent **从 Repository 恢复**，方法见下方 `## Context Recovery`。

---

## Core Rules

### 1. 以仓库为项目事实源

项目范围、业务事实、正式设计、决策和工程状态最终以 Git 仓库中的正式内容为准。

聊天、临时讨论、Agent 输出和用户提出的想法，不自动成为正式项目事实或决策。

---

### 2. 尊重项目事实与阶段边界

不得擅自：

- 修改 `FROZEN` 文档的实质内容；
- 将 `HYPOTHESIS`、`UNKNOWN`、`TBD` 等转换为已确认事实；
- 伪造客户访谈、业务数据、系统信息或其他 Discovery 证据；
- 扩大已经授权的 Scope；
- 自行跨越项目阶段。

缺少必要信息时，应明确指出，而不是自行补全。

---

### 3. 已授权任务默认自治执行

对于范围明确且已经授权的任务，Agent 默认拥有完成该任务所需的自治权。

应自主完成必要的：

理解 → 计划 → 实现 → 测试 → 修复 → 验证 → 文档同步 → Git commit → Push

普通、低风险、局部且可逆的实现细节，不需要反复请求用户确认。

遇到不确定性时，优先采用简单、可逆、低耦合、影响范围较小的方案。

如果当前任务带有明确限制，例如不 commit、不 push、只修改指定文件、仅分析不实施等，则当前任务的明确限制优先于上述默认自治流程。

---

### 4. 重大决策必须升级

涉及以下情况时，应暂停相关实施并请求 Human Approval：

- 改变业务范围、P0 / P1 或正式 Requirement；
- 修改核心 Architecture 或核心技术栈；
- 引入具有显著长期影响的基础设施或核心依赖；
- 权限、安全、Secrets 或生产环境变更；
- 破坏性数据操作或难以回滚的修改；
- 修改受保护 Git 历史；
- 其他可能产生较大 Blast Radius 的决策。

提出问题时，应同时给出合理选项、主要 Trade-off 和建议，而不是只把问题交给用户。

---

### 5. 未经验证不得宣称完成

任何影响系统行为的修改，都必须进行与其性质匹配的测试或验证。

- 新功能应增加或更新相关测试；
- Bug 修复应增加能够复现问题的回归测试；
- AI / Agent / Prompt / Tool 行为变化应执行相关 Eval；
- 测试或验证失败时不得宣称任务完成；
- 无法执行的验证必须明确说明原因。

不得为了让测试、CI 或 Eval 通过而删除、跳过或弱化有效的验证标准。

---

### 6. 变更必须可追踪、可回滚

每个逻辑完整、已经验证、可以独立理解和回滚的变更单元，应形成对应的 Git commit。

正式变更在远端仓库已配置的情况下，应推送到对应的任务分支。

不得：

- 将无关修改混入同一变更；
- 默认直接修改受保护的 `main` 分支；
- 未经授权执行 force push、改写历史或其他高风险 Git 操作。

---

### 7. 控制复杂度和故障影响范围

新增复杂度应尽可能限制在局部。

优先：

- 模块化；
- 清晰边界；
- 低耦合；
- 独立测试；
- 可替换；
- 可回滚。

不得为了未来可能出现的需求提前引入没有当前证据支持的复杂基础设施。

单个模块、外部服务或 AI 能力发生故障时，应尽可能限制故障影响范围，并在合理情况下提供 Graceful Degradation。

AI 不应成为确定性核心业务能力的唯一执行路径。

---

## Context Recovery

### 适用情形

在以下情况下，Agent **不得依赖之前的聊天记忆**：

- fresh Session；
- Context reset，或 conversation history 被压缩、截断、替换；
- conversation history 不可用；
- Agent 对当前项目状态不确定。

**Conversation history 不是恢复项目状态的必需依赖。Repository 是 durable project memory。**

### 恢复顺序

1. **确认 repository root 与 working directory** —— 二者可能不同，不得假定相同。
2. **读取 `AGENTS.md`** —— 已被自动注入时无需重复读取全文。
3. **`CONTRIBUTING.md`** —— 如果它存在、当前 Task 涉及其规范领域（见下）、且相关规则**尚未在当前 Context 中可靠可用**，则读取其相关章节。
4. **识别当前 Task 所需的 active canonical documents** —— 只识别与当前 Task 有关的文档。
5. **检查必要的 Git state** —— current branch、working tree、recent relevant commits。
6. **如果当前 Task 与 GitHub PR / CI 有关**，检查 relevant PR / CI state。
7. **从上述来源重建** —— current phase、applicable decisions、unresolved work、current Task boundary。

### Minimum Necessary Context

Context Recovery **不等于**每次新 Session 都无差别读取整个仓库。

**不要求**：

- 读取全部 Git history；
- 读取所有 docs；
- 读取全部 closed PR；
- 扫描全部代码。

只读取**足以可靠恢复当前 Task 状态**的内容。

不确定某项内容是否必要时，先不读取；确实需要时再读取。

该原则的 Canonical Definition 见 `CONTRIBUTING.md` 第 4 节「Context & Delegation」，本文件不重复其内容。

### CONTRIBUTING.md

**不得假定** `CONTRIBUTING.md` 已作为 workspace instruction 自动注入。

如果当前 Task 涉及以下任一规范领域，Agent **必须确保相关规则在当前 Context 中可靠可用**；如果尚未加载，则读取 `CONTRIBUTING.md` 的**相关章节**并遵守：

- workflow
- Git / GitHub
- DoR / DoD
- testing
- documentation
- architecture decision
- rule conflict
- context / delegation

本文件**只建立引用关系，不复制** `CONTRIBUTING.md` 的内容。

二者关系与冲突处理由 `CONTRIBUTING.md` 第 1 节「规则优先级（Rule Precedence）」及「与 AGENTS.md 的关系」定义，本文件不重复该规则。

### Fresh Context Continuation

如果 Repository 已能**可靠恢复**当前状态，Agent **不应仅因为「这是新 Context」**就要求 Human 重新解释整个项目。

对于**已经明确授权且仍然有效**的 Task：

- 如果该授权可以从**当前 Task 输入**或 **Repository 状态**可靠确定，应**继续执行**；
- 只有在**无法确定当前授权是否仍然有效**时，才请求 Human clarification。

如果恢复出的 Repository 状态与预期不一致，应**先明确指出差异**，而不是自行假定某一方正确。

---

## Project Standards

详细的开发流程、Git / GitHub Workflow、Definition of Done、测试、PR、代码质量和其他工程规范，由项目其他正式规范文件定义。

Agent 在执行相关任务时，只在实际存在相关规范文件的情况下才要求读取并遵循这些规范。

相关规范文件不存在时，不得自行假设其内容，也不得擅自创建。

如果规范缺失已经影响当前任务的执行或判断，应明确指出缺失了什么，而不是自行补全。
