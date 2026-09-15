"use client";

import { useEffect, useMemo, useState } from "react";

const API = "/api/backend";

type Investigation = {
  priority_rank: number;
  entity_type: string;
  entity_id: string;
  risk_score: number;
  risk_band: string;
  reasons: string;
};

function riskClass(band: string) {
  switch (band) {
    case "CRITICAL":
      return "risk-critical";
    case "HIGH":
      return "risk-high";
    case "MEDIUM":
      return "risk-medium";
    default:
      return "risk-low";
  }
}

function formatReason(reason: string) {
  return reason
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function InvestigationsPage() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [entityFilter, setEntityFilter] = useState("ALL");
  const [selected, setSelected] = useState<Investigation | null>(null);

  useEffect(() => {
    async function loadInvestigations() {
      try {
        setLoading(true);

        const response = await fetch(
          `${API}/investigations?limit=346`,
          { cache: "no-store" }
        );

        if (!response.ok) {
          throw new Error("Investigation API failed");
        }

        const data = await response.json();
        setInvestigations(data.investigations || []);
      } catch (err) {
        console.error(err);
        setError("Unable to load investigation queue.");
      } finally {
        setLoading(false);
      }
    }

    loadInvestigations();
  }, []);

  const filteredInvestigations = useMemo(() => {
    const query = search.toLowerCase().trim();

    return investigations.filter((item) => {
      const matchesSearch =
        !query ||
        item.entity_id.toLowerCase().includes(query) ||
        item.entity_type.toLowerCase().includes(query) ||
        item.reasons.toLowerCase().includes(query);

      const matchesRisk =
        riskFilter === "ALL" || item.risk_band === riskFilter;

      const matchesEntity =
        entityFilter === "ALL" || item.entity_type === entityFilter;

      return matchesSearch && matchesRisk && matchesEntity;
    });
  }, [investigations, search, riskFilter, entityFilter]);

  const highCount = investigations.filter(
    (item) => item.risk_band === "HIGH"
  ).length;

  const criticalCount = investigations.filter(
    (item) => item.risk_band === "CRITICAL"
  ).length;

  return (
    <main className="dashboard-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">U</div>
          <div>
            <div className="brand-name">UPI Sentinel</div>
            <div className="brand-subtitle">Fraud Intelligence</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <a href="/" className="nav-item">
            <span>⌂</span>
            Dashboard
          </a>

          <a href="/investigations" className="nav-item active">
            <span>⌕</span>
            Investigations
          </a>

          <a href="/" className="nav-item">
            <span>⇄</span>
            Transactions
          </a>

          <a href="/" className="nav-item">
            <span>◎</span>
            Users
          </a>

          <a href="/" className="nav-item">
            <span>▣</span>
            Merchants
          </a>

          <a href="/" className="nav-item">
            <span>⌘</span>
            Networks
          </a>

          <div className="nav-section-title">INTELLIGENCE</div>

          <a href="/" className="nav-item">
            <span>✦</span>
            AI Investigator
          </a>
        </nav>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-dot" />
            Intelligence Engine Online
          </div>
          <div className="version">UPI Sentinel v0.2.0</div>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">FRAUD OPERATIONS</div>
            <h1>Investigation Center</h1>
            <p>
              Prioritized entities requiring investigator review.
            </p>
          </div>

          <div className="topbar-status">
            <span className="status-dot" />
            API Connected
          </div>
        </header>

        <section className="stats-grid investigation-stats">
          <div className="stat-card">
            <div className="stat-label">TOTAL CANDIDATES</div>
            <div className="stat-value">{investigations.length}</div>
            <div className="stat-meta">Prioritized investigation queue</div>
          </div>

          <div className="stat-card">
            <div className="stat-label">HIGH RISK</div>
            <div className="stat-value">{highCount}</div>
            <div className="stat-meta">Entities requiring review</div>
          </div>

          <div className="stat-card">
            <div className="stat-label">CRITICAL</div>
            <div className="stat-value">{criticalCount}</div>
            <div className="stat-meta">Highest-priority entities</div>
          </div>

          <div className="stat-card">
            <div className="stat-label">VISIBLE RESULTS</div>
            <div className="stat-value">
              {filteredInvestigations.length}
            </div>
            <div className="stat-meta">After active filters</div>
          </div>
        </section>

        <section className="panel investigation-panel">
          <div className="panel-header">
            <div>
              <div className="panel-kicker">INVESTIGATION QUEUE</div>
              <h2>Suspicious entities</h2>
            </div>

            <div className="queue-description">
              Risk scores combine behavioral, network and anomaly signals.
            </div>
          </div>

          <div className="filter-bar">
            <div className="search-box">
              <span>⌕</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search entity, ID or reason..."
              />
            </div>

            <select
              value={entityFilter}
              onChange={(event) => setEntityFilter(event.target.value)}
            >
              <option value="ALL">All entities</option>
              <option value="USER">Users</option>
              <option value="MERCHANT">Merchants</option>
              <option value="TRANSACTION">Transactions</option>
            </select>

            <select
              value={riskFilter}
              onChange={(event) => setRiskFilter(event.target.value)}
            >
              <option value="ALL">All risk levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          {loading && (
            <div className="empty-state">
              Loading investigation intelligence...
            </div>
          )}

          {error && (
            <div className="empty-state error-state">
              {error}
            </div>
          )}

          {!loading && !error && (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>PRIORITY</th>
                    <th>ENTITY</th>
                    <th>ENTITY ID</th>
                    <th>RISK SCORE</th>
                    <th>RISK BAND</th>
                    <th>WHY FLAGGED</th>
                    <th />
                  </tr>
                </thead>

                <tbody>
                  {filteredInvestigations.map((item) => (
                    <tr
                      key={`${item.entity_type}-${item.entity_id}`}
                      onClick={() => setSelected(item)}
                      className="investigation-row"
                    >
                      <td>
                        <span className="priority-number">
                          #{item.priority_rank}
                        </span>
                      </td>

                      <td>
                        <span className="entity-type">
                          {item.entity_type}
                        </span>
                      </td>

                      <td>
                        <span className="entity-id">
                          {item.entity_id}
                        </span>
                      </td>

                      <td>
                        <div className="risk-score-cell">
                          <strong>
                            {item.risk_score.toFixed(2)}
                          </strong>
                          <div className="mini-risk-bar">
                            <span
                              style={{
                                width: `${Math.min(
                                  item.risk_score,
                                  100
                                )}%`,
                              }}
                            />
                          </div>
                        </div>
                      </td>

                      <td>
                        <span
                          className={`risk-pill ${riskClass(
                            item.risk_band
                          )}`}
                        >
                          {item.risk_band}
                        </span>
                      </td>

                      <td>
                        <div className="reason-list">
                          {item.reasons
                            .split("|")
                            .slice(0, 2)
                            .map((reason) => (
                              <span key={reason}>
                                {formatReason(reason)}
                              </span>
                            ))}
                        </div>
                      </td>

                      <td>
                        <button
                          className="view-button"
                          onClick={(event) => {
                            event.stopPropagation();
                            setSelected(item);
                          }}
                        >
                          View →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {filteredInvestigations.length === 0 && (
                <div className="empty-state">
                  No investigation candidates match the current filters.
                </div>
              )}
            </div>
          )}
        </section>
      </section>

      {selected && (
        <div
          className="drawer-backdrop"
          onClick={() => setSelected(null)}
        >
          <aside
            className="investigation-drawer"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="drawer-header">
              <div>
                <div className="panel-kicker">
                  INVESTIGATION CASE
                </div>

                <h2>{selected.entity_id}</h2>

                <div className="drawer-entity-type">
                  {selected.entity_type}
                </div>
              </div>

              <button
                className="close-button"
                onClick={() => setSelected(null)}
              >
                ×
              </button>
            </div>

            <div className="drawer-risk">
              <div>
                <div className="drawer-label">UNIFIED RISK SCORE</div>
                <div className="drawer-score">
                  {selected.risk_score.toFixed(2)}
                </div>
              </div>

              <span
                className={`risk-pill large ${riskClass(
                  selected.risk_band
                )}`}
              >
                {selected.risk_band}
              </span>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">
                WHY THIS ENTITY WAS FLAGGED
              </div>

              <div className="drawer-reasons">
                {selected.reasons.split("|").map((reason) => (
                  <div className="drawer-reason" key={reason}>
                    <span className="reason-icon">!</span>
                    <span>{formatReason(reason)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">
                INVESTIGATION SIGNALS
              </div>

              <div className="signal-card">
                <div className="signal-icon">◈</div>
                <div>
                  <strong>Behavioral Intelligence</strong>
                  <p>
                    Entity exhibits elevated behavioral risk
                    signals relative to the analytical population.
                  </p>
                </div>
              </div>

              <div className="signal-card">
                <div className="signal-icon">⌘</div>
                <div>
                  <strong>Network Intelligence</strong>
                  <p>
                    Entity is associated with a suspicious
                    user-merchant network component.
                  </p>
                </div>
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">
                RECOMMENDED ACTION
              </div>

              <div className="recommendation">
                <div className="recommendation-title">
                  Review before escalation
                </div>

                <p>
                  Examine KYC quality, transaction behavior,
                  chargeback history and linked network entities
                  before making a final determination.
                </p>
              </div>
            </div>

            <div className="drawer-footer">
              <span>
                Risk score is an investigative prioritization
                signal, not a confirmed fraud verdict.
              </span>
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}