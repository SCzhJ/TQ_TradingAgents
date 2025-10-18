from tradingagents.trading_view_screener import scan_breakout
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from dotenv import load_dotenv
import datetime

def AutoSuggestion(date: str):
    '''
    AutoSuggestion for selected stock on date

    Args:
        date: str, format "YYYY-MM-DD"
    Returns:
        all_suggestions: dict, key is stock name, value is decision
    '''
    load_dotenv()
    selected_stock_df = scan_breakout()
    selected_stock_name = selected_stock_df['name'].tolist()
    print(f"Selected stock name: {selected_stock_name}")

    # Create a custom config
    config = DEFAULT_CONFIG.copy()
    config["deep_think_llm"] = "kimi-k2-0905-preview"  # Use a different model
    config["quick_think_llm"] = "kimi-k2-0905-preview"  # Use a different model
    config["max_debate_rounds"] = 1  # Increase debate rounds

    # Configure data vendors (default uses yfinance and alpha_vantage)
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",           # Options: yfinance, alpha_vantage, local
        "technical_indicators": "yfinance",      # Options: yfinance, alpha_vantage, local
        "fundamental_data": "alpha_vantage",     # Options: openai, alpha_vantage, local
        "news_data": "alpha_vantage",            # Options: openai, alpha_vantage, google, local
    }

    all_suggestions = {}

    for i, stock in enumerate(selected_stock_name):
        # Create a unique config copy for each iteration
        unique_config = config.copy()
        # Add a unique identifier to avoid collection name conflicts
        unique_config['instance_id'] = f"instance_{i}_{datetime.datetime.now().timestamp()}"
        
        # Initialize a new instance for each stock iteration
        ta = TradingAgentsGraph(debug=True, config=unique_config)
        # forward propagate
        _, decision = ta.propagate(stock, date)
        # Memorize mistakes and reflect
        # ta.reflect_and_remember(1000) # parameter is the position returns
        all_suggestions[stock] = decision
    
    return all_suggestions


def main():
    # Get yesterday's date in "YYYY-MM-DD" format
    print("Get yesterday's date")
    today = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    print(today)
    all_suggestions = AutoSuggestion(today)
    print(all_suggestions)

if __name__ == "__main__":
    main()
