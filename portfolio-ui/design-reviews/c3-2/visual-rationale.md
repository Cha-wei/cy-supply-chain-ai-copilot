# C3.2 — Apple Premium Rich / Visual rationale

Human保留Concept C架构与C3 Premium气质，明确不接受C3.1为最终稿。本轮只交付C3.2，不产生候选组。本文件仅记录presentation层，非canonical业务文档。

## First-glance hierarchy

以温暖明亮的阅读平面为主体，烟熏石墨toolbar提供稳定锚点；右侧低饱和蓝灰连续区域承载AI解释、人工审核与草稿。系统蓝只强调主要操作与少量可发现链接。色彩不编码新业务状态。

| 层级 | 材质 | 目的 |
|---|---|---|
| Canvas | #e6e5df，左上极轻冷灰蓝环境色 | 脱离纯灰网页感，不形成显眼渐变 |
| Primary Workspace | #fcfcf9 | 保持明亮与连续阅读，避免暗色界面 |
| Toolbar | rgba(88,103,114,.95) | 比C3.1有锚点，比原C3石墨黑更轻 |
| Decision Surface | #e8eef4 | 通过色温而非大量卡片区分理解与判断 |
| Primary Action | #176bcc / hover#105bb0 | 纯净、有存在感的系统蓝，限定于小面积操作 |
| Floating / Modal | 97%冷暖中性近白，柔和深度 | 与主页面同一系统，正文不依赖玻璃效果 |

背景只有一个低透明度ambient tint，无强渐变、霓虹、多色KPI或图表。toolbar使用局部blur和细高光；工作区使用柔和阴影；decision surface保持实色易读。没有card stacking。

## Typography rationale

延续系统字体栈，中文与数字同源：-apple-system、BlinkMacSystemFont、SF Pro Text、PingFang SC、Hiragino Sans GB、Microsoft YaHei UI、system-ui、sans-serif。不引入或分发Apple字体文件。

标题500字重，正文15px/1.8行高，中文tracking0；数字60px/500、tabular-nums，单位15px/400。数量与单位在解释中保持同行。品牌使用适当字重与更精确的toolbar对齐，不放大业务数字来代替整页设计。

依据保持summary first：自然文案解释30与100的关系，下面分需求/采购策略，原始technical fields仅在完整依据。AI问题采用“为什么建议采购100件？”。文字层级服务阅读，色彩系统是本轮第一优先级。

## Controls and motion

Primary、Secondary、Ghost、Dialog、Input、Textarea、Switch、Segmented、Tooltip与Disclosure均使用C32 token和局部状态样式。按钮44px，焦点明确；深色toolbar使用浅色focus token。控件原语仍为shadcn/Radix，未使用默认Card布局。

150–220ms：材质颜色过渡、轻微4px页面进入、dialog scale/fade、disclosure展开。无bounce、parallax或装饰动画；reduced motion保留最终状态和焦点。

## Business boundary

fixture仍为Shortage30、BasePurchaseNeed30、MOQ100、MOQAdjustment70、Recommended100。AI仅解释，人工决定。无API/runtime、真实AI、真实HumanDecision、供应商选择、ERP写入、采购订单或生产执行。

STOP FOR HUMAN VISUAL REVIEW；不进入完整Demo交互开发。

## 评审后的精炼

普通辅助文字从偏蓝灰调整为中性石墨灰，决策区保留冷色文字，避免所有小字都像链接。问题句为17px、分区标题18px；主数字仍60px，没有用放大数字替代色彩设计。

工具栏辅助文字提亮至#f0f4f7以满足对比度；Tooltip箭头与容器共用同一材质色。审核结果行使用单一轻分隔和适当间距，关闭按钮使用明确的系统蓝焦点。移动端只收紧局部间距，保留完整事实与信息顺序。

## Human feedback revision — 2026-10-05

当前视觉以 `design-reviews/c3-2/feedback/` 截图为准，早期 final/ 保留作对比。主按钮改为浅蓝底 #d6e7f7、深蓝文字 #24577f；暖石色 #f0ede5 将采购建议与数量关系组成一个整体，冷珍珠灰 #edf1f2 承载连续决策区。计算依据保持开放，不为每个模块加框。工具栏使用更柔和的石墨灰，正文仍采用 system UI。

手机端说明按语义分为两行，避免孤字；正文不缩小。完整复审记录见 `design-reviews/c3-2/feedback-review.md`。当前仍为待 Human 视觉确认的静态原型。
