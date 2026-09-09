# ClimateShield Infrastructure & Deployment Module (`/infra`)

This module provides containerization specifications, orchestration manifests, environment templates, and operational runbooks for ClimateShield.

---

## 1. Directory Structure

```
infra/
├── docker/
│   ├── Dockerfile.api               # Hardened Python 3.11 API Gateway container
│   ├── Dockerfile.data-layer        # Climate ingestion daemon container
│   ├── Dockerfile.risk-engine       # Risk & trigger evaluation daemon container
│   ├── Dockerfile.integration-layer # LMS action & audit verifier daemon container
│   └── Dockerfile.frontend          # React + Vite dashboard container
├── env/
│   ├── .env.dev.example             # Local developer workstation template
│   ├── .env.staging.example         # Pre-production cloud staging template
│   ├── .env.prod.example            # Production template (zero default secrets)
│   ├── CONFIG_SPEC.md               # Environment variable dictionary & security tiers
│   └── README.md                    # Environment management principles
└── README.md                        # This document
```

---

## 2. What Was Built

1. **Service Containerization (`infra/docker/`)**:
   - Hardened, non-root (`appuser`, UID 10001) Dockerfiles for all 5 layers.
   - Built-in container healthcheck probes (`curl -f http://localhost:8000/health`).
   - Clean layer-caching structure installing shared packages before service sources.
2. **Unified Local Orchestration (`docker-compose.yml`)**:
   - Single-command orchestration for `data-layer`, `risk-engine`, `integration-layer`, `api`, and `frontend`.
   - Shared bridge network (`climateshield-network`) and persistent storage volumes (`./data`).
   - Health-gated startup ordering (frontend waits for healthy API probe).
3. **Multi-Environment Configuration Management (`infra/env/`)**:
   - Granular `.env.*.example` templates for development, staging, and production.
   - Authoritative [`CONFIG_SPEC.md`](file:///C:/Users/Abdul%20Azeez/.gemini/antigravity/scratch/climateshield/infra/env/CONFIG_SPEC.md) matrix classifying variables by security level.
   - Startup Pydantic validator in [`api/core/config.py`](file:///C:/Users/Abdul%20Azeez/.gemini/antigravity/scratch/climateshield/api/src/api/core/config.py) failing immediately if default secret keys are loaded in staging or production.
4. **Automated CI/CD Quality Pipeline (`.github/workflows/ci.yml`)**:
   - Automated pre-commit secrets & credential scanning (`scripts/check_secrets.py`).
   - Dependency vulnerability scanning (`pip-audit` for Python, `npm audit --audit-level=critical` for Node.js).
   - Python code quality / syntax linting with Flake8.
   - Backend automated test suite (84 tests across API, Risk Engine, Data Layer, Integration Layer).
   - Frontend TypeScript type checking, Vitest suite (13 tests), and Vite production bundle compilation.
   - Docker Compose configuration syntax validation.
5. **Observability & Telemetry Subsystems**:
   - Production structured JSON logging (`StructuredJsonFormatter`) with automated borrower PII redaction.
   - Prometheus metrics exposition endpoint (`/metrics`) and JSON summary endpoint (`/api/v1/metrics/summary`).
   - Live counters for HTTP throughput, error rates, request latency summary, climate trigger evaluations/activations, and LMS relief dispatches.
6. **Production Architecture Roadmap (`DEPLOYMENT.md`)**:
   - Complete operations guide detailing local run, CI flow, and enterprise graduation requirements (AWS Secrets Manager, Amazon RDS PostgreSQL with PostGIS, mTLS LMS adapter, Cloudflare/AWS WAF).

---

## 3. Key Assumptions & Design Decisions

1. **Daemonized Microservices in Docker Compose**:
   - In single-process development, `api` directly invokes `data_layer`, `risk_engine`, and `integration_layer` as in-process packages.
   - In distributed/containerized deployment (`docker compose`), `data-layer`, `risk-engine`, and `integration-layer` run as standalone background workers (`python -m <package>`) with graceful shutdown and health logging, matching a true decoupled microservices topology.
2. **Strict Whitelisting of CORS & Origins**:
   - Wildcard CORS (`*`) is explicitly rejected in all environments to prevent unauthorized browser cross-origin requests to financial endpoints.
3. **Zero Secrets in Version Control**:
   - Real `.env` files are strictly excluded via `.gitignore` and enforced by `scripts/check_secrets.py`.
   - Production secrets are assumed to be injected directly into container memory by a cloud secrets manager (AWS Secrets Manager, Vault, or Kubernetes Secrets).
