import subprocess
import os
import sys
from .read_json import *
from datetime import datetime
from zoneinfo import ZoneInfo
from .trading_view_screener import *
from .tv_screen import *
from dotenv import load_dotenv
import time

def run_research_a_stock(ticker:str, date:str):
    save_path = os.getenv("SAVE_FOLDER")
    print(f"save_folder: {save_path}")

    print(f"调用 research_a_stock {ticker} {date}")
    print(f"starting at {datetime.now(ZoneInfo("US/Eastern"))}")
    print("this takes about 15-20 minutes")
    print("researching ...")
    # get current folder
    current_folder = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run([sys.executable, os.path.join(current_folder, 'research_a_stock.py'), ticker, date], capture_output=True, text=True)

    # 将stdout和stderr分别存到output文件夹里的{ticker}_stdout.txt和{ticker}_stderr.txt
    if not os.path.exists(f"{save_path}/eval_results/{date}/output"):
        os.makedirs(f"{save_path}/eval_results/{date}/output")
    with open(f"{save_path}/eval_results/{date}/output/{ticker}_stdout.txt", "w") as f:
        f.write(result.stdout)
    if result.stderr:
        with open(f"{save_path}/eval_results/{date}/output/{ticker}_stderr.txt", "w") as f:
            f.write(result.stderr)
    # 从full_states_log_{ticker}.json文件中读取最后一个状态
    print(f"finished at {datetime.now(ZoneInfo("US/Eastern"))}")
    # 等待3秒，确保文件写入完成
    i = 0
    while i < 5:
        if os.path.exists(f"{save_path}/eval_results/{date}/TradingAgentsStrategy_logs/full_states_log_{ticker}.json"):
            break
        print(f"wait for full_states_log_{ticker}.json to be created ...")
        time.sleep(3)
        i += 1
    if i == 5:
        raise TimeoutError(f"timeout waiting for full_states_log_{ticker}.json to be created: {ticker} {date}")
    print("saving each report ...")
    save_each_report(date, ticker)

def scan_and_research():
    load_dotenv()

    save_path = os.getenv("SAVE_FOLDER")
    formatted_date = datetime.now(ZoneInfo("US/Eastern")).strftime("%Y-%m-%d")

    previous_tickers = get_previous_tickers(formatted_date, 30)
    df = scan_all(universe_num_each=1000)
    list_of_tickers = df["name"].tolist()
    print(f"found: {list_of_tickers}")
    print(f"previous: {previous_tickers}")
    list_of_tickers = [ticker for ticker in list_of_tickers if ticker not in previous_tickers]
    print("research:", list_of_tickers)

    # list_of_tickers = ["VICR"]

    if not os.path.exists(f"{save_path}/eval_results/{formatted_date}"):
        os.makedirs(f"{save_path}/eval_results/{formatted_date}")
    with open(f"{save_path}/eval_results/{formatted_date}/tickers.txt", "a") as f:
        f.write(formatted_date)
        f.write("\n")
        f.write(str(df))
        f.write("\n")
        f.write(str(list_of_tickers))
        f.write("\n")
    
    for ticker in list_of_tickers:
        run_research_a_stock(ticker, formatted_date)

if __name__ == "__main__":
    scan_and_research()