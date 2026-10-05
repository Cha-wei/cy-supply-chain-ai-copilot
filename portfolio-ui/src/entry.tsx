import { ArrowRight } from "lucide-react";
import { scenario, recommendationPath } from "./fixture";

// Task discovery only. No approval, evidence expansion or business state here.
export function EntryPage() {
  return (
    <section className="design-stage material entry-page" data-variant="C32">
      <div className="workspace">
        <header className="workspace-nav">
          <div className="brand">
            <span className="brand-mark">CY</span>
            <span>供应链 AI Copilot</span>
          </div>
          <div className="nav-end">
            <span className="simulation">
              模拟演示 <span>SIMULATED Portfolio POC</span>
            </span>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <h1>采购决策工作台</h1>
              <p>查看当前采购建议，由人工决定下一步。</p>
            </div>
          </div>
          <section aria-labelledby="pending-title" className="pending-section">
            <div className="section-heading">
              <h2 id="pending-title">
                待审核采购建议 <span className="pending-count">· 1</span>
              </h2>
              <span className="role-label">SIMULATED Portfolio POC</span>
            </div>
            <article
              className="recommendation-surface entry-recommendation"
              aria-label={`${scenario.display_name}采购建议`}
            >
              <div className="entry-material">
                <div>
                  <h3>{scenario.display_name}</h3>
                  <p className="material-context">
                    <span className="material-identity">
                      物料编码：{scenario.material_code}
                    </span>
                    <span className="display-label-note">模拟展示名称</span>
                  </p>
                </div>
                <span className="status">
                  <span />
                  待人工审核
                </span>
              </div>
              <dl className="entry-facts">
                <div>
                  <dt>当前缺口</dt>
                  <dd>
                    {scenario.shortage}
                    <span>件</span>
                  </dd>
                </div>
                <div>
                  <dt>建议采购量</dt>
                  <dd>
                    {scenario.recommended}
                    <span>件</span>
                  </dd>
                </div>
                <div>
                  <dt>调整原因</dt>
                  <dd className="entry-reason">
                    MOQ
                    <span>
                      增加 {scenario.adjustment} 件，满足最低起订量{" "}
                      {scenario.moq} 件
                    </span>
                  </dd>
                </div>
              </dl>
              <div className="entry-task-action">
                <p>查看依据与预置解释，再由人工审核。</p>
                <a className="system-button primary" href={recommendationPath}>
                  查看建议 <ArrowRight />
                </a>
              </div>
            </article>
          </section>
          <p className="entry-boundary">
            固定模拟场景 · 无实时 AI 请求 · 不保存业务状态
          </p>
        </main>
        <footer className="workspace-footer">
          <span>
            确定性计算 <ArrowRight /> AI 解释 <ArrowRight /> 人工决策
          </span>
          <span>presentation-only · 无 ERP 写入 / 采购订单 / 生产执行</span>
        </footer>
      </div>
    </section>
  );
}
