

from datetime import datetime
import os
from openai import OpenAI

from memory.ai_db import get_information


client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_API_BASE"),
        )
while 1:
    user_input = input("问点什么：")
    if user_input == "exit":
        break
    # message = prompt_chat(question=user_input)
    # print(message)
    time_start = datetime.now()  

    ai_response = get_information(client, message=user_input)
    print(ai_response)

    time_end = datetime.now() 
    print(f"{round((time_end - time_start).total_seconds(), 2)}s") 