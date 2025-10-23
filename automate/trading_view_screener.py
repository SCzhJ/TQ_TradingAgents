from tradingview_screener import Query, Column, col
import pandas as pd

import yfinance as yf
from datetime import datetime, timedelta

import time

def query_stock(name: str):
    query = (
        Query()
        .select(
            'name', 'exchange', 'close', 'High.3M', 'change', 'Perf.3M', 'Perf.6M', 'Perf.5Y', 'average_volume_30d_calc', 'RSI10', 'RSI30', 'ADRP', 'is_primary'
        )
        .where(col('name') == name)
    )
    total, df = query.get_scanner_data()
    return df

def scan_breakout_simple(
    breakout_percent:int=0.03,
    min_close:float=10,
    min_market_cap:float=1_000_000_000,
    min_perf_6M:float=30,
    min_perf_5Y:float=50,
    min_volume_30d:float=1_000_000,
    min_rsi30:float=45,
    max_rsi30:float=75,
    min_change:float=3,
    max_adrp:float=8,
    ordered_by:str='Perf.6M',
    ):
    query = (
        Query()
        .select(
            'name', 'close', 'High.3M', 'change', 'Perf.3M', 'Perf.6M', "ADRP", 'price_52_week_high'
        )
        .where(
            # col('is_primary') == True,
            col('exchange').isin(['NYSE', 'NASDAQ']),
            col('close') > min_close,
            col('market_cap_basic') > min_market_cap,
            col('Perf.6M') > min_perf_6M,
            col('Perf.5Y') > min_perf_5Y,
            col('average_volume_30d_calc') > min_volume_30d,
            col('RSI30').between(min_rsi30, max_rsi30),
            col('change') > min_change,
            col('ADRP') < max_adrp,
        )
        .order_by(ordered_by, ascending=False)
        # .order_by('Perf.5Y', ascending=False)
        .limit(1000)
    )
    total, df = query.get_scanner_data()
    print(f"Find {total} stocks")
    print(df)
    print("-----------------")
    print("Breakouts")
    df= df[df['close'] * (1 + breakout_percent) >= df['High.3M']]
    # Order based on close/price_52_week_high ratio
    df['ratio'] = df['close'] / df['price_52_week_high']
    df = df.nlargest(25, 'ratio')
    df = df.reset_index(drop=True)
    print(df)
    return df

def scan_breakout_3timeframes(
    breakout_percent:int=0.02,
    min_close:float=20,
    min_market_cap:float=1_000_000_000,
    min_perf_6M:float=20,
    min_perf_5Y:float=50,
    min_volume_30d:float=1_000_000,
    min_rsi30:float=45,
    max_rsi30:float=75,
    min_change:float=0,
    max_adrp:float=8,
    scan_limit:int=90,
    breakout_limit:int=60,
    ):

    query = (
        Query()
        .select(
            'name', 'close', 'High.3M', 'change', 'Perf.3M', 'Perf.6M', "ADRP", 'price_52_week_high', "RSI30"
        )
        .where(
            # col('is_primary') == True,
            col('exchange').isin(['NYSE', 'NASDAQ']),
            col('close') > min_close,
            col('market_cap_basic') > min_market_cap,
            col('Perf.6M') > min_perf_6M,
            col('Perf.5Y') > min_perf_5Y,
            col('average_volume_30d_calc') > min_volume_30d,
            col('RSI30').between(min_rsi30, max_rsi30),
            col('change') > min_change,
            col('ADRP') < max_adrp,
        )
        .order_by('Perf.3M', ascending=False)
        .limit(scan_limit)
    )
    total, df_3M = query.get_scanner_data()
    print(f"Find {total} stocks, top Perf.3M")
    print(df_3M)

    query = (
        Query()
        .select(
            'name', 'close', 'High.3M', 'change', 'Perf.3M', 'Perf.6M', "ADRP", 'price_52_week_high', "RSI30"
        )
        .where(
            # col('is_primary') == True,
            col('exchange').isin(['NYSE', 'NASDAQ']),
            col('close') > min_close,
            col('market_cap_basic') > min_market_cap,
            col('Perf.6M') > min_perf_6M,
            col('Perf.5Y') > min_perf_5Y,
            col('average_volume_30d_calc') > min_volume_30d,
            col('RSI30').between(min_rsi30, max_rsi30),
            col('change') > min_change,
            col('ADRP') < max_adrp,
        )
        .order_by('Perf.1M', ascending=False)
        .limit(scan_limit)
    )
    total, df_1M = query.get_scanner_data()
    print(f"Find {total} stocks, top Perf.1M")
    print(df_1M)

    query = (
        Query()
        .select(
            'name', 'close', 'High.3M', 'change', 'Perf.3M', 'Perf.6M', "ADRP", 'price_52_week_high', "RSI30"
        )
        .where(
            # col('is_primary') == True,
            col('exchange').isin(['NYSE', 'NASDAQ']),
            col('close') > min_close,
            col('market_cap_basic') > min_market_cap,
            col('Perf.6M') > min_perf_6M,
            col('Perf.5Y') > min_perf_5Y,
            col('average_volume_30d_calc') > min_volume_30d,
            col('RSI30').between(min_rsi30, max_rsi30),
            col('change') > min_change,
            col('ADRP') < max_adrp,
        )
        .order_by('Perf.6M', ascending=False)
        .limit(scan_limit)
    )
    total, df_6M = query.get_scanner_data()
    print(f"Find {total} stocks, top Perf.6M")
    print(df_6M)

    # concatenate all 3 dataframes without repetition
    df = pd.concat([df_3M, df_1M, df_6M]).drop_duplicates(subset=['name'])
    print("-----------------")
    df= df[df['close'] * (1 + breakout_percent) >= df['High.3M']]
    # Order based on close/price_52_week_high ratio
    df['ratio'] = df['close'] / df['price_52_week_high']
    df = df.nlargest(breakout_limit, 'ratio')
    df = df.reset_index(drop=True)
    print(f"Breakouts: {len(df)}")
    print(df)
    return df

