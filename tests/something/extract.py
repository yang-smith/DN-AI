


import asyncio
from datetime import datetime
import os
import re
from openai import OpenAI

from knowledge_graph import KnowledgeGraph


text = """
大周_余村: @阿RUI 希望中国数字游民社区也能成为中老年的乌托邦 ，希望中年人能够在青年人迷茫时分享自己的经历和思考，再过几年 ，有行动能力的老年人也能来社区旅居做义工
大周_余村: 这是不是在探索共产主义大团结的实现方式
阿RUI: 指日可待！ 乌托邦没有前缀，就是乌托邦
引用:大周:@阿RUI 希望中国数字游民社区也能成为中老年的乌托邦，希望中年人能够在青年人迷茫时分享自己的经历和思考，再过几年， 有行动能力的老年人也能来社区旅居做义工
大周_余村: 嗯嗯，不过观察下来，年轻人来乌托邦里寻找爱也是一大趋势[呲牙]
引用:未知
Lili: 我代表中老年在这里扎根…
引用:大周:@阿RUI 希望中国数字游民社区也能成为中老年的乌托邦，希望中年人能够在青年人迷茫时分享自己的经历和思考，再过几年， 有行动能力的老年人也能来社区旅居做义工
结巴的Frank: 如果说让老人来养老还有号召力，呼吁让老人在做义工，这。。。我都以为看错了。。。
引用:大周:@阿RUI 希望中国数字游民社区也能成为中老年的乌托邦，希望中年人能够在青年人迷茫时分享自己的经历和思考，再过几年， 有行动能力的老年人也能来社区旅居做义工
"""
text2 = """
K_C_: 云南滇味园米线/烧烤今日开业了啊！等了很久的朋友们可以去啦！
Lili: 之前没开吗？
引用:K.C.（社恐版）:云南滇味园米线/烧烤今日开业了啊！等了很久的朋友们可以去啦！
Lili: 晚上去！
K_C_: 老板前天刚回天荒坪！
引用:未知
"""

text3 = """
如风_余村: 请教一下大家 哪里的公共空间可以吹头发呀
Casey: 吹风机拿到外面随便吹呗
福尔摩瑞_余村: 去a3的人性交流市
木一凡: 可以a3娱乐室
趁早✨_余村: a2卫生间
引用:如风:请教一下大家 哪里的公共空间可以吹头发呀
如风_余村: 谢谢大家 A2有好多人在办公 A3娱乐室确实不错！      
如风_余村: 公共浴室能接个电源+镜子就更好啦！
"""
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

import prompt_entities

def prompt_extract(text):
    prompt = """Your task is to extract named entities from the given paragraph. 
    Respond with a JSON list of entities.(in language of the paragraphs)
    entities包括人名、活动名称、地点和具体产品。请从构建知识图谱角度考量。
    One-Shot Demonstration: 
    Paragraph:
    ```
    在2024年4月9日的聊天记录中，阿银Kuro发起了一个接龙活动，邀请
    大家在19:30到21:30的B1讨论室一起讨论动漫《江户盗贼团五叶》， 强调这部作品的悠闲叙事风格。参与者包括风清和张可茵。

    随后，初YX和STELLALALA接龙分享了他们认为最好吃的抹茶和可可瑞 士卷，价格为6.5元一块，参与者有小初、大猫、晨宸、小虎、阿银和Jay02。

    晚上10点多，📟77KUKU77_余村发起了另一个接龙活动，主题是“以防万一你饿了”，提供脆皮淀粉肠和脆皮年糕，参与者包括风清气 歪、板栗、杨光、紫薇和Casey，大家可以自带杯子享用自助可乐。
    ```
    {{
    "entities": [
    {{"name": "阿银Kuro", "type": "人物"}},
    {{"name": "B1讨论室", "type": "地点"}},
    {{"name": "江户盗贼团五叶", "type": "动漫"}},
    {{"name": "抹茶", "type": "食物", "price": "6.5元一块"}},
    {{"name": "可可瑞士卷", "type": "食物", "price": "6.5元一块"}},
    {{"name": "脆皮淀粉肠", "type": "食物"}},
    {{"name": "脆皮年糕", "type": "食物"}},
    ]
    }}

    -Real Data-
    Paragraph:
    ```
    {}
    ```
    """
    prompt = prompt_entities.UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT
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

import graph_extractor
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import networkx as nx

font_path = 'C:\\Windows\\Fonts\\simhei.ttf'  # 确保路径正确
prop = fm.FontProperties(fname=font_path)

def visualize_and_save_graph(graph: nx.Graph, file_path: str):
    
    pos = nx.spring_layout(graph)  # 为图形的节点设置布局
    nx.draw(graph, pos, with_labels=False, node_color='skyblue', edge_color='#FF5733', node_size=40, font_size=5)
    
    # 使用正确的参数调用
    labels = nx.draw_networkx_labels(graph, pos, font_family=prop.get_name(), font_size=5)
    
    # 保存图形到文件
    plt.savefig(file_path)
    plt.close()
    nx.write_graphml(graph, "./graphtest.graphml")



async def main():
    kg = KnowledgeGraph()

    time_start = datetime.now()  # 记录开始时间
    
    summary =  ai_chat(prompt_summary(text=text2),model="gpt-4o-mini")
    print(summary)
    prompt = prompt_extract(text=summary)
    result =  ai_chat(prompt,model="gpt-4o-mini")
    # result = ai_chat(prompt,model="gpt-4o")
    print(result)

    all_records: dict[int, str] = {}
    all_records[1] = result

    summary =  ai_chat(prompt_summary(text=text),model="gpt-4o-mini")
    print(summary)
    prompt = prompt_extract(text=summary)
    result =  ai_chat(prompt,model="gpt-4o-mini")
    # result = ai_chat(prompt,model="gpt-4o")
    print(result)

    all_records[2] = result
    results = await graph_extractor.process_results(all_records)
    
    print(results)
    # visualize_and_save_graph(results, './graphtest.png')


    time_end = datetime.now()  # 记录结束时间
    print(f"{round((time_end - time_start).total_seconds(), 2)}s")


if __name__ == "__main__":
    asyncio.run(main())