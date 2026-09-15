"use client";

import Link from "next/link";
import { useState } from "react";

const API = "/api/backend";

type AnalysisRow = {
  label: string;
  value: number;
  transactions?: number;
  chargebacks?: number;
  risk_band?: string;
  network_risk_score?: number;
  chargeback_rate?: number;
  priority_rank?: number;
};

type AgentResponse = {
  question: string;
  intent: string;
  chart_type: string;
  title: string;
  analysis: {
    rows: AnalysisRow[];
    labels: string[];
    values: number[];
    unit: string;
    period?: string;
    metric?: string;
    secondary_metric?: string;
  };
  explanation: string;
  ai_routing: boolean;
  ai_explanation: boolean;
};

const suggestions = [
  // ============================================================
  // RISK INTELLIGENCE
  // ============================================================

  {
    label: "Highest-risk users",
    question: "Show me the highest-risk users",
    category: "Risk Intelligence",
  },
  {
    label: "Users needing investigation",
    question: "Which users need immediate investigation?",
    category: "Risk Intelligence",
  },
  {
    label: "Risk distribution",
    question: "Show me the risk distribution",
    category: "Risk Intelligence",
  },

  // ============================================================
  // MERCHANT INTELLIGENCE
  // ============================================================

  {
    label: "Highest chargeback category",
    question:
      "Which merchant category has the highest chargeback ratio this quarter?",
    category: "Merchant Intelligence",
  },
  {
    label: "Merchant chargeback rates",
    question:
      "Show me the merchant categories with the highest chargeback rates",
    category: "Merchant Intelligence",
  },

  // ============================================================
  // NETWORK INTELLIGENCE
  // ============================================================

  {
    label: "Most suspicious networks",
    question:
      "Show me the most suspicious transaction networks",
    category: "Network Intelligence",
  },
  {
    label: "Highest network risk",
    question:
      "Which suspicious networks have the highest risk scores?",
    category: "Network Intelligence",
  },
  {
    label: "Network chargeback rates",
    question:
      "Which networks have the highest chargeback rates?",
    category: "Network Intelligence",
  },

  // ============================================================
  // TRANSACTION INTELLIGENCE
  // ============================================================

  {
    label: "Transaction activity",
    question:
      "Show me transaction activity over time",
    category: "Transaction Intelligence",
  },
  {
    label: "Transaction status",
    question:
      "Show failed vs successful transactions",
    category: "Transaction Intelligence",
  },
  {
    label: "Chargeback trend",
    question:
      "Show me the chargeback trend",
    category: "Transaction Intelligence",
  },

  // ============================================================
  // INVESTIGATION OPERATIONS
  // ============================================================

  {
    label: "Investigation priority",
    question:
      "Show me the investigation priority queue",
    category: "Investigation Operations",
  },
  {
    label: "Cases to review first",
    question:
      "Which cases should investigators review first?",
    category: "Investigation Operations",
  },
];

// ============================================================
// VISUALIZATION COMPONENTS
// ============================================================

function formatChartValue(
  value: number,
  unit: string
) {
  if (!Number.isFinite(value)) {
    return "0";
  }

  const normalizedUnit =
    unit?.toLowerCase() || "";

  if (
    normalizedUnit.includes("percent") ||
    normalizedUnit.includes("%")
  ) {
    return `${value.toFixed(2)}%`;
  }

  if (Math.abs(value) >= 1_000_000) {
    return `${(
      value / 1_000_000
    ).toFixed(2)}M`;
  }

  if (Math.abs(value) >= 1_000) {
    return `${(
      value / 1_000
    ).toFixed(1)}K`;
  }

  if (Number.isInteger(value)) {
    return value.toLocaleString();
  }

  return value.toLocaleString(
    undefined,
    {
      maximumFractionDigits: 2,
    }
  );
}


// ============================================================
// BAR CHART
// ============================================================

function BarChart({
  rows,
  unit,
}: {
  rows: AnalysisRow[];
  unit: string;
}) {
  if (!rows.length) {
    return (
      <div className="empty-chart">
        No ranking data available.
      </div>
    );
  }

  const safeRows = rows.filter(
    (row) =>
      Number.isFinite(row.value)
  );

  if (!safeRows.length) {
    return (
      <div className="empty-chart">
        No valid chart values available.
      </div>
    );
  }

  const maxValue = Math.max(
    ...safeRows.map(
      (row) =>
        Math.max(
          Number(row.value) || 0,
          0
        )
    ),
    1
  );

  return (
    <div className="visual-chart bar-chart">
      {safeRows.map(
        (row, index) => {
          const numericValue =
            Math.max(
              Number(row.value) || 0,
              0
            );

          const width =
            Math.min(
              100,
              Math.max(
                3,
                (numericValue /
                  maxValue) *
                  100
              )
            );

          return (
            <div
              className="visual-bar-row"
              key={`${row.label}-${index}`}
            >
              <div
                className="visual-bar-label"
                title={row.label}
              >
                {row.label}
              </div>

              <div className="visual-bar-area">
                <div className="visual-bar-track">
                  <div
                    className="visual-bar-fill"
                    style={{
                      width: `${width}%`,
                    }}
                  />
                </div>
              </div>

              <div className="visual-bar-value">
                {formatChartValue(
                  numericValue,
                  unit
                )}
              </div>
            </div>
          );
        }
      )}
    </div>
  );
}


// ============================================================
// LINE CHART
// ============================================================

