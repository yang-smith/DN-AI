import memory.sessions
import memory.db
import memory.vector_db
import memory.loader
import memory.graph_extractor
import memory.query
import lib
import networkx as nx
from datetime import datetime

system_prompt = """
请扮演一位社区成员。你叫“核桃”。
你的风格是喜欢打趣，稍微有点暴躁和冒犯。你经常在社区微信群里面活跃。
请注意你是在微信中回复，所以风格是微信消息风格。
你基于事实说话，不会捏造信息。
"""
prompt = """
这些是你记忆里的事情：
图记忆：
{memory_graph}
块记忆：
{memory_chunk}

out：
格式要求：
- 回复是微信风格。
- 如果user在询问信息而你的记忆中没有，谨慎回答，回复类似“我不太清楚”。

######################
# Real Data
当前时间 {time}
user say now：{user_input}
######################
"""

prompt_reset = """
目标：
从给定的聊天对话中提取关键词，以便在知识库中进行高效查询。

背景：
你是一个智能助手，背后连接着一个广泛的知识库。你的任务是分析对话内容，特别是最后一句话，并提取出最相关、最有价值的查询关键词。同时给出查询日期范围。

输入：
对话内容：{input2}
当前时间：{time}
候选实体：{entities}

要求：
1. 专注于对话的最后一句话，但也要考虑整体上下文。
2. 提取 3-9 个最相关的关键词或短语。
3. 如果存在专有名词、技术术语或独特概念，请优先考虑。
4. 考虑词语的重要性和相关性，而不仅仅是出现频率。
5. 如果最后一句话是问题，请特别注意问题的核心概念。
6. 从候选实体中仅选择与当前询问高度相关的实体。
7. 排除明显不相关或可能导致混淆的实体和关键词。
8. 当没有明显时间要求时，日期范围为2024年6到2024年9月。


输出格式：
第一行：关键词，以空格分隔
第二行：日期范围，格式为{{YYYY-MM-DD,YYYY-MM-DD}}，包含开始和结束日期


示例输出：
机器学习 神经网络 模型优化
{{2023-08-01,2024-09-15}}


注意：
- 只输出关键词和日期范围，无需其他文本。
- 确保所有输出的关键词都与询问内容高度相关。
- 如果遇到“活动”加入关键字“接龙”

"""

class Baishi:
    def __init__(self, dir_path= './records_db'):
        self.system_prompt = system_prompt
        self.prompt = prompt
        self.db = memory.db.DB(sqlitedb_path = f"{dir_path}/sqlite.db", vecdb_path=f"{dir_path}/chroma")
        self.entities_db = memory.vector_db.VectorDB(db_path=f"{dir_path}/entities")
        self.max_entities = 30
        self.graph = nx.read_graphml(f"{dir_path}/records.graphml")
        self.sessions = memory.sessions.Sessions()

    async def query(self, id, user_input, model='gpt-4o-2024-08-06'):

        if user_input == "exit":
            return

        if user_input.startswith("核桃"):
            user_input = user_input[2:].strip()

        time_start = datetime.now()  

        self.sessions.set_system_message(id, self.system_prompt)
        messages = self.sessions.get_messages(id)

        user_messages = [message["content"] for message in messages if message["role"] == "user"]
        user_messages.append(user_input)
        user_messages = user_messages[-5:]
        query_string = "\n".join(user_messages)
        print(query_string)
        
        all_entities = self.entities_db.query_entities(query_string, n_results=self.max_entities, threshold=350)
        entities = [entity for entity in all_entities if entity in self.graph]
        print(entities)
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        query_r = lib.ai.ai_chat(prompt_reset.format(input2=query_string, time=time_now, entities=entities),'deepseek-chat')
        print(query_r)
        
        keywords, time_range = query_r.strip().split('\n')
        start_date, end_date = time_range.strip('{}').split(',')
    
        info = await memory.query.find_related_entities(query=keywords,vecdb=self.entities_db, graph=self.graph)
        # print(info)
        # docs = self.db.query(query_r,threshold=300)
        docs = self.db.query_by_time(start_date, end_date, keywords, threshold=300)
        contents = ''
        char_limit = 2000
        for content in docs['documents'][0]:
            if len(contents) + len(content) > char_limit:
                contents += content[:char_limit - len(contents)]
                break
            contents += content
        contents = contents[:char_limit]
        # print(docs)
        # print(contents)

        time_end = datetime.now() 
        print(f"查询耗时：{round((time_end - time_start).total_seconds(), 2)}s") 


        time_start = datetime.now()  
        
        prompt = self.prompt.format(
            user_input=user_input,
            memory_graph=info, 
            memory_chunk=contents, 
            time=time_now
        )
        messages.append({"role": "user",
                "content": prompt,})
        message = {
                "role": "user",
                "content": user_input,
            }
        self.sessions.add_message(id, message)
        print(messages)
        results = lib.ai.ai_long_chat(messages,model)
        print('AI： \n '+ results)
        message = {
            "role": "assistant",
            "content": results,
        }
        self.sessions.add_message(id, message)
        time_end = datetime.now() 
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
        
        return results
