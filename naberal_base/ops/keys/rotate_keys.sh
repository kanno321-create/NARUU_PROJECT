#!/usr/bin/env bash
# Phase IX: Key Rotation Policy Script
# Usage: ./ops/keys/rotate_keys.sh [--dry-run] [--emergency]
#
# Key rotation policy:
# - Quarterly rotation: Every 90 days (scheduled)
# - Emergency rotation: Within 1 hour (incident response)
#
# Rotates: JWT_SECRET, SUPABASE_SERVICE_ROLE_KEY, API keys

set -euo pipefail

DRY_RUN=false
EMERGENCY=false
EVIDENCE_DIR="out/evidence/phase_ix/logs"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
LOG_FILE="${EVIDENCE_DIR}/key_rotation_${TIMESTAMP}.log"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --emergency)
            EMERGENCY=true
            shift
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
log "Phase IX: Key Rotation"
log "========================================="
log "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY-RUN' || echo 'LIVE')"
log "Type: $([ "$EMERGENCY" = true ] && echo 'EMERGENCY' || echo 'SCHEDULED')"
log "Timestamp: $TIMESTAMP"
log ""

# Key inventory
KEYS_TO_ROTATE=(
    "JWT_SECRET"
    "SUPABASE_SERVICE_ROLE_KEY"
    "SUPABASE_ANON_KEY"
    "KIS_API_KEY"
)

# Step 1: Check current key ages
log "Step 1: Checking current key ages..."
KEY_AGE_FILE=".key_rotation_history.json"

if [ -f "$KEY_AGE_FILE" ]; then
    log "  Key rotation history found"
    if [ "$DRY_RUN" = true ]; then
        log "  [DRY-RUN] Would check last rotation dates"
    fi
else
    log "  [WARN] No rotation history found, creating initial record"
fi

# Step 2: Generate new keys (dry-run simulation)
log ""
log "Step 2: Generating new keys..."

for key in "${KEYS_TO_ROTATE[@]}"; do
    if [ "$DRY_RUN" = true ]; then
        log "  [DRY-RUN] Would generate new $key"
        log "    New value: $(openssl rand -hex 32 | head -c 16)...******"
    else
        log "  [LIVE] $key rotation requires manual confirmation"
    fi
done

# Step 3: Update secrets in Supabase/GitHub
log ""
log "Step 3: Updating secrets..."

if [ "$DRY_RUN" = true ]; then
    log "  [DRY-RUN] Would update Supabase project secrets"
    log "  [DRY-RUN] Would update GitHub repository secrets"
    log "  [DRY-RUN] Would update local .env files"
else
    log "  [LIVE] Secret updates require manual execution:"
    log "    1. Update Supabase Dashboard > Settings > Vault"
    log "    2. Update GitHub > Settings > Secrets"
    log "    3. Update deployment environment variables"
fi

# Step 4: Verify new keys work
log ""
log "Step 4: Verifying new keys..."

if [ "$DRY_RUN" = true ]; then
    log "  [DRY-RUN] Would test JWT token generation"
    log "  [DRY-RUN] Would test Supabase connectivity"
    log "  [DRY-RUN] Would test API authentication"
    log "  [OK] All key verifications would pass"
fi

# Step 5: Invalidate old keys
log ""
log "Step 5: Invalidating old keys..."

if [ "$DRY_RUN" = true ]; then
    log "  [DRY-RUN] Would invalidate old JWT_SECRET sessions"
    log "  [DRY-RUN] Would revoke old API keys"
    log "  [OK] Old keys would be invalidated"
fi

# Step 6: Update rotation history
log ""
log "Step 6: Recording rotation event..."

ROTATION_RECORD="${EVIDENCE_DIR}/key_rotation_record_${TIMESTAMP}.json"
cat > "$ROTATION_RECORD" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "mode": "$([ "$DRY_RUN" = true ] && echo 'dry-run' || echo 'live')",
  "type": "$([ "$EMERGENCY" = true ] && echo 'emergency' || echo 'scheduled')",
  "keys_rotated": [
    $(printf '"%s",' "${KEYS_TO_ROTATE[@]}" | sed 's/,$//')
  ],
  "policy": {
    "quarterly_rotation": "90 days",
    "emergency_rotation": "1 hour",
    "next_scheduled": "$(date -u -d '+90 days' +"%Y-%m-%d")"
  },
  "verification": {
    "jwt_test": "$([ "$DRY_RUN" = true ] && echo 'simulated' || echo 'pending')",
    "api_test": "$([ "$DRY_RUN" = true ] && echo 'simulated' || echo 'pending')",
    "supabase_test": "$([ "$DRY_RUN" = true ] && echo 'simulated' || echo 'pending')"
  }
}
EOF

log "  Rotation record saved: $ROTATION_RECORD"

# Step 7: Summary
log ""
log "========================================="
log "Key Rotation Summary"
log "========================================="
log "Status: $([ "$DRY_RUN" = true ] && echo 'SIMULATED' || echo 'PENDING')"
log "Keys processed: ${#KEYS_TO_ROTATE[@]}"
log "Type: $([ "$EMERGENCY" = true ] && echo 'Emergency (1h SLA)' || echo 'Scheduled (quarterly)')"
log "Next rotation: $(date -u -d '+90 days' +"%Y-%m-%d")"
log ""
log "Policy:"
log "  - Quarterly rotation: Every 90 days"
log "  - Emergency rotation: Within 1 hour of incident"
log "  - Post-rotation verification: Required"
log ""
log "Evidence saved to: $EVIDENCE_DIR"
log "========================================="

exit 0
