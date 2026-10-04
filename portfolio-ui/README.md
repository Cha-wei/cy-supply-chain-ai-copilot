# Portfolio Demo UI — 技术原型与视觉探索

独立、实验性的高保真 presentation prototype。**SIMULATED Portfolio POC**，不是 runtime evidence。所有代码与依赖仅在本目录；不影响 Python package。最终状态目标为 READY_FOR_REVIEW，不自动 merge main。

## 本地预览

需要 Node 20.19+ 或 22.12+。

```powershell
cd portfolio-ui
npm ci
npm run dev -- --port 4178 --strictPort
```

浏览器打开 http://127.0.0.1:4178 。Vite 仅为本地前端开发预览工具，不是业务 backend/API。

## 3–5 分钟演示

1. 说明 SIMULATED、presentation-only 与 Calculation / Explanation / Decision authority。
2. 说明 accepted snapshot 是 fixture 展示；比较 shortage 30 与 MOQ 100。
3. 展开 calculation evidence，展示五个事实以及 30 + 70 = 100 的关系。
4. Explore explanation：AI 解释既有数量，不负责计算；本页显示 prepared wording。
5. 在 Human Review 选择 Approve as recommended，检查确认框并确认 demo approval。
6. 展示 approved 100 的 Procurement Request Draft；强调无 ERP、无 PO、无生产执行。
7. 可选：Reset 后切换 AI unavailable，确认 calculation 未变；或 Reject，确认无 approved Draft。

## 验证

```powershell
npm run build
npx playwright install chromium
npm test
```

Playwright 覆盖桌面 1440×1100 与移动 390×844：主流程、取消确认、reject、reset、刷新清空、AI unavailable、无水平溢出、浏览器错误检查；截图在忽略的 `test-results/`。视觉规格见 [DESIGN.md](DESIGN.md)。

## 范围与风险

数量来自 `tests/test_hitl_review.py` 的同名五项事实（baseline 96b19ea）。本页没有 Python bridge、真实 AI 调用、校验、业务算法、数据库、认证或持久化。Supplier risk 未展示实际值；override / stale 未加入第一版。批准只改变浏览器内存中的 presentation state，不是有效 runtime HumanDecision。

真实客户验证 NOT PERFORMED；业务价值 NOT PROVEN；Production Readiness 与 POC SUCCESS NOT CLAIMED。浏览器测试不替代 core runtime tests / AI eval / business acceptance。

Human Design Review 后才能决定下一阶段；runtime integration 须独立 Architecture Review。

## 验证记录（2026-10-04）

- PASS：TypeScript / Vite production build。
- PASS：Playwright 10 项，1440×1100 / 390×844 主流程与 1280×800 键盘检查。
- PASS：浏览器截图自查（桌面、移动、确认框、Draft）；发现并修复了移动 grid 的 min-content 水平溢出，保持原断言后重新通过。
- PASS：核心 Python 回归 1160 项，原有 2 项 skip 保留；未修改 Python。
- NOT CONFIGURED：独立前端 CI；本目录提供可复现本地测试。仓库既有 CI 在 PR 运行。
- N/A：AI Eval（无 AI / Agent / Prompt / Tool runtime 行为变更）。
- Human Design Review：待完成；不把自查当作独立审查或 Human acceptance。

## v0.2 视觉探索（当前工作）

Human 已否决 v0.1 视觉；v0.1只保留为技术原型。三个全新中文方向入口为 `/concepts.html?concept=A`（也可B/C），详见 DESIGN.md。仅preview，不是完整交互产品。v0.1入口仍为 `/`，原测试保留。

Impeccable Critique（双代理）→ Revision → Audit → Revision已完成。20项Playwright通过；当前READY_FOR_REVIEW，等待Human Design Selection，尚未选择最终方案。

启动本次预览：npm run dev -- --port 4182 --strictPort；停止：在运行该命令的终端按Ctrl+C。浏览地址：http://127.0.0.1:4182/concepts.html?concept=A 。最终截图：design-reviews/final/，设计报告：design-reviews/critique.md 与 audit.md。

## 当前评审：Concept C 整体视觉系统（2026-10-05）

Human 已选 C 信息架构。打开 `http://127.0.0.1:4178/apple.html?variant=C1`，比较 C1明净、C2层叠、C3雅致。`&present=1` 为纯画面模式；工具栏提供控件与状态样本。只做视觉预览，不执行批准或生成草稿。

最终截图在 `design-reviews/apple/final/`；设计理由在 DESIGN.md。Impeccable Critique/Audit及修订记录在 `design-reviews/apple/critique.md`、`audit.md`。32项Playwright测试通过，包含原有20项和本轮12项；build通过。状态READY_FOR_REVIEW，等待Human选择，未合并main。

截图复现：先以4184启动预览，再运行 `node capture-apple.mjs final`；对比度采样使用 `node audit-apple.mjs`。这些验证只证明展示层，不是运行时业务证据。

## 当前评审：C3.1 Apple Premium Light（2026-10-05）

Human已选择C3，当前只交付C3.1。打开 `http://127.0.0.1:4178/premium.html`；`?present=1`为纯画面。工具栏可查看控件与状态样本。

1440、1280×800、390和控件/审核弹窗截图在 `design-reviews/c3-1/final/`；设计理由、Impeccable Critique和Audit在 `design-reviews/c3-1/`。40项Playwright测试和build通过。C3.1使用本地system UI字体，不引入Apple字体文件；旧入口保持原样。

截图复现：以4184启动预览，运行 `node capture-premium.mjs final`。状态READY_FOR_REVIEW，STOP FOR HUMAN FINAL VISUAL REVIEW，不实现完整业务交互，不merge main。
