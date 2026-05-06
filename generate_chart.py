import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

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
                up_count = len(df[df['Change_Pct'] > 0])
                down_count = len(df[df['Change_Pct'] < 0])
                unchanged_count = len(df[df['Change_Pct'] == 0])
                data_found = True
        conn.close()
    except Exception as e:
        print(f"無法讀取資料庫: {e}")

# 若無資料庫則使用模擬數據
if not data_found:
    print("查無真實數據，使用模擬數據繪製圖表...")
    up_count = 650
    down_count = 820
    unchanged_count = 130

# 準備繪圖資料
labels = [f'上漲家數 ({up_count})', f'下跌家數 ({down_count})', f'平盤家數 ({unchanged_count})']
sizes = [up_count, down_count, unchanged_count]
# 台灣股市習慣：紅色上漲、綠色下跌、灰色平盤
colors = ['#ff4d4f', '#52c41a', '#d9d9d9'] 
explode = (0.05, 0, 0)  # 稍微突顯上漲區塊

# 繪製圓餅圖
fig, ax = plt.subplots(figsize=(8, 6))
wedges, texts, autotexts = ax.pie(
    sizes, 
    explode=explode,
    labels=labels, 
    colors=colors, 
    autopct='%1.1f%%', 
    shadow=True, 
    startangle=140,
    textprops=dict(fontsize=12)
)

ax.axis('equal')  # 使圓餅圖比例為正圓
plt.title('大盤多空結構比例圖', fontsize=16, fontweight='bold', pad=20)

# 儲存圖表
save_path = 'graph/6_1_market_breadth.png'
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"圖表已成功匯出至: {os.path.abspath(save_path)}")
