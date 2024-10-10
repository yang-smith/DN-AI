import time
from walnut.utils import ai
from walnut.utils.restaurants import multiple_restaurant_recommendations, read_markdown_file

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
以下今日随机推荐餐厅列表：
{restaurants}

请根据当前时间（{time}），从上述列表中推荐一家最合适的餐厅。

输出规范：
餐厅：[餐厅名称]
说明：[简要说明为什么这家餐厅合适，100字以内]

请用简洁幽默的语气回答，展现"核桃"的个性。

out：
"""

class RandomRestaurant:
    def __init__(self):
        self.system_prompt = system_prompt
        self.prompt = prompt
        file_path = 'docs/documents/eat.md'
        self.markdown_content = read_markdown_file(file_path)

    def query(self, id, user_input, model='gpt-4o-2024-08-06'):

        restaurants = multiple_restaurant_recommendations(self.markdown_content, 3)

        messages=[
            {
                "role": "system", 
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": self.prompt.format(restaurants=restaurants, time = time.strftime("%Y-%m-%d %H:%M")),
            }
        ]
        results = ai.ai_long_chat(messages,model)   
        return results

if __name__ == "__main__":
    random_restaurant = RandomRestaurant()
    conversation_id = "test_conversation"

    print("开始测试 query 方法。输入 'quit' 退出测试。")

    while True:
        user_input = input("\n请输入消息: ")
        
        if user_input.lower() == 'quit':
            break

        start_time = time.time()
        
        result = random_restaurant.query(conversation_id, user_input)
        
        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"Query result: {result}")
        print(f"查询耗时: {elapsed_time:.2f} 秒")
