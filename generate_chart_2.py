# 匯入 os 模組，用於處理檔案與目錄路徑
import os
# 匯入 sqlite3 模組，用於與本地 SQLite 資料庫互動
import sqlite3
# 匯入 pandas 模組，用於強大的資料操作與分析
import pandas as pd
# 匯入 matplotlib.pyplot 模組，用於繪製靜態圖表
import matplotlib.pyplot as plt
# 匯入 matplotlib.ticker 模組，用於自訂座標軸的刻度顯示方式
import matplotlib.ticker as ticker

# 設定 matplotlib 支援中文字型，確保中文字元能正常顯示
# (Mac 預設可使用 Arial Unicode MS，或 Heiti TC，Windows 可能需替換為 Microsoft JhengHei)
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
# 解決 matplotlib 中座標軸負號 (-) 顯示成方塊的異常問題
plt.rcParams['axes.unicode_minus'] = False

# 建立名為 'graph' 的資料夾，若已存在則不報錯，用以存放產生的圖表檔案
os.makedirs('graph', exist_ok=True)

# 指定歷史資料庫的相對路徑
db_path = 'backend/historical_data.db'
# 初始化一個布林變數，標記是否成功取得資料
data_found = False

# 檢查指定的資料庫檔案是否存在於路徑中
if os.path.exists(db_path):
    try:
        # 建立與 SQLite 資料庫的連線
        conn = sqlite3.connect(db_path)
        # 取得游標物件，以用來執行 SQL 指令
        cursor = conn.cursor()
        
        # 執行 SQL 查詢，找出 daily_market_data 資料表中的最新日期
        cursor.execute("SELECT MAX(Date) FROM daily_market_data")
        # 擷取第一筆結果的第一個欄位值，即最新日期
        latest_date = cursor.fetchone()[0]
        
        # 若順利取得最新日期，則查詢該日期下的所有股票漲跌幅
        if latest_date:
            # 透過 pandas 讀取 SQL 查詢結果，存為 DataFrame 格式
            df = pd.read_sql(f"SELECT Change_Pct FROM daily_market_data WHERE Date = '{latest_date}'", conn)
            # 確認回傳的 DataFrame 不是空的
            if not df.empty:
                # 若有資料，將標記設為 True
                data_found = True
        
        # 關閉資料庫連線，釋放資源
        conn.close()
    except Exception as e:
        # 捕捉任何在讀取資料庫時發生的例外錯誤並印出
        print(f"無法讀取資料庫: {e}")

# 若成功從資料庫取得真實數據，則開始繪圖
if data_found:
    # 建立圖表物件 (fig) 和座標軸物件 (ax)，設定畫布大小為 10x6 吋
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 定義直方圖的區間 (bins)。台股漲跌幅限制為 10%，故設定從 -10 到 11，每個區間寬度為 1%
    bins = range(-10, 12, 1) 
    
    # 匯入 numpy 模組，用於進行數值計算，如計算直方圖次數分佈
    import numpy as np
    
    # 使用 matplotlib 原生的 hist 方法初步計算分佈，取得次數、邊界和柱子物件
    counts, bins, patches = ax.hist(df['Change_Pct'], bins=bins, edgecolor='black', alpha=0.7)
    
    # 依據漲跌設定不同顏色：大於 0 為紅，小於 0 為綠，等於 0 為灰
    for i in range(len(patches)):
        if bins[i] > 0:
            patches[i].set_facecolor('#ff4d4f') # 紅色代表上漲
        elif bins[i] < -1: # 若左邊界小於 -1，屬於下跌範圍
            patches[i].set_facecolor('#52c41a') # 綠色代表下跌
        else: # 落在 [-1, 0) 或 [0, 1) 區間，包含 0 (平盤)
            # 此處原用 pass 跳過，後續將以更精準的手動繪製方式取代
            if bins[i] == -1 or bins[i] == 0:
                 pass

    # 清除上述初步畫出的直方圖，準備以更精準的方式重新繪製
    ax.clear()
    
    # 限制漲跌幅數據在 -10% 到 +10% 的合理範圍內，過濾極端異常值
    plot_data = df['Change_Pct'].clip(-10, 10)
    
    # 將數據拆分為上漲、下跌、平盤三個獨立的 Series
    up_data = plot_data[plot_data > 0]
    down_data = plot_data[plot_data < 0]
    zero_data = plot_data[plot_data == 0]
    
    # 手動計算各區間的分佈數量 (利用 numpy.histogram)
    # 計算上漲區間的分佈 (從 0 到 11，間隔 0.5)
    counts_up, _ = np.histogram(up_data, bins=np.arange(0, 11.5, 0.5))
    # 計算下跌區間的分佈 (從 -10 到 0，間隔 0.5)
    counts_down, _ = np.histogram(down_data, bins=np.arange(-10, 0.5, 0.5))
    # 計算平盤數量
    count_zero = len(zero_data)
    
    # 建立 X 軸的位置陣列，對應剛剛計算的數量
    x_up = np.arange(0.25, 11, 0.5)    # 上漲的長條圖中心位置
    x_down = np.arange(-9.75, 0, 0.5)  # 下跌的長條圖中心位置
    
    # 使用 ax.bar 繪製獨立的長條圖，分別給予上漲(紅)、下跌(綠)、平盤(灰)不同的樣式
    ax.bar(x_up, counts_up, width=0.4, color='#ff4d4f', label='上漲', edgecolor='black', alpha=0.8)
    ax.bar(x_down, counts_down, width=0.4, color='#52c41a', label='下跌', edgecolor='black', alpha=0.8)
    ax.bar([0], [count_zero], width=0.4, color='#d9d9d9', label='平盤', edgecolor='black', alpha=0.8)
    
    # 設定圖表標題，包含動態的最新日期，以及設定字型與內邊距
    plt.title(f'台股單日漲跌幅分佈圖 ({latest_date})', fontsize=16, fontweight='bold', pad=20)
    # 設定 X 軸與 Y 軸的標籤名稱
    plt.xlabel('漲跌幅 (%)', fontsize=12)
    plt.ylabel('股票家數', fontsize=12)
    
    # 強制 X 軸刻度以整數 1 為單位顯示，提升可讀性
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    
    # 加上 Y 軸的水平網格線，方便對照數值
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 顯示圖例說明 (上漲、下跌、平盤)
    plt.legend()
    
    # 定義圖表儲存的路徑
    save_path = 'graph/6_2_change_pct_dist.png'
    # 儲存圖表為高解析度 (300 dpi) 的 PNG 檔案，並自動裁切多餘邊界
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    # 輸出成功儲存圖表的訊息與絕對路徑
    print(f"圖表已成功匯出至: {os.path.abspath(save_path)}")
else:
    # 若未找到真實資料則印出提示訊息
    print("未找到資料。")
