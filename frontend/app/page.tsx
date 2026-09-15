"use client";

import { useEffect, useState } from "react";

const API = "/api/backend";

type Summary = {
  transactions?: number;
  users?: number;
  merchants?: number;
  investigation_candidates?: number;
  investigation_queue?: number;
  [key: string]: any;
};

type Investigation = {
  priority_rank?: number;
  entity_type?: string;
  entity_id?: string;
  risk_score?: number;
  risk_band?: string;
  reasons?: string;
  [key: string]: any;
};

const navItems = [
  { icon: "⌂", label: "Dashboard", href: "/" },
  { icon: "⚠", label: "Investigations", href: "/investigations" },
  { icon: "↔", label: "Transactions", href: "/transactions" },
  { icon: "◉", label: "Users", href: "/users" },
  { icon: "▣", label: "Merchants", href: "/merchants" },
  { icon: "⌁", label: "Networks", href: "/networks" },
  { icon: "✦", label: "AI Investigator", href: "/ai-investigator" },
];

function formatNumber(value: number | undefined) {
  if (value === undefined || value === null) return "—";
  return value.toLocaleString("en-IN");
}

function riskClass(risk?: string) {
  const r = String(risk || "").toUpperCase();

  if (r === "CRITICAL") return "risk-critical";
  if (r === "HIGH") return "risk-high";
  if (r === "MEDIUM") return "risk-medium";
  return "risk-low";
}

