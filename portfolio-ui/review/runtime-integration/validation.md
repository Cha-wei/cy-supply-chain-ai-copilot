# First connected runtime tranche — validation

Issue #248 / PR #249. Base: ba99e47dace3c384ff07530ec8356b1e45f84236. SIMULATED, offline provider only. C3.2 CSS、UI primitives、字体与依赖未变。

## Executed evidence

- Python full suite: 1181 tests, PASS, 2 existing skips. Includes 21 new composition/session/HTTP regressions; these 21 also passed again after the bounded intent capacity update.
- Build: PASS. Connected Playwright: **132 / 132 PASS** (1440×800, 1280×800, 390×844).
- CI: repository Foundation + Python 3.11/3.12 and Portfolio UI connected-demo checks are required on PR #249. Head-bound results are recorded in PR checks / PR validation summary; READY_FOR_REVIEW requires all to pass.
- Independent technical review: original stale-review/current-Q3 visibility finding fixed and regressed; HTTP exact lifecycle coverage added. Final independent technical + documentation review completed: no remaining blocking findings.

## Test migration

原 87 项 browser-fixture tests 不再对生产路径使用本地 reducer。保留有效质量标准，按真实 authority 迁移：

| Previous obligation | Connected coverage |
| --- | --- |
| Workspace / Shell / identity / detail | runtime SIM-M2、single module、稳定 rail、row keyboard/hover、三尺寸与 900px |
| Approve / override / Reject / Draft | 真正 HTTP → Python 对象；原建议100、override120、拒绝无 approved Draft、terminal/replay |
| Exact invalid input / retry / long input | 原文传输、既有 Python grammar/MOQ/reason、Fraction 字符串、非法无决定后重试、长文无 overflow |
| Refresh/reset clears browser business | 有意更新：refresh/多标签读取 Python；服务重启不恢复；new_analysis 后必须新 review |
| Four-component stale binding | Python 既有 HITL/Draft binding matrix + connected new-run stale；不在 TS 复制 binding 规则 |
| Cancel / Escape / focus / Enter | 三类确认弹窗无隐式决定、focus trap/restore、重新审核焦点 |
| Typography / contrast / reduced motion | CDP 实际 Noto、自托管字体失败可操作、>=4.5 对比度、reduced motion 与 responsive 截图 |
| No business network | 有意更新：仅同 origin 本地 runtime；无 hosted 请求、无 browser persistence 或 fixture fallback |
| Explanation fixture | existing Q3 projection/validator offline stub + unavailable 不阻塞；晚解释不变更 Review |

额外失败覆盖：响应丢失后权威重读、跨标签新 run 关闭旧弹窗、stale/session/replay 拒绝、Host/Origin/duplicate JSON/size/framing/timeout、静态路径与 symlink、secret sentinel、并发上限。无测试以 hosted 服务为依赖。

## Limits / non-claims

无 hosted observation、身份权限、持久审计、数据库、ERP/PO/生产执行。画面检查是冻结视觉与可读性检查，不宣称 pixel-perfect image-diff。截图由本地 Windows Chromium 实际连接生成；此前探索图仍为历史记录。


## Screenshots

| Viewport | Workspace | Detail | Override dialog |
| --- | --- | --- | --- |
| 1440×800 | [workspace](workspace-desktop.png) | [detail](detail-desktop.png) | [dialog](dialog-desktop.png) |
| 1280×800 | [workspace](workspace-laptop.png) | [detail](detail-laptop.png) | [dialog](dialog-laptop.png) |
| 390×844 | [workspace](workspace-mobile.png) | [detail](detail-mobile.png) | [dialog](dialog-mobile.png) |

Screenshots use full-page capture, so image height may exceed viewport height. Final suite passed without retries. Earlier local runs exposed a Windows socket-buffer error and an incorrect test-only cancel-button selector; the complete final rerun passed. No effective assertion was removed to obtain this result.
