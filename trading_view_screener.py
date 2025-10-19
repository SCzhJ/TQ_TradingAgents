from tradingview_screener import Query, col
import pandas as pd

def scan_breakout(
    breakout_percent:int=0.05,
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

def main():
    df = scan_breakout()

if __name__ == '__main__':
    main()