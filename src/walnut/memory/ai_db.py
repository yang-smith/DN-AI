
import json
import os
from openai import OpenAI
from walnut.memory.vector_db import get_document_by_similar_search, get_records_by_similar_search, get_records_by_time, collection,collection_DN
import logging
from datetime import datetime

from walnut.memory.prompt.prompt import prompt_chat, prompt_sys, prompt_tools, prompt_start
from collections import deque

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

def get_record_by_time(start, end):
    return get_records_by_time(collection=collection, start=start, end=end)

def get_record_by_similar_search(user_input):
    return get_records_by_similar_search(collection=collection, user_input=user_input, n_results=10)

def get_information_from_documents(user_input):
    return get_document_by_similar_search(collection=collection_DN, user_input=user_input, n_results=4)

def get_information(client, message, model="gpt-4-turbo-2024-04-09"):
    """获取辅助信息"""
    message += f"\n 辅助信息：现在是 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
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
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    print(response)
    tool_calls = response_message.tool_calls
    
    second_message = ""
    if tool_calls:
        available_functions = {
            "get_record_by_time": get_record_by_time,
            "get_record_by_similar_search": get_record_by_similar_search,
            "get_information_from_documents": get_information_from_documents,
        }
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name == "get_information_from_documents":
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                second_message += f"\n 文档的参考信息:{function_response}\n"
            else:
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                second_message += f"\n 群聊天记录参考信息:{function_response}\n"
    else:
        second_message = response.choices[0].message.content
        
    return second_message


def check_information():
    """检查获取到的辅助信息是否过多或者包含无效信息"""
    return