function LineChart({
  labels,
  values,
  unit,
}: {
  labels: string[];
  values: number[];
  unit: string;
}) {
  const safeValues =
    values.filter(
      (value) =>
        Number.isFinite(value)
    );

  if (!safeValues.length) {
    return (
      <div className="empty-chart">
        No trend data available.
      </div>
    );
  }

  const safeLabels =
    labels.length === values.length
      ? labels
      : safeValues.map(
          (_, index) =>
            `${index + 1}`
        );

  const width = 900;
  const height = 330;

  const paddingLeft = 62;
  const paddingRight = 28;
  const paddingTop = 28;
  const paddingBottom = 58;

  const chartWidth =
    width -
    paddingLeft -
    paddingRight;

  const chartHeight =
    height -
    paddingTop -
    paddingBottom;

  const maxValue =
    Math.max(
      ...safeValues,
      1
    );

  const minValue =
    Math.min(
      ...safeValues,
      0
    );

  const range =
    maxValue - minValue || 1;

  const points =
    safeValues.map(
      (value, index) => {
        const x =
          paddingLeft +
          (
            index /
            Math.max(
              safeValues.length - 1,
              1
            )
          ) *
            chartWidth;

        const y =
          paddingTop +
          chartHeight -
          (
            (value -
              minValue) /
            range
          ) *
            chartHeight;

        return {
          x,
          y,
          value,
        };
      }
    );

  const linePoints =
    points
      .map(
        (point) =>
          `${point.x},${point.y}`
      )
      .join(" ");

  const areaPoints = [
    `${paddingLeft},${
      paddingTop +
      chartHeight
    }`,
    ...points.map(
      (point) =>
        `${point.x},${point.y}`
    ),
    `${
      paddingLeft +
      chartWidth
    },${
      paddingTop +
      chartHeight
    }`,
  ].join(" ");

  const labelStep =
    Math.max(
      1,
      Math.ceil(
        safeLabels.length / 7
      )
    );

  const peak =
    Math.max(...safeValues);

  const total =
    safeValues.reduce(
      (sum, value) =>
        sum + value,
      0
    );

  return (
    <div className="line-chart-wrapper">
      <svg
        className="line-chart-svg"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        role="img"
        aria-label="Trend visualization"
      >
        {[0, 0.25, 0.5, 0.75, 1].map(
          (fraction) => {
            const y =
              paddingTop +
              chartHeight *
                fraction;

            return (
              <line
                key={`grid-${fraction}`}
                x1={paddingLeft}
                x2={
                  paddingLeft +
                  chartWidth
                }
                y1={y}
                y2={y}
                className="chart-grid-line"
              />
            );
          }
        )}

        {[0, 0.25, 0.5, 0.75, 1].map(
          (fraction) => {
            const value =
              maxValue -
              (
                maxValue -
                minValue
              ) *
                fraction;

            const y =
              paddingTop +
              chartHeight *
                fraction;

            return (
              <text
                key={`y-${fraction}`}
                x={paddingLeft - 10}
                y={y + 4}
                textAnchor="end"
                className="chart-axis-text"
              >
                {formatChartValue(
                  value,
                  unit
                )}
              </text>
            );
          }
        )}

        <polygon
          points={areaPoints}
          className="chart-area"
        />

        <polyline
          points={linePoints}
          fill="none"
          className="chart-line"
        />

        {points.map(
          (point, index) => (
            <circle
              key={`point-${index}`}
              cx={point.x}
              cy={point.y}
              r="4"
              className="chart-point"
            />
          )
        )}

        {safeLabels.map(
          (label, index) => {
            if (
              index % labelStep !== 0 &&
              index !==
                safeLabels.length - 1
            ) {
              return null;
            }

            const x =
              paddingLeft +
              (
                index /
                Math.max(
                  safeLabels.length - 1,
                  1
                )
              ) *
                chartWidth;

            return (
              <text
                key={`x-${label}-${index}`}
                x={x}
                y={
                  paddingTop +
                  chartHeight +
                  32
                }
                textAnchor="middle"
                className="chart-axis-text"
              >
                {label}
              </text>
            );
          }
        )}
      </svg>

      <div className="line-chart-summary">
        <span>
          {safeValues.length}{" "}
          {safeValues.length === 1
            ? "period"
            : "periods"}
        </span>

        <span>
          Peak:{" "}
          {formatChartValue(
            peak,
            unit
          )}
        </span>

        <span>
          Total:{" "}
          {formatChartValue(
            total,
            unit
          )}
        </span>
      </div>
    </div>
  );
}


// ============================================================
// DONUT CHART
// ============================================================

