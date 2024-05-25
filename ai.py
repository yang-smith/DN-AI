
import os
from openai import OpenAI

def ai_chat(message, model="gpt-3.5-turbo"):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
        model=model,
    )

    print(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content