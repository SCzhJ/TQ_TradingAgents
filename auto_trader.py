import subprocess
import os
import sys
from read_json import *
import datetime

def run_research_a_stock(ticker:str, date:str):
    print(f"调用 research_a_stock {ticker} {date}")
    print(f"starting at {datetime.datetime.now()}")
    print("this takes about 20 minutes")
    print("researching ...")
    result = subprocess.run([sys.executable, 'research_a_stock.py', ticker, date], capture_output=True, text=True)
    # 将stdout和stderr分别存到output文件夹里的{ticker}_stdout.txt和{ticker}_stderr.txt
    if not os.path.exists(f"eval_results/{date}/output"):
        os.makedirs(f"eval_results/{date}/output")
    with open(f"eval_results/{date}/output/{ticker}_stdout.txt", "w") as f:
        f.write(result.stdout)
    if result.stderr:
        with open(f"eval_results/{date}/output/{ticker}_stderr.txt", "w") as f:
            f.write(result.stderr)
    # 从full_states_log_{ticker}.json文件中读取最后一个状态
    print(f"finished at {datetime.datetime.now()}")
    print("saving each report ...")
    save_each_report(date, ticker)

def main():
    list_of_ticker = ["PLTR", "NVDA", "AMD", "INTC", "TSM", "MSFT", "GOOGL"]
    # ticker = "U"
    date = "2024-10-10"
    for ticker in list_of_ticker:
        run_research_a_stock(ticker, date)

if __name__ == "__main__":
    main()