# Product

面向求职Portfolio演示的供应链AI Copilot，中文优先。一次固定SIMULATED采购场景，展示确定性事实、预置解释、显式人工批准与临时草稿。用户成功条件是区分三种authority并完成一次批准路径。

当前唯一范围与交付边界见README；视觉C3.2冻结见DESIGN。不是生产采购系统，不连接runtime或服务。

系统入口现在为采购决策工作台，仅发现任务并进入既有详情。物料M2为既有fixture身份；装配连接件为SIMULATED display_name，不成为业务事实。

Workspace Shell v1.2仅强化发现任务→进入同一任务的连续性。一个真实演示模块、一个固定模拟任务；概况条不代表生产KPI。共享框架不引入新的业务能力。
