# import pandas as pd
# import re

# def process_chained_entries(dataframe, content_column, type_column='类型', type_value='文本'):
#     # Initialize an empty DataFrame to store processed chained entries
#     chained_df = pd.DataFrame(columns=[content_column, 'activity_title', 'participants_count'])
    
#     # Filter entries where the type column is '文本'
#     valid_entries = dataframe[dataframe[type_column] == type_value]
    
#     for idx, row in valid_entries.iterrows():
#         content = row[content_column]
#         # Check if the content starts with '#接龙'
#         if content.startswith('#接龙'):
#             # Extract activity title using regex from '#接龙' to the first occurrence of "1."
#             match = re.search(r'#接龙\s*(.*?)(?=\n1\.)', content, re.DOTALL)
#             if match:
#                 activity_title = match.group(1).strip()
#             else:
#                 # If the regex doesn't find a match, use a fallback method to determine the title
#                 activity_title = content.split('\n')[1] if len(content.split('\n')) > 1 else None

#             if activity_title:
#                 # Extract the content below the title
#                 title_end_position = content.find(activity_title) + len(activity_title)
#                 participants_content = content[title_end_position:].strip()  # Remove any leading or trailing whitespace
#                 # Count the number of participant lines, assuming each participant is on a new line
#                 participants_count = len(participants_content.split('\n'))  # Subtract one for the last usually empty line


#                 # Check if this entry already exists
#                 existing_entry = chained_df[chained_df['activity_title'] == activity_title]
#                 if existing_entry.empty:
#                     # If it doesn't exist, add the new entry
#                     new_entry = pd.DataFrame({
#                         content_column: [content],
#                         'activity_title': [activity_title],
#                         'participants_count': [participants_count]
#                     })
#                     chained_df = pd.concat([chained_df, new_entry], ignore_index=True)
#                 else:
#                     # If it exists and the new content is longer, update the existing entry
#                     if len(content) > len(existing_entry[content_column].values[0]):
#                         index = chained_df[chained_df['activity_title'] == activity_title].index
#                         chained_df.loc[index, content_column] = content
#                         chained_df.loc[index, 'participants_count'] = participants_count

#     return chained_df

# def save_to_excel(dataframe, filename):
#     if not dataframe.empty:
#         # Save to Excel file
#         dataframe.to_excel(filename, index=False)

# # Load the xlsx file
# # file_path = 'DNbase.xlsx' 
# # df = pd.read_excel(file_path, engine='openpyxl')

# # result_df = process_chained_entries(df, '内容')

# # save_to_excel(result_df, 'chained_activities.xlsx')

# # print(result_df)

# file_path = 'chained_activities.xlsx' 
# df = pd.read_excel(file_path, engine='openpyxl')

# if 'activity_title' in df.columns:
#     title_list = df['activity_title'].tolist()
#     # print(title_list)
# else:
#     print('Column "activity_title" does not exist in the dataframe.')

# def split_and_label_list(input_list, group_size=50):
#     # 切分列表，每组group_size个元素
#     grouped_lists = [input_list[i:i + group_size] for i in range(0, len(input_list), group_size)]
    
#     # 给每个元素添加标签
#     labeled_lists = []
#     for index, group in enumerate(grouped_lists):
#         labeled_group = [f"{index * group_size + i + 1}: {item}" for i, item in enumerate(group)]
#         labeled_lists.append(labeled_group)
    
#     return labeled_lists

# labeled_lists = split_and_label_list(title_list)
# # print(labeled_lists[-1])




# import os
# from openai import OpenAI

# def prompt_test(activities):
#     prompt = f"""
#         -Goal-
#         我想让你帮我做活动分类，我将给你一个活动列表，你需要将它们分到指定的类别中。
#         类别包括6种:
#         电影视频
#         约饭聚餐
#         运动
#         学习分享
#         桌游和纸牌
#         其他


#         输出一个字典格式，key是活动类别名称，value是活动在列表中的数值。
#         只输出这个字典。

#         -Examples-
#         Example 1:
#         活动列表：
#         1:今晚20：00大厅放映波兰斯基电影《苦月亮》，想看的来。
#         2: 德州第二季
#         3: 卡坦岛，八点半左右
#         4: 晚饭，贵州小刘家
#         5: 今日夏至，宜吃火锅，中午12：00园区重庆火锅（六折）约饭，如果人太少就蹲蹲晚上
#         6: 飞盘比赛🥏  18:00-20:00

