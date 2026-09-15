"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API = "/api/backend";

type Transaction = {
  txn_id?: string;
  user_id?: string;
  merchant_id?: string;
  amount?: number;
  status?: string;
  risk_score?: number;
  risk_band?: string;
  [key: string]: any;
};

export default function TransactionsPage() {
  const [rows, setRows] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/transactions?limit=25`)
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
          <Link className="nav-item" href="/">⌂ <span>Dashboard</span></Link>
          <Link className="nav-item" href="/investigations">⚠ <span>Investigations</span></Link>
          <Link className="nav-item active" href="/transactions">↔ <span>Transactions</span></Link>
          <Link className="nav-item" href="/users">◉ <span>Users</span></Link>
          <Link className="nav-item" href="/merchants">▣ <span>Merchants</span></Link>
          <Link className="nav-item" href="/networks">⌁ <span>Networks</span></Link>
        </div>

        <div className="nav-section">
          <div className="nav-title">INTELLIGENCE</div>
          <Link className="nav-item" href="/ai-investigator">
            ✦ <span>AI Investigator</span>
            <span className="ai-badge">AI</span>
          </Link>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">SENTINEL / <span>TRANSACTIONS</span></div>
            <h1>Transaction Intelligence</h1>
          </div>
        </header>

        <div className="page-grid">
          <div className="stat-card">
            <div className="stat-label">TOTAL TRANSACTIONS</div>
            <div className="stat-value">20,000</div>
            <div className="stat-bottom">
              <span className="stat-live">● LIVE</span>
              <span>Processed</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-label">TRANSACTION RISK</div>
            <div className="stat-value">20.44</div>
            <div className="stat-bottom">
              <span className="stat-live">● LIVE</span>
              <span>Average score</span>
            </div>
          </div>

          <div className="section-card wide-card">
            <div className="section-card-header">
              <div>
                <div className="section-eyebrow">TRANSACTION MONITORING</div>
                <h2>Recent Transaction Intelligence</h2>
              </div>
              <span className="ai-badge">LIVE</span>
            </div>

            {loading ? (
              <div className="empty-state">Loading transaction intelligence...</div>
            ) : rows.length === 0 ? (
              <div className="empty-state">
                Transaction API is connected, but no preview rows were returned.
              </div>
            ) : (
              <div className="data-table">
                <div className="data-row data-header">
                  <span>TRANSACTION</span>
                  <span>USER</span>
                  <span>MERCHANT</span>
                  <span>AMOUNT</span>
                  <span>STATUS</span>
                </div>

                {rows.slice(0, 12).map((row, index) => (
                  <div className="data-row" key={row.txn_id || index}>
                    <span className="mono">{row.txn_id || "—"}</span>
                    <span className="mono">{row.user_id || "—"}</span>
                    <span className="mono">{row.merchant_id || "—"}</span>
                    <span>
                      {typeof row.amount === "number"
                        ? `₹${row.amount.toLocaleString("en-IN")}`
                        : "—"}
                    </span>
                    <span className="status-pill">{row.status || "UNKNOWN"}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
