 "use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

const API = "/api/backend";

type User = {
  user_id?: string;

  // Stage 08 / unified intelligence fields
  unified_user_risk_score?: number;
  unified_user_risk_band?: string;
  network_transaction_count?: number;
  network_chargeback_count?: number;
  network_chargeback_rate?: number;
  total_amount?: number;
  transaction_volume?: number;
  volume?: number;

  // Backward-compatible aliases
  risk_score?: number;
  risk_band?: string;
  transaction_count?: number;
  chargeback_count?: number;

  [key: string]: any;
};

const navMonitoring = [
  ["⌂", "Dashboard", "/"],
  ["⚠", "Investigations", "/investigations"],
  ["↔", "Transactions", "/transactions"],
  ["◉", "Users", "/users"],
  ["▣", "Merchants", "/merchants"],
  ["⌁", "Networks", "/networks"],
];

function riskClass(band?: string) {
  const value = String(band || "").toUpperCase();

  if (value === "CRITICAL") return "risk-critical";
  if (value === "HIGH") return "risk-high";
  if (value === "MEDIUM") return "risk-medium";
  if (value === "LOW") return "risk-low";

  return "risk-unknown";
}

function riskNumber(row: User) {
  const value = Number(
    row.unified_user_risk_score ?? row.risk_score
  );

  return Number.isFinite(value) ? value : 0;
}

function userBand(row: User) {
  const explicit = String(
    row.unified_user_risk_band ?? row.risk_band ?? ""
  ).toUpperCase();

  if (["LOW", "MEDIUM", "HIGH", "CRITICAL"].includes(explicit)) {
    return explicit;
  }

  const rawScore = row.unified_user_risk_score ?? row.risk_score;
  const score = Number(rawScore);

  if (!Number.isFinite(score)) return "UNKNOWN";
  if (score > 75) return "CRITICAL";
  if (score > 50) return "HIGH";
  if (score > 25) return "MEDIUM";

  return "LOW";
}

function userTransactions(row: User) {
  return Number(
    row.network_transaction_count ??
    row.transaction_count ??
    0
  );
}

function userChargebacks(row: User) {
  return Number(
    row.network_chargeback_count ??
    row.chargeback_count ??
    0
  );
}

