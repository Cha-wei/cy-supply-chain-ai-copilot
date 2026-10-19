# Portfolio Demo — Local Runtime Integration

固定 SIMULATED 场景，C3.2 视觉冻结。React 只展示 Python 结果并提交显式 Human intent；stdlib localhost boundary 编排现有 Python runtime。Issue #248 / PR #249。

## 启动

### 首次准备（或前端代码更新后）

Windows PowerShell 5.1+；Python **>=3.11**（见根目录 `pyproject.toml`；CI 覆盖 3.11 / 3.12）。确保 `python --version` 指向合适的安装，避免 Windows Store 的未安装别名。

Node/npm **仅构建时需要**。优先使用 CI 已覆盖的 **Node 22** 环境，建议 22 系列最新维护版、至少 **22.20.0**：锁定的 Vite 要求 `^20.19.0 || >=22.12.0`，可选平台依赖 `@napi-rs/lzma-linux-x64-gnu` 要求 `^22.20 || ^24.12 || >=25`。这是当前锁文件约束，不代表扩大 Node 测试矩阵。

在仓库根目录单独准备静态资产：

```powershell
cd portfolio-ui
npm ci
npm run build
Set-Location ..
```

当前锁文件的 198 个 `resolved` 下载地址均为 `registry.npmmirror.com`；`npm ci` 依赖该镜像的可达性和可用性。换网络时可能因 DNS、代理或镜像限制而失败；仅修改 npm 的 registry 配置不能保证覆盖锁定的完整下载 URL。遇到此类失败保留错误并单独排查，不手工批量替换 lockfile 或升级依赖来绕过。本任务只验证执行环境下的干净安装，不证明所有网络可复现。

### 日常启动（已构建，无需 Node/npm）

从仓库根目录执行：

```powershell
.\scripts\start-portfolio-demo.ps1
```

也可以在任意工作目录通过脚本的绝对路径运行（路径按实际克隆位置替换）：

```powershell
& 'D:\桌面\cy-supply-chain-ai-copilot\scripts\start-portfolio-demo.ps1'
```

脚本定位自身所在仓库，检查 Python、`dist/index.html` 和固定端口，再前台执行现有 `python -m snapshot_loader.demo_server --port 4190`。不安装依赖、不构建、不启动 Node、不自动打开浏览器。看到 **`SIMULATED local runtime: http://127.0.0.1:4190`** 后，手动打开 [Demo](http://127.0.0.1:4190/)。启动前提示不是监听成功确认；Python 的实际绑定与启动结果才是依据。

保持终端打开，按 **Ctrl+C** 停止；不创建后台服务。停止会丢失该 Python 内存会话的决定与 Draft。仅绑定 127.0.0.1，浏览器须使用相同 Host/Origin。详情地址 `/procurement/SIM-M2`，身份来自 Python，装配连接件仅为 SIMULATED 展示名称。仍可从仓库根目录直接运行上述 Python 命令。

### 故障排查

| 提示 / 情况 | 处理 |
| --- | --- |
| Python 不在 PATH、版本不足或 probe 失败 | 安装 Python >=3.11，重新打开 PowerShell，运行 `python --version`；确认 PATH 或激活已有合适的虚拟环境。脚本只使用 PATH 上的 `python`，不自动安装或改选解释器。 |
| React build missing | 按“首次准备”执行 `npm ci` 与 `npm run build`。日常脚本不会修复构建；前端改动后也要重建。 |
| Cannot bind 127.0.0.1:4190 | 检查 `Get-NetTCPConnection -LocalPort 4190`；若是之前的 Demo，在原终端 Ctrl+C。不要盲目终止其他进程。端口预检不能消除启动瞬间的竞争。 |
| Python 启动后非零退出 | 阅读原始 Python 错误及退出码；检查构建完整性、静态资产路径/链接或端口。预检失败退出 1，底层服务器失败保留其真实退出码，不把失败报告为成功。 |
| PowerShell 阻止执行脚本 | 按所在组织的脚本执行策略处理，或使用原有 Python 命令；脚本不修改系统执行策略。 |
| 浏览器断线或服务重启 | 重新连接当前服务；旧内存会话不可恢复。不回退到 fixture，也不自动恢复决定或 Draft。 |

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

Windows 上完整 Python 套件还会执行 `tests/test_demo_launcher.py`：用隔离 PATH 和临时构建检查启动错误与底层退出状态。运行前停止 4190 上的 Demo，避免与端口测试竞争；非 Windows 环境显式跳过这组平台测试，不代表 Windows 启动验证通过。

## 非声明

SIMULATED / localhost / Python-memory-only；无数据库、跨会话恢复、持久审计、登录/RBAC、真实 ERP、采购订单或生产执行。无 hosted observation 授权，无整体 AI Eval closure、客户验证或生产就绪声明。ADR-003 不因本实现被重写；§8 overall NOT CLOSED，rule/code-version freshness NOT RESOLVED。停在 Human review，不 merge。
