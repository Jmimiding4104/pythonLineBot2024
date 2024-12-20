'''  
"""
這是一個用來存取資料的模組
如果沒有連到資料庫，會先將資料存到記憶體中
存到記憶體的資料會在程式結束後消失

環境變數沒有DB的設定時，會預設將資料存到記憶體中

"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# 起始或讀取環境變數
load_dotenv()

# 定義全域變數
collection = None
user_map = {}


# 插入資料
def insert_data(userID: str, data: any):
    global collection
    if collection != None:
        collection.insert_one(data)
    else:
        user_map[userID] = data


# 查詢資料
def query_data(userID: str):
    global collection
    if collection != None:
        result = collection.find_one({"user_id": userID})
        return result
    else:
        if userID in user_map:
            return user_map[userID]

    return None


# 更新文件
def update_data(userID: str, data):
    global collection
    if collection != None:
        collection.update_one({"user_id": userID}, {"$set": data})
    else:
        user_map[userID] = data


# 刪除文件
def delete_data(userID: str):
    global collection
    if collection != None:
        collection.delete_one({"user_id": userID})
    else:
        if userID in user_map:
            del user_map[userID]

# 起始資料庫
def init_db():
    global collection
    enable_db = os.getenv("ENABLE_DB", "false")
    if enable_db.lower() == "true":
        dbHost = os.getenv("DBHOST")
        if dbHost != None:
            dbClient = MongoClient(dbHost)
            dbName = os.getenv("dbName")
            database = dbClient[dbName]
            collectionName = os.getenv("collectionName")
            collection = database[collectionName]


def main():
    print("Hello, World!")


if __name__ == "__main__":
    main()





  
# --- 測試函式 ---
def main():
    """
    測試用的主函式
    """
    init_db()  # 初始化資料庫

    # 測試用戶資料
    test_user_id = "12345"
    test_data = {"user_id": test_user_id, "name": "John Doe", "step": 1}

    print("\n--- 插入資料 ---")
    insert_data(test_user_id, test_data)
    print(f"資料已插入: {query_data(test_user_id)}")

    print("\n--- 更新資料 ---")
    updated_data = {"name": "Jane Doe", "step": 2}
    update_data(test_user_id, updated_data)
    print(f"資料已更新: {query_data(test_user_id)}")

    print("\n--- 刪除資料 ---")
    delete_data(test_user_id)
    print(f"資料已刪除: {query_data(test_user_id)}")
'''







import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
#from fastapi import FastAPI, HTTPException

from fastapi import APIRouter, HTTPException
from persistence_db import init_db, insert_data, query_data, update_data, delete_data

router = APIRouter()



# 起始或讀取環境變數
load_dotenv()

# 定義全域變數
collection = None
user_map = {}

# 初始化 FastAPI 應用
#app = FastAPI()

# 插入資料
async def insert_data(userID: str, data: dict):
    global collection
    if collection is not None:
        await collection.insert_one(data)
    else:
        user_map[userID] = data

# 查詢資料
async def query_data(userID: str):
    global collection
    if collection is not None:
        result = await collection.find_one({"user_id": userID})
        return result
    else:
        return user_map.get(userID)

# 更新資料
async def update_data(userID: str, data: dict):
    global collection
    if collection is not None:
        await collection.update_one({"user_id": userID}, {"$set": data})
    else:
        user_map[userID] = data

# 刪除資料
async def delete_data(userID: str):
    global collection
    if collection is not None:
        await collection.delete_one({"user_id": userID})
    else:
        user_map.pop(userID, None)

# 初始化資料庫
async def init_db():
    global collection
    enable_db = os.getenv("ENABLE_DB", "false")
    if enable_db.lower() == "true":
        mongo_uri = os.getenv("MONGO_URI")
        if mongo_uri is not None:
            db_client = AsyncIOMotorClient(mongo_uri)
            db_name = os.getenv("dbName")
            database = db_client[db_name]
            collection_name = os.getenv("collectionName")
            collection = database[collection_name]
            print("Connected to MongoDB")
        else:
            print("MONGO_URI is not set. Falling back to in-memory storage.")
    else:
        print("Database is disabled. Using in-memory storage.")
        
        

async def init_db():
    enable_db = os.getenv("ENABLE_DB", "false").lower() == "true"
    if enable_db:
        mongo_uri = os.getenv("MONGO_URI")
        if mongo_uri:
            client = AsyncIOMotorClient(mongo_uri)
            db_name = os.getenv("DB_NAME")
            collection_name = os.getenv("COLLECTION_NAME")
            global collection
            if db_name and collection_name:
                database = client[db_name]
                collection = database[collection_name]
                print(f"成功連接到 MongoDB: {db_name}, 集合: {collection_name}")
            else:
                print("DB_NAME 或 COLLECTION_NAME 未設定，將使用記憶體模式")
        else:
            print("MONGO_URI 未設定，將使用記憶體模式")



# FastAPI 路由

@router.on_event("startup")
async def startup_event():
    """應用啟動時初始化資料庫"""
    await init_db()

@router.post("/data/{user_id}")
async def create_data(user_id: str, data: dict):
    """新增資料"""
    await insert_data(user_id, data)
    return {"message": "Data inserted successfully"}

@router.get("/data/{user_id}")
async def read_data(user_id: str):
    """查詢資料"""
    result = await query_data(user_id)
    if result:
        return result
    raise HTTPException(status_code=404, detail="Data not found")

@router.put("/data/{user_id}")
async def update_user_data(user_id: str, data: dict):
    """更新資料"""
    await update_data(user_id, data)
    return {"message": "Data updated successfully"}

@router.delete("/data/{user_id}")
async def delete_user_data(user_id: str):
    """刪除資料"""
    await delete_data(user_id)
    return {"message": "Data deleted successfully"}



def main():
    print("Hello, World!")

# 主程式
if __name__ == "__main__":
    main()
