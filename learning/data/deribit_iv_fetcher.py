#!/usr/bin/env python3
"""
Deribit IV Fetcher - Implied Volatility Data for Crypto Options

Module: Master 5 - Derivatives & Advanced Risk
Author: Saiyan Autonomous Trading System
Date: May 26, 2026

Features:
- Fetch IV data from Deribit API (BTC/ETH options)
- Calculate IV percentile and skew
- Vega risk monitoring integration
- Cache IV data (1h freshness)
"""

import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class DeribitIVFetcher:
    """
    Fetch implied volatility data from Deribit API.
    
    Deribit dominates crypto options volume (80%+) → reference for IV.
    
    API Endpoints:
    - GET /api/v2/public/get_volatility: Current IV for asset
    - GET /api/v2/public/get_instruments: Available options contracts
    - GET /api/v2/public/ticker: Mark prices for IV calculation
    """
    
    def __init__(self, cache_dir: str = "data/iv_cache", cache_ttl_hours: int = 1):
        """
        Initialize Deribit IV fetcher.
        
        Args:
            cache_dir: Directory for caching IV data
            cache_ttl_hours: Cache freshness (hours)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.base_url = "https://www.deribit.com/api/v2/public"
        
        print(f"📊 Deribit IV Fetcher initialized")
        print(f"   Cache: {self.cache_dir}")
        print(f"   TTL: {cache_ttl_hours}h")
    
    async def fetch_volatility(self, asset: str = "BTC") -> Optional[Dict]:
        """
        Fetch current implied volatility for asset.
        
        Args:
            asset: Asset symbol (BTC, ETH)
            
        Returns:
            Dict with IV data or None if fetch failed
        """
        url = f"{self.base_url}/get_volatility"
        params = {"instrument": asset}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("jsonrpc") and data.get("result"):
                            result = data["result"]
                            return {
                                "asset": asset,
                                "iv_25d": result.get("volatility_25d", 0) * 100,  # Convert to %
                                "iv_50d": result.get("volatility_50d", 0) * 100,
                                "iv_90d": result.get("volatility_90d", 0) * 100,
                                "timestamp": datetime.utcnow().isoformat()
                            }
        except Exception as e:
            print(f"⚠️  Deribit API error: {e}")
        
        return None
    
    async def fetch_options_chain(self, asset: str = "BTC", currency: str = "BTC") -> Optional[List[Dict]]:
        """
        Fetch options chain for IV skew calculation.
        
        Args:
            asset: Base asset (BTC, ETH)
            currency: Settlement currency (BTC, USD)
            
        Returns:
            List of options with IV data
        """
        url = f"{self.base_url}/get_instruments"
        params = {
            "currency": currency,
            "kind": "option",
            "expired": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("result"):
                            # Filter for asset (e.g., BTC-26MAY26)
                            options = [
                                opt for opt in data["result"]
                                if opt.get("instrument_name", "").startswith(asset)
                            ]
                            return options
        except Exception as e:
            print(f"⚠️  Deribit API error: {e}")
        
        return None
    
    def calculate_iv_skew(self, options: List[Dict]) -> Optional[float]:
        """
        Calculate Put/Call IV skew from options chain.
        
        Skew = Put IV / Call IV
        - Skew > 1.0: Puts more expensive (fear)
        - Skew > 1.3: Elevated fear, often precedes dips
        - Skew < 1.0: Calls more expensive (greed/FOMO)
        
        Args:
            options: List of options from fetch_options_chain
            
        Returns:
            Put/Call IV ratio or None
        """
        if not options:
            return None
        
        # Separate puts and calls
        puts = [opt for opt in options if opt.get("option_type") == "put"]
        calls = [opt for opt in options if opt.get("option_type") == "call"]
        
        if not puts or not calls:
            return None
        
        # Calculate average IV for puts and calls (weighted by mark price)
        put_iv = sum(opt.get("mark_iv", 0) for opt in puts) / len(puts)
        call_iv = sum(opt.get("mark_iv", 0) for opt in calls) / len(calls)
        
        if call_iv == 0:
            return None
        
        skew = put_iv / call_iv
        return skew
    
    def calculate_iv_percentile(self, current_iv: float, historical_iv: List[float]) -> float:
        """
        Calculate current IV percentile vs historical data.
        
        Args:
            current_iv: Current implied volatility (%)
            historical_iv: List of historical IV values (%)
            
        Returns:
            Percentile (0-100)
        """
        if not historical_iv:
            return 50.0  # Default to median if no history
        
        # Count how many historical values are below current
        below = sum(1 for iv in historical_iv if iv < current_iv)
        percentile = (below / len(historical_iv)) * 100
        return percentile
    
    def _get_cache_path(self, asset: str) -> Path:
        """Get cache file path for asset"""
        return self.cache_dir / f"{asset.lower()}_iv_cache.json"
    
    def _load_cache(self, asset: str) -> Optional[Dict]:
        """Load cached IV data if fresh"""
        cache_path = self._get_cache_path(asset)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Check freshness
            cached_time = datetime.fromisoformat(data["timestamp"])
            if datetime.utcnow() - cached_time > self.cache_ttl:
                return None  # Stale cache
            
            return data
        except Exception:
            return None
    
    def _save_cache(self, asset: str, data: Dict):
        """Save IV data to cache"""
        cache_path = self._get_cache_path(asset)
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Cache write error: {e}")
    
    async def get_iv_data(self, asset: str = "BTC") -> Optional[Dict]:
        """
        Get IV data with caching.
        
        Args:
            asset: Asset symbol (BTC, ETH)
            
        Returns:
            Dict with IV metrics or None
        """
        # Try cache first
        cached = self._load_cache(asset)
        if cached:
            print(f"📦 Cache hit for {asset} IV")
            return cached
        
        # Fetch from API
        print(f"🌐 Fetching {asset} IV from Deribit...")
        iv_data = await self.fetch_volatility(asset)
        
        if iv_data:
            # Add IV history for percentile calculation
            history_path = self.cache_dir / f"{asset.lower()}_iv_history.json"
            if history_path.exists():
                with open(history_path, 'r') as f:
                    history = json.load(f)
                history.append(iv_data["iv_25d"])
                history = history[-100:]  # Keep last 100 readings
            else:
                history = [iv_data["iv_25d"]]
            
            with open(history_path, 'w') as f:
                json.dump(history, f)
            
            # Calculate percentile
            iv_data["iv_percentile"] = self.calculate_iv_percentile(
                iv_data["iv_25d"], history
            )
            
            # Fetch skew
            options = await self.fetch_options_chain(asset)
            if options:
                iv_data["iv_skew"] = self.calculate_iv_skew(options)
            
            # Cache it
            self._save_cache(asset, iv_data)
            print(f"✅ {asset} IV: {iv_data['iv_25d']:.1f}% (p{iv_data['iv_percentile']:.0f})")
            
            return iv_data
        
        return None
    
    async def get_multi_asset_iv(self, assets: List[str] = ["BTC", "ETH"]) -> Dict[str, Dict]:
        """
        Get IV data for multiple assets.
        
        Args:
            assets: List of asset symbols
            
        Returns:
            Dict of asset → IV data
        """
        results = {}
        for asset in assets:
            data = await self.get_iv_data(asset)
            if data:
                results[asset] = data
        
        return results


async def test_fetcher():
    """Test the Deribit IV fetcher"""
    print("🧪 Testing Deribit IV Fetcher...\n")
    
    fetcher = DeribitIVFetcher()
    
    # Test single asset
    print("📊 Fetching BTC IV...")
    btc_iv = await fetcher.get_iv_data("BTC")
    if btc_iv:
        print(f"   IV 25d: {btc_iv['iv_25d']:.1f}%")
        print(f"   IV 50d: {btc_iv['iv_50d']:.1f}%")
        print(f"   IV 90d: {btc_iv['iv_90d']:.1f}%")
        print(f"   Percentile: {btc_iv['iv_percentile']:.0f}th")
        if btc_iv.get('iv_skew'):
            print(f"   Skew (P/C): {btc_iv['iv_skew']:.2f}")
    else:
        print("   ⚠️  Fetch failed (API may be rate-limited)")
    
    print()
    
    # Test multi-asset
    print("📊 Fetching multi-asset IV...")
    multi_iv = await fetcher.get_multi_asset_iv(["BTC", "ETH"])
    for asset, data in multi_iv.items():
        print(f"   {asset}: {data['iv_25d']:.1f}% (p{data['iv_percentile']:.0f})")
    
    print("\n✅ Test complete!")
    return fetcher


if __name__ == "__main__":
    asyncio.run(test_fetcher())
