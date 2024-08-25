

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