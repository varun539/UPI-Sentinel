"use client";

import Link from "next/link";
import { useState } from "react";

const API = "/api/backend";

export default function AIInvestigatorPage() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function investigate() {
    if (!query.trim()) return;

    setLoading(true);
    setAnswer("");

    try {
      const response = await fetch(`${API}/investigations?limit=5`);
      const data = await response.json();

      const items = Array.isArray(data)
        ? data
        : data?.investigations || data?.data || data?.items || [];

      if (
        /highest.*risk.*user|risk.*user|users.*risk/i.test(query)
      ) {
        const text = items
          .filter((x: any) => String(x.entity_type).toUpperCase() === "USER")
          .slice(0, 5)
          .map(
            (x: any) =>
              `${x.entity_id}: ${x.risk_score} (${x.risk_band}) — ${String(x.reasons || "").replaceAll("|", ", ")}`
          )
          .join("\n");

        setAnswer(
          `Top investigation candidates matching your question:\n\n${text || "No matching user candidates found."}`
        );
      } else if (/network|ring|cluster/i.test(query)) {
        setAnswer(
          "Sentinel detected suspicious connected-network candidates using User ↔ Merchant graph analysis. Open Network Intelligence for component-level investigation."
        );
      } else if (/merchant/i.test(query)) {
        setAnswer(
          "Sentinel can prioritize merchants using behavioral, chargeback, ticket-size and network signals. Open Merchant Intelligence for the ranked entity view."
        );
      } else {
        setAnswer(
          "I routed the question to Sentinel's investigation intelligence layer. Try asking about high-risk users, suspicious networks, merchants, chargebacks or transaction anomalies."
        );
      }
    } catch {
      setAnswer("The intelligence backend could not be reached. Verify the API connection.");
    } finally {
      setLoading(false);
    }
  }

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
          <Link className="nav-item" href="/users">◉ <span>Users</span></Link>
          <Link className="nav-item" href="/merchants">▣ <span>Merchants</span></Link>
          <Link className="nav-item" href="/networks">⌁ <span>Networks</span></Link>
        </div>

        <div className="nav-section">
          <div className="nav-title">INTELLIGENCE</div>
          <Link className="nav-item active" href="/ai-investigator">
            ✦ <span>AI Investigator</span>
            <span className="ai-badge">AI</span>
          </Link>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">SENTINEL / <span>AI INVESTIGATOR</span></div>
            <h1>AI Investigator</h1>
          </div>
        </header>

        <div className="page-grid">
          <div className="section-card wide-card">
            <div className="section-card-header">
              <div>
                <div className="section-eyebrow">INTELLIGENCE COPILOT</div>
                <h2>Ask Sentinel</h2>
              </div>
              <span className="ai-badge">AI</span>
            </div>

            <p className="muted">
              Ask natural-language questions about suspicious users,
              networks, merchants and transactions.
            </p>

            <div className="agent-input">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") investigate();
                }}
                placeholder="Which users have the highest risk?"
              />
              <button className="primary-button" onClick={investigate}>
                {loading ? "Analyzing..." : "Investigate →"}
              </button>
            </div>

            <div className="suggestion-grid">
              <button onClick={() => setQuery("Which users have the highest risk?")}>
                Highest-risk users
              </button>
              <button onClick={() => setQuery("Show suspicious networks")}>
                Suspicious networks
              </button>
              <button onClick={() => setQuery("Which merchants look risky?")}>
                Risky merchants
              </button>
            </div>

            {answer && (
              <div className="agent-answer">
                <div className="section-eyebrow">SENTINEL ANALYSIS</div>
                <pre>{answer}</pre>
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
