#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import signal
from argparse import ArgumentParser

from robot import Robot, __version__
from wcferry import Wcf


async def main(chat_type: int = 3):
    wcf = Wcf(debug=True)
    print("here")
    def handler(sig, frame):
        wcf.cleanup()  # 退出前清理环境
        exit(0)

    signal.signal(signal.SIGINT, handler)

    robot = Robot(wcf)
    robot.LOG.info(f"WeChatRobot【{__version__}】成功启动···")

    # 机器人启动发送测试消息
    robot.sendTextMsg("机器人启动成功！", "filehelper")

    # 接收消息
    # robot.enableRecvMsg()     # 可能会丢消息？
    await robot.enableReceivingMsg()  # 加队列

    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()


if __name__ == "__main__":
    parser = ArgumentParser()
    # parser.add_argument('-c', type=int, default=0, help=f'选择模型参数序号: {ChatType.help_hint()}')
    # args = parser.parse_args().c
    asyncio.run(main())
 
    # root = r"C:\Mine\project\DN-AI\DN_AI\lib\site-packages\wcferry"
    # cmd = fr'"{root}\wcf.exe" start 10086 debug'
    # print(os.path.exists(root))
    # print(cmd)
    # print(os.system(cmd))
    # import subprocess

    # root = r"C:\Mine\project\DN-AI\DN_AI\lib\site-packages\wcferry\wcf.exe"
    # cmd = [root, 'start', '10086', 'debug']
    # result = subprocess.run(cmd, capture_output=True, text=True)

    # print("返回码:", result.returncode)
    # print("标准输出:", result.stdout)
    # print("标准错误:", result.stderr)

