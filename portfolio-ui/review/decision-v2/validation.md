# Human Decision Interaction v2 — review and validation

日期：2026-10-06。基线：e5d5d4c（已接受 Workspace Shell v1.2）。当前状态：READY_FOR_REVIEW，等待Human Decision Review；不merge main。

## 范围与语义来源

- 详情三入口：按建议批准、修改采购数量、拒绝建议。Workspace和Shell源文件未修改。
- 语义对照：POC Design §10.4/§10.5、§6.1；snapshot_loader/exact_quantity.py与constants.py；test_hitl_review.py O1–O8。
- 仅在UI验证Human输入，不接Python/runtime/API。精确十进制输入，>0且>=适用MOQ100，原因非空；科学计数、千分位、空白和malformed输入fail closed。无rounding/clamp，无新业务精度限制。
- sourceRecommendation固定100；approvedQuantity来自显式Human决定。Override内部仍approve+override标识；即使等值也保持真实路径。Reject无批准数量、不可打开Draft。此记录是presentation-only，不是canonical HumanDecision。
- Draft只从有效批准决定读取数量，显示来源建议100，DRAFT和ERP/PO/生产执行NO；所有状态只在内存中。

## 验证结果

- build：PASS。
- Playwright：63 passed（最终修复后33.0s），1440×800、1280×800、390×844。
- 原39项回归保留，唯一相应调整为初始按钮从「进入人工审核」改为「按建议批准」；未降低原断言。
- 新增：120+原因→OVERRIDDEN→Draft120/来源100；Reject必填原因→REJECTED/无草稿；输入格式、零/负数/低于MOQ、高精度/大数/等值override、重复与跨弹窗事件保护；刷新和重置；两路径无API或storage。
- A11y：三入口键盘打开；Tab不决定；数量输入Enter不提交；Escape/取消回到触发器；决定后焦点到Draft或Reset；错误关联字段并聚焦；状态live announcement；reduced motion。
- 60位数量加小数与长原因验证状态、human-review和dialog内部无溢出；没有通过输入上限规避问题。
- 24张截图：三种宽度下pending、批准摘要、override弹窗/摘要/Draft、invalid输入、reject弹窗/摘要。弹窗为实际800px视口截图，正文长页使用full-page。

## Impeccable bounded critique / audit

沿用冻结C3.2字体/材质/控件，只审查此次Human Decision增量。首轮发现手机草稿按钮挤压，调整为纵向按钮；独立只读审查发现合法长数量会在状态句中裁切，增加anywhere换行与内部容器测试。第二轮截图确认两者解决。detector执行退出0、无输出；不把该扫描当作视觉质量证明。

独立Reviewer复核exact/MOQ/reason/终态/Reject/focus未发现其他问题。P2长数量裁切经独立390px复测关闭：status和human-review均clientWidth=scrollWidth=278px。

## 边界与剩余事项

没有新依赖、Python修改、后台、API、持久化、身份权限、ERP/PO/生产执行。未实现Stale、Re-review、AI unavailable或supplier扩展。技术验证无已知未解决项；Human尚需评审三条决定路径的产品表现。停止在该评审关口。

## Final Copy Polish（2026-10-06）

Human已接受Interaction v2。本次只移除人工摘要「调整」差额行和专用显示计算函数，状态改为「已修改并批准 · 演示」。决定摘要保留系统建议、人工批准、决定方式、原因；不在其他位置展示人工差额。state.ts、输入校验、fixture、CSS、Shell和Draft逻辑未修改。

build PASS；完整Portfolio UI 63项测试PASS（37.4s）。新增精确字段列表、无+20、状态文字、MOQ调整+70不变断言；既有100建议→120批准→120草稿和Reject无草稿继续通过。最终截图在final-copy目录，覆盖1440/1280/390；此前截图为修改前历史记录。

本轮独立Reviewer因用量限制未执行；主执行者已核对限定diff与截图。未声称本轮独立审查通过。现有PR #244保持Draft，不新建Issue/branch/PR，不merge。

Status: READY_FOR_REVIEW — Human Decision v2 Final Polish。远端CI结果见原PR当前提交checks。
