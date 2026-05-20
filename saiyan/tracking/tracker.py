#!/usr/bin/env python3
"""
Saiyan Trading Position Tracker
SQLite-based tracking for signals, positions, and performance metrics.
"""

import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, List, Any
import math

DB_PATH = Path(__file__).parent / "positions.db"
DASHBOARD_PATH = Path(__file__).parent / "dashboard.md"


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Signals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            pair TEXT NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('LONG', 'SHORT')),
            entry_price REAL NOT NULL,
            tp_price REAL NOT NULL,
            sl_price REAL NOT NULL,
            confidence INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'CLOSED', 'TP_HIT', 'SL_HIT', 'BREAKEVEN')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Positions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            exit_price REAL,
            pnl_usdt REAL,
            pnl_percent REAL,
            R_ratio REAL,
            outcome TEXT CHECK(outcome IN ('WIN', 'LOSS', 'BREAKEVEN')),
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        )
    """)
    
    # Performance table (daily aggregates)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            n_trades INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            total_pnl REAL DEFAULT 0,
            win_rate REAL,
            avg_R REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def log_signal(
    timestamp: str,
    pair: str,
    direction: str,
    entry_price: float,
    tp_price: float,
    sl_price: float,
    confidence: int,
    status: str = "OPEN"
) -> int:
    """
    Log a new trading signal.
    Returns the signal ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO signals (timestamp, pair, direction, entry_price, tp_price, sl_price, confidence, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, pair, direction, entry_price, tp_price, sl_price, confidence, status))
    
    signal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return signal_id


