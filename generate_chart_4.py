import os
import sqlite3
import pandas as pd
import plotly.graph_objects as go

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
            df = pd.read_sql(f"""
                SELECT Stock_ID, Stock_Name, Foreign_Net, Trust_Net, Dealer_Net, Total_Net, Change_Pct 
                FROM daily_market_data 
                WHERE Date = '{latest_date}'
            """, conn)
            if not df.empty:
                data_found = True
        conn.close()
    except Exception as e:
        print(f"無法讀取資料庫: {e}")

if data_found:
    # 資料前處理
    for col in ['Foreign_Net', 'Trust_Net', 'Dealer_Net', 'Total_Net', 'Change_Pct']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 取三大法人買超合計前 20 名的股票
    df_top20 = df.nlargest(20, 'Total_Net').copy()
    
    # 為了讓圖表由上到下顯示從最大到最小，需要將 DataFrame 反轉 (Plotly horizontal bar 預設從下往上疊)
    df_top20 = df_top20.iloc[::-1]
    
    # 建立股票標籤 (代號 + 名稱)
    df_top20['Label'] = df_top20['Stock_ID'].astype(str) + ' ' + df_top20['Stock_Name']
    
    # 建立互動式堆疊長條圖 (Stacked Bar Chart)
    fig = go.Figure()
    
    # 外資買賣超
    fig.add_trace(go.Bar(
        y=df_top20['Label'],
        x=df_top20['Foreign_Net'],
        name='外資',
        orientation='h',
        marker=dict(color='#1f77b4'),
        customdata=df_top20['Change_Pct'],
        hovertemplate="外資: %{x:,.0f} 張<br>當日漲跌: %{customdata:.2f}%<extra></extra>"
    ))
    
    # 投信買賣超
    fig.add_trace(go.Bar(
        y=df_top20['Label'],
        x=df_top20['Trust_Net'],
        name='投信',
        orientation='h',
        marker=dict(color='#ff7f0e'),
        customdata=df_top20['Change_Pct'],
        hovertemplate="投信: %{x:,.0f} 張<br>當日漲跌: %{customdata:.2f}%<extra></extra>"
    ))
    
    # 自營商買賣超
    fig.add_trace(go.Bar(
        y=df_top20['Label'],
        x=df_top20['Dealer_Net'],
        name='自營商',
        orientation='h',
        marker=dict(color='#2ca02c'),
        customdata=df_top20['Change_Pct'],
        hovertemplate="自營商: %{x:,.0f} 張<br>當日漲跌: %{customdata:.2f}%<extra></extra>"
    ))
    
    # 設定圖表版面
    fig.update_layout(
        title=f'三大法人同買熱門股 (買超前20大) - {latest_date}',
        barmode='stack',
        xaxis_title='買賣超張數',
        yaxis_title='股票名稱',
        legend_title='法人身分',
        template='plotly_white',
        height=700,
        margin=dict(l=150) # 預留左側空間給較長的股票名稱
    )
    
    # 儲存為互動式 HTML 檔案與靜態圖檔
    save_path_html = 'graph/6_4_institutional_stacked_bar.html'
    save_path_png = 'graph/6_4_institutional_stacked_bar.png'
    fig.write_html(save_path_html)
    try:
        fig.write_image(save_path_png, scale=2)
        print(f"圖表截圖已成功匯出至: {os.path.abspath(save_path_png)}")
    except Exception as e:
        print(f"匯出 PNG 失敗，可能需要安裝 kaleido: {e}")
        
    print(f"互動式圖表已成功匯出至: {os.path.abspath(save_path_html)}")
else:
    print("未找到資料。")
