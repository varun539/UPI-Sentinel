# UPI Sentinel

## AI-Powered UPI Fraud & Merchant Intelligence Platform

UPI Sentinel transforms messy UPI transactions, KYC records, merchant data and chargebacks into explainable fraud intelligence for investigators.

### Core capabilities

- Data rescue and validation
- Duplicate and missing-value handling
- Currency, timestamp and identifier normalization
- Transaction, user and merchant risk scoring
- Chargeback analytics
- User-Merchant graph intelligence
- Suspicious network detection
- Isolation Forest anomaly detection
- Unified fraud intelligence
- Investigation prioritization
- AI Investigator

### Architecture

Raw Data -> Data Rescue -> Validation -> Feature Engineering -> Risk + ML + Graph Intelligence -> Unified Intelligence -> Investigation Queue -> Dashboard -> AI Investigator

### Analytical results

- 20,000 cleaned transactions
- 17,878 transaction-linked users
- 8,051 transaction-linked merchant entities
- 2,800 chargebacks
- 3,109 suspicious network candidates
- 346 investigation candidates
- 400 transaction ML anomalies
- 537 user ML anomalies
- 242 merchant ML anomalies

### Pipeline

01_profile -> 02_cleaning -> 03_validation -> 04_transform -> 05_features -> 06_fraud_graph -> 07_anomaly_detection -> 08_unified_intelligence

Processed artifacts are stored in data/processed/ and reports are stored in reports/.

### API

/health
/api/dashboard/summary
/api/transactions
/api/users
/api/merchants
/api/investigations
/api/networks
/api/networks/{component_id}

### Frontend

Next.js routes:

/
/investigations
/transactions
/users
/merchants
/networks
/ai-investigator

### Running locally

Backend:
uvicorn backend.main:app --host 0.0.0.0 --port 8000

Frontend:
cd frontend
npm run dev

### Data governance

Risk scores and anomaly flags are investigative prioritization signals, not confirmed fraud verdicts. Unmatched entities are preserved and are not automatically classified as fraud.

### Hackathon

TransOrg AgentIQ Datathon - Track 1: FinTech & BFSI - UPI Fraud Ring & Merchant Analytics.

Clean It. Analyze It. Visualize It. Ask It.
