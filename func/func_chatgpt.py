#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
import os

import httpx
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI
from prompt import prompt_sys, prompt_tools, prompt_start

class ChatGPT():
    def __init__(self) -> None:
        self.LOG = logging.getLogger("ChatGPT")
        self.client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_API_BASE"),
        )
        self.model = "gpt-3.5-turbo"
        self.conversation_list = {}
        self.system_content_msg = {"role": "system", "content": prompt_sys}

    def __repr__(self):
        return 'ChatGPT'

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf:
            if conf.get("key") and conf.get("api") and conf.get("prompt"):
                return True
        return False

    def get_answer(self, question: str, wxid: str) -> str:
        # wxid或者roomid,个人时为微信id，群消息时为群id
        self.updateMessage(wxid, question, "user")
        rsp = ""
        try:
            # ret = self.client.chat.completions.create(model=self.model,
            #                                           messages=self.conversation_list[wxid],
            #                                           temperature=0.2)
            # rsp = ret.choices[0].message.content
            # rsp = rsp[2:] if rsp.startswith("\n\n") else rsp
            # rsp = rsp.replace("\n\n", "\n")
            rsp = run_conversation(self.client, message=self.conversation_list[wxid])
            self.updateMessage(wxid, rsp, "assistant")
        except AuthenticationError:
            self.LOG.error("OpenAI API 认证失败，请检查 API 密钥是否正确")
        except APIConnectionError:
            self.LOG.error("无法连接到 OpenAI API，请检查网络连接")
        except APIError as e1:
            self.LOG.error(f"OpenAI API 返回了错误：{str(e1)}")
        except Exception as e0:
            self.LOG.error(f"发生未知错误：{str(e0)}")

        return rsp

    def updateMessage(self, wxid: str, question: str, role: str) -> None:
        now_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        time_mk = "当需要回答时间时请直接参考回复:"
        # 初始化聊天记录,组装系统信息
        if wxid not in self.conversation_list.keys():
            question_ = [
                self.system_content_msg,
                {"role": "system", "content": "" + time_mk + now_time}
            ]
            self.conversation_list[wxid] = question_

        # 当前问题
        content_question_ = {"role": role, "content": question}
        self.conversation_list[wxid].append(content_question_)

        for cont in self.conversation_list[wxid]:
            if cont["role"] != "system":
                continue
            if cont["content"].startswith(time_mk):
                cont["content"] = time_mk + now_time

        # 只存储10条记录，超过滚动清除
        i = len(self.conversation_list[wxid])
        if i > 10:
            print("滚动清除微信记录：" + wxid)
            # 删除多余的记录，倒着删，且跳过第一个的系统消息
            del self.conversation_list[wxid][1]

import json
import os
from openai import OpenAI
from db import get_document_by_similar_search, get_records_by_similar_search, get_records_by_time, collection,collection_DN



def get_record_by_time(start, end):
    # collection = init_db()
    return get_records_by_time(collection=collection, start=start, end=end)

def get_record_by_similar_search(user_input):
    return get_records_by_similar_search(collection=collection, user_input=user_input, n_results=10)

def get_information_from_documents(user_input):
    return get_document_by_similar_search(collection=collection_DN, user_input=user_input, n_results=4)

def run_conversation(client, message, model="gpt-4o"):
    messages=[
            {
                "role": "system", 
                "content": prompt_tools
            },
            {
                "role": "user",
                "content": message[-1]["content"],
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
        # messages[0]['content'] = prompt_sys
        message.append(messages[1])
        print(message)
        second_response = client.chat.completions.create(
            model=model,
            messages=message,
        )
        return second_response.choices[0].message.content



if __name__ == "__main__":

    chat = ChatGPT()

    while True:
        q = input(">>> ")
        try:
            time_start = datetime.now()  # 记录开始时间
            print(chat.get_answer(q, "wxid"))
            time_end = datetime.now()  # 记录结束时间

            print(f"{round((time_end - time_start).total_seconds(), 2)}s")  # 计算的时间差为程序的执行时间，单位为秒/s
        except Exception as e:
            print(e)
