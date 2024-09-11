import logging
import queue
from memory.prompt.prompt import system_prompt_memory
logging.basicConfig(filename='sessions.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Sessions:
    def __init__(self, maxsize=20) -> None:
        self.sessions = {}
        self.maxsize = maxsize  
        logging.info("Initialized Sessions with maxsize {}".format(maxsize))

    def add_message(self, id, message):
        if id not in self.sessions:
            self.sessions[id] = {
                "system_message": {"role": "system", "content": system_prompt_memory},
                "user_messages": queue.Queue(maxsize=self.maxsize)
            }
            logging.info("Created new session for ID {}".format(id))
        
        if message['role'] == 'system':
            self.sessions[id]["system_message"] = message
        else:
            user_messages_queue = self.sessions[id]["user_messages"]
            if user_messages_queue.full():
                oldest_message = user_messages_queue.get()
                logging.warning("Removed oldest user message: {}".format(oldest_message['content']))
                user_messages_queue.task_done()
            user_messages_queue.put(message)
            logging.debug("Added user message: {}".format(message['content']))

    def get_messages(self, id):
        combined_messages = []
        if id in self.sessions:
            session = self.sessions[id]
            if session["system_message"]:
                combined_messages.append(session["system_message"])
            combined_messages.extend(list(session["user_messages"].queue))
        else:
            self.sessions[id] = {
                "system_message": {"role": "system", "content": system_prompt_memory},
                "user_messages": queue.Queue(maxsize=self.maxsize)
            }
            logging.info("Created new session for ID {}".format(id))
            session = self.sessions[id]
            combined_messages.append(session["system_message"])
        
        return combined_messages

    def set_system_message(self, id, system_message):
        if id not in self.sessions:
            self.sessions[id] = {
                "system_message": {"role": "system", "content": system_message},
                "user_messages": queue.Queue(maxsize=self.maxsize)
            }
            logging.info("Created new session for ID {}".format(id))
        else:
            self.sessions[id]["system_message"] = {"role": "system", "content": system_message}
        logging.info("Set system message for ID {}: {}".format(id, system_message))

if __name__ == "__main__":
    # 使用示例
    sessions = Sessions(maxsize=3)

    # 添加消息
    messages = [
        {"role": "system", "content": "Youa helpful assistant."},
        {"role": "user", "content": "How can I manage an increasing queue?"}
    ]

    # 假设每条消息使用相同的id
    session_id = "session1"
    for message in messages:
        sessions.add_message(session_id, message)

    # 再添加额外的消息以测试队列限制
    sessions.add_message(session_id, {"role": "user", "content": "Message 3"})
    sessions.add_message(session_id, {"role": "user", "content": "Message 4"})  
    sessions.add_message(session_id, {"role": "user", "content": "Message 5"}) 
    # 获取并打印指定id的所有消息
    messages_for_id = sessions.get_messages(session_id)

    print(messages_for_id)