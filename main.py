import random
import asyncio
import os
import re
import json
import datetime
import aiohttp
import urllib.parse
import logging
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

        # moe
        self.moe_urls = [
            "https://t.mwm.moe/pc/",
            "https://t.mwm.moe/mp",
            "https://www.loliapi.com/acg/",
            "https://www.loliapi.com/acg/pc/",
        ]

        self.search_anmime_demand_users = {}

    def time_convert(self, t):
        m, s = divmod(t, 60)
        return f"{int(m)}分{int(s)}秒"


    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_search_anime(self, message: AstrMessageEvent):
        """检查是否有搜番请求"""
        sender = message.get_sender_id()
        if sender in self.search_anmime_demand_users:
            message_obj = message.message_obj
            url = "https://api.trace.moe/search?anilistInfo&url="
            image_obj = None
            for i in message_obj.message:
                if isinstance(i, Image):
                    image_obj = i
                    break
            try:
                try:
                    # 需要经过url encode
                    image_url = urllib.parse.quote(image_obj.url)
                    url += image_url
                except BaseException as _:
                    if sender in self.search_anmime_demand_users:
                        del self.search_anmime_demand_users[sender]
                    return CommandResult().error(
                        f"发现不受本插件支持的图片数据：{type(image_obj)}，插件无法解析。"
                    )

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            if sender in self.search_anmime_demand_users:
                                del self.search_anmime_demand_users[sender]
                            return CommandResult().error("请求失败")
                        data = await resp.json()

                if data["result"] and len(data["result"]) > 0:
                    # 番剧时间转换为x分x秒
                    data["result"][0]["from"] = self.time_convert(
                        data["result"][0]["from"]
                    )
                    data["result"][0]["to"] = self.time_convert(data["result"][0]["to"])

                    warn = ""
                    if float(data["result"][0]["similarity"]) < 0.8:
                        warn = "相似度过低，可能不是同一番剧。建议：相同尺寸大小的截图; 去除四周的黑边\n\n"
                    if sender in self.search_anmime_demand_users:
                        del self.search_anmime_demand_users[sender]
                    return CommandResult(
                        chain=[
                            Plain(
                                f"{warn}番名: {data['result'][0]['anilist']['title']['native']}\n相似度: {data['result'][0]['similarity']}\n剧集: 第{data['result'][0]['episode']}集\n时间: {data['result'][0]['from']} - {data['result'][0]['to']}\n精准空降截图:"
                            ),
                            Image.fromURL(data["result"][0]["image"]),
                        ],
                        use_t2i_=False,
                    )
                else:
                    if sender in self.search_anmime_demand_users:
                        del self.search_anmime_demand_users[sender]
                    return CommandResult(True, False, [Plain("没有找到番剧")], "sf")
            except Exception as e:
                raise e





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

    @filter.command("moe")
    async def get_moe(self, message: AstrMessageEvent):
        """随机动漫图片"""
        shuffle = random.sample(self.moe_urls, len(self.moe_urls))
        for url in shuffle:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            return CommandResult().error(f"获取图片失败: {resp.status}")
                        data = await resp.read()
                        break
            except Exception as e:
                logger.error(f"从 {url} 获取图片失败: {e}。正在尝试下一个API。")
                continue
        # 保存图片到本地
        try:
            with open("moe.jpg", "wb") as f:
                f.write(data)
            return CommandResult().file_image("moe.jpg")

        except Exception as e:
            return CommandResult().error(f"保存图片失败: {e}")

    @filter.command("搜番")
    async def get_search_anime(self, message: AstrMessageEvent):
        """以图搜番"""
        sender = message.get_sender_id()
        if sender in self.search_anmime_demand_users:
            yield message.plain_result("正在等你发图喵，请不要重复发送")
        self.search_anmime_demand_users[sender] = False
        yield message.plain_result("请在 30 喵内发送一张图片让我识别喵")
        await asyncio.sleep(30)
        if sender in self.search_anmime_demand_users:
            if self.search_anmime_demand_users[sender]:
                del self.search_anmime_demand_users[sender]
                return
            del self.search_anmime_demand_users[sender]
            yield message.plain_result("🧐你没有发送图片，搜番请求已取消了喵")

    @filter.command("mc")
    async def mcs(self, message: AstrMessageEvent):
        """查mc服务器"""
        message_str = message.message_str
        if message_str == "mc":
            return CommandResult().error("查 Minecraft 服务器。格式: /mc [服务器地址]")
        ip = message_str.strip()
        if ip.startswith("mc"):
            ip = ip[2:].strip()
        
        url = f"http://您的网址域名/api.php?server={ip}"
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
    """60秒看世界调用60s的项目"""
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
            # 第1步：验证API可用性
            if not await verify_image(session):
                yield message.plain_result("⚠️新闻服务暂时不可用，请稍后再试")
                return

            # 第2步：返回图片结果 - 移除了 use_t2i 参数
            yield CommandResult(chain=[Image.fromURL(API_URL)])

    except Exception as e:
        logger.error(f"获取今日新闻时出错: {str(e)}", exc_info=True)
        yield message.plain_result("❌获取新闻时发生错误，请稍后再试")


@filter.command("帮助")
async def help_command(self, message: AstrMessageEvent):
    """获取机器人使用说明"""
    url = "http://您的网址域名/help.html"
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


path = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本目录
food_json_path = os.path.join(path, "resources", "ys.json")  # 构造 JSON 文件路径

@filter.command("原神")
async def genshin_quote(self, message: AstrMessageEvent):
    """来一句原神语录"""
    
    # 尝试读取本地 JSON 文件
    try:
        with open(food_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict) or "data" not in data or not isinstance(data["data"], list):
            return CommandResult().error("本地数据为空或格式错误")
        
        quote = random.choice(data["data"])  # 从 "data" 数组中随机选择一句
        
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
