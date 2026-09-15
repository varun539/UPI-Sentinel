"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API = "/api/backend";

type User = {
  user_id?: string;
  risk_score?: number;
  risk_band?: string;
  transaction_count?: number;
  chargeback_count?: number;
  [key: string]: any;
};

export default function UsersPage() {
  const [rows, setRows] = useState<User[]>([]);

  useEffect(() => {
    fetch(`${API}/users?limit=25`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        const items = Array.isArray(data)
          ? data
          : data?.users || data?.data || data?.items || [];
        setRows(items);
      })
      .catch(() => setRows([]));
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
          <Link className="nav-item" href="/transactions">↔ <span>Transactions</span></Link>
          <Link className="nav-item active" href="/users">◉ <span>Users</span></Link>
          <Link className="nav-item" href="/merchants">▣ <span>Merchants</span></Link>
          <Link className="nav-item" href="/networks">⌁ <span>Networks</span></Link>
        </div>

        <div className="nav-section">
          <div className="nav-title">INTELLIGENCE</div>
          <Link className="nav-item" href="/ai-investigator">✦ <span>AI Investigator</span><span className="ai-badge">AI</span></Link>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">SENTINEL / <span>USERS</span></div>
            <h1>User Intelligence</h1>
          </div>
        </header>

        <div className="page-grid">
          <div className="stat-card">
            <div className="stat-label">UNIQUE USERS</div>
            <div className="stat-value">17,878</div>
            <div className="stat-bottom"><span className="stat-live">● LIVE</span><span>Monitored</span></div>
          </div>

          <div className="stat-card">
            <div className="stat-label">HIGH / CRITICAL</div>
            <div className="stat-value">1,075</div>
            <div className="stat-bottom"><span className="stat-live">● SIGNAL</span><span>Prioritized entities</span></div>
          </div>

          <div className="section-card wide-card">
            <div className="section-card-header">
              <div>
                <div className="section-eyebrow">ENTITY INTELLIGENCE</div>
                <h2>User Risk Profiles</h2>
              </div>
            </div>

            {rows.length === 0 ? (
              <div className="empty-state">User intelligence endpoint is connected. No preview rows returned.</div>
            ) : (
              <div className="data-table">
                <div className="data-row data-header">
                  <span>USER</span><span>RISK</span><span>BAND</span><span>TXNS</span><span>CHARGEBACKS</span>
                </div>
                {rows.slice(0, 12).map((row, i) => (
                  <div className="data-row" key={row.user_id || i}>
                    <span className="mono">{row.user_id || "—"}</span>
                    <span>{row.risk_score ?? "—"}</span>
                    <span className="status-pill">{row.risk_band || "—"}</span>
                    <span>{row.transaction_count ?? "—"}</span>
                    <span>{row.chargeback_count ?? "—"}</span>
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
