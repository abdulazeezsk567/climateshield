# ClimateShield Dependency & Platform Hygiene Guide

This guide outlines the dependency auditing, vulnerability management, and supply-chain security hygiene practices for **ClimateShield**.

---

## 1. Automated Vulnerability Scanning

### Python Ecosystem (`pip-audit` & `safety`)

All Python packages (`climateshield-shared`, `data-layer`, `risk-engine`, `integration-layer`, `api`) are audited against the PyPI Advisory Database and OSV (Open Source Vulnerabilities) index.

#### Running pip-audit Locally
```bash
# Install audit tool
pip install pip-audit

# Audit installed environment
pip-audit

# Audit specific requirements file or package
pip-audit -r api/requirements.txt
```

#### Running in CI/CD Pipeline (GitHub Actions)
```yaml
name: Dependency Vulnerability Audit

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run weekly every Monday at 04:00 UTC
    - cron: '0 4 * * 1'

jobs:
  python-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pip-audit
      - name: Run pip-audit
        run: |
          pip-audit --desc on --strict
```

---

### Node.js / Frontend Ecosystem (`npm audit`)

When running the frontend client or documentation site:

#### Running npm audit Locally
```bash
# Check for known vulnerabilities
npm audit

# In production CI, fail on moderate or higher vulnerabilities:
npm audit --audit-level=moderate
```

---

## 2. Secrets & Credential Leakage Prevention

### Pre-Commit Secrets Scanner
A built-in scanner is located at `scripts/check_secrets.py`. It checks:
1. Absence of `.env`, `.pem`, `.key`, or RSA certificate files in tracked Git files.
2. Verified `.gitignore` configuration disallowing `.env` and sensitive artifacts.
3. Absence of hardcoded AWS keys, GitHub tokens, database passwords, or JWT secrets in source code.

#### Running the Scanner:
```bash
python scripts/check_secrets.py
```

#### Git Pre-Commit Hook Configuration
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/sh
python scripts/check_secrets.py
if [ $? -ne 0 ]; then
    echo "Commit aborted due to detected secrets or unignored sensitive files."
    exit 1
fi
```

---

## 3. Supply Chain Security Best Practices

1. **Pinned Dependencies with Hashes**: In production deployment, generate lockfiles (`pip compile` or `poetry.lock` / `package-lock.json`) with cryptographic SHA-256 hashes to prevent dependency confusion and tampering.
2. **Minimal Base Images**: Docker containers build upon `python:3.12-slim` or distroless images, stripping out compilers, debuggers, and unnecessary shell utilities.
3. **Non-Root Execution**: Container workloads execute as non-privileged system users (`UID 10001: climateshield`).
4. **Read-Only Root Filesystems**: In Kubernetes/ECS deployments, mount root filesystem as read-only, allocating an ephemeral `/tmp` volume only where strictly necessary.
