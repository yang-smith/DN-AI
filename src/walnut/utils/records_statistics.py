import os
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba
import jieba.posseg as pseg
from matplotlib.font_manager import FontProperties
import matplotlib.patheffects as PathEffects
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.colors as mcolors  # Add this import
import random

def load_file(file_path):
    _, file_extension = os.path.splitext(file_path)

    if file_extension == '.xlsx':
        df = pd.read_excel(file_path, engine='openpyxl')
    elif file_extension == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file type")

    return df


def base(df):
    # 1. 总聊天条数
    total_chats = len(df)

    # 2. 平均每天聊天数量
    average_daily_chats = df.groupby('日期').size().mean()

    # 3. 总文字数
    total_words = df.loc[df['类型'] == '文本', '内容'].apply(len).sum()

    # 打印统计结果
    print("总聊天条数:", total_chats)
    print("平均每天聊天数量:", average_daily_chats)
    print("总文字数:", total_words)

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


# 4. 词云分析
import random

def ciyun(df):
    df = process_and_clean_chaining_messages(df)
    words = jieba.lcut(''.join(df.loc[df['类型'] == '文本', '内容']))
    filtered_words = [word for word in words if len(word) > 1]  
    stopwords = []
    object_list = []
    with open('./lib/stopwords.txt', 'r', encoding='UTF-8') as meaninglessFile:
        stopwords = set(meaninglessFile.read().split('\n'))
    stopwords.add(' ')
    for word in filtered_words:        
        if word not in stopwords:       
            object_list.append(word)    

    # 生成词云
    all_text = ' '.join(object_list)
    
    # 创建颜色映射
    color_list = ['#FF3F02', '#FEBE03', '#D5BCFF']
    custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom", color_list, N=256)
    
    # 修改颜色函数以返回整数RGB值
    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        return tuple(int(x*255) for x in custom_cmap(random.random())[:3])
    
    wordcloud = WordCloud(font_path='C:\\Windows\\Fonts\\simhei.ttf', 
                          width=800, 
                          height=400, 
                          background_color='white',
                          color_func=color_func).generate(all_text)

    # 显示词云
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()


def save_to_excel(dataframe, filename):
    if not dataframe.empty:
        # Save to Excel file
        dataframe.to_excel(filename, index=False)
        


def week(df):
    # Convert day names to Chinese
    day_name_map = {
        'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三',
        'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六', 'Sunday': '周日'
    }
    df['周天'] = df['时间'].dt.day_name().map(day_name_map)

    # 1. 每周聊天最多的那一天
    # 按周天分组计算总聊天次数
    day_of_week_counts = df.groupby('周天').size()

    # 确保周天顺序正确
    days_order = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    day_of_week_counts = day_of_week_counts.reindex(days_order, fill_value=0)

    # 准备 ECharts 配置
    weekly_chart_option = {
        "xAxis": {
            "type": 'category',
            "data": days_order,
        },
        "yAxis": {
            "type": 'value',
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": 'dashed'
                }
            }
        },
        "series": [
            {
                "data": list(day_of_week_counts.values),
                "type": 'bar',
                "barWidth": '50%', 
                "barCategoryGap": '50%',  
                "itemStyle": {
                    "color": '#FC7900',
                    "borderRadius": [5, 5, 5, 5]
                }
            }
        ]
    }

    # 2. 每天聊天频率最高的时段
    hourly_counts = df.groupby('小时').size()
    max_hour = hourly_counts.idxmax()

    # 准备每小时聊天数据的 ECharts 配置
    hourly_chart_option = {
        "xAxis": {
            "type": 'category',
            "data": list(range(24)),  # 0-23 小时
        },
        "yAxis": {
            "type": 'value',
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": 'dashed'
                }
            }
        },
        "series": [
            {
                "data": list(hourly_counts.reindex(range(24), fill_value=0)),
                "type": 'bar',
                "itemStyle": {
                    "color": '"#D5BCFF",',
                    "borderRadius": [5, 5, 5, 5]
                }
            }
        ]
    }

    return weekly_chart_option, hourly_chart_option, max_hour
    

def parse_chaining_activities(df):
    chaining_activities = {}

    for index, row in df.iterrows():
        if row['类型'] == '文本':
            if "#接龙" in row['内容'] or "#Group Note" in row['内容']:
                lines = row['内容'].split('\n')
                identifier = " ".join(lines[0:3]).strip() 
                current_date = row['时间'].date()
                
                if identifier in chaining_activities:
                    previous_date, participants = chaining_activities[identifier]
                    date_difference = (current_date - previous_date).days
                    if -5 <= date_difference <= 5:
                        participants.add(row['昵称'])
                    else:
                        chaining_activities[identifier] = (current_date, set([row['昵称']]))
                else:
                    chaining_activities[identifier] = (current_date, set([row['昵称']]))

    return chaining_activities

def count_chaining_activities(chaining_activities):
    # 直接计算字典的长度来得到接龙活动的次数
    return len(chaining_activities)

def total_participants(chaining_activities):
    # 计算所有活动的唯一参与者总数
    all_participants = set()
    for date, participants in chaining_activities.values():
        all_participants.update(participants)
    return len(all_participants)

def top_chaining_activities(chaining_activities, top_n=7):
    # 根据参与人数排序接龙活动
    sorted_activities = sorted(chaining_activities.items(), key=lambda x: len(x[1][1]), reverse=True)
    return sorted_activities[:top_n]

def filter_by_year_month(df, year, month):
    """
    过滤数据框架以返回特定年份和月份的数据。
    
    参数:
    df : pandas.DataFrame
        输入的数据框架。
    year : int
        指定的年份，例如2024。
    month : int
        指定的月份，例如1代表一月，12代表十二月。
        
    返回:
    pandas.DataFrame
        包含指定年份和月份数据的数据框架。
    """
    df['时间'] = pd.to_datetime(df['时间'])
    
    return df[(df['时间'].dt.year == year) & (df['时间'].dt.month == month)]


def activites(df):
    chaining_activities = parse_chaining_activities(df)
    chaining_count = count_chaining_activities(chaining_activities)
    total = total_participants(chaining_activities)
    top_activities = top_chaining_activities(chaining_activities, 20)
    # print(chaining_activities)
    print("接龙活动次数:", chaining_count)
    print("总参与人次:", total)
    print("参与人数最多的活动排行前 7:")
    for activity, (date, participants) in top_activities:
        print(f"{activity}, 参与人数: {len(participants)}")
    # 接龙需要做一个二次校正

def main():
    file_path = 'DNbase.xlsx' 
    df = load_file(file_path)

    # 数据预处理
    df['时间'] = pd.to_datetime(df['时间'])  # 转换时间列为datetime类型
    df['日期'] = df['时间'].dt.date
    df['小时'] = df['时间'].dt.hour
    df['周天'] = df['时间'].dt.day_name()

    

    # df = filter_by_year_month(df, 2024, 8)

    base(df)
    weekly_data, hourly_data, max_hour = week(df)
    
    print("\n每周聊天数据:")
    print(weekly_data)
    
    print("\n每小时聊天数据:")
    print(hourly_data)

    ciyun(df)
    activites(df)

if __name__ == "__main__":
    main()