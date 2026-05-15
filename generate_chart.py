# 匯入作業系統與路徑處理模組
import os
# 匯入 SQLite 資料庫模組，用於與本地資料庫互動
import sqlite3
# 匯入 pandas 模組，用於資料處理與分析
import pandas as pd
# 匯入 matplotlib.pyplot，用於繪製靜態圖表
import matplotlib.pyplot as plt
# 匯入 matplotlib，用於進階圖表設定
import matplotlib

# 設定 matplotlib 支援中文字型顯示 (針對 Mac 環境預設字型設定)
# 若在 Windows 上，可能需要改為 'Microsoft JhengHei'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
# 解決 matplotlib 中負號 '-' 顯示為方塊的問題
plt.rcParams['axes.unicode_minus'] = False

# 確保 'graph' 資料夾存在，若不存在則建立，以存放產生的圖表檔案
os.makedirs('graph', exist_ok=True)

# 設定 SQLite 資料庫的檔案路徑
db_path = 'backend/historical_data.db'
# 設定標記變數，用於判斷是否成功讀取到真實資料
data_found = False

# 檢查資料庫檔案是否存在
if os.path.exists(db_path):
    try:
        # 連線至 SQLite 資料庫
        conn = sqlite3.connect(db_path)
        # 建立游標物件以執行 SQL 語法
        cursor = conn.cursor()
        
        # 執行 SQL 查詢，取得 daily_market_data 資料表中最新的一天日期
        cursor.execute("SELECT MAX(Date) FROM daily_market_data")
        latest_date = cursor.fetchone()[0]
        
        # 若成功取得最新日期，則進一步查詢該日期的漲跌幅資料
        if latest_date:
            # 讀取當天所有股票的漲跌幅 (Change_Pct) 資料，存為 pandas DataFrame
            df = pd.read_sql(f"SELECT Change_Pct FROM daily_market_data WHERE Date = '{latest_date}'", conn)
            
            # 若 DataFrame 不為空，則統計上漲、下跌、平盤的股票數量
            if not df.empty:
                # 計算漲跌幅大於 0 的股票數量 (上漲)
                up_count = len(df[df['Change_Pct'] > 0])
                # 計算漲跌幅小於 0 的股票數量 (下跌)
                down_count = len(df[df['Change_Pct'] < 0])
                # 計算漲跌幅等於 0 的股票數量 (平盤)
                unchanged_count = len(df[df['Change_Pct'] == 0])
                # 成功取得資料，將標記設為 True
                data_found = True
        
        # 關閉資料庫連線
        conn.close()
    except Exception as e:
        # 若資料庫讀取過程中發生錯誤，則印出錯誤訊息
        print(f"無法讀取資料庫: {e}")

# 若無法取得真實資料，則使用預設的模擬數據繪製圖表
if not data_found:
    print("查無真實數據，使用模擬數據繪製圖表...")
    # 模擬的上漲家數
    up_count = 650
    # 模擬的下跌家數
    down_count = 820
    # 模擬的平盤家數
    unchanged_count = 130

# 準備圓餅圖所需的資料標籤，顯示狀態與對應數量
labels = [f'上漲家數 ({up_count})', f'下跌家數 ({down_count})', f'平盤家數 ({unchanged_count})']
# 準備圓餅圖所需的數值陣列
sizes = [up_count, down_count, unchanged_count]
# 設定圓餅圖區塊顏色 (符合台灣股市習慣：紅色代表上漲、綠色代表下跌、灰色代表平盤)
colors = ['#ff4d4f', '#52c41a', '#d9d9d9'] 
# 設定圓餅圖分離效果，讓「上漲」區塊稍微向外突出以凸顯
explode = (0.05, 0, 0)  

# 建立圖表物件與座標軸，設定圖表大小為 8x6 英吋
fig, ax = plt.subplots(figsize=(8, 6))

# 呼叫 pie() 函數繪製圓餅圖，並取得相關物件
wedges, texts, autotexts = ax.pie(
    sizes, 
    explode=explode,          # 設定區塊突出
    labels=labels,            # 設定資料標籤
    colors=colors,            # 設定區塊顏色
    autopct='%1.1f%%',        # 設定顯示百分比，保留一位小數
    shadow=True,              # 開啟陰影效果
    startangle=140,           # 設定起始角度
    textprops=dict(fontsize=12) # 設定文字大小
)

# 設定座標軸比例相等，確保圓餅圖繪製為正圓形而非橢圓
ax.axis('equal')  
# 設定圖表標題，設定字型大小、粗體，以及標題與圖表的距離 (pad)
plt.title('大盤多空結構比例圖', fontsize=16, fontweight='bold', pad=20)

# 定義圖表輸出的儲存路徑
save_path = 'graph/6_1_market_breadth.png'
# 將圖表儲存為 PNG 圖片，設定解析度為 300 dpi，並移除多餘的空白邊界
plt.savefig(save_path, dpi=300, bbox_inches='tight')
# 印出成功匯出圖表的絕對路徑
print(f"圖表已成功匯出至: {os.path.abspath(save_path)}")
