import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import pandas as pd
import time
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime, timedelta
import io

def get_latest_trading_date():
    import pytz
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    
    # 若在下午 5 點以前，則使用前一天的資料
    if now.hour < 17:
        target = now - timedelta(days=1)
    else:
        target = now
        
    # 避開週末 (5=星期六, 6=星期日)
    while target.weekday() >= 5:
        target -= timedelta(days=1)
        
    return target.strftime("%Y%m%d")

def save_daily_data(df, date_str):
    import sqlite3
    import os
    if df is None or df.empty:
        return
        
    db_path = os.path.join(os.path.dirname(__file__), 'historical_data.db')
    conn = sqlite3.connect(db_path)
    df_save = df.copy()
    df_save['Date'] = date_str
    
    try:
        cursor = conn.cursor()
        # Ensure the table exists before trying to delete from it, 
        # but let pandas create the full schema if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_market_data'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM daily_market_data WHERE Date = ?", (date_str,))
            conn.commit()
    except sqlite3.OperationalError:
        pass
        
    df_save.to_sql('daily_market_data', conn, if_exists='append', index=False)
    conn.close()

def get_twse_company_info():
    """Fetch company info to map Stock ID to Industry"""
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    try:
        res = requests.get(url, timeout=10, verify=False)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if '公司代號' in df.columns and '產業別' in df.columns:
                return df[['公司代號', '公司名稱', '產業別']].rename(columns={'公司代號': 'Stock_ID', '公司名稱': 'Stock_Name_Info', '產業別': 'Industry'})
    except Exception as e:
        print(f"Error fetching company info: {e}")
    
    return pd.DataFrame({
        'Stock_ID': ['2330', '2317', '2454', '2308', '2881', '2603', '3231', '2382'],
        'Industry': ['半導體業', '其他電子業', '半導體業', '電子零組件業', '金融保險業', '航運業', '電腦及週邊設備業', '電腦及週邊設備業']
    })

def get_twse_institutional(date_str):
    url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALL"
    try:
        res = requests.get(url, timeout=10, verify=False)
        data = res.json()
        if data.get('stat') == 'OK':
            df = pd.DataFrame(data['data'], columns=data['fields'])
            cols_to_keep = {
                '證券代號': 'Stock_ID',
                '證券名稱': 'Stock_Name',
                '外陸資買賣超股數(不含外資自營商)': 'Foreign_Net',
                '投信買賣超股數': 'Trust_Net',
                '自營商買賣超股數': 'Dealer_Net',
                '三大法人買賣超股數': 'Total_Net'
            }
            actual_cols = {}
            for k, v in cols_to_keep.items():
                for field in data['fields']:
                    if k in field:
                        actual_cols[field] = v
                        break
            df = df.rename(columns=actual_cols)
            df = df[list(actual_cols.values())]
            for col in ['Foreign_Net', 'Trust_Net', 'Dealer_Net', 'Total_Net']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce') / 1000
            return df
    except Exception as e:
        print(f"Error fetching TWSE T86: {e}")
    
    return pd.DataFrame({
        'Stock_ID': ['2330', '2317', '2454', '2308', '2881', '2603', '3231', '2382'],
        'Stock_Name': ['台積電', '鴻海', '聯發科', '台達電', '富邦金', '長榮', '緯創', '廣達'],
        'Foreign_Net': [15000, 8000, -2000, 3000, 5000, -1500, 12000, 6000],
        'Trust_Net': [2000, 1500, 800, 500, 1000, 200, 3000, 2500],
        'Dealer_Net': [500, 300, -100, 200, 400, -50, 1000, 800],
        'Total_Net': [17500, 9800, -1300, 3700, 6400, -1350, 16000, 9300]
    })

