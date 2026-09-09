# ClimateShield Documentation Hub

This directory maintains formal architectural specifications, security guidelines, test execution procedures, deployment runbooks, and evaluator resources for ClimateShield.

---

## Technical & Architecture Documents Index

- **[ARCHITECTURE.md](../ARCHITECTURE.md)**: Full technical breakdown of the 5-layer architecture, inter-service contracts, data flow (`Monitor -> Assess -> Act -> Learn`), and microservice boundaries.
- **[SECURITY.md](../SECURITY.md)**: Threat model, PII masking with audit surveillance, RBAC policies, and secrets management standards.
- **[TESTING.md](../TESTING.md)**: Comprehensive test execution guide, test matrix across 97 tests, and coverage boundaries.
- **[DEPLOYMENT.md](../DEPLOYMENT.md)**: Single-command local execution with Docker Compose, CI pipeline architecture, and enterprise production rollout roadmap.
- **[JUDGE_FAQ.md](./JUDGE_FAQ.md)**: One-page evaluator reference answering key questions on trigger threshold mathematics, basis risk mitigation, security posture, simulated vs. real components, and production gaps.
- **[CHANGELOG.md](../CHANGELOG.md)**: Chronological progression of deliverables built across all modules.
- **[CONFIG_SPEC.md](../infra/env/CONFIG_SPEC.md)**: Authoritative environment variable reference matrix per service.
