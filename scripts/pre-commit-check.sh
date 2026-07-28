#!/bin/bash
# Run before committing: bash scripts/pre-commit-check.sh
# Catches common issues before they hit production

set -eo pipefail

echo "=== Python Syntax Check ==="
find backend -name "*.py" -not -path "*/__pycache__/*" | \
  xargs python3 -c "
import ast, sys, pathlib
errors = []
for f in sys.argv[1:]:
    try: ast.parse(pathlib.Path(f).read_text())
    except SyntaxError as e: errors.append(f'{f}:{e.lineno}: {e.msg}')
if errors:
    for e in errors: print(f'FAIL: {e}')
    sys.exit(1)
print(f'OK: {len(sys.argv)-1} files pass syntax check')
"

echo ""
echo "=== Credential Scan ==="
CRED_HITS=$(grep -rn "MagicUnicorn2025\|CmonWidja\|sk_test_\|pk_test_\|whsec_" backend/*.py src/**/*.jsx 2>/dev/null | grep -v "node_modules\|dist\|__pycache__" | head -5)
if [ -n "$CRED_HITS" ]; then
  echo "WARNING: Possible hardcoded credentials:"
  echo "$CRED_HITS"
else
  echo "OK: No hardcoded credentials found"
fi

echo ""
echo "=== All checks passed ==="
