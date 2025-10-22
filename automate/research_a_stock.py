from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from dotenv import load_dotenv
import datetime

import argparse, sys, os

# parse arguments
parser = argparse.ArgumentParser(description='research a stock')
parser.add_argument('ticker', type=str, help='the ticker of the stock')
parser.add_argument('date', type=str, help='the date to research')
args = parser.parse_args()           # 解析完后所有结果都挂在 args 上
print(f'Research {args.ticker} on {args.date}')

# Load environment variables from .env file
load_dotenv()

# Create a custom config
config = DEFAULT_CONFIG.copy()

config["tpm"] = os.getenv("TPM", 1500)

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
config["llm_provider"] = LLM_PROVIDER
if LLM_PROVIDER == "moonshot":
    config["backend_url"] = "https://api.moonshot.cn/v1"
    config["api_key"] = os.getenv("MOONSHOT_API_KEY")
    config["deep_think_llm"] = "kimi-k2-0905-preview"  # Use a different model
    config["quick_think_llm"] = "kimi-k2-0905-preview"  # Use a different model
    if not config["api_key"]:
        raise ValueError("MOONSHOT_API_KEY not found in environment variables")
elif LLM_PROVIDER == "siliconflow":
    config["backend_url"] = "https://api.siliconflow.cn/v1"
    config["api_key"] = os.getenv("SILICONFLOW_API_KEY")
    config["deep_think_llm"] = "Qwen/Qwen3-235B-A22B-Instruct-2507"
    config["quick_think_llm"] = "Qwen/Qwen3-30B-A3B-Instruct-2507"  # Use a different model
    if not config["api_key"]:
        raise ValueError("SILICONFLOW_API_KEY not found in environment variables")
elif LLM_PROVIDER == "dashscope":
    config["backend_url"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    config["api_key"] = os.getenv("DASHSCOPE_API_KEY")
    config["deep_think_llm"] = "qwen3-max"
    config["quick_think_llm"] = "qwen3-max"  # Use a different model
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

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate(args.ticker, args.date)

# decision = "BUY" # a test variable
print("decision:", decision)

save_path = os.getenv("SAVE_FOLDER")
# 保存决策到txt文件
if not os.path.exists(f"{save_path}/eval_results/{args.date}/decisions"):
    os.makedirs(f"{save_path}/eval_results/{args.date}/decisions")
with open(f"{save_path}/eval_results/{args.date}/decisions/{args.ticker}.txt", "w") as f:
    f.write(decision)

# test
# a = 0
# b = 5/a
# print(b)
# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