def update_position(
    signal_id: int,
    current_price: float,
    exit_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check if TP or SL has been hit for a signal and update position accordingly.
    Returns position update info.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get signal details
    cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
    signal = cursor.fetchone()
    
    if not signal:
        conn.close()
        return {"error": "Signal not found"}
    
    entry_price = signal["entry_price"]
    tp_price = signal["tp_price"]
    sl_price = signal["sl_price"]
    direction = signal["direction"]
    current_status = signal["status"]
    
    if current_status != "OPEN":
        conn.close()
        return {"status": "already_closed", "outcome": current_status}
    
    # Determine if TP or SL hit
    new_status = "OPEN"
    outcome = None
    pnl_usdt = 0
    pnl_percent = 0
    
    if direction == "LONG":
        if current_price >= tp_price:
            new_status = "TP_HIT"
            outcome = "WIN"
            exit_price = tp_price
        elif current_price <= sl_price:
            new_status = "SL_HIT"
            outcome = "LOSS"
            exit_price = sl_price
        else:
            conn.close()
            return {"status": "still_open", "current_price": current_price}
    else:  # SHORT
        if current_price <= tp_price:
            new_status = "TP_HIT"
            outcome = "WIN"
            exit_price = tp_price
        elif current_price >= sl_price:
            new_status = "SL_HIT"
            outcome = "LOSS"
            exit_price = sl_price
        else:
            conn.close()
            return {"status": "still_open", "current_price": current_price}
    
    # Calculate PnL
    if direction == "LONG":
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
    else:
        pnl_percent = ((entry_price - exit_price) / entry_price) * 100
    
    # Assume 1 unit position for pnl_usdt calculation
    pnl_usdt = pnl_percent * entry_price / 100
    
    # Calculate R ratio (reward/risk based on original TP-SL distances)
    risk = abs(entry_price - sl_price)
    reward = abs(tp_price - entry_price)
    R_ratio = reward / risk if risk > 0 else 0
    
    if exit_time is None:
        exit_time = datetime.utcnow().isoformat()
    
    # Update signal status
    cursor.execute("UPDATE signals SET status = ? WHERE id = ?", (new_status, signal_id))
    
    # Insert position record
    cursor.execute("""
        INSERT INTO positions (signal_id, entry_time, exit_time, exit_price, pnl_usdt, pnl_percent, R_ratio, outcome)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (signal_id, signal["timestamp"], exit_time, exit_price, pnl_usdt, pnl_percent, R_ratio, outcome))
    
    conn.commit()
    conn.close()
    
    return {
        "status": "closed",
        "new_status": new_status,
        "outcome": outcome,
        "exit_price": exit_price,
        "pnl_percent": pnl_percent,
        "pnl_usdt": pnl_usdt,
        "R_ratio": R_ratio
    }


def get_performance(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get performance statistics including Win Rate, Total PnL, Sharpe Ratio.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all closed positions
    query = """
        SELECT p.*, s.pair, s.direction, s.timestamp as signal_time
        FROM positions p
        JOIN signals s ON p.signal_id = s.id
        WHERE p.outcome IS NOT NULL
    """
    params = []
    
    if start_date:
        query += " AND date(p.exit_time) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date(p.exit_time) <= ?"
        params.append(end_date)
    
    cursor.execute(query, params)
    positions = cursor.fetchall()
    
    # Calculate metrics
    n_trades = len(positions)
    wins = sum(1 for p in positions if p["outcome"] == "WIN")
    losses = sum(1 for p in positions if p["outcome"] == "LOSS")
    breakevens = sum(1 for p in positions if p["outcome"] == "BREAKEVEN")
    
    win_rate = (wins / n_trades * 100) if n_trades > 0 else 0
    total_pnl = sum(p["pnl_usdt"] for p in positions)
    avg_pnl = total_pnl / n_trades if n_trades > 0 else 0
    
    # Calculate Sharpe Ratio (simplified, assuming risk-free rate = 0)
    if n_trades > 1:
        pnl_values = [p["pnl_percent"] for p in positions]
        mean_pnl = sum(pnl_values) / len(pnl_values)
        variance = sum((x - mean_pnl) ** 2 for x in pnl_values) / len(pnl_values)
        std_pnl = math.sqrt(variance) if variance > 0 else 0
        sharpe_ratio = (mean_pnl / std_pnl * math.sqrt(252)) if std_pnl > 0 else 0  # Annualized
    else:
        sharpe_ratio = 0
    
    # Average R ratio
    avg_R = sum(p["R_ratio"] for p in positions) / n_trades if n_trades > 0 else 0
    
    # Get open positions count
    cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'OPEN'")
    open_positions = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "n_trades": n_trades,
        "wins": wins,
        "losses": losses,
        "breakevens": breakevens,
        "win_rate": win_rate,
        "total_pnl_usdt": total_pnl,
        "avg_pnl_percent": avg_pnl,
        "sharpe_ratio": sharpe_ratio,
        "avg_R_ratio": avg_R,
        "open_positions": open_positions
    }


def export_dashboard() -> str:
    """
    Generate a Markdown dashboard with current performance stats.
    Returns the dashboard content and saves it to dashboard.md.
    """
    stats = get_performance()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get recent signals
    cursor.execute("""
        SELECT * FROM signals ORDER BY timestamp DESC LIMIT 10
    """)
    recent_signals = cursor.fetchall()
    
    # Get recent closed positions
    cursor.execute("""
        SELECT p.*, s.pair, s.direction 
        FROM positions p 
        JOIN signals s ON p.signal_id = s.id 
        ORDER BY p.exit_time DESC LIMIT 10
    """)
    recent_positions = cursor.fetchall()
    
    # Get daily performance
    cursor.execute("""
        SELECT * FROM performance ORDER BY date DESC LIMIT 7
    """)
    daily_perf = cursor.fetchall()
    
    conn.close()
    
    now = datetime.utcnow().isoformat()
    
    dashboard = f"""# 📊 Saiyan Trading Dashboard

**Generated:** {now} UTC  
**Database:** `{DB_PATH.name}`

---

## 🎯 Performance Overview

| Metric | Value |
|---|---|
| **Total Trades** | {stats['n_trades']} |
| **Wins** | {stats['wins']} ✅ |
| **Losses** | {stats['losses']} ❌ |
| **Breakevens** | {stats['breakevens']} ➖ |
| **Win Rate** | {stats['win_rate']:.1f}% |
| **Total PnL** | {stats['total_pnl_usdt']:.2f} USDT |
| **Avg PnL/Trade** | {stats['avg_pnl_percent']:.2f}% |
| **Sharpe Ratio** | {stats['sharpe_ratio']:.2f} |
| **Avg R/Ratio** | {stats['avg_R_ratio']:.2f} |
| **Open Positions** | {stats['open_positions']} 🟡 |

---

## 📈 Recent Signals

| Timestamp | Pair | Direction | Entry | TP | SL | Confidence | Status |
|---|---|---|---|---|---|---|---|
"""
    
    for sig in recent_signals:
        status_emoji = {"OPEN": "🟡", "TP_HIT": "✅", "SL_HIT": "❌", "CLOSED": "⚪", "BREAKEVEN": "➖"}.get(sig["status"], "⚪")
        dashboard += f"| {sig['timestamp']} | {sig['pair']} | {sig['direction']} | {sig['entry_price']:.2f} | {sig['tp_price']:.2f} | {sig['sl_price']:.2f} | {sig['confidence']}/100 | {status_emoji} {sig['status']} |\n"
    
    dashboard += """
---

## 💰 Closed Positions

| Exit Time | Pair | Direction | Entry | Exit | PnL % | PnL USDT | R/R | Outcome |
|---|---|---|---|---|---|---|---|---|
"""
    
    for pos in recent_positions:
        outcome_emoji = {"WIN": "✅", "LOSS": "❌", "BREAKEVEN": "➖"}.get(pos["outcome"], "⚪")
        dashboard += f"| {pos['exit_time']} | {pos['pair']} | {pos['direction']} | {pos['entry_time']} | {pos['exit_price']:.2f} | {pos['pnl_percent']:.2f}% | {pos['pnl_usdt']:.2f} | {pos['R_ratio']:.2f} | {outcome_emoji} {pos['outcome']} |\n"
    
    if not recent_positions:
        dashboard += "| - | - | - | - | - | - | - | - | - |\n"
    
    dashboard += """
---

## 📅 Daily Performance (Last 7 Days)

| Date | Trades | Wins | Losses | Win Rate | Total PnL | Avg R |
|---|---|---|---|---|---|---|
"""
    
    for perf in daily_perf:
        wr = (perf["wins"] / perf["n_trades"] * 100) if perf["n_trades"] > 0 else 0
        dashboard += f"| {perf['date']} | {perf['n_trades']} | {perf['wins']} | {perf['losses']} | {wr:.1f}% | {perf['total_pnl']:.2f} | {perf['avg_R']:.2f} |\n"
    
    if not daily_perf:
        dashboard += "| - | - | - | - | - | - | - |\n"
    
    dashboard += f"""
---

## 📝 Notes

- Data sourced from SQLite database at `{DB_PATH}`
- PnL calculated assuming 1 unit position size per trade
- Sharpe Ratio annualized (√252)
- R/Ratio = Reward/Risk based on original TP-SL distances

---

*Auto-generated by Saiyan Trading Tracker*
"""
    
    # Save to file
    with open(DASHBOARD_PATH, "w") as f:
        f.write(dashboard)
    
    return dashboard


def update_daily_performance(target_date: Optional[str] = None):
    """Update daily performance aggregates."""
    if target_date is None:
        target_date = date.today().isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get positions closed on this date
    cursor.execute("""
        SELECT 
            COUNT(*) as n_trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
            SUM(pnl_usdt) as total_pnl,
            AVG(R_ratio) as avg_R
        FROM positions p
        JOIN signals s ON p.signal_id = s.id
        WHERE date(p.exit_time) = ?
    """, (target_date,))
    
    row = cursor.fetchone()
    
    if row["n_trades"] > 0:
        win_rate = (row["wins"] / row["n_trades"]) * 100
    else:
        win_rate = 0
    
    cursor.execute("""
        INSERT OR REPLACE INTO performance (date, n_trades, wins, losses, total_pnl, win_rate, avg_R, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (target_date, row["n_trades"], row["wins"], row["losses"], 
          row["total_pnl"] or 0, win_rate, row["avg_R"] or 0))
    
    conn.commit()
    conn.close()


def migrate_signal(
    timestamp: str,
    pair: str,
    direction: str,
    entry_price: float,
    tp_price: float,
    sl_price: float,
    confidence: int,
    status: str = "OPEN",
    current_price: Optional[float] = None
) -> int:
    """
    Migrate a historical signal into the database.
    If current_price is provided and signal is OPEN, check for TP/SL hits.
    Returns signal ID.
    """
    signal_id = log_signal(timestamp, pair, direction, entry_price, tp_price, sl_price, confidence, status)
    
    if current_price and status == "OPEN":
        update_position(signal_id, current_price)
    
    return signal_id


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tracker.py <command> [args]")
        print("Commands:")
        print("  init              - Initialize database")
        print("  dashboard         - Generate dashboard")
        print("  stats             - Show performance stats")
        print("  migrate           - Run migration from reports")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        init_db()
        print("✅ Database initialized")
    
    elif command == "dashboard":
        init_db()
        content = export_dashboard()
        print(f"✅ Dashboard generated at {DASHBOARD_PATH}")
    
    elif command == "stats":
        init_db()
        stats = get_performance()
        print("\n📊 Performance Stats:")
        print(f"  Trades: {stats['n_trades']}")
        print(f"  Win Rate: {stats['win_rate']:.1f}%")
        print(f"  Total PnL: {stats['total_pnl_usdt']:.2f} USDT")
        print(f"  Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
        print(f"  Avg R/Ratio: {stats['avg_R_ratio']:.2f}")
        print(f"  Open Positions: {stats['open_positions']}")
    
    elif command == "migrate":
        init_db()
        # Migration will be handled separately
        print("Migration script ready")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
