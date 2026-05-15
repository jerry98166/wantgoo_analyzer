# 匯入 requests 模組，用於發送 HTTP GET 請求以測試本機 API 端點
import requests
# 匯入 json 模組，用於解析或格式化 JSON 資料
import json
# 匯入 math 模組，用於檢查數值是否為 NaN (Not a Number)
import math

def check_data(data, path="root"):
    """
    遞迴檢查 API 回傳的 JSON 資料結構。
    主要目的是確保回傳的資料中沒有非法的 NaN (會導致前端解析失敗)，
    並警告如果是空陣列或 null 值。
    """
    # 如果資料是串列 (List)
    if isinstance(data, list):
        # 檢查是否為空陣列
        if len(data) == 0:
            print(f"  [WARN] {path} is empty list")
        # 遞迴檢查前 3 筆資料，避免資料量過大導致測試過久
        for i, item in enumerate(data[:3]): # check first 3 items
            check_data(item, f"{path}[{i}]")
    # 如果資料是字典 (Dict / Object)
    elif isinstance(data, dict):
        for k, v in data.items():
            # 檢查浮點數是否為 NaN，若是則印出錯誤
            if isinstance(v, float) and math.isnan(v):
                print(f"  [ERROR] {path}.{k} is NaN")
            # 檢查值是否為 None (null)，若是則警告
            elif v is None:
                print(f"  [WARN] {path}.{k} is null")
            # 如果值又是字典或串列，進行遞迴檢查
            elif isinstance(v, (dict, list)):
                check_data(v, f"{path}.{k}")

# 定義要測試的本機 API 端點列表
endpoints = [
    "/api/meta", "/api/top-stocks", "/api/industry-focus", "/api/correlation", 
    "/api/market-breadth", "/api/synchrony", "/api/participation", "/api/volume-leaders", 
    "/api/smart-money", "/api/turnover-leaders", "/api/institutional-radar", 
    "/api/day-trading", "/api/retail-sentiment", "/api/stock/2330", "/api/articles", 
    "/api/historical-stats"
]

# 走訪每一個端點進行測試
for ep in endpoints:
    # 組裝本機測試網址 (假設 FastAPI 運行在 port 8000)
    url = f"http://127.0.0.1:8000{ep}"
    print(f"Testing {ep} ...")
    try:
        # 發送 GET 請求
        res = requests.get(url)
        # 檢查 HTTP 狀態碼是否為 200 OK
        if res.status_code != 200:
            print(f"  [ERROR] Status code {res.status_code}")
            continue
            
        # 將回應內容轉為 JSON 格式
        data = res.json()
        # 檢查資料是否為空
        if not data:
            print(f"  [WARN] Response is empty")
            
        # 呼叫檢查函式，驗證資料的正確性
        check_data(data)
    except Exception as e:
        # 捕捉並印出請求或解析過程中的任何錯誤
        print(f"  [ERROR] {e}")

# 所有端點測試完成
print("Done.")
