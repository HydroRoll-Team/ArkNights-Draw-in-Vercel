import json
import time
import base64
import re
import asyncio
from tqdm import tqdm, trange
import os
from urllib.parse import unquote
import aiofiles as aiofiles
import aiohttp
from lxml import etree, html
from os.path import dirname, abspath, join

class TableData:
    pass

dir = dirname(abspath(__file__))
# 更新核心函数
class UpdateHandle:

    def __init__(self, data_path: str, conf_path: str):
        self.headers = {
            "User-Agent": '"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)"'
        }
        self.data_path = data_path
        self.conf_path = conf_path
        pass

    def get_char_data(self):
        pass

    def get_table_data(self):
        pass

    def get_up_table(self):
        pass

    async def download_file(self, url: str, name: str, path: str) -> bool:
        r"""下载文件

        :param url: 下载链接
        :param name: 文件名
        :param path: 储存目录
        :rtype bool
        """
        dir_path = self.data_path + path
        file_path = self.data_path + path + name

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            return True
        if os.path.exists(file_path):
            # print("文件"+name+"已存在")
            return True
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=10) as response:
                    async with aiofiles.open(str(file_path), "wb") as f:
                        await f.write(await response.read())
            # print(f"下载文件{name}成功")
            # print(f"下载文件{name}成功，url：{url}，储存目录：{path}")
            return True
        except TimeoutError:
            print(f"下载文件{name} 超时，url：{url}")
            return False
        except:
            print(f"下载文件 {name} 链接错误，url：{url}")
            return False

    def request_data(self, url: str, cookie: list):
        pass

    # 获取url链接内容
    async def get_url(self, url: str) -> str:
        result = ""
        retry = 5
        for i in range(retry):

            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(url) as resp:
                        result = await resp.text()
                break
            except TimeoutError:
                self.log_print()
                await asyncio.sleep(1)
        return result

    # 显示日志
    def log_print(self, message: str) -> bool:
        pass

    #

    def test(self):
        pass

class UpdateHandleArk(UpdateHandle):
    def __init__(self, data_path: str, conf_path: str):
        super().__init__(data_path, conf_path)

    # 获取人物更新信息
    async def get_info(self):
        char_data_list = {}
        simple_star_list = {
            6: [],
            5: [],
            4: [],
            3: []
        }
        limit_activity = {
            "全部活动": [],
            "linkage": {},
            "limit_": {}
        }
        url = "https://wiki.biligame.com/arknights/干员数据表"
        result = await self.get_url(url)
        if not result:
            return ""
        dom = etree.HTML(result, etree.HTMLParser())
        char_list = dom.xpath("//table[@id='CardSelectTr']/tbody/tr")
        for char in trange(len(char_list), desc="处理人物素材", unit="char"):
            char = char_list[char]
            try:
                # 获取基本信息
                avatar = char.xpath("./td[1]/div/div/div/a/img/@srcset")[0]
                name = char.xpath("./td[2]/a/text()")[0]
                profession = char.xpath("./td[4]/img/@alt")[0]
                star = char.xpath("./td[5]/text()")[0]
                sources = [_.strip('\n') for _ in char.xpath("./td[8]/text()")]

                # 获取半身图/全身立绘
                url_root = "https://prts.wiki/w/文件:半身像_" + name + "_1.png"
                result = await self.get_url(url_root)
                if not result:
                    return ""
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
                "半身像": "https://prts.wiki" + str(image_url_path.group()) + "/半身像_" + name + "_1.png",
                "立绘": "https://prts.wiki" + str(image_url_path.group()) + "/立绘_" + name + "_1.png"
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

        json_write(self.data_path + 'simple_star_list.json', simple_star_list)
        json_write(self.data_path + 'char_data_list.json', char_data_list)
        return char_data_list

    # 下载图片数据
    async def char_image_download(self, char_list):
        download_path = join(dir,"..","data","image","char")
        with tqdm(range(len(char_list)), desc="下载图片素材", unit="char") as pbar:
            for char in range(len(char_list)):
                name = list(char_list)[char]
                await self.download_file(char_list[name]["半身像"], "半身像_" + name + ".png", download_path)
                await self.download_file(char_list[name]["立绘"], "立绘_" + name + ".png", download_path)
                pbar.set_postfix(prograss=str(name) + "下载完毕")
                pbar.update(1)

    def start_update(self):
        loop = asyncio.get_event_loop()
        char_list = loop.run_until_complete(self.get_info())
        loop.run_until_complete(self.char_image_download(char_list))


def json_write(path, data) -> bool:
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return True
    except:
        return False


def upload_file_to_repo(file_path, repo_owner, repo_name, branch, token):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    with open(file_path, 'rb') as file:
        content = file.read()
        data = {
            "message": "Upload file",
            "content": base64.b64encode(content).decode("utf-8"),
            "branch": branch
        }
        response = requests.put(url, json=data, headers=headers)
        if response.status_code == 201:
            print("File uploaded successfully.")
        else:
            print(f"Failed to upload file. Response: {response.content.decode('utf-8')}")

            
if __name__ == "__main__":
    data_path = join(dir,"..","data","Arknights")
    conf_path = join(dir,"..","conf","Arknights")
    github_token = os.getenv('GITHUB_TOKEN')
    repo_fullname = os.getenv('GITHUB_REPOSITORY')
    repo_owner, repo_name = repo_fullname.split("/")
    branch = os.getenv('GITHUB_REF').split("/")[-1]

    # 执行脚本更新数据和下载图片
    ark_update = UpdateHandleArk(data_path, conf_path)
    ark_update.start_update()

    # 上传文件到对应的Repo文件夹
    upload_file_to_repo(data_path + 'simple_star_list.json', repo_owner, repo_name, branch, github_token)
    upload_file_to_repo(data_path + 'char_data_list.json', repo_owner, repo_name, branch, github_token)

    # 上传图片文件夹里的所有文件
    file_path = join(dir,"..","data","image","char")
    files = os.listdir(file_path)
    for file in files:
        upload_file_to_repo(file_path + file, repo_owner, repo_name, branch, github_token)
