"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

const API = "/api/backend";

type Transaction = {
  txn_id?: string;
  user_id?: string;
  merchant_id?: string;
  amount?: number;
  status?: string;
  risk_score?: number;
  risk_band?: string;
  timestamp?: string;
  transaction_timestamp?: string;
  mcc?: string | number;
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

function statusClass(status?: string) {
  const value = String(status || "").toUpperCase();
  if (value === "SUCCESS") return "tx-success";
  if (value === "FAILED") return "tx-failed";
  if (value === "PENDING") return "tx-pending";
  return "";
}

function formatAmount(amount?: number) {
  return typeof amount === "number"
    ? `₹${amount.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`
    : "—";
}

function formatTime(row: Transaction) {
  const raw = row.timestamp || row.transaction_timestamp;
  if (!raw) return "—";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return String(raw);
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function TransactionsPage() {
  const [rows, setRows] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Transaction | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [sort, setSort] = useState<"latest" | "amount" | "risk">("latest");
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetch(`${API}/transactions?limit=100`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        const items = Array.isArray(data)
          ? data
          : data?.transactions || data?.data || data?.items || [];
        setRows(items);
      })
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();

    return [...rows]
      .filter((row) => {
        const searchable = [
          row.txn_id,
          row.user_id,
          row.merchant_id,
          row.status,
          row.risk_band,
        ]
          .join(" ")
          .toLowerCase();

        const matchesSearch = !query || searchable.includes(query);
        const matchesStatus =
          statusFilter === "ALL" ||
          String(row.status || "").toUpperCase() === statusFilter;
        const matchesRisk =
          riskFilter === "ALL" ||
          String(row.risk_band || "").toUpperCase() === riskFilter;

        return matchesSearch && matchesStatus && matchesRisk;
      })
      .sort((a, b) => {
        if (sort === "amount")
          return Number(b.amount || 0) - Number(a.amount || 0);
        if (sort === "risk")
          return Number(b.risk_score || 0) - Number(a.risk_score || 0);

        const aTime = new Date(a.timestamp || a.transaction_timestamp || 0).getTime();
        const bTime = new Date(b.timestamp || b.transaction_timestamp || 0).getTime();
        return bTime - aTime;
      });
  }, [rows, search, statusFilter, riskFilter, sort]);

  const visibleRows = showAll ? filteredRows : filteredRows.slice(0, 12);

  const summary = useMemo(() => {
    const success = rows.filter((r) => String(r.status).toUpperCase() === "SUCCESS").length;
    const failed = rows.filter((r) => String(r.status).toUpperCase() === "FAILED").length;
    const pending = rows.filter((r) => String(r.status).toUpperCase() === "PENDING").length;
    const highRisk = rows.filter((r) =>
      ["HIGH", "CRITICAL"].includes(String(r.risk_band || "").toUpperCase())
    ).length;
    const volume = rows.reduce((sum, r) => sum + Number(r.amount || 0), 0);
    const avgRisk = rows.length
      ? rows.reduce((sum, r) => sum + Number(r.risk_score || 0), 0) / rows.length
      : 0;

    return { success, failed, pending, highRisk, volume, avgRisk };
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
              className={`nav-item ${href === "/transactions" ? "active" : ""}`}
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
            <div className="breadcrumb">SENTINEL / <span>TRANSACTIONS</span></div>
            <h1>Transaction Intelligence</h1>
            <p className="page-description">
              Monitor transaction flow, payment outcomes and risk signals in one place.
            </p>
          </div>
          <div className="topbar-status">
            <span className="live-dot" /> LIVE DATA
          </div>
        </header>

        <div className="page-grid">
          <div className="stat-card interactive-stat">
            <div className="stat-icon">↔</div>
            <div className="stat-label">TRANSACTIONS LOADED</div>
            <div className="stat-value">{rows.length ? rows.length.toLocaleString() : "—"}</div>
            <div className="stat-bottom"><span className="stat-live">● LIVE</span><span>Monitored records</span></div>
          </div>

          <div className="stat-card interactive-stat">
            <div className="stat-icon">₹</div>
            <div className="stat-label">OBSERVED VOLUME</div>
            <div className="stat-value">
              {rows.length ? `₹${summary.volume.toLocaleString("en-IN", { maximumFractionDigits: 0 })}` : "—"}
            </div>
            <div className="stat-bottom"><span>Loaded transaction volume</span></div>
          </div>

          <div className="stat-card interactive-stat danger-stat">
            <div className="stat-icon">!</div>
            <div className="stat-label">HIGH / CRITICAL</div>
            <div className="stat-value">{rows.length ? summary.highRisk.toLocaleString() : "—"}</div>
            <div className="stat-bottom"><span className="stat-live">● SIGNAL</span><span>Risk-prioritized</span></div>
          </div>

          <div className="stat-card interactive-stat">
            <div className="stat-icon">✓</div>
            <div className="stat-label">SUCCESS RATE</div>
            <div className="stat-value">
              {rows.length ? `${((summary.success / rows.length) * 100).toFixed(1)}%` : "—"}
            </div>
            <div className="stat-bottom">
              <span>{summary.success.toLocaleString()} successful</span>
            </div>
          </div>

          <div className="section-card wide-card transaction-intelligence-card">
            <div className="section-card-header transactions-toolbar-header">
              <div>
                <div className="section-eyebrow">TRANSACTION MONITORING</div>
                <h2>Transaction Intelligence</h2>
                <p className="card-description">
                  Search, filter and inspect individual payment activity.
                </p>
              </div>
              <div className="record-count">{filteredRows.length.toLocaleString()} MATCHED</div>
            </div>

            <div className="transaction-summary-strip">
              <div><span className="summary-dot success" /><strong>{summary.success}</strong><span>Success</span></div>
              <div><span className="summary-dot failed" /><strong>{summary.failed}</strong><span>Failed</span></div>
              <div><span className="summary-dot pending" /><strong>{summary.pending}</strong><span>Pending</span></div>
              <div><span>AVG RISK</span><strong>{rows.length ? summary.avgRisk.toFixed(2) : "—"}</strong></div>
            </div>

            <div className="user-toolbar transaction-toolbar">
              <div className="user-search">
                <span>⌕</span>
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search transaction, user or merchant..."
                />
                {search && <button onClick={() => setSearch("")}>×</button>}
              </div>

              <div className="filter-group">
                {["ALL", "SUCCESS", "FAILED", "PENDING"].map((filter) => (
                  <button
                    key={filter}
                    className={`filter-chip ${statusFilter === filter ? "selected" : ""}`}
                    onClick={() => setStatusFilter(filter)}
                  >
                    {filter}
                  </button>
                ))}
              </div>

              <select
                className="sort-select"
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
              >
                <option value="ALL">Risk: All</option>
                <option value="CRITICAL">Risk: Critical</option>
                <option value="HIGH">Risk: High</option>
                <option value="MEDIUM">Risk: Medium</option>
                <option value="LOW">Risk: Low</option>
              </select>

              <select
                className="sort-select"
                value={sort}
                onChange={(e) => setSort(e.target.value as typeof sort)}
              >
                <option value="latest">Sort: Latest</option>
                <option value="risk">Sort: Risk</option>
                <option value="amount">Sort: Amount</option>
              </select>
            </div>

            {loading ? (
              <div className="user-loading">
                <div className="loading-orbit" />
                <div>
                  <strong>Loading transaction intelligence...</strong>
                  <span>Pulling payment activity from Sentinel.</span>
                </div>
              </div>
            ) : filteredRows.length === 0 ? (
              <div className="empty-state">
                {rows.length ? "No transactions match the current filters." : "Transaction API is connected, but no preview rows were returned."}
              </div>
            ) : (
              <>
                <div className="data-table transaction-table">
                  <div className="data-row data-header">
                    <span>TRANSACTION</span>
                    <span>USER</span>
                    <span>MERCHANT</span>
                    <span>AMOUNT</span>
                    <span>STATUS</span>
                    <span>RISK</span>
                  </div>

                  {visibleRows.map((row, index) => {
                    const band = String(row.risk_band || "").toUpperCase();
                    return (
                      <button
                        className="data-row transaction-row"
                        key={row.txn_id || index}
                        onClick={() => setSelected(row)}
                      >
                        <span className="mono txn-id-cell">{row.txn_id || "—"}</span>
                        <span className="mono">{row.user_id || "—"}</span>
                        <span className="mono">{row.merchant_id || "—"}</span>
                        <span className="amount-cell">{formatAmount(row.amount)}</span>
                        <span>
                          <span className={`status-pill ${statusClass(row.status)}`}>
                            {String(row.status || "UNKNOWN").toUpperCase()}
                          </span>
                        </span>
                        <span className="risk-inline">
                          {row.risk_score ?? "—"}
                          {band && <small className={riskClass(band)}>{band}</small>}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {filteredRows.length > 12 && (
                  <button
                    className="show-more-users"
                    onClick={() => setShowAll((value) => !value)}
                  >
                    {showAll ? "Show top 12" : `View all ${filteredRows.length} matching transactions`} →
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </section>

      {selected && (
        <div className="user-drawer-backdrop" onClick={() => setSelected(null)}>
          <aside className="user-drawer transaction-drawer" onClick={(e) => e.stopPropagation()}>
            <button className="drawer-close" onClick={() => setSelected(null)}>×</button>

            <div className="drawer-kicker">TRANSACTION INSPECTION</div>
            <div className="drawer-user-heading">
              <div className={`drawer-avatar ${riskClass(selected.risk_band)}`}>↔</div>
              <div>
                <h2>{selected.txn_id || "Unknown Transaction"}</h2>
                <span className={`status-pill ${statusClass(selected.status)}`}>
                  {String(selected.status || "UNKNOWN").toUpperCase()}
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

            <div className="drawer-amount">
              <span>TRANSACTION AMOUNT</span>
              <strong>{formatAmount(selected.amount)}</strong>
            </div>

            <div className="drawer-metrics">
              <div><span>USER</span><strong className="mono">{selected.user_id || "—"}</strong></div>
              <div><span>MERCHANT</span><strong className="mono">{selected.merchant_id || "—"}</strong></div>
              <div><span>MCC</span><strong>{selected.mcc ?? "—"}</strong></div>
              <div><span>TIME</span><strong>{formatTime(selected)}</strong></div>
            </div>

            <div className="drawer-section">
              <div className="section-eyebrow">INVESTIGATOR NOTE</div>
              <p>
                Transaction risk is an investigative signal generated from Sentinel
                intelligence features. A flagged transaction is not, by itself, proof of fraud.
              </p>
            </div>

            <Link
              href={`/ai-investigator?txn=${encodeURIComponent(String(selected.txn_id || ""))}`}
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
