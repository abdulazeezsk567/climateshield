# ClimateShield Security Specification

> **Note**: This document is mirrored at the repository root as [`SECURITY.md`](../SECURITY.md). Please refer to the root document for authoritative security standards.

See [SECURITY.md](../SECURITY.md) for full details on:
1. Security Architecture & Threat Boundary Model
2. Secrets Management & Environment Hygiene
3. Security Responsibilities by Layer:
   - Data Layer: PII masking, tokenization, coordinate coarsening, ingestion integrity
   - Risk & Trigger Engine: Model tampering resistance, deterministic bounds enforcement
   - API Layer: Transport security (TLS 1.3), RBAC authorization, schema validation, rate limiting
   - Action & Integration Layer: HMAC-SHA256 signature verification, idempotency keys, immutable audit trails
   - Presentation Layer: Strict CSP, sanitization, role-aware conditional rendering
4. Vulnerability Disclosure & Incident Response
