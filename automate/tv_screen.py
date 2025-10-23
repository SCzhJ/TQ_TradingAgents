from tradingview_screener import Query, Column, col
import pandas as pd
from datetime import datetime, timedelta
import time

def get_top_performers(perf_col: str, n: int = 300) -> list[str]:
    """
    Return a list with the top-<n> tickers sorted by <perf_col> desc.
    """
    q = (Query()
         .select('name', perf_col)
         .where(
             col('exchange').isin(['NYSE', 'NASDAQ']),
             col('market_cap_basic') > 1_000_000_000,
             col('volume') > 500_000,
             col('ADRP') < 10,
             col(perf_col) > 20,
         )
         .order_by(perf_col, ascending=False)
         .limit(n))

    _, df = q.get_scanner_data()
    print(f"found {len(df)} Top-{n} performers by {perf_col}")
    return df['name'].tolist()

def get_3_timefraames_top_performers(n: int=300) -> list[str]:
    """
    Return a list with the top-100 tickers sorted by Perf.1M, Perf.3M, Perf.6M desc.
    """
    universe = list(set(
        get_top_performers('Perf.1M', n) +
        get_top_performers('Perf.3M', n) +
        get_top_performers('Perf.6M', n)
    ))
    print(f"Universe built: {len(universe)} tickers (top-100 1M/3M/6M)")
    return universe

def scan_resistance_breakout(universe: list[str],relative_volume_threshold: float=1.3, change_threshold: float=1.5):
    """
    Scan for stocks breaking above recent resistance levels
    Uses Donchian Channels as proxy for resistance levels
    """
    print("=== Scanning for Resistance Breakouts ===")
    try:
        query = (Query()
                .select('name', 'change', 'close', 'Perf.6M', 'Perf.3M', 'Perf.1M', 'volume', 'relative_volume_10d_calc', 'RSI', 'gap_up')
                .where(
                    # Price broke above 20-period Donchian Channel (resistance)
                    col('name').isin(universe),
                    col('exchange').isin(['NYSE', 'NASDAQ']), col('market_cap_basic') > 1000_000_000, col('volume') > 500_000, 
                    col('ADRP') < 10, col('RSI').between(50, 80), col('Perf.6M') > 10, 
                    col('high').above_pct('DonchCh20.Upper',0.97),
                    col('relative_volume_10d_calc') > 1.2,  # Volume spike
                    col('Stoch.K') > col('Stoch.D'),  # Stochastic bullish
                    col('ADX') > 24,  # Trend strength
                    col('relative_volume_10d_calc') > relative_volume_threshold,
                    col('change') > change_threshold,
                )
                .order_by('Perf.3M', ascending=False)
                .limit(50))
        total_count, df = query.get_scanner_data()
        if not df.empty:
            print(f"Found {len(df)} stocks with resistance breakout patterns:")
            print(df)
            return df
        else:
            print("No resistance breakout patterns found")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error in resistance breakout scan: {e}")
        return pd.DataFrame()

def scan_momentum_breakout(universe: list[str], relative_volume_threshold: float=1.3, change_threshold: float=1.5):
    """
    Scan for momentum-based breakouts using multiple indicators
    Good for catching early stage breakouts
    """
    print("=== Scanning for Momentum Breakouts ===")
    try:
        query = (Query()
                .select('name', 'change', 'close', 'Perf.6M', 'Perf.3M', 'Perf.1M', 'volume', 'relative_volume_10d_calc', 'RSI', 'gap_up')
                .where(
                    col('name').isin(universe),
                    # Multiple momentum conditions
                    col('exchange').isin(['NYSE', 'NASDAQ']), col('market_cap_basic') > 1000_000_000, col('volume') > 500_000, 
                    col('ADRP') < 10, col('RSI').between(50, 80), col('Perf.6M') > 10,
                    col('Mom') > 0,  # Positive momentum
                    col('ROC') > 5,  # Rate of change positive
                    col('MACD.hist') > 0,  # MACD histogram positive
                    col('MACD.macd') > col('MACD.signal'),  # MACD bullish
                    col('close') > col('SMA5'),  # Price above short-term MA
                    col('SMA5') > col('SMA10'),  # Short MA above medium MA
                    col('ADX') > 24,  # Strong trend
                    col('relative_volume_10d_calc') > relative_volume_threshold,
                    col('change') > change_threshold,
                )
                .order_by('Perf.3M', ascending=False)
                .limit(50))
        total_count, df = query.get_scanner_data()
        if not df.empty:
            print(f"Found {len(df)} stocks with momentum breakout patterns:")
            print(df)
            return df
        else:
            print("No momentum breakout patterns found")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error in momentum breakout scan: {e}")
        return pd.DataFrame()

