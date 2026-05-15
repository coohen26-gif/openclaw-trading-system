#!/bin/bash
# Gateway Watchdog - Script de surveillance et restart auto
# À utiliser en backup du cron job OpenClaw

LOG_FILE="/root/.openclaw/workspace/logs/gateway-watchdog.log"
ALERT_FILE="/root/.openclaw/workspace/logs/gateway-alerts.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

alert() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ ALERTE: $1" >> "$ALERT_FILE"
    log "ALERTE: $1"
}

log "=== Gateway Watchdog Check ==="

# Check status
STATUS=$(openclaw gateway status 2>&1)
STATE=$(echo "$STATUS" | grep "Runtime:" | awk '{print $2}')

log "Gateway status: $STATE"

if [[ "$STATE" == "stopped" || "$STATE" == "deactivating" || "$STATE" == "failed" ]]; then
    alert "Gateway DOWN (state: $STATE) - Tentative de restart..."
    
    # Restart
    log "Restarting gateway..."
    systemctl --user restart openclaw-gateway.service
    sleep 10
    
    # Re-check
    STATUS2=$(openclaw gateway status 2>&1)
    STATE2=$(echo "$STATUS2" | grep "Runtime:" | awk '{print $2}')
    
    if [[ "$STATE2" == "running" || "$STATE2" == "active" ]]; then
        log "✅ Gateway restarted successfully (new state: $STATE2)"
        exit 0
    else
        alert "❌ ECHEC restart gateway (state: $STATE2) - Intervention humaine requise!"
        exit 1
    fi
else
    log "✅ Gateway OK (state: $STATE)"
    exit 0
fi
