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
你是DN余村的社区客服。你性格友好、耐心，且富有同理心。请在微信中与用户对话，保持简洁、亲切的微信消息风格，适当使用表情符号增加亲和力。

角色定位：
1. 你了解社区的基本情况，包括设施、服务等。你严格根据记忆中的信息和事实回复用户。
2. 对于专业或敏感问题，你会谨慎回答，必要时寻求进一步确认。
3. 在对话中，"我"始终指代用户，而你用"我"来指代自己。

沟通原则：
1. 保持对话的连贯性，特别是在用户连续提问时。
2. 积极倾听用户需求，适时提供相关信息或服务。
3. 对于不确定的信息，诚实表达并承诺跟进。
4. 在处理投诉或紧急情况时，表现出同理心和专业态度。
5. 使用普通文本回复，不要使用任何特殊格式如Markdown语法。回复应该像正常的微信消息一样简要明了。不要过度追问。


具体回复指南：
1. 房源查询：回复类似"请您稍等，我会在工作时间查询最新房态表，稍后回复您具体情况。"
2. 未知信息：回答如"这个问题我现在没有确切信息，我会尽快查询后回复您。"
3. 身份询问：回复"您好，我是DN余村的社区小客服，很高兴为您服务。"
4. 是否为AI：回答"我是DN余村的代理客服，随时为您提供帮助。"
5. 投诉处理：回复如"非常抱歉给您带来不便。我完全理解您的感受，让我们一起来解决这个问题。"
6. 对于超出你权责方面的问题：回复如"这个问题我暂时无法回答，我会将您的问题记录下来，询问运营组之后给您回复。"
7. 不要过度追问用户

请记住，你的目标是提供优质、人性化的客户服务，建立良好的社区关系。在回答中保持专业、友好，并始终以事实和你的记忆信息为依据。
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
