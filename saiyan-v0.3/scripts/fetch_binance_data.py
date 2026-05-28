#!/usr/bin/env python3
"""
Télécharge données fraîches depuis Binance API
Usage: python scripts/fetch_binance_data.py --symbol BTCUSDT --days 60
"""

import argparse
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path

def fetch_binance_klines(symbol: str = "BTCUSDT", interval: str = "1d", 
                         days: int = 60) -> pd.DataFrame:
    """
    Fetch klines/candlestick data from Binance public API
    
    Args:
        symbol: Trading pair (BTCUSDT, ETHUSDT, etc.)
        interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
        days: Number of days to fetch
    
    Returns:
        DataFrame with OHLCV data
    """
    base_url = "https://api.binance.com/api/v3/klines"
    
    # Calculate time range
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (days * 24 * 60 * 60 * 1000)
    
    all_data = []
    current_start = start_time
    
    print(f"📊 Fetching {symbol} {interval} data for last {days} days...")
    
    while current_start < end_time:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': current_start,
            'limit': 1000  # Max per request
        }
        
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            break
        
        all_data.extend(data)
        
        # Move to next batch
        current_start = data[-1][0] + 1
        
        print(f"  Fetched {len(all_data)} candles...")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    # Convert types
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    # Select columns
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
    
    print(f"✅ Total: {len(df)} candles")
    print(f"   Range: {df['date'].iloc[0]} → {df['date'].iloc[-1]}")
    print(f"   Last close: ${df['close'].iloc[-1]:.2f}")
    
    return df


def main():
    parser = argparse.ArgumentParser(description='Fetch fresh Binance data')
    parser.add_argument('--symbol', type=str, default='BTCUSDT',
                       help='Trading pair (default: BTCUSDT)')
    parser.add_argument('--interval', type=str, default='1d',
                       help='Candlestick interval (default: 1d)')
    parser.add_argument('--days', type=int, default=60,
                       help='Number of days to fetch (default: 60)')
    parser.add_argument('--output', type=str,
                       help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Fetch data
    df = fetch_binance_klines(
        symbol=args.symbol,
        interval=args.interval,
        days=args.days
    )
    
    # Save if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"💾 Saved to: {output_path}")
    else:
        # Default save location
        output_dir = Path('/root/.openclaw/workspace/saiyan-v0.3/data')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{args.symbol.lower()}_{args.interval}_fresh.csv"
        df.to_csv(output_file, index=False)
        print(f"💾 Saved to: {output_file}")


if __name__ == '__main__':
    main()
