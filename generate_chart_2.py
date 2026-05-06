import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 設定中文字型 (Mac 預設可使用 Arial Unicode MS，或 Heiti TC)
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 建立 graph 資料夾
os.makedirs('graph', exist_ok=True)

# 嘗試從資料庫讀取真實數據
db_path = 'backend/historical_data.db'
data_found = False

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        # 取得最新一天的日期
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(Date) FROM daily_market_data")
        latest_date = cursor.fetchone()[0]
        
        if latest_date:
            df = pd.read_sql(f"SELECT Change_Pct FROM daily_market_data WHERE Date = '{latest_date}'", conn)
            if not df.empty:
                data_found = True
        conn.close()
    except Exception as e:
        print(f"無法讀取資料庫: {e}")

if data_found:
    # 繪製直方圖 (Histogram)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 漲跌幅通常在 -10% 到 +10% 之間
    bins = range(-10, 12, 1) # 從 -10 到 11，每隔 1% 一個 bin
    
    # 使用 numpy 計算頻率
    import numpy as np
    counts, bins, patches = ax.hist(df['Change_Pct'], bins=bins, edgecolor='black', alpha=0.7)
    
    # 依據漲跌設定不同顏色：大於0為紅，小於0為綠，等於0為灰
    for i in range(len(patches)):
        if bins[i] > 0:
            patches[i].set_facecolor('#ff4d4f') # 紅色
        elif bins[i] < -1: # 因為 bin 包含左邊界，0 的 bin 是 [0, 1)
            patches[i].set_facecolor('#52c41a') # 綠色
        else: # [-1, 0) 以及 [0, 1) 其中 0 會有灰色
            if bins[i] == -1 or bins[i] == 0:
                 # 更精細的上色可以拆開，簡單的話用統一顏色或細分
                 pass

    # 針對 bin 重新上色，確保視覺正確：
    ax.clear()
    
    # 篩選掉極端值，只看 -10 到 10
    plot_data = df['Change_Pct'].clip(-10, 10)
    
    # 畫紅、綠、灰三個直方圖來疊加，會更準確
    up_data = plot_data[plot_data > 0]
    down_data = plot_data[plot_data < 0]
    zero_data = plot_data[plot_data == 0]
    
    # 手動繪製長條圖
    # 計算各區間的數量
    counts_up, _ = np.histogram(up_data, bins=np.arange(0, 11.5, 0.5))
    counts_down, _ = np.histogram(down_data, bins=np.arange(-10, 0.5, 0.5))
    count_zero = len(zero_data)
    
    # x 軸
    x_up = np.arange(0.25, 11, 0.5)
    x_down = np.arange(-9.75, 0, 0.5)
    
    ax.bar(x_up, counts_up, width=0.4, color='#ff4d4f', label='上漲', edgecolor='black', alpha=0.8)
    ax.bar(x_down, counts_down, width=0.4, color='#52c41a', label='下跌', edgecolor='black', alpha=0.8)
    ax.bar([0], [count_zero], width=0.4, color='#d9d9d9', label='平盤', edgecolor='black', alpha=0.8)
    
    # 設定圖表標題與標籤
    plt.title(f'台股單日漲跌幅分佈圖 ({latest_date})', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('漲跌幅 (%)', fontsize=12)
    plt.ylabel('股票家數', fontsize=12)
    
    # 設定 x 軸刻度
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    
    # 加入網格線
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 顯示圖例
    plt.legend()
    
    # 儲存圖表
    save_path = 'graph/6_2_change_pct_dist.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"圖表已成功匯出至: {os.path.abspath(save_path)}")
else:
    print("未找到資料。")
