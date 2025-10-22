import subprocess
import os
import sys
from read_json import *
import datetime
from zoneinfo import ZoneInfo
from trading_view_screener import *
from dotenv import load_dotenv

def run_research_a_stock(ticker:str, date:str):
    print(f"调用 research_a_stock {ticker} {date}")
    print(f"starting at {datetime.datetime.now(ZoneInfo("US/Eastern"))}")
    print("this takes about 15-20 minutes")
    print("researching ...")
    # get current folder
    current_folder = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run([sys.executable, os.path.join(current_folder, 'research_a_stock.py'), ticker, date], capture_output=True, text=True)

    save_path = os.getenv("SAVE_FOLDER")
    # 将stdout和stderr分别存到output文件夹里的{ticker}_stdout.txt和{ticker}_stderr.txt
    if not os.path.exists(f"{save_path}/eval_results/{date}/output"):
        os.makedirs(f"{save_path}/eval_results/{date}/output")
    with open(f"{save_path}/eval_results/{date}/output/{ticker}_stdout.txt", "w") as f:
        f.write(result.stdout)
    if result.stderr:
        with open(f"{save_path}/eval_results/{date}/output/{ticker}_stderr.txt", "w") as f:
            f.write(result.stderr)
    # 从full_states_log_{ticker}.json文件中读取最后一个状态
    print(f"finished at {datetime.datetime.now(ZoneInfo("US/Eastern"))}")
    print("saving each report ...")
    save_each_report(date, ticker)

def main():
    load_dotenv()
    save_path = os.getenv("SAVE_FOLDER")
    formatted_date = datetime.datetime.now(ZoneInfo("US/Eastern")).strftime("%Y-%m-%d")
    df = scan_breakout_3timeframes()
    
    if not os.path.exists(f"{save_path}/eval_results/{formatted_date}"):
        os.makedirs(f"{save_path}/eval_results/{formatted_date}")
    with open(f"{save_path}/eval_results/{formatted_date}/tickers.txt", "a") as f:
        f.write(formatted_date)
        f.write("\n")
        f.write(str(df))
        f.write("\n")
    list_of_ticker = df["name"].tolist()
    
    for ticker in list_of_ticker:
        run_research_a_stock(ticker, formatted_date)

if __name__ == "__main__":
    main()