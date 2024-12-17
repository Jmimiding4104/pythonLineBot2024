'''
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


@app.get("/items/{item_id}")
async def get_item(item_id: str):
    item = await app.mongodb["items"].find_one({"_id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item



app = FastAPI()

# MongoDB 連接設置
@app.on_event("startup")
async def startup_db():
    app.mongodb_client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.mongodb = app.mongodb_client["mydatabase"]

@app.on_event("shutdown")
async def shutdown_db():
    app.mongodb_client.close()

# Pydantic 模型 - 定義資料結構
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

# 將 ObjectId 轉換為字符串
def item_helper(item) -> dict:
    return {
        "id": str(item["_id"]),
        "name": item["name"],
        "description": item.get("description"),
        "price": item["price"],
        "tax": item.get("tax"),
    }

# RESTful API 路由
@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.dict()
    result = await app.mongodb["items"].insert_one(item_dict)
    return {"id": str(result.inserted_id)}

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    item = await app.mongodb["items"].find_one({"_id": ObjectId(item_id)})
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item_helper(item)

@app.get("/items/")
async def get_items():
    items = []
    async for item in app.mongodb["items"].find():
        items.append(item_helper(item))
    return items




from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import json
import requests
from dotenv import load_dotenv
import persistence as db

# --- 載入環境變數 ---
load_dotenv()

# --- 初始化 FastAPI 應用 ---
app = FastAPI()

# CORS 支援
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 環境變數 ---
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
SECRET = os.getenv("SECRET")
WEBHOOK = os.getenv("WEBHOOK", "/")

# --- LINE API 配置 ---
LINE_API_URL = "https://api.line.me/v2/bot/message"

# --- 基本健康資訊 (示範) ---
health_info = None

# --- 訊息事件處理 ---
@app.post(WEBHOOK)
async def handle_line_webhook(request: Request, background_tasks: BackgroundTasks):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    body_str = body.decode()

    # 驗證請求
    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature")

    try:
        payload = json.loads(body_str)
        events = payload.get("events", [])
        
        for event in events:
            user_id = event["source"]["userId"]
            message_type = event["type"]

            # 判斷事件類型
            if message_type == "message" and event["message"]["type"] == "text":
                user_message = event["message"]["text"]
                response_message = process_message(user_id, user_message)
                background_tasks.add_task(reply_to_user, user_id, response_message)

        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Webhook Error")

# --- 回覆訊息給使用者 ---
def reply_to_user(user_id: str, message: str):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        response = requests.post(LINE_API_URL + "/push", headers=headers, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"LINE API Error: {e}")

# --- 健康資訊處理 ---
def process_message(user_id: str, message: str) -> str:
    db_data = db.query_data(user_id)
    if not db_data:
        db.insert_data(user_id, {"user_id": user_id, "step": 0})
        return "歡迎您！請輸入「新會員」開始註冊流程。"

    # 根據步驟處理邏輯
    step = db_data.get("step", 0)
    if message == "新會員":
        db.update_data(user_id, {"step": 1})
        return "請輸入您的姓名："
    elif step == 1:
        db.update_data(user_id, {"name": message, "step": 2})
        return "請輸入您的身份證字號："
    elif step == 2:
        if re.match(r"^[A-Z][0-9]{9}$", message):
            db.update_data(user_id, {"idNumber": message, "step": 3})
            return "請輸入您的電話號碼："
        return "格式錯誤，請重新輸入有效的身份證字號。"
    elif step == 3:
        if re.match(r"^\d{10}$", message):
            db.update_data(user_id, {"tel": message, "step": 4})
            return "您的資料已經完成，感謝註冊！"
        return "電話號碼格式錯誤，請重新輸入。"
    else:
        return "輸入指令有誤，請輸入「新會員」以開始註冊流程。"

# --- 健康資訊加載 ---
def load_health_info(config_file: str):
    global health_info
    try:
        with open(config_file, "r", encoding="utf-8") as fh:
            health_info = json.load(fh)
    except Exception as e:
        print(f"Error loading health info: {e}")

# --- 測試用健康路由 ---
@app.get("/trigger")
def health_check():
    return {"status": "OK"}

# --- 主函式 ---
def main():
    db.init_db()
    load_health_info("bot_health_info.json")
    print("FastAPI 啟動成功！")

if __name__ == "__main__":
    import uvicorn
    main()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))






'''


