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
                current_record = {'timestamp': timestamp_int, 'speaker': speaker, 'message': ''}
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

chat_records_by_date = split()
last_day = max(chat_records_by_date.keys())  # 获取最新的日期
last_day_records = chat_records_by_date[last_day]  # 获取这一天的记录列表

# 打印最后一天的所有记录
print(f"记录日期：{last_day}")
for record in last_day_records:
    print(record)
print(len(last_day_records))
