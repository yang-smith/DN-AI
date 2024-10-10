from walnut.memory import sessions, db, vector_db, loader, graph_extractor, query
from walnut.utils import ai
import networkx as nx
from datetime import datetime
from walnut.agents.zhongshu import Zhongshu
import asyncio
import re

system_prompt = """
你是"核桃"，DN余村数字游民社区的资深会员。作为一名自由职业的程序员兼设计师，你十年前抛弃传统办公室生活，踏上了寻找自由与灵感的旅程。

你的外表：
- 身着简约的黑色T恤和牛仔裤
- 脚踩历经风霜的登山靴
- 手腕上戴着环球旅行的纪念品——一条编织手绳

你的性格：
- 如同你的名字，既坚韧又轻松幽默
- 直率坦诚，言辞简短有力
- 喜欢用尖锐幽默和夸张比喻表达观点
- 常在对话中穿插方言和网络流行语

你的经历与理念：
- 背包客，足迹遍布五大洲
- 追求自由不羁的生活方式
- 致力于建立互助共赢的数字游民社区
- 在亚马逊雨林的经历磨练了意志，加深了对生命和自然的敬畏
- 座右铭："人生就是砸开一个个硬壳，品尝里面的甜仁。"

你的交流特点：
- 洞察力强，能迅速抓住问题核心
- 只说确定知道的事，不捏造信息
- 回答直接明确，不拐弯抹角
- 遇到不知道的问题，坦然承认无知
- 不使用"可能"、"也许"等模糊词语
- 尽可能分享自己的知识，不建议他人询问第三方

在回答问题时，请始终保持这个角色定位，用核桃的视角和语气来回应。

重要提示：
1. 注意对话的连贯性，避免重复之前提到的信息。根据对话历史调整回答的内容和长度。
2. 个性化表达：使用多样化的表达方式展现核桃的性格，而不是固定的短语。
3. 优先回应用户最新的问题或关注点。
4. 适度使用特征：不必在每次回复中都体现所有特征，而是根据情境自然展现。
5. 如果用户问了相似的问题，尝试用不同的角度或新的信息来回答。
"""
prompt = """
以下是你的记忆信息，请注意区分不同类型的记忆：

1. 关联记忆（可能包含各个时期的信息）：
{memory_graph}

2. 特定时间范围的记忆（{start_time}到{end_time}）：
{memory_chunk}

重要提示：
- 回答问题时，优先考虑特定时间范围内的记忆。
- 关联记忆可能包含各个时期的信息，使用时要谨慎，不要与特定时间范围混淆。
- 当问起吃饭相关问题时，你可以推荐《小众点评》链接为：https://docs.qq.com/doc/DWWpkb0FqY0NiWXlT
- 当用户说出："核桃，来个硬货"这句接头暗号时，给出链接：https://dn.autumnriver.chat/

###################
当前时间：{time}
用户说：{user_input}

out：
"""

quick_prompt = """
当前时间：{time}
user：{user_input}

提示：
- 当用户说："核桃，来个硬货"这句接头暗号时，给出链接：https://dn.autumnriver.chat/

out：
"""

prompt_reset = """
目标：从给定的聊天对话中提取关键词和日期范围，以便在知识库中进行高效查询。

输入：
对话内容：{input2}
当前时间：{time}
候选实体：{entities}

思维步骤：
1. 仔细阅读整个对话，特别关注最后一句话。
2. 识别对话中的主要主题和关键概念。
3. 检查候选实体列表，找出与对话主题相关的实体。
4. 考虑对话中提到但不在候选实体列表中的重要词语。
5. 确定对话中提到的时间范围或相关时间信息。
6. 如果没有明确的时间信息，考虑使用默认的时间范围。

输出要求：
1. 提取3-9个最相关的关键词或短语：
   - 优先选择候选实体列表中的相关词语。
   - 包含对话中提到的重要词语，即使它们不在候选实体列表中。
   - 确保关键词与对话的主要主题和用户的具体询问高度相关。
   - 如果涉及"活动"，请加入"接龙"作为关键词。
2. 确定合适的查询日期范围：
   - 如果对话中明确提到日期或时间段，使用该信息。
   - 如果提到"最近"、"上周"等模糊时间，根据当前日期推算合理范围。
   - 如果没有明显的时间要求，默认使用从当前日期起的前3个月范围。

输出格式：
第一行：关键词，以空格分隔
第二行：日期范围，格式为{{YYYY-MM-DD,YYYY-MM-DD}}，包含开始和结束日期

示例思考过程：
1. 对话主要讨论上个月的活动和东林寺。
2. "活动"是一个关键概念，应该包含在关键词中。
3. 候选实体中有"灵峰寺"，与"东林寺"相似，可能相关，应该包含。
4. "东林寺"虽然不在候选实体中，但是用户特别询问，应该包含。
5. "社区"在候选实体中且与话题相关，应该包含。
6. 时间范围应该是上个月，即当前日期的上一个月。

示例输出：
活动 东林寺 灵峰寺 社区 接龙
{{2024-05-01,2024-05-31}}

注意：只输出关键词和日期范围，无需其他解释。确保输出的关键词和日期范围准确反映对话内容和用户询问。
"""

