# C3.2 Final Polish — Apple Premium Rich

状态：READY_FOR_REVIEW / STOP FOR HUMAN VISUAL FREEZE REVIEW。Human已批准palette、surface zoning、layout/IA、primary action style。Typography与material polish交付待冻结；不自行宣称FROZEN。

本文件为portfolio-ui非canonical视觉规格，不定义业务规则或runtime。

## 当前视觉系统

rich.html（?present=1隐藏评审工具）。石墨toolbar #5b666b/96% → 暖白连续工作区 #fdfcf9 → 左暖石色建议面 #f0ede5 + 右冷珍珠灰决策面 #edf1f2；计算依据开放。浅蓝主操作 #d6e7f7 / 深蓝文字 #24577f。所有已批准颜色保持。仅内高光、极细tonal edge与微弱柔影精修材质，不增加分区或卡片。

本地OFL授权Noto Sans SC variable统一中文、英文与数字；system UI作fallback。标题28/500，section19/500，正文15/400，数字60/450（手机50），单位14（手机13）共baseline。正文1.85行距，手机支持说明按语义两行。150–220ms控件状态过渡，reduced motion直接终态。

Concept C信息关系：采购建议 → 计算依据 + AI解释 → 人工审核 → 采购申请草稿。fixture30/30/100/70/100不变，AI只解释，最终决策属人工。审核/草稿为静态预览；无API、runtime、真实批准、ERP写入或生产执行。

## 当前证据

- [字体比较、许可与材质理由](design-reviews/c3-2/final-polish-rationale.md)
- [独立Impeccable Critique与Audit](design-reviews/c3-2/final-polish-review.md)：31/36与17/20，无P0/P1/P2。
- [最终截图与Windows实际字体记录](design-reviews/c3-2/final-polish/)：1440×800、1280×800、390全长、控件及审核dialog。
- 52项Playwright与TypeScript/Vite构建通过；desktop内容796.72px，三尺寸无横向溢出。
- Windows CDP实际Noto Sans SC custom font；主页面541KiB字体成本，无新增依赖。许可随public/licenses分发。字体失败fallback已验证。

未做macOS实机、物理触屏、完整辅助技术或冷缓存性能trace。旧final/与feedback/截图及报告只作历史证据。此前system-only说明不适用于当前版本。

不merge main、不扩业务、不进入runtime integration。唯一下一决策：Human是否正式冻结C3.2视觉系统。