def scan_breakout_3timeframes_orderbychange(
    breakout_percent:int=0.02,
    min_close:float=20,
    min_market_cap:float=1_000_000_000,
    min_perf_6M:float=20,
    min_perf_5Y:float=50,
    min_volume_30d:float=1_000_000,
    min_rsi30:float=45,
    max_rsi30:float=75,
    min_change:float=3,
    max_adrp:float=8,
    scan_limit:int=90,
    breakout_limit:int=60,
    ):

    query = (
        Query()
        .select(
            'name', 'close', 'High.3M', 'change', 'Perf.3M', 'Perf.6M', "ADRP", 'price_52_week_high', "RSI30"
        )
        .where(
            # col('is_primary') == True,
            col('exchange').isin(['NYSE', 'NASDAQ']),
            col('close') > min_close,
            col('market_cap_basic') > min_market_cap,
            col('Perf.6M') > min_perf_6M,
            col('Perf.5Y') > min_perf_5Y,
            col('average_volume_30d_calc') > min_volume_30d,
            col('RSI30').between(min_rsi30, max_rsi30),
            col('change') > min_change,
            col('ADRP') < max_adrp,
        )
        .order_by('Perf.3M', ascending=False)
        .limit(scan_limit)
    )
    total, df_3M = query.get_scanner_data()
    print(f"Find {total} stocks, top Perf.3M")
    print(df_3M)

    query = (
        Query()
        .select(
            'name', 'close', 'High.3M', 'change', 'Perf.3M', 'Perf.6M', "ADRP", 'price_52_week_high', "RSI30"
        )
        .where(
            # col('is_primary') == True,
            col('exchange').isin(['NYSE', 'NASDAQ']),
            col('close') > min_close,
            col('market_cap_basic') > min_market_cap,
            col('Perf.6M') > min_perf_6M,
            col('Perf.5Y') > min_perf_5Y,
            col('average_volume_30d_calc') > min_volume_30d,
            col('RSI30').between(min_rsi30, max_rsi30),
            col('change') > min_change,
            col('ADRP') < max_adrp,
        )
        .order_by('Perf.1M', ascending=False)
        .limit(scan_limit)
    )
    total, df_1M = query.get_scanner_data()
    print(f"Find {total} stocks, top Perf.1M")
    print(df_1M)

    query = (
        Query()
        .select(
            'name', 'close', 'High.3M', 'change', 'Perf.3M', 'Perf.6M', "ADRP", 'price_52_week_high', "RSI30"
        )
        .where(
            # col('is_primary') == True,
            col('exchange').isin(['NYSE', 'NASDAQ']),
            col('close') > min_close,
            col('market_cap_basic') > min_market_cap,
            col('Perf.6M') > min_perf_6M,
            col('Perf.5Y') > min_perf_5Y,
            col('average_volume_30d_calc') > min_volume_30d,
            col('RSI30').between(min_rsi30, max_rsi30),
            col('change') > min_change,
            col('ADRP') < max_adrp,
        )
        .order_by('Perf.6M', ascending=False)
        .limit(scan_limit)
    )
    total, df_6M = query.get_scanner_data()
    print(f"Find {total} stocks, top Perf.6M")
    print(df_6M)

    # concatenate all 3 dataframes without repetition
    df = pd.concat([df_3M, df_1M, df_6M]).drop_duplicates(subset=['name'])
    print("-----------------")
    df = df[df['close'] * (1 + breakout_percent) >= df['High.3M']]
    df = df.nlargest(breakout_limit, 'change')
    df = df.reset_index(drop=True)
    print(f"Breakouts: {len(df)}")
    print(df)
    return df

