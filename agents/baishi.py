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
请扮演一位社区成员。你叫BOO。
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

辅助信息：
现在是 {time}

out：
格式要求：
- 回复应该像普通的微信消息一样，使用正常文本。

######################
user say now：{user_input}
######################
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
        query_string = "\n".join(user_messages)
        
        info = await memory.query.find_related_entities(query=query_string,vecdb=self.entities_db, graph=self.graph)
        # print(info)
        docs = self.db.query(query_string)
        contents = ''
        for content in docs['documents'][0]:
            contents += content
        # print(docs)
        # print(contents)

        time_end = datetime.now() 
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 

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
