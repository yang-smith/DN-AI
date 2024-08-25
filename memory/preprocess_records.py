import asyncio
import json
import os
import re
from datetime import datetime
from openai import OpenAI
import tiktoken
import re
from datetime import datetime

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
    """将聊天记录中的重复接龙合并，只保留最长接龙"""
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



async def main():
    return
    
if __name__ == "__main__":
    asyncio.run(main())