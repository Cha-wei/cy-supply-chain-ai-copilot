# Human Decision v3 — Stale / Re-review validation

2026-10-06。Status: READY_FOR_REVIEW。STOP FOR HUMAN STALE / RE-REVIEW REVIEW。

## Baseline / scope

Accepted UI head: 864785e58138d4e2f042d7c2bb50ed94391d44e0。开工前fetch确认main仍为78427dc67e9dcc1ca79342fd77e5b4ac9c6f2f48。新分支codex/human-decision-v3-stale；不修改/扩展PR #244，不merge。

语义来源：POC Design §6 HD-4、§10.3–10.6；HITL H10–H13/R4–R5/O12–O14/B5–B7、Draft D12–D15/D26–D27相关源码/测试。未修改canonical docs或Python。

## Implementation invariants

- DemoBinding仅占位字符串，不生成真实AnalysisRun。四组件全比较，无rule/code-version字段或freshness能力宣称。
- review owns binding/decision/stale/draftViewed。失配产生同id的永久stale快照；恢复原绑定也不清除stale。
- REREVIEW creates a different object/id，previousReview仅保存最近一次stale快照以保证可验证，非历史功能、非持久审计；新review决定与草稿状态为空。
- 决定事件携带reviewId，旧实例的confirm不能作用于新review。旧实例所有决定及Draft入口fail closed。
- Explanation绑定初始prepared context，失配后retired，本演示会话不复活；没有provider调用或新解释伪造。RESET是全演示重启，旧对象不改写。
- 旧决定仅参考；120的旧草稿非actionable，新review可明确approve100或override130并生成新草稿。推荐固定100及MOQ调整70不变，不重算、不主张跨run等价。

## Validation

- npm run build: PASS。
- npm test: 87 passed (41.7s)，1440×800 / 1280×800 / 390×844。
- 原63项回归全部保留，测试仅适配review嵌套字段与reviewId参数，没有弱化业务/视觉断言。
- 新增24项跨三视口测试：四组件×pending/approve/override/reject矩阵；恢复原绑定仍stale；所有旧动作与Draft阻断；新对象/id与无继承；旧事件reviewId拒绝；旧解释不可用；新审核不依赖解释完成批准；重复演示周期；键盘、焦点、Escape、reduced motion、刷新/reset；无API/fetch/xhr/非GET业务调用或local/session storage。
- 15张截图：三视口演示控制、pending stale、override stale、新review、新Draft。正文full-page，弹窗800px视口；measurements.json记录宽度/id/state。
- 独立只读审查未发现可操作问题；独立手机验证批准→模拟更新→新review，焦点依次落在重新审核与按建议批准，新id=2无旧决定、旧解释仍不可用。

## Impeccable bounded review

沿用C3.2冻结材料/字体/按钮，仅增加失效提示。批量检查桌面/手机截图：失效标识与旧决定区分明确；无红色故障页、虚构菜单或新业务输入；移动弹窗完整且技术绑定文案能换行。源码detector退出0、无输出；不将扫描当作视觉质量的单独证明。无进一步视觉探索。

## Limits / remaining gate

无runtime、Python bridge、API、provider、ERP/PO、真实run生成、权限或持久记录。fixed fixture仅服务展示，不代表真实新run结果。技术验证无已知未解决finding。剩余Human Stale / Re-review Review；远端CI结果由新Draft PR当前checks提供。
