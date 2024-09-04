

def prompt_split(records):
    prompt = f"""
        -Goal-
        我想让你帮我对下面的聊天记录做分割。将相关的聊天记录聚在一块。
        我给你的聊天记录按时间顺序排列，请你尽量从相关性角度聚类分割。
        注意你只做分割，不要改变聊天记录本身。
        使用json格式输出，key是聚类主题，value是对应聊天记录的id
        不要漏掉任何一条聊天记录。每一条聊天记录只能出现一次。
        

        聚类主题请保留较多的信息。将不好判断的聊天记录放在“未知”主题下。
        ######################
        -Real Data-
        Use the following input for your answer.
        聊天记录：
        {records}

        Output:
        """
    return prompt

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

prompt_records_split = """
        -Background-
        处理和分析动态群聊中的信息，将聊天记录转化为方便记忆的文本段，以便后续的信息检索和内容概览。

        -Goal-
        将聊天记录转化为方便记忆的文本段

        -Constraints-
        保持对话的完整性，避免随意分割具有内在关联的消息。维持对话的连贯性和完整性。
        使用内在相关性作为分割的主要依据。
        以JSON格式输出转化后的文本段。

        -Workflow-
        理解聊天记录：仔细阅读提供的聊天记录，理解对话的上下文和内容。识别对话中的关键主题，如聚餐安排、活动组织等。
        聚类分割：根据时间戳、对话内容的连贯性和参与者的变化，对聊天记录进行逻辑分割。
        聚类相似对话：将有共同主题或者相似时间发生的对话聚集在一起。
        文本转化：将分割后的聊天记录转为方便记忆的一段话。请尽量保留大部分信息。保留相关的人和时间。
        格式化输出：将分割和转化后的文本段以JSON格式输出。
        
        -OutputFormat-
        所有文本段组成一个JSON数组，每个段为一个对象。
        json
        [
            {{
                "1": "文本段"
            }},
            {{
                "2": "文本段"
            }},
            ...
        ]

        -Suggestions-
        逻辑性强化：确保分割逻辑反映对话的自然流程，避免通过过于机械的规则（如仅时间间隔）破坏对话的连贯性。
        细节保留：在摘要中，除了时间和人物，还应尽可能保留对话的主体信息。
        ######################
        -Real Data-
        Use the following input for your answer.
        聊天记录：
        {records}

        Output:
        """

def prompt_split(records):
    prompt = prompt_records_split.format(records = records)
    return prompt