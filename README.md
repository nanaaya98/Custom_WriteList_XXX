# 自定义白名单 插件

--------------------------------------------------

## 插件说明

1. 该是为XXXBot项目中管理机器人在不同群之间开启关闭而设置的管理型插件，您可以在配置文件中根据喜好设置唤醒词、退出词、欢迎词、再见词等内容。
2. 插件优先级默认定为80(priority=80) ，请根据需要自行调整代码中优先级数值；建议菜单、插件管理器高于该插件优先级，其余插件低于该优先级
3. 当前仅管理不同群之间的开启关闭，如需控制私聊仅管理员使用，请根据“其他配置”进行操作
4. XXXBot项目地址：https://github.com/NanSsye/xxxbot-pad

## 插件安装 

1. 将插件文件夹复制到 `plugins` 目录，文件夹名称:Webhook_XXX
2. 编辑 `config.toml` 配置文件
3. 重启 XXXBot 或使用管理命令加载插件

## 配置说明

```toml
[Custom_WriteList_XXX]
Enable = true                           # 是否启用此功能

#机器人配置
Robotname = "麻了"      #机器人昵称，务必设置准确，否则会影响群聊@消息的收发
Wxid = "wxid_27q2wvyh9j1p21"              #机器人Wxid

#个体白名单功能，可以针对某一个群开启，仅限管理员
Whitelist_Enable=true      # 是否启用此功能
Wake_Word="/on"        #唤醒词，根据喜好自行设置，例：原神，启动！
Sleep_Word="/off"      #退出词，根据喜好自行设置
Welcome_Word="服务已启动，欢迎使用！"    #欢迎词，根据喜好自行设置
Goodbye_Word="服务已退出，谢谢使用！"    #再见词，根据喜好自行设置
```

## 其他配置
1. 如需开启私聊仅管理员使用，则自行在代码中增加以下内容

```
####################################处理文本消息####################################
    @on_text_message(priority=80)         #装饰器，指定消息类型和优先级
    async def handle_text(self, bot: WechatAPIClient, message: Dict):   #异步处理文本消息的方法
        if not self.enable:
            return True   
        else:
            if not self.whitelist_enable:
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
```


## 开发者信息

- 作者：喵子柒
- 版本：1.0.0
- 许可证：MIT
