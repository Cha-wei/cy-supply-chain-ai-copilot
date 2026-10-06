# Workspace Shell v1.2 — validation

2026-10-06。增量基线：07d495d（Workspace Entry v1）；C3.2与Interaction v1保持。

## 实现与视觉审查

- 桌面96px共享导航栏，仅采购决策；顶部改为上下文栏。
- 入口连续概况条、116px任务行；同一M2身份与模拟展示名称。
- 移动端紧凑顶栏，无虚构菜单。暖石任务表面、冷灰概况条、Noto Sans SC与冻结控制语言延续。
- 1440/1280/390的工作台和详情截图均来自当前4190预览；文件见同目录。390为完整页面截图。
- Impeccable有界视觉审查：入口层级清楚、任务表面已压缩、主从页框架连续；未更改详情正文。源代码detect执行结束，无输出；不将其视为视觉质量的单独证明。

## 验证

- npm run build：通过。
- npm test：39 passed，桌面1440×800、1280×800、390×844。
- 覆盖单模块/无假菜单、两页rail位置与宽度一致、任务行100–130px、整行点击和Enter、焦点、3px悬停、reduced motion、实际Noto渲染、未知ID、刷新/重置及既有批准→草稿路径。
- 初次新增布局测试在入场动画中测量，出现小于1px的位置误差；改为等待动画finished后测量，同样精确比较，不放宽断言。
- 独立只读review：未发现可操作的实现或边界问题；额外检查320/761/900/1101宽度，两路由无溢出。review时三个测试失败已由上述最终39项通过解决。
- 无新增依赖、API、runtime、存储或业务规则；src/state.ts不变。

STOP FOR HUMAN WORKSPACE SHELL REVIEW。未merge main。