"""
TradingView Breakout Pattern Scanner for Swing Trading
This script scans for various breakout patterns using the tradingview_screener library
"""


def scan_moving_average_breakout():
    """
    Scan for stocks breaking above/below key moving averages with volume confirmation
    This is a classic breakout pattern for swing trading
    """
    print("=== Scanning for Moving Average Breakouts ===")
    
    try:
        # Create query for MA breakout patterns
        query = (Query()
                .select('name', 'close', 'volume', 'relative_volume_10d_calc', 
                       'SMA20', 'SMA50', 'SMA200', 'EMA20', 'EMA50',
                       'RSI', 'MACD.macd', 'MACD.signal', 'BB.upper', 'BB.lower')
                .where(
                    # Price crossed above 20-day SMA with volume spike
                    col('exchange').isin(['NYSE', 'NASDAQ']),
                    col('market_cap_basic') > 1000_000_000,
                    col('volume') > 500_000,  # Minimum volume filter
                    col('close').crosses_above('SMA20'),
                    col('relative_volume_10d_calc') > 1.2,  # 50% above average volume
                    col('close') > col('SMA50'),  # Price above 50-day MA (uptrend)
                    col('RSI') > 50,  # RSI showing bullish momentum
                    col('RSI') < 70,  # But not overbought
                    col('MACD.macd') > col('MACD.signal'),  # MACD bullish crossover
                    col('close') > 10.0,  # Minimum price filter
                    col('ADRP') < 10,
                )
                .order_by('relative_volume_10d_calc', ascending=False)
                .limit(50))
        
        total_count, df = query.get_scanner_data()
        
        if not df.empty:
            print(f"Found {len(df)} stocks with MA breakout patterns:")
            print(df[['name', 'close', 'relative_volume_10d_calc', 'RSI']].head(10))
            return df
        else:
            print("No MA breakout patterns found")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error in MA breakout scan: {e}")
        return pd.DataFrame()

def scan_bollinger_band_breakout():
    """
    Scan for Bollinger Band squeeze and breakout patterns
    These often indicate significant price movements
    """
    print("=== Scanning for Bollinger Band Breakouts ===")
    
    try:
        query = (Query()
                .select('name', 'close', 'volume', 'relative_volume_10d_calc',
                       'BB.upper', 'BB.lower', 'BB.basis', 'ATR',
                       'RSI', 'ADX', 'price_52_week_high', 'price_52_week_low')
                .where(
                    # Price broke above upper Bollinger Band
                    col('exchange').isin(['NYSE', 'NASDAQ']),
                    col('market_cap_basic') > 1000_000_000,
                    col('volume') > 500_000,  # Minimum volume filter
                    col('close').crosses_above('BB.upper'),
                    col('relative_volume_10d_calc') > 1.2,  # Volume confirmation
                    col('ADX') > 25,  # Strong trend
                    col('RSI') > 50,  # Bullish momentum
                    col('RSI') < 80,  # Not extremely overbought
                    col('close').above_pct('price_52_week_high', 0.95), # Near 52-week highs
                    col('ADRP') < 10,
                )
                .order_by('Perf.3M', ascending=False)
                .limit(30))
        
        total_count, df = query.get_scanner_data()
        
        if not df.empty:
            print(f"Found {len(df)} stocks with BB breakout patterns:")
            print(df[['name', 'close', 'ADX', 'relative_volume_10d_calc']].head(10))
            return df
        else:
            print("No BB breakout patterns found")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error in BB breakout scan: {e}")
        return pd.DataFrame()

