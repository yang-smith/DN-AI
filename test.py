import agents.baishi as baishi
import agents.customer_services as customer_services
import agents.judger as judger
import asyncio

class MockMessage:
    def __init__(self, roomid, content, sender):
        self.roomid = roomid
        self.content = content
        self.sender = sender

    def is_at(self, wxid):
        return "@" + wxid in self.content

class MockRobot:
    def __init__(self):
        self.baishi_agent = baishi.Baishi()
        self.judger_agent = judger.Judger()
        self.state = {}
        self.wxid = "robot"

    async def process_message(self, msg):
        if msg.roomid not in self.state:
            self.state[msg.roomid] = 'waiting'


        if msg.is_at(self.wxid) or msg.content.startswith('核桃') or self.state[msg.roomid] == 'running':
            rsp, check = await asyncio.gather(
                self.baishi_agent.query(msg.roomid, msg.content, model='deepseek-chat'),
                self.judger_agent.check(msg.roomid, msg.sender+'：'+msg.content, model='deepseek-chat')
            )

            if rsp and check:
                print(f"发送消息: {rsp}")
                self.state[msg.roomid] = 'running'
                self.judger_agent.add_conversation(msg.roomid, '核桃：'+rsp)
            elif not check:
                self.state[msg.roomid] = 'waiting'

async def main():
    robot = MockRobot()
    while True:
        user_input = input("请输入消息 (格式: roomid content): ")
        if user_input.lower() == "exit":
            break
        try:
            roomid, content = user_input.split(" ", 1)
            msg = MockMessage(roomid, content, "user")
            await robot.process_message(msg)
        except ValueError:
            print("输入格式错误，请使用 'roomid content' 格式")

if __name__ == "__main__":
    asyncio.run(main())
