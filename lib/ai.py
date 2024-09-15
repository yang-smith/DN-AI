
import os
from openai import OpenAI
import tiktoken
from lib.prompt import prompt_sys, prompt_tools

import os
import httpx
from aiolimiter import AsyncLimiter
import asyncio

limiter = AsyncLimiter(4, 1)  # 每秒最多4个请求

async def ai_chat_async(message, model="gpt-4o-mini", response_format='NOT_GIVEN', retries=3):
    timeout = httpx.Timeout(20.0, read=50.0)  
    async with httpx.AsyncClient(timeout=timeout) as client:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ]

        params = {
            "messages": messages,
            "model": model,
            "temperature": 0.05,
        }

        headers = {
            "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}"
        }

        if response_format == 'json':
            params["response_format"] = {"type": "json_object"}

        url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1") + "/chat/completions"

        for attempt in range(retries + 1):
            try:
                # 使用速率限制
                async with limiter:
                    response = await client.post(url, json=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data['choices'][0]['message']['content']
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # 处理请求过多的情况
                    await asyncio.sleep((2 ** attempt) * 60)  # 指数级退避
                elif e.response.status_code >= 500:  # 处理服务器错误
                    await asyncio.sleep(2 ** attempt)  # 短暂退避
                else:
                    raise  # 其他错误不重试
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt < retries:
                    await asyncio.sleep(2 ** attempt)  # 网络问题的指数级退避
                else:
                    raise  

def ai_chat(message, model="gpt-3.5-turbo", response_format = 'NOT_GIVEN'):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )
    messages=[
        {
            "role": "system", 
            "content": "You are a helpful assitant."
        },
        {
            "role": "user",
            "content": message,
        }
    ]
    if response_format == 'json':
        chat_completion = client.chat.completions.create(
            messages=messages,
            response_format=  { "type": "json_object" },
            model=model,
            temperature=0.05
        )
    else:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.05
        )
    return chat_completion.choices[0].message.content



def ai_long_chat(messages, model="gpt-3.5-turbo", response_format = 'NOT_GIVEN'):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )
    if response_format == 'json':
        chat_completion = client.chat.completions.create(
            messages=messages,
            response_format=  { "type": "json_object" },
            model=model,
            temperature=0.05
        )
    else:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.05
        )
    return chat_completion.choices[0].message.content

def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def truncate_list_by_token_size(list_data: list,max_token_size: int):
    """Truncate a list of data by token size"""
    tokens = 0
    for i, data in enumerate(list_data):
        tokens += num_tokens_from_string(data)
        if tokens > max_token_size:
            return list_data[:i]
    return list_data

import json
import os
from openai import OpenAI
from lib.db import get_document_by_similar_search, get_records_by_similar_search, get_records_by_time, collection,collection_DN



def get_record_by_time(start, end):
    # collection = init_db()
    return get_records_by_time(collection=collection, start=start, end=end)

def get_record_by_similar_search(user_input):
    return get_records_by_similar_search(collection=collection, user_input=user_input, n_results=10)

def get_information_from_documents(user_input):
    return get_document_by_similar_search(collection=collection_DN, user_input=user_input, n_results=4)

def run_conversation(message, model="gpt-4o"):
    client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE"),
    )
    messages=[
            {
                "role": "system", 
                "content": prompt_tools
            },
            {
                "role": "user",
                "content": message,
            }
        ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_record_by_time",
                "description": "Retrieve chat records from a WeChat group within a specified date range",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                        "end": {"type": "string", "description": "End date in YYYY-MM-DD format"},
                    },
                    "required": ["start", "end"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_record_by_similar_search",
                "description": "Retrieve chat records by searching for text similar to the user input",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_input": {"type": "string", "description": "Text input by the user to search similar chat records"},
                    },
                    "required": ["user_input"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_information_from_documents",
                "description": "Retrieve relevant information from documents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_input": {"type": "string", "description": "multi Search query from different dimensions"},
                    },
                    "required": ["user_input"],
                },
            },
        },
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    print(response)
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "get_record_by_time": get_record_by_time,
            "get_record_by_similar_search": get_record_by_similar_search,
            "get_information_from_documents": get_information_from_documents,
        }
        # messages.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name == "get_information_from_documents":
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                messages[1]["content"] += f"\n 文档的参考信息:{function_response}\n"
            else:
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                messages[1]["content"] += f"\n 在地群聊天记录:{function_response}\n"
            # messages.append({
            #     "tool_call_id": tool_call.id,
            #     "role": "tool",
            #     "name": function_name,
            #     "content": function_response,
            # })
        messages[0]['content'] = prompt_sys
        print(messages)
        second_response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return second_response.choices[0].message.content

# print(run_conversation())