export default function UsersPage() {
  const [rows, setRows] = useState<User[]>([]);
  const [serverSummary, setServerSummary] = useState<{
    total?: number;
    highCritical?: number;
    medium?: number;
    chargebacks?: number;
  }>({});
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<User | null>(null);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [sort, setSort] = useState<"risk" | "txns" | "chargebacks">("risk");
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetch(`${API}/users?limit=100`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        const items = Array.isArray(data)
          ? data
          : data?.users || data?.data || data?.items || [];

        setRows(items);

        if (data && !Array.isArray(data)) {
          setServerSummary({
            total: Number(data?.total ?? data?.count ?? data?.total_users) || undefined,
            highCritical: Number(data?.high_critical ?? data?.highCritical) || undefined,
            medium: Number(data?.medium) || undefined,
            chargebacks: Number(data?.chargebacks ?? data?.chargeback_signals) || undefined,
          });
        }
      })
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();

    return [...rows]
      .filter((row) => {
        const matchesSearch =
          !query || String(row.user_id || "").toLowerCase().includes(query);
        const matchesRisk =
          riskFilter === "ALL" ||
          userBand(row) === riskFilter;
        return matchesSearch && matchesRisk;
      })
      .sort((a, b) => {
        if (sort === "txns")
          return userTransactions(b) - userTransactions(a);
        if (sort === "chargebacks")
          return userChargebacks(b) - userChargebacks(a);
        return riskNumber(b) - riskNumber(a);
      });
  }, [rows, search, riskFilter, sort]);

  const visibleRows = showAll ? filteredRows : filteredRows.slice(0, 12);

  const summary = useMemo(() => {
    const high = rows.filter((r) =>
      ["HIGH", "CRITICAL"].includes(userBand(r))
    ).length;

    const medium = rows.filter(
      (r) => userBand(r) === "MEDIUM"
    ).length;

    const chargebacks = rows.reduce(
      (sum, r) => sum + userChargebacks(r),
      0
    );

    return {
      high: serverSummary.highCritical ?? high,
      medium: serverSummary.medium ?? medium,
      chargebacks: serverSummary.chargebacks ?? chargebacks,
    };
  }, [rows, serverSummary]);

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
          {navMonitoring.map(([icon, label, href]) => (
            <Link
              key={href}
              className={`nav-item ${href === "/users" ? "active" : ""}`}
              href={href}
            >
              {icon} <span>{label}</span>
            </Link>
          ))}
        </div>

        <div className="nav-section">
          <div className="nav-title">INTELLIGENCE</div>
          <Link className="nav-item" href="/ai-investigator">
            ✦ <span>AI Investigator</span><span className="ai-badge">AI</span>
          </Link>
        </div>

        <div className="sidebar-footer">
          <span className="live-dot" /> SENTINEL ONLINE
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">SENTINEL / <span>USERS</span></div>
            <h1>User Intelligence</h1>
            <p className="page-description">
              Investigate user-level risk signals, transaction behavior and chargeback exposure.
            </p>
          </div>
          <div className="topbar-status">
            <span className="live-dot" /> LIVE DATA
          </div>
        </header>

        <div className="page-grid">
          <div className="stat-card interactive-stat">
            <div className="stat-icon">◎</div>
            <div className="stat-label">UNIQUE USERS</div>
            <div className="stat-value">
              {(serverSummary.total ?? rows.length) ? (serverSummary.total ?? rows.length).toLocaleString() : "—"}
            </div>
            <div className="stat-bottom"><span className="stat-live">● LIVE</span><span>Loaded entities</span></div>
          </div>

          <div className="stat-card interactive-stat danger-stat">
            <div className="stat-icon">!</div>
            <div className="stat-label">HIGH / CRITICAL</div>
            <div className="stat-value">{rows.length ? summary.high.toLocaleString() : "—"}</div>
            <div className="stat-bottom"><span className="stat-live">● SIGNAL</span><span>Prioritized entities</span></div>
          </div>

          <div className="stat-card interactive-stat">
            <div className="stat-icon">↯</div>
            <div className="stat-label">MEDIUM RISK</div>
            <div className="stat-value">{rows.length ? summary.medium.toLocaleString() : "—"}</div>
            <div className="stat-bottom"><span>Review recommended</span></div>
          </div>

          <div className="stat-card interactive-stat">
            <div className="stat-icon">↗</div>
            <div className="stat-label">CHARGEBACK SIGNALS</div>
            <div className="stat-value">{rows.length ? summary.chargebacks.toLocaleString() : "—"}</div>
            <div className="stat-bottom"><span>Across loaded profiles</span></div>
          </div>

          <div className="section-card wide-card user-intelligence-card">
            <div className="section-card-header users-toolbar-header">
              <div>
                <div className="section-eyebrow">ENTITY INTELLIGENCE</div>
                <h2>User Risk Profiles</h2>
                <p className="card-description">
                  Select a profile to inspect its risk posture and activity signals.
                </p>
              </div>
              <div className="record-count">
                {filteredRows.length.toLocaleString()} MATCHED
              </div>
            </div>

            <div className="user-toolbar">
              <div className="user-search">
                <span>⌕</span>
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search user ID..."
                />
                {search && <button onClick={() => setSearch("")}>×</button>}
              </div>

              <div className="filter-group">
                {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((filter) => (
                  <button
                    key={filter}
                    className={`filter-chip ${riskFilter === filter ? "selected" : ""} ${filter !== "ALL" ? riskClass(filter) : ""}`}
                    onClick={() => setRiskFilter(filter)}
                  >
                    {filter}
                  </button>
                ))}
              </div>

              <select
                className="sort-select"
                value={sort}
                onChange={(e) => setSort(e.target.value as typeof sort)}
              >
                <option value="risk">Sort: Risk</option>
                <option value="txns">Sort: Transactions</option>
                <option value="chargebacks">Sort: Chargebacks</option>
              </select>
            </div>

            {loading ? (
              <div className="user-loading">
                <div className="loading-orbit" />
                <div>
                  <strong>Loading user intelligence...</strong>
                  <span>Pulling the latest risk profiles from Sentinel.</span>
                </div>
              </div>
            ) : filteredRows.length === 0 ? (
              <div className="empty-state">
                {rows.length
                  ? "No users match the current filters."
                  : "User intelligence endpoint is connected. No preview rows returned."}
              </div>
            ) : (
              <>
                <div className="data-table user-table">
                  <div className="data-row data-header">
                    <span>USER</span>
                    <span>RISK SCORE</span>
                    <span>BAND</span>
                    <span>TXNS</span>
                    <span>CHARGEBACKS</span>
                  </div>

                  {visibleRows.map((row, i) => {
                    const band = userBand(row);
                    const score = riskNumber(row);
                    const transactions = userTransactions(row);
                    const chargebacks = userChargebacks(row);

                    return (
                      <button
                        className="data-row user-row"
                        key={row.user_id || i}
                        onClick={() => setSelected(row)}
                      >
                        <span className="user-id-cell">
                          <span className={`user-avatar ${riskClass(band)}`}>
                            {String(row.user_id || "U").slice(-2)}
                          </span>
                          <span className="mono">{row.user_id || "—"}</span>
                        </span>

                        <span className="risk-score-cell">
                          <span className="risk-bar">
                            <span
                              style={{
                                width: `${Math.min(
                                  100,
                                  Math.max(0, score)
                                )}%`,
                              }}
                            />
                          </span>
                          <strong>{score.toFixed(2)}</strong>
                        </span>

                        <span>
                          <span className={`status-pill ${riskClass(band)}`}>
                            {band}
                          </span>
                        </span>

                        <span>{transactions.toLocaleString("en-IN")}</span>
                        <span>{chargebacks.toLocaleString("en-IN")}</span>
                      </button>
                    );
                  })}
                </div>

                {filteredRows.length > 12 && (
                  <button
                    className="show-more-users"
                    onClick={() => setShowAll((value) => !value)}
                  >
                    {showAll ? "Show top 12" : `View all ${filteredRows.length} matching users`} →
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </section>

      {selected && (
        <div className="user-drawer-backdrop" onClick={() => setSelected(null)}>
          <aside className="user-drawer" onClick={(e) => e.stopPropagation()}>
            <button className="drawer-close" onClick={() => setSelected(null)}>×</button>

            <div className="drawer-kicker">USER INVESTIGATION</div>
            <div className="drawer-user-heading">
              <div className={`drawer-avatar ${riskClass(userBand(selected))}`}>
                {String(selected.user_id || "U").slice(-2)}
              </div>
              <div>
                <h2>{selected.user_id || "Unknown User"}</h2>
                <span className={`status-pill ${riskClass(userBand(selected))}`}>
                  {userBand(selected)}
                </span>
              </div>
            </div>

            <div className="drawer-risk">
              <div>
                <span>RISK SCORE</span>
                <strong>
                  {Number.isFinite(riskNumber(selected))
                    ? riskNumber(selected).toFixed(2)
                    : "—"}
                </strong>
              </div>
              <div className="drawer-risk-meter">
                <span style={{ width: `${Math.min(100, Math.max(0, riskNumber(selected)))}%` }} />
              </div>
            </div>

            <div className="drawer-metrics">
              <div><span>TRANSACTIONS</span><strong>{userTransactions(selected).toLocaleString("en-IN")}</strong></div>
              <div><span>CHARGEBACKS</span><strong>{userChargebacks(selected).toLocaleString("en-IN")}</strong></div>
              <div><span>CB RATE</span><strong>
                {userTransactions(selected) > 0
                  ? `${((userChargebacks(selected) / userTransactions(selected)) * 100).toFixed(1)}%`
                  : "—"}
              </strong></div>
              <div><span>ENTITY</span><strong>USER</strong></div>
            </div>

            <div className="drawer-section">
              <div className="section-eyebrow">INVESTIGATOR NOTE</div>
              <p>
                This profile is surfaced using Sentinel risk signals. A high score is an
                investigative priority, not proof of fraudulent activity.
              </p>
            </div>

            <Link
              href={`/ai-investigator?user=${encodeURIComponent(String(selected.user_id || ""))}`}
              className="drawer-action"
            >
              ✦ Investigate with AI →
            </Link>
          </aside>
        </div>
      )}
    </main>
  );
}