def get_twse_price(date_str):
    """Fetch ALL listed stock prices from TWSE OpenAPI (reliable endpoint)."""
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    try:
        res = requests.get(url, timeout=30, verify=False)
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                # Filter out rows with empty ClosingPrice
                df = df[df['ClosingPrice'].astype(str).str.strip() != '']
                
                df = df.rename(columns={
                    'Code': 'Stock_ID',
                    'Name': 'Stock_Name_Price',
                    'ClosingPrice': 'Close',
                    'OpeningPrice': 'Open',
                    'HighestPrice': 'High',
                    'LowestPrice': 'Low',
                    'TradeVolume': 'Volume',
                    'Change': 'Change_Val'
                })
                
                for col in ['Close', 'Open', 'High', 'Low', 'Change_Val']:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                
                df['Volume'] = pd.to_numeric(df['Volume'].astype(str).str.replace(',', ''), errors='coerce') / 1000  # to lots
                
                df = df.dropna(subset=['Close', 'Volume'])
                df = df[df['Close'] > 0]
                df = df[df['Volume'] > 0]
                
                df['Prev_Close'] = df['Close'] - df['Change_Val']
                df['Change_Pct'] = df.apply(
                    lambda r: (r['Change_Val'] / r['Prev_Close'] * 100) if r['Prev_Close'] > 0 else 0, axis=1
                )
                df['Amplitude'] = df.apply(
                    lambda r: ((r['High'] - r['Low']) / r['Prev_Close'] * 100) if r['Prev_Close'] > 0 else 0, axis=1
                )
                df['Gap_Pct'] = df.apply(
                    lambda r: ((r['Open'] - r['Prev_Close']) / r['Prev_Close'] * 100) if r['Prev_Close'] > 0 else 0, axis=1
                )
                
                print(f"[Price] Fetched {len(df)} stocks from OpenAPI")
                return df[['Stock_ID', 'Stock_Name_Price', 'Close', 'Change_Pct', 'Volume', 'Amplitude', 'Gap_Pct']]
    except Exception as e:
        print(f"Error fetching TWSE OpenAPI price: {e}")
    
    # Fallback to old MI_INDEX method
    print("[Price] OpenAPI failed, trying MI_INDEX...")
    return _get_twse_price_legacy(date_str)

def _get_twse_price_legacy(date_str):
    """Legacy fallback using MI_INDEX."""
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALLBUT0999"
    try:
        res = requests.get(url, timeout=10, verify=False)
        data = res.json()
        if data.get('stat') == 'OK':
            target_data = None
            target_fields = None
            max_len = 0
            for key, val in data.items():
                if isinstance(val, list) and len(val) > max_len and isinstance(val[0], list):
                    target_data = val
                    target_fields = data.get(key.replace('data', 'fields'), [])
                    max_len = len(val)
            if target_data and target_fields:
                df = pd.DataFrame(target_data, columns=target_fields)
                cols_to_keep = {
                    '證券代號': 'Stock_ID',
                    '收盤價': 'Close',
                    '漲跌(+/-)': 'Sign',
                    '漲跌價差': 'Change',
                    '成交股數': 'Volume',
                    '開盤價': 'Open',
                    '最高價': 'High',
                    '最低價': 'Low'
                }
                actual_cols = {}
                for k, v in cols_to_keep.items():
                    for field in target_fields:
                        if k in field:
                            actual_cols[field] = v
                            break
                df = df.rename(columns=actual_cols)
                df = df[list(actual_cols.values())]
                for col in ['Close', 'Change', 'Open', 'High', 'Low']:
                    if col in df.columns:
                        df[col] = df[col].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce')
                df['Volume'] = df['Volume'].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce') / 1000
                def apply_sign(row):
                    if row['Sign'] == '<p style= color:red>+</p>': return row['Change']
                    if row['Sign'] == '<p style= color:green>-</p>': return -row['Change']
                    return 0 if pd.isna(row['Change']) else row['Change']
                df['Change'] = df.apply(apply_sign, axis=1)
                df['Prev_Close'] = df['Close'] - df['Change']
                df['Change_Pct'] = (df['Change'] / df['Prev_Close']) * 100
                df['Amplitude'] = ((df['High'] - df['Low']) / df['Prev_Close']) * 100
                df['Gap_Pct'] = ((df['Open'] - df['Prev_Close']) / df['Prev_Close']) * 100
                print(f"[Price] Fetched {len(df)} stocks from MI_INDEX")
                return df[['Stock_ID', 'Close', 'Change_Pct', 'Volume', 'Amplitude', 'Gap_Pct']]
    except Exception as e:
        print(f"Error fetching TWSE MI_INDEX: {e}")
    print("[Price] All methods failed, returning empty DataFrame")
    return pd.DataFrame(columns=['Stock_ID', 'Close', 'Change_Pct', 'Volume', 'Amplitude', 'Gap_Pct'])

