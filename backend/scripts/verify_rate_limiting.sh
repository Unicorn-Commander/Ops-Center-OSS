#!/bin/bash
# Rate Limiting Implementation Verification Script

echo "========================================="
echo "Rate Limiting Implementation Verification"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check files
echo "1. Checking core files..."
FILES=(
    "rate_limiter.py"
    ".env.ratelimit"
    "requirements.txt"
    "scripts/integrate_rate_limiting.py"
    "tests/test_rate_limiting.py"
    "docs/RATE_LIMITING_README.md"
    "docs/RATE_LIMITING_INTEGRATION.md"
    "RATE_LIMITING_SUMMARY.md"
    "RATE_LIMITING_QUICK_REFERENCE.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (MISSING)"
    fi
done

echo ""

# Check dependencies
echo "2. Checking dependencies in requirements.txt..."
if grep -q "redis==5.0.1" requirements.txt && grep -q "hiredis==2.3.2" requirements.txt; then
    echo -e "  ${GREEN}✓${NC} Redis dependencies added"
else
    echo -e "  ${RED}✗${NC} Redis dependencies missing"
fi

echo ""

# Check Python syntax
echo "3. Checking Python syntax..."
if python3 -m py_compile rate_limiter.py 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} rate_limiter.py syntax valid"
else
    echo -e "  ${RED}✗${NC} rate_limiter.py syntax error"
fi

if python3 -m py_compile scripts/integrate_rate_limiting.py 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} integrate_rate_limiting.py syntax valid"
else
    echo -e "  ${RED}✗${NC} integrate_rate_limiting.py syntax error"
fi

echo ""

# Check Redis connection
echo "4. Checking Redis availability..."
if docker ps | grep -q "redis"; then
    echo -e "  ${GREEN}✓${NC} Redis container running"
    if docker exec unicorn-lago-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo -e "  ${GREEN}✓${NC} Redis responding to ping"
    else
        echo -e "  ${YELLOW}⚠${NC} Redis container exists but not responding"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Redis container not found (unicorn-lago-redis)"
    echo "     Expected container name from config: unicorn-lago-redis"
fi

echo ""

# Check configuration
echo "5. Checking configuration..."
if [ -f ".env.ratelimit" ]; then
    echo "  Configuration values:"
    grep -E "^RATE_LIMIT_" .env.ratelimit | head -10 | while read line; do
        echo "    $line"
    done
fi

echo ""

# Integration status
echo "6. Checking integration status..."
if grep -q "from rate_limiter import" ../server.py 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Rate limiter already integrated into server.py"
else
    echo -e "  ${YELLOW}⚠${NC} Rate limiter NOT yet integrated into server.py"
    echo "     Run: python scripts/integrate_rate_limiting.py"
fi

echo ""

# Summary
echo "========================================="
echo "Next Steps:"
echo "========================================="
echo ""
echo "1. Review configuration in .env.ratelimit"
echo "2. Install dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "3. Integrate into server.py (if not done):"
echo "   python scripts/integrate_rate_limiting.py --dry-run  # Preview"
echo "   python scripts/integrate_rate_limiting.py            # Apply"
echo ""
echo "4. Restart service:"
echo "   docker restart unicorn-ops-center"
echo ""
echo "5. Test implementation:"
echo "   pytest tests/test_rate_limiting.py -v"
echo ""
echo "6. Verify in production:"
echo "   curl -v http://localhost:8084/api/v1/services 2>&1 | grep -i ratelimit"
echo ""
echo "Documentation:"
echo "  - Quick start: RATE_LIMITING_QUICK_REFERENCE.md"
echo "  - Full guide: docs/RATE_LIMITING_README.md"
echo "  - Integration: docs/RATE_LIMITING_INTEGRATION.md"
echo ""
