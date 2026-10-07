# Portfolio Demo — Local Runtime Integration

固定 SIMULATED 场景，C3.2 视觉冻结。React 只展示 Python 结果并提交显式 Human intent；stdlib localhost boundary 编排现有 Python runtime。Issue #248 / PR #249。

## 启动

先单独构建静态资产：

```powershell
cd portfolio-ui
npm ci
npm run build
cd ..
python -m snapshot_loader.demo_server --port 4190
```

打开 http://127.0.0.1:4190/ 。Python 不启动 Node、不自动构建；缺少 dist 时拒绝启动。仅绑定 127.0.0.1，浏览器须使用相同 Host/Origin。详情地址 `/procurement/SIM-M2`，身份来自 Python，装配连接件仅为 SIMULATED 展示名称。

## 主路径与 authority

工作台 → 建议与计算依据 → 可选 Q3 → 人工审核 → 按建议批准 / 修改数量后批准 / 拒绝 → 批准后查看 Draft。

- Python 独立 composition 使用固定已批准模拟输入，经现有 loader、handoff、pipeline 推导 30 / 30 / 100 / 70 / 100；不依赖 tests 或 observation script。
- Python 创建 AnalysisRun，首个场景日期固定为 2026-10-01。刷新、打开页面/审核/草稿不创建新 run。
- 多标签共享同一 Python 内存会话；刷新读取服务器决定；服务重启丢失会话，浏览器不恢复旧决定或 Draft。
- “模拟新分析运行”在相同 accepted input 上创建新 run。旧 Review/Draft 永久 stale；重新审核不继承旧决定。
- Q3 默认明确 unavailable，不读取 provider credentials、不调用 hosted AI。离线测试注入 stub 验证现有 projection/validator。Review 打开后拒绝补写解释证据。
- Review 创建实际 initial Draft；确认时将实际 HumanDecision 对象绑定至 Draft。Reject 无 approved Draft。固定模拟 actor 不代表认证身份。
- 数量原始字符串传至 Python 既有精确验证；无 TypeScript 数量规则。Fraction 以 numerator/denominator 字符串传输；非整数以精确分数显示，不进行舍入。原建议始终为 100。
- 请求失败不回落到 fixture。结果不确定时读取权威状态，不自动重放决定；显式重新连接不恢复浏览器业务对象。

## 限定传输

仅 `/demo/state` 读取及 `/demo/intent` 有限操作，非通用 API 平台。严格 Host/Origin、字段、绑定、重复 intent 检查；32 KiB body、8 个并发连接、3 秒连接超时、1024 个会话 intent 上限（达到上限 fail closed，需重启演示）。静态资源启动时检查路径/符号链接并快照白名单；无任意文件读取、代理或 provider raw response。

## 验证

```powershell
python -m unittest discover -s tests -q
cd portfolio-ui
npm run build
npm test
```

Playwright 在 4193 启动已构建资产的 Python 服务，串行使用一个会话；覆盖 1440×800、1280×800、390×844。测试设置通过显式 new_analysis 操作隔离，不增加 reset API。[验证与历史测试迁移](review/runtime-integration/validation.md)。既有 review 目录及 capture 脚本属于历史 presentation-only 证据，不是当前运行入口。

## 非声明

SIMULATED / localhost / Python-memory-only；无数据库、跨会话恢复、持久审计、登录/RBAC、真实 ERP、采购订单或生产执行。无 hosted observation 授权，无整体 AI Eval closure、客户验证或生产就绪声明。ADR-003 不因本实现被重写；§8 overall NOT CLOSED，rule/code-version freshness NOT RESOLVED。停在 Human review，不 merge。
