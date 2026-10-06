import { ArrowRight } from "lucide-react";
import { scenario, recommendationPath } from "./fixture";
import { AppShell } from "./shell";

export function EntryPage() {
  return (
    <AppShell>
      <main className="workspace-entry">
        <div className="page-heading">
          <div>
            <h1>采购决策工作台</h1>
            <p>查看当前需要人工处理的采购建议</p>
          </div>
        </div>
        <dl className="overview-strip" aria-label="当前演示概况">
          <div>
            <dt>待处理建议</dt>
            <dd>1</dd>
          </div>
          <div>
            <dt>当前场景</dt>
            <dd>SIMULATED</dd>
          </div>
          <div>
            <dt>决策方式</dt>
            <dd>人工审核</dd>
          </div>
        </dl>
        <section className="pending-section" aria-labelledby="pending-title">
          <div className="section-heading">
            <h2 id="pending-title">
              待审核采购建议 <span className="pending-count">· 1</span>
            </h2>
          </div>
          <article aria-label={`${scenario.display_name}采购建议`}>
            <a
              className="task-row"
              href={recommendationPath}
              aria-label={`查看建议：${scenario.display_name}，${scenario.material_code}，待人工审核`}
            >
              <div className="task-identity">
                <h3>{scenario.display_name}</h3>
                <p>
                  <span>物料编码：{scenario.material_code}</span>
                  <span>模拟展示名称</span>
                </p>
              </div>
              <dl className="task-quantities">
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
                  <dt>MOQ 调整</dt>
                  <dd>+{scenario.adjustment}</dd>
                </div>
              </dl>
              <span className="status">
                <span />
                待人工审核
              </span>
              <span className="task-affordance">
                查看建议 <ArrowRight aria-hidden="true" />
              </span>
            </a>
          </article>
        </section>
        <p className="entry-boundary">
          固定模拟场景 · 无实时 AI 请求 · 不保存业务状态
        </p>
      </main>
    </AppShell>
  );
}
