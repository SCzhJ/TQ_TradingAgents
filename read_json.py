# 读取full_states_log_EL.json文件
import os
import json


def get_json(date:str, ticker:str):
    with open(f"eval_results/{date}/TradingAgentsStrategy_logs/full_states_log_{ticker}.json", "r") as f:
        data = json.load(f)
    return data

def get_each_report(date:str, ticker:str):
    data = get_json(date, ticker)[date]

    market_report = data["market_report"]
    sentiment_report = data["sentiment_report"]
    news_report = data["news_report"]
    fundamentals_report = data["fundamentals_report"]

    bull_history = data['investment_debate_state']['bull_history']
    bear_history = data['investment_debate_state']['bear_history']
    history_bb   = data['investment_debate_state']['history']
    current_response = data['investment_debate_state']['current_response']
    judge_decision_bb = data['investment_debate_state']['judge_decision']
    
    trader_investment_decision = data['trader_investment_decision']

    risky_history = data['risk_debate_state']['risky_history']
    safe_history = data['risk_debate_state']['safe_history']
    neutral_history = data['risk_debate_state']['neutral_history']
    history_rs = data['risk_debate_state']['history']
    judge_decision_rs = data['risk_debate_state']['judge_decision']

    investment_plan = data['investment_plan']
    final_trade_decision = data['final_trade_decision']
    return {
        "0_market_report": market_report,
        "1_sentiment_report": sentiment_report,
        "2_news_report": news_report,
        "3_fundamentals_report": fundamentals_report,
        "4_bull_history": bull_history,
        "5_bear_history": bear_history,
        "6_history_bb": history_bb,
        "7_current_response": current_response,
        "8_judge_decision_bb": judge_decision_bb,
        "9_trader_investment_decision": trader_investment_decision,
        "10_risky_history": risky_history,
        "11_safe_history": safe_history,
        "12_neutral_history": neutral_history,
        "13_history_rs": history_rs,
        "14_judge_decision_rs": judge_decision_rs,
        "15_investment_plan": investment_plan,
        "16_final_trade_decision": final_trade_decision,
    }

def save_in_txt(date:str, ticker:str, report:str, name:str):
    '''
    保存每个报告的txt文件
    '''
    # make directory
    if not os.path.exists(f"eval_results/{date}/reports/{ticker}"):
        os.makedirs(f"eval_results/{date}/reports/{ticker}")
    
    with open(f"eval_results/{date}/reports/{ticker}/{ticker}_{name}.txt", "w", encoding='utf-8') as f:
        f.write(report)

def save_each_report(date:str, ticker:str):
    all_report = get_each_report(date, ticker)
    for key, value in all_report.items():
        save_in_txt(date, ticker, value, key)


if __name__ == "__main__":
    date = "2025-10-17"
    ticker = "AXP"
    save_each_report(date, ticker)