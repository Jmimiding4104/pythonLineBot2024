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

load_dotenv(".env")

user_info = {
    "user_id":None,
    "name": None,
    "idNumber": None,
    "tel": None,
    "step": 0  # 用來追蹤步驟，0 表示尚未開始，1 表示請輸入姓名，2 表示請輸入身分證字號，以此類推
}

access_token = os.getenv("ACCESS_TOKEN")
secret = os.getenv("SECRET")

configuration = Configuration(
    access_token=access_token)
handler = WebhookHandler(secret)




def main():
    port = int(os.getenv("PORT", 5000))  # 默認使用 5000，但優先使用環境變數 PORT
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()  # 呼叫 main() 函式啟動應用