function DonutChart({
  rows,
}: {
  rows: AnalysisRow[];
}) {
  const safeRows =
    rows.filter(
      (row) =>
        Number.isFinite(
          row.value
        ) &&
        row.value >= 0
    );

  const total =
    safeRows.reduce(
      (sum, row) =>
        sum + row.value,
      0
    );

  if (
    !safeRows.length ||
    total <= 0
  ) {
    return (
      <div className="empty-chart">
        No distribution data available.
      </div>
    );
  }

  const radius = 82;

  const circumference =
    2 *
    Math.PI *
    radius;

  let accumulated = 0;

  return (
    <div className="donut-layout">
      <div className="donut-visual">
        <svg
          viewBox="0 0 220 220"
          className="donut-svg"
          role="img"
          aria-label="Distribution visualization"
        >
          <circle
            cx="110"
            cy="110"
            r={radius}
            className="donut-track"
          />

          {safeRows.map(
            (row, index) => {
              const percentage =
                row.value /
                total;

              const dash =
                percentage *
                circumference;

              const offset =
                -accumulated *
                circumference;

              accumulated +=
                percentage;

              return (
                <circle
                  key={`${row.label}-${index}`}
                  cx="110"
                  cy="110"
                  r={radius}
                  className={`donut-segment donut-segment-${
                    index % 5
                  }`}
                  strokeDasharray={`${dash} ${
                    circumference -
                    dash
                  }`}
                  strokeDashoffset={
                    offset
                  }
                  transform="rotate(-90 110 110)"
                />
              );
            }
          )}

          <text
            x="110"
            y="104"
            textAnchor="middle"
            className="donut-total"
          >
            {total.toLocaleString()}
          </text>

          <text
            x="110"
            y="124"
            textAnchor="middle"
            className="donut-caption"
          >
            TOTAL
          </text>
        </svg>
      </div>

      <div className="donut-legend">
        {safeRows.map(
          (row, index) => {
            const percentage =
              total > 0
                ? (
                    row.value /
                    total
                  ) *
                  100
                : 0;

            return (
              <div
                className="donut-legend-row"
                key={`${row.label}-${index}`}
              >
                <div className="donut-legend-left">
                  <span
                    className={`donut-dot donut-dot-${
                      index % 5
                    }`}
                  />

                  <span
                    title={row.label}
                  >
                    {row.label}
                  </span>
                </div>

                <div className="donut-legend-value">
                  <strong>
                    {row.value.toLocaleString()}
                  </strong>

                  <small>
                    {percentage.toFixed(
                      1
                    )}
                    %
                  </small>
                </div>
              </div>
            );
          }
        )}
      </div>
    </div>
  );
}


// ============================================================
// VISUALIZATION ROUTER
// ============================================================

function Visualization({
  chartType,
  rows,
  labels,
  values,
  unit,
  intent,
}: {
  chartType: string;
  rows: AnalysisRow[];
  labels: string[];
  values: number[];
  unit: string;
  intent: string;
}) {
  const normalizedType =
    (
      chartType || "bar"
    ).toLowerCase();

  const hasRows =
    Array.isArray(rows) &&
    rows.length > 0;

  const hasLineData =
    Array.isArray(values) &&
    values.length > 0;

  // Some backend versions keep network_risk_score in `value` while also
  // returning `chargeback_rate`. For a chargeback-rate question, the chart
  // must visualize the metric the investigator actually asked for.
  const isNetworkChargebackQuery =
    String(intent || "").toLowerCase() === "network_chargeback_rate";

  const chartRows = isNetworkChargebackQuery
    ? rows.map((row) => ({
        ...row,
        value:
          Number.isFinite(Number(row.chargeback_rate))
            ? Number(row.chargeback_rate) * 100
            : row.value,
      }))
    : rows;

  const chartUnit =
    isNetworkChargebackQuery
      ? "percent"
      : unit || "";

  if (
    !hasRows &&
    !hasLineData
  ) {
    return (
      <div className="empty-chart">
        No results available for this analysis.
      </div>
    );
  }

  if (
    normalizedType === "line" ||
    normalizedType === "trend"
  ) {
    return (
      <LineChart
        labels={labels || []}
        values={values || []}
        unit={chartUnit}
      />
    );
  }

  if (
    normalizedType === "donut" ||
    normalizedType === "pie"
  ) {
    return (
      <DonutChart
        rows={rows}
      />
    );
  }

  return (
    <BarChart
      rows={chartRows}
      unit={chartUnit}
    />
  );
}


