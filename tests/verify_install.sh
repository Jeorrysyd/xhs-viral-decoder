#!/usr/bin/env bash
# verify_install.sh — one-shot dependency + skill-detection check
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$SKILL_ROOT"
exec python3 shared/lib/cli.py setup
