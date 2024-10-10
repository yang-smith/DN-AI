import time
from walnut.utils import ai
from walnut.utils.restaurants import multiple_restaurant_recommendations, read_markdown_file

system_prompt = """
请扮演一位社区成员。你叫“核桃”。
你擅长微信个人聊天和群聊场景的判断。你的任务是准确评估你是否要回话。
"""
prompt = """
你角色是名为“核桃”。请仔细分析以下对话，并判断你是否需要回应最后一句话。

对话内容：
######################
{records}
######################

请只回复以下两种结果之一：
- "继续回答"：如果最后一句话需要你（核桃）回应
- "结束对话"：如果最后一句话不需要你（核桃）回应

在做出判断时，请考虑以下几点：
1. 如果最后一条消息明确提到或询问其他人（不是核桃），则不需要回应。
2. 如果最后一条消息是对核桃之前回复的直接回应，则需要回应。
3. 如果最后一条消息包含"核桃"或直接询问核桃，则需要回应。
4. 如果最后一条消息与核桃之前的回复无关，则不需要回应。


你的判断（仅回复"继续回答"或"结束对话"）：
"""

class Judger:
    def __init__(self, dir_path= './records_db', max_queue_size=10):
        self.system_prompt = system_prompt
        self.prompt = prompt
        self.conversations = {}  # 新增：用于存储对话历史的字典
        self.max_queue_size = max_queue_size  # 新增：设置队列最大长度

    async def query(self, id, user_input, model='gpt-4o-2024-08-06'):
        # 更新对话历史
        if id not in self.conversations:
            self.conversations[id] = deque(maxlen=self.max_queue_size)
        self.conversations[id].append(user_input)

        time_start = datetime.now()  
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 构建对话历史字符串
        records = "\n".join(self.conversations[id])

        messages=[
            {
                "role": "system", 
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": self.prompt.format(records=records),
            }
        ]

        results = ai.ai_long_chat(messages,model)
        time_end = datetime.now()
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
        
        return results
    
    async def check(self, id, user_input, model='gpt-4o-2024-08-06'):

        result = await self.query(id, user_input, model)
        print(result)
        print(self.conversations[id])
        if result == "继续回答":
            return True
        else:
            return False

    def add_conversation(self, id, message):
        if id not in self.conversations:
            self.conversations[id] = deque(maxlen=self.max_queue_size)
        self.conversations[id].append(message)

    def clear_conversation(self, id):
        if id in self.conversations:
            del self.conversations[id]
