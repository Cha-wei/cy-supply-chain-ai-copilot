# Product

面向求职 Portfolio 的中文供应链 AI Copilot，C3.2 与 Workspace Shell 保持冻结。一个固定 SIMULATED 场景，通过本地 Python runtime 展示计算依据、可选 Q3、显式人工决定与批准后 Draft。

工作台只发现任务并进入详情，不扩展业务能力。SIM-M2 身份来自 runtime；装配连接件仅为展示名称，不参与 identity、计算或 provenance。

建议 100 不因人工决定改变。批准、数量 override、拒绝、stale 与重新审核均由现有 Python 对象执行。浏览器只有显示状态与显式意图；刷新保留服务器状态，重启服务结束会话。相同输入的新分析运行不声称输入发生变化。

Q3 默认 unavailable；不请求真实 provider。已有 Review 的解释证据不可后补。没有 ERP/PO/生产执行、认证身份、持久审批或审计能力。范围与启动见 README，证据见 review/runtime-integration/validation.md。
