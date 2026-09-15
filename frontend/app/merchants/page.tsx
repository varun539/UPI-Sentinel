

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

const API = "/api/backend";

type Merchant = {
  merchant_id?: string;
  merchant_name?: string;
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
  return "risk-low";
}

function riskNumber(row: Merchant) {
  const value = Number(row.risk_score);
  return Number.isFinite(value) ? value : 0;
}

export default function MerchantsPage() {
  const [rows, setRows] = useState<Merchant[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Merchant | null>(null);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [sort, setSort] = useState<"risk" | "txns" | "chargebacks">("risk");
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetch(`${API}/merchants?limit=100`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        const items = Array.isArray(data)
          ? data
          : data?.merchants || data?.data || data?.items || [];
        setRows(Array.isArray(items) ? items : []);
      })
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();

    return [...rows]
      .filter((row) => {
        const searchable = [
          row.merchant_id,
          row.merchant_name,
          row.risk_band,
        ].join(" ").toLowerCase();

        const matchesSearch = !query || searchable.includes(query);
        const matchesRisk =
          riskFilter === "ALL" ||
          String(row.risk_band || "").toUpperCase() === riskFilter;

        return matchesSearch && matchesRisk;
      })
      .sort((a, b) => {
        if (sort === "txns") {
          return Number(b.transaction_count || 0) - Number(a.transaction_count || 0);
        }
        if (sort === "chargebacks") {
          return Number(b.chargeback_count || 0) - Number(a.chargeback_count || 0);
        }
        return riskNumber(b) - riskNumber(a);
      });
  }, [rows, search, riskFilter, sort]);

  const visibleRows = showAll ? filteredRows : filteredRows.slice(0, 12);

  const summary = useMemo(() => {
    const high = rows.filter((r) =>
      ["HIGH", "CRITICAL"].includes(String(r.risk_band || "").toUpperCase())
    ).length;

    const chargebacks = rows.reduce(
      (sum, r) => sum + Number(r.chargeback_count || 0),
      0
    );

    const transactions = rows.reduce(
      (sum, r) => sum + Number(r.transaction_count || 0),
      0
    );

    const volume = rows.reduce(
      (sum, r) => sum + Number(r.total_amount || r.transaction_volume || r.volume || 0),
      0
    );

    return { high, chargebacks, transactions, volume };
  }, [rows]);

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
              className={`nav-item ${href === "/merchants" ? "active" : ""}`}
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
            <div className="breadcrumb">SENTINEL / <span>MERCHANTS</span></div>
            <h1>Merchant Intelligence</h1>
            <p className="page-description">
              Investigate merchant risk, payment activity and chargeback exposure.
            </p>
          </div>
          <div className="topbar-status">
            <span className="live-dot" /> LIVE DATA
          </div>
        </header>

        <div className="page-grid">
          <div className="stat-card interactive-stat">
            <div className="stat-icon">▣</div>
            <div className="stat-label">MERCHANT ENTITIES</div>
            <div className="stat-value">{rows.length ? rows.length.toLocaleString() : "—"}</div>
            <div className="stat-bottom">
              <span className="stat-live">● LIVE</span><span>Loaded entities</span>
            </div>
          </div>

          <div className="stat-card interactive-stat danger-stat">
            <div className="stat-icon">!</div>
            <div className="stat-label">HIGH / CRITICAL</div>
            <div className="stat-value">{rows.length ? summary.high.toLocaleString() : "—"}</div>
            <div className="stat-bottom">
              <span className="stat-live">● SIGNAL</span><span>Priority review</span>
            </div>
          </div>

          <div className="stat-card interactive-stat">
            <div className="stat-icon">↔</div>
            <div className="stat-label">TRANSACTIONS</div>
            <div className="stat-value">
              {rows.length ? summary.transactions.toLocaleString() : "—"}
            </div>
            <div className="stat-bottom"><span>Across loaded profiles</span></div>
          </div>

          <div className="stat-card interactive-stat">
            <div className="stat-icon">↗</div>
            <div className="stat-label">CHARGEBACK SIGNALS</div>
            <div className="stat-value">
              {rows.length ? summary.chargebacks.toLocaleString() : "—"}
            </div>
            <div className="stat-bottom"><span>Across merchant profiles</span></div>
          </div>

          <div className="section-card wide-card merchant-intelligence-card">
            <div className="section-card-header merchants-toolbar-header">
              <div>
                <div className="section-eyebrow">MERCHANT RISK ENGINE</div>
                <h2>Merchant Risk Profiles</h2>
                <p className="card-description">
                  Search, prioritize and inspect merchant-level risk signals.
                </p>
              </div>
              <div className="record-count">
                {filteredRows.length.toLocaleString()} MATCHED
              </div>
            </div>

            <div className="user-toolbar merchant-toolbar">
              <div className="user-search">
                <span>⌕</span>
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search merchant ID or name..."
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
                  <strong>Loading merchant intelligence...</strong>
                  <span>Pulling merchant profiles from Sentinel.</span>
                </div>
              </div>
            ) : filteredRows.length === 0 ? (
              <div className="empty-state">
                {rows.length
                  ? "No merchants match the current filters."
                  : "Merchant API is connected, but no preview rows were returned."}
              </div>
            ) : (
              <>
                <div className="merchant-table merchant-table-fixed">
                  <div className="merchant-table-header">
                    <span>MERCHANT</span>
                    <span>NAME</span>
                    <span>RISK SCORE</span>
                    <span>BAND</span>
                    <span>TXNS</span>
                    <span>CHARGEBACKS</span>
                  </div>

                  {visibleRows.map((row, i) => {
                    const band = String(row.risk_band || "UNKNOWN").toUpperCase();
                    const score = riskNumber(row);

                    return (
                      <button
                        className="merchant-table-row"
                        key={row.merchant_id || i}
                        onClick={() => setSelected(row)}
                      >
                        <span className="merchant-id-cell">
                          <span className={`merchant-avatar ${riskClass(band)}`}>▣</span>
                          <span className="mono">{row.merchant_id || "—"}</span>
                        </span>

                        <span className="merchant-name-cell">
                          {row.merchant_name || "Unnamed merchant"}
                        </span>

                        <span className="merchant-risk-cell">
                          <span className="merchant-risk-bar">
                            <span style={{ width: `${Math.min(100, Math.max(0, score))}%` }} />
                          </span>
                          <strong>{row.risk_score ?? "—"}</strong>
                        </span>

                        <span>
                          <span className={`status-pill ${riskClass(band)}`}>{band}</span>
                        </span>

                        <span>{row.transaction_count ?? "—"}</span>
                        <span>{row.chargeback_count ?? "—"}</span>
                      </button>
                    );
                  })}
                </div>

                {filteredRows.length > 12 && (
                  <button
                    className="show-more-users"
                    onClick={() => setShowAll((value) => !value)}
                  >
                    {showAll ? "Show top 12" : `View all ${filteredRows.length} matching merchants`} →
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </section>

      {selected && (
        <div className="user-drawer-backdrop" onClick={() => setSelected(null)}>
          <aside className="user-drawer merchant-drawer" onClick={(e) => e.stopPropagation()}>
            <button className="drawer-close" onClick={() => setSelected(null)}>×</button>

            <div className="drawer-kicker">MERCHANT INVESTIGATION</div>

            <div className="drawer-user-heading">
              <div className={`drawer-avatar ${riskClass(selected.risk_band)}`}>▣</div>
              <div>
                <h2>{selected.merchant_id || "Unknown Merchant"}</h2>
                <span className={`status-pill ${riskClass(selected.risk_band)}`}>
                  {String(selected.risk_band || "UNKNOWN").toUpperCase()}
                </span>
              </div>
            </div>

            <div className="drawer-risk">
              <div>
                <span>RISK SCORE</span>
                <strong>{selected.risk_score ?? "—"}</strong>
              </div>
              <div className="drawer-risk-meter">
                <span style={{ width: `${Math.min(100, Math.max(0, Number(selected.risk_score) || 0))}%` }} />
              </div>
            </div>

            <div className="drawer-section merchant-profile-name">
              <div className="section-eyebrow">MERCHANT PROFILE</div>
              <strong>{selected.merchant_name || "Unnamed merchant"}</strong>
            </div>

            <div className="drawer-metrics">
              <div>
                <span>TRANSACTIONS</span>
                <strong>{selected.transaction_count ?? "—"}</strong>
              </div>
              <div>
                <span>CHARGEBACKS</span>
                <strong>{selected.chargeback_count ?? "—"}</strong>
              </div>
              <div>
                <span>CB RATE</span>
                <strong>
                  {Number(selected.transaction_count) > 0
                    ? `${((Number(selected.chargeback_count || 0) / Number(selected.transaction_count)) * 100).toFixed(1)}%`
                    : "—"}
                </strong>
              </div>
              <div>
                <span>ENTITY</span>
                <strong>MERCHANT</strong>
              </div>
            </div>

            <div className="drawer-section">
              <div className="section-eyebrow">INVESTIGATOR NOTE</div>
              <p>
                This merchant is prioritized using Sentinel risk signals. A high score is
                an investigative priority, not proof of fraudulent activity.
              </p>
            </div>

            <Link
              href={`/ai-investigator?merchant=${encodeURIComponent(String(selected.merchant_id || ""))}`}
              className="drawer-action"
            >
              ✦ Investigate with AI →
            </Link>
          </aside>
        </div>
      )}

      <style jsx>{`
        .merchant-table-fixed {
          width: 100%;
          min-width: 0;
          overflow-x: auto;
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 14px;
          background: rgba(8, 12, 18, 0.55);
        }

        .merchant-table-header,
        .merchant-table-row {
          display: grid;
          grid-template-columns:
            minmax(175px, 1.25fr)
            minmax(150px, 1.15fr)
            minmax(145px, 1fr)
            minmax(105px, .75fr)
            minmax(85px, .65fr)
            minmax(125px, .85fr);
          align-items: center;
          column-gap: 18px;
          width: 100%;
          min-width: 900px;
          box-sizing: border-box;
        }

        .merchant-table-header {
          min-height: 48px;
          padding: 0 20px;
          border-bottom: 1px solid rgba(148, 163, 184, 0.12);
          color: #718096;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: .14em;
          text-transform: uppercase;
        }

        .merchant-table-row {
          min-height: 72px;
          padding: 12px 20px;
          border: 0;
          border-bottom: 1px solid rgba(148, 163, 184, 0.09);
          background: transparent;
          color: inherit;
          text-align: left;
          cursor: pointer;
          font: inherit;
          transition: background .18s ease;
        }

        .merchant-table-row:last-child { border-bottom: 0; }
        .merchant-table-row:hover { background: rgba(74, 222, 128, 0.055); }

        .merchant-table-row:focus-visible {
          outline: 2px solid rgba(74, 222, 128, .65);
          outline-offset: -2px;
        }

        .merchant-table-row > span {
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .merchant-id-cell {
          display: flex;
          align-items: center;
          gap: 11px;
          min-width: 0;
        }

        .merchant-avatar {
          display: inline-flex;
          width: 30px;
          height: 30px;
          flex: 0 0 30px;
          align-items: center;
          justify-content: center;
          border-radius: 9px;
          background: rgba(148, 163, 184, .10);
          font-size: 13px;
        }

        .merchant-name-cell {
          color: #cbd5e1;
        }

        .merchant-risk-cell {
          display: grid;
          grid-template-columns: minmax(55px, 1fr) auto;
          align-items: center;
          gap: 10px;
          min-width: 0;
        }

        .merchant-risk-bar {
          display: block;
          width: 100%;
          height: 5px;
          overflow: hidden;
          border-radius: 999px;
          background: rgba(148, 163, 184, .13);
        }

        .merchant-risk-bar > span {
          display: block;
          height: 100%;
          border-radius: inherit;
          background: currentColor;
          opacity: .9;
        }

        .merchant-risk-cell strong {
          min-width: 36px;
          color: #d7dee8;
          font-size: 12px;
          text-align: right;
        }

        .merchant-table-row .status-pill {
          display: inline-flex;
          width: fit-content;
          align-items: center;
          justify-content: center;
          white-space: nowrap;
        }

        .merchant-table-row .mono {
          font-family: var(--font-geist-mono), ui-monospace, SFMono-Regular, Menlo, monospace;
          font-size: 12px;
        }

        .merchant-profile-name strong {
          display: block;
          margin-top: 8px;
          color: #d7dee8;
          font-size: 16px;
        }

        @media (max-width: 900px) {
          .merchant-table-fixed { overflow-x: auto; }
        }
      `}</style>
    </main>
  );
}