export default function AIInvestigatorPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function investigate(customQuery?: string) {
    const question = (customQuery ?? query).trim();

    if (!question) return;

    setQuery(question);
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API}/agent/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail || `Investigation failed (${response.status})`
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "The intelligence backend could not be reached."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatValue(value: number, unit: string) {
    if (unit.includes("percent")) {
      return `${value.toFixed(2)}%`;
    }

    return value.toFixed(2);
  }

  const rows = result?.analysis?.rows ?? [];

  const displayUnit =
    result?.intent === "network_chargeback_rate"
      ? "percent"
      : result?.analysis?.unit || "";

  return (
    <main className="app-shell">

      {/* =====================================================
          SIDEBAR
      ===================================================== */}

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-mark">
            <span>U</span>
          </div>

          <div>
            <div className="brand-name">
              UPI SENTINEL
            </div>

            <div className="brand-subtitle">
              FRAUD INTELLIGENCE
            </div>
          </div>
        </div>

        <div className="nav-section">

          <div className="nav-title">
            MONITORING
          </div>

          <Link className="nav-item" href="/">
            ⌂ <span>Dashboard</span>
          </Link>

          <Link className="nav-item" href="/investigations">
            ⚠ <span>Investigations</span>
          </Link>

          <Link className="nav-item" href="/transactions">
            ↔ <span>Transactions</span>
          </Link>

          <Link className="nav-item" href="/users">
            ◉ <span>Users</span>
          </Link>

          <Link className="nav-item" href="/merchants">
            ▣ <span>Merchants</span>
          </Link>

          <Link className="nav-item" href="/networks">
            ⌁ <span>Networks</span>
          </Link>

        </div>

        <div className="nav-section">

          <div className="nav-title">
            INTELLIGENCE
          </div>

          <Link
            className="nav-item active"
            href="/ai-investigator"
          >
            ✦ <span>Sentinel AI Analyst</span>
            <span className="ai-badge">AI</span>
          </Link>

        </div>

        <div className="sidebar-status">
          <span className="status-dot" />
          <span>Sentinel Engine Online</span>
        </div>

      </aside>


      {/* =====================================================
          MAIN CONTENT
      ===================================================== */}

      <section className="main-content">

        {/* TOP BAR */}

        <header className="topbar">

          <div>

            <div className="breadcrumb">
              SENTINEL /{" "}
              <span>SENTINEL COPILOT</span>
            </div>

            <h1>
              Sentinel AI Analyst
            </h1>

          </div>

          <div className="topbar-status">
            <span className="status-dot" />
            AI ENGINE READY
          </div>

        </header>


        <div className="page-grid">

          <div className="section-card wide-card">

            {/* =================================================
                COPILOT HEADER
            ================================================= */}

            <div className="section-card-header">

              <div>

                <div className="section-eyebrow">
                  UPI SENTINEL · INTELLIGENCE ANALYST
                </div>

                <h2>
                  Ask the Sentinel Analyst
                </h2>

              </div>

              <span className="ai-badge">
                AI
              </span>

            </div>


            <p className="muted">
              Ask natural-language questions about UPI
              transactions, users, merchants, chargebacks
              and suspicious networks.
            </p>


            {/* =================================================
                INPUT
            ================================================= */}

            <div className="agent-input">

              <input
                value={query}
                onChange={(e) =>
                  setQuery(e.target.value)
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    investigate();
                  }
                }}
                placeholder="Ask about risk, merchants, networks or transactions..."
                disabled={loading}
              />

              <button
                className="primary-button"
                onClick={() => investigate()}
                disabled={
                  loading || !query.trim()
                }
              >
                {loading
                  ? "Analyzing..."
                  : "Analyze →"}
              </button>

            </div>


            {/* =================================================
                QUICK QUESTIONS
            ================================================= */}

            <div className="quick-questions">

              <div className="quick-section">

                <div className="quick-section-title">
                  RISK INTELLIGENCE
                </div>

                <div className="suggestion-grid">

                  {suggestions
                    .filter(
                      (item) =>
                        item.category ===
                        "Risk Intelligence"
                    )
                    .map((item) => (
                      <button
                        key={item.question}
                        className="suggestion"
                        onClick={() =>
                          investigate(item.question)
                        }
                        disabled={loading}
                        title={item.question}
                      >
                        {item.label}
                      </button>
                    ))}

                </div>

              </div>


              <div className="quick-section">

                <div className="quick-section-title">
                  MERCHANT INTELLIGENCE
                </div>

                <div className="suggestion-grid">

                  {suggestions
                    .filter(
                      (item) =>
                        item.category ===
                        "Merchant Intelligence"
                    )
                    .map((item) => (
                      <button
                        key={item.question}
                        className="suggestion"
                        onClick={() =>
                          investigate(item.question)
                        }
                        disabled={loading}
                        title={item.question}
                      >
                        {item.label}
                      </button>
                    ))}

                </div>

              </div>


              <div className="quick-section">

                <div className="quick-section-title">
                  NETWORK INTELLIGENCE
                </div>

                <div className="suggestion-grid">

                  {suggestions
                    .filter(
                      (item) =>
                        item.category ===
                        "Network Intelligence"
                    )
                    .map((item) => (
                      <button
                        key={item.question}
                        className="suggestion"
                        onClick={() =>
                          investigate(item.question)
                        }
                        disabled={loading}
                        title={item.question}
                      >
                        {item.label}
                      </button>
                    ))}

                </div>

              </div>


              <div className="quick-section">

                <div className="quick-section-title">
                  TRANSACTION INTELLIGENCE
                </div>

                <div className="suggestion-grid">

                  {suggestions
                    .filter(
                      (item) =>
                        item.category ===
                        "Transaction Intelligence"
                    )
                    .map((item) => (
                      <button
                        key={item.question}
                        className="suggestion"
                        onClick={() =>
                          investigate(item.question)
                        }
                        disabled={loading}
                        title={item.question}
                      >
                        {item.label}
                      </button>
                    ))}

                </div>

              </div>


              <div className="quick-section">

                <div className="quick-section-title">
                  INVESTIGATION OPERATIONS
                </div>

                <div className="suggestion-grid">

                  {suggestions
                    .filter(
                      (item) =>
                        item.category ===
                        "Investigation Operations"
                    )
                    .map((item) => (
                      <button
                        key={item.question}
                        className="suggestion"
                        onClick={() =>
                          investigate(item.question)
                        }
                        disabled={loading}
                        title={item.question}
                      >
                        {item.label}
                      </button>
                    ))}

                </div>

              </div>

            </div>


            {/* =================================================
                LOADING
            ================================================= */}

            {loading && (

              <div className="agent-loading">

                <div className="loading-pulse" />

                <div>

                  <strong>
                    Sentinel is analyzing...
                  </strong>

                  <p>
                    Understanding your question and
                    querying the intelligence layer.
                  </p>

                </div>

              </div>

            )}


            {/* =================================================
                ERROR
            ================================================= */}

            {error && (

              <div className="agent-error">

                <div className="section-eyebrow">
                  ANALYSIS ERROR
                </div>

                <p>
                  {error}
                </p>

              </div>

            )}


            {/* =================================================
                RESULTS
            ================================================= */}

            {result && !loading && (

              <div className="agent-results">

                {/* RESULT HEADER */}

                <div className="result-header">

                  <div>

                    <div className="section-eyebrow">
                      SENTINEL ANALYSIS
                    </div>

                    <h2>
                      {result.title}
                    </h2>

                    <p className="result-question">
                      “{result.question}”
                    </p>

                  </div>


                  <div className="result-badges">

                    {result.ai_routing && (
                      <span className="result-badge">
                        AI ROUTED
                      </span>
                    )}

                    {result.ai_explanation && (
                      <span className="result-badge">
                        AI ANALYSIS
                      </span>
                    )}

                  </div>

                </div>


                {/* =================================================
                    ANALYSIS META
                ================================================= */}

                <div className="analysis-meta">

                  <div>

                    <span>
                      INTENT
                    </span>

                    <strong>
                      {result.intent.replaceAll(
                        "_",
                        " "
                      )}
                    </strong>

                  </div>


                  <div>

                    <span>
                      VISUALIZATION
                    </span>

                    <strong>
                      {result.chart_type}
                    </strong>

                  </div>


                  {result.analysis.period && (
                    <div>

                      <span>
                        PERIOD
                      </span>

                      <strong>
                        {result.analysis.period}
                      </strong>

                    </div>
                  )}


                  <div>

                    <span>
                      RESULTS
                    </span>

                    <strong>
                      {rows.length}
                    </strong>

                  </div>

                </div>


                {/* =================================================
                    VISUAL ANALYSIS
                ================================================= */}

                <div className="chart-card">

                  <div className="chart-card-header">

                    <div>

                      <div className="section-eyebrow">
                        VISUAL ANALYSIS
                      </div>

                      <h3>
                        {result.title}
                      </h3>

                    </div>

                    <span className="chart-unit">
                      {displayUnit}
                    </span>

                  </div>


                  <Visualization
                    chartType={result.chart_type}
                    rows={rows}
                    labels={
                      result.analysis.labels || []
                    }
                    values={
                      result.analysis.values || []
                    }
                    unit={
                      result.analysis.unit || ""
                    }
                    intent={result.intent}
                  />

                </div>


                {/* =================================================
                    NETWORK SUPPORTING METRICS
                ================================================= */}

                {(
                  result.intent ===
                    "suspicious_networks" ||
                  result.intent ===
                    "network_chargeback_rate"
                ) &&
                  rows.length > 0 && (

                    <div className="network-evidence-grid">

                      <div className="network-metric">

                        <span>
                          PRIMARY METRIC
                        </span>

                        <strong>
                          Network Risk Score
                        </strong>

                        <small>
                          Bars represent network
                          risk score.
                        </small>

                      </div>


                      <div className="network-metric">

                        <span>
                          SUPPORTING SIGNAL
                        </span>

                        <strong>
                          Chargeback Rate
                        </strong>

                        <small>
                          Used as supporting
                          investigation evidence.
                        </small>

                      </div>


                      <div className="network-metric">

                        <span>
                          RISK BAND
                        </span>

                        <strong>
                          HIGH
                        </strong>

                        <small>
                          Review network evidence
                          before taking action.
                        </small>

                      </div>

                    </div>

                  )}


                {/* =================================================
                    INVESTIGATOR SUMMARY
                ================================================= */}

                <div className="agent-answer">

                  <div className="answer-heading">

                    <div>

                      <div className="section-eyebrow">
                        INVESTIGATOR SUMMARY
                      </div>

                      <h3>
                        What Sentinel found
                      </h3>

                    </div>

                    <span className="insight-icon">
                      ✦
                    </span>

                  </div>


                  <p className="explanation">
                    {result.explanation}
                  </p>

                </div>


                {/* =================================================
                    EVIDENCE
                ================================================= */}

                {rows.length > 0 && (

                  <div className="evidence-card">

                    <div className="section-eyebrow">
                      EVIDENCE
                    </div>


                    <div className="evidence-list">

                      {rows
                        .slice(0, 5)
                        .map(
                          (row, index) => (

                            <div
                              className="evidence-row"
                              key={`evidence-${row.label}-${index}`}
                            >

                              <div className="evidence-rank">
                                #{index + 1}
                              </div>


                              <div className="evidence-main">

                                <strong>
                                  {row.label}
                                </strong>


                                <span>

                                  {row.transactions !==
                                    undefined &&
                                    `${row.transactions} transactions`}

                                  {row.chargebacks !==
                                    undefined &&
                                    ` · ${row.chargebacks} chargeback${
                                      row.chargebacks ===
                                      1
                                        ? ""
                                        : "s"
                                    }`}

                                  {row.risk_band &&
                                    ` · ${row.risk_band}`}

                                  {row.network_risk_score !==
                                    undefined &&
                                    ` · Network risk ${row.network_risk_score}`}

                                  {row.chargeback_rate !==
                                    undefined &&
                                    ` · Chargeback ${row.chargeback_rate}%`}

                                </span>

                              </div>


                              <div className="evidence-value">

                                {formatValue(
                                  row.value,
                                  result.analysis.unit
                                )}

                              </div>

                            </div>

                          )
                        )}

                    </div>

                  </div>

                )}


                {/* =================================================
                    DISCLAIMER
                ================================================= */}

                <div className="investigator-disclaimer">

                  <span>
                    ⓘ
                  </span>

                  <p>
                    Risk scores and network signals are
                    investigative indicators, not proof of
                    fraud. Review supporting transaction
                    and entity evidence before taking
                    action.
                  </p>

                </div>

              </div>

            )}

          </div>

        </div>

      </section>


      {/* =======================================================
          STYLES
      ======================================================= */}

      <style jsx>{`

        .topbar-status {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 10px;
          letter-spacing: 0.12em;
          color: rgba(255, 255, 255, 0.5);
        }


        .status-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #48d597;
          display: inline-block;
          box-shadow:
            0 0 10px rgba(72, 213, 151, 0.55);
        }


        .sidebar-status {
          margin-top: auto;
          padding: 14px 16px;
          border:
            1px solid rgba(255, 255, 255, 0.07);
          border-radius: 10px;
          display: flex;
          align-items: center;
          gap: 9px;
          font-size: 10px;
          color: rgba(255, 255, 255, 0.42);
          letter-spacing: 0.05em;
        }


        /* =====================================================
           QUICK QUESTIONS
        ===================================================== */

        .quick-questions {
          margin-top: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }


        .quick-section {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }


        .quick-section-title {
          font-size: 8px;
          font-weight: 700;
          letter-spacing: 0.12em;
          color: rgba(255, 255, 255, 0.28);
        }


        .suggestion-grid {
          display: grid;
          grid-template-columns:
            repeat(2, minmax(0, 1fr));
          gap: 8px;
        }


        .suggestion {
          padding: 11px 13px;
          border:
            1px solid rgba(255, 255, 255, 0.07);
          border-radius: 9px;
          background:
            rgba(255, 255, 255, 0.018);
          color: rgba(255, 255, 255, 0.58);
          font-size: 11px;
          text-align: left;
          cursor: pointer;
          transition:
            border-color 160ms ease,
            background 160ms ease,
            color 160ms ease,
            transform 160ms ease;
        }


        .suggestion:hover {
          border-color:
            rgba(72, 213, 151, 0.28);
          background:
            rgba(72, 213, 151, 0.045);
          color: #78e3b0;
          transform: translateY(-1px);
        }


        .suggestion:disabled {
          opacity: 0.45;
          cursor: not-allowed;
          transform: none;
        }


        /* =====================================================
           LOADING
        ===================================================== */

        .agent-loading {
          margin-top: 24px;
          padding: 18px;
          border:
            1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          display: flex;
          gap: 14px;
          align-items: center;
          background:
            rgba(255, 255, 255, 0.02);
        }


        .loading-pulse {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #48d597;
          box-shadow:
            0 0 18px rgba(72, 213, 151, 0.8);
          animation: pulse 1.2s infinite;
        }


        .agent-loading strong {
          font-size: 13px;
        }


        .agent-loading p {
          margin: 4px 0 0;
          color:
            rgba(255, 255, 255, 0.45);
          font-size: 12px;
        }


        /* =====================================================
           ERROR
        ===================================================== */

        .agent-error {
          margin-top: 24px;
          padding: 18px;
          border:
            1px solid rgba(255, 100, 100, 0.2);
          border-radius: 12px;
          background:
            rgba(255, 70, 70, 0.05);
        }


        .agent-error p {
          margin: 8px 0 0;
          color:
            rgba(255, 255, 255, 0.65);
          font-size: 13px;
        }


        /* =====================================================
           RESULTS
        ===================================================== */

        .agent-results {
          margin-top: 30px;
        }


        .result-header {
          display: flex;
          justify-content: space-between;
          gap: 20px;
          align-items: flex-start;
        }


        .result-header h2 {
          margin: 5px 0 6px;
        }


        .result-question {
          margin: 0;
          color:
            rgba(255, 255, 255, 0.42);
          font-size: 12px;
        }


        .result-badges {
          display: flex;
          gap: 7px;
          flex-wrap: wrap;
          justify-content: flex-end;
        }


        .result-badge {
          padding: 6px 9px;
          border:
            1px solid rgba(72, 213, 151, 0.22);
          border-radius: 999px;
          color: #78e3b0;
          font-size: 9px;
          letter-spacing: 0.08em;
          white-space: nowrap;
        }


        /* =====================================================
           META
        ===================================================== */

        .analysis-meta {
          display: grid;
          grid-template-columns:
            repeat(4, 1fr);
          gap: 10px;
          margin-top: 22px;
        }


        .analysis-meta > div {
          padding: 13px 14px;
          border:
            1px solid rgba(255, 255, 255, 0.07);
          border-radius: 10px;
          background:
            rgba(255, 255, 255, 0.018);
        }


        .analysis-meta span {
          display: block;
          font-size: 8px;
          letter-spacing: 0.1em;
          color:
            rgba(255, 255, 255, 0.32);
          margin-bottom: 6px;
        }


        .analysis-meta strong {
          font-size: 12px;
          text-transform: capitalize;
          color:
            rgba(255, 255, 255, 0.75);
        }


        /* =====================================================
           REAL VISUALIZATION SYSTEM
        ===================================================== */

        .visual-chart {
          width: 100%;
          margin-top: 24px;
        }

        /* =====================================================
           BAR CHART
        ===================================================== */

        .bar-chart {
          width: 100%;
        }

        .visual-bar-row {
          display: grid;
          grid-template-columns:
            minmax(120px, 170px)
            minmax(0, 1fr)
            90px;
          align-items: center;
          gap: 14px;
          margin-bottom: 14px;
        }

        .visual-bar-row:last-child {
          margin-bottom: 0;
        }

        .visual-bar-label {
          min-width: 0;
          font-size: 11px;
          color: rgba(255, 255, 255, 0.62);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .visual-bar-area {
          width: 100%;
          min-width: 0;
        }

        .visual-bar-track {
          width: 100%;
          height: 14px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.055);
          overflow: hidden;
        }

        .visual-bar-fill {
          height: 100%;
          min-width: 3px;
          border-radius: inherit;
          background: linear-gradient(
            90deg,
            #48d597,
            #67e0b0
          );
          box-shadow:
            0 0 16px
            rgba(72, 213, 151, 0.22);
          transition:
            width 600ms ease;
        }

        .visual-bar-value {
          text-align: right;
          font-size: 11px;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.78);
          white-space: nowrap;
        }


        /* =====================================================
           LINE CHART
        ===================================================== */

        .line-chart-wrapper {
          width: 100%;
          margin-top: 22px;
        }

        .line-chart-svg {
          width: 100%;
          height: 330px;
          display: block;
          overflow: visible;
        }

        .chart-grid-line {
          stroke: rgba(255, 255, 255, 0.07);
          stroke-width: 1;
        }

        .chart-axis-text {
          fill: rgba(255, 255, 255, 0.35);
          font-size: 10px;
        }

        .chart-line {
          stroke: #48d597;
          stroke-width: 3;
          stroke-linecap: round;
          stroke-linejoin: round;
          filter:
            drop-shadow(
              0 0 7px
              rgba(72, 213, 151, 0.35)
            );
        }

        .chart-point {
          fill: #48d597;
          stroke: rgba(255, 255, 255, 0.9);
          stroke-width: 2;
          transition:
            r 150ms ease;
        }

        .chart-area {
          fill: rgba(72, 213, 151, 0.055);
        }

        .line-chart-summary {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 15px;
          margin-top: 9px;
          font-size: 10px;
          color: rgba(255, 255, 255, 0.35);
        }


        /* =====================================================
           DONUT CHART
        ===================================================== */

        .donut-layout {
          width: 100%;
          margin-top: 20px;
          display: grid;
          grid-template-columns:
            280px
            minmax(0, 1fr);
          gap: 35px;
          align-items: center;
        }

        .donut-visual {
          display: flex;
          justify-content: center;
          align-items: center;
        }

        .donut-svg {
          width: 230px;
          height: 230px;
          overflow: visible;
        }

        .donut-track {
          fill: none;
          stroke: rgba(255, 255, 255, 0.06);
          stroke-width: 24;
        }

        .donut-segment {
          fill: none;
          stroke-width: 24;
          stroke-linecap: butt;
          transition:
            opacity 180ms ease;
        }

        .donut-segment:hover {
          opacity: 0.82;
        }

        .donut-segment-0 {
          stroke: #48d597;
        }

        .donut-segment-1 {
          stroke: #67e0b0;
        }

        .donut-segment-2 {
          stroke: #b4efd5;
        }

        .donut-segment-3 {
          stroke: #6ba88d;
        }

        .donut-segment-4 {
          stroke: #d1f5e5;
        }

        .donut-total {
          fill: rgba(255, 255, 255, 0.88);
          font-size: 23px;
          font-weight: 700;
        }

        .donut-caption {
          fill: rgba(255, 255, 255, 0.3);
          font-size: 8px;
          letter-spacing: 0.15em;
        }

        .donut-legend {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        .donut-legend-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 15px;
          padding-bottom: 12px;
          border-bottom:
            1px solid
            rgba(255, 255, 255, 0.055);
        }

        .donut-legend-row:last-child {
          border-bottom: 0;
          padding-bottom: 0;
        }

        .donut-legend-left {
          min-width: 0;
          display: flex;
          align-items: center;
          gap: 9px;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.62);
        }

        .donut-legend-left span:last-child {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .donut-dot {
          width: 8px;
          height: 8px;
          flex-shrink: 0;
          border-radius: 50%;
        }

        .donut-dot-0 {
          background: #48d597;
        }

        .donut-dot-1 {
          background: #67e0b0;
        }

        .donut-dot-2 {
          background: #b4efd5;
        }

        .donut-dot-3 {
          background: #6ba88d;
        }

        .donut-dot-4 {
          background: #d1f5e5;
        }

        .donut-legend-value {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 10px;
          flex-shrink: 0;
        }

        .donut-legend-value strong {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.78);
        }

        .donut-legend-value small {
          min-width: 42px;
          text-align: right;
          font-size: 10px;
          color: rgba(255, 255, 255, 0.32);
        }


        /* =====================================================
           EMPTY CHART
        ===================================================== */

        .empty-chart {
          width: 100%;
          margin-top: 20px;
          padding: 35px 20px;
          text-align: center;
          border:
            1px dashed
            rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          color: rgba(255, 255, 255, 0.35);
          font-size: 12px;
        }


        /* =====================================================
           CHART RESPONSIVE
        ===================================================== */

        @media (max-width: 900px) {

          .visual-bar-row {
            grid-template-columns:
              110px
              minmax(0, 1fr)
              75px;
            gap: 10px;
          }

          .donut-layout {
            grid-template-columns: 1fr;
            gap: 25px;
          }

          .donut-visual {
            justify-content: flex-start;
          }

          .line-chart-summary {
            flex-wrap: wrap;
          }

        }

        @media (max-width: 600px) {

          .visual-bar-row {
            grid-template-columns:
              90px
              minmax(0, 1fr)
              65px;
            gap: 8px;
          }

          .visual-bar-label {
            font-size: 10px;
          }

          .visual-bar-value {
            font-size: 10px;
          }

          .visual-bar-track {
            height: 12px;
          }

          .line-chart-svg {
            height: 260px;
          }

          .donut-svg {
            width: 200px;
            height: 200px;
          }

          .donut-layout {
            gap: 20px;
          }

        }


        /* =====================================================
           NETWORK METRICS
        ===================================================== */

        .network-evidence-grid {
          display: grid;
          grid-template-columns:
            repeat(3, 1fr);
          gap: 10px;
          margin-top: 14px;
        }


        .network-metric {
          padding: 14px;
          border:
            1px solid rgba(255, 255, 255, 0.07);
          border-radius: 10px;
          background:
            rgba(255, 255, 255, 0.018);
        }


        .network-metric span {
          display: block;
          font-size: 8px;
          letter-spacing: 0.1em;
          color:
            rgba(255, 255, 255, 0.3);
          margin-bottom: 7px;
        }


        .network-metric strong {
          display: block;
          font-size: 12px;
          color:
            rgba(255, 255, 255, 0.72);
        }


        .network-metric small {
          display: block;
          margin-top: 5px;
          font-size: 9px;
          line-height: 1.5;
          color:
            rgba(255, 255, 255, 0.32);
        }


        /* =====================================================
           AI ANSWER
        ===================================================== */

        .agent-answer {
          margin-top: 14px;
          padding: 20px;
          border:
            1px solid rgba(72, 213, 151, 0.13);
          border-radius: 12px;
          background:
            rgba(72, 213, 151, 0.025);
        }


        .answer-heading {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }


        .answer-heading h3 {
          margin: 5px 0 0;
          font-size: 14px;
        }


        .insight-icon {
          width: 28px;
          height: 28px;
          border-radius: 8px;
          display: grid;
          place-items: center;
          background:
            rgba(72, 213, 151, 0.08);
          color: #78e3b0;
        }


        .explanation {
          margin: 16px 0 0;
          line-height: 1.7;
          font-size: 13px;
          color:
            rgba(255, 255, 255, 0.67);
        }


        /* =====================================================
           EVIDENCE
        ===================================================== */

        .evidence-card {
          margin-top: 14px;
          padding: 20px;
          border:
            1px solid rgba(255, 255, 255, 0.07);
          border-radius: 12px;
        }


        .evidence-list {
          margin-top: 12px;
        }


        .evidence-row {
          display: grid;
          grid-template-columns:
            42px 1fr auto;
          gap: 12px;
          align-items: center;
          padding: 13px 0;
          border-top:
            1px solid rgba(255, 255, 255, 0.055);
        }


        .evidence-rank {
          font-size: 10px;
          color:
            rgba(255, 255, 255, 0.3);
        }


        .evidence-main {
          display: flex;
          flex-direction: column;
          gap: 4px;
          min-width: 0;
        }


        .evidence-main strong {
          font-size: 12px;
          color:
            rgba(255, 255, 255, 0.72);
        }


        .evidence-main span {
          font-size: 10px;
          color:
            rgba(255, 255, 255, 0.35);
          line-height: 1.5;
        }


        .evidence-value {
          font-size: 12px;
          font-weight: 600;
          color: #78e3b0;
        }


        /* =====================================================
           DISCLAIMER
        ===================================================== */

        .investigator-disclaimer {
          margin-top: 14px;
          padding: 12px 14px;
          border-radius: 9px;
          background:
            rgba(255, 255, 255, 0.025);
          display: flex;
          gap: 10px;
          align-items: flex-start;
        }


        .investigator-disclaimer span {
          color:
            rgba(255, 255, 255, 0.35);
          font-size: 12px;
        }


        .investigator-disclaimer p {
          margin: 0;
          font-size: 10px;
          line-height: 1.6;
          color:
            rgba(255, 255, 255, 0.35);
        }


        /* =====================================================
           BUTTON / INPUT STATES
        ===================================================== */

        .agent-input input:disabled {
          opacity: 0.65;
        }


        .primary-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }


        /* =====================================================
           ANIMATION
        ===================================================== */

        @keyframes pulse {

          0%,
          100% {
            transform: scale(0.8);
            opacity: 0.55;
          }

          50% {
            transform: scale(1.2);
            opacity: 1;
          }

        }


        /* =====================================================
           RESPONSIVE
        ===================================================== */

        @media (max-width: 800px) {

          .analysis-meta {
            grid-template-columns:
              repeat(2, 1fr);
          }


          .network-evidence-grid {
            grid-template-columns: 1fr;
          }


          .result-header {
            flex-direction: column;
          }


          .result-badges {
            justify-content: flex-start;
          }

        }


        @media (max-width: 600px) {

          .suggestion-grid {
            grid-template-columns: 1fr;
          }


          .analysis-meta {
            grid-template-columns: 1fr;
          }


          .chart-card-header {
            align-items: flex-start;
            flex-direction: column;
          }

        }

      `}</style>

    </main>
  );
}