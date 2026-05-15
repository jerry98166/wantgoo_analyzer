# 匯入 os 模組，用於建立目錄或處理檔案路徑
import os
# 匯入 sqlite3 模組，用於與本地 SQLite 資料庫互動
import sqlite3
# 匯入 pandas 模組，用於資料處理與分析
import pandas as pd
# 匯入 plotly.graph_objects 模組，用於建立客製化、複雜的互動式圖表
import plotly.graph_objects as go

# 建立名為 'graph' 的目錄，若已存在則不報錯
os.makedirs('graph', exist_ok=True)

# 定義要讀取的資料庫檔案相對路徑
db_path = 'backend/historical_data.db'
# 初始化標記變數，用於判斷是否找到有效資料
data_found = False

# 檢查資料庫檔案是否存在
if os.path.exists(db_path):
    try:
        # 建立資料庫連線
        conn = sqlite3.connect(db_path)
        # 建立游標物件以執行 SQL 指令
        cursor = conn.cursor()
        
        # 查詢 daily_market_data 資料表中最近的日期
        cursor.execute("SELECT MAX(Date) FROM daily_market_data")
        # 提取最新日期
        latest_date = cursor.fetchone()[0]
        
        if latest_date:
            # 讀取該最新日期的特定欄位：代號、名稱、外資/投信/自營商買賣超、三大法人合計買賣超以及漲跌幅
            df = pd.read_sql(f"""
                SELECT Stock_ID, Stock_Name, Foreign_Net, Trust_Net, Dealer_Net, Total_Net, Change_Pct 
                FROM daily_market_data 
                WHERE Date = '{latest_date}'
            """, conn)
            # 如果讀取出的 DataFrame 不是空的，則代表有資料
            if not df.empty:
                data_found = True
                
        # 關閉資料庫連線
        conn.close()
    except Exception as e:
        # 印出讀取過程中發生的錯誤
        print(f"無法讀取資料庫: {e}")

# 若成功從資料庫獲取資料則開始處理和繪製圖表
if data_found:
    # --- 資料前處理 ---
    # 確保數值型別欄位均為正確的數字，若有非數值字串則轉為 NaN，隨後以 0 填補
    for col in ['Foreign_Net', 'Trust_Net', 'Dealer_Net', 'Total_Net', 'Change_Pct']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 取得三大法人買超合計 (Total_Net) 前 20 名的股票，建立新的 DataFrame 複本
    df_top20 = df.nlargest(20, 'Total_Net').copy()
    
    # 將 DataFrame 的列反轉
    # 因為 Plotly 的水平長條圖 (horizontal bar) 預設會將第一筆資料畫在最下方，
    # 反轉後可讓買超最大的股票顯示在最上方
    df_top20 = df_top20.iloc[::-1]
    
    # 建立一個新欄位 'Label'，組合股票代號和名稱，做為 Y 軸標籤使用
    df_top20['Label'] = df_top20['Stock_ID'].astype(str) + ' ' + df_top20['Stock_Name']
    
    # --- 建立互動式堆疊長條圖 (Stacked Bar Chart) ---
    # 初始化一個 Plotly 的 Figure 物件
    fig = go.Figure()
    
    # 加入外資買賣超的資料層 (Trace)
    fig.add_trace(go.Bar(
        y=df_top20['Label'],          # Y 軸設定為股票標籤
        x=df_top20['Foreign_Net'],    # X 軸設定為外資買賣超數量
        name='外資',                  # 圖例名稱
        orientation='h',              # 設定為水平長條圖 (horizontal)
        marker=dict(color='#1f77b4'), # 設定顏色為藍色
        customdata=df_top20['Change_Pct'], # 夾帶額外的漲跌幅資料，供懸停提示使用
        # 設定滑鼠懸停時顯示的 HTML 格式資訊
        hovertemplate="外資: %{x:,.0f} 張<br>當日漲跌: %{customdata:.2f}%<extra></extra>"
    ))
    
    # 加入投信買賣超的資料層
    fig.add_trace(go.Bar(
        y=df_top20['Label'],
        x=df_top20['Trust_Net'],
        name='投信',
        orientation='h',
        marker=dict(color='#ff7f0e'), # 設定顏色為橘色
        customdata=df_top20['Change_Pct'],
        hovertemplate="投信: %{x:,.0f} 張<br>當日漲跌: %{customdata:.2f}%<extra></extra>"
    ))
    
    # 加入自營商買賣超的資料層
    fig.add_trace(go.Bar(
        y=df_top20['Label'],
        x=df_top20['Dealer_Net'],
        name='自營商',
        orientation='h',
        marker=dict(color='#2ca02c'), # 設定顏色為綠色
        customdata=df_top20['Change_Pct'],
        hovertemplate="自營商: %{x:,.0f} 張<br>當日漲跌: %{customdata:.2f}%<extra></extra>"
    ))
    
    # --- 設定圖表整體版面配置 ---
    fig.update_layout(
        title=f'三大法人同買熱門股 (買超前20大) - {latest_date}', # 圖表標題
        barmode='stack',       # 設定長條圖模式為「堆疊」，各法人買超會疊加在一起
        xaxis_title='買賣超張數', # X 軸名稱
        yaxis_title='股票名稱',   # Y 軸名稱
        legend_title='法人身分',  # 圖例標題
        template='plotly_white', # 使用白底簡潔樣式
        height=700,            # 設定圖表高度，讓 20 檔股票有足夠空間顯示
        margin=dict(l=150)     # 增加左側 (left) 邊界空間，避免較長的股票名稱被截斷
    )
    
    # --- 儲存圖表 ---
    save_path_html = 'graph/6_4_institutional_stacked_bar.html'
    save_path_png = 'graph/6_4_institutional_stacked_bar.png'
    
    # 匯出互動式的 HTML 網頁
    fig.write_html(save_path_html)
    
    try:
        # 匯出靜態的 PNG 圖片，scale=2 可提升解析度
        fig.write_image(save_path_png, scale=2)
        print(f"圖表截圖已成功匯出至: {os.path.abspath(save_path_png)}")
    except Exception as e:
        # 若系統未安裝 kaleido 套件，將無法匯出圖片，並印出錯誤提示
        print(f"匯出 PNG 失敗，可能需要安裝 kaleido: {e}")
        
    print(f"互動式圖表已成功匯出至: {os.path.abspath(save_path_html)}")
else:
    # 如果找不到資料，輸出提示訊息
    print("未找到資料。")