#         Output:
#         {{
#             "电影视频": [1],
#             "约饭聚餐": [4, 5],
#             "运动": [6],
#             "学习分享": [],
#             "桌游和纸牌":[2, 3],
#             "其他": []
#         }}

#         Example 2:
#         活动列表：
#         1: 明日午后三点，图书馆举行科幻小说分享会。
#         2: 明晚七点，社区中心将播放经典电影《教父》。
#         3: 本周六下午一点至三点，公园内有社区瑜伽活动。
#         4: 下周一，科技园区开发者会议，讨论最新的AI技术。
#         5: 本周五晚，麻将比赛，需要提前报名。
#         6: 本月底，地方餐馆组织的美食节，有各种特色小吃。

#         Output:
#         {{
#             "电影视频": [2],
#             "约饭聚餐": [6],
#             "运动": [3],
#             "学习分享": [1, 4],
#             "桌游和纸牌": [5],
#             "其他": []
#         }}
#         ######################
#         -Real Data-
#         Use the following input for your answer.
#         活动列表：
#         {activities}

#         Output:
#         """
#     return prompt


# def prompt_summary(activities):
#     prompt = f"""
#         -Goal-
#         我想让你帮我做一个总结。我将给你一个活动列表。
#         确保每一个活动都提及了。
#         从活动内容角度进行聚类。
#         不用提及时间。
#         我想让这个总结作为这个活动列表的索引。
#         ######################
#         -Real Data-
#         Use the following input for your answer.
#         活动列表：
#         {activities}

#         Output:
#         """
#     return prompt

# def ai_chat(message, model="gpt-3.5-turbo"):
#     client = OpenAI(
#         # This is the default and can be omitted
#         api_key=os.environ.get("OPENAI_API_KEY"),
#         base_url=os.environ.get("OPENAI_API_BASE"),
#     )

#     chat_completion = client.chat.completions.create(
#         messages=[
#             {
#                 "role": "system", 
#                 "content": "You are a helpful assitant."
#             },
#             {
#                 "role": "user",
#                 "content": message,
#             }
#         ],
#         model=model,
#         temperature=0.05
#     )

#     return chat_completion.choices[0].message.content

# import json
# import re

# extracted_dicts = []
# error_list = []
# results = []
# i = 0
# for activity_list in labeled_lists:
#     # prompt = prompt_test(activity_list)
#     prompt = prompt_summary(activity_list)
#     # print(prompt)

#     result = ai_chat(prompt, model="gpt-4o-mini-2024-07-18")
#     print(result)
#     results.append(result)
#     json_part = re.search(r'({.*?})', result, re.DOTALL)

#     if json_part:
#         extracted_json = json_part.group(1)
#         data_dict = json.loads(extracted_json)
#         print("Extracted JSON:")
#         print(data_dict)
#         extracted_dicts.append(data_dict)
#     else:
#         print("No JSON found")
#         error_list.append(activity_list)
#     i+=1
#     if i > 3:
#         break

# # print(results)
# prompt = prompt_summary(results)
# # print(prompt)

# result = ai_chat(prompt, model="gpt-4o-mini-2024-07-18")
# print(result)

# # print(error_list)
# # # 指定要保存的文件路径
# # file_path = 'extracted_data.json'

# # # 将数据写入JSON文件
# # with open(file_path, 'w', encoding='utf-8') as file:
# #     json.dump(extracted_dicts, file, ensure_ascii=False, indent=4)
# # # prompt = prompt_test(labeled_lists[-1])
# # # print(prompt)

# # # result = ai_chat(prompt, model="gpt-4o")
# # # print(result)


# # from collections import defaultdict

# # final_dict = defaultdict(list)

# # # 合并所有字典
# # for d in extracted_dicts:
# #     for key, value in d.items():
# #         final_dict[key].extend(value)

# # # 将defaultdict转换回普通字典
# # final_dict = dict(final_dict)

# # final_file_path = 'final_combined_dict.json'

# # with open(final_file_path, 'w', encoding='utf-8') as file:
# #     json.dump(final_dict, file, ensure_ascii=False, indent=4)

# # print(f"Combined data has been saved to {final_file_path}.")




# # with open('error_list.json', 'w') as file:
# #     json.dump(error_list, file, indent=4)