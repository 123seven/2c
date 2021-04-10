#!/usr/bin/env python
"""
    Created by howie.hu at 2021/4/7.
    Description：获取公众号文章列表
    Changelog: all notable changes to this file will be documented
"""

import asyncio
import time

import ujson
import xmltodict

from ruia import Response, Spider
from ruia_motor import RuiaMotorUpdate, init_spider

from src.config import Config
from src.utils import md5_encryption


class WechatDocSpider(Spider):
    """
    微信RSS文章爬虫
    """

    collection = "2c_articles"

    async def parse(self, response: Response):
        """
        爬虫解析函数
        :param response:
        :type response: Response
        """
        xml_data = await response.text()
        json_data = ujson.loads(ujson.dumps(xmltodict.parse(xml_input=xml_data)))
        channel_data = json_data["rss"]["channel"]
        item_data = channel_data["item"]

        json_title = channel_data["title"]
        wechat_name = json_title.split("|")[0].strip()
        wechat_des = channel_data["description"]
        for each in item_data:
            pub_date = each["pubDate"]
            doc_name, doc_link = each.get("title", ""), each.get("link", "")
            doc_id = md5_encryption(f"{doc_name}_{doc_link}")
            s_time = time.strptime(pub_date, "%a, %d %b %Y %H:%M:%S +0800")
            each_data = {
                "doc_id": doc_id,
                "doc_name": doc_name,
                "doc_des": each.get("description", ""),
                "doc_link": doc_link,
                "doc_content": each.get("content:encoded", ""),
                "doc_date": time.strftime("%Y-%m-%d", s_time),
                "doc_ts": time.mktime(s_time),
                "doc_source": "wechat",
                "doc_ext": {"wechat_name": wechat_name, "wechat_des": wechat_des,},
            }
            yield RuiaMotorUpdate(
                collection=self.collection,
                filter={"doc_id": doc_id},
                update={"$set": each_data},
                upsert=True,
            )


async def init_motor_after_start(spider_ins):
    """
    初始化ruia-motor插件，数据自动持久化到MongoDB
    """
    spider_ins.mongodb_config = Config.MONGODB_CONFIG
    init_spider(spider_ins=spider_ins)


def run_wechat_doc_spider():
    """
    启动爬虫
    """
    loop = asyncio.get_event_loop()
    WechatDocSpider.start_urls = list(Config.RSS_DICT.values())
    WechatDocSpider.start(
        loop=loop, after_start=init_motor_after_start, close_event_loop=False
    )


if __name__ == "__main__":
    run_wechat_doc_spider()