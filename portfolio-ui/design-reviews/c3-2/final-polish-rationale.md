# C3.2 Final Polish — typography and material

状态：READY_FOR_REVIEW；仅待 Human Visual Freeze Review。配色、分区、IA、布局和浅蓝主按钮已获 Human 通过，本轮不重新探索方向。

## 字体比较与选择

同一最终页面只替换字体进行比较：final-polish/typography-system-comparison.png 与 typography-noto-comparison.png。前者 Windows 实际为 Microsoft YaHei UI，后者为 Noto Sans SC variable；CDP 证据在 typography-comparison-fonts.json。typography-system-before.png 另保留精修前的历史画面，不作为严格同参数比较。

选择 Noto Sans SC。中文的笔画与数字形成更一致的密度，避免微软雅黑在此环境下较细弱的正文与机械节奏。并非恢复 v0.1 的 Noto + Manrope：全页、数字、工具栏和 portal 控件统一同一字族；不引入独立数字展示字体。自然度仍属于 Human 的视觉判断，不宣称该字体普遍优于系统字体。

主标题28px/500/1.4；分节19px/500/1.5；问题句17px/450/1.65；正文15px/400/1.85；辅助12–14px。中文标题轻微0.01–0.015em字距，正文不增加tracking。主数字60px/450，移动端50px；公式26px/450；表格事实16px，tabular-nums统一。单位14px（手机13px）与数字共用baseline和9px（手机6px）间距。中英文品牌采用同一字族，12px图文间距，CY仅通过字重和紧字距识别。手机说明按语义换为两行，不缩小字号。

## 来源、许可与加载成本

复用已安装的 @fontsource-variable/noto-sans-sc 5.3.0，无新增npm依赖。包metadata声明来源 https://github.com/google/fonts ，字体系列Noto Sans SC，Google Inc.，SIL Open Font License 1.1。完整随包许可已复制至 public/licenses/noto-sans-sc-OFL.txt 并随构建分发。未使用或分发Apple字体文件，未修改字体资产。

字体由本地服务提供，unicode-range按需加载WOFF2分片，font-display:swap。主页面11片，encoded font body总计554,164 bytes（约541KiB），这是相对系统字体的明确成本；不是加载时间或冷缓存性能评分。未增加远程CDN依赖。额外弹窗文字可能请求更多分片。Windows CDP实际命中Noto Sans SC Thin，isCustomFont=true；Thin是variable内部family名称，实际CSS权重400/450/500/650，不代表统一使用100字重。标题、分节、正文、数字、品牌逐角色证据见measurements.json。字体请求失败时回退system UI，自动验证事实与对话框仍可读、无横向溢出。

## 材质精修

所有已批准色值保留。石墨toolbar仅添加极弱顶部内高光、底部hairline、12px克制背景模糊和1px柔和阴影；品牌间距和hover区域同步精修。暖石色建议面、冷珍珠灰决策面使用同一极弱内边缘与低偏移柔影，计算依据保持开放。没有新增卡片或表面层级。

控件保留现有结构和radius体系：14px按钮文字与16px图标居中，轻微内高光呼应表面；secondary、disclosure、tabs、switch、input、textarea、tooltip继承C32 token；portal标题字重、输入文字、光标色与关闭按钮圆角统一。既有hover/active/focus/disabled及150–220ms动作语言保留，reduced motion保留终态。

## 交付

final-polish/：C3.2-1440.png（1440×800）、C3.2-1280.png（1280×800）、C3.2-390.png（390宽完整滚动页）、C3.2-controls.png、C3.2-review-dialog.png。内容桌面高度796.72px；mobile1572.06px，三尺寸无横向溢出。独立critique与audit见final-polish-review.md。

未改变30/30/100/70/100、解释责任或人工决定权。SIMULATED/presentation-only，未接runtime、未改Python/API，不merge main。
