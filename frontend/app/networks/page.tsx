"use client";

import Link from "next/link";
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
  const value = String(band || "").toUpperCase();
  if (value === "CRITICAL") return "risk-critical";
  if (value === "HIGH") return "risk-high";
  if (value === "MEDIUM") return "risk-medium";
  return "risk-low";
}

function formatSignal(signal: string) {
  return signal
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatAmount(amount: number) {
  if (!Number.isFinite(amount)) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatPercent(value: number) {
  if (!Number.isFinite(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function scoreValue(value: number) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(2) : "—";
}

function clampPercent(value: number) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.min(Math.max(numeric, 0), 100);
}

function signalList(value?: string) {
  return String(value || "")
    .split("|")
    .map((signal) => signal.trim())
    .filter(Boolean);
}

export default function NetworksPage() {
  const [networks, setNetworks] = useState<Network[]>([]);
  const [selected, setSelected] = useState<Network | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [apiOnline, setApiOnline] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    async function loadNetworks() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(`${API}/networks`, {
          cache: "no-store",
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Network API failed: ${response.status}`);
        }

        const data = await response.json();

        const items = Array.isArray(data)
          ? data
          : Array.isArray(data?.networks)
            ? data.networks
            : Array.isArray(data?.data)
              ? data.data
              : [];

        setNetworks(items);
        setApiOnline(true);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;

        console.error(err);
        setApiOnline(false);
        setError("Unable to load network intelligence.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadNetworks();

    return () => controller.abort();
  }, []);

  async function openNetwork(network: Network) {
    setSelected(network);
    setDetailLoading(true);

    try {
      const response = await fetch(`${API}/networks/${network.component_id}`, {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Network detail API failed: ${response.status}`);
      }

      const detail = await response.json();
      const normalized = detail?.network ?? detail?.data ?? detail;

      if (normalized && typeof normalized === "object") {
        setSelected(normalized as Network);
      }
    } catch (err) {
      console.error(err);
      // Keep the summary card visible if the detail endpoint fails.
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
        String(network.risk_band || "").toLowerCase().includes(query) ||
        String(network.signals || "").toLowerCase().includes(query);

      const matchesRisk =
        riskFilter === "ALL" ||
        String(network.risk_band || "").toUpperCase() === riskFilter;

      return matchesSearch && matchesRisk;
    });
  }, [networks, search, riskFilter]);

  const candidateCount = networks.length;

  const highRisk = networks.filter(
    (network) => String(network.risk_band || "").toUpperCase() === "HIGH"
  ).length;

  const criticalRisk = networks.filter(
    (network) => String(network.risk_band || "").toUpperCase() === "CRITICAL"
  ).length;

  const totalChargebacks = networks.reduce(
    (sum, network) => sum + (Number(network.total_chargebacks) || 0),
    0
  );

  const totalVolume = networks.reduce(
    (sum, network) => sum + (Number(network.total_amount) || 0),
    0
  );

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
          <Link href="/" className="nav-item">
            <span>⌂</span>
            Dashboard
          </Link>

          <Link href="/investigations" className="nav-item">
            <span>⌕</span>
            Investigations
          </Link>

          <Link href="/transactions" className="nav-item">
            <span>⇄</span>
            Transactions
          </Link>

          <Link href="/users" className="nav-item">
            <span>◎</span>
            Users
          </Link>

          <Link href="/merchants" className="nav-item">
            <span>▣</span>
            Merchants
          </Link>

          <Link href="/networks" className="nav-item active">
            <span>⌘</span>
            Networks
          </Link>

          <div className="nav-section-title">INTELLIGENCE</div>

          <Link href="/ai-investigator" className="nav-item">
            <span>✦</span>
            AI Investigator
            <span className="ai-badge">AI</span>
          </Link>
        </nav>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className={`status-dot ${apiOnline ? "" : "offline"}`} />
            {apiOnline ? "Intelligence Engine Online" : "Intelligence Engine Offline"}
          </div>

          <div className="version">UPI Sentinel v0.2.0</div>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">GRAPH INTELLIGENCE</div>

            <h1>Network Intelligence</h1>

            <p>
              Detect suspicious relationships across users and merchants.
            </p>
          </div>

          <div className="topbar-status">
            <span className={`status-dot ${apiOnline ? "" : "offline"}`} />
            {loading
              ? "Loading network data"
              : apiOnline
                ? "API Connected"
                : "API Offline"}
          </div>
        </header>

        <section className="stats-grid network-stats">
          <div className="stat-card">
            <div className="stat-label">DISPLAYED CANDIDATES</div>
            <div className="stat-value">{candidateCount.toLocaleString("en-IN")}</div>
            <div className="stat-meta">Returned by current API view</div>
          </div>

          <div className="stat-card">
            <div className="stat-label">HIGH / CRITICAL</div>
            <div className="stat-value">
              {(highRisk + criticalRisk).toLocaleString("en-IN")}
            </div>
            <div className="stat-meta">
              {highRisk} high · {criticalRisk} critical
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-label">NETWORK CHARGEBACKS</div>
            <div className="stat-value">
              {totalChargebacks.toLocaleString("en-IN")}
            </div>
            <div className="stat-meta">Across displayed networks</div>
          </div>

          <div className="stat-card">
            <div className="stat-label">DISPLAYED VOLUME</div>
            <div className="stat-value network-money">
              {formatAmount(totalVolume)}
            </div>
            <div className="stat-meta">Across returned candidates</div>
          </div>
        </section>

        <section className="network-hero">
          <div className="network-hero-copy">
            <div className="panel-kicker">USER ↔ MERCHANT GRAPH</div>

            <h2>Map suspicious relationship clusters</h2>

            <p>
              UPI Sentinel connects transaction participants into a graph and
              prioritizes dense or chargeback-heavy components for investigation.
            </p>
          </div>

          <div className="network-visual" aria-label="Illustration of users connected to a merchant">
            <div className="graph-orbit orbit-one" />
            <div className="graph-orbit orbit-two" />

            <span className="graph-line line-1" />
            <span className="graph-line line-2" />
            <span className="graph-line line-3" />
            <span className="graph-line line-4" />
            <span className="graph-line line-5" />
            <span className="graph-line line-6" />

            <div className="graph-node center-node" title="Merchant">
              M
            </div>

            <div className="graph-node graph-user user-1" title="User">
              U
            </div>

            <div className="graph-node graph-user user-2" title="User">
              U
            </div>

            <div className="graph-node graph-user user-3" title="User">
              U
            </div>

            <div className="graph-node graph-user user-4" title="User">
              U
            </div>

            <div className="graph-node graph-user user-5" title="User">
              U
            </div>

            <div className="graph-node graph-user user-6" title="User">
              U
            </div>

            <div className="graph-label merchant-label">MERCHANT</div>
            <div className="graph-label user-label">CONNECTED USERS</div>
            <div className="graph-caption">Relationship pattern</div>
          </div>
        </section>

        <section className="panel network-panel">
          <div className="panel-header">
            <div>
              <div className="panel-kicker">SUSPICIOUS NETWORK CANDIDATES</div>
              <h2>Highest-risk network components</h2>
            </div>

            <div className="queue-description">
              Candidates ranked by network risk score.
            </div>
          </div>

          <div className="filter-bar">
            <div className="search-box">
              <span>⌕</span>

              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search component or signal..."
                aria-label="Search networks"
              />
            </div>

            <select
              value={riskFilter}
              onChange={(event) => setRiskFilter(event.target.value)}
              aria-label="Filter networks by risk"
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

          {!loading && error && (
            <div className="empty-state error-state">{error}</div>
          )}

          {!loading && !error && filteredNetworks.length === 0 && (
            <div className="empty-state">
              No network candidates match the current filters.
            </div>
          )}

          {!loading && !error && filteredNetworks.length > 0 && (
            <div className="network-grid">
              {filteredNetworks.map((network) => (
                <button
                  key={network.component_id}
                  type="button"
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

                    <span className={`risk-pill ${riskClass(network.risk_band)}`}>
                      {network.risk_band || "LOW"}
                    </span>
                  </div>

                  <div className="network-score-row">
                    <span>Network risk</span>
                    <strong>{scoreValue(network.network_risk_score)}</strong>
                  </div>

                  <div className="network-score-bar">
                    <span
                      style={{
                        width: `${clampPercent(network.network_risk_score)}%`,
                      }}
                    />
                  </div>

                  <div className="network-metrics">
                    <div>
                      <span>Transactions</span>
                      <strong>{network.total_transactions ?? "—"}</strong>
                    </div>

                    <div>
                      <span>Chargebacks</span>
                      <strong>{network.total_chargebacks ?? "—"}</strong>
                    </div>

                    <div>
                      <span>CB Rate</span>
                      <strong>{formatPercent(network.chargeback_rate)}</strong>
                    </div>
                  </div>

                  <div className="network-signals">
                    {signalList(network.signals).slice(0, 3).map((signal) => (
                      <span key={signal}>{formatSignal(signal)}</span>
                    ))}
                  </div>

                  <div className="network-card-footer">
                    <span>{formatAmount(network.total_amount)}</span>
                    <span>View network →</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>
      </section>

      {selected && (
        <div className="drawer-backdrop" onClick={() => setSelected(null)}>
          <aside
            className="investigation-drawer network-drawer"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="drawer-header">
              <div>
                <div className="panel-kicker">NETWORK INVESTIGATION</div>
                <h2>#{selected.component_id}</h2>
                <div className="drawer-entity-type">
                  USER ↔ MERCHANT COMPONENT
                </div>
              </div>

              <button
                type="button"
                className="close-button"
                onClick={() => setSelected(null)}
                aria-label="Close network details"
              >
                ×
              </button>
            </div>

            {detailLoading && (
              <div className="detail-loading">Loading network details...</div>
            )}

            <div className="drawer-risk">
              <div>
                <div className="drawer-label">NETWORK RISK SCORE</div>
                <div className="drawer-score">
                  {scoreValue(selected.network_risk_score)}
                </div>
              </div>

              <span className={`risk-pill large ${riskClass(selected.risk_band)}`}>
                {selected.risk_band || "LOW"}
              </span>
            </div>

            <div className="network-detail-grid">
              <div>
                <span>USERS</span>
                <strong>{selected.user_count ?? "—"}</strong>
              </div>

              <div>
                <span>MERCHANTS</span>
                <strong>{selected.merchant_count ?? "—"}</strong>
              </div>

              <div>
                <span>TRANSACTIONS</span>
                <strong>{selected.total_transactions ?? "—"}</strong>
              </div>

              <div>
                <span>VOLUME</span>
                <strong>{formatAmount(selected.total_amount)}</strong>
              </div>

              <div>
                <span>CHARGEBACKS</span>
                <strong>{selected.total_chargebacks ?? "—"}</strong>
              </div>

              <div>
                <span>CHARGEBACK RATE</span>
                <strong>{formatPercent(selected.chargeback_rate)}</strong>
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">NETWORK STRUCTURE</div>

              <div className="network-structure">
                <div className="structure-center">
                  <div className="structure-merchant">M</div>
                  <span>Merchant</span>
                </div>

                <div className="structure-users">
                  {Array.from(
                    { length: Math.min(Math.max(selected.user_count || 0, 0), 8) },
                    (_, index) => (
                      <div key={index} className="structure-user">
                        U
                      </div>
                    )
                  )}
                </div>
              </div>

              <div className="structure-caption">
                {selected.user_count ?? 0} users connected across{" "}
                {selected.merchant_count ?? 0} merchant
                {(selected.merchant_count ?? 0) !== 1 ? "s" : ""}.
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">DETECTION SIGNALS</div>

              <div className="drawer-reasons">
                {signalList(selected.signals).length === 0 ? (
                  <div className="drawer-reason">
                    <span className="reason-icon">i</span>
                    <span>No detection signals returned.</span>
                  </div>
                ) : (
                  signalList(selected.signals).map((signal) => (
                    <div className="drawer-reason" key={signal}>
                      <span className="reason-icon">!</span>
                      <span>{formatSignal(signal)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">
                RELATIONSHIP INTELLIGENCE
              </div>

              <div className="relationship-box">
                <div>
                  <span>Average relationship risk</span>
                  <strong>{scoreValue(selected.avg_relationship_risk)}</strong>
                </div>

                <div>
                  <span>Maximum relationship risk</span>
                  <strong>{scoreValue(selected.max_relationship_risk)}</strong>
                </div>

                <div>
                  <span>Shared merchants</span>
                  <strong>{selected.shared_merchant_count ?? "—"}</strong>
                </div>

                <div>
                  <span>Network density</span>
                  <strong>{formatPercent(selected.network_density)}</strong>
                </div>

                <div>
                  <span>Max shared users / merchant</span>
                  <strong>{selected.max_shared_users_per_merchant ?? "—"}</strong>
                </div>
              </div>
            </div>

            <div className="drawer-section">
              <div className="drawer-section-title">INVESTIGATOR GUIDANCE</div>

              <div className="recommendation">
                <div className="recommendation-title">Review linked entities</div>

                <p>
                  Examine the connected users, merchant relationships,
                  transaction behavior and chargeback concentration before
                  making a final determination.
                </p>
              </div>
            </div>

            <div className="drawer-footer">
              A suspicious network is an investigative candidate, not proof
              of coordinated fraud.
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}