def scan_resistance_breakout():
    """
    Scan for stocks breaking above recent resistance levels
    Uses Donchian Channels as proxy for resistance levels
    """
    print("=== Scanning for Resistance Breakouts ===")
    
    try:
        query = (Query()
                .select('name', 'close', 'volume', 'relative_volume_10d_calc',
                       'DonchCh20.Upper', 'DonchCh20.Lower', 'DonchCh20.Middle',
                       'RSI', 'Stoch.K', 'Stoch.D', 'ADX',
                       'High.1M', 'High.3M')
                .where(
                    # Price broke above 20-period Donchian Channel (resistance)
                    col('exchange').isin(['NYSE', 'NASDAQ']),
                    col('market_cap_basic') > 1000_000_000,
                    col('volume') > 500_000,  # Minimum volume filter
                    col('high').above_pct('DonchCh20.Upper',0.97),
                    col('relative_volume_10d_calc') > 1.2,  # Volume spike
                    col('Stoch.K') > col('Stoch.D'),  # Stochastic bullish
                    col('ADX') > 20,  # Trend strength
                    col('RSI').between(50, 75),  # Moderate bullish momentum
                    col('close').above_pct('High.1M', 0.95),  # Near 1-month highs
                    col('high').above_pct('price_52_week_high',0.98),
                    col('ADRP') < 10,
                )
                .order_by('Perf.3M', ascending=False)
                .limit(30))
        
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

def scan_momentum_breakout():
    """
    Scan for momentum-based breakouts using multiple indicators
    Good for catching early stage breakouts
    """
    print("=== Scanning for Momentum Breakouts ===")
    
    try:
        query = (Query()
                .select('name', 'close', 'volume', 'relative_volume_10d_calc',
                       'RSI', 'RSI7', 'Mom', 'ROC', 'ADX',
                       'MACD.macd', 'MACD.signal', 'MACD.hist',
                       'SMA5', 'SMA10', 'SMA20')
                .where(
                    # Multiple momentum conditions
                    col('exchange').isin(['NYSE', 'NASDAQ']),
                    col('market_cap_basic') > 1000_000_000,
                    col('volume') > 500_000,  # Minimum volume filter
                    col('RSI') > 60,  # Strong momentum
                    col('RSI7') > col('RSI'),  # Short-term momentum accelerating
                    col('Mom') > 0,  # Positive momentum
                    col('ROC') > 5,  # Rate of change positive
                    col('MACD.hist') > 0,  # MACD histogram positive
                    col('MACD.macd') > col('MACD.signal'),  # MACD bullish
                    col('close') > col('SMA5'),  # Price above short-term MA
                    col('SMA5') > col('SMA10'),  # Short MA above medium MA
                    col('relative_volume_10d_calc') > 1.2,  # Volume confirmation
                    col('high').above_pct('price_52_week_high',0.98),
                    col('ADX') > 25,  # Strong trend
                    col('ADRP') < 10,
                )
                .order_by('Perf.3M', ascending=False)
                .limit(30))
        
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

def scan_gap_breakout():
    """
    Scan for gap-up breakouts that often signal strong momentum
    """
    print("=== Scanning for Gap Breakouts ===")
    
    try:
        query = (Query()
                .select('name', 'close', 'volume', 'relative_volume_10d_calc',
                       'gap', 'gap_up', 'open', 'high', 'low',
                       'RSI', 'ADX', 'SMA20', 'SMA50')
                .where(
                    # Significant gap up (more than 2%)
                    col('exchange').isin(['NYSE', 'NASDAQ']),
                    col('market_cap_basic') > 1000_000_000,
                    col('volume') > 500_000,  # Minimum volume filter
                    col('gap_up') > 2.0,
                    col('relative_volume_10d_calc') > 1.5,  # Volume confirmation
                    col('close') > col('open'),  # Closed higher than opened
                    col('RSI') > 50,  # Bullish momentum
                    col('RSI') < 75,  # Not overbought
                    col('ADX') > 20,  # Trend strength
                    col('close') > col('SMA20'),  # Above 20-day MA
                    col('SMA20') > col('SMA50'),  # 20 MA above 50 MA
                    col('high').above_pct('price_52_week_high',0.98),
                    col('ADRP') < 10,
                )
                .order_by('gap_up', ascending=False)
                .limit(25))
        
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

