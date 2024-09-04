import asyncio
import json
import os
import re
import datetime
from openai import OpenAI
import tiktoken
import re
import pandas as pd

def load_file(file_path):
    _, file_extension = os.path.splitext(file_path)

    if file_extension == '.xlsx':
        df = pd.read_excel(file_path, engine='openpyxl')
    elif file_extension == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file type")

    return df

def process_and_clean_chaining_messages(df):
    # 接龙数据存储
    chaining_dict = {}
    # 存储要删除的行索引
    rows_to_delete = []

    for index, row in df.iterrows():
        if row['类型'] == '文本':
            content = row['内容']
            # 检查是否为接龙消息
            if "#接龙" in content or "#Group Note" in content:
                lines = content.split('\n')
                if len(lines) > 1:
                    identifier = lines[0].strip() + " " + lines[1].strip()
                    # 如果已存在此接龙活动，则将先前存储的行索引加入删除列表
                    if identifier in chaining_dict:
                        rows_to_delete.append(chaining_dict[identifier]['index'])
                    # 更新字典中的接龙信息
                    chaining_dict[identifier] = {'content': content, 'index': index}

    # 使用收集到的行索引列表删除行
    df_cleaned = df.drop(rows_to_delete)

    # 返回清理后的 DataFrame 和接龙的最新状态
    return df_cleaned

def split_by_day(df):
    df['内容'] = df['内容'].str.replace('\n', ' ')  # 移除换行符
    df['内容'] = df['内容'].str.strip()  # 去除前后空白

    grouped = df.groupby('日期')
    
    # 生成每天的聊天记录字符串
    daily_texts = {}
    for date, group in grouped:
        messages = []
        for _, row in group.iterrows():
            if row['类型'] == '文本' or row['类型'] == '引用消息':
                message = f"[{row['时间']}] {row['昵称']}：{row['内容']}"
                messages.append(message)
        daily_texts[date] = '\n\n'.join(messages)
    
    return daily_texts

def preprocess_chat_data(df):

    df['时间'] = pd.to_datetime(df['时间'], format='%Y-%m-%d %H:%M:%S')
    df['日期'] = df['时间'].dt.date
    df['小时'] = df['时间'].dt.hour
    df['周天'] = df['时间'].dt.day_name()
    
    # 合并接龙
    df = process_and_clean_chaining_messages(df)

    # 处理引用消息，提取引用内容
    def extract_referenced_content(content):
        if type(content) == str: 
            if '【引用消息】' in content:
                parts = content.split('\n')
                return ' '.join(parts[1:2])  # 提取除“【引用消息】”之外的部分
        return content
    
    df['内容'] = df['内容'].apply(extract_referenced_content)
    
    daily_texts = split_by_day(df)

    return daily_texts

from memory.prompt.preprocess import prompt_split
from lib.ai import ai_chat
async def main():
    file_path = './DNbase.xlsx'
    df = load_file(file_path)
    daily_texts = preprocess_chat_data(df)
    # print(daily_texts.keys())
    records = daily_texts.get(datetime.date(2024, 7, 16))

    prompt = prompt_split(records)
    print(prompt)
    result = ai_chat(prompt, 'gpt-4o-mini')
    print(result)

    return
    
if __name__ == "__main__":
    asyncio.run(main())