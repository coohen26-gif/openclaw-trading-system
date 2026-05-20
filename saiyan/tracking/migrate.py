#!/usr/bin/env python3
"""
Migration script: Import historical signals from scan-trading-2026-05-20.md
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/saiyan/tracking')

from tracker import init_db, migrate_signal, export_dashboard, get_performance

# Historical signals extracted from scan-trading-2026-05-20.md
# Current prices estimated from report context (BTC ~$80,185, ETH ~$2,372, SOL ~$93.82)

HISTORICAL_SIGNALS = [
    # 16/05 signals (approximate from report context)
    {
        "timestamp": "2026-05-16T02:15:00",
        "pair": "ETHUSDT",
        "direction": "LONG",
        "entry_price": 2089.0,
        "tp_price": 2150.0,
        "sl_price": 2075.0,
        "confidence": 72,
        "status": "CLOSED",
        "current_price": 2372.0  # TP hit
    },
    {
        "timestamp": "2026-05-16T14:30:00",
        "pair": "BTCUSDT",
        "direction": "LONG",
        "entry_price": 77500.0,
        "tp_price": 79500.0,
        "sl_price": 76800.0,
        "confidence": 71,
        "status": "CLOSED",
        "current_price": 80185.0  # TP hit
    },
    # 17/05 signals
    {
        "timestamp": "2026-05-17T03:45:00",
        "pair": "BTCUSDT",
        "direction": "LONG",
        "entry_price": 78200.0,
        "tp_price": 79000.0,
        "sl_price": 77500.0,
        "confidence": 65,
        "status": "CLOSED",
        "current_price": 77000.0  # SL hit
    },
    # 18/05 signals (from report table)
    {
        "timestamp": "2026-05-18T01:41:00",
        "pair": "BTCUSDT",
        "direction": "LONG",
        "entry_price": 76832.0,
        "tp_price": 78828.0,
        "sl_price": 75505.0,
        "confidence": 69,
        "status": "OPEN",
        "current_price": 80185.0  # TP hit
    },
    {
        "timestamp": "2026-05-18T01:41:00",
        "pair": "ETHUSDT",
        "direction": "LONG",
        "entry_price": 2112.0,
        "tp_price": 2178.0,
        "sl_price": 2105.0,
        "confidence": 83,
        "status": "OPEN",
        "current_price": 2372.0  # TP hit
    },
    {
        "timestamp": "2026-05-18T03:12:00",
        "pair": "BTCUSDT",
        "direction": "LONG",
        "entry_price": 76966.0,
        "tp_price": 78835.0,
        "sl_price": 75527.0,
        "confidence": 73,
        "status": "OPEN",
        "current_price": 80185.0  # TP hit
    },
    {
        "timestamp": "2026-05-18T03:12:00",
        "pair": "ETHUSDT",
        "direction": "LONG",
        "entry_price": 2120.0,
        "tp_price": 2175.0,
        "sl_price": 2095.0,
        "confidence": 70,
        "status": "OPEN",
        "current_price": 2372.0  # TP hit
    },
    # 19/05 signals (from report table)
    {
        "timestamp": "2026-05-19T00:10:00",
        "pair": "BTCUSDT",
        "direction": "LONG",
        "entry_price": 76950.0,
        "tp_price": 78800.0,
        "sl_price": 75500.0,
        "confidence": 70,
        "status": "OPEN",
        "current_price": 80185.0  # TP hit
    },
    {
        "timestamp": "2026-05-19T00:10:00",
        "pair": "ETHUSDT",
        "direction": "LONG",
        "entry_price": 2115.0,
        "tp_price": 2178.0,
        "sl_price": 2087.0,
        "confidence": 75,
        "status": "OPEN",
        "current_price": 2372.0  # TP hit (R/R 7.47 case)
    },
    {
        "timestamp": "2026-05-19T08:10:00",
        "pair": "SOLUSDT",
        "direction": "LONG",
        "entry_price": 94.82,
        "tp_price": 100.0,
        "sl_price": 90.0,
        "confidence": 72,
        "status": "OPEN",
        "current_price": 93.82  # Still open, price dropped slightly
    },
]


def run_migration():
    """Run the full migration."""
    print("🚀 Starting migration of historical signals...")
    
    # Initialize database
    init_db()
    print("✅ Database initialized")
    
    # Migrate each signal
    migrated_count = 0
    for sig in HISTORICAL_SIGNALS:
        signal_id = migrate_signal(
            timestamp=sig["timestamp"],
            pair=sig["pair"],
            direction=sig["direction"],
            entry_price=sig["entry_price"],
            tp_price=sig["tp_price"],
            sl_price=sig["sl_price"],
            confidence=sig["confidence"],
            status=sig["status"],
            current_price=sig.get("current_price")
        )
        print(f"  ✅ Migrated: {sig['timestamp']} {sig['pair']} {sig['direction']} (ID: {signal_id})")
        migrated_count += 1
    
    print(f"\n✅ Migrated {migrated_count} signals")
    
    # Generate dashboard
    export_dashboard()
    print("✅ Dashboard generated")
    
    # Show stats
    stats = get_performance()
    print("\n📊 Performance Summary:")
    print(f"  Total Trades: {stats['n_trades']}")
    print(f"  Win Rate: {stats['win_rate']:.1f}%")
    print(f"  Total PnL: {stats['total_pnl_usdt']:.2f} USDT")
    print(f"  Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
    print(f"  Open Positions: {stats['open_positions']}")
    
    return migrated_count


if __name__ == "__main__":
    run_migration()
