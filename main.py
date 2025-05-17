import tomllib                              #用于解析TOML格式的配置文件
import time                                 #用于时间相关操作
import xml.etree.ElementTree as ET          #用于解析XML格式的配置文件
import sqlite3                              #用于操作SQLite数据库
import logging                              #用于记录日志信息
import os                                   #用于操作文件和目录
from WechatAPI import WechatAPIClient       #微信API模块
from utils.decorators import *              #装饰器模块
from utils.plugin_base import PluginBase    #插件必备模块
from typing import Dict, List, Optional, Union, Any  #类型提示模块
from loguru import logger                    #日志记录模块

################Webhook对接插件，用于将系统与外部服务通过Webhook进行集成################
class Custom_WriteList_XXX(PluginBase):                 #定义Webhook类，继承PluginBase类
    name = "Custom_WriteList_XXX"
    description = "管理机器人在特定群聊中的是否启用，可自定义唤醒、退出词。"
    author = "喵子柒"
    version = "1.0.0"

######################################基础配置######################################
    def __init__(self):                    #初始化方法，读取配置文件并设置属性
        super().__init__()
        self.processed_msg_ids = {}
        self.admins = []
        self.wxid = None

        # 读取主配置
        with open("main_config.toml", "rb") as f:
            main_config = tomllib.load(f)
            # 获取管理员列表
            self.admins = main_config.get("XYBot", {}).get("admins", [])
            self.whitelist  = main_config.get("XYBot", {}).get("whitelist ", [])

        # 读取插件配置

        # 获取配置文件路径
        config_path = os.path.join(os.path.dirname(__file__), "config.toml")
        

        with open(config_path, "rb") as f:
            plugin_config = tomllib.load(f)
            config = plugin_config["Custom_WriteList_XXX"]
            self.enable = config.get("enable", False)  # 读取插件开关


            # 使用 get 方法获取配置项
            self.enable = config.get("Enable", False)
            self.robotname = config.get("Robotname", "麻了")
            self.wxid = config.get("Wxid", "")
            self.wake_word = config.get("Wake_Word", "啊打发二次去去啊长期无法承担事故我去问")
            self.sleep_word = config.get("Sleep_Word", "v安慰得过且过v飞奔过去弄i呵呵男女扣篮扣篮")
            self.welcome_word = config.get("Welcome_Word", "服务已启动")
            self.goodbye_word  = config.get("Goodbye_Word", "服务已退出")
            self.one_chat_mode = config.get("One_Chat_Mode", False)


    def clean_processed_msg_ids(self, time_window=3600):
        # 清理超过时间窗口的消息 ID
        current_time = time.time()
        expired_ids = [msg_id for msg_id, timestamp in self.processed_msg_ids.items() if current_time - timestamp > time_window]
        for msg_id in expired_ids:
            del self.processed_msg_ids[msg_id]

    def ensure_table_exists(self, cursor, table_name):
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        table_exists = cursor.fetchone()

        if not table_exists:
            # 数据表不存在，创建数据表
            create_table_query = f'''CREATE TABLE IF NOT EXISTS {table_name} (
                id TEXT UNIQUE,
                mode TEXT CHECK (mode IN ('on', 'off'))
            )'''
            cursor.execute(create_table_query)

####################################处理文本消息####################################
    @on_text_message(priority=80)         #装饰器，指定消息类型和优先级
    async def handle_text(self, bot: WechatAPIClient, message: Dict):   #异步处理文本消息的方法
        if not self.enable:
            return True   
        else:
            msg_id = message["MsgId"]
            content = message["Content"]
            sender_wxid = message["SenderWxid"]
            from_wxid = message["FromWxid"]
            is_group = message["IsGroup"]
            query = content

            if msg_id in self.processed_msg_ids:  # 检查消息 ID 是否已经处理过
                logger.info(f"消息 {msg_id} 已处理，跳过。")
                return False
            # 修改为字典操作，记录消息 ID 和处理时间
            self.processed_msg_ids[msg_id] = time.time()
            if is_group:    # 是否群聊
                is_at = "group-chat"
                # 是否群聊@机器人或私聊
                if f"@{self.robotname}" in query:
                    query = query.replace(f"@{self.robotname}", "").strip()
                    is_at = "group-at"
            else:
                is_at = "one-one-chat"

            msg={ 
                "msg_id": msg_id,
                "sender_wxid": sender_wxid,
                "from_wxid": from_wxid,
                "query": query,
                "is_at": is_at,
                "wxid": self.wxid,
            }
            return await self.handle_db(msg, bot)

