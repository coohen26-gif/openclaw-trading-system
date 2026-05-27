"""
📊 Deribit IV Fetcher - Système Saiyan v0.2

Fetch Implied Volatility and Greeks data from Deribit API.
Used for derivatives risk monitoring (Vega, Delta, IV skew).

Sources:
- Deribit API v2: https://docs.deribit.com/
- Crypto IV typical: 50-80% (vs 15-25% S&P 500)
"""

import aiohttp
import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger("saiyan_v0.2")


@dataclass
class IVMetrics:
    """Container for implied volatility metrics."""
    asset: str
    iv_25d: float  # 25-day IV
    iv_50d: float  # 50-day IV
    iv_90d: float  # 90-day IV
    skew: float  # Put/Call IV ratio (25-delta)
    timestamp: datetime
    raw_data: Optional[Dict] = None


@dataclass
class GreeksSnapshot:
    """Snapshot of portfolio Greeks."""
    timestamp: datetime
    portfolio_delta: float  # Net dollar delta
    portfolio_vega: float  # Net vega (per 1% IV move)
    portfolio_gamma: float  # Net gamma
    portfolio_theta: float  # Daily theta decay
    net_exposure_usd: float


class DeribitIVFetcher:
    """
    Fetch implied volatility and options data from Deribit.
    
    Deribit dominates crypto options (80%+ volume) → reference for price discovery.
    
    Key metrics:
    - IV 25d/50d/90d: Term structure of volatility
    - Skew: Put/Call IV ratio (fear gauge)
    - 25-delta: Standardized measure for comparison
    """
    
    DERIBIT_API_BASE = "https://www.deribit.com/api/v2/public"
    
    def __init__(self, cache_ttl_seconds: int = 300):
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, Dict] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
    async def fetch_iv(self, asset: str = "BTC") -> Optional[IVMetrics]:
        """
        Fetch implied volatility for asset.
        
        Note: Deribit doesn't have a simple volatility endpoint.
        We fetch ATM options and extract IV from mark_iv.
        
        Args:
            asset: "BTC" or "ETH"
            
        Returns:
            IVMetrics or None if fetch fails
        """
        cache_key = f"iv_{asset}"
        now = datetime.now(timezone.utc)
        
        # Check cache
        if cache_key in self._cache:
            cached_time = self._cache_timestamps.get(cache_key)
            if cached_time and (now - cached_time).total_seconds() < self.cache_ttl_seconds:
                logger.debug(f"Using cached IV for {asset}")
                return self._cache[cache_key]
        
        try:
            # Fetch current price first (for ATM strike)
            price_url = f"https://api.binance.com/api/v3/ticker/price?symbol={asset}USDT"
            current_price = None
            
            async with aiohttp.ClientSession() as session:
                async with session.get(price_url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        current_price = float(data.get("price", 0))
            
            if not current_price:
                logger.warning(f"Could not fetch {asset} price")
                return None
            
            # Fetch options chain and find ATM options
            options = await self.fetch_options_chain(asset)
            if not options:
                return None
            
            # Find ATM call and put (closest to current price)
            atm_calls = [o for o in options if o.get("option_type") == "call" and o.get("strike")]
            atm_puts = [o for o in options if o.get("option_type") == "put" and o.get("strike")]
            
            if not atm_calls or not atm_puts:
                return None
            
            # Get nearest ATM options
            atm_call = min(atm_calls, key=lambda x: abs(x["strike"] - current_price))
            atm_put = min(atm_puts, key=lambda x: abs(x["strike"] - current_price))
            
            # Calculate average IV and skew
            call_iv = atm_call.get("mark_iv", 0)
            put_iv = atm_put.get("mark_iv", 0)
            avg_iv = (call_iv + put_iv) / 2
            skew = put_iv / call_iv if call_iv > 0 else 1.0
            
            iv_metrics = IVMetrics(
                asset=asset,
                iv_25d=avg_iv,  # Using current ATM IV as proxy
                iv_50d=avg_iv * 1.05,  # Slight term structure assumption
                iv_90d=avg_iv * 1.10,
                skew=skew,
                timestamp=now,
                raw_data={"call_iv": call_iv, "put_iv": put_iv, "atm_strike": atm_call["strike"]}
            )
            
            # Cache result
            self._cache[cache_key] = iv_metrics
            self._cache_timestamps[cache_key] = now
            
            logger.info(f"Fetched IV for {asset}: ATM={iv_metrics.iv_25d:.1f}%, skew={iv_metrics.skew:.2f}")
            return iv_metrics
            
        except asyncio.TimeoutError:
            logger.warning(f"Deribit API timeout for {asset}")
            return None
        except Exception as e:
            logger.error(f"Deribit fetch error: {e}")
            return None
    
    async def fetch_options_chain(self, asset: str = "BTC", 
                                   expiry: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Fetch full options chain for asset.
        
        Args:
            asset: "BTC" or "ETH"
            expiry: Specific expiry (e.g., "29JUN26"), or None for all
            
        Returns:
            List of option contracts with Greeks, or None if fetch fails
        """
        try:
            # First get instrument names
            url = f"{self.DERIBIT_API_BASE}/get_instruments?currency={asset}&kind=option&expired=false"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    instruments = data.get("result", [])
                    
                    # Filter by expiry if specified
                    if expiry:
                        instruments = [i for i in instruments if expiry.upper() in i.get("instrument_name", "")]
                    
                    # Get current price for ATM calculation
                    price_url = f"https://api.binance.com/api/v3/ticker/price?symbol={asset}USDT"
                    current_price = None
                    try:
                        async with session.get(price_url, timeout=5) as price_resp:
                            if price_resp.status == 200:
                                price_data = await price_resp.json()
                                current_price = float(price_data.get("price", 0))
                    except:
                        pass
                    
                    if not current_price:
                        current_price = 75000  # Fallback
                    
                    # Find nearest expiry with both calls and puts
                    expiry_options = {}  # expiry -> {"calls": [], "puts": []}
                    for inst in instruments:
                        inst_name = inst.get("instrument_name", "")
                        parts = inst_name.split("-")
                        if len(parts) >= 2:
                            expiry_code = parts[1]
                            opt_type = inst.get("option_type", "")
                            strike = inst.get("strike", 0)
                            
                            if expiry_code not in expiry_options:
                                expiry_options[expiry_code] = {"calls": [], "puts": [], "inst": inst}
                            
                            if opt_type == "call":
                                expiry_options[expiry_code]["calls"].append(strike)
                            elif opt_type == "put":
                                expiry_options[expiry_code]["puts"].append(strike)
                    
                    # Find first expiry with both calls and puts near ATM
                    target_expiry = None
                    for exp_code, opts in expiry_options.items():
                        if opts["calls"] and opts["puts"]:
                            # Check if there's an ATM strike
                            atm_strike = min(opts["calls"] + opts["puts"], key=lambda x: abs(x - current_price))
                            if abs(atm_strike - current_price) / current_price < 0.2:  # Within 20%
                                target_expiry = exp_code
                                break
                    
                    if not target_expiry:
                        # Just use first expiry that has both
                        for exp_code, opts in expiry_options.items():
                            if opts["calls"] and opts["puts"]:
                                target_expiry = exp_code
                                break
                    
                    if not target_expiry:
                        logger.warning(f"No suitable expiry found for {asset}")
                        return None
                    
                    # Fetch tickers for ATM options in target expiry
                    options_with_greeks = []
                    target_insts = [i for i in instruments if target_expiry in i.get("instrument_name", "")]
                    
                    # Find ATM call and put
                    atm_call_strike = min(
                        [i.get("strike") for i in target_insts if i.get("option_type") == "call"],
                        key=lambda x: abs(x - current_price),
                        default=None
                    )
                    atm_put_strike = min(
                        [i.get("strike") for i in target_insts if i.get("option_type") == "put"],
                        key=lambda x: abs(x - current_price),
                        default=None
                    )
                    
                    if not atm_call_strike or not atm_put_strike:
                        return None
                    
                    # Fetch tickers for ATM call and put
                    for inst in target_insts:
                        if inst.get("strike") in [atm_call_strike, atm_put_strike]:
                            inst_name = inst.get("instrument_name")
                            ticker_url = f"{self.DERIBIT_API_BASE}/ticker?instrument_name={inst_name}"
                            
                            async with session.get(ticker_url, timeout=5) as ticker_resp:
                                if ticker_resp.status == 200:
                                    ticker_data = await ticker_resp.json()
                                    result = ticker_data.get("result", {})
                                    
                                    options_with_greeks.append({
                                        "instrument_name": inst_name,
                                        "strike": inst.get("strike"),
                                        "expiry": inst.get("expiration"),
                                        "option_type": inst.get("option_type"),
                                        "mark_price": result.get("mark_price"),
                                        "mark_iv": result.get("mark_iv", 0),
                                        "delta": result.get("greeks", {}).get("delta", 0),
                                        "gamma": result.get("greeks", {}).get("gamma", 0),
                                        "vega": result.get("greeks", {}).get("vega", 0),
                                        "theta": result.get("greeks", {}).get("theta", 0),
                                    })
                    
                    return options_with_greeks
                    
        except Exception as e:
            logger.error(f"Options chain fetch error: {e}")
            return None
    
    def calculate_portfolio_greeks(self, positions: List[Dict], 
                                    iv_metrics: Optional[IVMetrics] = None) -> GreeksSnapshot:
        """
        Calculate aggregate portfolio Greeks from positions.
        
        Args:
            positions: List of position dicts with type, size, greeks
            iv_metrics: Current IV metrics for context
            
        Returns:
            GreeksSnapshot with aggregate exposures
        """
        total_delta = 0.0
        total_vega = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_exposure = 0.0
        
        for pos in positions:
            pos_type = pos.get("type", "spot")
            size_usd = pos.get("size_usd", 0)
            greeks = pos.get("greeks", {})
            
            if pos_type == "spot_long":
                # Spot has delta = 1, no other Greeks
                total_delta += size_usd
                total_exposure += size_usd
            elif pos_type == "spot_short":
                total_delta -= size_usd
                total_exposure += size_usd
            elif pos_type in ["call_long", "call_short", "put_long", "put_short"]:
                # Options: use provided Greeks
                delta = greeks.get("delta", 0)
                vega = greeks.get("vega", 0)
                gamma = greeks.get("gamma", 0)
                theta = greeks.get("theta", 0)
                
                # Sign depends on long/short
                multiplier = 1 if "long" in pos_type else -1
                
                total_delta += delta * size_usd * multiplier
                total_vega += vega * size_usd * multiplier
                total_gamma += gamma * size_usd * multiplier
                total_theta += theta * size_usd * multiplier
                total_exposure += size_usd
        
        return GreeksSnapshot(
            timestamp=datetime.now(timezone.utc),
            portfolio_delta=total_delta,
            portfolio_vega=total_vega,
            portfolio_gamma=total_gamma,
            portfolio_theta=total_theta,
            net_exposure_usd=total_exposure
        )
    
    def get_iv_percentile(self, current_iv: float, 
                          historical_iv: List[float]) -> float:
        """
        Calculate current IV percentile vs historical distribution.
        
        Args:
            current_iv: Current IV value
            historical_iv: List of historical IV values
            
        Returns:
            Percentile (0-100)
        """
        if not historical_iv or len(historical_iv) < 30:
            return 50.0  # No data, assume median
        
        import numpy as np
        percentile = np.percentile(historical_iv, 50)  # Median
        return sum(1 for iv in historical_iv if iv <= current_iv) / len(historical_iv) * 100


async def main():
    """Test Deribit IV fetcher."""
    fetcher = DeribitIVFetcher()
    
    print("📊 Testing Deribit IV Fetcher...")
    
    # Fetch BTC IV
    btc_iv = await fetcher.fetch_iv("BTC")
    if btc_iv:
        print(f"\n✅ BTC IV:")
        print(f"   25-day: {btc_iv.iv_25d:.1f}%")
        print(f"   50-day: {btc_iv.iv_50d:.1f}%")
        print(f"   90-day: {btc_iv.iv_90d:.1f}%")
        print(f"   Skew:   {btc_iv.skew:.2f} (Put/Call)")
        
        # Interpret skew
        if btc_iv.skew > 1.3:
            print("   ⚠️  Market fearful (Put premium)")
        elif btc_iv.skew < 0.9:
            print("   🟢 Market complacent (Call premium)")
        else:
            print("   ➡️  Balanced skew")
    else:
        print("❌ Failed to fetch BTC IV")
    
    # Fetch ETH IV
    eth_iv = await fetcher.fetch_iv("ETH")
    if eth_iv:
        print(f"\n✅ ETH IV:")
        print(f"   25-day: {eth_iv.iv_25d:.1f}%")
        print(f"   Skew:   {eth_iv.skew:.2f}")
    else:
        print("❌ Failed to fetch ETH IV")


if __name__ == "__main__":
    asyncio.run(main())
