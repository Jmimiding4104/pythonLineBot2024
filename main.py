import logging

from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    PushMessageRequest
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent
import re
import requests
from dotenv import load_dotenv
import os

app = Flask(__name__)
configuration = None
handler = None

load_dotenv(".env")

user_info = {
    "user_id":None,
    "name": None,
    "idNumber": None,
    "tel": None,
    "step": 0  # 用來追蹤步驟，0 表示尚未開始，1 表示請輸入姓名，2 表示請輸入身分證字號，以此類推
}


# 處理Line webhook的callback
def callback():
    global app, configuration, handler

    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        # 這邊會把訊息的內容傳給對應的handler
        # 會把request的內容解析成對應的物件(event, 所以內容不等於原本的json)
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return "OK"


# 處理和分派一般訊息
def handle_message(event):

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="haha")]
            )
        )



def main():
    global configuration, handler
    
    webhook = os.getenv("WEBHOOK", "/callback")
    
    app.add_url_rule(webhook, "callback", callback, methods=["POST"])
    app.logger.setLevel(logging.INFO)
    
    configuration = Configuration(access_token=os.getenv("ACCESS_TOKEN"))
    handler = WebhookHandler(os.getenv("SECRET"))
    handler.add(MessageEvent, message=TextMessageContent)(handle_message)

    
    host_ip = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))  # 默認使用 5000，但優先使用環境變數 PORT

    if os.getenv("HTTPTYPE") == "https":
        cerfile = os.getenv("certfile")
        keyfile = os.getenv("keyfile")
        app.run(host=host_ip, port=port, ssl_context=(cerfile, keyfile))
    else:
        app.run(host=host_ip, port=port)    

if __name__ == "__main__":
    main()  # 呼叫 main() 函式啟動應用
