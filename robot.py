# -*- coding: utf-8 -*-

import asyncio
import logging
import re
import time
import xml.etree.ElementTree as ET
from queue import Empty
from threading import Thread

import schedule
from wcferry import Wcf, WxMsg

import memory
import agents.baishi as baishi
import agents.customer_services as customer_services
import agents.judger as judger
# from job_mgmt import Job

__version__ = "39.0.10.1"


class Robot():
    """个性化自己的机器人
    """

    def __init__(self, wcf: Wcf) -> None:
        self.wcf = wcf
        self.LOG = logging.getLogger("Robot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()
        self.customer_services_agent = customer_services.CustomerServices()
        self.baishi_agent = baishi.Baishi()
        self.judger_agent = judger.Judger()
        self.type = 'baishi'
        self.state = {}

    @staticmethod
    def value_check(args: dict) -> bool:
        if args:
            return all(value is not None for key, value in args.items() if key != 'proxy')
        return False

    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        return self.toChitchat(msg)

    async def toChitchat(self, msg: WxMsg) -> bool:
        """闲聊，接入 ChatGPT
        """
        try:
            q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
            rsp = await self.customer_services_agent.query((msg.roomid if msg.from_group() else msg.sender), q)
        except Exception as e:
            self.LOG.error(f"Error in toChitchat: {e}")
        
        if rsp:
            if msg.from_group():
                self.sendTextMsg(rsp, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(rsp, msg.sender)

            return True
        else:
            self.LOG.error(f"无法从 ChatGPT 获得答案")
            return False

    async def processMsg(self, msg: WxMsg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        此处可进行自定义发送的内容,如通过 msg.content 关键字自动获取当前天气信息，并发送到对应的群组@发送者
        群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
        content = "xx天气信息为："
        receivers = msg.roomid
        self.sendTextMsg(content, receivers, msg.sender)
        """

        # 群聊消息
        if msg.from_group():
            # 如果在群里被 @
            # if msg.roomid not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
            #     return
            if msg.content.startswith('核桃，切换成小客服模式'):
                self.type = 'customer_services'
                self.sendTextMsg('小客服模式已开启', msg.roomid, msg.sender)
                return
            if msg.content.startswith('核桃，切换成核桃模式'):
                self.type = 'baishi'
                self.sendTextMsg('核桃模式已开启', msg.roomid, msg.sender)
                return

            if msg.roomid not in self.state:
                self.state[msg.roomid] = 'waiting'

            if msg.is_at(self.wxid) or msg.content.startswith('核桃') or self.state[msg.roomid] == 'running':
                if self.type == 'baishi':
                    rsp, check = await asyncio.gather(
                        self.baishi_agent.query(msg.roomid, msg.content, model='deepseek-chat'),
                        self.judger_agent.check(msg.roomid, msg.sender+'：'+msg.content, model='deepseek-chat')
                    )
                elif self.type == 'customer_services':
                    rsp, check = await asyncio.gather(
                        self.customer_services_agent.query(msg.roomid, msg.content, model='deepseek-chat'),
                        self.judger_agent.check(msg.roomid, msg.sender+'：'+msg.content, model='deepseek-chat')
                    )
                if msg.content.startswith('核桃'):
                    check = True
                    
                if rsp and check:
                    self.sendTextMsg(rsp, msg.roomid, msg.sender)
                    self.state[msg.roomid] = 'running'
                    self.judger_agent.add_conversation(msg.roomid, '核桃：'+rsp)
                elif not check:
                    self.state[msg.roomid] = 'waiting'
                    self.judger_agent.clear_conversation(msg.roomid)

            return  # 处理完群聊信息，后面就不需要处理了

        # 非群聊信息，按消息类型进行处理
        if msg.type == 37:  # 好友请求
            self.autoAcceptFriendRequest(msg)

        elif msg.type == 10000:  # 系统信息
            self.sayHiToNewFriend(msg)

        elif msg.type == 0x01:  # 文本消息
            # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
            if msg.from_self():
                if msg.content == "^更新$":
                    self.config.reload()
                    self.LOG.info("已更新")
            else:
                if msg.content.startswith("核桃"):
                    rsp = await self.baishi_agent.query(msg.roomid, msg.content)
                    if rsp:
                        self.sendTextMsg(rsp, msg.sender)
                else:
                    await self.toChitchat(msg)

    def onMsg(self, msg: WxMsg) -> int:
        try:
            self.LOG.info(msg)  # 打印信息
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)

        return 0

    def enableRecvMsg(self) -> None:
        self.wcf.enable_recv_msg(self.onMsg)

    async def enableReceivingMsg(self) -> None:
        async def innerProcessMsg(wcf: Wcf):
            while wcf.is_receiving_msg():
                try:
                    msg = wcf.get_msg()
                    self.LOG.info(msg)
                    await self.processMsg(msg)
                except Empty:
                    continue  # Empty message
                except Exception as e:
                    self.LOG.error(f"Receiving message error: {e}")

        self.wcf.enable_receiving_msg()
        task = asyncio.create_task(innerProcessMsg(self.wcf))
        await task

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            if at_list == "notify@all":  # @所有人
                ats = " @所有人"
            else:
                wxids = at_list.split(",")
                for wxid in wxids:
                    # 根据 wxid 查找群昵称
                    ats += f"{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
        if ats == "":
            self.LOG.info(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
        else:
            self.LOG.info(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats}, {msg}", receiver, at_list)

    def getAllContacts(self) -> dict:
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)

    def autoAcceptFriendRequest(self, msg: WxMsg) -> None:
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            scene = int(xml.attrib["scene"])
            self.wcf.accept_new_friend(v3, v4, scene)

        except Exception as e:
            self.LOG.error(f"同意好友出错：{e}")

    def sayHiToNewFriend(self, msg: WxMsg) -> None:
        nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
        if nickName:
            # 添加了好友，更新好友列表
            self.allContacts[msg.sender] = nickName[0]
            self.sendTextMsg(f"Hi {nickName[0]}，我自动通过了你的好友请求。", msg.sender)
    
    def runPendingJobs(self) -> None:
        schedule.run_pending()

