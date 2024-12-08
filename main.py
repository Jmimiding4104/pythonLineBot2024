from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    MessageAction,
    TextMessage,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    PushMessageRequest,
)

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    UnfollowEvent,
    PostbackEvent,
)


from linebot.exceptions import LineBotApiError
import re
import requests
from dotenv import load_dotenv
import os

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

load_dotenv(".env")

webhook = os.getenv("WEBHOOK", "/")

user_info = {
    "user_id": None,
    "name": None,
    "idNumber": None,
    "tel": None,
    "step": 0,  # 用來追蹤步驟，0 表示尚未開始，1 表示請輸入姓名，2 表示請輸入身分證字號，以此類推
}

access_token = os.getenv("ACCESS_TOKEN")
secret = os.getenv("SECRET")

configuration = Configuration(access_token=access_token)
handler = WebhookHandler(secret)


def send_operation_options(line_bot_api, user_id):
    print(user_id)
    buttons_template = ButtonsTemplate(
        title="請問你要進行什麼操作？",
        text="請點擊以下選項",
        actions=[
            PostbackAction(label="開始集點", data="start"),
            PostbackAction(label="不需要操作", data="logout"),
        ],
    )

    template_message = TemplateMessage(
        alt_text="請問你要進行什麼操作？", template=buttons_template
    )
    line_bot_api.push_message_with_http_info(
        PushMessageRequest(to=user_id, messages=[template_message])
    )


def send_other_operation_options(line_bot_api, user_id):
    buttons_template = ButtonsTemplate(
        title="請問你還需要處理其他項目嗎？",
        text="請點擊以下選項",
        actions=[
            PostbackAction(label="生理監測", data="monitor"),
            PostbackAction(label="AI衛教", data="educate"),
            PostbackAction(label="運動", data="exercise"),
            PostbackAction(label="登出", data="logout"),
        ],
    )
    template_message = TemplateMessage(
        alt_text="請問你還需要處理其他項目嗎？", template=buttons_template
    )
    line_bot_api.push_message_with_http_info(
        PushMessageRequest(to=user_id, messages=[template_message])
    )


@app.route(webhook, methods=["POST"])
def linebot():
    global user_info

    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    #app.logger.info("Request body: " + body)
    print("\nRequest body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except Exception as e:
        app.logger.error(f"Error: {e}")

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_info["user_id"] = event.source.user_id

        if event.message.text == "連結LINE集點":
            reply_text = "請輸入身分證字號"
            user_info["step"] = 1
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )

        elif user_info["step"] == 1:
            idNumber = event.message.text
            lineId = event.source.user_id

            if re.match(r"^[A-Za-z]\d{9}$", idNumber):
                try:
                    response = requests.post(
                        url="https://linebotapi-tgkg.onrender.com/linkLineID/",
                        json={"idNumber": idNumber, "lineId": lineId},
                    )
                    if response.status_code == 200:
                        reply_text = "連結成功"
                    else:
                        reply_text = "重複連結或錯誤，請確認!"
                except Exception as e:
                    print(f"Error during request: {e}")
                    reply_text = "請聯絡管理員"

                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )

                # 完成步驟後，重設步驟狀態（如果需要）
                user_info["step"] = 0  # 重設步驟為0
            else:
                reply_text = (
                    "身分證字號格式錯誤，請輸入有效的身分證字號（1個字母 + 9個數字）"
                )
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )

        elif event.message.text == "集點":
            user_info["user_id"] = event.source.user_id
            print(event.source.user_id)
            response = requests.put(
                url="https://linebotapi-tgkg.onrender.com/add/healthMeasurement",
                json={"lineId": user_info["user_id"]},  # 傳遞的 JSON 資料
            )
            print(response.status_code)
            data = response.json()
            health_measurement = data.get("healthMeasurement")  # 使用 .get() 確保鍵存在
            if response.status_code == 200:
                if health_measurement < 15:
                    reply_text = f"集點完成，目前測量次數為{health_measurement}，加油!!"
                if health_measurement == 15:
                    reply_text = f"集滿囉!!!可以拿給志工確認換禮物囉~"
                if health_measurement > 15:
                    reply_text = "有持續量血壓很棒喔~"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
            else:
                reply_text = "集點失敗！請稍後嘗試!"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )

        if event.message.text == "新會員":
            user_info["step"] = 1
            reply_text = "請輸入姓名"
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        elif user_info["step"] == 1:
            user_info["name"] = event.message.text
            user_info["step"] = 2
            reply_text = "請輸入身分證字號"
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        elif user_info["step"] == 2:
            if re.match(r"^[A-Za-z]\d{9}$", event.message.text):
                user_info["idNumber"] = event.message.text
                user_info["step"] = 3
                reply_text = "請輸入電話號碼"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
            else:
                reply_text = "格式錯誤！請輸入 1 個英文字母和 9 個數字。"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
        elif user_info["step"] == 3:
            user_info["tel"] = event.message.text
            user_info["step"] = 4

            # Create confirmation template message
            buttons_template = ButtonsTemplate(
                title="請確認您的資料",
                text=(
                    f"您的姓名是 {user_info['name']}、\n"
                    f"身份證字號是 {user_info['idNumber']}、\n"
                    f"電話是 {user_info['tel']}。\n請問是否正確？"
                ),
                actions=[
                    PostbackAction(label="是", data="correct"),
                    PostbackAction(label="否", data="incorrect"),
                ],
            )

            template_message = TemplateMessage(
                alt_text="確認資料", template=buttons_template
            )

            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token, messages=[template_message]
                )
            )
        elif re.match(r"^[A-Za-z]\d{9}$", event.message.text) or user_info["step"] == 4:
            user_info["idNumber"] = event.message.text
            try:
                response = requests.get(
                    url="https://linebotapi-tgkg.onrender.com/search/",
                    json={"idNumber": user_info["idNumber"]},
                )
                print(response, user_info["idNumber"])
                if response.status_code == 200:

                    send_operation_options(line_bot_api, user_info["user_id"])
                else:
                    reply_text = "請註冊!!"
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=reply_text)],
                        )
                    )
            except:
                reply_text = "請聯絡管理員"