def scan_breakout_comprehensive(universe: list[str], relative_volume_threshold: float=1.3, change_threshold: float=1.5):
    print("=== Scanning for Comprehensive Breakouts ===")
    
    try:
        query = (Query()
                .select('name', 'change', 'close', 'Perf.6M', 'Perf.3M', 'Perf.1M', 'volume', 'relative_volume_10d_calc', 'RSI', 'gap_up')
                .where(
                    col('name').isin(universe),
                    col('exchange').isin(['NYSE', 'NASDAQ']), col('market_cap_basic') > 1000_000_000, col('volume') > 500_000, 
                    col('ADRP') < 10, col('RSI').between(50, 80), col('Perf.6M') > 10, 
                    col('ADX') > 25,  # Strong trend
                    col('RSI30') > 45,  # Bullish momentum
                    col('RSI30') < 75,  # Not extremely overbought
                    col('high').above_pct('DonchCh20.Upper',0.98),
                    col('Stoch.K') > col('Stoch.D'),  # Stochastic bullish
                    col('SMA10') > col('SMA30'),  # Short MA above medium MA
                    col('Perf.5Y') > 20,
                    col('relative_volume_10d_calc') > relative_volume_threshold,
                    col('change') > change_threshold,
                )
                .order_by('Perf.6M', ascending=False)
                .limit(50))
        total_count, df = query.get_scanner_data()
        if not df.empty:
            print(f"Found {len(df)} stocks with comprehensive breakout patterns:")
            print(df)
            return df
        else:
            print("No comprehensive breakout patterns found")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error in comprehensive breakout scan: {e}")
        return pd.DataFrame()

def scan_gap_breakout(relative_volume_threshold: float=1.3, change_threshold: float=1.5):
    """
    Scan for gap-up breakouts that often signal strong momentum
    """
    print("=== Scanning for Gap Breakouts ===")
    
    try:
        query = (Query()
                .select('name', 'change', 'close', 'Perf.6M', 'Perf.3M', 'Perf.1M', 'volume', 'relative_volume_10d_calc', 'RSI', 'gap_up')
                .where(
                    # Significant gap up (more than 10%)
                    col('exchange').isin(['NYSE', 'NASDAQ']), col('market_cap_basic') > 1000_000_000, col('volume') > 500_000, 
                    col('RSI').between(50, 100), col('Perf.6M') > 10, 
                    col('gap_up') > 8.0,
                    col('close') > col('open'),  # Closed higher than opened
                    col('ADX') > 20,  # Trend strength
                    col('close') > col('SMA20'),  # Above 20-day MA
                    col('SMA20') > col('SMA50'),  # 20 MA above 50 MA
                    col('relative_volume_10d_calc') > relative_volume_threshold,
                    col('change') > change_threshold,
                )
                .order_by('gap_up', ascending=False)
                .limit(20))
        
        total_count, df = query.get_scanner_data()
        
        if not df.empty:
            print(f"Found {len(df)} stocks with gap breakout patterns:")
            print(df[['name', 'close', 'gap_up', 'relative_volume_10d_calc']].head(10))
            return df
        else:
            print("No gap breakout patterns found")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error in gap breakout scan: {e}")
        return pd.DataFrame()

def scan_all(universe_num_each: int=500, relative_volume_threshold: float=1.3, change_threshold: float=0.5):

    print("=== Scanning for all breakout patterns... ===")
    MAX_ITER = 5
    iter_count = 0
    TARGET_LENGTH = 20
    current_length = 100
    universe = get_3_timefraames_top_performers(n=universe_num_each)
    while current_length > TARGET_LENGTH and iter_count < MAX_ITER:
        relative_volume_threshold += 0.025
        change_threshold += 0.05
        df1 = scan_gap_breakout(relative_volume_threshold, change_threshold)
        df2 = scan_resistance_breakout(universe, relative_volume_threshold, change_threshold)
        df3 = scan_breakout_comprehensive(universe, relative_volume_threshold, change_threshold)
        df4 = scan_momentum_breakout(universe, relative_volume_threshold, change_threshold)
        df = pd.concat([df1, df2, df3, df4], axis=0)
        df = df.drop_duplicates(subset=['name'])
        current_length = len(df)
        iter_count += 1
    # reset index
    df = df.reset_index(drop=True)
    
    print(f"Found {len(df)} stocks with any breakout patterns:")
    print(df)
    return df
    


if __name__=="__main__":
    # scan_gap_breakout()
    # scan_momentum_breakout()
    # scan_resistance_breakout()
    scan_all(universe_num_each=1000)