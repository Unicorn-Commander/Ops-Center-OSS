#!/bin/bash

###############################################################################
# Asset Audit Script
#
# Checks asset sizes and optimization status
# Run regularly to identify new large images that need optimization
#
# Usage: ./scripts/asset-audit.sh
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Asset Optimization Audit${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "public/logos" ]; then
    echo -e "${RED}Error: public/logos directory not found${NC}"
    echo "Please run this script from the ops-center directory"
    exit 1
fi

###############################################################################
# 1. Total Asset Sizes
###############################################################################

echo -e "${BLUE}📦 Total Asset Sizes${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_PUBLIC=$(du -sh public/ | cut -f1)
TOTAL_LOGOS=$(du -sh public/logos/ | cut -f1)
TOTAL_DIST=$(du -sh dist/ 2>/dev/null | cut -f1 || echo "N/A")

echo -e "public/ directory:       ${YELLOW}${TOTAL_PUBLIC}${NC}"
echo -e "public/logos/ directory: ${YELLOW}${TOTAL_LOGOS}${NC}"
echo -e "dist/ directory:         ${YELLOW}${TOTAL_DIST}${NC}"
echo ""

###############################################################################
# 2. Image Counts
###############################################################################

echo -e "${BLUE}🖼️  Image Counts${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PNG_COUNT=$(find public/logos -name "*.png" 2>/dev/null | wc -l)
JPG_COUNT=$(find public/logos -name "*.jpg" -o -name "*.jpeg" 2>/dev/null | wc -l)
WEBP_COUNT=$(find public/logos -name "*.webp" 2>/dev/null | wc -l)
SVG_COUNT=$(find public/logos -name "*.svg" 2>/dev/null | wc -l)

echo -e "PNG files:  ${YELLOW}${PNG_COUNT}${NC}"
echo -e "JPG files:  ${YELLOW}${JPG_COUNT}${NC}"
echo -e "WebP files: ${GREEN}${WEBP_COUNT}${NC}"
echo -e "SVG files:  ${YELLOW}${SVG_COUNT}${NC}"
echo ""

###############################################################################
# 3. Large Images (> 50 KB)
###############################################################################

echo -e "${BLUE}⚠️  Large Images (> 50 KB)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

LARGE_IMAGES=$(find public/logos -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -size +50k 2>/dev/null)

if [ -z "$LARGE_IMAGES" ]; then
    echo -e "${GREEN}✓ No large PNG/JPG images found (all < 50 KB)${NC}"
else
    LARGE_COUNT=$(echo "$LARGE_IMAGES" | wc -l)
    echo -e "${RED}Found ${LARGE_COUNT} large images:${NC}"
    echo ""

    while IFS= read -r file; do
        SIZE=$(du -h "$file" | cut -f1)
        BASENAME=$(basename "$file")
        WEBP_FILE="${file%.*}.webp"

        if [ -f "$WEBP_FILE" ]; then
            WEBP_SIZE=$(du -h "$WEBP_FILE" | cut -f1)
            echo -e "  ${YELLOW}${BASENAME}${NC} (${SIZE}) → ${GREEN}WebP exists${NC} (${WEBP_SIZE})"
        else
            echo -e "  ${RED}${BASENAME}${NC} (${SIZE}) → ${RED}No WebP${NC}"
        fi
    done <<< "$LARGE_IMAGES"

    echo ""
    echo -e "${YELLOW}💡 Run: node scripts/convert-images-to-webp.js${NC}"
fi

echo ""

###############################################################################
# 4. Missing WebP Files
###############################################################################

echo -e "${BLUE}🔍 Missing WebP Conversions${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MISSING_WEBP=()

while IFS= read -r file; do
    # Get file without extension
    BASE="${file%.*}"
    WEBP_FILE="${BASE}.webp"

    # Check if image is > 50KB
    SIZE_KB=$(du -k "$file" | cut -f1)

    if [ $SIZE_KB -gt 50 ] && [ ! -f "$WEBP_FILE" ]; then
        MISSING_WEBP+=("$file")
    fi
done < <(find public/logos -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) 2>/dev/null)