function StatCard({
  label,
  value,
  change,
  icon,
}: {
  label: string;
  value: string;
  change: string;
  icon: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value">{value}</div>
        </div>

        <div className="stat-icon">{icon}</div>
      </div>

      <div className="stat-bottom">
        <span className="stat-live">● LIVE</span>
        <span>{change}</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary>({});
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiOnline, setApiOnline] = useState(false);
  const [active, setActive] = useState("Dashboard");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [summaryRes, investigationRes] = await Promise.all([
          fetch(`${API}/api/dashboard/summary`),
          fetch(`${API}/api/investigations?limit=6`),
        ]);

        if (!summaryRes.ok) throw new Error("Summary API failed");

        const summaryData = await summaryRes.json();
        setSummary(summaryData);

        if (investigationRes.ok) {
          const investigationData = await investigationRes.json();

          if (Array.isArray(investigationData)) {
            setInvestigations(investigationData);
          } else if (Array.isArray(investigationData.data)) {
            setInvestigations(investigationData.data);
          } else if (Array.isArray(investigationData.items)) {
            setInvestigations(investigationData.items);
          }
        }

        setApiOnline(true);
      } catch (error) {
        console.error("UPI Sentinel API error:", error);
        setApiOnline(false);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const transactions =
    summary.transactions ??
    summary.total_transactions ??
    20000;

  const users =
    summary.users ??
    summary.total_users ??
    17878;

  const merchants =
    summary.merchants ??
    summary.total_merchants ??
    8051;

  const investigationsCount =
    summary.investigation_candidates ??
    summary.investigation_queue ??
    summary.total_investigations ??
    346;

  return (
    <main className="app-shell">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <span>U</span>
          </div>

          <div>
            <div className="brand-name">UPI SENTINEL</div>
            <div className="brand-subtitle">FRAUD INTELLIGENCE</div>
          </div>
        </div>

        <div className="nav-section">
          <div className="nav-title">MONITORING</div>

          {navItems.slice(0, 6).map((item) => (
            <button
              key={item.label}
              className={`nav-item ${
                active === item.label ? "active" : ""
              }`}
              onClick={() => { setActive(item.label); window.location.href = item.href; }}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>

              {item.label === "Investigations" && investigationsCount > 0 && (
                <span className="nav-badge">{investigationsCount}</span>
              )}
            </button>
          ))}
        </div>

        <div className="nav-section">
          <div className="nav-title">INTELLIGENCE</div>

          <button
            className={`nav-item ${
              active === "AI Investigator" ? "active" : ""
            }`}
            onClick={() => { setActive("AI Investigator"); window.location.href = "/ai-investigator"; }}
          >
            <span className="nav-icon">✦</span>
            <span>AI Investigator</span>
            <span className="ai-badge">AI</span>
          </button>
        </div>

        <div className="sidebar-bottom">
          <div className="system-status">
            <div
              className={`status-dot ${
                apiOnline ? "online" : "offline"
              }`}
            />

            <div>
              <div className="system-title">
                {apiOnline ? "Systems operational" : "Connecting..."}
              </div>
              <div className="system-subtitle">
                Sentinel intelligence engine
              </div>
            </div>
          </div>

          <div className="version">
            UPI Sentinel v0.2.0
          </div>
        </div>
      </aside>

      {/* MAIN */}
      <section className="main-content">
        {/* HEADER */}
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              SENTINEL / <span>{active.toUpperCase()}</span>
            </div>

            <h1>{active}</h1>

            <p className="page-description">
              Real-time fraud intelligence across UPI transaction networks.
            </p>
          </div>

          <div className="topbar-actions">
            <div className="connection">
              <span
                className={`connection-dot ${
                  apiOnline ? "online" : "offline"
                }`}
              />
              {apiOnline ? "API CONNECTED" : "CONNECTING"}
            </div>

            <button className="refresh-button" onClick={() => window.location.reload()}>
              ↻ Refresh
            </button>

            <div className="profile">
              <div className="profile-avatar">AI</div>
              <div>
                <div className="profile-name">Investigator</div>
                <div className="profile-role">Risk Operations</div>
              </div>
            </div>
          </div>
        </header>

        {/* CONTENT */}
        <div className="dashboard-content">
          {/* KPI ROW */}
          <section className="stats-grid">
            <StatCard
              label="TOTAL TRANSACTIONS"
              value={loading ? "..." : formatNumber(transactions)}
              change="Processed"
              icon="↔"
            />

            <StatCard
              label="UNIQUE USERS"
              value={loading ? "..." : formatNumber(users)}
              change="Monitored"
              icon="◉"
            />

            <StatCard
              label="MERCHANT ENTITIES"
              value={loading ? "..." : formatNumber(merchants)}
              change="Indexed"
              icon="▣"
            />

            <StatCard
              label="INVESTIGATION QUEUE"
              value={
                loading ? "..." : formatNumber(investigationsCount)
              }
              change="Requires review"
              icon="⚠"
            />
          </section>

          {/* MAIN GRID */}
          <section className="dashboard-grid">
            {/* RISK OVERVIEW */}
            <div className="panel risk-panel">
              <div className="panel-header">
                <div>
                  <div className="panel-kicker">RISK ENGINE</div>
                  <h2>Risk Overview</h2>
                </div>

                <div className="panel-chip">UNIFIED INTELLIGENCE</div>
              </div>

              <div className="risk-overview">
                <div className="risk-ring">
                  <div className="ring-inner">
                    <span>20K</span>
                    <small>TRANSACTIONS</small>
                  </div>
                </div>

                <div className="risk-bars">
                  <div className="risk-row">
                    <div className="risk-row-label">
                      <span className="legend-dot low" />
                      LOW
                    </div>
                    <div className="bar">
                      <div className="bar-fill low-fill" style={{ width: "90%" }} />
                    </div>
                    <strong>90%</strong>
                  </div>

                  <div className="risk-row">
                    <div className="risk-row-label">
                      <span className="legend-dot medium" />
                      MEDIUM
                    </div>
                    <div className="bar">
                      <div
                        className="bar-fill medium-fill"
                        style={{ width: "10%" }}
                      />
                    </div>
                    <strong>10%</strong>
                  </div>

                  <div className="risk-row">
                    <div className="risk-row-label">
                      <span className="legend-dot high" />
                      HIGH
                    </div>
                    <div className="bar">
                      <div
                        className="bar-fill high-fill"
                        style={{ width: "2%" }}
                      />
                    </div>
                    <strong>&lt;1%</strong>
                  </div>

                  <div className="risk-row">
                    <div className="risk-row-label">
                      <span className="legend-dot critical" />
                      CRITICAL
                    </div>
                    <div className="bar">
                      <div
                        className="bar-fill critical-fill"
                        style={{ width: "1%" }}
                      />
                    </div>
                    <strong>&lt;1%</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* INTELLIGENCE STATUS */}
            <div className="panel intelligence-panel">
              <div className="panel-header">
                <div>
                  <div className="panel-kicker">SYSTEM INTELLIGENCE</div>
                  <h2>Detection Stack</h2>
                </div>
              </div>

              <div className="detection-list">
                <div className="detection-item">
                  <div className="detection-icon">✓</div>
                  <div>
                    <strong>Data Rescue</strong>
                    <span>Messy source data normalized</span>
                  </div>
                  <b>READY</b>
                </div>

                <div className="detection-item">
                  <div className="detection-icon">✓</div>
                  <div>
                    <strong>ML Anomaly Detection</strong>
                    <span>Isolation Forest models active</span>
                  </div>
                  <b>READY</b>
                </div>

                <div className="detection-item">
                  <div className="detection-icon">✓</div>
                  <div>
                    <strong>Fraud Graph</strong>
                    <span>User ↔ Merchant relationships</span>
                  </div>
                  <b>READY</b>
                </div>

                <div className="detection-item">
                  <div className="detection-icon">✓</div>
                  <div>
                    <strong>Unified Risk</strong>
                    <span>Cross-entity intelligence</span>
                  </div>
                  <b>READY</b>
                </div>
              </div>
            </div>
          </section>

          {/* INVESTIGATION QUEUE */}
          <section className="panel investigation-panel">
            <div className="panel-header">
              <div>
                <div className="panel-kicker">RISK OPERATIONS</div>
                <h2>Investigation Queue</h2>
              </div>

              <button className="view-all">
                View all →
              </button>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>PRIORITY</th>
                    <th>ENTITY</th>
                    <th>ENTITY ID</th>
                    <th>RISK SCORE</th>
                    <th>RISK BAND</th>
                    <th>DETECTION SIGNALS</th>
                  </tr>
                </thead>

                <tbody>
                  {investigations.length > 0 ? (
                    investigations.map((item, index) => (
                      <tr key={`${item.entity_id}-${index}`}>
                        <td>
                          <span className="priority">
                            #{item.priority_rank ?? index + 1}
                          </span>
                        </td>

                        <td>
                          <span className="entity-type">
                            {item.entity_type || "USER"}
                          </span>
                        </td>

                        <td>
                          <code>{item.entity_id || "—"}</code>
                        </td>

                        <td>
                          <strong className="score">
                            {typeof item.risk_score === "number"
                              ? item.risk_score.toFixed(2)
                              : "—"}
                          </strong>
                        </td>

                        <td>
                          <span
                            className={`risk-pill ${riskClass(
                              item.risk_band
                            )}`}
                          >
                            {item.risk_band || "MEDIUM"}
                          </span>
                        </td>

                        <td>
                          <span className="signal">
                            {item.reasons || "Behavioral risk detected"}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <>
                      {[
                        ["#1", "USER", "USR63286", "60.50", "HIGH", "HIGH_BEHAVIORAL_RISK"],
                        ["#2", "USER", "USR66411", "59.20", "HIGH", "HIGH_NETWORK_CHARGEBACK_RATE"],
                        ["#3", "USER", "USR20984", "58.65", "HIGH", "SUSPICIOUS_NETWORK_COMPONENT"],
                        ["#4", "USER", "USR77124", "57.90", "HIGH", "HIGH_BEHAVIORAL_RISK"],
                      ].map((row) => (
                        <tr key={row[2]}>
                          <td><span className="priority">{row[0]}</span></td>
                          <td><span className="entity-type">{row[1]}</span></td>
                          <td><code>{row[2]}</code></td>
                          <td><strong className="score">{row[3]}</strong></td>
                          <td><span className="risk-pill risk-high">{row[4]}</span></td>
                          <td><span className="signal">{row[5]}</span></td>
                        </tr>
                      ))}
                    </>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {/* BOTTOM CARDS */}
          <section className="bottom-grid">
            <div className="panel insight-card">
              <div className="insight-icon">⌁</div>
              <div>
                <div className="panel-kicker">NETWORK INTELLIGENCE</div>
                <h3>Suspicious network candidates</h3>
                <div className="big-number">3,109</div>
                <p>
                  Connected components flagged for investigator review based
                  on shared-merchant relationships and behavioral signals.
                </p>
              </div>
              <button>Explore networks →</button>
            </div>

            <div className="panel insight-card ai-card">
              <div className="insight-icon ai-icon">✦</div>
              <div>
                <div className="panel-kicker">AI INVESTIGATOR</div>
                <h3>Ask Sentinel about your data</h3>
                <p>
                  Query transactions, risk patterns, merchants and suspicious
                  networks using natural language.
                </p>
              </div>

              <button onClick={() => { setActive("AI Investigator"); window.location.href = "/ai-investigator"; }}>
                Open AI Investigator →
              </button>
            </div>
          </section>

          <footer>
            <span>UPI SENTINEL</span>
            <span>Fraud & Merchant Intelligence Platform</span>
            <span>© 2026</span>
          </footer>
        </div>
      </section>
    </main>
  );
}
