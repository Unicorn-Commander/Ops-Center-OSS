#!/bin/bash
# GPU Monitoring Deployment Script
# Deploys DCGM Exporter and GPU Monitoring Dashboard
# Author: DevOps Team Lead
# Date: November 29, 2025

set -e

echo "🚀 GPU Monitoring Deployment Script"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GRAFANA_URL="http://localhost:3102"
GRAFANA_API_KEY="your-grafana-api-key"
PROMETHEUS_URL="http://localhost:9091"
GPU_EXPORTER_PORT="9400"

# Step 1: Check Prerequisites
echo "📋 Step 1: Checking Prerequisites..."
echo ""

# Check if nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}❌ ERROR: nvidia-smi not found!${NC}"
    echo "   NVIDIA drivers must be installed on the host system."
    echo "   Install drivers: https://www.nvidia.com/Download/index.aspx"
    exit 1
else
    echo -e "${GREEN}✅ nvidia-smi found${NC}"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ ERROR: Docker not found!${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Docker found${NC}"
    docker --version
fi

# Check Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ ERROR: Docker Compose not found!${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Docker Compose found${NC}"
    docker compose version
fi

# Check if Grafana is running
if ! docker ps | grep -q taxsquare-grafana; then
    echo -e "${RED}❌ ERROR: Grafana container not running!${NC}"
    echo "   Start Grafana: docker compose -f docker-compose.monitoring.yml up -d grafana"
    exit 1
else
    echo -e "${GREEN}✅ Grafana running${NC}"
fi

# Check if Prometheus is running
if ! docker ps | grep -q taxsquare-prometheus; then
    echo -e "${RED}❌ ERROR: Prometheus container not running!${NC}"
    echo "   Start Prometheus: docker compose -f docker-compose.monitoring.yml up -d prometheus"
    exit 1
else
    echo -e "${GREEN}✅ Prometheus running${NC}"
fi

echo ""

# Step 2: Create GPU Exporter Configuration
echo "📝 Step 2: Creating GPU Exporter Configuration..."
echo ""

# Create docker-compose.gpu.yml
cat > /tmp/docker-compose.gpu.yml <<'EOF'
version: '3.8'

services:
  dcgm-exporter:
    image: nvcr.io/nvidia/k8s/dcgm-exporter:3.3.5-3.4.0-ubuntu22.04
    container_name: unicorn-dcgm-exporter
    restart: unless-stopped
    ports:
      - "9400:9400"
    runtime: nvidia
    environment:
      - DCGM_EXPORTER_LISTEN=:9400
      - DCGM_EXPORTER_KUBERNETES=false
      - DCGM_EXPORTER_COLLECTORS=/etc/dcgm-exporter/default-counters.csv
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    networks:
      - unicorn-network
    cap_add:
      - SYS_ADMIN

networks:
  unicorn-network:
    external: true
EOF

echo -e "${GREEN}✅ Created docker-compose.gpu.yml${NC}"

# Step 3: Deploy GPU Exporter
echo ""
echo "🐳 Step 3: Deploying DCGM Exporter..."
echo ""

docker compose -f /tmp/docker-compose.gpu.yml up -d

# Wait for exporter to start
echo "   Waiting for exporter to start..."
sleep 5

# Check if exporter is running
if docker ps | grep -q unicorn-dcgm-exporter; then
    echo -e "${GREEN}✅ DCGM Exporter deployed successfully${NC}"
else
    echo -e "${RED}❌ ERROR: DCGM Exporter failed to start${NC}"
    docker logs unicorn-dcgm-exporter
    exit 1
fi

# Test exporter endpoint
echo "   Testing exporter endpoint..."
if curl -s http://localhost:${GPU_EXPORTER_PORT}/metrics | grep -q DCGM; then
    echo -e "${GREEN}✅ Exporter metrics endpoint working${NC}"
    echo "   Sample metrics:"
    curl -s http://localhost:${GPU_EXPORTER_PORT}/metrics | grep "DCGM_FI_DEV_GPU_UTIL" | head -2
else
    echo -e "${YELLOW}⚠️  WARNING: No DCGM metrics found yet (may need a few seconds)${NC}"
fi

echo ""

# Step 4: Update Prometheus Configuration
echo "📊 Step 4: Updating Prometheus Configuration..."
echo ""

# Check if Prometheus config file exists
PROMETHEUS_CONFIG="/opt/uc-cloud/monitoring/prometheus-config.yml"
if [ ! -f "$PROMETHEUS_CONFIG" ]; then
    PROMETHEUS_CONFIG="/opt/ops-center/monitoring/prometheus-config.yml"
fi

if [ ! -f "$PROMETHEUS_CONFIG" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Prometheus config not found at expected locations${NC}"
    echo "   You'll need to manually add this scrape config to prometheus.yml:"
    echo ""
    echo "  - job_name: 'gpu'"
    echo "    static_configs:"
    echo "      - targets: ['unicorn-dcgm-exporter:9400']"
    echo ""
else
    # Backup config
    cp "$PROMETHEUS_CONFIG" "${PROMETHEUS_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅ Backed up Prometheus config${NC}"

    # Check if GPU job already exists
    if grep -q "job_name: 'gpu'" "$PROMETHEUS_CONFIG"; then
        echo -e "${YELLOW}⚠️  GPU scrape config already exists${NC}"
    else
        # Add GPU scrape config
        cat >> "$PROMETHEUS_CONFIG" <<'EOF'

  # GPU Metrics (DCGM Exporter)
  - job_name: 'gpu'
    scrape_interval: 15s
    static_configs:
      - targets: ['unicorn-dcgm-exporter:9400']
        labels:
          service: 'gpu-monitoring'
EOF
        echo -e "${GREEN}✅ Added GPU scrape config to Prometheus${NC}"
    fi

    # Reload Prometheus
    echo "   Reloading Prometheus configuration..."
    curl -X POST ${PROMETHEUS_URL}/-/reload || echo -e "${YELLOW}⚠️  Could not reload Prometheus (may need manual restart)${NC}"
fi

echo ""

# Step 5: Import Grafana Dashboard
echo "📈 Step 5: Importing GPU Monitoring Dashboard..."
echo ""

# Check if dashboard JSON exists
if [ ! -f "/tmp/gpu-monitoring-dashboard.json" ]; then
    echo -e "${RED}❌ ERROR: Dashboard JSON not found at /tmp/gpu-monitoring-dashboard.json${NC}"
    echo "   Please create the dashboard JSON first."
    exit 1
fi

# Import dashboard via API
IMPORT_RESULT=$(curl -s -X POST \
  "${GRAFANA_URL}/api/dashboards/db" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @/tmp/gpu-monitoring-dashboard.json)

if echo "$IMPORT_RESULT" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✅ Dashboard imported successfully${NC}"
    DASHBOARD_UID=$(echo "$IMPORT_RESULT" | grep -o '"uid":"[^"]*"' | cut -d'"' -f4)
    echo "   Dashboard UID: ${DASHBOARD_UID}"
    echo "   Dashboard URL: ${GRAFANA_URL}/d/${DASHBOARD_UID}/gpu-monitoring"
elif echo "$IMPORT_RESULT" | grep -q '"message":"Dashboard not found"'; then
    echo -e "${YELLOW}⚠️  Dashboard already exists, updating...${NC}"
else
    echo -e "${RED}❌ ERROR: Dashboard import failed${NC}"
    echo "   Response: ${IMPORT_RESULT}"
fi

echo ""

# Step 6: Verify Integration
echo "🔍 Step 6: Verifying Integration..."
echo ""

# Wait for Prometheus to scrape
echo "   Waiting for Prometheus to scrape GPU metrics (15 seconds)..."
sleep 15

# Check Prometheus targets
echo "   Checking Prometheus targets..."
TARGETS=$(curl -s "${PROMETHEUS_URL}/api/v1/targets" | grep -o '"job":"gpu"' | wc -l)
if [ "$TARGETS" -gt 0 ]; then
    echo -e "${GREEN}✅ GPU target found in Prometheus${NC}"
else
    echo -e "${YELLOW}⚠️  GPU target not yet visible in Prometheus${NC}"
fi

# Check for GPU metrics in Prometheus
echo "   Checking for GPU metrics..."
GPU_METRICS=$(curl -s "${PROMETHEUS_URL}/api/v1/label/__name__/values" | grep -c "DCGM\|nvidia_gpu" || echo "0")
if [ "$GPU_METRICS" -gt 0 ]; then
    echo -e "${GREEN}✅ Found ${GPU_METRICS} GPU metrics in Prometheus${NC}"
else
    echo -e "${YELLOW}⚠️  No GPU metrics found yet (may need more time)${NC}"
fi

echo ""

# Step 7: Test Dashboard
echo "🎨 Step 7: Testing Dashboard..."
echo ""

# Get dashboard status
DASHBOARD_STATUS=$(curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "${GRAFANA_URL}/api/dashboards/uid/gpu-monitoring-v1")

if echo "$DASHBOARD_STATUS" | grep -q '"title":"GPU Monitoring Dashboard"'; then
    echo -e "${GREEN}✅ Dashboard accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Dashboard may not be ready yet${NC}"
fi

echo ""

# Final Summary
echo "=========================================="
echo "📊 GPU Monitoring Deployment Complete!"
echo "=========================================="
echo ""
echo "📍 Access Points:"
echo "   • GPU Exporter Metrics: http://localhost:${GPU_EXPORTER_PORT}/metrics"
echo "   • Grafana Dashboard: ${GRAFANA_URL}/d/gpu-monitoring-v1/gpu-monitoring"
echo "   • Prometheus Targets: ${PROMETHEUS_URL}/targets"
echo ""
echo "🔧 Management Commands:"
echo "   • View exporter logs: docker logs unicorn-dcgm-exporter -f"
echo "   • Restart exporter: docker restart unicorn-dcgm-exporter"
echo "   • Stop exporter: docker compose -f /tmp/docker-compose.gpu.yml down"
echo ""
echo "📝 Next Steps:"
echo "   1. Open Grafana dashboard and verify panels are loading data"
echo "   2. Configure alerts for temperature/utilization thresholds"
echo "   3. Add GPU monitoring link to Ops-Center UI"
echo "   4. Update Ops-Center .env.auth with Grafana API key"
echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""
