from tradingview_screener import Query, Column, col
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup retry session function is defined later in the file

def get_top_performers(perf_col: str, n: int = 300, max_retries: int = 3) -> list[str]:
    """
    Return a list with the top-<n> tickers sorted by <perf_col> desc.
    Includes retry logic to handle connection issues.
    """
    for attempt in range(max_retries):
        try:
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
        except Exception as e:
            print(f"Error in get_top_performers (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Returning empty list.")
                return []

def setup_retry_session(retries=3, backoff_factor=0.3):
    """
    Setup a session with retry capabilities
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

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
        # Get top performers on 1M timeframe with retry
        symbols_1m = fetch_with_retry(
            lambda: (Query()
                .select('name', 'close', 'Perf.1M')
                .where(
                    col('exchange').isin(['NYSE', 'NASDAQ']), 
                    col('market_cap_basic') > 1000_000_000, 
                    col('volume') > 500_000, 
                    col('Perf.1M') > 0
                )
                .order_by('Perf.1M', ascending=False)
                .limit(n)),
            "1M"
        )
        
        # Add delay between timeframe queries
        time.sleep(random.uniform(2, 4))
        
        # Get top performers on 3M timeframe with retry
        symbols_3m = fetch_with_retry(
            lambda: (Query()
                .select('name', 'close', 'Perf.3M')
                .where(
                    col('exchange').isin(['NYSE', 'NASDAQ']), 
                    col('market_cap_basic') > 1000_000_000, 
                    col('volume') > 500_000, 
                    col('Perf.3M') > 0
                )
                .order_by('Perf.3M', ascending=False)
                .limit(n)),
            "3M"
        )
        
        # Add delay between timeframe queries
        time.sleep(random.uniform(2, 4))
        
        # Get top performers on 6M timeframe with retry
        symbols_6m = fetch_with_retry(
            lambda: (Query()
                .select('name', 'close', 'Perf.6M')
                .where(
                    col('exchange').isin(['NYSE', 'NASDAQ']), 
                    col('market_cap_basic') > 1000_000_000, 
                    col('volume') > 500_000, 
                    col('Perf.6M') > 0
                )
                .order_by('Perf.6M', ascending=False)
                .limit(n)),
            "6M"
        )
        
        # Combine all symbols
        combined_symbols = list(symbols_1m | symbols_3m | symbols_6m)
        
        # Print final summary
        print(f"Universe built: {len(combined_symbols)} tickers (from 1M/3M/6M timeframes)")
        
        # If we have no symbols, return a fallback universe
        if len(combined_symbols) == 0:
            print("Warning: No symbols found across any timeframe. Using fallback approach.")
            # Try a simpler query with higher chance of success
            try:
                query_fallback = (Query()
                    .select('name', 'close')
                    .where(
                        col('exchange').isin(['NYSE', 'NASDAQ']),
                        col('market_cap_basic') > 10_000_000_000,
                        col('volume') > 1_000_000
                    )
                    .limit(100))
                time.sleep(1)
                _, df_fallback = query_fallback.get_scanner_data()
                if not df_fallback.empty:
                    fallback_symbols = list(df_fallback['name'].tolist())
                    print(f"Using fallback universe with {len(fallback_symbols)} large-cap stocks")
                    return fallback_symbols
            except Exception as e:
                print(f"Fallback query also failed: {e}")
                
        return combined_symbols
        
    except Exception as e:
        print(f"Critical error in get_3_timeframes_top_performers: {e}")
        # Return empty list as fallback
        return []

def scan_resistance_breakout(universe: list[str], relative_volume_threshold: float=1.3, change_threshold: float=1.5, max_retries: int = 3):
    """
    Scan for stocks breaking above recent resistance levels
    Uses Donchian Channels as proxy for resistance levels
    Includes retry logic to handle connection issues
    """
    print("=== Scanning for Resistance Breakouts ===")
    for attempt in range(max_retries):
        try:
            query = (Query()
                    .select('name', 'change', 'close', 'Perf.6M', 'Perf.3M', 'Perf.1M', 'volume', 'relative_volume_10d_calc', 'RSI', 'gap_up')
                    .where(
                        # Price broke above 20-period Donchian Channel (resistance)
                        col('name').isin(universe),
                        col('exchange').isin(['NYSE', 'NASDAQ']), 
                        col('market_cap_basic') > 1000_000_000, 
                        col('volume') > 500_000, 
                        col('ADRP') < 10, 
                        col('RSI').between(50, 80), 
                        col('Perf.6M') > 10, 
                        col('close').above_pct('DonchCh20.Upper', 0.97),
                        col('relative_volume_10d_calc') > 1.2,  # Volume spike
                        col('Stoch.K') > col('Stoch.D'),  # Stochastic bullish
                        col('ADX') > 24,  # Trend strength
                        col('relative_volume_10d_calc') > relative_volume_threshold,
                        col('change') > change_threshold,
                    )
                    .order_by('Perf.3M', ascending=False)
                    .limit(50))
            
            # Add a small delay before the request
            time.sleep(random.uniform(0.5, 2.0))
            
            total_count, df = query.get_scanner_data()
            if not df.empty:
                print(f"Found {len(df)} stocks with resistance breakout patterns:")
                print(df)
                return df
            else:
                print("No resistance breakout patterns found")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error in resistance breakout scan (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Returning empty DataFrame.")
                return pd.DataFrame()

def scan_momentum_breakout(universe: list[str], relative_volume_threshold: float=1.3, change_threshold: float=1.5, max_retries: int = 3):
    """
    Scan for momentum-based breakouts using multiple indicators
    Good for catching early stage breakouts
    Includes retry logic to handle connection issues
    """
    print("=== Scanning for Momentum Breakouts ===")
    for attempt in range(max_retries):
        try:
            query = (Query()
                    .select('name', 'change', 'close', 'Perf.6M', 'Perf.3M', 'Perf.1M', 'volume', 'relative_volume_10d_calc', 'RSI', 'gap_up')
                    .where(
                        col('name').isin(universe),
                        # Multiple momentum conditions
                        col('exchange').isin(['NYSE', 'NASDAQ']), 
                        col('market_cap_basic') > 1000_000_000, 
                        col('volume') > 500_000, 
                        col('ADRP') < 10, 
                        col('RSI').between(50, 80), 
                        col('Perf.6M') > 10,
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
            
            # Add a small delay before the request
            time.sleep(random.uniform(0.5, 2.0))
            
            total_count, df = query.get_scanner_data()
            if not df.empty:
                print(f"Found {len(df)} stocks with momentum breakout patterns:")
                print(df)
                return df
            else:
                print("No momentum breakout patterns found")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error in momentum breakout scan (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Returning empty DataFrame.")
                return pd.DataFrame()

def scan_breakout_comprehensive(universe: list[str], relative_volume_threshold: float=1.3, change_threshold: float=1.5, max_retries: int = 3):
    print("=== Scanning for Comprehensive Breakouts ===")
    
    for attempt in range(max_retries):
        try:
            query = (Query()
                    .select('name', 'change', 'close', 'Perf.6M', 'Perf.3M', 'Perf.1M', 'volume', 'relative_volume_10d_calc', 'RSI', 'gap_up')
                    .where(
                        col('name').isin(universe),
                        col('exchange').isin(['NYSE', 'NASDAQ']), 
                        col('market_cap_basic') > 1000_000_000, 
                        col('volume') > 500_000, 
                        col('ADRP') < 10, 
                        col('RSI').between(50, 80), 
                        col('Perf.6M') > 10, 
                        col('ADX') > 25,  # Strong trend
                        col('RSI30') > 45,  # Bullish momentum
                        col('RSI30') < 75,  # Not extremely overbought
                        col('close').above_pct('DonchCh20.Upper', 0.97),
                        col('Stoch.K') > col('Stoch.D'),  # Stochastic bullish
                        col('SMA10') > col('SMA30'),  # Short MA above medium MA
                        col('Perf.5Y') > 20,
                        col('relative_volume_10d_calc') > relative_volume_threshold,
                        col('change') > change_threshold,
                    )
                    .order_by('Perf.6M', ascending=False)
                    .limit(50))
            
            # Add a small delay before the request
            time.sleep(random.uniform(0.5, 2.0))
            
            total_count, df = query.get_scanner_data()
            if not df.empty:
                print(f"Found {len(df)} stocks with comprehensive breakout patterns:")
                print(df)
                return df
            else:
                print("No comprehensive breakout patterns found")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error in comprehensive breakout scan (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Returning empty DataFrame.")
                return pd.DataFrame()

def scan_gap_breakout(relative_volume_threshold: float=1.3, change_threshold: float=1.5, max_retries: int = 3):
    """
    Scan for gap-up breakouts that often signal strong momentum
    Includes retry logic to handle connection issues
    """
    print("=== Scanning for Gap Breakouts ===")
    
    for attempt in range(max_retries):
        try:
            query = (Query()
                    .select('name', 'change', 'close', 'Perf.6M', 'Perf.3M', 'Perf.1M', 'volume', 'relative_volume_10d_calc', 'RSI', 'gap_up')
                    .where(
                        # Significant gap up (more than 10%)
                        col('exchange').isin(['NYSE', 'NASDAQ']), 
                        col('market_cap_basic') > 1000_000_000, 
                        col('volume') > 500_000, 
                        col('RSI').between(50, 100), 
                        col('Perf.6M') > 10, 
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
            
            # Add a small delay before the request
            time.sleep(random.uniform(0.5, 2.0))
        
            total_count, df = query.get_scanner_data()
            
            if not df.empty:
                print(f"Found {len(df)} stocks with gap breakout patterns:")
                print(df[['name', 'close', 'gap_up', 'relative_volume_10d_calc']].head(10))
                return df
            else:
                print("No gap breakout patterns found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error in gap breakout scan (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Returning empty DataFrame.")
                return pd.DataFrame()

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
            df1 = scan_gap_breakout(relative_volume_threshold, change_threshold, max_retries=max_retries)
            print(f"  Gap breakout scan found {len(df1)} stocks")
            time.sleep(random.uniform(1, 3))
            
            df2 = scan_resistance_breakout(universe, relative_volume_threshold, change_threshold, max_retries=max_retries)
            print(f"  Resistance breakout scan found {len(df2)} stocks")
            time.sleep(random.uniform(1, 3))
            
            df3 = scan_breakout_comprehensive(universe, relative_volume_threshold, change_threshold, max_retries=max_retries)
            print(f"  Comprehensive breakout scan found {len(df3)} stocks")
            time.sleep(random.uniform(1, 3))
            
            df4 = scan_momentum_breakout(universe, relative_volume_threshold, change_threshold, max_retries=max_retries)
            print(f"  Momentum breakout scan found {len(df4)} stocks")
            
            # Combine results and remove duplicates
            df_list = [d for d in [df1, df2, df3, df4] if not d.empty]
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
    scan_all(universe_num_each=1000)