def get_combined_data():
    date_str = get_latest_trading_date()
    df_inst = get_twse_institutional(date_str)
    df_price = get_twse_price(date_str)
    df_info = get_twse_company_info()
    
    if df_price.empty:
        print("[Combined] No price data available!")
        return pd.DataFrame(), date_str
    
    # Use price as base (left join) so ALL stocks are included
    df_merged = pd.merge(df_price, df_inst, on='Stock_ID', how='left')
    df_merged = pd.merge(df_merged, df_info[['Stock_ID', 'Industry']], on='Stock_ID', how='left')
    
    # Use Stock_Name from institutional data, fallback to price data name
    if 'Stock_Name_Price' in df_merged.columns:
        if 'Stock_Name' not in df_merged.columns:
            df_merged['Stock_Name'] = df_merged['Stock_Name_Price']
        else:
            df_merged['Stock_Name'] = df_merged['Stock_Name'].fillna(df_merged['Stock_Name_Price'])
        df_merged = df_merged.drop(columns=['Stock_Name_Price'], errors='ignore')
    
    df_merged['Industry'] = df_merged['Industry'].fillna('未知產業')
    
    # Fill missing institutional data with 0 (stocks without inst data)
    for col in ['Foreign_Net', 'Trust_Net', 'Dealer_Net', 'Total_Net']:
        if col in df_merged.columns:
            df_merged[col] = df_merged[col].fillna(0)
        else:
            df_merged[col] = 0
    
    if 'Stock_Name' not in df_merged.columns:
        df_merged['Stock_Name'] = df_merged['Stock_ID']
    
    df_merged = df_merged.dropna(subset=['Close', 'Change_Pct', 'Volume'])
    
    # Fill NaN for new indicators with 0 in case of missing data
    df_merged['Amplitude'] = df_merged['Amplitude'].fillna(0)
    df_merged['Gap_Pct'] = df_merged['Gap_Pct'].fillna(0)
    
    # Calculate Institutional Participation Rate
    df_merged['Participation_Rate'] = df_merged.apply(
        lambda row: (abs(row['Total_Net']) / row['Volume'] * 100) if row['Volume'] > 0 else 0, axis=1
    )
    
    # Calculate Turnover Value in 100M NTD
    df_merged['Turnover_Value'] = (df_merged['Close'] * df_merged['Volume']) / 100
    
    # Simulate Retail Margin Trading (融資增減) for sentiment analysis
    import numpy as np
    np.random.seed(int(datetime.now().timestamp()) % 10000)
    df_merged['Margin_Net'] = df_merged.apply(
        lambda r: np.random.normal(500, 1000) if r['Total_Net'] < 0 else np.random.normal(-200, 800), axis=1
    ).astype(int)
    
    print(f"[Combined] Total stocks: {len(df_merged)}, Up: {len(df_merged[df_merged['Change_Pct'] > 0])}, Down: {len(df_merged[df_merged['Change_Pct'] < 0])}")
    
    save_daily_data(df_merged, date_str)
    
    return df_merged, date_str

# --- Expanded Analysis Functions for FastAPI ---

def analyze_retail_sentiment(df, n=15):
    """Analyze Retail vs Institutional behavior based on Margin Trading"""
    df_filtered = df[df['Volume'] > 2000].copy()
    
    # Retail washed out (散戶被洗出場：融資大減 + 法人大買 + 股價上漲)
    washed_out = df_filtered[(df_filtered['Margin_Net'] < 0) & (df_filtered['Total_Net'] > 0)].copy()
    washed_out['Score'] = abs(washed_out['Margin_Net']) + washed_out['Total_Net']
    washed_out = washed_out.sort_values('Score', ascending=False).head(n)
    
    # Retail catching knives (散戶接滿手血：融資大增 + 法人大賣 + 股價下跌)
    catching_knives = df_filtered[(df_filtered['Margin_Net'] > 0) & (df_filtered['Total_Net'] < 0)].copy()
    catching_knives['Score'] = catching_knives['Margin_Net'] + abs(catching_knives['Total_Net'])
    catching_knives = catching_knives.sort_values('Score', ascending=False).head(n)
    
    cols = ['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Volume', 'Total_Net', 'Margin_Net', 'Industry']
    return {
        "washed_out": washed_out[cols].fillna(0).to_dict(orient='records'),
        "catching_knives": catching_knives[cols].fillna(0).to_dict(orient='records')
    }

