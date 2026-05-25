#!/bin/bash
# update-positions.sh - Update paper trading positions with live prices
# Run at each heartbeat to track PnL, duration, and TP/SL hits
# 
# Usage: ./scripts/update-positions.sh [--commit]
#   --commit: Auto commit and push changes after update

set -e

WORKSPACE="/root/.openclaw/workspace"
POSITIONS_FILE="$WORKSPACE/dashboard/positions-paper.json"
REPORTS_DIR="$WORKSPACE/reports"
MEMORY_DIR="$WORKSPACE/memory"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE=$(date -u +"%Y-%m-%d")

echo "📊 Updating paper positions at $TIMESTAMP"

# Check if positions file exists
if [ ! -f "$POSITIONS_FILE" ]; then
    echo "❌ Error: $POSITIONS_FILE not found"
    exit 1
fi

# Fetch current prices (using CoinGecko free API - no auth required)
echo "📈 Fetching live prices..."

# CoinGecko API endpoints
BTC_PRICE=$(curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd" 2>/dev/null | jq -r '.bitcoin.usd' || echo "null")
ETH_PRICE=$(curl -s "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd" 2>/dev/null | jq -r '.ethereum.usd' || echo "null")
SOL_PRICE=$(curl -s "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd" 2>/dev/null | jq -r '.solana.usd' || echo "null")

echo "   BTC: $BTC_PRICE USD"
echo "   ETH: $ETH_PRICE USD"
echo "   SOL: $SOL_PRICE USD"

# Create backup
cp "$POSITIONS_FILE" "${POSITIONS_FILE}.bak.$(date +%s)"

# Update positions using jq
echo "🔄 Updating positions..."

jq --arg ts "$TIMESTAMP" \
   --argjson btc "$BTC_PRICE" \
   --argjson eth "$ETH_PRICE" \
   --argjson sol "$SOL_PRICE" '
# Helper function to calculate PnL
def calc_pnl(entry; current; type):
  if type == "LONG" then
    if current == null or entry == null then null
    else ((current - entry) / entry * 100) | . * 100 | round / 100
    end
  else null
  end;

# Helper function to check TP/SL
def check_status(entry; tp; sl; current; type):
  if current == null then "OPEN"
  elif type == "LONG" then
    if tp != null and current >= tp then "TP_HIT"
    elif sl != null and current <= sl then "SL_HIT"
    else "OPEN"
    end
  else "OPEN"
  end;

# Helper function to calculate duration
def calc_duration(start_ts; current_ts):
  # Simple approximation: parse ISO dates and calculate hours
  # This is a simplified version - production would use proper date math
  null;

# Update each position
.positions |= map(
  . as $pos |
  ($pos.asset | split("") | map(if . == "USDT" then "" else . end) | join("")) as $base |
  (if $base == "BTC" then $btc elif $base == "ETH" then $eth elif $base == "SOL" then $sol else null end) as $current_price |
  
  $pos |
  .pnl_percent = calc_pnl(.entry_price; $current_price; .type) |
  .status = check_status(.entry_price; .tp_price; .sl_price; $current_price; .type) |
  .last_price_update = $current_price
) |

# Update summary
.summary.last_updated = $ts |
.summary.prices = {
  "BTC": $btc,
  "ETH": $eth,
  "SOL": $sol
}
' "$POSITIONS_FILE" > "${POSITIONS_FILE}.tmp" && mv "${POSITIONS_FILE}.tmp" "$POSITIONS_FILE"

echo "✅ Positions updated"

# Count statuses
OPEN_COUNT=$(jq '[.positions[] | select(.status == "OPEN")] | length' "$POSITIONS_FILE")
TP_COUNT=$(jq '[.positions[] | select(.status == "TP_HIT")] | length' "$POSITIONS_FILE")
SL_COUNT=$(jq '[.positions[] | select(.status == "SL_HIT")] | length' "$POSITIONS_FILE")

echo "📊 Status: $OPEN_COUNT open, $TP_COUNT TP hit, $SL_COUNT SL hit"

# Generate quick summary
if [ "$TP_COUNT" -gt 0 ] || [ "$SL_COUNT" -gt 0 ]; then
    WIN_RATE=$(echo "scale=2; $TP_COUNT * 100 / ($TP_COUNT + $SL_COUNT)" | bc)
    echo "🎯 Win Rate: ${WIN_RATE}%"
fi

# Update metadata
jq --arg ts "$TIMESTAMP" '.metadata.last_updated = $ts' "$POSITIONS_FILE" > "${POSITIONS_FILE}.tmp" && mv "${POSITIONS_FILE}.tmp" "$POSITIONS_FILE"

# Auto-commit if requested
if [ "$1" == "--commit" ]; then
    echo "📦 Committing changes..."
    cd "$WORKSPACE"
    git add dashboard/positions-paper.json
    git commit -m "📊 Update paper positions - $TIMESTAMP" || echo "No changes to commit"
    git push || echo "Push failed (may need auth)"
fi

# Log update
echo "[$TIMESTAMP] Positions updated: $OPEN_COUNT open, $TP_COUNT TP, $SL_COUNT SL" >> "$MEMORY_DIR/positions-update.log"

echo "✅ Update complete"
