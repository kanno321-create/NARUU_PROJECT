#!/usr/bin/env bash
# Phase IX: Cost Telemetry Export Script
# Usage: ./ops/cost/export_telemetry.sh [--check-threshold PERCENT]
#
# Exports cost and bandwidth telemetry for monitoring.
# Triggers alerts when usage exceeds threshold.

set -euo pipefail

THRESHOLD=80  # Default alert threshold (%)
EVIDENCE_DIR="out/evidence/phase_ix/logs"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
LOG_FILE="${EVIDENCE_DIR}/cost_telemetry_${TIMESTAMP}.log"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure evidence directory exists
mkdir -p "$EVIDENCE_DIR"

log() {
    local msg="[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $1"
    echo "$msg" | tee -a "$LOG_FILE"
}

log "========================================="
log "Phase IX: Cost Telemetry Export"
log "========================================="
log "Alert Threshold: ${THRESHOLD}%"
log "Timestamp: $TIMESTAMP"
log ""

# Budget configuration (from environment or defaults)
MONTHLY_BUDGET=${KIS_MONTHLY_BUDGET:-100}  # USD
BANDWIDTH_LIMIT=${KIS_BANDWIDTH_LIMIT:-50}  # GB

# Step 1: Fetch current usage (simulated for local dev)
log "Step 1: Fetching current usage..."

# In production, these would come from Supabase/Cloud billing APIs
CURRENT_COST=${KIS_CURRENT_COST:-25}  # USD
CURRENT_BANDWIDTH=${KIS_CURRENT_BANDWIDTH:-12}  # GB
DAYS_IN_MONTH=30
DAY_OF_MONTH=$(date +%d)

# Calculate percentages
COST_PERCENT=$((CURRENT_COST * 100 / MONTHLY_BUDGET))
BANDWIDTH_PERCENT=$((CURRENT_BANDWIDTH * 100 / BANDWIDTH_LIMIT))
PROJECTED_COST=$((CURRENT_COST * DAYS_IN_MONTH / DAY_OF_MONTH))

log "  Current cost: \$${CURRENT_COST} / \$${MONTHLY_BUDGET} (${COST_PERCENT}%)"
log "  Current bandwidth: ${CURRENT_BANDWIDTH}GB / ${BANDWIDTH_LIMIT}GB (${BANDWIDTH_PERCENT}%)"
log "  Projected month-end: \$${PROJECTED_COST}"

# Step 2: Check thresholds
log ""
log "Step 2: Checking thresholds..."

ALERTS=()

if [ "$COST_PERCENT" -ge "$THRESHOLD" ]; then
    ALERTS+=("COST: ${COST_PERCENT}% >= ${THRESHOLD}% threshold")
    log "  [ALERT] Cost usage exceeds threshold!"
else
    log "  [OK] Cost within budget (${COST_PERCENT}% < ${THRESHOLD}%)"
fi

if [ "$BANDWIDTH_PERCENT" -ge "$THRESHOLD" ]; then
    ALERTS+=("BANDWIDTH: ${BANDWIDTH_PERCENT}% >= ${THRESHOLD}% threshold")
    log "  [ALERT] Bandwidth usage exceeds threshold!"
else
    log "  [OK] Bandwidth within limit (${BANDWIDTH_PERCENT}% < ${THRESHOLD}%)"
fi

# Step 3: Generate telemetry report
log ""
log "Step 3: Generating telemetry report..."

TELEMETRY_FILE="${EVIDENCE_DIR}/cost_telemetry_${TIMESTAMP}.json"
cat > "$TELEMETRY_FILE" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "period": {
    "month": "$(date +%Y-%m)",
    "day_of_month": $DAY_OF_MONTH,
    "days_remaining": $((DAYS_IN_MONTH - DAY_OF_MONTH))
  },
  "budget": {
    "monthly_limit_usd": $MONTHLY_BUDGET,
    "current_spend_usd": $CURRENT_COST,
    "projected_spend_usd": $PROJECTED_COST,
    "usage_percent": $COST_PERCENT
  },
  "bandwidth": {
    "monthly_limit_gb": $BANDWIDTH_LIMIT,
    "current_usage_gb": $CURRENT_BANDWIDTH,
    "usage_percent": $BANDWIDTH_PERCENT
  },
  "alerts": {
    "threshold_percent": $THRESHOLD,
    "triggered": ${#ALERTS[@]},
    "messages": [
      $(printf '"%s",' "${ALERTS[@]}" 2>/dev/null | sed 's/,$//' || echo '')
    ]
  },
  "services": {
    "supabase": {
      "database_size_mb": 256,
      "storage_size_mb": 512,
      "edge_functions_invocations": 10000
    },
    "github_actions": {
      "minutes_used": 500,
      "minutes_limit": 2000
    }
  },
  "recommendations": [
    $(if [ "$COST_PERCENT" -ge 70 ]; then echo '"Review database query efficiency",'; fi)
    $(if [ "$BANDWIDTH_PERCENT" -ge 70 ]; then echo '"Enable CDN caching for static assets",'; fi)
    "Monitor daily usage trends"
  ]
}
EOF

log "  Telemetry saved: $TELEMETRY_FILE"

# Step 4: Send alerts if needed
log ""
log "Step 4: Processing alerts..."

if [ ${#ALERTS[@]} -gt 0 ]; then
    log "  [WARN] ${#ALERTS[@]} alert(s) triggered:"
    for alert in "${ALERTS[@]}"; do
        log "    - $alert"
    done

    # In production, this would send to Slack/Email/PagerDuty
    log "  [INFO] Alert notification would be sent to:"
    log "    - Slack: #kis-alerts"
    log "    - Email: ops@kis-estimator.com"
else
    log "  [OK] No alerts triggered"
fi

# Step 5: Summary
log ""
log "========================================="
log "Cost Telemetry Summary"
log "========================================="
log "Monthly Budget: \$${MONTHLY_BUDGET}"
log "Current Spend: \$${CURRENT_COST} (${COST_PERCENT}%)"
log "Projected: \$${PROJECTED_COST}"
log "Bandwidth: ${CURRENT_BANDWIDTH}GB / ${BANDWIDTH_LIMIT}GB (${BANDWIDTH_PERCENT}%)"
log "Alerts: ${#ALERTS[@]}"
log ""
log "Thresholds:"
log "  - Warning: 70%"
log "  - Alert: ${THRESHOLD}%"
log "  - Critical: 95%"
log ""
log "Evidence saved to: $EVIDENCE_DIR"
log "========================================="

# Exit with alert status
if [ ${#ALERTS[@]} -gt 0 ]; then
    exit 1
else
    exit 0
fi
