#!/bin/bash
# Cloudflare API Token Documentation Cleanup Script
# This script replaces exposed token references with redacted placeholders
#
# Date: October 23, 2025
# Purpose: Clean up token exposures in documentation files

set -e

OLD_TOKEN="0LVXYAzHsGRtxn1Qe0_ItTlCFGxW9iogQCmsegC_"
NEW_PLACEHOLDER="<CLOUDFLARE_API_TOKEN_REDACTED>"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Cloudflare Token Documentation Cleanup${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Files to update (documentation and test files only, NOT configuration)
FILES=(
  "EPIC_1.6_DEPLOYMENT_COMPLETE.md"
  "EPIC_1.6_TEST_REPORT.md"
  "NEXT_DEVELOPMENT_PRIORITIES.md"
  "CREDENTIAL_MANAGEMENT_IMPLEMENTATION_REPORT.md"
  "backend/docs/CREDENTIAL_API.md"
  "docs/CREDENTIAL_EXPLORATION_INDEX.md"
  "docs/CREDENTIAL_CODE_REFERENCE.md"
  "docs/CREDENTIAL_MANAGEMENT_ANALYSIS.md"
  "CREDENTIAL_MANAGEMENT.md"
  "SECURITY_FIXES_APPLIED.md"
  "MASTER_CHECKLIST.md"
  "tests/CLOUDFLARE_TESTS_README.md"
  "tests/security/test_security.py"
  "tests/unit/test_cloudflare_manager.py"
)

cd /home/muut/Production/UC-Cloud/services/ops-center

UPDATED_COUNT=0
SKIPPED_COUNT=0
ERROR_COUNT=0

echo -e "${YELLOW}Scanning and updating documentation files...${NC}"
echo ""

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    # Check if file contains the old token
    if grep -q "$OLD_TOKEN" "$file"; then
      echo -e "  📝 Updating: ${file}"

      # Create backup
      cp "$file" "${file}.backup"

      # Replace token with placeholder
      sed -i "s/$OLD_TOKEN/$NEW_PLACEHOLDER/g" "$file"

      # Verify replacement worked
      if ! grep -q "$OLD_TOKEN" "$file"; then
        echo -e "     ${GREEN}✅ Success${NC}"
        UPDATED_COUNT=$((UPDATED_COUNT + 1))
      else
        echo -e "     ${RED}❌ Failed - token still present${NC}"
        ERROR_COUNT=$((ERROR_COUNT + 1))
        # Restore from backup
        mv "${file}.backup" "$file"
      fi
    else
      echo -e "  ⏭️  Skipping: ${file} (no token found)"
      SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    fi
  else
    echo -e "  ${YELLOW}⚠️  Warning: ${file} not found${NC}"
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
  fi
done

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Cleanup Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}✅ Updated: ${UPDATED_COUNT} files${NC}"
echo -e "${YELLOW}⏭️  Skipped: ${SKIPPED_COUNT} files${NC}"
if [ $ERROR_COUNT -gt 0 ]; then
  echo -e "${RED}❌ Errors: ${ERROR_COUNT} files${NC}"
fi
echo ""

if [ $UPDATED_COUNT -gt 0 ]; then
  echo -e "${GREEN}Documentation cleanup complete!${NC}"
  echo ""
  echo -e "${YELLOW}⚠️  IMPORTANT NOTES:${NC}"
  echo -e "  1. Backup files created (*.backup) - delete after verification"
  echo -e "  2. .env.auth and backend code files NOT modified"
  echo -e "  3. You should update those with new token via Platform Settings GUI"
  echo -e "  4. Old token should be revoked in Cloudflare dashboard AFTER new token works"
  echo ""

  # Show where backups are
  echo -e "${YELLOW}Backup files created:${NC}"
  find . -name "*.backup" -type f
  echo ""

  # Final verification
  echo -e "${YELLOW}Verifying cleanup...${NC}"
  REMAINING=$(grep -r "$OLD_TOKEN" . --exclude-dir=node_modules --exclude-dir=dist --exclude="*.backup" --exclude="cleanup-token-references.sh" --exclude="CLOUDFLARE_TOKEN_ROTATION_GUIDE.md" | wc -l)

  if [ "$REMAINING" -eq 0 ]; then
    echo -e "${GREEN}✅ No exposed tokens found in documentation!${NC}"
  else
    echo -e "${RED}⚠️  Warning: $REMAINING file(s) still contain the old token${NC}"
    echo -e "${YELLOW}These are likely configuration files that need manual update:${NC}"
    grep -r "$OLD_TOKEN" . --exclude-dir=node_modules --exclude-dir=dist --exclude="*.backup" --exclude="cleanup-token-references.sh" --exclude="CLOUDFLARE_TOKEN_ROTATION_GUIDE.md" -l
  fi

  echo ""
  echo -e "${YELLOW}Next Steps:${NC}"
  echo -e "  1. Go to: https://your-domain.com/admin/platform/settings"
  echo -e "  2. Update CLOUDFLARE_API_TOKEN with new token from Cloudflare"
  echo -e "  3. Click 'Save & Restart'"
  echo -e "  4. Verify Cloudflare DNS page works"
  echo -e "  5. Revoke old token in Cloudflare dashboard"
  echo -e "  6. Delete backup files: ${YELLOW}find . -name '*.backup' -delete${NC}"
else
  echo -e "${YELLOW}No files needed updating - token already cleaned up!${NC}"
fi

echo ""
echo -e "${YELLOW}========================================${NC}"
