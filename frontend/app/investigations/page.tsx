"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

const API = "/api/backend";

type Investigation = {
  priority_rank?: number;
  entity_type?: string;
  entity_id?: string;
  risk_score?: number;
  risk_band?: string;
  reasons?: string;
  [key: string]: unknown;
};

const navItems = [
  { icon: "⌂", label: "Dashboard", href: "/" },
  { icon: "⚠", label: "Investigations", href: "/investigations" },
  { icon: "↔", label: "Transactions", href: "/transactions" },
  { icon: "◉", label: "Users", href: "/users" },
  { icon: "▣", label: "Merchants", href: "/merchants" },
  { icon: "⌁", label: "Networks", href: "/networks" },
];

function formatNumber(value?: number) {
  if (value === undefined || value === null || !Number.isFinite(value)) return "—";
  return value.toLocaleString("en-IN");
}

function formatScore(value?: number) {
  if (value === undefined || value === null || !Number.isFinite(value)) return "—";
  return value.toFixed(2);
}

function riskClass(risk?: string) {
  const value = String(risk || "").toUpperCase();
  if (value === "CRITICAL") return "risk-critical";
  if (value === "HIGH") return "risk-high";
  if (value === "MEDIUM") return "risk-medium";
  return "risk-low";
}

function formatReason(reason: string) {
  return reason
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function reasonList(value?: string) {
  if (!value) return [];
  return value.split("|").map((item) => item.trim()).filter(Boolean);
}

export default function InvestigationsPage() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [selected, setSelected] = useState<Investigation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");

  useEffect(() => {
    const controller = new AbortController();

    async function loadInvestigations() {
      try {
        const response = await fetch(`${API}/investigations?limit=500`, {
          cache: "no-store",
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Investigation API failed: ${response.status}`);
        }

        const data = await response.json();
        const items = Array.isArray(data)
          ? data
          : Array.isArray(data?.data)
            ? data.data
            : Array.isArray(data?.items)
              ? data.items
              : Array.isArray(data?.investigations)
                ? data.investigations
                : [];

        setInvestigations(items);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        console.error(err);
        setError("Unable to load the investigation queue.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadInvestigations();
    return () => controller.abort();
  }, []);

  const filteredInvestigations = useMemo(() => {
    const query = search.trim().toLowerCase();

    return investigations.filter((item) => {
      const searchable = [
        item.entity_type,
        item.entity_id,
        item.risk_band,
        item.reasons,
        item.priority_rank,
      ]
        .filter((value) => value !== undefined && value !== null)
        .join(" ")
        .toLowerCase();

      const matchesSearch = !query || searchable.includes(query);
      const matchesRisk =
        riskFilter === "ALL" ||
        String(item.risk_band || "").toUpperCase() === riskFilter;

      return matchesSearch && matchesRisk;
    });
  }, [investigations, search, riskFilter]);

  const criticalCount = investigations.filter(
    (item) => String(item.risk_band || "").toUpperCase() === "CRITICAL"
  ).length;

  const highCount = investigations.filter(
    (item) => String(item.risk_band || "").toUpperCase() === "HIGH"
  ).length;

  const mediumPlusCount = investigations.filter((item) => {
    const score = Number(item.risk_score);
    return Number.isFinite(score) && score >= 50;
  }).length;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><span>U</span></div>
          <div>
            <div className="brand-name">UPI SENTINEL</div>
            <div className="brand-subtitle">FRAUD INTELLIGENCE</div>
          </div>
        </div>

        <div className="nav-section">
          <div className="nav-title">MONITORING</div>
          {navItems.map((item) => (
            <Link
              key={item.label}
              className={`nav-item ${item.label === "Investigations" ? "active" : ""}`}
              href={item.href}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
              {item.label === "Investigations" && investigations.length > 0 && (
                <span className="nav-badge">{investigations.length}</span>
              )}
            </Link>
          ))}
        </div>

        <div className="nav-section">
          <div className="nav-title">INTELLIGENCE</div>
          <Link className="nav-item" href="/ai-investigator">
            <span className="nav-icon">✦</span>
            <span>AI Investigator</span>
            <span className="ai-badge">AI</span>
          </Link>
        </div>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className={`status-dot ${error ? "offline" : ""}`} />
            <div>
              <div className="system-title">
                {error ? "Intelligence engine issue" : "Intelligence engine online"}
              </div>
              <div className="system-subtitle">UPI Sentinel investigation layer</div>
            </div>
          </div>
          <div className="version">UPI Sentinel v0.2.0</div>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">SENTINEL / <span>INVESTIGATIONS</span></div>
            <h1>Investigation Center</h1>
            <p className="page-description">
              Prioritize users, transactions and merchants that warrant analyst review.
            </p>
          </div>
          <div className="topbar-actions">
            <div className="connection">
              <span className={`connection-dot ${error ? "offline" : ""}`} />
              {loading ? "LOADING QUEUE" : error ? "API ERROR" : "API CONNECTED"}
            </div>
          </div>
        </header>

        <div className="dashboard-content">
          <section className="stats-grid investigation-stats">
            <div className="stat-card">
              <div className="stat-top"><div>
                <div className="stat-label">INVESTIGATION QUEUE</div>
                <div className="stat-value">{formatNumber(investigations.length)}</div>
              </div><div className="stat-icon">⚠</div></div>
              <div className="stat-bottom"><span className="stat-live">● LIVE</span><span>Risk-scored candidates</span></div>
            </div>

            <div className="stat-card">
              <div className="stat-top"><div>
                <div className="stat-label">CRITICAL</div>
                <div className="stat-value">{formatNumber(criticalCount)}</div>
              </div><div className="stat-icon">!</div></div>
              <div className="stat-bottom"><span className="stat-live">● PRIORITY</span><span>Score above 75</span></div>
            </div>

            <div className="stat-card">
              <div className="stat-top"><div>
                <div className="stat-label">HIGH RISK</div>
                <div className="stat-value">{formatNumber(highCount)}</div>
              </div><div className="stat-icon">↑</div></div>
              <div className="stat-bottom"><span className="stat-live">● REVIEW</span><span>High-risk candidates</span></div>
            </div>

            <div className="stat-card">
              <div className="stat-top"><div>
                <div className="stat-label">MEDIUM+</div>
                <div className="stat-value">{formatNumber(mediumPlusCount)}</div>
              </div><div className="stat-icon">◎</div></div>
              <div className="stat-bottom"><span className="stat-live">● SIGNAL</span><span>Score 50 or above</span></div>
            </div>
          </section>

          <section className="panel investigation-panel">
            <div className="panel-header">
              <div>
                <div className="panel-kicker">RISK OPERATIONS</div>
                <h2>Priority Investigation Queue</h2>
              </div>
              <div className="queue-description">
                Candidates are ranked by unified risk score for analyst review.
              </div>
            </div>

            <div className="filter-bar">
              <div className="search-box">
                <span>⌕</span>
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search entity, ID, risk level or signal..."
                  aria-label="Search investigation queue"
                />
              </div>
              <select
                value={riskFilter}
                onChange={(event) => setRiskFilter(event.target.value)}
                aria-label="Filter by risk level"
              >
                <option value="ALL">All risk levels</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>

            {loading && <div className="empty-state">Loading investigation intelligence...</div>}
            {error && !loading && <div className="empty-state error-state">{error}</div>}

            {!loading && !error && filteredInvestigations.length === 0 && (
              <div className="empty-state">No investigation candidates match the current filters.</div>
            )}

            {!loading && !error && filteredInvestigations.length > 0 && (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>PRIORITY</th>
                      <th>ENTITY</th>
                      <th>ENTITY ID</th>
                      <th>RISK SCORE</th>
                      <th>RISK BAND</th>
                      <th>REASONS</th>
                      <th>ACTION</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredInvestigations.map((item, index) => {
                      const score = Number(item.risk_score);
                      const safeScore = Number.isFinite(score) ? score : 0;

                      return (
                        <tr
                          key={`${item.entity_type || "ENTITY"}-${item.entity_id || index}-${item.priority_rank || index}`}
                          className="investigation-row"
                          onClick={() => setSelected(item)}
                        >
                          <td><span className="priority-number">#{formatNumber(item.priority_rank ?? index + 1)}</span></td>
                          <td><span className="entity-type">{String(item.entity_type || "UNKNOWN")}</span></td>
                          <td><code className="entity-id">{String(item.entity_id || "—")}</code></td>
                          <td className="risk-score-cell">
                            <strong>{formatScore(item.risk_score)}</strong>
                            <div className="mini-risk-bar">
                              <span style={{ width: `${Math.min(Math.max(safeScore, 0), 100)}%` }} />
                            </div>
                          </td>
                          <td>
                            <span className={`risk-pill ${riskClass(item.risk_band)}`}>
                              {String(item.risk_band || "LOW")}
                            </span>
                          </td>
                          <td>
                            <div className="reason-list">
                              {reasonList(item.reasons).slice(0, 3).map((reason) => (
                                <span key={reason}>{formatReason(reason)}</span>
                              ))}
                            </div>
                          </td>
                          <td>
                            <button
                              type="button"
                              className="view-button"
                              onClick={(event) => {
                                event.stopPropagation();
                                setSelected(item);
                              }}
                            >
                              Review
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <div className="bottom-grid">
            <div className="panel insight-card">
              <div className="insight-icon">⚡</div>
              <div>
                <h3>How to use the queue</h3>
                <p>
                  Start with the highest-ranked candidates, inspect the risk signals,
                  then cross-check supporting transaction, user, merchant and network evidence.
                </p>
              </div>
            </div>

            <div className="panel insight-card">
              <div className="insight-icon ai-icon">✦</div>
              <div>
                <h3>Need a faster answer?</h3>
                <p>
                  Use AI Investigator to ask natural-language questions and generate
                  chart-backed analysis from the same intelligence layer.
                </p>
                <Link href="/ai-investigator">Open AI Investigator →</Link>
              </div>
            </div>
          </div>

          <footer>
            <span>UPI Sentinel · Investigation Intelligence</span>
            <span>Risk scores are investigative signals, not calibrated probabilities.</span>
          </footer>
        </div>
      </section>

      {selected && (
        <div className="drawer-backdrop" onClick={() => setSelected(null)}>
          <aside className="investigation-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <div className="panel-kicker">INVESTIGATION CASE</div>
                <h2>{String(selected.entity_id || "—")}</h2>
                <div className="drawer-entity-type">
                  {String(selected.entity_type || "UNKNOWN")} · PRIORITY #{formatNumber(selected.priority_rank)}
                </div>
              </div>
              <button
                type="button"
                className="close-button"
                onClick={() => setSelected(null)}
                aria-label="Close investigation"
              >×</button>
            </div>

            <div className="drawer-risk">
              <div>
                <div className="drawer-label">UNIFIED RISK SCORE</div>
                <div className="drawer-score">{formatScore(selected.risk_score)}</div>
              </div>
              <span className={`risk-pill large ${riskClass(selected.risk_band)}`}>
                {String(selected.risk_band || "LOW")}
              </span>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">DETECTION SIGNALS</div>
              <div className="drawer-reasons">
                {reasonList(selected.reasons).length === 0 ? (
                  <div className="drawer-reason">
                    <span className="reason-icon">i</span>
                    <span>No explicit reason codes were returned.</span>
                  </div>
                ) : (
                  reasonList(selected.reasons).map((reason) => (
                    <div className="drawer-reason" key={reason}>
                      <span className="reason-icon">!</span>
                      <span>{formatReason(reason)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">INVESTIGATOR GUIDANCE</div>
              <div className="recommendation">
                <div className="recommendation-title">Review supporting evidence</div>
                <p>
                  Examine the entity&apos;s transaction behavior and related user,
                  merchant and network signals before making a final determination.
                </p>
              </div>
            </div>

            <div className="drawer-footer">
              A queue entry is an investigative candidate, not proof of fraud.
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}
