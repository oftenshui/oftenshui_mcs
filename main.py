import random
import asyncio
import os
import re
import json
import datetime
import aiohttp
import urllib.parse
import logging
from typing import Dict, List, Optional, Any
from PIL import Image as PILImage
from PIL import ImageDraw as PILImageDraw
from PIL import ImageFont as PILImageFont
from astrbot.api.all import AstrMessageEvent, CommandResult, Context, Image, Plain
import astrbot.api.event.filter as filter
from astrbot.api.star import register, Star

logger = logging.getLogger("astrbot")

@register("astrbot_plugin_essential", "Soulter", "", "", "")
class Main(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.PLUGIN_NAME = "astrbot_plugin_essential"
        PLUGIN_NAME = self.PLUGIN_NAME
        path = os.path.abspath(os.path.dirname(__file__))
        self.mc_html_tmpl = open(
            path + "/templates/mc.html", "r", encoding="utf-8"
        ).read()
        self.what_to_eat_data: list = json.loads(
            open(path + "/resources/food.json", "r", encoding="utf-8").read()
        )["data"]

        if not os.path.exists(f"data/{PLUGIN_NAME}_data.json"):
            with open(f"data/{PLUGIN_NAME}_data.json", "w", encoding="utf-8") as f:
                f.write(json.dumps({}, ensure_ascii=False, indent=2))
        with open(f"data/{PLUGIN_NAME}_data.json", "r", encoding="utf-8") as f:
            self.data = json.loads(f.read())
        self.good_morning_data = self.data.get("good_morning", {})

    @filter.command("喜报")
    async def congrats(self, message: AstrMessageEvent):
        """喜报生成器"""
        msg = message.message_str.replace("喜报", "").strip()
        for i in range(20, len(msg), 20):
            msg = msg[:i] + "\n" + msg[i:]

        path = os.path.abspath(os.path.dirname(__file__))
        bg = path + "/congrats.jpg"
        img = PILImage.open(bg)
        draw = PILImageDraw.Draw(img)
        font = PILImageFont.truetype(path + "/simhei.ttf", 65)

        # Calculate the width and height of the text
        text_width, text_height = draw.textbbox((0, 0), msg, font=font)[2:4]

        # Calculate the starting position of the text to center it.
        x = (img.size[0] - text_width) / 2
        y = (img.size[1] - text_height) / 2

        draw.text(
            (x, y),
            msg,
            font=font,
            fill=(255, 0, 0),
            stroke_width=3,
            stroke_fill=(255, 255, 0),
        )

        img.save("congrats_result.jpg")
        return CommandResult().file_image("congrats_result.jpg")

    @filter.command("悲报")
    async def uncongrats(self, message: AstrMessageEvent):
        """悲报生成器"""
        msg = message.message_str.replace("悲报", "").strip()
        for i in range(20, len(msg), 20):
            msg = msg[:i] + "\n" + msg[i:]

        path = os.path.abspath(os.path.dirname(__file__))
        bg = path + "/uncongrats.jpg"
        img = PILImage.open(bg)
        draw = PILImageDraw.Draw(img)
        font = PILImageFont.truetype(path + "/simhei.ttf", 65)

        # Calculate the width and height of the text
        text_width, text_height = draw.textbbox((0, 0), msg, font=font)[2:4]

        # Calculate the starting position of the text to center it.
        x = (img.size[0] - text_width) / 2
        y = (img.size[1] - text_height) / 2

        draw.text(
            (x, y),
            msg,
            font=font,
            fill=(0, 0, 0),
            stroke_width=3,
            stroke_fill=(255, 255, 255),
        )

        img.save("uncongrats_result.jpg")
        return CommandResult().file_image("uncongrats_result.jpg")

    @filter.command("mc")
    async def mcs(self, message: AstrMessageEvent):
        """查mc服务器"""
        message_str = message.message_str
        if message_str == "mc":
            return CommandResult().error("查 Minecraft 服务器。格式: /mc [服务器地址]")
        ip = message_str.strip()
        if ip.startswith("mc"):
            ip = ip[2:].strip()

        url = f"http://地址/mc/?server={ip}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return CommandResult().error("请求失败")
                data = await resp.json()
                logger.info(f"获取到 {ip} 的服务器信息。")

        # result = await context.image_renderer.render_custom_template(self.mc_html_tmpl, data, return_url=True)
        motd = "查询失败"
        if (
                "motd" in data
                and isinstance(data["motd"], dict)
                and isinstance(data["motd"].get("clean"), list)
                and isinstance(data["motd"].get("motd"), list)
        ):
            motd_lines = [
                i.strip()
                for i in data["motd"]["clean"]
                if isinstance(i, str) and i.strip()
            ]
            motd = "\n".join(motd_lines) if motd_lines else "查询失败"
        if motd == "查询失败" and isinstance(data.get("motd"), str):
            motd = data["motd"].strip() if data["motd"].strip() else "查询失败"
        players = "查询失败"
        version = "查询失败"
        if "error" in data:
            return CommandResult().error(f"查询失败: {data['error']}")

        name_list = []

        if "players" in data:
            players = f"{data['players']['online']}/{data['players']['max']}"

            if "sample" in data["players"]:
                name_list = data["players"]["sample"]
            elif "list" in data["players"]:
                name_list = data["players"]["list"]

        if "version" in data:
            version = str(data["version"])

        status = "🟢在线" if data["online"] else "🔴离线"

        name_list_str = ""
        if name_list:
            name_list_str = " | ".join(name_list)
        if not name_list_str:
            name_list_str = "查询失败"

        ping_value = data.get("ping")
        if ping_value:
            ping_display = f"{ping_value}ms"
        else:
            ping_display = "查询失败"

        result_text = (
            "-----【查询结果】-----\n"
            f"当前状态: {status}\n"
            f"当前延迟: {ping_display}\n"
            f"网际协议: {ip}\n"
            f"当时版本: {version}\n"
            f"玩家人数: {players}\n"
            f"在线玩家: {name_list_str}\n"
            f"描述信息: {motd}\n"
        )
        return CommandResult().message(result_text).use_t2i(False)

    @filter.command("一言")
    async def hitokoto(self, message: AstrMessageEvent):
        """来一条一言"""
        url = "https://v1.hitokoto.cn"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status != 200:
                        return CommandResult().error("请求失败")
                    data = await resp.json()
                    return CommandResult().message(data["hitokoto"] + " —— " + data["from"])
        except Exception as e:
            return CommandResult().error(f"获取一言出错: {str(e)}")

    @filter.command("60s")
    async def today_news(self, message: AstrMessageEvent):
        """60秒看世界"""
        API_URL = "https://60s.viki.moe/v2/60s?encoding=image"

        async def verify_image(session):
            """验证接口是否返回图片"""
            try:
                async with session.get(API_URL) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if isinstance(content_type, bytes):
                            content_type = content_type.decode('utf-8')
                        return content_type.startswith('image/')
                    return False
            except aiohttp.ClientError as e:
                logger.warning(f"验证图片接口失败: {str(e)}")
                return False

        try:
            async with aiohttp.ClientSession() as session:
                if not await verify_image(session):
                    yield message.plain_result("⚠️新闻服务暂时不可用，请稍后再试")
                    return

                yield CommandResult(chain=[Image.fromURL(API_URL)])
        except Exception as e:
            logger.error(f"获取今日新闻时出错: {str(e)}", exc_info=True)
            yield message.plain_result("❌获取新闻时发生错误，请稍后再试")

    @filter.command("moe")
    async def get_moe_image(self, message: AstrMessageEvent):
        """随机动漫图片"""
        API_URL = "http://地址/tu/moe"

        async def verify_image(session):
            """验证接口是否返回图片"""
            try:
                async with session.get(API_URL) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if isinstance(content_type, bytes):
                            content_type = content_type.decode('utf-8')
                        return content_type.startswith('image/')
                    return False
            except aiohttp.ClientError as e:
                logger.warning(f"验证图片接口失败: {str(e)}")
                return False

        try:
            async with aiohttp.ClientSession() as session:
                if not await verify_image(session):
                    yield message.plain_result("⚠️MOE服务暂时不可用，请稍后再试")
                    return

                yield CommandResult(chain=[Image.fromURL(API_URL)])
        except Exception as e:
            logger.error(f"获取MOE图片时出错: {str(e)}", exc_info=True)
            yield message.plain_result("❌获取动漫图片时发生错误，请稍后再试")

    @filter.command("帮助")
    async def help_command(self, message: AstrMessageEvent):
        """获取机器人使用说明"""
        url = "http://地址/help.html"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status != 200:
                        return CommandResult().error("请求帮助页面失败")

                    # 获取原始HTML内容
                    html_content = await resp.text()

                    # 提取"help："之后的内容
                    if "help：" in html_content:
                        help_text = html_content.split("help：")[1].strip()
                        return CommandResult().message(help_text)
                    else:
                        return CommandResult().error("帮助内容格式不正确")

        except Exception as e:
            return CommandResult().error(f"获取帮助出错: {str(e)}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("mcs")
    async def mcs_control(self, message: AstrMessageEvent):
        """
        管理MC实例
        1. 查询列表: /mcs 列表
        2. 管理实例: /mcs [实例名称] [启动/停止/重启]
        3. 发送指令: /mcs [实例名称] [op xxx / say xxx]
        """
        # 配置信息
        API_BASE = "http://地址:2354"
        API_KEY = "63415204421d4d1699109500e5014834"
        DAEMON_ID = "156232f2288745689e22713056ad958e"

        # 解析指令，去掉 mcs 前缀
        msg = message.message_str.replace("mcs", "").strip()
        args = msg.split()

        # 如果没有参数，或者参数不对
        if not args:
            return CommandResult().error("请输入指令。\n列表：/mcs 列表\n操作：/mcs 跳转服 启动")

        try:
            async with aiohttp.ClientSession() as session:

                # ---------------------------------------------------------
                # 功能 1: 获取实例列表 (/mcs 列表)
                # ---------------------------------------------------------
                if len(args) == 1 and args[0] in ["列表", "list"]:
                    list_url = f"{API_BASE}/api/service/remote_service_instances"
                    list_params = {
                        "apikey": API_KEY,
                        "daemonId": DAEMON_ID,
                        "page": "1",
                        "page_size": "100",
                        "instance_name": "",
                        "status": ""
                    }

                    async with session.get(list_url, params=list_params) as resp:
                        if resp.status != 200:
                            return CommandResult().error(f"获取列表失败，状态码: {resp.status}")

                        data = await resp.json()

                        # 解析 JSON 提取 nickname
                        # 路径: data -> data -> list -> config -> nickname
                        instance_names = []
                        if (data.get("status") == 200 and
                                "data" in data and
                                "data" in data["data"]):

                            for item in data["data"]["data"]:
                                # 提取昵称，如果获取不到则显示未知
                                name = item.get("config", {}).get("nickname", "未知实例")
                                # 提取状态 (可选优化: status 0=停止, 2=运行中, 只是猜测，可根据实际情况调整)
                                # status = item.get("status")
                                instance_names.append(f"• {name}")

                    if not instance_names:
                        return CommandResult().message("当前没有任何实例。")

                    result_msg = "【当前实例列表】\n" + "\n".join(instance_names)
                    return CommandResult().message(result_msg)

                # ---------------------------------------------------------
                # 功能 2: 实例控制与指令 (/mcs 跳转服 op xxx)
                # ---------------------------------------------------------

                if len(args) < 2:
                    return CommandResult().error("格式错误。\n操作示例：/mcs 跳转服 启动\n指令示例：/mcs 跳转服 op player")

                instance_name = args[0]
                action_raw = " ".join(args[1:]) # 获取剩余所有内容作为指令

                # 定义电源管理操作映射
                power_action_map = {
                    "启动": "open", "start": "open", "open": "open", "开启": "open",
                    "停止": "stop", "stop": "stop", "关闭": "stop",
                    "重启": "restart", "restart": "restart",
                    "终止": "kill", "kill": "kill", "强停": "kill"
                }

                # --- 步骤 A: 搜索实例获取 UUID ---
                search_url = f"{API_BASE}/api/service/remote_service_instances"
                search_params = {
                    "apikey": API_KEY,
                    "daemonId": DAEMON_ID,
                    "page": "1",
                    "page_size": "100",
                    "instance_name": instance_name, # 这里利用API的搜索功能
                    "status": ""
                }

                async with session.get(search_url, params=search_params) as resp:
                    if resp.status != 200:
                        return CommandResult().error(f"查询实例失败，状态码: {resp.status}")

                    search_data = await resp.json()
                    instance_uuid = None
                    target_full_name = ""

                    if (search_data.get("status") == 200 and
                            "data" in search_data and
                            "data" in search_data["data"] and
                            len(search_data["data"]["data"]) > 0):

                        # 遍历查找完全匹配
                        for inst in search_data["data"]["data"]:
                            config = inst.get("config", {})
                            if config.get("nickname") == instance_name:
                                instance_uuid = inst.get("instanceUuid")
                                target_full_name = config.get("nickname")
                                break

                        # 模糊匹配
                        if not instance_uuid:
                            first_inst = search_data["data"]["data"][0]
                            instance_uuid = first_inst.get("instanceUuid")
                            target_full_name = first_inst.get("config", {}).get("nickname")

                if not instance_uuid:
                    return CommandResult().error(f"未找到名称包含 '{instance_name}' 的实例")

                # --- 步骤 B: 执行操作 ---
                final_url = ""
                final_params = {
                    "apikey": API_KEY,
                    "daemonId": DAEMON_ID,
                    "uuid": instance_uuid
                }

                # 判断是 电源操作 还是 控制台指令
                if action_raw in power_action_map:
                    target_action = power_action_map[action_raw]
                    final_url = f"{API_BASE}/api/protected_instance/{target_action}"
                    log_msg = f"正在对【{target_full_name}】执行【{action_raw}】..."
                else:
                    final_url = f"{API_BASE}/api/protected_instance/command"
                    final_params["command"] = action_raw
                    log_msg = f"正在向【{target_full_name}】发送指令: /{action_raw}"

                async with session.get(final_url, params=final_params) as resp:
                    if resp.status != 200:
                        return CommandResult().error(f"请求失败，状态码: {resp.status}")

                    res_text = await resp.text()
                    try:
                        res_json = json.loads(res_text)
                        if res_json.get("status") == 200:
                            return CommandResult().message(f"✅ {log_msg} 成功。")
                        else:
                            return CommandResult().error(f"操作失败: {res_text}")
                    except:
                        return CommandResult().message(f"请求已发送，响应: {res_text}")

        except Exception as e:
            logger.error(f"MCS Control Error: {e}")
            return CommandResult().error(f"执行出错: {str(e)}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("添加")
    async def add_subscription(self, message: AstrMessageEvent):
        """
        添加订阅节点
        格式: /添加 [备注] [天数] [可选:自定义Token]
        示例1: /添加 测试 1
        示例2: /添加 测试 1 jQo8XCoyVZh34X46BPlta
        """
        import random
        import string

        # 1. 解析参数
        msg = message.message_str.replace("添加", "").strip()
        args = msg.split()

        if len(args) < 2:
            return CommandResult().error("格式错误。示例：\n/添加 测试 1\n/添加 测试 1 自定义token")

        remark = args[0]
        # 处理时间单位，如果用户输入 1，自动补齐为 1d；如果输入 1d，则原样保留
        days = args[1] if args[1].endswith("d") else args[1] + "d"

        # 2. 决定要使用的 Token
        if len(args) >= 3:
            # 如果用户提供了第三个参数，就使用用户自定义的
            token = args[2]
        else:
            # 如果没提供，机器人自己生成一个21位的随机字符串（大小写字母+数字）
            chars = string.ascii_letters + string.digits
            token = ''.join(random.choices(chars, k=21))

        url = "http://地址/密钥/api/token"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "com.mmbox.xbrowser",
        }

        # 3. 准备你要发送的三个请求的 payload
        payloads = [
            {
                "payload": {"type": "col", "name": "A", "displayName": "A组", "remark": remark, "token": token},
                "options": {"expiresIn": days}
            }
        ]

        try:
            async with aiohttp.ClientSession() as session:
                # 4. 循环发送这三个请求
                for p in payloads:
                    # 使用 json=p 会自动带上 Content-Type: application/json
                    async with session.post(url, headers=headers, json=p) as resp:
                        if resp.status != 200:
                            err_text = await resp.text()
                            return CommandResult().error(f"⚠️ 添加失败。\n类型: {p['payload']['name']}\n错误: {err_text}")

            # 5. 如果三个都成功了，返回最终拼接好的订阅链接
            sub_link = f"https://地址/?token={token}"
            return CommandResult().message(
                f"✅ 订阅添加成功！\n"
                f"备注：{remark}\n"
                f"有效期：{days}\n\n"
                f"您的订阅链接：\n{sub_link}"
            )

        except Exception as e:
            logger.error(f"添加订阅出错: {e}")
            return CommandResult().error(f"执行出错: {str(e)}")

    @filter.command("原神")
    async def genshin_quote(self, message: AstrMessageEvent):
        """来一句原神语录"""

        import os
        import json
        import random

        try:
            # 1. 定义文件路径（您之前缺失的部分）
            plugin_path = os.path.abspath(os.path.dirname(__file__))
            genshin_json_path = os.path.join(plugin_path, "resources", "ys.json")

            # 2. 读取文件
            with open(genshin_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 3. 检查数据格式（原来的检查代码）
            if not isinstance(data, dict) or "data" not in data or not isinstance(data["data"], list):
                return CommandResult().error("本地数据为空或格式错误")

            # 4. 随机选择一句
            quote = random.choice(data["data"])
            return CommandResult().message(quote)

        except Exception as e:
            return CommandResult().error(f"读取本地数据失败: {str(e)}")


class BotCommands:
    def __init__(self):
        self.what_to_eat_data: List[str] = []
        self.good_morning_data = {}
        self.PLUGIN_NAME = "bot_plugin"

    async def save_what_eat_data(self):
        """保存食物列表"""
        with open("data/what_to_eat.json", "w", encoding="utf-8") as f:
            json.dump(self.what_to_eat_data, f, ensure_ascii=False, indent=2)

    @filter.command("今天吃什么")
    async def what_to_eat(self, message: AstrMessageEvent):
        """今天吃什么"""
        cmd, *items = message.message_str.split(" ")

        if cmd == "添加":
            if not items:
                return CommandResult().error("格式：今天吃什么 添加 [食物1] [食物2] ...")
            self.what_to_eat_data.extend(items)
            await self.save_what_eat_data()
            return CommandResult().message("添加成功")

        if cmd == "删除":
            if not items:
                return CommandResult().error("格式：今天吃什么 删除 [食物1] [食物2] ...")
            self.what_to_eat_data = [item for item in self.what_to_eat_data if item not in items]
            await self.save_what_eat_data()
            return CommandResult().message("删除成功")

        if self.what_to_eat_data:
            return CommandResult().message(f"今天吃 {random.choice(self.what_to_eat_data)}！")
        return CommandResult().message("食物列表为空，请先添加食物")

    @filter.command("喜加一")
    async def epic_free_game(self, message: AstrMessageEvent):
        """EPIC 喜加一"""
        url = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return CommandResult().error("请求失败")
                data = await resp.json()

        games = []
        upcoming = []

        for game in data["data"]["Catalog"]["searchStore"]["elements"]:
            title = game.get("title", "未知")
            try:
                if not game.get("promotions"):
                    continue
                original_price = game["price"]["totalPrice"]["fmtPrice"][
                    "originalPrice"
                ]
                discount_price = game["price"]["totalPrice"]["fmtPrice"][
                    "discountPrice"
                ]
                promotions = game["promotions"]["promotionalOffers"]
                upcoming_promotions = game["promotions"]["upcomingPromotionalOffers"]

                if promotions:
                    promotion = promotions[0]["promotionalOffers"][0]
                else:
                    promotion = upcoming_promotions[0]["promotionalOffers"][0]
                start = promotion["startDate"]
                end = promotion["endDate"]
                # 2024-09-19T15:00:00.000Z
                start_utc8 = datetime.datetime.strptime(
                    start, "%Y-%m-%dT%H:%M:%S.%fZ"
                ) + datetime.timedelta(hours=8)
                start_human = start_utc8.strftime("%Y-%m-%d %H:%M")
                end_utc8 = datetime.datetime.strptime(
                    end, "%Y-%m-%dT%H:%M:%S.%fZ"
                ) + datetime.timedelta(hours=8)
                end_human = end_utc8.strftime("%Y-%m-%d %H:%M")
                discount = float(promotion["discountSetting"]["discountPercentage"])
                if discount != 0:
                    # 过滤掉不是免费的游戏
                    continue

                if promotions:
                    games.append(
                        f"【{title}】\n原价: {original_price} | 现价: {discount_price}\n活动时间: {start_human} - {end_human}"
                    )
                else:
                    upcoming.append(
                        f"【{title}】\n原价: {original_price} | 现价: {discount_price}\n活动时间: {start_human} - {end_human}"
                    )

            except BaseException as e:
                raise e
                games.append(f"处理 {title} 时出现错误")

        if len(games) == 0:
            return CommandResult().message("暂无免费游戏")
        return (
            CommandResult()
            .message(
                "【EPIC 喜加一】\n"
                + "\n\n".join(games)
                + "\n\n"
                + "【即将免费】\n"
                + "\n\n".join(upcoming)
            )
            .use_t2i(False)
        )

    @filter.regex(r"^(早安|晚安)")
    async def good_morning(self, message: AstrMessageEvent):
        """记录早晚安时间"""
        umo_id, user = message.unified_msg_origin, message.message_obj.sender
        user_id, user_name = user.user_id, user.nickname
        curr_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        curr_time_str = curr_time.strftime("%Y-%m-%d %H:%M:%S")
        is_night = "晚安" in message.message_str

        user_data = self.good_morning_data.setdefault(umo_id, {}).setdefault(user_id, {"daily": {"morning_time": "", "night_time": ""}})
        if is_night:
            user_data["daily"]["night_time"] = curr_time_str
            user_data["daily"]["morning_time"] = ""
        else:
            user_data["daily"]["morning_time"] = curr_time_str

        # 统计今天睡觉的人数
        curr_day_sleeping = sum(
            1 for v in self.good_morning_data[umo_id].values()
            if v["daily"]["night_time"] and not v["daily"]["morning_time"] and
            datetime.datetime.strptime(v["daily"]["night_time"], "%Y-%m-%d %H:%M:%S").day == curr_time.day
        )

        # 计算睡眠时间
        if not is_night and user_data["daily"]["night_time"]:
            night_time = datetime.datetime.strptime(user_data["daily"]["night_time"], "%Y-%m-%d %H:%M:%S")
            sleep_duration = (curr_time - night_time).total_seconds()
            sleep_duration_human = f"{int(sleep_duration / 3600)}小时{int((sleep_duration % 3600) / 60)}分"
            return CommandResult().message(f"早安喵，{user_name}！\n现在是 {curr_time_str}，昨晚你睡了 {sleep_duration_human}。").use_t2i(False)

        return CommandResult().message(f"晚安喵，{user_name}！\n现在是 {curr_time_str}，你是本群今天第 {curr_day_sleeping} 个睡觉的。").use_t2i(False)
