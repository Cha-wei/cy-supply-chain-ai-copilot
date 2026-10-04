# C3.2 Impeccable Audit

日期：2026-10-05。独立 Assessment B 使用新建原生 IAB 页签，检查源码、截图、computed styles、键盘、portal 和 Switch 状态，检查后关闭页签。浏览器只读 evaluate 不支持注入，所以未声称存在 detector overlay，也未启动 detector live-server。

Detector：扫描 src/rich，exit 0，原始结果 []，0 findings。继承 CSS 另行阅读；父代理未重复扫描。

| 维度 | 初稿评分 /4 | 发现 |
|---|---:|---|
| Accessibility |2|工具栏小字对比度不足|
| Performance |3|无字体下载，blur局部使用，无持续动画|
| Responsive |4|三档尺寸无横向溢出，主要控件44px|
| Theming |3|C32正确贯穿portal，局部保留显式覆盖|
| Implementation Integrity |4|fixture固定，预览边界明确|
| 合计 |16/20|Good；不是修复后的认证分数|

## 问题与修订

- P1：工具栏#e3e9ed小字与半透明背景合成后的对比为4.26:1。将nav-muted提亮至#f0f4f7；最终回归测试按alpha合成计算并要求至少4.5:1，通过。
- 父代理回归发现：Tooltip容器为rgb(65,85,103)，箭头却是默认黑色。二者改用同一个材质token；最终颜色一致性测试通过。
- 移动Tooltip测试先把触发器移入视口、等待两个绘制帧，再聚焦，避免自动滚动触发Radix关闭；可见性断言没有删除或弱化。
- 弹窗关闭焦点显式采用C32系统蓝；结果行保留单一分隔，避免相邻双线。

其他初稿测量：主按钮白字5.24:1，决策区正文10.46:1，辅助文字4.98:1，输入边界3.16:1，关闭态Switch轮廓对弹窗3.13:1，未选Tab4.66:1，选中Tab7.23:1，Tooltip7.31:1。工具栏浅色焦点4.09:1，已实测键盘状态。

Switch轮廓对轨道2.43:1不单独记为失败：外轮廓对弹窗达到3.13:1，白色thumb可辨，视觉26px轨道的命中区由伪元素扩展为44px。

## 最终验证

- PASS：50项Playwright测试，包含40项历史验证和10项C3.2验证。覆盖五项事实、AI职责、只读审核/草稿、Escape和焦点恢复、输入/分段/开关、portal主题、尺寸、减少动态、字体请求、对比度、Tooltip箭头和导航焦点。
- PASS：TypeScript / Vite build。
- 1440×800、1280×800截图均包含默认完整工作区，实测793.92px高。390px全页1547.20px，无横向溢出。主动展开内容后允许自然增长。
- Windows实际使用Microsoft YaHei UI，非自定义字体；三档fontRequests均为空，不分发Apple字体。
- 最终主界面、控件、审核弹窗和手机截图已检查。源代码修订仅作用于src/rich，历史视觉入口保持原样。

限制：未做macOS/iOS实机字体、物理触屏、屏幕阅读器研究、200%缩放或GPU性能trace。减少动态由父代理Playwright验证，不能归为B的OS偏好实测。初稿评分不等于完整WCAG认证。

STOP FOR HUMAN VISUAL REVIEW。没有业务runtime、API、Python或完整交互实现变更。
