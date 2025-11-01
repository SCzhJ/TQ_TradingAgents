import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class StockDataDownloader:
    """
    股票数据下载器 - 支持多个数据源
    默认使用yfinance (免费且稳定)
    """
    
    def __init__(self, 
                 default_source: str = 'yfinance',
                 retry_attempts: int = 3,
                 retry_delay: int = 1,
                 cache_enabled: bool = True):
        """
        初始化数据下载器
        
        Args:
            default_source: 默认数据源 ('yfinance', 'alpha_vantage', 'polygon')
            retry_attempts: 重试次数
            retry_delay: 重试延迟(秒)
            cache_enabled: 是否启用缓存
        """
        self.default_source = default_source
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.cache_enabled = cache_enabled
        self._cache = {}
        
        # 数据源配置
        self.sources = {
            'yfinance': {
                'function': self._download_yfinance,
                'needs_api_key': False,
                'rate_limit': 2000  # 每小时请求限制
            },
            'alpha_vantage': {
                'function': self._download_alpha_vantage,
                'needs_api_key': True,
                'rate_limit': 500
            },
        }
    
    def download_stock_data(self, 
                          symbols: List[str],
                          period: str = '6mo',
                          interval: str = '1d',
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          source: Optional[str] = None,
                          auto_adjust: bool = True,
                          prepost: bool = True) -> Dict[str, pd.DataFrame]:
        """
        批量下载股票数据
        
        Args:
            symbols: 股票代码列表，如 ['NVDA', 'TSLA', 'MU']
            period: 时间周期 ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: 时间间隔 ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            source: 数据源 (None则使用默认)
            auto_adjust: 是否自动调整价格 (分红配股)
            prepost: 是否包含盘前盘后数据
            
        Returns:
            dict: {symbol: DataFrame} 格式的数据
        """
        if source is None:
            source = self.default_source
            
        print(f"📥 开始下载数据，使用数据源: {source}")
        print(f"📈 股票列表: {symbols}")
        
        results = {}
        failed_symbols = []
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n🔍 [{i}/{len(symbols)}] 正在下载 {symbol}...")
            
            try:
                # 尝试从缓存获取
                if self.cache_enabled and symbol in self._cache:
                    df = self._cache[symbol]
                    print(f"✅ {symbol} 从缓存加载")
                else:
                    # 下载数据
                    df = self._download_with_retry(
                        symbol=symbol,
                        period=period,
                        interval=interval,
                        start_date=start_date,
                        end_date=end_date,
                        source=source,
                        auto_adjust=auto_adjust,
                        prepost=prepost
                    )
                    
                    # 缓存数据
                    if self.cache_enabled:
                        self._cache[symbol] = df
                    
                    print(f"✅ {symbol} 下载完成，共 {len(df)} 条记录")
                
                # 验证数据质量
                if self._validate_data_quality(df, symbol):
                    results[symbol] = df
                    print(f"✅ {symbol} 数据验证通过")
                else:
                    failed_symbols.append(symbol)
                    print(f"❌ {symbol} 数据质量检查失败")
                
                # 控制请求频率
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ {symbol} 下载失败: {str(e)}")
                failed_symbols.append(symbol)
        
        # 打印总结
        print(f"\n📊 下载完成!")
        print(f"✅ 成功: {len(results)} 只股票")
        print(f"❌ 失败: {len(failed_symbols)} 只股票")
        
        if failed_symbols:
            print(f"失败的代码: {failed_symbols}")
        
        return results
    
    def _download_with_retry(self, **kwargs) -> pd.DataFrame:
        """带重试机制的数据下载"""
        source = kwargs.get('source', self.default_source)
        
        for attempt in range(self.retry_attempts):
            try:
                return self.sources[source]['function'](**kwargs)
            except Exception as e:
                print(f"⚠️  第 {attempt + 1} 次尝试失败: {str(e)}")
                
                if attempt < self.retry_attempts - 1:
                    print(f"⏳ 等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"下载失败，已尝试 {self.retry_attempts} 次")
    
    def _download_yfinance(self, symbol: str, period: str, interval: str,
                          start_date: Optional[str], end_date: Optional[str],
                          auto_adjust: bool, prepost: bool, **kwargs) -> pd.DataFrame:
        """使用yfinance下载数据"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 如果指定了起止日期，使用日期范围
            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, 
                                  interval=interval, auto_adjust=auto_adjust,
                                  prepost=prepost, actions=False)
            else:
                df = ticker.history(period=period, interval=interval,
                                  auto_adjust=auto_adjust, prepost=prepost,
                                  actions=False)
            
            if df.empty:
                raise ValueError(f"{symbol} 没有返回数据")
            
            # 标准化列名
            df = self._standardize_columns(df)
            
            return df
            
        except Exception as e:
            raise Exception(f"yfinance 下载失败: {str(e)}")
    
    def _download_alpha_vantage(self, symbol: str, interval: str, **kwargs) -> pd.DataFrame:
        """使用Alpha Vantage下载数据 (需要API密钥)"""
        # 注意：Alpha Vantage 需要注册获取免费API密钥
        # 这里提供代码框架，实际使用时需要设置API_KEY
        
        API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')  # 设置你的API密钥
        
        if API_KEY == 'demo':
            print("⚠️  使用演示模式，可能有限制")
        
        try:
            # 构建请求URL
            function_map = {
                '1m': 'TIME_SERIES_INTRADAY&interval=1min',
                '5m': 'TIME_SERIES_INTRADAY&interval=5min',
                '15m': 'TIME_SERIES_INTRADAY&interval=15min',
                '1d': 'TIME_SERIES_DAILY',
                '1wk': 'TIME_SERIES_WEEKLY',
                '1mo': 'TIME_SERIES_MONTHLY'
            }
            
            function = function_map.get(interval, 'TIME_SERIES_DAILY')
            
            url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={API_KEY}&outputsize=full"
            
            response = requests.get(url)
            data = response.json()
            
            # 解析数据
            if "Time Series" in data:
                time_series_key = list(data["Time Series"].keys())[0]
                df = pd.DataFrame.from_dict(data["Time Series"][time_series_key], orient='index')
                df = df.astype(float)
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                return df
            else:
                raise ValueError(f"Alpha Vantage 返回错误: {data}")
                
        except Exception as e:
            raise Exception(f"Alpha Vantage 下载失败: {str(e)}")
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名格式"""
        # yfinance返回的列名首字母大写，我们转换为小写
        column_mapping = {
            'Open': 'open',
            'High': 'high', 
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 确保所有需要的列都存在
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                # 如果缺少某列，尝试用close列填充或创建默认值
                if col in ['open', 'high', 'low']:
                    df[col] = df['close']
                else:
                    df[col] = 0
        
        return df[required_columns]
    
    def _validate_data_quality(self, df: pd.DataFrame, symbol: str) -> bool:
        """验证数据质量"""
        if df.empty:
            print(f"❌ {symbol} 数据为空")
            return False
        
        if len(df) < 30:  # 至少需要30条记录
            print(f"❌ {symbol} 数据量不足: {len(df)} 条")
            return False
        
        # 检查是否有缺失值
        if df.isnull().any().any():
            null_counts = df.isnull().sum()
            print(f"⚠️  {symbol} 存在缺失值: {null_counts.to_dict()}")
            
            # 简单的缺失值处理
            df.fillna(method='ffill', inplace=True)
            df.fillna(method='bfill', inplace=True)
        
        # 检查价格是否合理（不为负，不为零）
        if (df[['open', 'high', 'low', 'close']] <= 0).any().any():
            print(f"❌ {symbol} 存在无效价格数据")
            return False
        
        # 检查价格逻辑（high >= low, close在high-low范围内）
        price_logic_errors = 0
        price_logic_errors += (df['high'] < df['low']).sum()
        price_logic_errors += (df['close'] > df['high']).sum()
        price_logic_errors += (df['close'] < df['low']).sum()
        
        if price_logic_errors > 0:
            print(f"⚠️  {symbol} 存在 {price_logic_errors} 条价格逻辑错误")
        
        return price_logic_errors < len(df) * 0.1  # 错误率小于10%
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        return {
            'cache_size': len(self._cache),
            'cached_symbols': list(self._cache.keys()),
            'cache_enabled': self.cache_enabled
        }
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        print("✅ 缓存已清空")
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'current_price': info.get('currentPrice', 'N/A'),
                'currency': info.get('currency', 'USD')
            }
        except Exception as e:
            print(f"获取 {symbol} 信息失败: {e}")
            return {'symbol': symbol, 'error': str(e)}


# ===== 使用示例 =====
if __name__ == "__main__":
    # 股票列表
    symbols = ['NVDA', 'TSLA', 'MU', 'AAPL', 'MSFT']
    period = '6mo',
    interval = '1d'

    # 1. 下载数据
    downloader = StockDataDownloader()
    stock_data = downloader.download_stock_data(
        symbols=symbols,
        period=period,
        interval=interval
    )
    
    