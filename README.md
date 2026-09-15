# 🛡️ UPI Sentinel
### AI-Powered UPI Fraud & Merchant Intelligence Platform

> **Clean It. Analyze It. Visualize It. Ask It.**

UPI Sentinel is an end-to-end fraud-intelligence platform designed for financial investigators, risk teams, and merchant operations.

It transforms messy UPI transaction, KYC, merchant, and chargeback data into a governed intelligence layer that helps investigators identify high-risk entities, uncover suspicious user–merchant networks, detect anomalies, understand merchant risk, and ask natural-language questions about the data.

**Hackathon:** TransOrg AgentIQ Datathon 2026  
**Track:** FinTech & BFSI — UPI Fraud Ring & Merchant Analytics  
**Team:** Data Ninjas

---

## 🌐 Live Demo

### 🚀 https://upi-sentinel-ruby.vercel.app/

**Frontend:** Vercel  
**Backend:** FastAPI on Render

> The backend is deployed on a free-tier service, so the first request after inactivity may take a few seconds while the service wakes up.

---

# 🎯 The Problem

UPI fraud investigations rarely fail because there is no data.

They fail because the data is:

- fragmented across multiple sources
- inconsistent and incomplete
- difficult to join reliably
- full of duplicate and invalid records
- difficult to investigate at network level
- too large for manual analysis
- disconnected from the investigator's natural-language workflow

A transaction viewed in isolation may look harmless.

A group of users repeatedly connected to the same merchant, combined with abnormal behavior and concentrated chargebacks, can tell a very different story.

**UPI Sentinel is built to expose that second layer of intelligence.**

---

# 💡 Our Solution

UPI Sentinel creates a complete investigation workflow:

```text
Raw Financial Data
       ↓
   DATA RESCUE
       ↓
Cleaning + Validation
       ↓
Entity Resolution
       ↓
Feature Engineering
       ↓
Risk Intelligence
       ↓
ML Anomaly Detection
       ↓
Fraud Network Graph
       ↓
Unified Intelligence
       ↓
Investigation Dashboard
       ↓
Sentinel AI Analyst
```

The platform does not simply label transactions as "fraud."

Instead, it produces **investigative signals and candidate networks** that help a human investigator decide where to look first.

> **Important:** risk scores and suspicious networks are investigative signals, not calibrated probabilities or proof of fraud.

---

# 🧠 What UPI Sentinel Does

## 1. Data Rescue

Upload a supported financial data source and Sentinel validates it before analysis.

Supported sources:

| Source | Purpose |
|---|---|
| UPI Transactions | Transaction-level behavior and payment activity |
| KYC Records | Identity and customer-risk context |
| Merchant Master | Merchant identity and merchant-risk context |
| Chargebacks | Dispute and chargeback intelligence |

The upload workflow provides:

- file validation
- schema validation
- missing-value detection
- duplicate detection
- row/column inspection
- source-specific validation
- pipeline processing
- refreshed dashboard intelligence

The system is designed for **new datasets with the same expected schema**, rather than being tied only to the original dataset.

---

# 🔄 End-to-End Intelligence Pipeline

Every accepted source can flow through the Sentinel pipeline:

```text
01 — Profile
        ↓
02 — Cleaning
        ↓
03 — Validation
        ↓
04 — Transformation
        ↓
05 — Feature Engineering
        ↓
06 — Fraud Graph
        ↓
07 — Anomaly Detection
        ↓
08 — Unified Intelligence
```

The dashboard communicates this workflow directly to investigators:

**Cleaning → Validation → Features → Graph → Anomaly Detection → Unified Intelligence**

Long-running ingestion is handled as a background job so the browser does not need to keep one large request open.

---

# 🧹 Data Quality & Engineering

One of the core design principles of UPI Sentinel is:

> **Never manufacture a relationship just to make the data look complete.**

The pipeline preserves raw identifiers while creating canonical forms for reliable matching.

### Example

Merchant identifiers were normalized for:

- whitespace
- casing
- formatting differences
- hyphen inconsistencies

This recovered legitimate merchant relationships without fabricating joins.

Similarly, unmatched user IDs are treated as **unmatched entities**, not automatically as suspicious users.

---

# 📊 Dataset Cleaning Results

The supplied challenge data contained substantial quality issues.

### UPI Transactions

- Raw rows: **20,400**
- Clean rows: **20,000**
- Exact duplicates removed: **400**
- Missing UTR: **1,000**
- Missing MCC: **2,872**
- Negative amounts: **420**

### KYC Records

