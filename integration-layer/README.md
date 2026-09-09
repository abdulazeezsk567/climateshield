# ClimateShield Action & Integration Layer (`/integration-layer`)

The **Action & Integration Layer** is ClimateShield's operational bridge to core lending infrastructure at **Satin Finserv Ltd (SFL)**. When the Risk & Trigger Engine detects parametric climate shocks, this layer executes the **Act** phase of the *Monitor $\to$ Assess $\to$ Act $\to$ Learn* feedback loop.

This layer is called **strictly by the API Layer** (never directly by the frontend or external clients) and is built around financial-grade security, pluggable interface adapters, and an immutable cryptographic audit ledger.

---

## 1. Key Capabilities & Deliverables Built

### 1.1 Intervention Lifecycle State Machine
Climate relief actions (moratoriums, liquidity top-ups) advance through an authoritative 4-stage lifecycle state machine:

```
[TRIGGERED]  ───>  [NOTIFIED]  ───>  [APPLIED]  ───>  [CONFIRMED]
     │                 │                │
     └───> [CANCELLED] / [FAILED] <─────┘
```

1. **`TRIGGERED`**: Parametric threshold breached by the Risk Engine. An intervention record is created with a unique ID (`INTV-...`) and tied to the originating trigger event via `correlation_id`.
2. **`NOTIFIED`**: Localized advisory notice generated and dispatched to the affected borrower via SMS/WhatsApp/Email.
3. **`APPLIED`**: Signed loan modification instruction formatted and dispatched to the Core LMS.
4. **`CONFIRMED`**: Webhook callback receipt from the LMS verified and recorded in the audit trail.
- **Enforcement**: Invalid or jumping transitions (e.g. `TRIGGERED` $\to$ `CONFIRMED`) raise `InvalidInterventionStateTransitionError`.

### 1.2 Pluggable LMS Webhook Integration (Adapter Pattern)
- **Interface / Adapter**: Outbound and inbound LMS integration is abstracted behind `LMSAdapter`, allowing switching from mock simulation to Satin's real Finnone core-banking platform via configuration:
  - `SimulatedLMSAdapter`: Generates instantaneous, realistic confirmations with transaction IDs (`LMS-TXN-...`) and HMAC signature verification.
  - `HttpLMSAdapter`: Production adapter dispatching real HTTP POST requests with HMAC-SHA256 headers (`X-ClimateShield-Signature`), configurable timeouts, and retries.
- **HMAC-SHA256 Signature Verification**: Inbound callbacks from the LMS are verified in constant time (`hmac.compare_digest`) using the shared secret `LMS_WEBHOOK_SECRET`.

### 1.3 Borrower Alert Service with Zero-Fabrication Safeguards
- **Zero Fabrication**: In demo/mock mode, notifications are explicitly tagged as `SIMULATED_DISPATCHED` (`is_simulated=True`). The system never falsely claims real carrier delivery in logs or API responses.
- **Bilingual Copy Generation**: Rich, localized message copy in Hindi and English explaining the climate shock, moratorium duration, zero penal interest, and customer care contact details.

### 1.4 Tamper-Evident Cryptographic Audit Trail
- **Correlation ID Linking**: Every intervention action, state transition, alert dispatch, and LMS receipt carries a `correlation_id` tying it back to the originating trigger event.
- **SHA-256 Hash Chaining**: Every log record contains a parent hash pointer (`previous_hash`) and computes a deterministic digest over the block preimage:
  $$\text{Preimage} = \text{previous\_hash} \mid \text{timestamp} \mid \text{event\_type} \mid \text{origin\_service} \mid \text{actor} \mid \text{correlation\_id} \mid \text{payload\_snapshot}$$
- **On-Demand Verification**: `verify_chain_integrity()` traverses the ledger from the genesis block to prove zero unauthorized record alteration or deletion.

---

## 2. Configuration & Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LMS_ADAPTER_TYPE` | `mock` | `mock` for demo simulation; `http` for real production LMS. |
| `LMS_ENDPOINT_URL` | `https://lms.satinfinserv.com/api/v1/interventions` | Target URL for production LMS HTTP adapter. |
| `LMS_WEBHOOK_SECRET` | `demo-sfl-lms-hmac-secret-2026` | Shared secret for signing and verifying HMAC-SHA256 webhook payloads. |
| `SMS_GATEWAY_API_KEY`| *(empty)* | Optional telecom API key; when empty, operates safely in simulation mode. |

---

## 3. Financial Placeholder Disclosures

In compliance with project safety guidelines, finance-adjacent values are explicit placeholders driven by configuration rather than arbitrary business logic:
- `DEFAULT_RELIEF_PERIOD_DAYS_PLACEHOLDER`: `30` days moratorium window.
- `DEFAULT_TOPUP_PERCENTAGE_PLACEHOLDER`: `0.10` (10% of active principal).
- `DEFAULT_INTEREST_MORATORIUM_RATE_PLACEHOLDER`: `0.0%` (zero penalty during relief window).

---

## 4. Assumptions & Design Notes
1. **Idempotency**: Every outbound LMS request generates an idempotency key (`IDEM-<loan_id>-<uuid>`) to prevent duplicate processing on network retries.
2. **Persistence**: The in-memory state machine and audit log stores provide thread-safe execution suitable for demo presentation, and mirror production PostgreSQL schemas with row-level locking.
