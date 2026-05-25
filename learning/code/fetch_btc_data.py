#!/usr/bin/env python3
"""
Fetch BTC/USDT daily data from Binance (2020-2026)
Save to learning/data/btc_usdt_daily.csv
"""

import ccxt
import pandas as pd
from datetime import datetime
import os

def fetch_btc_data():
    """Fetch BTC/USDT daily OHLCV from Binance"""
    
    # Initialize Binance (public API, no auth needed for OHLCV)
    exchange = ccxt.binance()
    
    print("📊 Fetching BTC/USDT daily data from Binance...")
    
    # Fetch all daily candles since 2020-01-01
    since = exchange.parse8601('2020-01-01T00:00:00Z')
    timeframe = '1d'
    
    all_ohlcv = []
    current_since = since
    
    # Binance limit: 1000 candles per request
    while True:
        print(f"  Fetching batch starting {exchange.iso8601(current_since)}...")
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe, since=current_since, limit=1000)
        
        if not ohlcv:
            break
            
        all_ohlcv.extend(ohlcv)
        
        # Move to next batch
        current_since = ohlcv[-1][0] + 86400000  # +1 day
        
        # Stop if we've reached today
        if ohlcv[-1][0] > exchange.parse8601(datetime.now().strftime('%Y-%m-%dT00:00:00Z')):
            break
    
    # Convert to DataFrame
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Sort by date
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"\n✅ Data fetched successfully!")
    print(f"   Rows: {len(df)}")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"   Price range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")
    
    # Save to CSV
    os.makedirs('data', exist_ok=True)
    output_path = 'data/btc_usdt_daily.csv'
    df.to_csv(output_path, index=False)
    print(f"   Saved to: {output_path}")
    
    # Display sample
    print("\n📋 Sample data:")
    print(df.head(10))
    
    return df

if __name__ == '__main__':
    fetch_btc_data()
