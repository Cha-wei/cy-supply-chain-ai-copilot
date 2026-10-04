# Concept C — holistic Apple-inspired visual systems

状态：READY_FOR_REVIEW，等待 Human Visual Selection。Human 已选择 Concept C 信息架构；C1/C2/C3 视觉系统尚未选择。v0.1 仅 technical prototype，A/B/C 为历史探索。

本文件仅为 portfolio-ui 的非 canonical 视觉规格，不定义业务语义、正式架构或生产能力。用户指定方向优先于 Impeccable concept-seed（ae5ef1b9）的随机建议。

## 同一结构与事实

入口 apple.html?variant=C1|C2|C3；加 &present=1 隐藏外部评审工具栏。

单一 Workspace 组件：导航 → 采购决策标题 → 左侧采购建议与计算依据 / 右侧 AI解释、人工审核、草稿 → 权责边界。三个方向 DOM 与 fixture 相同，仅材质、字号、间距、圆角、控件、深度不同。

当前缺口30；基础采购需求30；MOQ100；MOQ调整70；建议采购100。展示30+70=100，AI只解释，人工作最终决定。没有真实计算、AI调用、审核记录或草稿生成。保留原技术原型入口，不连接 runtime。

## C1 — Apple Clean / 明净

连续白色主表面，以细分隔表达两栏，右侧不另起卡片。中性灰画布、几乎无阴影、蓝色操作、平整数量关系带。28px中文标题与18px分区标题；正文14px。控件9px、主表面22px、弹窗22px圆角。

层级依靠文字重量、对齐和留白；结果与依据并置，AI与人工区域共用同一平面。

优势：最安静，事实清晰，适合长时间阅读。取舍：空间深度最弱，Portfolio截图辨识度较克制。

## C2 — Apple Layered / 层叠

冷中性色画布 → 浅蓝灰工作区 → 内嵌的半透明导航 → 轻抬起的白色决策表面 → 聚焦弹窗。阴影只分配给工作区与决策平面，不逐条包卡。依据关系带下沉，右侧浮起，表达阅读到决定的层次。导航22px backdrop blur，弹窗背景12px blur；正文保持实色。

27px中等重量标题，正文14px；控件11px、次级表面18px、主表面26px、弹窗26px圆角。蓝色聚焦主要操作，数字保持64px，与另外两案一致。

优势：最接近现代 macOS 的材质与空间语言；整体区分明确。取舍：依赖细腻层次，压缩截图或低质量投屏会损失部分材质。

## C3 — Apple Premium / 雅致

深石墨导航、暖中性画布、连续米白工作区与浅暖灰决策区域。低饱和蓝灰操作，较宽横向内距，30px轻一些的中文标题、15px解释正文；数字450字重。控件7px、次级表面12px、主表面18px、弹窗18px圆角。

层级通过深色导航框架、温润内容平面与从容文字节奏建立，保持企业工作区的信息密度。

优势：画面最具编辑感，适合Portfolio与真实产品叙事。取舍：更像专业桌面软件，明亮轻盈感弱于C1/C2；深色导航不是完整dark mode。

## 系统实现

Tailwind CSS v4 负责reset、font theme及shadcn utility基础；局部语义CSS变量统一三个系统的color/spacing/radius/shadow/motion。未采用Card网格。shadcn只提供Button、Tabs、Dialog、Collapsible、Tooltip、Switch、Input、Textarea交互原语，视觉均由本页token重写。

Noto Sans SC Variable中文 + Manrope Variable数字，自托管；主要数字64px，移动56px；正文14–15px，辅助12–13px，英文SIMULATED11px。图标Lucide，1.65stroke，17px为主。数据使用tabular numerals。

控件44px高；分段44px命中高度；Switch26px视觉轨道配44px命中区；键盘焦点3px。输入边界独立token满足3:1以上。深色导航使用浅色焦点。弹窗继承所属variant，不回落默认shadcn样式。

## Motion / responsive

同一页面只做一次4px轻微进入，180/220/200ms分别对应C1/C2/C3；按钮150ms微位移和颜色；弹窗0.985scale，disclosure高度过渡。无计数计算假象、bounce或parallax。减少动态偏好直接显示终态、保留文本状态与焦点。

桌面两栏比例1.27:1共享，760px以下按同样信息顺序堆叠。1280与1440下完整presentation画面高度分别约780/780/797px；移动需正常纵向滚动，无横向溢出。外部评审工具栏不属于产品画面。

## Review / delivery

完成 Concept Design → Impeccable dual-agent Critique → Revision → Impeccable Audit → Revision → final verification。初稿和最终截图、对比度记录及完整评审在design-reviews/apple/。

推荐C2作为本轮整体Apple材质语言的优先候选；C3是偏Portfolio编辑感的候选。这是设计建议，不是最终选择。STOP FOR HUMAN VISUAL SELECTION，不自动进入完整交互开发。
