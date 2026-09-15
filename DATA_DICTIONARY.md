# UPI Sentinel Data Dictionary

## UPI Transactions

txn_id - transaction identifier
timestamp - transaction timestamp
user_id - user identifier
merchant_id - merchant identifier
amount - normalized transaction amount
utr - unique transaction reference
mcc - merchant category code
status - SUCCESS, FAILED or PENDING

## KYC Records

user_id - user identifier
full_name - recorded user name
pan - PAN identifier
aadhaar - Aadhaar identifier
date_of_birth - normalized date of birth
city - user city
state - user state
monthly_income - normalized income
occupation - occupation
signup_timestamp - signup time
kyc_status - standardized KYC status
risk_segment - LOW, MEDIUM, HIGH or UNKNOWN

## Merchant Master

merchant_id - merchant identifier
merchant_name - merchant name
mcc - merchant category code
merchant_category - merchant category
business_type - business type
city/state - merchant location
onboarding_date - onboarding date
settlement_account - settlement account reference
merchant_status - standardized merchant status
declared_avg_ticket_size - declared average ticket size

## Chargebacks

complaint_id - complaint identifier
txn_id - related transaction
user_id - related user
merchant_id - related merchant
transaction_timestamp - original transaction time
reported_timestamp - complaint time
disputed_amount - disputed amount
reason_code - chargeback reason
complaint_text - complaint description
resolution_status - resolution state
bank_response_timestamp - bank response time
severity - LOW, MEDIUM, HIGH or CRITICAL
channel - complaint channel

## Analytical Outputs

transaction_features - transaction behavioral risk features
user_features - user behavioral and KYC risk features
merchant_features - merchant behavioral and chargeback features
fraud_graph_nodes - graph entities and network features
fraud_graph_edges - User-Merchant relationships
transaction_ml_anomalies - transaction Isolation Forest anomalies
user_ml_anomalies - user Isolation Forest anomalies
merchant_ml_anomalies - merchant Isolation Forest anomalies
transaction_intelligence - unified transaction intelligence
user_intelligence - unified user intelligence
merchant_intelligence - unified merchant intelligence
investigation_queue - prioritized investigation candidates

## Data Quality

The pipeline removes exact duplicates, normalizes currencies and timestamps, standardizes statuses, validates identifiers, reports missing values, validates temporal consistency and measures cross-dataset relationship coverage.

Unmatched records are preserved. Missing relationships are not automatically interpreted as fraud.

Risk scores are investigative signals, not confirmed fraud verdicts.