####################################处理@消息####################################
    @on_at_message(priority=80)         #装饰器，指定消息类型和优先级
    async def handle_at(self, bot: WechatAPIClient, message: Dict):   #异步处理文本消息的方法
        # 添加日志记录消息详细信息
        if not self.enable:
            return None   
        else:
            msg_id = message["MsgId"]
            content = message["Content"]
            sender_wxid = message["SenderWxid"]
            from_wxid = message["FromWxid"]
            is_group = message["IsGroup"]
            query = content

            if msg_id in self.processed_msg_ids:  # 检查消息 ID 是否已经处理过
                logger.info(f"消息 {msg_id} 已处理，跳过。")
                return False
            # 修改为字典操作，记录消息 ID 和处理时间
            self.processed_msg_ids[msg_id] = time.time()
            if is_group:    # 是否群聊
                is_at = "group-at"
            else:
                is_at = "one-one-chat"
            msg={
                "msg_id": msg_id,
                "sender_wxid": sender_wxid,
                "from_wxid": from_wxid,
                "query": query,
                "is_at": is_at,
                "wxid": self.wxid,
            }
            return await self.handle_db(msg, bot)

####################################数据库操作####################################
    async def handle_db(self, msg, bot: WechatAPIClient):
        # 获取数据库文件路径
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Custom_WriteList.db')
        if msg["is_at"] == "one-one-chat":
            if msg["from_wxid"] in self.admins:
                return True
            else:
                if not self.one_chat_mode:
                        if msg["from_wxid"] not in self.whitelist:
                            return False
                        else:
                            return True
                else:
                        return True 
        try:
            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            table_name = self.wxid  # 使用机器人的 wxid 作为表名
            if table_name:
                self.ensure_table_exists(cursor, table_name)

                # 对照数据库 id 索引
                from_wxid = msg["from_wxid"]  
                cursor.execute(f"SELECT mode FROM {table_name} WHERE id = ?", (from_wxid,))
                result = cursor.fetchone()

                # 初始化mode变量，默认为'off'，如果查询结果为空则保持不变，否则更新为查询结果中的mode值
                mode = 'off'
                if result:
                    # 匹配到相同的 id，提取 mode 值
                    mode = result[0]
                else:
                    # 没有匹配到，创建新数据
                    cursor.execute(f"INSERT INTO {table_name} (id, mode) VALUES (?, 'off')", (from_wxid,))
                conn.commit()

                # 处理消息，对应不同的 mode 值，执行不同的操作
                if msg["sender_wxid"] in self.admins:
                    if msg["query"] == self.wake_word:
                        cursor.execute(f"UPDATE {table_name} SET mode = 'on' WHERE id = ?", (from_wxid,))
                        conn.commit()
                        mode = 'on'
                        await bot.send_text_message(msg["from_wxid"], self.welcome_word)
                        return False
                    elif msg["query"] == self.sleep_word:
                        cursor.execute(f"UPDATE {table_name} SET mode = 'off' WHERE id = ?", (from_wxid,))
                        conn.commit()
                        mode = 'off'
                        await bot.send_text_message(msg["from_wxid"], self.goodbye_word)
                        return False
                

        except sqlite3.Error as e:
            logger.error(f"数据库操作出错: {e}")
        finally:
            # 关闭数据库连接
            if 'conn' in locals():
                conn.close()

        if mode == 'on':
            return True
        else:
            return False

