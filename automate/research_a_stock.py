from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from dotenv import load_dotenv
import datetime

import argparse, sys, os

# parse arguments
parser = argparse.ArgumentParser(description='research a stock')
parser.add_argument('ticker', type=str, help='the ticker of the stock')
parser.add_argument('date', type=str, help='the date to research')
parser.add_argument('company_name', type=str, help='the company name of the stock')
args = parser.parse_args()           # 解析完后所有结果都挂在 args 上
print(f'Research {args.ticker} on {args.date}, company name: {args.company_name}')

# Load environment variables from .env file
load_dotenv()

# Create a custom config
config = DEFAULT_CONFIG.copy()

config["tpm"] = os.getenv("TPM", 1000000)

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
config["llm_provider"] = LLM_PROVIDER
config["backend_url"] = os.getenv("BASE_URL")
if LLM_PROVIDER == "moonshot":
    config["api_key"] = os.getenv("MOONSHOT_API_KEY")
    config["deep_think_llm"] = "kimi-k2-0905-preview"  # Use a different model
    config["quick_think_llm"] = "kimi-k2-0905-preview"  # Use a different model
    if not config["api_key"]:
        raise ValueError("MOONSHOT_API_KEY not found in environment variables")
elif LLM_PROVIDER == "dashscope":
    config["api_key"] = os.getenv("DASHSCOPE_API_KEY")
    config["deep_think_llm"] = os.getenv("DEEPTHINK_MODEL", "qwen3-max")
    config["quick_think_llm"] = os.getenv("QUICKTHINK_MODEL", "qwen-flash")
    if not config["api_key"]:
        raise ValueError("DASHSCOPE_API_KEY not found in environment variables")
else:
    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

config["max_debate_rounds"] = 1  # Increase debate rounds

# Configure data vendors (default uses yfinance and alpha_vantage)
config["data_vendors"] = {
    "core_stock_apis": "yfinance",           # Options: yfinance, alpha_vantage, local
    "technical_indicators": "yfinance",      # Options: yfinance, alpha_vantage, local
    "fundamental_data": "alpha_vantage",     # Options: openai, alpha_vantage, local
    "news_data": "alpha_vantage",            # Options: openai, alpha_vantage, google, local
}


print("===============================================")
print(f"researching {args.ticker} ({args.company_name}) on {args.date}")
print("===============================================")

ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate(company_name=args.company_name, trade_date=args.date, ticker_name=args.ticker)

# decision = "BUY" # a test variable
print("decision:", decision)

save_path = os.getenv("SAVE_FOLDER")
print(f"save_path: {save_path}")
# 保存决策到txt文件
if not os.path.exists(f"{save_path}/eval_results/{args.date}/decisions"):
    os.makedirs(f"{save_path}/eval_results/{args.date}/decisions")
with open(f"{save_path}/eval_results/{args.date}/decisions/{args.ticker}.txt", "w") as f:
    f.write(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
