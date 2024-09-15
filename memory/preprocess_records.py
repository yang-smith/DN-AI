import asyncio
import json
import os
import re
import datetime
from openai import OpenAI
import tiktoken
import re
import pandas as pd
import calendar
from datetime import datetime, date, timedelta

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
    chaining_dict = {}

    for index, row in df.iterrows():
        if row['类型'] == '文本':
            content = row['内容']
            if "#接龙" in content or "#Group Note" in content:
                lines = content.split('\n')
                if len(lines) > 1:
                    identifier = lines[0].strip() + " " + lines[1].strip()
                    if identifier not in chaining_dict:
                        # 初始化新的接龙条目
                        chaining_dict[identifier] = {
                            'content': content,
                            'indices': [index],
                            'initiator': row['昵称']
                        }
                    else:
                        # 更新现有接龙条目
                        chaining_dict[identifier]['content'] = content
                        chaining_dict[identifier]['indices'].append(index)

    # 处理接龙信息
    for identifier, info in chaining_dict.items():
        initial_index = info['indices'][0]
        latest_index = info['indices'][-1]
        initial_content = df.loc[initial_index, '内容']
        latest_content = info['content']
        initiator = info['initiator']

        # 合并初始和最新状态的信息
        if initial_index != latest_index:
            merged_content = f"{latest_content}"
            df.loc[latest_index, '内容'] = merged_content
            df.loc[latest_index, '昵称'] = f"{initiator}"

        # 标记要保留的行
        df.loc[latest_index, 'keep'] = True

    # 只保留标记为保留的行和非接龙消息
    df_cleaned = df[df['keep'] == True].drop(columns=['keep'])
    df_cleaned = pd.concat([df_cleaned, df[~df.index.isin(sum([info['indices'] for info in chaining_dict.values()], []))]])

    return df_cleaned.sort_index()

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
    df['日期'] = pd.to_datetime(df['时间'], format='%Y-%m-%d').dt.date
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

from memory.prompt.preprocess import prompt_split, prompt_analyze, prompt_analyze_dig, prompt_analyze_summary
from lib.ai import ai_chat, ai_chat_async
# async def main():
#     file_path = './DNbase.xlsx'
#     df = load_file(file_path)
#     daily_texts = preprocess_chat_data(df)
#     # print(daily_texts.keys())
#     records = daily_texts.get(datetime.date(2024, 7, 16))

#     prompt = prompt_split(records)
#     # print(prompt)
#     result = ai_chat(prompt, 'gpt-4o-mini')
#     print(result)

#     prompt = prompt_analyze_dig(records)
#     # print(prompt)
#     result = ai_chat(prompt, 'gpt-4o-mini')
#     print(result)

#     return
    
async def summarize_month(daily_texts, year, month, output_dir='./summarize_results'):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    start_date = date(year, month, 1)
    end_date = date(year, month, calendar.monthrange(year, month)[1])

    results = []

    for current_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
        if current_date in daily_texts:
            records = daily_texts[current_date]
            prompt = prompt_split(records)
            result = await ai_chat_async(prompt, 'gpt-4o-mini')
            results.append(f"\n\n{result}\n\n")

    # 将结果写入文件
    output_file = os.path.join(output_dir, f"summarize_{year}_{month:02d}.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(results))

    print(f"summarize for {year}-{month:02d} completed. Results saved to {output_file}")


async def analyze_month(daily_texts, year, month, output_dir='./analysis_results'):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    start_date = date(year, month, 1)
    end_date = date(year, month, calendar.monthrange(year, month)[1])

    results = []

    for current_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
        if current_date in daily_texts:
            records = daily_texts[current_date]
            prompt = prompt_analyze_dig(records)
            result = await ai_chat_async(prompt, 'deepseek-chat')
            results.append(f"Date: {current_date}\n\n{result}\n\n{'='*50}\n")
        else:
            results.append(f"Date: {current_date}\n\nNo data available for this date.\n\n{'='*50}\n")

    # 将结果写入文件
    output_file = os.path.join(output_dir, f"analysis_{year}_{month:02d}.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(results))

    print(f"Analysis for {year}-{month:02d} completed. Results saved to {output_file}")

async def merge_monthly_analysis(file_path, output_dir='./analysis_results'):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 将内容分割成每天的分析
    daily_analyses = content.split('='*50)

    # 每5天的分析作为一组进行合并
    chunk_size = 5
    merged_results = []

    for i in range(0, len(daily_analyses), chunk_size):
        chunk = daily_analyses[i:i+chunk_size]
        chunk_content = '\n\n'.join(chunk)

        # 使用AI合并这5天的分析
        prompt = prompt_analyze_summary(chunk_content)
        merged_analysis = await ai_chat_async(prompt, 'gpt-4o-mini')
        merged_results.append(merged_analysis)

    # 最后将所有合并后的结果再次合并
    final_prompt = prompt_analyze_summary('\n\n'.join(merged_results))
    final_analysis = await ai_chat_async(final_prompt, 'gpt-4o-mini')

    # 保存最终结果
    output_file = os.path.join(output_dir, f"merged_analysis_{os.path.basename(file_path)}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_analysis)

    print(f"Merged analysis completed. Results saved to {output_file}")

    return final_analysis

def write_monthly_records_to_file(daily_texts, year, month, output_dir='./monthly_records'):
    os.makedirs(output_dir, exist_ok=True)

    # 获取指定月份的开始日期和结束日期
    start_date = date(year, month, 1)
    end_date = date(year, month, calendar.monthrange(year, month)[1])

    # 准备输出文件
    output_file = os.path.join(output_dir, f"records_{year}_{month:02d}.txt")

    with open(output_file, 'w', encoding='utf-8') as f:
        for current_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
            if current_date in daily_texts:
                f.write(daily_texts[current_date])
    print(f"Monthly records for {year}-{month:02d} have been written to {output_file}")


# 修改 main 函数
async def main():
    file_path = './DNbase.xlsx'
    df = load_file(file_path)
    daily_texts = preprocess_chat_data(df)

    # 指定要分析的年份和月份
    year = 2024
    month = 6
    # records = daily_texts.get(date(2024, 7, 16))

    # prompt = prompt_split(records)
    # # print(prompt)
    # result = ai_chat(prompt, 'gpt-4o-mini')
    # print(result)

    write_monthly_records_to_file(daily_texts, year, month)
    write_monthly_records_to_file(daily_texts, year, 7)
    write_monthly_records_to_file(daily_texts, year, 8)
    write_monthly_records_to_file(daily_texts, year, 9)
    # await summarize_month(daily_texts, year, month)

    # await analyze_month(daily_texts, year, month)
    # # 合并月度分析
    # analysis_file = f'./analysis_results/analysis_{year}_{month:02d}.txt'
    # merged_analysis = await merge_monthly_analysis(analysis_file)
    # print("Final merged analysis:", merged_analysis)

if __name__ == "__main__":
    asyncio.run(main())