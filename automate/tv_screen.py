from tradingview_screener import Query, Column, col
import pandas as pd
from datetime import datetime, timedelta
import time
import random

def get_3_timeframes_top_performers(n: int=500, max_retries: int = 3) -> list[str]:
    """
    Get top performing stocks across multiple timeframes with retry logic
    to create a quality universe for breakout scanning
    """
    print("=== Getting Top Performers Across Multiple Timeframes ===")
    
    # Initialize empty sets to store symbols
    symbols_1m = set()
    symbols_3m = set()
    symbols_6m = set()
    
    # Function to fetch data with retries
    def fetch_with_retry(query_func, timeframe_name, attempt=0):
        try:
            # Add a delay before each request to prevent rate limiting
            time.sleep(random.uniform(0.5, 2.0))
            
            query = query_func()
            total_count, df = query.get_scanner_data()
            
            if not df.empty:
                symbols = set(df['name'].tolist())
                print(f"Found {len(symbols)} top performers on {timeframe_name} timeframe")
                return symbols
            return set()
        except Exception as e:
            print(f"Error fetching {timeframe_name} performers (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                return fetch_with_retry(query_func, timeframe_name, attempt + 1)
            return set()
    try:
        combined_symbols = []
        perf_col = [('Perf.1M', 20), ('Perf.3M', 25), ('Perf.6M', 30)]
        for perf, thrs in perf_col:
            symbols = fetch_with_retry(
                lambda: (Query()
                    .select('name', 'close', perf)
                    .where(
                        col('exchange').isin(['NYSE', 'NASDAQ']), 
                        col('market_cap_basic') > 1000_000_000, 
                        col('volume') > 500_000, 
                        col(perf) > thrs
                    )
                    .order_by(perf, ascending=False)
                    .limit(n)),
                f"{perf} timeframe"
            )
            combined_symbols.extend(symbols)
        combined_symbols = list(set(combined_symbols))
        # Print final summary
        print(f"Universe built: {len(combined_symbols)} tickers (from 1M/3M/6M timeframes)")
        return combined_symbols
        
    except Exception as e:
        print(f"Critical error in get_3_timeframes_top_performers: {e}")
        # Return empty list as fallback
        return []

def condition_scan(
    condition_name: str, 
    conditions: list[Column], 
    select: list[str], 
    universe: list[str], 
    relative_volume_threshold: float, change_threshold: float, 
    max_rsi: float, order_by: str,
    max_retries: int, 
    ):

    control_conditions = [
        col('name').isin(universe), 
        col('relative_volume_10d_calc') > relative_volume_threshold, 
        col('change') > change_threshold,
        col('RSI').between(50, max_rsi)
    ]
    conditions = conditions + control_conditions
    print(f"=== Scanning for {condition_name} ===")
    for attempt in range(max_retries):
        try:
            query = (Query()
                    .select(*select)
                    .where(
                        *conditions
                    )
                    .order_by(order_by, ascending=False)
                    .limit(50))
            
            # Add a small delay before the request
            time.sleep(random.uniform(0.5, 2.0))
            total_count, df = query.get_scanner_data()
            if not df.empty:
                print(f"Found {len(df)} stocks with {condition_name} patterns:")
                print(df)
                return df
            else:
                print(f"No {condition_name} patterns found")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error in {condition_name} scan (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Returning empty DataFrame.")
                return pd.DataFrame()

REGULAR_SELECT = ['name', 'change', 'close', 'Perf.6M', 'Perf.3M', 'Perf.1M', 'volume', 'relative_volume_10d_calc', 'RSI', 'gap_up']

COMMON_CONDITION = [
    col('exchange').isin(['NYSE', 'NASDAQ']), col('market_cap_basic') > 1000_000_000, 
    col('volume') > 500_000, col('ADRP') < 10, col('Perf.6M') > 20, col('close') > 10,
]
RESISTANCE_CONDITION = [
    col('close').above_pct('DonchCh20.Upper', 0.97),
    col('relative_volume_10d_calc') > 1.2,  # Volume spike
    col('Stoch.K') > col('Stoch.D'),  # Stochastic bullish
    col('ADX') > 24,  # Trend strength
]
COMPREHENSIVE_CONDITION = [
    col('ADX') > 25,  # Strong trend
    col('RSI30') > 45,  # Bullish momentum
    col('RSI30') < 75,  # Not extremely overbought
    col('close').above_pct('DonchCh20.Upper', 0.97),
    col('Stoch.K') > col('Stoch.D'),  # Stochastic bullish
    col('SMA10') > col('SMA30'),  # Short MA above medium MA
    col('Perf.5Y') > 20,
]
MACD_CONDITION = [
    col('close').crosses_above('SMA20'),
    col('close') > col('SMA50'),  # Price above 50-day MA (uptrend)
    col('MACD.macd') > col('MACD.signal'),  # MACD bullish crossover
]
BOLLINGER_CONDITION = [
    col('close').crosses_above('BB.upper'),
    col('ADX') > 25,  # Strong trend
    col('close').above_pct('price_52_week_high', 0.95), # Near 52-week highs
]
GAP_CONDITION = [
    col('gap_up') > 8.0,
    col('close') > col('open'),  # Closed higher than opened
    col('ADX') > 20,  # Trend strength
    col('close') > col('SMA20'),  # Above 20-day MA
    col('SMA20') > col('SMA50'),  # 20 MA above 50 MA
]

def scan_all(universe_num_each: int=500, relative_volume_threshold: float=1.25, change_threshold: float=0.45, max_retries: int = 3):
    """
    Run all breakout scans with enhanced error handling and retry support
    """
    print("\n" + "="*50)
    print("RUNNING ALL BREAKOUT SCANS WITH ENHANCED ERROR HANDLING")
    print("="*50)
    
    try:
        # Get universe with retry logic
        universe = get_3_timeframes_top_performers(n=universe_num_each)
        
        # If universe is empty after retries, use a fallback approach
        if not universe:
            print("Warning: Failed to get universe. Using a simplified approach.")
            # Use a direct scan without universe filtering with retry support
            df = scan_gap_breakout(relative_volume_threshold, change_threshold, max_retries=max_retries)
            print(f"=== Found {len(df)} stocks with gap breakout patterns: ===")
            print(df)
            return df
        
        MAX_ITER = 5
        iter_count = 0
        TARGET_LENGTH = 20
        current_length = 100
        
        while current_length > TARGET_LENGTH and iter_count < MAX_ITER:
            relative_volume_threshold += 0.025
            change_threshold += 0.05
            
            print(f"Iteration {iter_count+1}/{MAX_ITER}: Using volume threshold {relative_volume_threshold:.3f}, change threshold {change_threshold:.2f}")
            
            # Add delays between different scan types to avoid rate limiting
            df1 = condition_scan(
                condition_name="Gap Breakout", conditions=COMMON_CONDITION+GAP_CONDITION, select=REGULAR_SELECT, universe=universe,
                relative_volume_threshold=relative_volume_threshold, change_threshold=change_threshold, 
                max_rsi=90, order_by='Perf.6M', max_retries=max_retries
            )
            print(f"  Gap breakout scan found {len(df1)} stocks")
            time.sleep(random.uniform(1, 3))

            df2 = condition_scan(
                condition_name="Bollinger Breakout", conditions=COMMON_CONDITION+BOLLINGER_CONDITION, select=REGULAR_SELECT, universe=universe,
                relative_volume_threshold=relative_volume_threshold, change_threshold=change_threshold, 
                max_rsi=75, order_by='Perf.3M', max_retries=max_retries
            )
            print(f"  Bollinger breakout scan found {len(df2)} stocks")
            time.sleep(random.uniform(1, 3))

            df3 = condition_scan(
                condition_name="MACD Breakout", conditions=COMMON_CONDITION+MACD_CONDITION, select=REGULAR_SELECT, universe=universe,
                relative_volume_threshold=relative_volume_threshold, change_threshold=change_threshold, 
                max_rsi=75, order_by='Perf.3M', max_retries=max_retries
            )
            print(f"  MACD breakout scan found {len(df3)} stocks")
            time.sleep(random.uniform(1, 3))

            df4 = condition_scan(
                condition_name="Resistance Breakout", conditions=COMMON_CONDITION+RESISTANCE_CONDITION, select=REGULAR_SELECT, universe=universe,
                relative_volume_threshold=relative_volume_threshold, change_threshold=change_threshold, 
                max_rsi=75, order_by='Perf.3M', max_retries=max_retries
            )
            print(f"  Resistance breakout scan found {len(df4)} stocks")
            time.sleep(random.uniform(1, 3))
            
            df5 = condition_scan(
                condition_name="Comprehensive Breakout", conditions=COMMON_CONDITION+COMPREHENSIVE_CONDITION, select=REGULAR_SELECT, universe=universe,
                relative_volume_threshold=relative_volume_threshold, change_threshold=change_threshold, 
                max_rsi=75, order_by='Perf.6M', max_retries=max_retries
            )
            print(f"  Comprehensive breakout scan found {len(df5)} stocks")
            time.sleep(random.uniform(1, 3))
            
            # Combine results and remove duplicates
            df_list = [d for d in [df1, df2, df3, df4, df5] if not d.empty]
            if df_list:
                df = pd.concat(df_list, axis=0)
                df = df.drop_duplicates(subset=['name'])
            else:
                df = pd.DataFrame()
                
            current_length = len(df)
            iter_count += 1
            
            print(f"Iteration {iter_count}/{MAX_ITER}: Found {current_length} unique stocks")
        
        # reset index
        if not df.empty:
            df = df.reset_index(drop=True)
        
        print("\n" + "="*50)
        print("BREAKOUT SCAN SUMMARY")
        print("="*50)
        print(f"=== Found {len(df)} stocks with any breakout patterns: ===")
        if not df.empty:
            print(df)
        else:
            print("No stocks found with breakout patterns after all attempts.")
        
        return df
        
    except Exception as e:
        print(f"Critical error in scan_all: {e}")
        return pd.DataFrame()
    


if __name__=="__main__":
    # scan_gap_breakout()
    # scan_momentum_breakout()
    # scan_resistance_breakout()
    scan_all(universe_num_each=180)