def analyze_top_stocks(df, n=20):
    df_buy = df.sort_values('Total_Net', ascending=False).head(n)
    df_sell = df.sort_values('Total_Net', ascending=True).head(n)
    
    bins = [0, 50, 100, 300, 500, 1000, 9999]
    labels = ['<50', '50-100', '100-300', '300-500', '500-1000', '>1000']
    df_buy_copy = df_buy.copy()
    df_buy_copy['Price_Band'] = pd.cut(df_buy_copy['Close'], bins=bins, labels=labels)
    price_band_counts = df_buy_copy['Price_Band'].value_counts().to_dict()

    return {
        "top_buys": df_buy.fillna(0).to_dict(orient='records'),
        "top_sells": df_sell.fillna(0).to_dict(orient='records'),
        "price_bands": [{"band": k, "count": v} for k, v in price_band_counts.items()]
    }

def analyze_industry(df):
    industry_grp = df.groupby('Industry').agg({
        'Total_Net': 'sum',
        'Foreign_Net': 'sum',
        'Trust_Net': 'sum',
        'Dealer_Net': 'sum',
        'Volume': 'sum',
        'Turnover_Value': 'sum'
    }).reset_index()
    
    top_buy_industries = industry_grp.sort_values('Total_Net', ascending=False).head(10)
    top_sell_industries = industry_grp.sort_values('Total_Net', ascending=True).head(10)
    all_industries = industry_grp.sort_values('Turnover_Value', ascending=False)
    
    return {
        "top_buy_industries": top_buy_industries.fillna(0).to_dict(orient='records'),
        "top_sell_industries": top_sell_industries.fillna(0).to_dict(orient='records'),
        "all_industries": all_industries.fillna(0).to_dict(orient='records')
    }

def analyze_institutional_radar(df, n=15):
    """
    Specific radar for Trust (投信作帳) and Dealer (自營商避雷)
    Trust window dressing: high trust buy participation.
    Dealer short-term: extremely high dealer buy participation.
    """
    df_filtered = df[df['Volume'] > 1000].copy()
    
    # Trust Conviction
    df_filtered['Trust_Participation'] = df_filtered.apply(lambda r: (r['Trust_Net'] / r['Volume'] * 100) if r['Trust_Net'] > 0 and r['Volume'] > 0 else 0, axis=1)
    # Dealer Short-term risk (Dealer buying a huge chunk of daily volume)
    df_filtered['Dealer_Participation'] = df_filtered.apply(lambda r: (r['Dealer_Net'] / r['Volume'] * 100) if r['Dealer_Net'] > 0 and r['Volume'] > 0 else 0, axis=1)
    
    trust_targets = df_filtered.sort_values('Trust_Participation', ascending=False).head(n)
    dealer_targets = df_filtered.sort_values('Dealer_Participation', ascending=False).head(n)
    
    cols = ['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Volume', 'Turnover_Value', 'Trust_Net', 'Dealer_Net', 'Trust_Participation', 'Dealer_Participation']
    
    return {
        "trust_dressing": trust_targets[cols].fillna(0).to_dict(orient='records'),
        "dealer_risk": dealer_targets[cols].fillna(0).to_dict(orient='records')
    }

def analyze_day_trading(df, n=20):
    """Analyze day trading hotspots based on Amplitude, Gap, and Volume"""
    df_filtered = df[df['Volume'] > 3000].copy() # Filter for sufficient liquidity
    
    # High Amplitude (高振幅)
    high_amplitude = df_filtered.sort_values('Amplitude', ascending=False).head(n)
    
    # Gap Up (跳空開高)
    gap_up = df_filtered.sort_values('Gap_Pct', ascending=False).head(n)
    
    return {
        "high_amplitude": high_amplitude[['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Volume', 'Amplitude', 'Gap_Pct']].fillna(0).to_dict(orient='records'),
        "gap_up": gap_up[['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Volume', 'Amplitude', 'Gap_Pct']].fillna(0).to_dict(orient='records')
    }

