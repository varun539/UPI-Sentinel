"use client";

import { useEffect, useMemo, useState } from "react";

const API = "/api/backend";

type Network = {
  component_id: number;
  user_count: number;
  merchant_count: number;
  edge_count: number;
  total_transactions: number;
  total_amount: number;
  total_chargebacks: number;
  chargeback_rate: number;
  network_density: number;
  max_shared_users_per_merchant: number;
  shared_merchant_count: number;
  avg_relationship_risk: number;
  max_relationship_risk: number;
  network_risk_score: number;
  risk_band: string;
  signals: string;
};

function riskClass(band: string) {
  if (band === "CRITICAL") return "risk-critical";
  if (band === "HIGH") return "risk-high";
  if (band === "MEDIUM") return "risk-medium";
  return "risk-low";
}

function formatSignal(signal: string) {
  return signal
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatAmount(amount: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export default function NetworksPage() {
  const [networks, setNetworks] = useState<Network[]>([]);
  const [selected, setSelected] = useState<Network | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");

  useEffect(() => {
    async function loadNetworks() {
      try {
        const response = await fetch(`${API}/networks`, {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("Network API failed");
        }

        const data = await response.json();
        setNetworks(data.networks || []);
      } catch (err) {
        console.error(err);
        setError("Unable to load network intelligence.");
      } finally {
        setLoading(false);
      }
    }

    loadNetworks();
  }, []);

  async function openNetwork(network: Network) {
    setSelected(network);
    setDetailLoading(true);

    try {
      const response = await fetch(
        `${API}/networks/${network.component_id}`,
        { cache: "no-store" }
      );

      if (!response.ok) {
        throw new Error("Network detail API failed");
      }

      const detail = await response.json();
      setSelected(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  }

  const filteredNetworks = useMemo(() => {
    const query = search.trim().toLowerCase();

    return networks.filter((network) => {
      const matchesSearch =
        !query ||
        String(network.component_id).includes(query) ||
        network.risk_band.toLowerCase().includes(query) ||
        network.signals.toLowerCase().includes(query);

      const matchesRisk =
        riskFilter === "ALL" ||
        network.risk_band === riskFilter;

      return matchesSearch && matchesRisk;
    });
  }, [networks, search, riskFilter]);

  const highRisk = networks.filter(
    (network) => network.risk_band === "HIGH"
  ).length;

  const totalChargebacks = networks.reduce(
    (sum, network) => sum + network.total_chargebacks,
    0
  );

  const totalVolume = networks.reduce(
    (sum, network) => sum + network.total_amount,
    0
  );

  return (
    <main className="dashboard-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">U</div>

          <div>
            <div className="brand-name">UPI Sentinel</div>
            <div className="brand-subtitle">
              Fraud Intelligence
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <a href="/" className="nav-item">
            <span>⌂</span>
            Dashboard
          </a>

          <a href="/investigations" className="nav-item">
            <span>⌕</span>
            Investigations
            <span className="nav-badge">346</span>
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

          <a href="/networks" className="nav-item active">
            <span>⌘</span>
            Networks
          </a>

          <div className="nav-section-title">
            INTELLIGENCE
          </div>

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

          <div className="version">
            UPI Sentinel v0.2.0
          </div>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">
              GRAPH INTELLIGENCE
            </div>

            <h1>Network Intelligence</h1>

            <p>
              Detect suspicious relationships across users and
              merchants.
            </p>
          </div>

          <div className="topbar-status">
            <span className="status-dot" />
            API Connected
          </div>
        </header>

        <section className="stats-grid network-stats">
          <div className="stat-card">
            <div className="stat-label">
              SUSPICIOUS NETWORKS
            </div>

            <div className="stat-value">3,109</div>

            <div className="stat-meta">
              Candidates requiring review
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-label">
              HIGH RISK IN TOP 50
            </div>

            <div className="stat-value">
              {highRisk}
            </div>

            <div className="stat-meta">
              Highest-ranked network candidates
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-label">
              NETWORK CHARGEBACKS
            </div>

            <div className="stat-value">
              {totalChargebacks}
            </div>

            <div className="stat-meta">
              Across displayed networks
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-label">
              DISPLAYED VOLUME
            </div>

            <div className="stat-value network-money">
              {formatAmount(totalVolume)}
            </div>

            <div className="stat-meta">
              Top 50 network candidates
            </div>
          </div>
        </section>

        <section className="network-hero">
          <div className="network-hero-copy">
            <div className="panel-kicker">
              USER ↔ MERCHANT GRAPH
            </div>

            <h2>Find suspicious relationship clusters</h2>

            <p>
              UPI Sentinel connects transaction participants into
              a graph and prioritizes dense or chargeback-heavy
              components for investigation.
            </p>
          </div>

          <div className="network-visual">
            <div className="graph-node center-node">
              M
            </div>

            <div className="graph-node graph-user user-1">
              U
            </div>

            <div className="graph-node graph-user user-2">
              U
            </div>

            <div className="graph-node graph-user user-3">
              U
            </div>

            <div className="graph-node graph-user user-4">
              U
            </div>

            <span className="graph-line line-1" />
            <span className="graph-line line-2" />
            <span className="graph-line line-3" />
            <span className="graph-line line-4" />
          </div>
        </section>

        <section className="panel network-panel">
          <div className="panel-header">
            <div>
              <div className="panel-kicker">
                SUSPICIOUS NETWORK CANDIDATES
              </div>

              <h2>Highest-risk network components</h2>
            </div>

            <div className="queue-description">
              Top 50 candidates ranked by network risk score.
            </div>
          </div>

          <div className="filter-bar">
            <div className="search-box">
              <span>⌕</span>

              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search component or signal..."
              />
            </div>

            <select
              value={riskFilter}
              onChange={(event) =>
                setRiskFilter(event.target.value)
              }
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
              Loading network intelligence...
            </div>
          )}

          {error && (
            <div className="empty-state error-state">
              {error}
            </div>
          )}

          {!loading && !error && (
            <div className="network-grid">
              {filteredNetworks.map((network) => (
                <button
                  key={network.component_id}
                  className="network-card"
                  onClick={() => openNetwork(network)}
                >
                  <div className="network-card-top">
                    <div>
                      <div className="network-id">
                        NETWORK #{network.component_id}
                      </div>

                      <div className="network-title">
                        {network.user_count} users
                        <span>↔</span>
                        {network.merchant_count} merchants
                      </div>
                    </div>

                    <span
                      className={`risk-pill ${riskClass(
                        network.risk_band
                      )}`}
                    >
                      {network.risk_band}
                    </span>
                  </div>

                  <div className="network-score-row">
                    <span>Network risk</span>

                    <strong>
                      {network.network_risk_score.toFixed(2)}
                    </strong>
                  </div>

                  <div className="network-score-bar">
                    <span
                      style={{
                        width: `${Math.min(
                          network.network_risk_score,
                          100
                        )}%`,
                      }}
                    />
                  </div>

                  <div className="network-metrics">
                    <div>
                      <span>Transactions</span>
                      <strong>
                        {network.total_transactions}
                      </strong>
                    </div>

                    <div>
                      <span>Chargebacks</span>
                      <strong>
                        {network.total_chargebacks}
                      </strong>
                    </div>

                    <div>
                      <span>CB Rate</span>
                      <strong>
                        {formatPercent(
                          network.chargeback_rate
                        )}
                      </strong>
                    </div>
                  </div>

                  <div className="network-signals">
                    {network.signals
                      .split("|")
                      .slice(0, 3)
                      .map((signal) => (
                        <span key={signal}>
                          {formatSignal(signal)}
                        </span>
                      ))}
                  </div>

                  <div className="network-card-footer">
                    <span>
                      {formatAmount(network.total_amount)}
                    </span>

                    <span>
                      View network →
                    </span>
                  </div>
                </button>
              ))}
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
            className="investigation-drawer network-drawer"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="drawer-header">
              <div>
                <div className="panel-kicker">
                  NETWORK INVESTIGATION
                </div>

                <h2>
                  #{selected.component_id}
                </h2>

                <div className="drawer-entity-type">
                  USER ↔ MERCHANT COMPONENT
                </div>
              </div>

              <button
                className="close-button"
                onClick={() => setSelected(null)}
              >
                ×
              </button>
            </div>

            {detailLoading && (
              <div className="detail-loading">
                Loading network details...
              </div>
            )}

            <div className="drawer-risk">
              <div>
                <div className="drawer-label">
                  NETWORK RISK SCORE
                </div>

                <div className="drawer-score">
                  {selected.network_risk_score.toFixed(2)}
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

            <div className="network-detail-grid">
              <div>
                <span>USERS</span>
                <strong>
                  {selected.user_count}
                </strong>
              </div>

              <div>
                <span>MERCHANTS</span>
                <strong>
                  {selected.merchant_count}
                </strong>
              </div>

              <div>
                <span>TRANSACTIONS</span>
                <strong>
                  {selected.total_transactions}
                </strong>
              </div>

              <div>
                <span>VOLUME</span>
                <strong>
                  {formatAmount(
                    selected.total_amount
                  )}
                </strong>
              </div>

              <div>
                <span>CHARGEBACKS</span>
                <strong>
                  {selected.total_chargebacks}
                </strong>
              </div>

              <div>
                <span>CHARGEBACK RATE</span>
                <strong>
                  {formatPercent(
                    selected.chargeback_rate
                  )}
                </strong>
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">
                NETWORK STRUCTURE
              </div>

              <div className="network-structure">
                <div className="structure-center">
                  <div className="structure-merchant">
                    M
                  </div>

                  <span>
                    Merchant
                  </span>
                </div>

                <div className="structure-users">
                  {Array.from(
                    {
                      length: Math.min(
                        selected.user_count,
                        8
                      ),
                    },
                    (_, index) => (
                      <div
                        key={index}
                        className="structure-user"
                      >
                        U
                      </div>
                    )
                  )}
                </div>
              </div>

              <div className="structure-caption">
                {selected.user_count} users connected
                across {selected.merchant_count} merchant
                {selected.merchant_count !== 1
                  ? "s"
                  : ""}
                .
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">
                DETECTION SIGNALS
              </div>

              <div className="drawer-reasons">
                {selected.signals
                  .split("|")
                  .map((signal) => (
                    <div
                      className="drawer-reason"
                      key={signal}
                    >
                      <span className="reason-icon">
                        !
                      </span>

                      <span>
                        {formatSignal(signal)}
                      </span>
                    </div>
                  ))}
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">
                RELATIONSHIP INTELLIGENCE
              </div>

              <div className="relationship-box">
                <div>
                  <span>
                    Average relationship risk
                  </span>

                  <strong>
                    {selected.avg_relationship_risk.toFixed(
                      2
                    )}
                  </strong>
                </div>

                <div>
                  <span>
                    Maximum relationship risk
                  </span>

                  <strong>
                    {selected.max_relationship_risk.toFixed(
                      2
                    )}
                  </strong>
                </div>

                <div>
                  <span>
                    Shared merchants
                  </span>

                  <strong>
                    {selected.shared_merchant_count}
                  </strong>
                </div>

                <div>
                  <span>
                    Network density
                  </span>

                  <strong>
                    {(selected.network_density * 100).toFixed(
                      0
                    )}
                    %
                  </strong>
                </div>
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">
                INVESTIGATOR GUIDANCE
              </div>

              <div className="recommendation">
                <div className="recommendation-title">
                  Review linked entities
                </div>

                <p>
                  Examine the connected users, merchant
                  relationships, transaction behavior and
                  chargeback concentration before making a
                  final determination.
                </p>
              </div>
            </div>

            <div className="drawer-footer">
              A suspicious network is an investigative
              candidate, not proof of coordinated fraud.
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}
