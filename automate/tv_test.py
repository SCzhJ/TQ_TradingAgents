from tradingview_screener import Query, Column, col
import pandas as pd
from datetime import datetime, timedelta
import time
import random



def scan_macd_breakout():
    print("=== Scanning for MACD Breakouts ===")
    try:
        # Create query for MA breakout patterns
        query = (Query()
                .select('name', 'close', 'volume', 'relative_volume_10d_calc', 
                       'SMA20', 'SMA50', 'RSI', 'MACD.macd', 'MACD.signal', 'BB.upper')
                .where(
                    # Price crossed above 20-day SMA with volume spike
                    col('exchange').isin(['NYSE', 'NASDAQ']),
                    col('market_cap_basic') > 1000_000_000,
                    col('volume') > 500_000,  # Minimum volume filter
                    col('close').crosses_above('SMA20'),
                    col('close') > col('SMA50'),  # Price above 50-day MA (uptrend)
                    col('RSI').between(50, 70),  # RSI showing bullish momentum
                    col('relative_volume_10d_calc') > 1.2,  # 50% above average volume
                    col('MACD.macd') > col('MACD.signal'),  # MACD bullish crossover
                    col('close') > 10.0,  # Minimum price filter
                    col('ADRP') < 10,
                )
                .order_by('relative_volume_10d_calc', ascending=False)
                .limit(50))
        total_count, df = query.get_scanner_data()
        if not df.empty:
            print(f"Found {len(df)} stocks with MA breakout patterns:")
            print(df)
            return df
        else:
            print("No MA breakout patterns found")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error in MA breakout scan: {e}")
        return pd.DataFrame()

def scan_bollinger_band_breakout():
    print("=== Scanning for Bollinger Band Breakouts ===")
    try:
        query = (Query()
                .select('name', 'close', 'volume', 'relative_volume_10d_calc',
                       'BB.upper', 'RSI', 'ADX', 'price_52_week_high',)
                .where(
                    # Price broke above upper Bollinger Band
                    col('exchange').isin(['NYSE', 'NASDAQ']),
                    col('market_cap_basic') > 1000_000_000,
                    col('volume') > 500_000,  # Minimum volume filter
                    col('close').crosses_above('BB.upper'),
                    col('relative_volume_10d_calc') > 1.2,  # Volume confirmation
                    col('ADX') > 25,  # Strong trend
                    col('RSI').between(50, 75),  # RSI showing bullish momentum
                    col('close').above_pct('price_52_week_high', 0.95), # Near 52-week highs
                    col('ADRP') < 10,
                )
                .order_by('Perf.3M', ascending=False)
                .limit(30))
        
        total_count, df = query.get_scanner_data()
        
        if not df.empty:
            print(f"Found {len(df)} stocks with BB breakout patterns:")
            print(df)
            return df
        else:
            print("No BB breakout patterns found")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error in BB breakout scan: {e}")
        return pd.DataFrame()

def scan_custom1():
    print("=== Scanning for Bollinger Band Breakouts ===")
    try:
        query = (Query()
                .select('name', 'close', 'volume', 'relative_volume_10d_calc',
                       'BB.upper', 'RSI', 'ADX', 'price_52_week_high',)
                .where(
                    # Price broke above upper Bollinger Band
                    col('exchange').isin(['NYSE', 'NASDAQ']),
                    col('market_cap_basic') > 1000_000_000,
                    col('volume') > 500_000,  # Minimum volume filter
                    col('close').crosses_above('BB.upper'),
                    col('relative_volume_10d_calc') > 1.2,  # Volume confirmation
                    col('ADX') > 25,  # Strong trend
                    col('RSI').between(50, 75),  # RSI showing bullish momentum
                    col('close').above_pct('DonchCh20.Upper', 0.97),
                    col('ADRP') < 10,
                )
                .order_by('Perf.3M', ascending=False)
                .limit(30))
        
        total_count, df = query.get_scanner_data()
        
        if not df.empty:
            print(f"Found {len(df)} stocks with BB breakout patterns:")
            print(df)
            return df
        else:
            print("No BB breakout patterns found")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error in BB breakout scan: {e}")
        return pd.DataFrame()
def main():
    df = scan_custom1()
    return

if __name__=="__main__":
    main()