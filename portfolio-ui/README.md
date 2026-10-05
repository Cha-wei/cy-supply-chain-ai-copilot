# Portfolio Demo — Interaction v1

SIMULATED / presentation-only。React + TypeScript + Vite + Tailwind，shadcn/Radix交互原语。无API、Python bridge、真实AI请求、数据库、身份/权限强制或生产写入。

## 运行

```powershell
cd portfolio-ui
npm ci
npm run dev -- --port 4190 --strictPort
```

打开 http://127.0.0.1:4190/ 先进入采购决策工作台，点击「查看建议」进入 `/procurement/M2` 的既有详情页。旧A/B/C、C1/C2、C3.1和控件探索页不迁入本分支。

## 主路径

1. 从工作台选择唯一待审核建议；详情中采购建议为100件，查看完整依据（缺口30、基础需求30、MOQ100、调整70、建议100）。
2. 查看AI解释：明确预置演示、无实时请求、非runtime证据。
3. 进入人工审核，明确点击「按建议批准100件」。取消、关闭、Escape均不批准。
4. 页面显示人工已批准；原建议仍为100件。
5. 打开采购申请草稿，查看DRAFT、人工批准100、来源建议100，以及无ERP/PO/生产执行声明。
6. 「重新演示」或刷新回到初始状态；没有localStorage/sessionStorage或业务请求。

证据与解释可随时重看；没有把「先读完说明」添加成新的业务审批规则。Human只标识当前演示者的显式操作，不声称认证身份、权限、持久审批或真实runtime HumanDecision。

## 语义来源

- [POC Design §5.20](../docs/design/poc-design-v0.2.md)：解释只消费既有确定性事实。
- [POC Design §6](../docs/design/poc-design-v0.2.md)：approve-as-is保持确定性建议不变；决策来自Human。
- [POC Design §6.1](../docs/design/poc-design-v0.2.md)：decision-derived Draft与DRAFT/非PO/非生产边界。
- fixture源自 `tests/test_hitl_review.py::_FIXTURE_FACT_TEXT`，数值仅字符串投影；TypeScript不实现max(shortage,MOQ)或等价规则。

Canonical允许initial Draft；本演示按当前Human任务刻意只开放批准后的Draft，不修改canonical语义。未实现Override、Reject、Stale、AI unavailable、supplier risk扩展。

## UI状态

`RECOMMENDATION_READY → EVIDENCE_VIEWED → EXPLANATION_VIEWED → REVIEW_OPEN → APPROVED → DRAFT_READY` 是演示阅读/交互进度，不是canonical workflow enum。

`src/state.ts`唯一管理临时决定与弹窗；APPROVE只在审核窗口有效，重复批准被忽略，Draft入口要求决定存在。批准时已可预览；DRAFT_READY表示首次打开草稿。刷新重新mount，RESET清空。决定中的approvedQuantity仅复制fixture.recommended，不计算。

## 验证

```powershell
npm run build
npm test
```

Playwright独立端口4192；桌面1440×800、笔记本1280×800、手机390。覆盖完整路径、非法/重复动作、取消、焦点/Escape、刷新/重置、实际字体、减少动态、overflow和无业务网络/存储。`node scripts/capture.mjs`基于4190预览生成review截图。GitHub独立Portfolio UI workflow运行构建与同一组测试。

## 冻结视觉与来源

C3.2 Apple Premium Rich = FROZEN（Human本轮指令）。从`c10d28a`选择性迁入最终页面、所需原语、字体许可；CSS移除其他variant与展示gallery，仅保留C32及共用基础规则。没有cherry-pick历史探索提交。当前分支从GitHub main `78427dc67e9dcc1ca79342fd77e5b4ac9c6f2f48`新建。

冻结色盘/材质/字体/布局保持；仅增加实际交互所必需的按钮、状态文案、确认与草稿内容，以及180ms草稿轻微显示过渡。字体Noto Sans SC variable（OFL1.1），许可随public/licenses分发；未分发Apple字体。原冻结视觉证据保留在旧分支`codex/c3-2-apple-premium-rich`的`portfolio-ui/design-reviews/c3-2/final-polish/`，不复制旧探索进新实现分支。

## Workspace Entry v1

Interaction v1已获Human接受，本增量以ccd0bf1为基线。`/`仅负责发现固定模拟任务；`/procurement/M2`保留完整Interaction v1。普通同源链接与pathname精确分发，不新增router/backend；未知ID显示未找到，不能映射成另一个物料。返回工作台、再次通过链接打开详情是新页面演示，不持久保存业务状态；刷新与重置继续清除审批。

`material_code = M2`沿用 `test_hitl_review → test_supplier_risk_input → test_shortage_calculation.DEMAND`。`display_name = 装配连接件`只是明确标注的SIMULATED展示标签，不是新增canonical material_name，不参与身份、provenance或计算。路径中的M2只定位本单一fixture，不宣称全项目recommendation grain唯一标识。

工作台显示1条待审核建议、缺口30、建议100、MOQ调整提示和查看链接；不承载审批/拒绝/完整依据/AI展开，没有新增KPI、图表、sidebar或用户能力。详情仅补物料上下文和返回链接。原冻结色盘与正文布局保持。

`npm test`覆盖30项（三视口），新增身份来源、入口→既有主路径、未知路径与深链刷新。入口截图：`node scripts/capture-entry.mjs`，输出review/entry-v1。

STOP FOR HUMAN ENTRY-PAGE REVIEW。不得自动扩展下一里程碑或merge main。
