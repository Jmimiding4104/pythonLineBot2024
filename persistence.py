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

