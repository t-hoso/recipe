# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import os
import sys
from argparse import ArgumentParser
import urllib
import requests

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]
GNAVI_API_KEY = os.environ["GNAVI_API_KEY"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

RESTSEARCH_URL = "https://api.gnavi.co.jp/RestSearchAPI/v3/"
DEF_ERR_MESSAGE = """
データを取得できませんでした。
時間を空けて、もう一度試してみてください。
"""
NO_HIT_ERR_MESSAGE = "お近くにぐるなびに登録されているお店はないようです" + chr(0x100017)
LINK_TEXT = "ぐるなびで見る"
FOLLOWED_RESPONSE = "フォローありがとうございます。位置情報とキーワードを送っていただくことで、お近くのお店をお送りします。" + chr(0x100059)



@app.route("/")
def hello_world():
    return "hello world!"

def call_restsearch(latitude, longitude, freeword=None):
    query = {
        "keyid": GNAVI_API_KEY,
        "latitude": latitude,
        "longitude": longitude,
        #"freeword": freeword,
        # "range": search_range
    }
    params = urllib.parse.urlencode(query, safe=",")
    r = requests.get(RESTSEARCH_URL + "?" + params)
    result = r.json()

    if "error" in result:
        if "message" in result:
            raise Exception("{}".format(result["message"]))
        else:
            raise Exception(DEF_ERR_MESSAGE)

    total_hit_count = result.get("total_hit_count", 0)
    if total_hit_count < 1:
        raise Exception(NO_HIT_ERR_MESSAGE)

    return result

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    user_lat = event.message.latitude
    user_longit = event.message.longitude

    result = call_restsearch(user_lat, user_longit)
    print("result is: {}".format(result))

    response_json_list = []

    # process result
    for (count, rest) in enumerate(result.get("rest")):
        access = rest.get("access", {})
        access_walk = "徒歩 {}分".format(access.get("walk", ""))
        holiday = "定休日: {}".format(rest.get("holiday", ""))
        image_url = rest.get("image_url", {})
        image1 = image_url.get("shop_image1", "thumbnail_template.jpg")
        if image1 == "":
            image1 = BOT_SERVER_URL + "/static/img_template.jpg"
        name = rest.get("name", "")
        opentime = "営業時間: {}".format(rest.get("opentime", ""))
        # pr = rest.get("pr", "")
        # pr_short = pr.get("pr_short", "")
        url = rest.get("url", "")

        result_text = opentime + "\n" + holiday + "\n" + access_walk + "\n"
        if len(result_text) > 60:
            result_text = result_text[:56] + "..."

        result_dict = {
            "thumbnail_image_url": image1,
            "title": name,
            # "text": pr_short + "\n" + opentime + "\n" + holiday + "\n"
            # + access_walk + "\n",
            "text": result_text,
            "actions": {
                "label": "ぐるなびで見る",
                "uri": url
            }
        }
        response_json_list.append(result_dict)
    print("response_json_list is: {}".format(response_json_list))
    columns = [
        CarouselColumn(
            thumbnail_image_url=column["thumbnail_image_url"],
            title=column["title"],
            text=column["text"],
            actions=[
                URITemplateAction(
                    label=column["actions"]["label"],
                    uri=column["actions"]["uri"],
                )
            ]
        )
        for column in response_json_list
    ]

    messages = TemplateSendMessage(
        alt_text="お店情報でした！",
        template=CarouselTemplate(columns=columns),
    )
    print("messages is: {}".format(messages))

    line_bot_api.reply_message(
        event.reply_token,
        messages=messages
    )

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)