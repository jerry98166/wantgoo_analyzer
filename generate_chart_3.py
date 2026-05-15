# 匯入 os 模組，用於建立目錄與處理檔案路徑
import os
# 匯入 sqlite3 模組，用於與本地 SQLite 資料庫互動
import sqlite3
# 匯入 pandas 模組，用於高效處理與轉換結構化資料
import pandas as pd
# 匯入 plotly.express 模組，用於快速建立互動式圖表
import plotly.express as px

# 建立名為 'graph' 的目錄，若目錄已經存在，則不會拋出錯誤
os.makedirs('graph', exist_ok=True)

# 設定要讀取的 SQLite 資料庫相對路徑
db_path = 'backend/historical_data.db'
# 初始化布林變數，用來標記是否成功取得所需資料
data_found = False

# 檢查資料庫檔案是否存在於指定路徑
if os.path.exists(db_path):
    try:
        # 連線至資料庫
        conn = sqlite3.connect(db_path)
        # 取得游標物件，以執行 SQL 指令
        cursor = conn.cursor()
        
        # 執行 SQL 語法，找出 daily_market_data 資料表中的最大(最新)日期
        cursor.execute("SELECT MAX(Date) FROM daily_market_data")
        # 取得查詢結果中的最新日期字串
        latest_date = cursor.fetchone()[0]
        
        # 如果成功取得最新日期，則根據該日期取得相關資料
        if latest_date:
            # 讀取股票代號、名稱、外資買賣超、漲跌幅與成交值，並存為 DataFrame
            df = pd.read_sql(f"SELECT Stock_ID, Stock_Name, Foreign_Net, Change_Pct, Turnover_Value FROM daily_market_data WHERE Date = '{latest_date}'", conn)
            # 檢查取回的資料是否不為空
            if not df.empty:
                data_found = True
                
        # 關閉資料庫連線以釋放資源
        conn.close()
    except Exception as e:
        # 捕捉並印出讀取資料庫時可能發生的任何異常
        print(f"無法讀取資料庫: {e}")

# 若順利取得資料，則開始進行資料處理與繪圖
if data_found:
    # --- 資料前處理 ---
    # 處理可能的缺失值或非數值資料。將 Foreign_Net 轉換為數值型別，若有轉換錯誤則轉為 NaN，最後補 0
    df['Foreign_Net'] = pd.to_numeric(df['Foreign_Net'], errors='coerce').fillna(0)
    # 將 Change_Pct (漲跌幅) 轉換為數值型別，錯誤轉為 NaN 後補 0
    df['Change_Pct'] = pd.to_numeric(df['Change_Pct'], errors='coerce').fillna(0)
    # 將 Turnover_Value (成交值) 轉換為數值型別，錯誤轉為 NaN 後補 0
    df['Turnover_Value'] = pd.to_numeric(df['Turnover_Value'], errors='coerce').fillna(0)
    
    # 為了讓圖表更清晰，排除成交量過小或異常值，這裡只篩選出成交值前 300 名的股票
    df_top = df.nlargest(300, 'Turnover_Value').copy()
    
    # --- 建立動態氣泡圖 (Scatter Bubble Chart) ---
    # X軸: 外資買賣超, Y軸: 漲跌幅, 氣泡大小: 成交值, 顏色: 根據漲跌幅決定狀態 (上漲/下跌/平盤)
    
    # 定義一個輔助函式，根據數值大於 0、小於 0 還是等於 0 來回傳對應的中文狀態
    def get_color(val):
        if val > 0:
            return '上漲'
        elif val < 0:
            return '下跌'
        else:
            return '平盤'
            
    # 將函式應用到 Change_Pct 欄位，建立一個新欄位 '漲跌狀態' 用於分類
    df_top['漲跌狀態'] = df_top['Change_Pct'].apply(get_color)
    
    # 使用 plotly express 繪製散佈圖 (在此以氣泡圖形式呈現)
    fig = px.scatter(
        df_top,
        x='Foreign_Net',       # X軸設定為外資買賣超
        y='Change_Pct',        # Y軸設定為漲跌幅
        size='Turnover_Value', # 氣泡大小對應成交值
        color='漲跌狀態',        # 依據漲跌狀態給予不同顏色
        # 明確指定各狀態對應的顏色，符合台股紅漲綠跌習慣
        color_discrete_map={'上漲': '#ff4d4f', '下跌': '#52c41a', '平盤': '#d9d9d9'},
        hover_name='Stock_Name', # 滑鼠懸停時顯示的標題為股票名稱
        # 設定滑鼠懸停時顯示的詳細資料與格式
        hover_data={'Stock_ID': True, 'Foreign_Net': ':.2f', 'Change_Pct': ':.2f', 'Turnover_Value': ':.0f'},
        # 設定圖表主標題，包含最新日期
        title=f'外資買賣超 vs. 漲跌幅分析 (成交值前300大) - {latest_date}',
        # 設定各欄位在圖表上顯示的標籤名稱
        labels={
            'Foreign_Net': '外資買賣超 (張)',
            'Change_Pct': '漲跌幅 (%)',
            'Turnover_Value': '成交值',
            '漲跌狀態': '狀態'
        },
        size_max=40, # 限制氣泡的最大尺寸，避免過大遮擋
        template='plotly_white' # 使用白底簡潔風格的樣式
    )
    
    # 增加兩條參考線，方便快速看出正負區域
    # 加入水平線 y=0 (漲跌幅 0%)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    # 加入垂直線 x=0 (外資買賣超 0 張)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # 設定圖表儲存路徑
    save_path_html = 'graph/6_3_interactive_scatter.html'
    save_path_png = 'graph/6_3_interactive_scatter.png'
    
    # 匯出為互動式的 HTML 網頁格式
    fig.write_html(save_path_html)
    # 匯出為靜態的 PNG 圖片格式，將尺寸放大 2 倍以提高解析度
    fig.write_image(save_path_png, scale=2)
    
    # 印出成功匯出的訊息及絕對路徑
    print(f"互動式圖表已成功匯出至: {os.path.abspath(save_path_html)}")
    print(f"圖表截圖已成功匯出至: {os.path.abspath(save_path_png)}")
else:
    # 若資料庫不存在或無資料則印出提示
    print("未找到資料。")
