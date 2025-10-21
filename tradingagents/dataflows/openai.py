from openai import OpenAI
from .config import get_config
import os
import dotenv
import json

dotenv.load_dotenv()
# 使用 Moonshot API Key
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")

def chat_with_web_search(client, messages, model):
    """处理带有联网搜索的对话流程"""
    finish_reason = None
    final_response = None
    
    while finish_reason is None or finish_reason == "tool_calls":
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1,
            max_tokens=4096,
            top_p=1,
            tools=[
                {
                    "type": "builtin_function",
                    "function": {
                        "name": "$web_search",
                    },
                }
            ]
        )
        
        choice = completion.choices[0]
        finish_reason = choice.finish_reason
        
        if finish_reason == "tool_calls":
            messages.append(choice.message)
            for tool_call in choice.message.tool_calls:
                tool_call_name = tool_call.function.name
                tool_call_arguments = json.loads(tool_call.function.arguments)
                
                if tool_call_name == "$web_search":
                    # Moonshot 内置的 $web_search 只需要返回参数即可
                    tool_result = tool_call_arguments
                else:
                    tool_result = f"Error: unable to find tool by name '{tool_call_name}'"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call_name,
                    "content": json.dumps(tool_result),
                })
        else:
            final_response = choice.message.content
    
    return final_response

def get_stock_news_openai(query, start_date, end_date):
    config = get_config()
    client = OpenAI(
        api_key=MOONSHOT_API_KEY,
        base_url="https://api.moonshot.cn/v1"  # Moonshot API 端点
    )

    messages = [
        {
            "role": "system", 
            "content": "You are a professional financial analyst skilled in searching and analyzing stock-related information."
        },
        {
            "role": "user",
            "content": f"Can you search Social Media for {query} from {start_date} to {end_date}? Make sure you only get the data posted during that period."
        }
    ]

    response = chat_with_web_search(client, messages, "kimi-k2-0905-preview")
    return response

def get_global_news_openai(curr_date, look_back_days=7, limit=5):
    config = get_config()
    client = OpenAI(
        api_key=MOONSHOT_API_KEY,
        base_url="https://api.moonshot.cn/v1"
    )

    messages = [
        {
            "role": "system",
            "content": "You are a professional macroeconomic analyst skilled in searching and analyzing global news."
        },
        {
            "role": "user",
            "content": f"Can you search global or macroeconomics news from {look_back_days} days before {curr_date} to {curr_date} that would be informative for trading purposes? Make sure you only get the data posted during that period. Limit the results to {limit} articles."
        }
    ]

    response = chat_with_web_search(client, messages, "kimi-k2-0905-preview")
    return response

def get_fundamentals_openai(ticker, curr_date):
    config = get_config()
    client = OpenAI(
        api_key=MOONSHOT_API_KEY,
        base_url="https://api.moonshot.cn/v1"
    )

    messages = [
        {
            "role": "system",
            "content": "You are a professional financial analyst skilled in analyzing company fundamental data."
        },
        {
            "role": "user",
            "content": f"Can you search Fundamental for discussions on {ticker} during of the month before {curr_date} to the month of {curr_date}. Make sure you only get the data posted during that period. List as a table, with PE/PS/Cash flow/ etc"
        }
    ]

    response = chat_with_web_search(client, messages, "kimi-k2-0905-preview")
    return response

# from openai import OpenAI
# from .config import get_config
# import os
# import dotenv

# dotenv.load_dotenv()
# # The OPENAI_API_KEY is actually moonshot's kimi-2's api key
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# def get_stock_news_openai(query, start_date, end_date):
#     config = get_config()
#     client = OpenAI(
#         api_key=OPENAI_API_KEY,
#         base_url=config["backend_url"])

#     response = client.responses.create(
#         model=config["quick_think_llm"],
#         input=[
#             {
#                 "role": "system",
#                 "content": [
#                     {
#                         "type": "input_text",
#                         "text": f"Can you search Social Media for {query} from {start_date} to {end_date}? Make sure you only get the data posted during that period.",
#                     }
#                 ],
#             }
#         ],
#         text={"format": {"type": "text"}},
#         reasoning={},
#         tools=[
#             {
#                 "type": "web_search_preview",
#                 "user_location": {"type": "approximate"},
#                 "search_context_size": "low",
#             }
#         ],
#         temperature=1,
#         max_output_tokens=4096,
#         top_p=1,
#         store=True,
#     )

#     return response.output[1].content[0].text


# def get_global_news_openai(curr_date, look_back_days=7, limit=5):
#     config = get_config()
#     client = OpenAI(
#         api_key=OPENAI_API_KEY,
#         base_url=config["backend_url"])

#     response = client.responses.create(
#         model=config["quick_think_llm"],
#         input=[
#             {
#                 "role": "system",
#                 "content": [
#                     {
#                         "type": "input_text",
#                         "text": f"Can you search global or macroeconomics news from {look_back_days} days before {curr_date} to {curr_date} that would be informative for trading purposes? Make sure you only get the data posted during that period. Limit the results to {limit} articles.",
#                     }
#                 ],
#             }
#         ],
#         text={"format": {"type": "text"}},
#         reasoning={},
#         tools=[
#             {
#                 "type": "web_search_preview",
#                 "user_location": {"type": "approximate"},
#                 "search_context_size": "low",
#             }
#         ],
#         temperature=1,
#         max_output_tokens=4096,
#         top_p=1,
#         store=True,
#     )

#     return response.output[1].content[0].text


# def get_fundamentals_openai(ticker, curr_date):
#     config = get_config()
#     client = OpenAI(
#         api_key=OPENAI_API_KEY,
#         base_url=config["backend_url"])

#     response = client.responses.create(
#         model=config["quick_think_llm"],
#         input=[
#             {
#                 "role": "system",
#                 "content": [
#                     {
#                         "type": "input_text",
#                         "text": f"Can you search Fundamental for discussions on {ticker} during of the month before {curr_date} to the month of {curr_date}. Make sure you only get the data posted during that period. List as a table, with PE/PS/Cash flow/ etc",
#                     }
#                 ],
#             }
#         ],
#         text={"format": {"type": "text"}},
#         reasoning={},
#         tools=[
#             {
#                 "type": "web_search_preview",
#                 "user_location": {"type": "approximate"},
#                 "search_context_size": "low",
#             }
#         ],
#         temperature=1,
#         max_output_tokens=4096,
#         top_p=1,
#         store=True,
#     )

#     return response.output[1].content[0].text