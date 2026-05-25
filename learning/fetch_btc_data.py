#!/usr/bin/env python3
"""Fetch historical BTC/USDT data from Binance via CCXT."""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os

def fetch_ohlcv(symbol='BTC/USDT', timeframe='1h', limit=5000):
    """Fetch OHLCV data from Binance."""
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    
    # Fetch data
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    
    # Convert to DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    return df

def fetch_historical_data(symbol='BTC/USDT', timeframe='1h', months=12):
    """Fetch historical data going back several months."""
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months*30)
    
    # Convert to milliseconds
    since = int(start_date.timestamp() * 1000)
    
    all_data = []
    
    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        
        if not ohlcv:
            break
            
        all_data.extend(ohlcv)
        
        # Get the last timestamp
        last_timestamp = ohlcv[-1][0]
        
        # If we've reached recent data, stop
        if datetime.fromtimestamp(last_timestamp/1000) > end_date - timedelta(hours=1):
            break
            
        # Move since forward
        since = last_timestamp + 1
        
        print(f"Fetched batch, last date: {datetime.fromtimestamp(last_timestamp/1000)}")
    
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    
    # Filter to desired date range
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    return df

if __name__ == '__main__':
    os.makedirs('/root/.openclaw/workspace/learning/data', exist_ok=True)
    
    timeframes = {
        '5m': '5m',
        '1h': '1h',
        '1d': '1d'
    }
    
    for name, tf in timeframes.items():
        print(f"\nFetching {name} data...")
        try:
            if name == '5m':
                # For 5m, fetch recent 3 months (more granular)
                df = fetch_historical_data(timeframe=tf, months=6)
            elif name == '1h':
                df = fetch_historical_data(timeframe=tf, months=12)
            else:  # daily
                df = fetch_historical_data(timeframe=tf, months=24)
            
            print(f"Got {len(df)} records for {name}")
            print(f"Date range: {df.index.min()} to {df.index.max()}")
            
            # Save to CSV
            df.to_csv(f'/root/.openclaw/workspace/learning/data/btc_{name}.csv')
            print(f"Saved to btc_{name}.csv")
            
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            # Try fallback with simple fetch
            try:
                df = fetch_ohlcv(limit=5000)
                print(f"Fallback: got {len(df)} records for {name}")
                df.to_csv(f'/root/.openclaw/workspace/learning/data/btc_{name}_fallback.csv')
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
