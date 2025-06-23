#!/usr/bin/env python3
"""
Security check script to ensure no credentials are exposed before making repo public.
Run this before pushing to public repository!
"""

import os
import subprocess
import sys
from pathlib import Path

# Color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Sensitive file patterns
SENSITIVE_PATTERNS = [
    "service-account-key.json",
    "*.pem",
    "*.key",
    ".env",
    ".env.*",
    "credentials/*",
    "*secret*",
    "*password*",
    "*token*",
    "*api_key*",
]

# Files that should NEVER be in the repo
CRITICAL_FILES = [
    "service-account-key.json",
    "credentials/service-account-key.json",
    ".env",
]


def check_gitignore():
    """Ensure .gitignore has all sensitive patterns."""
    print("\n{YELLOW}Checking .gitignore...{RESET}")

    if not Path(".gitignore").exists():
        print("{RED}✗ .gitignore file not found!{RESET}")
        return False

    with open(".gitignore", "r") as f:
        gitignore_content = f.read()

    missing = []
    for pattern in [
        "service-account-key.json",
        ".env",
        "credentials/",
        "*.key",
        "*.pem",
    ]:
        if pattern not in gitignore_content:
            missing.append(pattern)

    if missing:
        print("{RED}✗ Missing patterns in .gitignore: {', '.join(missing)}{RESET}")
        return False

    print("{GREEN}✓ .gitignore properly configured{RESET}")
    return True


def check_staged_files():
    """Check if any sensitive files are staged for commit."""
    print("\n{YELLOW}Checking staged files...{RESET}")

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )

    if result.returncode != 0:
        print("{RED}✗ Error checking git status{RESET}")
        return False

    staged_files = result.stdout.strip().split("\n") if result.stdout.strip() else []
    sensitive_staged = []

    for file in staged_files:
        for critical in CRITICAL_FILES:
            if file == critical or file.endswith(critical):
                sensitive_staged.append(file)

    if sensitive_staged:
        print("{RED}✗ CRITICAL: Sensitive files staged for commit:{RESET}")
        for file in sensitive_staged:
            print("    {file}")
        print("{YELLOW}Run: git reset HEAD {' '.join(sensitive_staged)}{RESET}")
        return False

    print("{GREEN}✓ No sensitive files staged{RESET}")
    return True


def check_committed_files():
    """Check if any sensitive files have been committed."""
    print("\n{YELLOW}Checking commit history...{RESET}")

    issues = []
    for critical_file in CRITICAL_FILES:
        result = subprocess.run(
            ["git", "log", "--all", "--full-history", "--", critical_file],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            issues.append(critical_file)

    if issues:
        print("{RED}✗ CRITICAL: Sensitive files found in git history:{RESET}")
        for file in issues:
            print("    {file}")
        print("{YELLOW}These files need to be removed from git history!{RESET}")
        print(
            "See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository"
        )
        return False

    print("{GREEN}✓ No sensitive files in commit history{RESET}")
    return True


def check_working_directory():
    """Check if sensitive files exist in working directory."""
    print("\n{YELLOW}Checking working directory...{RESET}")

    found_files = []
    for critical_file in CRITICAL_FILES:
        if Path(critical_file).exists():
            found_files.append(critical_file)

    if found_files:
        print(
            "{YELLOW}⚠ Sensitive files found (make sure they're in .gitignore):{RESET}"
        )
        for file in found_files:
            # Check if file is ignored
            result = subprocess.run(["git", "check-ignore", file], capture_output=True)
            if result.returncode == 0:
                print("    {GREEN}✓{RESET} {file} (ignored)")
            else:
                print("    {RED}✗{RESET} {file} (NOT IGNORED!)")
    else:
        print("{GREEN}✓ No sensitive files in working directory{RESET}")

    return True


def main():
    """Run all security checks."""
    print("{YELLOW}{'=' *60}")
    print("Security Check for SentinelOps Repository")
    print("{'=' *60}{RESET}")

    all_good = True

    all_good &= check_gitignore()
    all_good &= check_staged_files()
    all_good &= check_committed_files()
    all_good &= check_working_directory()

    print("\n{YELLOW}{'=' *60}{RESET}")

    if all_good:
        print("{GREEN}✅ Security check passed!{RESET}")
        print("\nReminder before making repo public:")
        print("1. Never commit service-account-key.json")
        print("2. Keep .env file local only")
        print("3. Use .env.example for documentation")
        print("4. Double-check no credentials in code comments")
        return 0
    else:
        print(
            "{RED}❌ Security issues found! Fix them before making repo public.{RESET}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
