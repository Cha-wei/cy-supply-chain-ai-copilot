# C3.2 — Apple Premium Rich

状态：READY_FOR_REVIEW / STOP FOR HUMAN VISUAL REVIEW。Human 保留 Concept C 信息架构和 C3 Premium 气质，C3.1 未被接受为最终稿。本轮只交付 C3.2。

本文件仅为 portfolio-ui 非 canonical 视觉规格，不定义业务规则、runtime 或生产能力。

## 当前视觉系统

入口 rich.html；?present=1 隐藏评审工具栏。烟熏石墨 toolbar → 暖白连续工作区 → 蓝灰决策面 → 冷白临时弹层，形成四级材质关系。低透明度 ambient tint 仅用于画布，系统蓝集中在主要操作和少量链接。

Concept C 信息关系保持：采购建议 → 计算依据 + AI解释 → 人工审核 → 采购申请草稿。fixture 仍为30/30/100/70/100。AI只解释，最终决定属于人工；审核和草稿均为静态预览，不记录批准、不调用业务服务。

系统字体、500字重中文标题、15px正文与同字族数字延续。问题句调整为17px，普通辅助文字更中性，决策区文字保留轻微冷色。依据采用摘要和分组，完整技术字段放入详情。

所有按钮、输入、开关、分段、Tooltip、Disclosure与Dialog均使用C32视觉语言。150–220ms克制过渡；减少动态偏好直接呈现终态。无新增sidebar、dashboard或图表。

## 设计与验证证据

- [色彩／材质／字体理由](design-reviews/c3-2/visual-rationale.md)
- [Impeccable Critique](design-reviews/c3-2/critique.md)：双独立评审，初稿30/36。
- [Impeccable Audit](design-reviews/c3-2/audit.md)：初稿16/20，问题与修订分开记录。
- [最终截图](design-reviews/c3-2/final/)：1440×800、1280×800、390、控件、人工审核弹窗。

工具栏对比度与Tooltip箭头已修复；摘要/分组间距、问题句层级、审核结果行和弹窗焦点已调整。桌面完整工作区高793.92px，390移动无横向溢出。50项Playwright测试与TypeScript/Vite构建通过。

Windows实测Microsoft YaHei UI，无字体文件请求，不分发Apple字体。macOS实机、物理触屏和完整辅助技术验证未执行。

旧探索入口保留供追踪，本轮未重做C1/C2。等待Human视觉验收；不合并main，不自动开始完整Demo交互开发。
