import json
import time
import base64
import re
import asyncio
import os
from urllib.parse import unquote
import aiofiles
import aiohttp
from lxml import etree

async def download_file(url, name, path):
    dir_path = os.path.join(path)
    file_path = os.path.join(path, name)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        return True
    if os.path.exists(file_path):
        return True
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                async with aiofiles.open(str(file_path), "wb") as f:
                    await f.write(await response.read())
        return True
    except asyncio.TimeoutError:
        print(f"下载文件{name} 超时，url：{url}")
        return False
    except:
        print(f"下载文件 {name} 链接错误，url：{url}")
        return False

async def get_info(data_path):
    headers = {
        "User-Agent": '"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)"'
    }

    char_data_list = {}
    simple_star_list = {
        6: [],
        5: [],
        4: [],
        3: []
    }
    url = "https://wiki.biligame.com/arknights/干员数据表"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            result = await resp.text()
    dom = etree.HTML(result, etree.HTMLParser())
    char_list = dom.xpath("//table[@id='CardSelectTr']/tbody/tr")
    for char in char_list:
        try:
            # 获取基本信息
            avatar = char.xpath("./td[1]/div/div/div/a/img/@srcset")[0]
            name = char.xpath("./td[2]/a/text()")[0]
            profession = char.xpath("./td[4]/img/@alt")[0]
            star = char.xpath("./td[5]/text()")[0]
            sources = [_.strip('\n') for _ in char.xpath("./td[8]/text()")]

            # 获取半身图/全身立绘
            url_root = f"https://prts.wiki/w/文件:半身像_{name}_1.png"
            async with aiohttp.ClientSession() as session:
                async with session.get(url_root) as resp:
                    result = await resp.text()
            dom = etree.HTML(result, etree.HTMLParser())
            image_url_1 = dom.xpath("//img[@decoding='async' and @width='180'and @height='360']/@src")
            image_url_path = re.search("\/\w+\/\w+\/\w+", image_url_1[0], re.M | re.I)
        except IndexError:
            continue
        char_dict = {
            "头像": unquote(str(avatar).split(" ")[-2]),
            "名称": name,
            "职业": str(profession),
            "星级": int(str(star).strip()),
            "获取途径": sources,
            "半身像": f"https://prts.wiki{str(image_url_path.group())}/半身像_{name}_1.png",
            "立绘": f"https://prts.wiki{str(image_url_path.group())}/立绘_{name}_1.png",
        }

        # 稀有度分类
        if "标准寻访" in char_dict["获取途径"]:
            if char_dict["星级"] == 6:
                simple_star_list[6].append(name)
            elif char_dict["星级"] == 5:
                simple_star_list[5].append(name)
            elif char_dict["星级"] == 4:
                simple_star_list[4].append(name)
            elif char_dict["星级"] == 3:
                simple_star_list[3].append(name)

        char_data_list[name] = char_dict

    json_write(os.path.join(data_path, 'simple_star_list.json'), simple_star_list)
    json_write(os.path.join(data_path, 'char_data_list.json'), char_data_list)
    return char_data_list

async def char_image_download(char_list):
    data_path = "data"
    download_path = os.path.join(data_path, "image", "char")
    for char in char_list:
        name = char
        await download_file(char_list[name]["半身像"], f"半身像_{name}.png", download_path)
        await download_file(char_list[name]["立绘"], f"立绘_{name}.png", download_path)

def start_update():
    loop = asyncio.get_event_loop()
    char_list = loop.run_until_complete(get_info("data"))
    loop.run_until_complete(char_image_download(char_list))

def json_write(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return True
    except:
        return False

if __name__ == "__main__":
    start_update()
