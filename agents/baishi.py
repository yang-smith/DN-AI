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
- 回复应该像普通的微信消息一样，使用正常文本。

######################
# Real Data
现在是 {time}
user say now：{user_input}
######################
"""

prompt_reset = """
目标：
从给定的聊天对话中提取关键词，以便在知识库中进行高效查询。

背景：
你是一个智能助手，背后连接着一个广泛的知识库。你的任务是分析对话内容，特别是最后一句话，并提取出最相关、最有价值的查询关键词。

输入：
{input2}

要求：
1. 专注于对话的最后一句话，但也要考虑整体上下文。
2. 提取 3-9 个最相关的关键词或短语。
4. 如果存在专有名词、技术术语或独特概念，请优先考虑。
5. 考虑词语的重要性和相关性，而不仅仅是出现频率。
6. 如果最后一句话是问题，请特别注意问题的核心概念。

输出格式：
直接列出关键词，每个关键词用空格分隔。不需要编号或其他额外文本。

示例输出：
机器学习 深度学习 最好用的 应用

注意：
- 保持简洁，只输出关键词。
- 确保每个关键词都有助于在知识库中找到相关信息。

"""

class Baishi:
    def __init__(self, dir_path= './records_db'):
        self.system_prompt = system_prompt
        self.prompt = prompt
        self.db = memory.db.DB(sqlitedb_path = f"{dir_path}/sqlite.db", vecdb_path=f"{dir_path}/chroma")
        self.entities_db = memory.vector_db.VectorDB(db_path=f"{dir_path}/entities")
        self.graph = nx.read_graphml(f"{dir_path}/records.graphml")
        self.sessions = memory.sessions.Sessions()

    async def query(self, id, user_input, model='gpt-4o-2024-08-06'):

        if user_input == "exit":
            return

        time_start = datetime.now()  

        self.sessions.set_system_message(id, self.system_prompt)
        messages = self.sessions.get_messages(id)

        user_messages = [message["content"] for message in messages if message["role"] == "user"]
        user_messages.append(user_input)
        user_messages = user_messages[-5:]
        query_string = "\n".join(user_messages)
        print(query_string)
        
        query_r = lib.ai.ai_chat(prompt_reset.format(input2=query_string),'gpt-4o-mini')
        print(query_r)
        

        info = await memory.query.find_related_entities(query=query_r,vecdb=self.entities_db, graph=self.graph)
        # print(info)
        docs = self.db.query(query_r,threshold=300)
        contents = ''
        for content in docs['documents'][0]:
            contents += content
        # print(docs)
        # print(contents)

        time_end = datetime.now() 
        print(f"查询耗时：{round((time_end - time_start).total_seconds(), 2)}s") 

        time_start = datetime.now()  
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(time_now)
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