@handler.add(PostbackEvent)
def handle_postback(event):
    global user_info
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        tk = event.reply_token
        data = event.postback.data

        if data == "correct":
            try:
                response = requests.post(
                    url="https://linebotapi-tgkg.onrender.com/add_user/",
                    json={
                        "name": user_info["name"],
                        "idNumber": user_info["idNumber"],
                        "tel": user_info["tel"],
                    },  # 傳遞的 JSON 資料
                )
                if response.status_code == 200:
                    reply_text = "註冊完成！請輸入身分證字號登入"
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=reply_text)],
                        )
                    )
                else:
                    reply_text = "註冊失敗！請稍後嘗試!"
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=reply_text)],
                        )
                    )
            except:
                reply_text = "請聯絡管理員"
            # Confirm registration completion
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        elif data == "incorrect":
            # Reset user information if incorrect
            user_info = {"name": None, "idNumber": None, "tel": None, "step": 0}
            reply_text = "請重新輸入姓名"
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        elif data == "start":
            buttons_template = ButtonsTemplate(
                title="請問你要處理哪個項目？",
                text="請點擊以下選項",
                actions=[
                    PostbackAction(label="生理監測", data="monitor"),
                    PostbackAction(label="AI衛教", data="educate"),
                    PostbackAction(label="運動", data="exercise"),
                    PostbackAction(label="登出", data="logout"),
                ],
            )

            template_message = TemplateMessage(
                alt_text="請問你要進行什麼集點？", template=buttons_template
            )
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token, messages=[template_message]
                )
            )
        elif data == "logout":
            user_info = {  # 重設 user_info
                "name": "",
                "idNumber": "",
                "tel": "",
                "step": 0,
            }
            reply_text = "登出成功"
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        elif data == "monitor":
            response = requests.put(
                url="https://linebotapi-tgkg.onrender.com/add/healthMeasurement",
                json={"idNumber": user_info["idNumber"]},  # 傳遞的 JSON 資料
            )
            if response.status_code == 200:
                reply_text = "集點完成"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
                send_other_operation_options(line_bot_api, user_info["user_id"])
            else:
                reply_text = "集點失敗！請稍後嘗試!"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
        elif data == "educate":
            response = requests.put(
                url="https://linebotapi-tgkg.onrender.com/add/healthEducation",
                json={"idNumber": user_info["idNumber"]},  # 傳遞的 JSON 資料
            )
            if response.status_code == 200:
                reply_text = "集點完成"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
            else:
                reply_text = "集點失敗！請稍後嘗試!"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
            send_other_operation_options(line_bot_api, user_info["user_id"])
        elif data == "exercise":
            response = requests.put(
                url="https://linebotapi-tgkg.onrender.com/add/exercise",
                json={"idNumber": user_info["idNumber"]},  # 傳遞的 JSON 資料
            )
            if response.status_code == 200:
                reply_text = "集點完成"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
            else:
                reply_text = "集點失敗！請稍後嘗試!"
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
            send_other_operation_options(line_bot_api, user_info["user_id"])


# 加入好友
@handler.add(FollowEvent)
def handle_follow(event):
    app.logger.info("Got Follow event:" + event.source.user_id)
    msg_list = []

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        try:
            profile = line_bot_api.get_profile(event.source.user_id)
            print(profile.display_name)
            welcometitle = "您好！歡迎使用健康小幫手，您看起來還不是我們會員，請選擇新會員或其他以獲得服務。"
            if profile.display_name:                
                welcometitle = profile.display_name + welcometitle

            msg_list.append(TextMessage(text=welcometitle))
    
            buttons_template = ButtonsTemplate(
                title="服務選單",
                text="請點擊以下選項",
                actions=[
                    MessageAction(label="新會員", text="新會員"),
                    PostbackAction(label="其他", data="idontknow"),
                ],
            )

            template_message = TemplateMessage(
                alt_text="歡迎新朋友～", template=buttons_template
            )
    
            msg_list.append(template_message)
            
        except LineBotApiError as e:
            print(e.status_code)

        if len(msg_list) > 0:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=msg_list,
                )
            )

# 取消好友
@handler.add(UnfollowEvent)
def handle_unfollow(event):
    # 看法規政策 有時候可能需要刪除使用者資料
    app.logger.info("Got Unfollow event:" + event.source.user_id)


def main():
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


@app.route("/trigger", methods=["GET", "POST"])
def trigger_api():
    try:
        return "OKOK"
    except Exception as e:
        return "QQ"


# ngrok http http://127.0.0.1:5000
