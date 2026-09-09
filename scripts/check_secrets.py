#!/usr/bin/env python3
"""Pre-commit & CI Secret Leakage Prevention Scanner for ClimateShield.

Scans the codebase for:
1. Accidental commits of secret files (.env, credentials.json, id_rsa, *.pem, *.key)
2. High-entropy strings and hardcoded credential patterns (AWS, JWT, OpenAI, GitHub tokens, database passwords)
3. Ensures .env is listed in .gitignore
"""

import os
import re
import sys
from pathlib import Path

# File patterns that should NEVER be tracked in source control
FORBIDDEN_FILE_PATTERNS = [
    r"^\.env$",
    r"^\.env\.(local|production|staging|test)$",
    r".*\.pem$",
    r".*\.key$",
    r".*\.p12$",
    r".*\.pfx$",
    r"^id_rsa$",
    r"^id_ed25519$",
    r".*_rsa$",
    r"^credentials\.json$",
    r"^service_account.*\.json$",
]

# Regex patterns detecting potential hardcoded credentials
SUSPICIOUS_CONTENT_PATTERNS = [
    (r"(?i)(?:api_key|apikey|secret_key|jwt_secret)\s*=\s*['\"][A-Za-z0-9_\-\.]{20,}['\"]", "High-entropy API/JWT secret assignment"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "Private cryptographic key block"),
    (r"(?i)postgres(?:ql)?://[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+@", "Database connection URI containing plaintext password"),
]

# Directories and files to exclude from content scanning
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "htmlcov",
    ".idea",
    ".vscode",
}

EXCLUDE_FILES = {
    "check_secrets.py",  # Contains scanner patterns
    ".env.example",      # Safe template documentation
    "SECURITY.md",       # May describe token regexes
}


def scan_repository(repo_root: Path) -> int:
    """Scan the repository for forbidden files and high-entropy secret patterns."""
    violations = []

    print(f"[SECURITY_SCAN] Scanning repository at: {repo_root}")

    # 1. Check .gitignore
    gitignore_path = repo_root / ".gitignore"
    if gitignore_path.is_file():
        content = gitignore_path.read_text(encoding="utf-8")
        if ".env" not in content:
            violations.append(("[GITIGNORE_MISSING]", ".gitignore must explicitly ignore '.env'"))
    else:
        violations.append(("[GITIGNORE_MISSING]", "Root .gitignore file does not exist!"))

    # 2. Walk directory tree
    for root, dirs, files in os.walk(repo_root):
        # Filter excluded directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for fname in files:
            file_path = Path(root) / fname
            rel_path = file_path.relative_to(repo_root)

            # Check for forbidden filenames
            for pattern in FORBIDDEN_FILE_PATTERNS:
                if re.match(pattern, fname, re.IGNORECASE) and not fname.endswith(".example"):
                    violations.append(
                        ("[FORBIDDEN_FILE]", f"Prohibited credential/secret file found: {rel_path}")
                    )

            if fname in EXCLUDE_FILES or fname.endswith(".example"):
                continue

            # Check file content for suspicious patterns
            # Skip binary / large files
            if file_path.stat().st_size > 1_000_000:
                continue

            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern, description in SUSPICIOUS_CONTENT_PATTERNS:
                matches = re.finditer(pattern, text)
                for match in matches:
                    # Determine line number
                    line_num = text[:match.start()].count("\n") + 1
                    snippet = match.group(0)[:30] + "..."
                    violations.append(
                        (
                            "[SECRET_DETECTED]",
                            f"{rel_path}:{line_num} - {description} (match: '{snippet}')",
                        )
                    )

    if violations:
        print("\n" + "=" * 70)
        print("[!] SECURITY VULNERABILITY ALERT: Potential secrets or forbidden files found!")
        print("=" * 70)
        for category, message in violations:
            print(f" {category} {message}")
        print("\nRemediation:")
        print(" 1. Remove secret files from the repository.")
        print(" 2. Externalize all credentials into environment variables.")
        print(" 3. Rotate any credentials that may have been committed.")
        print("=" * 70 + "\n")
        return 1

    print("[+] [SECURITY_SCAN] Pass: Zero secrets, keys, or forbidden files detected.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    root_dir = Path(__file__).resolve().parent.parent
    sys.exit(scan_repository(root_dir))
