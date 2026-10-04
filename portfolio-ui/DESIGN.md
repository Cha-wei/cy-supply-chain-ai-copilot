# C3.1 — Apple Premium Light

状态：READY_FOR_REVIEW / STOP FOR HUMAN FINAL VISUAL REVIEW。Human已选择C3 Apple Premium；本轮只精炼为C3.1，不重新比较C1/C2，不进入完整Demo interaction implementation。

本文件仅为portfolio-ui非canonical视觉规格，不定义业务规则、runtime或生产能力。

## 当前视觉母版

入口 premium.html；?present=1隐藏评审工具栏。C3信息架构保留：采购建议 → 计算依据 + AI解释 → 人工审核 → 采购申请草稿。所有数量仍来自src/fixture.ts：30/30/100/70/100。AI只解释，人工决定；审核与草稿仅静态预览。

C3.1采用更浅的graphite工具栏、neutral warm gray画布、连续暖白工作区、轻灰决策面与柔和蓝灰操作。无sidebar，无card grid。系统字体替代独立Noto/Manrope；数字融入同一字族。中文标题500字重、正文15px/1.8；数字60px/500，单位15px；中文tracking0。

依据先摘要，再按需求/采购策略分组；完整字段在查看完整依据。AI职责改为原位disclosure。主要/次要按钮、Tabs、Switch、Input、Textarea、Dialog沿用shadcn原语并定制视觉；Tailwind基础与局部tokens保持同一节奏。150–220ms motion，reduced motion直达终态。

详细设计、字体和材质理由：[visual-rationale.md](design-reviews/c3-1/visual-rationale.md)。

## Review evidence

完成Redesign → Impeccable dual-agent Critique → Revision → Audit → Revision。标题字重、数量单位断行、桌面高度、运算符和关闭态开关对比度已修正。

- [Critique](design-reviews/c3-1/critique.md)：初稿26/32，评分不是最终认证。
- [Audit](design-reviews/c3-1/audit.md)：初稿15/20，修订和验证分开记录。
- [Final screenshots](design-reviews/c3-1/final/)：1440、1280×800、390、控件、审核弹窗。
- Build PASS，Playwright40项PASS。桌面默认完整画面793.83px高；手机无横向溢出。

当前Windows实测Microsoft YaHei UI，无字体文件请求，不分发Apple字体。macOS本地字体效果尚未实机验证。

历史技术原型、A/B/C和C1/C2/C3入口保留供追踪，本轮未重做这些方案。用户尚未完成C3.1最终视觉验收；不合并main。
