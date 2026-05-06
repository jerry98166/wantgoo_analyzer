import os
import sqlite3
import pandas as pd
import plotly.express as px

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
            df = pd.read_sql(f"SELECT Stock_ID, Stock_Name, Foreign_Net, Change_Pct, Turnover_Value FROM daily_market_data WHERE Date = '{latest_date}'", conn)
            if not df.empty:
                data_found = True
        conn.close()
    except Exception as e:
        print(f"無法讀取資料庫: {e}")

if data_found:
    # 資料前處理
    # 處理缺失值或非數值資料
    df['Foreign_Net'] = pd.to_numeric(df['Foreign_Net'], errors='coerce').fillna(0)
    df['Change_Pct'] = pd.to_numeric(df['Change_Pct'], errors='coerce').fillna(0)
    df['Turnover_Value'] = pd.to_numeric(df['Turnover_Value'], errors='coerce').fillna(0)
    
    # 篩選掉成交值過小或極端異常值的資料，讓圖表較為清晰
    # 例如：只顯示成交值前 300 名的股票
    df_top = df.nlargest(300, 'Turnover_Value').copy()
    
    # 建立動態氣泡圖 (Scatter Bubble Chart)
    # X軸: 外資買賣超, Y軸: 漲跌幅, 氣泡大小: 成交值, 顏色: 漲跌幅大小 (紅正綠負)
    
    # 新增一個欄位用來決定顏色類別
    def get_color(val):
        if val > 0:
            return '上漲'
        elif val < 0:
            return '下跌'
        else:
            return '平盤'
            
    df_top['漲跌狀態'] = df_top['Change_Pct'].apply(get_color)
    
    fig = px.scatter(
        df_top,
        x='Foreign_Net',
        y='Change_Pct',
        size='Turnover_Value',
        color='漲跌狀態',
        color_discrete_map={'上漲': '#ff4d4f', '下跌': '#52c41a', '平盤': '#d9d9d9'},
        hover_name='Stock_Name',
        hover_data={'Stock_ID': True, 'Foreign_Net': ':.2f', 'Change_Pct': ':.2f', 'Turnover_Value': ':.0f'},
        title=f'外資買賣超 vs. 漲跌幅分析 (成交值前300大) - {latest_date}',
        labels={
            'Foreign_Net': '外資買賣超 (張)',
            'Change_Pct': '漲跌幅 (%)',
            'Turnover_Value': '成交值',
            '漲跌狀態': '狀態'
        },
        size_max=40, # 設定氣泡最大尺寸
        template='plotly_white'
    )
    
    # 增加 x=0, y=0 的參考線
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # 儲存為互動式 HTML 檔案與靜態圖檔 (供預覽/報告使用)
    save_path_html = 'graph/6_3_interactive_scatter.html'
    save_path_png = 'graph/6_3_interactive_scatter.png'
    fig.write_html(save_path_html)
    fig.write_image(save_path_png, scale=2)
    print(f"互動式圖表已成功匯出至: {os.path.abspath(save_path_html)}")
    print(f"圖表截圖已成功匯出至: {os.path.abspath(save_path_png)}")
else:
    print("未找到資料。")
