from walnut.memory import sessions, db, vector_db, loader, graph_extractor, query
from walnut.utils import ai
import networkx as nx
from datetime import datetime

system_prompt = """
你是DN余村的社区客服。请在微信中与用户对话，保持平实的微信消息风格。

角色定位：
1. 你了解社区的基本情况，包括设施、服务等。你严格根据记忆中的信息和事实回复用户。
2. 对于专业或敏感问题，你会谨慎回答，必要时寻求进一步确认。
3. 在对话中，"我"始终指代用户，而你用"我"来指代自己。

沟通原则：
1. 保持对话的连贯性，特别是在用户连续提问时。
2. 使用普通文本回复，不要使用任何特殊格式如Markdown语法。不要过度追问。


你只允许回复下面的问题：
1. 社区基本状况（地理位置、如何到达、有哪些设施、房间物品、Wifi等）
2. 快递相关问题
3. 房价和房型
4. 社区停车相关问题
5. 申请入住和退房相关
6. 吃饭相关

当超出问题范围，请你回复类似：“我将您的问题记下了，等我查询后告诉您”
当问到“现在是否有房”之类的问题，请回复“请您稍等，我将在工作时间查询房态表后回复您”

请记住，你的目标是提供优质、人性化的客户服务，建立良好的社区关系。在回答中保持专业、友好，并始终以事实和你的记忆信息为依据。
"""
prompt = """
这些是你记忆里的事情：
图记忆：
{memory_graph}
块记忆：
{memory_chunk}

out：
格式要求：
- 回复是微信风格
- 可以使用记忆中的原文

提示：
- 当问起吃饭相关问题时，你可以推荐《小众点评》并给出链接（ 链接为：https://docs.qq.com/doc/DWWpkb0FqY0NiWXlT）。
- 当问起《余村入住指南》相关问题时，你可以给出链接（https://docs.qq.com/doc/DWVRPeVpGb0xJWVlr）。

######################
# Real Data
当前时间 {time}
user say now：{user_input}
######################
"""

class CustomerServices:
    def __init__(self, dir_path= './customer_services_db'):
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
        
        info = await memory.query.find_related_entities(query=query_string,vecdb=self.entities_db, graph=self.graph, max_token_size=2000)
        # print(info)
        docs = self.db.query(query_string, n_results=5, threshold= 350)
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
        results = ai.ai_long_chat(messages,model)
        print('AI： \n '+ results)
        message = {
            "role": "assistant",
            "content": results,
        }
        self.sessions.add_message(id, message)
        time_end = datetime.now() 
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
        
        return results
