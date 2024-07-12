from datetime import datetime
import requests

def ask_question(query):
    url = "http://localhost:5001/ask"
    response = requests.post(url, json={'query': query})
    return response.json()

if __name__ == '__main__':
    while True:
        user_input = input("问点什么：")
        if user_input.lower() == "exit":
            break
        time_start = datetime.now()
        response = ask_question(user_input)
        time_end = datetime.now()
        print(response)
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
