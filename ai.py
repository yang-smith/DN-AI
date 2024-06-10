
import os
from openai import OpenAI
from prompt import prompt_sys
def ai_chat(message, model="gpt-3.5-turbo"):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": prompt_sys
            },
            {
                "role": "user",
                "content": message,
            }
        ],
        model=model,
    )

    # print(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content




import json
import os
from openai import OpenAI
from db import get_records_by_similar_search, get_records_by_time, collection



def get_record_by_time(start, end):
    # collection = init_db()
    return get_records_by_time(collection=collection, start=start, end=end)

def get_record_by_similar_search(user_input):
    return get_records_by_similar_search(collection=collection, user_input=user_input, n_results=10)

def run_conversation(message, model="gpt-4o"):
    client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE"),
    )
    messages=[
            {
                "role": "system", 
                "content": prompt_sys
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
        }
        messages.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            # if function_to_call == 'get_record_by_time':
            #     function_response = function_to_call(**function_args)
            #     print(len(function_response))
            #     if len(function_response) > 8000:
            #         print("get_record_by_time too long")
            #     else:
            #         messages.append({
            #             "tool_call_id": tool_call.id,
            #             "role": "tool",
            #             "name": function_name,
            #             "content": function_response,
            #         })
            #     continue
            function_response = function_to_call(**function_args)
            # print(function_response)
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })

        second_response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return second_response.choices[0].message.content

# print(run_conversation())
