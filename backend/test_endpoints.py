import requests
import json
import math

def check_data(data, path="root"):
    if isinstance(data, list):
        if len(data) == 0:
            print(f"  [WARN] {path} is empty list")
        for i, item in enumerate(data[:3]): # check first 3 items
            check_data(item, f"{path}[{i}]")
    elif isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, float) and math.isnan(v):
                print(f"  [ERROR] {path}.{k} is NaN")
            elif v is None:
                print(f"  [WARN] {path}.{k} is null")
            elif isinstance(v, (dict, list)):
                check_data(v, f"{path}.{k}")

endpoints = [
    "/api/meta", "/api/top-stocks", "/api/industry-focus", "/api/correlation", 
    "/api/market-breadth", "/api/synchrony", "/api/participation", "/api/volume-leaders", 
    "/api/smart-money", "/api/turnover-leaders", "/api/institutional-radar", 
    "/api/day-trading", "/api/retail-sentiment", "/api/stock/2330", "/api/articles", 
    "/api/historical-stats"
]

for ep in endpoints:
    url = f"http://127.0.0.1:8000{ep}"
    print(f"Testing {ep} ...")
    try:
        res = requests.get(url)
        if res.status_code != 200:
            print(f"  [ERROR] Status code {res.status_code}")
            continue
        data = res.json()
        if not data:
            print(f"  [WARN] Response is empty")
        check_data(data)
    except Exception as e:
        print(f"  [ERROR] {e}")
print("Done.")
