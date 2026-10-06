import type { ReactNode } from "react";
import { ArrowLeft, ArrowRight, ClipboardList, Info } from "lucide-react";
import { scenario } from "./fixture";

export function AppShell({
  children,
  detail = false,
  demoState,
  onBoundary,
}: {
  children: ReactNode;
  detail?: boolean;
  demoState?: string;
  onBoundary?: (target: HTMLElement) => void;
}) {
  return (
    <section
      className="design-stage material app-shell"
      data-variant="C32"
      data-demo-state={demoState}
    >
      <div className="workspace shell-frame">
        <aside className="app-rail" aria-label="应用导航栏">
          <span className="rail-brand" aria-label="CY 供应链 AI Copilot">
            CY
          </span>
          <nav aria-label="应用模块">
            <a
              href="/"
              className="module-link"
              aria-current={detail ? "true" : "page"}
            >
              <ClipboardList aria-hidden="true" />
              <span>采购决策</span>
            </a>
          </nav>
          <span className="rail-simulation">SIMULATED</span>
        </aside>
        <div className="shell-content">
          <header className="context-bar">
            {detail ? (
              <div className="context-path">
                <a href="/" aria-label="返回采购决策工作台，重新演示">
                  <ArrowLeft aria-hidden="true" />
                  返回工作台
                </a>
                <span className="context-material">
                  /　{scenario.display_name} · {scenario.material_code}
                </span>
              </div>
            ) : (
              <span>采购决策工作台</span>
            )}
            <span className="context-simulation">
              SIMULATED<span> Portfolio POC</span>
            </span>
            {onBoundary && (
              <button
                className="system-button icon"
                aria-label="查看展示边界"
                onClick={(event) => onBoundary(event.currentTarget)}
              >
                <Info />
              </button>
            )}
          </header>
          {children}
          <footer className="workspace-footer">
            <span>
              确定性计算 <ArrowRight /> AI 解释 <ArrowRight /> 人工决策
            </span>
            <span>presentation-only · 无 ERP 写入 / 采购订单 / 生产执行</span>
          </footer>
        </div>
      </div>
    </section>
  );
}
