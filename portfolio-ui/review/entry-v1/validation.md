# Workspace Entry v1 — 验证与评审

基线：已获Human接受的Interaction v1，commit ccd0bf1。当前增量仅补任务入口、路由和物料展示上下文；C3.2仍FROZEN。

## 身份与边界

material_code M2从既有test_hitl_review → test_supplier_risk_input → test_shortage_calculation.DEMAND引用链恢复；自动测试直接核对源fixture。装配连接件为SIMULATED display_name，两页明确标注模拟展示名称；不进入state reducer、身份判断、provenance或采购计算，没有新增canonical字段。

`/`发现一条任务；`/procurement/M2`进入原详情。路径仅映射单一演示fixture，未知路径不映射到其他物料。原生同源链接导航，无路由依赖、API或backend；可直接访问/刷新深链（当前Vite SPA fallback）。部署时应配置等价静态fallback，未新增部署服务。

入口无Approve/Reject/Override、完整Evidence或AI展开。原Interaction v1的reducer未改，30/30/100/70/100和批准→草稿路径不变。普通链接打开新页面，刷新/重置清除演示状态；没有持久化业务状态。

## 验证

- Playwright30/30 PASS：原21项保留断言，仅更新详情URL；新增9项（三视口各3项）覆盖身份来源、首页1条建议、物料上下文、查看建议→既有主路径、未知ID与深链刷新。
- 原keyboard/Escape/reset/reduced motion/contrast/font fallback断言继续通过。
- TypeScript/Vite build PASS；Impeccable detector []。
- 无fetch/XHR/非GET业务请求、无localStorage/sessionStorage的完整入口→草稿路径检查PASS。
- workspace桌面780px，detail796.72px；1440/1280/390均无水平溢出。mobile入口约909.72px，可纵向滚动；截图与测量在同目录。

独立只读review直接检查增量、身份引用链、测试、截图与已有测试记录，未发现actionable findings；reviewer未代替执行测试。review后的唯一视觉修订为入口辅助文案缩短及边界说明间距，已重新截图与全量测试。

未做物理触屏或完整辅助技术审计。无runtime/ERP/PO或生产能力主张，未改Python/canonical业务设计，未merge main。

READY_FOR_REVIEW / STOP FOR HUMAN ENTRY-PAGE REVIEW。