if [ ${#MISSING_WEBP[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All large images have WebP versions${NC}"
else
    echo -e "${RED}Found ${#MISSING_WEBP[@]} images missing WebP conversions:${NC}"
    echo ""

    for file in "${MISSING_WEBP[@]}"; do
        SIZE=$(du -h "$file" | cut -f1)
        echo -e "  ${RED}•${NC} $(basename "$file") (${SIZE})"
    done

    echo ""
    echo -e "${YELLOW}💡 Run: node scripts/convert-images-to-webp.js${NC}"
fi

echo ""

###############################################################################
# 5. WebP Savings
###############################################################################

echo -e "${BLUE}💾 WebP Size Savings${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_ORIGINAL=0
TOTAL_WEBP=0

while IFS= read -r webp_file; do
    # Get original file (try PNG first, then JPG)
    BASE="${webp_file%.webp}"
    ORIGINAL_FILE=""

    if [ -f "${BASE}.png" ]; then
        ORIGINAL_FILE="${BASE}.png"
    elif [ -f "${BASE}.jpg" ]; then
        ORIGINAL_FILE="${BASE}.jpg"
    elif [ -f "${BASE}.jpeg" ]; then
        ORIGINAL_FILE="${BASE}.jpeg"
    fi

    if [ -n "$ORIGINAL_FILE" ] && [ -f "$ORIGINAL_FILE" ]; then
        ORIG_SIZE=$(stat -c%s "$ORIGINAL_FILE" 2>/dev/null || stat -f%z "$ORIGINAL_FILE" 2>/dev/null)
        WEBP_SIZE=$(stat -c%s "$webp_file" 2>/dev/null || stat -f%z "$webp_file" 2>/dev/null)

        TOTAL_ORIGINAL=$((TOTAL_ORIGINAL + ORIG_SIZE))
        TOTAL_WEBP=$((TOTAL_WEBP + WEBP_SIZE))
    fi
done < <(find public/logos -name "*.webp" 2>/dev/null)

if [ $TOTAL_ORIGINAL -gt 0 ]; then
    # Convert to MB
    ORIG_MB=$(echo "scale=2; $TOTAL_ORIGINAL / 1024 / 1024" | bc)
    WEBP_MB=$(echo "scale=2; $TOTAL_WEBP / 1024 / 1024" | bc)
    SAVED_MB=$(echo "scale=2; ($TOTAL_ORIGINAL - $TOTAL_WEBP) / 1024 / 1024" | bc)
    SAVINGS_PCT=$(echo "scale=2; (($TOTAL_ORIGINAL - $TOTAL_WEBP) / $TOTAL_ORIGINAL) * 100" | bc)

    echo -e "Original size:  ${YELLOW}${ORIG_MB} MB${NC}"
    echo -e "WebP size:      ${GREEN}${WEBP_MB} MB${NC}"
    echo -e "Space saved:    ${GREEN}${SAVED_MB} MB${NC} (${GREEN}${SAVINGS_PCT}%${NC})"
else
    echo -e "${YELLOW}No WebP conversions found${NC}"
fi

echo ""

###############################################################################
# 6. Bundle Analysis (if dist exists)
###############################################################################

if [ -d "dist" ]; then
    echo -e "${BLUE}📦 Bundle Analysis${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    JS_SIZE=$(find dist -name "*.js" | xargs du -ch 2>/dev/null | tail -1 | cut -f1)
    CSS_SIZE=$(find dist -name "*.css" | xargs du -ch 2>/dev/null | tail -1 | cut -f1)

    echo -e "JavaScript total: ${YELLOW}${JS_SIZE}${NC}"
    echo -e "CSS total:        ${YELLOW}${CSS_SIZE}${NC}"

    # Find largest chunks
    echo ""
    echo -e "${BLUE}Top 5 Largest Chunks:${NC}"
    find dist -name "*.js" -exec ls -lh {} \; | sort -k5 -h | tail -5 | awk '{print "  " $9 " (" $5 ")"}'

    echo ""
fi

###############################################################################
# 7. Recommendations
###############################################################################

echo -e "${BLUE}💡 Recommendations${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ${#MISSING_WEBP[@]} -gt 0 ]; then
    echo -e "${YELLOW}1.${NC} Convert ${#MISSING_WEBP[@]} images to WebP: ${YELLOW}node scripts/convert-images-to-webp.js${NC}"
fi

if [ -z "$LARGE_IMAGES" ]; then
    echo -e "${GREEN}✓${NC} All images are optimized (< 50 KB)"
else
    LARGE_COUNT=$(echo "$LARGE_IMAGES" | wc -l)
    echo -e "${YELLOW}2.${NC} Consider further optimizing ${LARGE_COUNT} large images"
fi

if [ ! -d "dist" ]; then
    echo -e "${YELLOW}3.${NC} Build not found. Run: ${YELLOW}npm run build${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Audit complete${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