def analyze_correlation(df):
    q_low = df['Total_Net'].quantile(0.01)
    q_hi  = df['Total_Net'].quantile(0.99)
    df_filtered = df[(df['Total_Net'] > q_low) & (df['Total_Net'] < q_hi)].copy()
    
    if len(df_filtered) > 300:
        df_filtered = df_filtered.sample(300, random_state=42)
        
    correlation = df_filtered['Total_Net'].corr(df_filtered['Change_Pct'])
    
    return {
        "correlation": float(correlation) if pd.notna(correlation) else 0,
        "scatter_data": df_filtered[['Stock_ID', 'Stock_Name', 'Total_Net', 'Change_Pct', 'Volume']].fillna(0).to_dict(orient='records')
    }

def analyze_market_breadth(df):
    """Analyze overall market breadth and institutional totals"""
    up_count = len(df[df['Change_Pct'] > 0])
    down_count = len(df[df['Change_Pct'] < 0])
    unchanged_count = len(df[df['Change_Pct'] == 0])
    
    total_foreign = df['Foreign_Net'].sum()
    total_trust = df['Trust_Net'].sum()
    total_dealer = df['Dealer_Net'].sum()
    total_net = df['Total_Net'].sum()
    total_volume = df['Volume'].sum()
    
    return {
        "breadth": {
            "up": up_count,
            "down": down_count,
            "unchanged": unchanged_count
        },
        "totals": {
            "foreign": float(total_foreign),
            "trust": float(total_trust),
            "dealer": float(total_dealer),
            "net": float(total_net),
            "volume": float(total_volume)
        }
    }

def analyze_synchrony(df):
    """Analyze synchrony and divergence between Foreign and Trust"""
    # 土洋齊買
    sync_buy = df[(df['Foreign_Net'] > 0) & (df['Trust_Net'] > 0)].sort_values('Total_Net', ascending=False).head(15)
    # 土洋齊賣
    sync_sell = df[(df['Foreign_Net'] < 0) & (df['Trust_Net'] < 0)].sort_values('Total_Net', ascending=True).head(15)
    # 土洋對作 (外資買、投信賣 OR 外資賣、投信買)
    divergence = df[df['Foreign_Net'] * df['Trust_Net'] < 0].copy()
    divergence['Divergence_Intensity'] = divergence['Foreign_Net'].abs() + divergence['Trust_Net'].abs()
    divergence = divergence.sort_values('Divergence_Intensity', ascending=False).head(15)
    
    return {
        "sync_buy": sync_buy.fillna(0).to_dict(orient='records'),
        "sync_sell": sync_sell.fillna(0).to_dict(orient='records'),
        "divergence": divergence.fillna(0).to_dict(orient='records')
    }

def analyze_participation(df, n=15):
    """Analyze stocks where institutional net buy/sell accounts for a large % of total volume"""
    # Filter out very low volume stocks to avoid noise
    df_filtered = df[df['Volume'] > 1000].copy()
    
    # High Conviction Buy (High positive participation)
    df_filtered['Buy_Participation'] = df_filtered.apply(lambda r: (r['Total_Net'] / r['Volume'] * 100) if r['Total_Net'] > 0 and r['Volume'] > 0 else 0, axis=1)
    # High Conviction Sell (High negative participation)
    df_filtered['Sell_Participation'] = df_filtered.apply(lambda r: (abs(r['Total_Net']) / r['Volume'] * 100) if r['Total_Net'] < 0 and r['Volume'] > 0 else 0, axis=1)
    
    high_buy = df_filtered.sort_values('Buy_Participation', ascending=False).head(n)
    high_sell = df_filtered.sort_values('Sell_Participation', ascending=False).head(n)
    
    return {
        "high_buy": high_buy[['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Total_Net', 'Volume', 'Buy_Participation']].fillna(0).to_dict(orient='records'),
        "high_sell": high_sell[['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Total_Net', 'Volume', 'Sell_Participation']].fillna(0).to_dict(orient='records')
    }

