from walnut.utils import ai
from datetime import datetime
from collections import deque
import asyncio
import time

system_prompt = """
你是一位名叫"核桃"的社区成员。你擅长微信个人聊天和群聊场景。
"""

prompt = """
你是名为"核桃"的社区成员。
你的任务是根据用户的聊天信息，进行深度思考，按照以下步骤识别用户意图，回复对应的策略。

**分析步骤：**
1. 理解对话：仔细阅读用户的消息，理解其文字含义、语境和潜在含义。
2. 分析上下文：考虑当前对话的上下文，包括之前的消息、对话主题和参与者。确定核心话题和用户关注点。特别是最近几条消息。
3. 分析意图：推测用户想获得什么（信息、解决方案、情感支持等）。
4. 判断用户意图：基于以上分析，判断用户的意图属于以下哪种情况：
    - 直接回复：用户直接向你提问，简单的日常问候或情感交流你可以直接回答。
    - 查询后回复：除非是非常简单的日常问候或情感交流，否则都应考虑查询知识库。
    - 无需回复：消息与你无关，或是群聊中不需要你参与的对话，或者明确表示不需要你回复。

请仅输出策略名称（查询后回复、直接回复、不需回复）

-example-
示例1：
对话内容：
用户A：大家好啊！
用户B：你好！
用户C：核桃，最近社区有什么新鲜事？

out：
查询后回复

示例2：
对话内容：
用户A：核桃，你知道DN余村最近有什么活动吗？
核桃：让我查询一下最新的社区活动信息。根据我的了解，DN余村下周六将举办一场农产品展销会，主要展示当地的有机蔬菜和手工艺品。
用户A：太好了，谢谢你核桃！

out：
直接回复

示例3：
对话内容：
用户D：@用户E 你今天有空出来聚聚吗？

out：
无需回复

-real data-
##########
对话内容：
{records}
out：

"""
class Zhongshu:
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

        results = await ai.ai_chat_AsyncOpenAI(self.prompt.format(records=records), model)
        time_end = datetime.now()
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
        
        return results
    
    async def check(self, id, user_input, model='gpt-4o-2024-08-06'):

        result = await self.query(id, user_input, model)
        print(result)
        print(self.conversations[id])
        if result == "无需回复":
            return False
        else:
            return True

    def add_conversation(self, id, message):
        if id not in self.conversations:
            self.conversations[id] = deque(maxlen=self.max_queue_size)
        self.conversations[id].append(message)

    def clear_conversation(self, id):
        if id in self.conversations:
            del self.conversations[id]

async def main():
    # 创建 Zhongshu 实例
    zhongshu = Zhongshu()

    # 测试对话 ID
    conversation_id = "test_conversation"

    print("开始测试 query 方法。输入 'quit' 退出测试。")

    while True:
        user_input = input("\n请输入消息: ")
        
        if user_input.lower() == 'quit':
            break

        start_time = time.time()
        
        result = await zhongshu.query(conversation_id, user_input)
        
        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"Query result: {result}")
        print(f"查询耗时: {elapsed_time:.2f} 秒")

    print("测试结束")

if __name__ == "__main__":
    asyncio.run(main())