def save_results(all_results, filename_prefix="breakout_scan"):
    """
    Save scan results to CSV files with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for scan_name, df in all_results.items():
        if not df.empty:
            filename = f"{filename_prefix}_{scan_name}_{timestamp}.csv"
            df.to_csv(filename, index=False)
            print(f"Saved {scan_name} results to {filename}")

def run_comprehensive_breakout_scan():
    """
    Run all breakout scans and combine results
    """
    print("Starting Comprehensive Breakout Pattern Scan")
    print("=" * 60)
    print(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_results = {}
    
    # Run different breakout scans
    all_results['ma_breakout'] = scan_moving_average_breakout()
    time.sleep(1)  # Small delay to avoid rate limiting
    
    all_results['bb_breakout'] = scan_bollinger_band_breakout()
    time.sleep(1)
    
    all_results['resistance_breakout'] = scan_resistance_breakout()
    time.sleep(1)
    
    all_results['momentum_breakout'] = scan_momentum_breakout()
    time.sleep(1)
    
    all_results['gap_breakout'] = scan_gap_breakout()
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SCAN SUMMARY")
    print("=" * 60)
    
    total_stocks_found = 0
    for scan_name, df in all_results.items():
        count = len(df) if not df.empty else 0
        total_stocks_found += count
        print(f"{scan_name.replace('_', ' ').title()}: {count} stocks")
    
    print(f"\nTotal unique breakout patterns found: {total_stocks_found}")
    
    # Save results
    save_results(all_results)
    
    return all_results

def scan_breakout_comprehensive():
    print("=== Scanning for Comprehensive Breakouts ===")
    
    try:
        query = (Query()
                .select('name', 'close', 'volume', 'relative_volume_10d_calc', 'ATR',
                       'RSI', 'ADX', 'Perf.6M')
                .where(
                    # Price broke above upper Bollinger Band
                    col('exchange').isin(['NYSE', 'NASDAQ']),
                    col('market_cap_basic') > 1000_000_000,
                    col('average_volume_30d_calc') > 500_000,  # Minimum volume filter
                    col('relative_volume_10d_calc') > 1.1,  # Volume confirmation
                    col('ADX') > 25,  # Strong trend
                    col('RSI30') > 45,  # Bullish momentum
                    col('RSI30') < 75,  # Not extremely overbought
                    col('high').above_pct('DonchCh20.Upper',0.98),
                    col('Stoch.K') > col('Stoch.D'),  # Stochastic bullish
                    col('SMA10') > col('SMA30'),  # Short MA above medium MA
                    col('ADRP') < 10,
                    col('Perf.5Y') > 20,
                )
                .order_by('Perf.6M', ascending=False)
                .limit(25))
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

def main_breakout_scanner():
    """
    Main function to run the breakout scanner
    """
    try:
        # Install the library if not already installed
        # import subprocess
        # subprocess.check_call(['pip', 'install', 'tradingview-screener'])
        
        results = run_comprehensive_breakout_scan()
        
        # Additional analysis - find stocks appearing in multiple scans
        print("\n" + "=" * 60)
        print("STOCKS WITH MULTIPLE BREAKOUT SIGNALS")
        print("=" * 60)
        
        all_stocks = []
        for scan_name, df in results.items():
            if not df.empty:
                df_copy = df.copy()
                df_copy['scan_type'] = scan_name
                all_stocks.append(df_copy[['name', 'scan_type']])
        
        if all_stocks:
            combined_df = pd.concat(all_stocks, ignore_index=True)
            stock_counts = combined_df.groupby('name').size().sort_values(ascending=False)
            
            # Show stocks with 2+ breakout signals
            multiple_signals = stock_counts[stock_counts >= 2]
            if not multiple_signals.empty:
                print("Stocks with multiple breakout signals (stronger conviction):")
                for stock, count in multiple_signals.head(10).items():
                    scans = combined_df[combined_df['name'] == stock]['scan_type'].tolist()
                    print(f"  {stock}: {count} signals ({', '.join(scans)})")
            else:
                print("No stocks with multiple breakout signals found today.")
        
    except Exception as e:
        print(f"Error running breakout scanner: {e}")

def main():
    print("Welcome to the Comprehensive Breakout Scanner!")
    print("=" * 60)
    # run first scanner
    

if __name__ == '__main__':
    scan_moving_average_breakout()
    scan_bollinger_band_breakout()
    scan_resistance_breakout()
    scan_momentum_breakout()
    scan_gap_breakout()
    scan_breakout_comprehensive()