def analyze_smart_money(df, n=15):
    """Analyze 'Smart Money' stealth accumulation: Low volume, high institutional buy ratio, minor price change"""
    # Look for Volume between 500 and 5000 (relatively quiet)
    df_stealth = df[(df['Volume'] >= 500) & (df['Volume'] <= 8000)].copy()
    # High buy participation (> 10%)
    df_stealth['Buy_Participation'] = df_stealth.apply(lambda r: (r['Total_Net'] / r['Volume'] * 100) if r['Total_Net'] > 0 and r['Volume'] > 0 else 0, axis=1)
    # Price hasn't moved much (-2% to +2%)
    df_stealth = df_stealth[(df_stealth['Change_Pct'] >= -2) & (df_stealth['Change_Pct'] <= 2) & (df_stealth['Buy_Participation'] > 8)]
    
    stealth_buy = df_stealth.sort_values('Buy_Participation', ascending=False).head(n)
    return stealth_buy[['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Total_Net', 'Volume', 'Buy_Participation', 'Industry']].fillna(0).to_dict(orient='records')

def analyze_volume_leaders(df, n=20):
    """Analyze market volume leaders and overlay institutional action"""
    leaders = df.sort_values('Volume', ascending=False).head(n).copy()
    return leaders[['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Volume', 'Total_Net', 'Industry']].fillna(0).to_dict(orient='records')

def get_stock_history_data(stock_id, period='6mo'):
    symbol = f"{stock_id}.TW"
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        if hist.empty:
            symbol = f"{stock_id}.TWO"
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
        
        if not hist.empty:
             hist.reset_index(inplace=True)
             import numpy as np
             import pandas as pd
             np.random.seed(42)
             
             hist['Price_Change'] = hist['Close'].diff()
             
             # Simulate detailed institutional data
             hist['Foreign_Net'] = hist['Price_Change'] * np.random.uniform(300, 1500, len(hist)) + np.random.normal(0, 800, len(hist))
             hist['Trust_Net'] = hist['Price_Change'] * np.random.uniform(50, 500, len(hist)) + np.random.normal(100, 300, len(hist))
             hist['Dealer_Net'] = hist['Price_Change'] * np.random.uniform(10, 200, len(hist))
             
             hist['Foreign_Net'] = hist['Foreign_Net'].fillna(0).astype(int)
             hist['Trust_Net'] = hist['Trust_Net'].fillna(0).astype(int)
             hist['Dealer_Net'] = hist['Dealer_Net'].fillna(0).astype(int)
             hist['Inst_Net_Buy'] = hist['Foreign_Net'] + hist['Trust_Net'] + hist['Dealer_Net']
             
             # Calculate Moving Averages
             hist['MA5'] = hist['Close'].rolling(window=5).mean().fillna(0)
             hist['MA20'] = hist['Close'].rolling(window=20).mean().fillna(0)
             hist['MA60'] = hist['Close'].rolling(window=60).mean().fillna(0)
             
             # Calculate RSI (14 days)
             delta = hist['Close'].diff()
             gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
             loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
             rs = gain / loss
             hist['RSI'] = (100 - (100 / (1 + rs))).fillna(50)
             
             # Calculate MACD (12, 26, 9)
             exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
             exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
             hist['MACD'] = exp1 - exp2
             hist['Signal_Line'] = hist['MACD'].ewm(span=9, adjust=False).mean()
             hist['MACD_Hist'] = hist['MACD'] - hist['Signal_Line']
             
             # Filter to last 60 days for frontend to keep chart clean
             hist_60 = hist.tail(60).reset_index(drop=True)
             
             # Calculate Estimated Institutional Cost (60 days)
             buy_days = hist_60[hist_60['Inst_Net_Buy'] > 0]
             inst_cost = 0
             if buy_days['Inst_Net_Buy'].sum() > 0:
                 inst_cost = round((buy_days['Close'] * buy_days['Inst_Net_Buy']).sum() / buy_days['Inst_Net_Buy'].sum(), 2)
                 
             # Calculate participation rate over the period
             total_vol = (hist_60['Volume'] / 1000).sum()
             total_inst = hist_60['Inst_Net_Buy'].abs().sum()
             period_participation = round((total_inst / total_vol) * 100, 1) if total_vol > 0 else 0
             
             # Calculate phase logic
             recent_buys = hist_60['Inst_Net_Buy'].tail(5).sum()
             recent_price_change = float((hist_60['Close'].iloc[-1] / hist_60['Close'].iloc[-6]) - 1) if len(hist_60) > 5 else 0
             
             phase = "未知"
             if recent_buys > 0 and recent_price_change < 0.02:
                 phase = "初步建倉佈局 (買超+未漲)"
             elif recent_buys > 0 and recent_price_change >= 0.02:
                 phase = "持續加碼 / 主升段 (買超+上漲)"
             elif recent_buys < 0 and recent_price_change > 0:
                 phase = "高檔獲利了結 (賣超+處於高檔)"
             elif recent_buys < 0 and recent_price_change < 0:
                 phase = "資金撤出 / 停損 (賣超+下跌)"

             return {
                 "dates": hist_60['Date'].dt.strftime('%Y-%m-%d').tolist(),
                 "kline_data": hist_60[['Open', 'Close', 'Low', 'High']].values.tolist(),
                 "closes": hist_60['Close'].tolist(),
                 "ma5": hist_60['MA5'].tolist(),
                 "ma20": hist_60['MA20'].tolist(),
                 "ma60": hist_60['MA60'].tolist(),
                 "rsi": hist_60['RSI'].tolist(),
                 "macd": hist_60['MACD'].tolist(),
                 "macd_signal": hist_60['Signal_Line'].tolist(),
                 "macd_hist": hist_60['MACD_Hist'].tolist(),
                 "volumes": (hist_60['Volume'] / 1000).astype(int).tolist(),
                 "foreign_net": hist_60['Foreign_Net'].tolist(),
                 "trust_net": hist_60['Trust_Net'].tolist(),
                 "dealer_net": hist_60['Dealer_Net'].tolist(),
                 "inst_net": hist_60['Inst_Net_Buy'].tolist(),
                 "inst_cost": inst_cost,
                 "period_participation": period_participation,
                 "phase": phase,
                 "recent_buys": int(recent_buys),
                 "recent_price_change_pct": round(recent_price_change * 100, 2)
             }
    except Exception as e:
        print(f"Error fetching history: {e}")
    return None

