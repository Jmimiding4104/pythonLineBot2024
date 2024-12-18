
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




'''


"""
這是一個用來存取資料的模組
如果沒有連到資料庫，會先將資料存到記憶體中
存到記憶體的資料會在程式結束後消失

環境變數沒有 DB 的設定時，會預設將資料存到記憶體中
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# --- 載入環境變數 ---
load_dotenv()

# --- 全域變數 ---
collection = None  # MongoDB 集合
user_map = {}      # 記憶體儲存用的字典

# --- 初始化資料庫 ---
def init_db():
    """
    初始化資料庫，根據環境變數 ENABLE_DB 決定是否啟用 MongoDB
    """
    global collection
    enable_db = os.getenv("ENABLE_DB", "false").lower() == "true"

    if enable_db:
        try:
            db_host = os.getenv("DBHOST")
            db_name = os.getenv("dbName")
            collection_name = os.getenv("collectionName")

            if db_host and db_name and collection_name:
                client = MongoClient(db_host)
                database = client[db_name]
                collection = database[collection_name]
                print("成功連接到 MongoDB 資料庫")
            else:
                print("MongoDB 配置不完整，改用記憶體儲存")
        except ConnectionFailure as e:
            print(f"MongoDB 連接失敗: {e}")
            collection = None
    else:
        print("未啟用 MongoDB，使用記憶體儲存")

# --- 插入資料 ---
def insert_data(userID: str, data: dict):
    """
    插入資料到 MongoDB 或記憶體
    """
    global collection
    if collection:
        collection.insert_one(data)
    else:
        user_map[userID] = data

# --- 查詢資料 ---
def query_data(userID: str):
    """
    根據 userID 查詢資料，從 MongoDB 或記憶體中取得
    """
    global collection
    if collection:
        result = collection.find_one({"user_id": userID})
        return result
    else:
        return user_map.get(userID, None)

# --- 更新資料 ---
def update_data(userID: str, data: dict):
    """
    更新資料到 MongoDB 或記憶體
    """
    global collection
    if collection:
        collection.update_one({"user_id": userID}, {"$set": data})
    else:
        user_map[userID] = data

# --- 刪除資料 ---
def delete_data(userID: str):
    """
    刪除指定 userID 的資料，從 MongoDB 或記憶體中移除
    """
    global collection
    if collection:
        collection.delete_one({"user_id": userID})
    else:
        user_map.pop(userID, None)

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

if __name__ == "__main__":
    main()
    







"""
這是一個用來存取資料的模組，支援 MongoDB Atlas 雲端資料庫。
如果未連接資料庫，將自動切換至記憶體模式進行資料儲存。
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# --- 載入環境變數 ---
load_dotenv()

# --- 全域變數 ---
collection = None  # MongoDB 集合
user_map = {}      # 記憶體儲存用的字典

# --- 初始化資料庫 ---
def init_db():
    """
    初始化資料庫，根據環境變數 ENABLE_DB 決定是否啟用 MongoDB Atlas
    """
    global collection
    enable_db = os.getenv("ENABLE_DB", "false").lower() == "true"

    if enable_db:
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if mongo_uri:
                # 建立 MongoDB Atlas 連線
                client = MongoClient(mongo_uri)
                db_name = os.getenv("DB_NAME")
                collection_name = os.getenv("COLLECTION_NAME")

                if db_name and collection_name:
                    database = client[db_name]
                    collection = database[collection_name]
                    print(f"成功連接到 MongoDB Atlas 的資料庫: {db_name}, 集合: {collection_name}")
                else:
                    print("環境變數 DB_NAME 或 COLLECTION_NAME 未設定，改用記憶體模式")
            else:
                print("環境變數 MONGO_URI 未設定，改用記憶體模式")
        except ConnectionFailure as e:
            print(f"無法連接到 MongoDB Atlas: {e}")
            collection = None
    else:
        print("未啟用 MongoDB，使用記憶體儲存")

# --- 插入資料 ---
def insert_data(userID: str, data: dict):
    """
    插入資料到 MongoDB Atlas 或記憶體
    """
    global collection
    if collection:
        collection.insert_one(data)
    else:
        user_map[userID] = data

# --- 查詢資料 ---
def query_data(userID: str):
    """
    根據 userID 查詢資料，從 MongoDB Atlas 或記憶體中取得
    """
    global collection
    if collection:
        result = collection.find_one({"user_id": userID})
        return result
    else:
        return user_map.get(userID, None)

# --- 更新資料 ---
def update_data(userID: str, data: dict):
    """
    更新資料到 MongoDB Atlas 或記憶體
    """
    global collection
    if collection:
        collection.update_one({"user_id": userID}, {"$set": data})
    else:
        user_map[userID] = data

# --- 刪除資料 ---
def delete_data(userID: str):
    """
    刪除指定 userID 的資料，從 MongoDB Atlas 或記憶體中移除
    """
    global collection
    if collection:
        collection.delete_one({"user_id": userID})
    else:
        user_map.pop(userID, None)

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

if __name__ == "__main__":
    main()

'''