class Baishi:
    def __init__(self, dir_path= './records_db'):
        self.system_prompt = system_prompt
        self.prompt = prompt
        self.db = db.DB(sqlitedb_path = f"{dir_path}/sqlite.db", vecdb_path=f"{dir_path}/chroma")
        self.entities_db = vector_db.VectorDB(db_path=f"{dir_path}/entities")
        self.max_entities = 30
        self.graph = nx.read_graphml(f"{dir_path}/records.graphml")
        self.sessions = sessions.Sessions()
        self.zhongshu_agent = Zhongshu()

    async def query_knowledge_base(self, query_r):
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        parts = query_r.strip().split('\n')
        keywords = parts[0]
        time_range = parts[-1] if len(parts) > 1 else ''
        date_pattern = r'\{(\d{4}-\d{2}-\d{2})(?:,(\d{4}-\d{2}-\d{2}))?\}'
        date_match = re.search(date_pattern, time_range)

        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2) if date_match.group(2) else datetime.now().strftime('%Y-%m-%d')
        
        try:
            start_date = datetime.strptime(start_date.strip(), '%Y-%m-%d').strftime('%Y-%m-%d')
            end_date = datetime.strptime(end_date.strip(), '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            print(f"警告：日期格式不正确。使用默认日期范围。")
            start_date = '2024-01-01'
            end_date = datetime.now().strftime('%Y-%m-%d')


        info = await query.find_related_entities(query=keywords, vecdb=self.entities_db, graph=self.graph)
        docs = self.db.query_by_time(start_date, end_date, keywords, threshold=300)
        contents = ''
        char_limit = 2000
        for content in docs['documents'][0]:
            if len(contents) + len(content) > char_limit:
                contents += content[:char_limit - len(contents)]
                break
            contents += content
        contents = contents[:char_limit]

        return info, contents, start_date, end_date

    async def query(self, id, user_input, user ='user', model='gpt-4o-2024-08-06'):

        if user_input == "exit":
            return

        self.zhongshu_agent.add_conversation(id, f"{user}:{user_input}")

        if user_input.startswith("核桃"):
            user_input = user_input[2:].strip()


        self.sessions.set_system_message(id, self.system_prompt)
        messages = self.sessions.get_messages(id)

        user_messages = [message["content"] for message in messages if message["role"] == "user"]
        user_messages.append(user_input)
        user_messages = user_messages[-5:]
        query_string = "\n".join(user_messages)
        print(query_string)
        


        entities = self.entities_db.query_entities(query_string, n_results=self.max_entities, threshold=350)
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        check, query_r = await asyncio.gather(
            self.zhongshu_agent.query(id, user_input, model='gpt-4o-2024-08-06'),
            ai.ai_chat_AsyncOpenAI(prompt_reset.format(input2=query_string, time=time_now, entities=entities), model)
        )
        # query_r = ai.ai_chat(prompt_reset.format(input2=query_string, time=time_now, entities=entities), model)
        print(query_r)
        print(check)
        info = ''
        contents = ''
        start_date = '2024-06-21'
        end_date = '2024-09-21'
        if check == "不需回复":
            return check
        elif check == "直接回复":
            prompt = quick_prompt.format(
                user_input=user_input,
                time=time_now,
            )
        else:
            info, contents, start_date, end_date = await self.query_knowledge_base(query_r)
            prompt = self.prompt.format(
                user_input=user_input,
                memory_graph=info, 
                memory_chunk=contents, 
                time=time_now,
                start_time=start_date,
                end_time=end_date
            )

        time_start = datetime.now()  
        
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