- Raw rows: **36,400**
- Clean rows: **35,934**
- Exact duplicates removed: **278**
- Invalid PAN format: **2,615**
- Invalid Aadhaar format: **3,228**
- Missing income: **4,648**

### Merchant Master

- Raw rows: **6,210**
- Clean rows: **6,190**
- Missing MCC: **691**
- Missing settlement account: **2,443**
- Negative declared ticket size: **501**

### Chargebacks

- Raw rows: **2,884**
- Clean rows: **2,800**
- Exact duplicates removed: **84**
- Missing transaction IDs: **77**
- Negative disputed amounts: **220**
- Invalid temporal relationships detected:
  - Reported before transaction: **211**
  - Bank response before reported timestamp: **108**

---

# 🔗 Entity Resolution

UPI Sentinel does not assume that every source will perfectly join.

The pipeline measures relationship coverage explicitly.

### Key relationship coverage

| Relationship | Match Rate |
|---|---:|
| Transaction → KYC | **27.96%** |
| Transaction → Merchant | **46.38%** |
| Chargeback → Transaction | **91.99%** |
| Chargeback → KYC | **23.57%** |
| Chargeback → Merchant | **42.82%** |

This makes data lineage and limitations visible to investigators instead of hiding them.

---

# ⚠️ Risk Intelligence Engine

UPI Sentinel calculates transparent investigative risk scores across:

- transactions
- users
- merchants
- combined entities

The scoring engine uses interpretable signals such as:

### Transaction signals

- unusually large amount
- negative amount
- failed status
- pending status
- chargeback relationship
- ticket-size deviation

### User signals

- failure behavior
- pending behavior
- negative transactions
- chargeback history
- KYC status
- identity-quality signals
- transaction activity

### Merchant signals

- failure rate
- pending activity
- negative transactions
- chargeback behavior
- ticket-size deviation
- merchant status
- activity level

Risk bands:

```text
LOW       ≤ 25
MEDIUM    25–50
HIGH      50–75
CRITICAL  > 75
```

The model is intentionally transparent and heuristic for the hackathon prototype.

---

# 🤖 ML Anomaly Detection

UPI Sentinel adds an unsupervised anomaly-detection layer using **Isolation Forest**.

Current challenge-data run:

- Transaction anomalies: **400**
- User anomalies: **537**
- Merchant anomalies: **242**

This adds a second perspective beyond deterministic risk rules.

A transaction does not need to match a predefined fraud rule to deserve investigation.

---

# 🕸️ Fraud Network Intelligence

Traditional fraud detection often asks:

> "Is this transaction suspicious?"

UPI Sentinel also asks:

> **"Who is connected to whom?"**

The fraud graph models relationships between:

```text
Users ↔ Merchants ↔ Transactions
```

Current challenge-data graph:

- Graph nodes: **25,929**
- Graph edges: **20,000**
- Connected components: **5,929**
- Suspicious network candidates: **3,109**

Network signals include:

- shared merchants
- dense user–merchant relationships
- concentrated chargebacks
- behavioral risk
- large connected clusters

### Example investigation candidate

One detected component contained:

- 7 users
- 1 merchant
- 7 transactions
- ₹91,459.25 total transaction value
- 2 chargebacks
- 28.57% chargeback rate
- network risk score: **74.02 — HIGH**

This is surfaced as a **suspicious network candidate for investigation**, not declared as confirmed fraud.

---

# 🧩 Unified Intelligence

Stage 08 combines the separate intelligence layers into one investigation model.

Current challenge-data run:

| Metric | Value |
|---|---:|
| Transactions | 20,000 |
| Users | 17,878 |
| Merchants | 8,051 |
| Graph edges | 20,000 |
| Graph nodes | 25,929 |
| Suspicious networks | 3,109 |
| Investigation queue | 346 |

Example high-priority candidates can combine:

```text
Behavioral Risk
      +
Network Evidence
      +
Chargeback Evidence
      ↓
Investigation Candidate
```

This makes the investigation queue more useful than a simple transaction-risk list.

---

# 📈 Investigator Dashboard

The dashboard provides a single operating view for:

### Executive KPIs

- total transactions
- unique users
- merchant entities
- investigation queue

### Data Rescue

- source selection
- dataset upload
- pipeline progress
- ingestion results
- cleaning statistics
- entity-match rates

### Risk Engine

- transaction risk distribution
- unified risk bands
- investigation signals

### Investigation Queue

- priority
- entity type
- entity ID
- risk score
- risk band
- detection signals

### Network Intelligence

- suspicious network candidates
- connected-component investigation

---

# ✦ Sentinel AI Analyst

