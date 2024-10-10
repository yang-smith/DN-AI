import asyncio
import json
import os
import re
from datetime import datetime
from openai import OpenAI
import tiktoken

def read_chat_records() -> list:
    """从txt中读取聊天记录,返回聊天记录列表"""
    chat_records = []

    with open('chat_records.txt', 'r', encoding='utf-8') as file:
        current_record = None
        for line in file:
            # 匹配时间和发言人
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*)', line)
            if match:
                # 如果有当前记录未保存，先保存当前记录
                if current_record:
                    chat_records.append(current_record)
                timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                timestamp_int = int(timestamp.timestamp())
                speaker = match.group(2)
                current_record = {'timestamp': timestamp_int, 'speaker': speaker, 'message': ''}
            elif current_record:
                # 处理多行消息
                current_record['message'] += line.strip() + '\n'
        # 添加最后一条记录
        if current_record:
            chat_records.append(current_record)

    # 移除每条消息末尾多余的换行符
    for record in chat_records:
        record['message'] = record['message'].strip()

    # 打印解析结果以验证
    for record in chat_records:
        print(record)
    print(len(chat_records))
    return chat_records

import re
from datetime import datetime

def split() -> dict:
    """从txt中读取聊天记录,返回按日期分组的聊天记录字典"""
    chat_records = {}
    
    with open('chat_records.txt', 'r', encoding='utf-8') as file:
        current_record = None
        current_date = None
        for line in file:
            # 匹配时间和发言人
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*)', line)
            if match:
                # 如果有当前记录未保存，先保存当前记录
                if current_record:
                    if current_date not in chat_records:
                        chat_records[current_date] = []
                    chat_records[current_date].append(current_record)
                
                # 解析时间戳，分割日期和时间
                timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                current_date = timestamp.date()  # 日期部分
                timestamp_int = int(timestamp.timestamp())
                speaker = match.group(2)
                current_record = {'timestamp': match.group(1), 'speaker': speaker, 'message': ''}
            elif current_record:
                # 处理多行消息
                current_record['message'] += line.strip() + '\n'
        
        # 添加最后一条记录
        if current_record and current_date:
            if current_date not in chat_records:
                chat_records[current_date] = []
            chat_records[current_date].append(current_record)

    # 移除每条消息末尾多余的换行符
    for date in chat_records:
        for record in chat_records[date]:
            record['message'] = record['message'].strip()

    # 打印解析结果以验证
    for date in chat_records:
        print(date)
        # for record in chat_records[date]:
        #     print(record)
        # print()

    return chat_records


def pre_jielong(records):
    jielongdict = {}
    to_remove = []  
    speakers = {} #将接龙的speaker改为发起接龙者
    for i, record in enumerate(records):
        if record['message'].startswith('#接龙'):
            temp = '\n'.join(record['message'].splitlines()[:-1])
            # print(record)
            if temp not in jielongdict:
                jielongdict[record['message']] = i
                speakers[record['message']] = record['speaker']
                
            else:
                to_remove.append(jielongdict[temp])
                jielongdict[record['message']] = i  

                record['speaker'] = speakers[temp]
                speakers[record['message']] = record['speaker']


    # 对to_remove列表进行排序,从后往前删除元素,避免索引错乱
    to_remove.sort(reverse=True)
    print(to_remove)
    for i in to_remove:
        del records[i]

    return records

def prompt_split(records):
    prompt = f"""
        -Goal-
        我想让你帮我对下面的聊天记录做分割。将相关的聊天记录聚在一块。
        我给你的聊天记录按时间顺序排列，请你尽量从相关性角度聚类分割。
        注意你只做分割，不要改变聊天记录本身。
        使用json格式输出，key是聚类主题，value是对应聊天记录的id
        不要漏掉任何一条聊天记录。每一条聊天记录只能出现一次。
        

        聚类主题请保留较多的信息。将不好判断的聊天记录放在“未知”主题下。
        ######################
        -Real Data-
        Use the following input for your answer.
        聊天记录：
        {records}

        Output:
        """
    return prompt

def prompt_summary(text):
    prompt = """你的任务是将下面的聊天记录转为方便记忆的一段话。
    请尽量保留大部分信息。保留相关的人和时间。
    -Real Data-
    records:
    ```
    {}
    ```
    """
    return prompt.format(text)

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

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


async def main():
    chat_records_by_date = split()
    all_dates = list(chat_records_by_date.keys())
    last_day_records = chat_records_by_date[all_dates[9]]
    print(f"记录日期：{all_dates[9]}")

    # for record in last_day_records:
    #     print(record)
    # print(len(last_day_records))
    pre_records = pre_jielong(last_day_records)


    records = {}
    for i, record in enumerate(pre_records):
        records[i] = record['timestamp'] + ' ' + record['speaker'] + ': ' + record['message']

    prompt = prompt_split(records)
    # print(prompt)
    print(num_tokens_from_string(prompt, "cl100k_base"))
    # result = ai_chat(message=prompt, model="gpt-4o")
    result = ai_chat(message=prompt, model="gpt-4o-mini")
    print(result)
    json_part = re.search(r'({.*?})', result, re.DOTALL)

    import extract
    import knowledge_graph
    import graph_extractor
    import networkx as nx


    if json_part:
        extracted_json = json_part.group(1)
        data_dict = json.loads(extracted_json)
        print("Extracted JSON:")
        print(data_dict)
        result_extracted = {}
        i= 0
        all_records: dict[int, str] = {} # type: ignore
        for key, value in data_dict.items():
            str = ''
            for v in value:
                str = str + '\n' + records[v]
                i += 1
            result_extracted[key] = str
            print('\n#########')
            print(key  + ': \n')
            summary = ai_chat(prompt_summary(str), "gpt-4o-mini")
            print(summary)
            result = ai_chat(extract.prompt_extract(summary),model="gpt-4o-mini")
            print(result)
            all_records[i] = result
            i+=1


        file_path = "./graphtest.graphml"
        if os.path.exists(file_path):
            try:
                graph = nx.read_graphml(file_path)
                print(f"成功读取图形文件：{file_path}")
                results = await graph_extractor.process_results(results=all_records, graph=graph)
            except Exception as e:
                print(f"读取图形文件时发生错误：{e}")
        else:
            print(f"文件 {file_path} 不存在")
            results = await graph_extractor.process_results(all_records)
        
        try:
            extract.visualize_and_save_graph(results, './graphtest.png')
            print("图形已成功可视化并保存")
        except Exception as e:
            print(f"可视化和保存图形时发生错误：{e}")

if __name__ == "__main__":
    asyncio.run(main())