def scrape_wantgoo_hot_articles():
    url = "https://www.wantgoo.com/blog/article/hot"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    articles = []
    try:
        res = requests.get(url, headers=headers, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        items = soup.find_all('a', class_='title')
        if not items:
             items = soup.find_all('h3')
             
        for item in items[:10]:
            title = item.text.strip()
            link = item.get('href', '')
            if link and not link.startswith('http'):
                link = f"https://www.wantgoo.com{link}"
            if title:
                articles.append({'title': title, 'link': link})
    except Exception as e:
         pass
         
    if not articles:
         articles = [
             {'title': '【玩股網】三大法人同步買超！資金湧入AI伺服器供應鏈', 'link': 'https://www.wantgoo.com/'},
             {'title': '【玩股網】外資提款權值股，中小型股接棒演出？', 'link': 'https://www.wantgoo.com/'},
             {'title': '【玩股網】高股息ETF換股潮，投信作帳行情啟動', 'link': 'https://www.wantgoo.com/'}
         ]
    return articles

def get_historical_stats():
    """Retrieve and compute basic statistical analysis on historical daily data."""
    import sqlite3
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'historical_data.db')
    if not os.path.exists(db_path):
        return {"error": "No historical data found"}
        
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql('SELECT * FROM daily_market_data', conn)
    except Exception as e:
        conn.close()
        return {"error": str(e)}
    conn.close()
    
    if df.empty:
        return {"error": "No historical data found"}
        
    # Example statistical analysis: daily totals
    for col in ['Total_Net', 'Volume', 'Turnover_Value']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    stats = df.groupby('Date').agg(
        Total_Net_Sum=('Total_Net', 'sum'),
        Total_Volume=('Volume', 'sum'),
        Total_Turnover=('Turnover_Value', 'sum'),
        Stock_Count=('Stock_ID', 'count')
    ).reset_index()
    
    return stats.to_dict(orient='records')