UPI Sentinel includes a natural-language investigation layer.

Instead of requiring an investigator to manually construct queries, the investigator can ask questions such as:

> "Which merchant category has the highest chargeback-to-transaction ratio this quarter?"

The AI investigation workflow is:

```text
Natural Language Question
          ↓
Intent Detection
          ↓
Relevant Intelligence
          ↓
Analysis
          ↓
Chart / Graph Selection
          ↓
Text Explanation
```

The goal is not simply to return an LLM-generated paragraph.

The system connects natural-language questions to the underlying intelligence layer and presents the result visually where appropriate.

---

# 🧰 Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- CSS
- Vercel

## Backend

- Python
- FastAPI
- Pandas
- Scikit-learn
- Network/graph analytics
- Render

## AI

- Groq
- `openai/gpt-oss-120b`
- Sentinel AI Analyst

## Data Engineering

- CSV / JSON ingestion
- data profiling
- cleaning
- validation
- entity resolution
- feature engineering
- anomaly detection
- graph analytics
- unified intelligence

---

# 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │     RAW SOURCES     │
                         │                     │
                         │ UPI | KYC | Merchant│
                         │      | Chargebacks  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     DATA RESCUE     │
                         │ Profile + Clean     │
                         │ Validate + Normalize│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  ENTITY RESOLUTION  │
                         │ Users / Merchants   │
                         └──────────┬──────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │ Risk Engine  │  │ ML Anomalies │  │ Fraud Graph  │
          └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                 └──────────────────┼──────────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ UNIFIED INTELLIGENCE│
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
          ┌──────────────────┐             ┌──────────────────┐
          │ Investigator UI  │             │ Sentinel AI      │
          │ Dashboard        │             │ Analyst          │
          └──────────────────┘             └──────────────────┘
```

---

# 📁 Repository Structure

```text
UPI-Sentinel/
│
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── dashboard.py
│   │   ├── transactions.py
│   │   ├── users.py
│   │   ├── merchants.py
│   │   ├── investigations.py
│   │   ├── networks.py
│   │   ├── agent.py
│   │   └── upload.py
│   │
│   └── services/
│       └── llm.py
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── transactions/
│   │   ├── users/
│   │   ├── merchants/
│   │   ├── networks/
│   │   ├── investigations/
│   │   └── ai-investigator/
│   │
├── pipeline/
│   ├── 01_profile.py
│   ├── 02_cleaning.py
│   ├── 03_validation.py
│   ├── 04_transform.py
│   ├── 05_features.py
│   ├── 06_fraud_graph.py
│   ├── 07_anomaly_detection.py
│   └── 08_unified_intelligence.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── reports/
├── notebooks/
├── tests/
│
├── DATA_DICTIONARY.md
├── README.md
└── requirements.txt
```

---

# 🚀 Running Locally

## 1. Clone

```bash
git clone https://github.com/varun539/UPI-Sentinel.git
cd UPI-Sentinel
```

## 2. Backend

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

## 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

---

# 🔐 Environment Variables

Create the required environment configuration locally.

Example:

```env
GROQ_API_KEY=your_key_here
BACKEND_API_URL=http://localhost:8000
```

**Never commit real API keys or secrets to GitHub.**

---

# 🧪 Data Upload Contract

UPI Sentinel expects source-specific schemas.

### Transactions

Required core fields include:

```text
txn_id
user_id
merchant_id
amount
status
```

### KYC

Required:

```text
user_id
```

### Merchants

Required:

```text
merchant_id
```

### Chargebacks

Required:

```text
complaint_id
```

Additional fields are used by the downstream intelligence pipeline when available.

If an uploaded file does not satisfy the expected source contract, Sentinel should reject it rather than silently producing misleading intelligence.

---

# 🔍 Design Principles

### 1. Data quality before AI

Bad inputs produce bad intelligence.

### 2. Explainability over black-box labels

Risk signals should be understandable to investigators.

### 3. Network context matters

Fraud can be relational, not transactional.

### 4. Never fabricate joins

An unmatched entity is not automatically fraudulent.

### 5. Human-in-the-loop investigation

The system prioritizes candidates; investigators make decisions.

### 6. AI should augment analysis

The AI analyst should explain and visualize evidence rather than inventing evidence.

---

# 🛣️ Future Roadmap

UPI Sentinel is currently a hackathon-ready prototype. The next step is turning it into a production-grade fraud-intelligence platform.

## 1. Persistent Database

Move processed intelligence from runtime files into PostgreSQL.

A production schema could include:

```text
users
merchants
transactions
chargebacks
risk_scores
anomalies
network_nodes
network_edges
investigations
investigation_events
datasets
pipeline_runs
```

This would allow:

- persistent data
- historical investigations
- incremental updates
- audit trails
- multi-user access
- dataset versioning

---

## 2. Dataset Versioning

Every uploaded dataset should receive:

```text
Dataset ID
Upload timestamp
Source type
Schema version
Pipeline version
Row count
Quality score
Processing status
```

Investigators could then compare:

```text
Dataset A → Dataset B → Dataset C
```

without losing previous intelligence.

---

## 3. Production-Grade Storage

Instead of relying on runtime filesystem storage:

```text
Object Storage
      +
PostgreSQL
      +
Background Job Queue
```

could provide durable ingestion and processing.

Possible architecture:

```text
Upload
  ↓
Object Storage
  ↓
Job Queue
  ↓
Pipeline Worker
  ↓
PostgreSQL
  ↓
API
  ↓
Dashboard
```

---

## 4. Real-Time / Streaming Fraud Detection

The next evolution would be transaction-level scoring as transactions arrive.

```text
UPI Event
   ↓
Feature Lookup
   ↓
Risk Model
   ↓
Network Context
   ↓
Risk Score
   ↓
Alert / Review
```

This could support near-real-time fraud monitoring instead of batch-only analysis.

---

## 5. Advanced Graph Analytics

Future versions could add:

- community detection
- centrality analysis
- ring discovery
- money-flow paths
- shared-account analysis
- temporal graph analysis
- graph embeddings
- Graph Neural Networks

This would make the network layer substantially more powerful for complex fraud rings.

---

## 6. Better Risk Models

The current heuristic engine can evolve into:

```text
Rules
 +
Supervised ML
 +
Unsupervised Anomaly Detection
 +
Graph Intelligence
 +
Temporal Features
```

with calibrated probabilities once suitable labeled fraud data is available.

---

## 7. Investigator Case Management

Allow investigators to:

- create cases
- assign cases
- add notes
- attach evidence
- mark entities
- change investigation status
- record decisions
- export investigation reports

Example:

```text
Suspicious Network
      ↓
Create Case
      ↓
Assign Investigator
      ↓
Review Evidence
      ↓
Add Notes
      ↓
Decision
      ↓
Audit Trail
```

---

## 8. Alerts & Monitoring

Future versions could trigger alerts for:

- sudden chargeback spikes
- abnormal merchant behavior
- newly formed dense networks
- high-risk users
- repeated failed transactions
- unusual transaction velocity
- emerging fraud clusters

---

## 9. Model Monitoring & Governance

For production BFSI environments:

- model versioning
- feature lineage
- drift monitoring
- false-positive tracking
- threshold management
- audit logs
- explainability records
- role-based access control

would become essential.

---

## 10. Enterprise Security

A production deployment could add:

- SSO
- RBAC
- encryption at rest
- encryption in transit
- secret management
- audit logging
- PII masking
- retention policies
- tenant isolation

---

# 🏆 Why This Approach Matters

Most simple fraud dashboards stop at:

```text
Transaction → Risk Score
```

UPI Sentinel goes further:

```text
Transaction
     ↓
User
     ↓
Merchant
     ↓
Chargeback
     ↓
Behavior
     ↓
Anomaly
     ↓
Network
     ↓
Unified Risk
     ↓
Investigation
     ↓
Natural-Language Analysis
```

The result is a shift from **transaction monitoring** to **investigation intelligence**.

---

# 👥 Team

## Data Ninjas

Built for the TransOrg AgentIQ Datathon 2026.

### Team Members

- **Varun**
- **Azim**
- **Kirthick**
- **Arnold**

---

# ⚠️ Prototype Disclaimer

UPI Sentinel is a hackathon prototype built for fraud-intelligence exploration.

Risk scores, anomaly flags, and suspicious network candidates are **investigative signals** and should not be interpreted as definitive proof of fraud.

The system should be validated with representative production data, calibrated models, appropriate controls, and domain-expert review before deployment in real financial decision-making.

---

# 🌐 Try It

### 🚀 Live Application

**https://upi-sentinel-ruby.vercel.app/**

### 📦 Source Code

**https://github.com/varun539/UPI-Sentinel**

---

# ⭐ Final Vision

> **UPI Sentinel aims to give financial investigators a single intelligence layer where messy payment data becomes explainable evidence, connected networks become visible risk, and natural language becomes an interface to fraud investigation.**

**Clean It. Analyze It. Visualize It. Ask It.**

### 🛡️ UPI Sentinel — Fraud Intelligence for the Connected Payment Era.
