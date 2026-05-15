import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import patterns

# 全域變數快取每日合併資料
df_combined = None
last_update_date = None

def _to_number(value):
    return pd.to_numeric(str(value).replace(',', '').strip(), errors='coerce')

def _previous_weekday(date_str):
    target = datetime.strptime(date_str, "%Y%m%d") - timedelta(days=1)
    while target.weekday() >= 5:
        target -= timedelta(days=1)
    return target.strftime("%Y%m%d")

def _safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default

def _score_series(series):
    numeric = pd.to_numeric(series, errors='coerce').fillna(0)
    min_value = numeric.min()
    max_value = numeric.max()
    if max_value == min_value:
        return pd.Series([50.0] * len(numeric), index=numeric.index)
    return ((numeric - min_value) / (max_value - min_value) * 100).clip(0, 100)

def get_latest_trading_date():
    import pytz
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    
    if now.hour < 17:
        target = now - timedelta(days=1)
    else:
        target = now
        
    while target.weekday() >= 5:
        target -= timedelta(days=1)
        
    return target.strftime("%Y%m%d")

def fetch_all_daily_data():
    """ 獲取並合併當日所有的報價、法人、產業與融資券資料 """
    global df_combined, last_update_date
    expected_date = get_latest_trading_date()
    
    # 1. 取得價格資料 (OpenAPI)
    url_price = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    df_price = pd.DataFrame()
    actual_data_date = None  # 從 API 回傳資料中提取真實日期
    try:
        res = requests.get(url_price, timeout=30, verify=False)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df = df[df['ClosingPrice'].astype(str).str.strip() != '']
            
            # 從 OpenAPI 回傳的 Date 欄位提取真實資料日期 (民國轉西元)
            if 'Date' in df.columns and len(df) > 0:
                raw_date = str(df.iloc[0]['Date']).strip()
                try:
                    # 民國格式 1150514 -> 西元 20260514
                    roc_year = int(raw_date[:3])
                    western_year = roc_year + 1911
                    actual_data_date = f"{western_year}{raw_date[3:]}"
                    print(f"[Price] OpenAPI actual data date: {actual_data_date} (raw: {raw_date})")
                except Exception:
                    print(f"[Price] Cannot parse date from OpenAPI: {raw_date}")
            
            df = df.rename(columns={
                'Code': 'Stock_ID',
                'Name': 'Stock_Name',
                'ClosingPrice': 'Close',
                'TradeVolume': 'Volume',
                'Change': 'Change_Val'
            })
            for col in ['Close', 'Change_Val']:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
            df['Volume'] = pd.to_numeric(df['Volume'].astype(str).str.replace(',', ''), errors='coerce') / 1000 
            df = df.dropna(subset=['Close', 'Volume'])
            df = df[df['Close'] > 0]
            df['Prev_Close'] = df['Close'] - df['Change_Val']
            df['Change_Pct'] = df.apply(lambda r: (r['Change_Val'] / r['Prev_Close'] * 100) if r['Prev_Close'] > 0 else 0, axis=1)
            # 粗估成交值 (百萬元) = (股價 * 成交量張數 * 1000) / 1,000,000 = (股價 * 張數) / 1000，這裡我們為了數字好看可直接算萬或百萬
            df['Turnover_Value'] = (df['Close'] * df['Volume']) / 100 # 以百萬元為單位
            df_price = df[['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Volume', 'Turnover_Value']]
            print(f"[Price] Fetched {len(df_price)} stocks")
    except Exception as e:
        print(f"Error fetching OpenAPI: {e}")

    # 使用真實資料日期（若能取得），否則使用預期日期
    # 確保 T86 和融資券用的日期與價格資料一致
    date_str = actual_data_date if actual_data_date else expected_date
    if actual_data_date and actual_data_date != expected_date:
        print(f"[WARNING] Date mismatch! Expected: {expected_date}, Actual from OpenAPI: {actual_data_date}")

    # 2. 取得三大法人資料 (T86) — 使用真實資料日期
    url_inst = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALL"
    df_inst = pd.DataFrame()
    try:
        res = requests.get(url_inst, timeout=10, verify=False)
        data = res.json()
        if data.get('stat') == 'OK':
            df = pd.DataFrame(data['data'], columns=data['fields'])
            cols_to_keep = {
                '證券代號': 'Stock_ID',
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
            df_inst = df
            print(f"[T86] Fetched {len(df_inst)} institutional records for {date_str}")
        else:
            print(f"[T86] No data for {date_str}: {data.get('stat')}")
    except Exception as e:
        print(f"Error fetching T86: {e}")

    # 3. 取得產業別 (OpenAPI)
    url_info = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    df_info = pd.DataFrame()
    INDUSTRY_MAP = {
        "01": "水泥工業", "02": "食品工業", "03": "塑膠工業", "04": "紡織纖維", "05": "電機機械",
        "06": "電器電纜", "08": "玻璃陶瓷", "09": "造紙工業", "10": "鋼鐵工業", "11": "橡膠工業",
        "12": "汽車工業", "14": "建材營造業", "15": "航運業", "16": "觀光餐旅", "17": "金融保險業",
        "18": "貿易百貨業", "20": "其他業", "21": "化學工業", "22": "生技醫療業", "23": "油電燃氣業",
        "24": "半導體業", "25": "電腦及週邊設備業", "26": "光電業", "27": "通信網路業", "28": "電子零組件業",
        "29": "電子通路業", "30": "資訊服務業", "31": "其他電子業", "35": "綠能環保業", "36": "數位雲端業",
        "37": "運動休閒業", "38": "居家生活業", "91": "存託憑證"
    }
    try:
        res = requests.get(url_info, timeout=10, verify=False)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if '公司代號' in df.columns and '產業別' in df.columns:
                df['產業別'] = df['產業別'].map(lambda x: INDUSTRY_MAP.get(x, x))
                df_info = df[['公司代號', '產業別']].rename(columns={'公司代號': 'Stock_ID', '產業別': 'Industry'})
    except Exception as e:
        print(f"Error fetching company info: {e}")

    # 4. 取得信用交易融資券 (MI_MARGN) — 使用真實資料日期
    df_margin = pd.DataFrame()
    query_date = date_str
    # 找最近有融資資料的一天 (最多往回推5天)
    for _ in range(6):
        url_margin = f"https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date={query_date}&selectType=ALL"
        try:
            res = requests.get(url_margin, timeout=10, verify=False)
            data = res.json()
            if data.get('stat') == 'OK':
                target_data = None
                for table in data.get('tables', []):
                    fields = table.get('fields', [])
                    rows = table.get('data', [])
                    if '代號' in fields and '名稱' in fields and rows:
                        target_data = rows
                        break
                if target_data:
                    records = []
                    for row in target_data:
                        if len(row) >= 14:
                            margin_prev = _to_number(row[5])
                            margin_today = _to_number(row[6])
                            records.append({
                                'Stock_ID': str(row[0]).strip(),
                                'Margin_Net': margin_today - margin_prev # 融資增減 (張)
                            })
                    df_margin = pd.DataFrame(records)
                    print(f"[Margin] Fetched {len(df_margin)} margin records for {query_date}")
                    break
        except Exception as e:
            print(f"Error fetching margin: {e}")
        query_date = _previous_weekday(query_date)

    # 5. 合併所有資料
    if df_price.empty:
        print("[WARNING] No price data fetched, skipping update.")
        df_combined = pd.DataFrame()
        return
        
    df_merged = df_price.copy()
    
    if not df_inst.empty:
        df_merged = pd.merge(df_merged, df_inst, on='Stock_ID', how='left')
    else:
        for col in ['Foreign_Net', 'Trust_Net', 'Dealer_Net', 'Total_Net']:
            df_merged[col] = 0

    if not df_info.empty:
        df_merged = pd.merge(df_merged, df_info, on='Stock_ID', how='left')
    else:
        df_merged['Industry'] = '未知'
        
    if not df_margin.empty:
        df_merged = pd.merge(df_merged, df_margin, on='Stock_ID', how='left')
    else:
        df_merged['Margin_Net'] = 0

    df_merged = df_merged.fillna(0)
    df_merged['Industry'] = df_merged['Industry'].replace(0, '未知')
    
    df_combined = df_merged
    # 使用真實資料日期，而非推算的日期
    last_update_date = date_str
    print(f"[Combined] Total stocks: {len(df_combined)}, Up: {int((df_combined['Change_Pct'] > 0).sum())}, Down: {int((df_combined['Change_Pct'] < 0).sum())}")
    print(f"[Combined] Data date: {last_update_date}")

def get_market_summary():
    """ 獲取大盤加權指數與總量概況 """
    date_str = get_latest_trading_date()
    summary = {
        "taiex": 0.0,
        "change": 0.0,
        "change_pct": 0.0,
        "volume": 0.0,
        "turnover": 0.0,
    }
    
    url_ind = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=IND"
    try:
        res = requests.get(url_ind, timeout=10, verify=False)
        data = res.json()
        if data.get('stat') == 'OK':
            for table in data.get('tables', []):
                for row in table.get('data', []):
                    if row[0] == '發行量加權股價指數':
                        summary['taiex'] = float(row[1].replace(',', ''))
                        change_val = float(row[3].replace(',', ''))
                        if 'green' in row[2] or '-' in row[2]:
                            change_val = -change_val
                        summary['change'] = change_val
                        summary['change_pct'] = float(row[4].replace(',', ''))
                        break
    except Exception as e:
        print(f"Error fetching MI_INDEX IND: {e}")

    url_fmt = f"https://www.twse.com.tw/exchangeReport/FMTQIK?response=json&date={date_str}"
    try:
        res = requests.get(url_fmt, timeout=10, verify=False)
        data = res.json()
        if data.get('stat') == 'OK' and data.get('data'):
            last_row = data['data'][-1]
            summary['volume'] = float(last_row[1].replace(',', '')) / 100000000
            summary['turnover'] = float(last_row[2].replace(',', '')) / 100000000
    except Exception as e:
        print(f"Error fetching FMTQIK: {e}")
        
    summary['date'] = date_str
    summary['stock_data_date'] = last_update_date
    return summary

def scrape_wantgoo_hot_articles():
    url = "https://news.cnyes.com/api/v3/news/category/tw_stock?limit=15"
    articles = []
    try:
        res = requests.get(url, timeout=10, verify=False)
        items = res.json().get('items', {}).get('data', [])
        for item in items:
            articles.append({
                'title': item.get('title', ''),
                'link': f"https://news.cnyes.com/news/id/{item.get('newsId', '')}",
                'summary': item.get('summary', '')
            })
    except Exception as e:
         pass
    return articles

def get_institutional_tracking():
    if df_combined is None or df_combined.empty:
        return {"error": "Data not ready yet"}
        
    df = df_combined
    
    total_foreign = float(df['Foreign_Net'].sum())
    total_trust = float(df['Trust_Net'].sum())
    total_dealer = float(df['Dealer_Net'].sum())
    total_net = float(df['Total_Net'].sum())

    # 土洋同步買賣
    df_sync_buy = df[(df['Foreign_Net'] > 0) & (df['Trust_Net'] > 0)].sort_values('Total_Net', ascending=False).head(15)
    df_sync_sell = df[(df['Foreign_Net'] < 0) & (df['Trust_Net'] < 0)].sort_values('Total_Net', ascending=True).head(15)

    # 散佈圖資料
    scatter_data = df[df['Volume'] > 1000][['Stock_ID', 'Stock_Name', 'Total_Net', 'Change_Pct', 'Volume']].to_dict(orient='records')

    # 1. 土洋對作榜 (Divergence)
    divergence_df = df[(df['Foreign_Net'] * df['Trust_Net'] < 0)].copy()
    divergence_df['Intensity'] = divergence_df['Foreign_Net'].abs() + divergence_df['Trust_Net'].abs()
    divergence_list = divergence_df.sort_values('Intensity', ascending=False).head(15)[
        ['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Foreign_Net', 'Trust_Net', 'Total_Net']
    ].to_dict(orient='records')

    # 2. 法人高參與度 (Participation)
    part_df = df[df['Volume'] > 1000].copy()
    part_df['Participation'] = (part_df['Total_Net'].abs() / part_df['Volume']) * 100
    participation_bubbles = part_df[part_df['Participation'] > 5][
        ['Stock_ID', 'Stock_Name', 'Change_Pct', 'Total_Net', 'Participation']
    ].to_dict(orient='records')

    # 3. 土洋產業偏好對比 (Industry Compare)
    # 轉換成億元為單位
    df_ind = df.copy()
    df_ind['Foreign_Net_Val'] = (df_ind['Foreign_Net'] * df_ind['Close']) / 100000
    df_ind['Trust_Net_Val'] = (df_ind['Trust_Net'] * df_ind['Close']) / 100000
    industry_grp = df_ind.groupby('Industry').agg({
        'Foreign_Net_Val': 'sum',
        'Trust_Net_Val': 'sum'
    }).reset_index()
    foreign_top = industry_grp.nlargest(5, 'Foreign_Net_Val')
    trust_top = industry_grp.nlargest(5, 'Trust_Net_Val')
    top_industries = pd.concat([foreign_top, trust_top]).drop_duplicates(subset=['Industry'])
    industry_compare = top_industries[['Industry', 'Foreign_Net_Val', 'Trust_Net_Val']].round(2).to_dict(orient='records')

    return {
        "date": last_update_date,
        "market_institutional": {
            "foreign": total_foreign,
            "trust": total_trust,
            "dealer": total_dealer,
            "net": total_net
        },
        "sync_buy": df_sync_buy.to_dict(orient='records'),
        "sync_sell": df_sync_sell.to_dict(orient='records'),
        "scatter_data": scatter_data,
        "divergence_list": divergence_list,
        "participation_bubbles": participation_bubbles,
        "industry_compare": industry_compare
    }

def get_market_breadth_industry():
    if df_combined is None or df_combined.empty:
        return {"error": "Data not ready yet"}
    
    df = df_combined
    
    # 大盤多空結構
    up_count = int((df['Change_Pct'] > 0).sum())
    down_count = int((df['Change_Pct'] < 0).sum())
    unchanged_count = int((df['Change_Pct'] == 0).sum())
    
    # 產業資金流向 (以金額：億元為單位)
    df_copy = df.copy()
    df_copy['Inst_Net_Value'] = (df_copy['Total_Net'] * df_copy['Close']) / 100000
    
    industry_grp = df_copy.groupby('Industry').agg({
        'Inst_Net_Value': 'sum'
    }).reset_index()
    
    # 為了圖表顯示美觀，將數值四捨五入到小數點後兩位
    industry_grp['Inst_Net_Value'] = industry_grp['Inst_Net_Value'].round(2)
    
    top_buy_industries = industry_grp.sort_values('Inst_Net_Value', ascending=False).head(10).to_dict(orient='records')
    top_sell_industries = industry_grp.sort_values('Inst_Net_Value', ascending=True).head(10).to_dict(orient='records')
    
    # 產業板塊資金地圖 (Treemap)
    treemap_grp = df_copy.groupby('Industry').agg({
        'Turnover_Value': 'sum',
        'Change_Pct': 'mean'
    }).reset_index()
    
    industry_treemap = []
    for _, row in treemap_grp.iterrows():
        if row['Turnover_Value'] > 0: # 只顯示有成交值的板塊
            industry_treemap.append({
                "name": row['Industry'],
                "value": round(row['Turnover_Value'], 2),
                "change": round(row['Change_Pct'], 2)
            })

    return {
        "breadth": [
            {"value": up_count, "name": "上漲"},
            {"value": down_count, "name": "下跌"},
            {"value": unchanged_count, "name": "平盤"}
        ],
        "top_buy_industries": top_buy_industries,
        "top_sell_industries": top_sell_industries,
        "industry_treemap": industry_treemap
    }

def get_retail_and_leaders():
    if df_combined is None or df_combined.empty:
        return {"error": "Data not ready yet"}
    
    df = df_combined.copy()
    
    # 吸金排行榜 (成交值)
    turnover_leaders = df.sort_values('Turnover_Value', ascending=False).head(20)[
        ['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Turnover_Value', 'Total_Net']
    ].to_dict(orient='records')
    
    # 散戶被洗出場 (融資減，法人買)
    washed_out = df[(df['Margin_Net'] < 0) & (df['Total_Net'] > 0)].sort_values('Total_Net', ascending=False).head(15)[
        ['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Margin_Net', 'Total_Net']
    ].to_dict(orient='records')
    
    # 散戶套牢滿手血 (融資增，法人賣)
    catching_knives = df[(df['Margin_Net'] > 0) & (df['Total_Net'] < 0)].sort_values('Total_Net', ascending=True).head(15)[
        ['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Margin_Net', 'Total_Net']
    ].to_dict(orient='records')
    
    return {
        "turnover_leaders": turnover_leaders,
        "washed_out": washed_out,
        "catching_knives": catching_knives
    }

def get_investor_dashboard():
    """投資決策儀表板：用每日快取資料推導市場、產業、風險與候選股訊號。"""
    if df_combined is None or df_combined.empty:
        return {"error": "Data not ready yet"}

    df = df_combined.copy()
    for col in ['Change_Pct', 'Volume', 'Turnover_Value', 'Foreign_Net', 'Trust_Net', 'Dealer_Net', 'Total_Net', 'Margin_Net']:
        df[col] = pd.to_numeric(df.get(col, 0), errors='coerce').fillna(0)

    total_count = max(len(df), 1)
    up_count = int((df['Change_Pct'] > 0).sum())
    down_count = int((df['Change_Pct'] < 0).sum())
    limit_up_count = int((df['Change_Pct'] >= 9.5).sum())
    limit_down_count = int((df['Change_Pct'] <= -9.5).sum())
    advance_ratio = up_count / total_count * 100
    strong_ratio = (df['Change_Pct'] >= 3).sum() / total_count * 100
    weak_ratio = (df['Change_Pct'] <= -3).sum() / total_count * 100
    net_buy_ratio = (df['Total_Net'] > 0).sum() / total_count * 100
    margin_pressure_ratio = (df['Margin_Net'] > 0).sum() / total_count * 100
    top10_turnover_share = 0.0
    total_turnover = _safe_float(df['Turnover_Value'].sum())
    if total_turnover > 0:
        top10_turnover_share = _safe_float(df.nlargest(10, 'Turnover_Value')['Turnover_Value'].sum()) / total_turnover * 100

    breadth_score = advance_ratio
    institutional_score = min(100, max(0, 50 + _safe_float(df['Total_Net'].sum()) / max(_safe_float(df['Volume'].sum()), 1) * 500))
    momentum_score = min(100, max(0, 50 + (strong_ratio - weak_ratio) * 2.2))
    risk_score = min(100, max(0, 50 + (limit_down_count - limit_up_count) * 4 + (margin_pressure_ratio - 50) * 0.8 + (top10_turnover_share - 25) * 0.7))
    market_temperature = round(breadth_score * 0.35 + institutional_score * 0.25 + momentum_score * 0.25 + (100 - risk_score) * 0.15, 1)

    if market_temperature >= 65:
        regime = "偏多進攻"
    elif market_temperature >= 50:
        regime = "中性偏多"
    elif market_temperature >= 35:
        regime = "震盪防守"
    else:
        regime = "偏空降風險"

    pulse = {
        "date": last_update_date,
        "market_temperature": market_temperature,
        "regime": regime,
        "advance_ratio": round(advance_ratio, 1),
        "net_buy_ratio": round(net_buy_ratio, 1),
        "margin_pressure_ratio": round(margin_pressure_ratio, 1),
        "top10_turnover_share": round(top10_turnover_share, 1),
        "limit_up_count": limit_up_count,
        "limit_down_count": limit_down_count,
        "scores": [
            {"name": "市場廣度", "value": round(breadth_score, 1)},
            {"name": "法人方向", "value": round(institutional_score, 1)},
            {"name": "強弱動能", "value": round(momentum_score, 1)},
            {"name": "風險控管", "value": round(100 - risk_score, 1)}
        ]
    }

    industry = df.groupby('Industry').agg(
        stocks=('Stock_ID', 'count'),
        avg_change=('Change_Pct', 'mean'),
        net=('Total_Net', 'sum'),
        turnover=('Turnover_Value', 'sum'),
        margin=('Margin_Net', 'sum')
    ).reset_index()
    industry = industry[industry['Industry'] != '未知']
    industry['heat_score'] = (
        _score_series(industry['avg_change']) * 0.35 +
        _score_series(industry['net']) * 0.35 +
        _score_series(industry['turnover']) * 0.2 +
        (100 - _score_series(industry['margin'])) * 0.1
    ).round(1)
    industry_heatmap = industry.sort_values('heat_score', ascending=False).head(18)

    smart_money = df.copy()
    smart_money['smart_score'] = (
        _score_series(smart_money['Total_Net']) * 0.42 +
        _score_series(smart_money['Trust_Net']) * 0.22 +
        _score_series(smart_money['Turnover_Value']) * 0.18 +
        _score_series(smart_money['Change_Pct']) * 0.12 +
        (100 - _score_series(smart_money['Margin_Net'])) * 0.06
    ).round(1)
    smart_money = smart_money[
        (smart_money['Total_Net'] > 0) &
        (smart_money['Turnover_Value'] > smart_money['Turnover_Value'].quantile(0.55))
    ].sort_values('smart_score', ascending=False).head(20)

    risk_watch = df.copy()
    risk_watch['risk_score'] = (
        _score_series(-risk_watch['Total_Net']) * 0.35 +
        _score_series(risk_watch['Margin_Net']) * 0.3 +
        _score_series(-risk_watch['Change_Pct']) * 0.2 +
        _score_series(risk_watch['Turnover_Value']) * 0.15
    ).round(1)
    risk_watch = risk_watch[
        (risk_watch['Margin_Net'] > 0) |
        (risk_watch['Total_Net'] < 0) |
        (risk_watch['Change_Pct'] < -2)
    ].sort_values('risk_score', ascending=False).head(20)

    opportunities = df.copy()
    opportunities['opportunity_score'] = (
        _score_series(opportunities['Total_Net']) * 0.28 +
        _score_series(opportunities['Trust_Net']) * 0.18 +
        _score_series(opportunities['Turnover_Value']) * 0.18 +
        _score_series(opportunities['Change_Pct']) * 0.2 +
        (100 - _score_series(opportunities['Margin_Net'])) * 0.16
    ).round(1)
    opportunities = opportunities[
        (opportunities['Total_Net'] > 0) &
        (opportunities['Change_Pct'] > 0) &
        (opportunities['Margin_Net'] <= opportunities['Margin_Net'].quantile(0.7))
    ].sort_values('opportunity_score', ascending=False).head(15)

    change_bins = [-100, -7, -3, -1, 0, 1, 3, 7, 100]
    change_labels = ['重挫<-7%', '-7~-3%', '-3~-1%', '-1~0%', '0~1%', '1~3%', '3~7%', '強漲>7%']
    change_distribution = pd.cut(df['Change_Pct'], bins=change_bins, labels=change_labels, include_lowest=True)
    change_distribution = change_distribution.value_counts(sort=False).reset_index()
    change_distribution.columns = ['range', 'count']

    institutional_mix = [
        {"name": "外資", "value": round(_safe_float(df['Foreign_Net'].sum()), 1)},
        {"name": "投信", "value": round(_safe_float(df['Trust_Net'].sum()), 1)},
        {"name": "自營商", "value": round(_safe_float(df['Dealer_Net'].sum()), 1)}
    ]

    turnover_concentration = df.nlargest(12, 'Turnover_Value')[
        ['Stock_ID', 'Stock_Name', 'Industry', 'Turnover_Value', 'Change_Pct', 'Total_Net']
    ]

    quadrant_sample = df[df['Turnover_Value'] > df['Turnover_Value'].quantile(0.6)].copy()
    quadrant_sample = quadrant_sample.nlargest(180, 'Turnover_Value')
    margin_quadrants = quadrant_sample[
        ['Stock_ID', 'Stock_Name', 'Industry', 'Change_Pct', 'Total_Net', 'Margin_Net', 'Turnover_Value']
    ]

    momentum_leaders = df[
        (df['Change_Pct'] > 3) &
        (df['Turnover_Value'] > df['Turnover_Value'].quantile(0.55))
    ].sort_values(['Change_Pct', 'Turnover_Value'], ascending=False).head(15)

    defensive_candidates = df[
        (df['Change_Pct'].between(-1.2, 1.8)) &
        (df['Total_Net'] > 0) &
        (df['Margin_Net'] <= 0) &
        (df['Turnover_Value'] > df['Turnover_Value'].quantile(0.45))
    ].copy()
    defensive_candidates['defense_score'] = (
        _score_series(defensive_candidates['Total_Net']) * 0.4 +
        (100 - _score_series(defensive_candidates['Change_Pct'].abs())) * 0.25 +
        (100 - _score_series(defensive_candidates['Margin_Net'])) * 0.2 +
        _score_series(defensive_candidates['Turnover_Value']) * 0.15
    ).round(1)
    defensive_candidates = defensive_candidates.sort_values('defense_score', ascending=False).head(15)

    sell_pressure = df[
        (df['Total_Net'] < 0) &
        (df['Turnover_Value'] > df['Turnover_Value'].quantile(0.55))
    ].copy()
    sell_pressure['sell_score'] = (
        _score_series(-sell_pressure['Total_Net']) * 0.45 +
        _score_series(-sell_pressure['Change_Pct']) * 0.25 +
        _score_series(sell_pressure['Turnover_Value']) * 0.2 +
        _score_series(sell_pressure['Margin_Net']) * 0.1
    ).round(1)
    sell_pressure = sell_pressure.sort_values('sell_score', ascending=False).head(15)

    trust_accumulation = df[
        (df['Trust_Net'] > 0) &
        (df['Turnover_Value'] > df['Turnover_Value'].quantile(0.45))
    ].copy()
    trust_accumulation['trust_score'] = (
        _score_series(trust_accumulation['Trust_Net']) * 0.55 +
        _score_series(trust_accumulation['Change_Pct']) * 0.25 +
        _score_series(trust_accumulation['Turnover_Value']) * 0.2
    ).round(1)
    trust_accumulation = trust_accumulation.sort_values('trust_score', ascending=False).head(15)

    foreign_accumulation = df[
        (df['Foreign_Net'] > 0) &
        (df['Turnover_Value'] > df['Turnover_Value'].quantile(0.45))
    ].copy()
    foreign_accumulation['foreign_score'] = (
        _score_series(foreign_accumulation['Foreign_Net']) * 0.55 +
        _score_series(foreign_accumulation['Change_Pct']) * 0.2 +
        _score_series(foreign_accumulation['Turnover_Value']) * 0.25
    ).round(1)
    foreign_accumulation = foreign_accumulation.sort_values('foreign_score', ascending=False).head(15)

    rebound_candidates = df[
        (df['Change_Pct'] < 0) &
        (df['Total_Net'] > 0) &
        (df['Margin_Net'] <= 0)
    ].copy()
    rebound_candidates['rebound_score'] = (
        _score_series(rebound_candidates['Total_Net']) * 0.45 +
        _score_series(-rebound_candidates['Change_Pct']) * 0.25 +
        (100 - _score_series(rebound_candidates['Margin_Net'])) * 0.2 +
        _score_series(rebound_candidates['Turnover_Value']) * 0.1
    ).round(1)
    rebound_candidates = rebound_candidates.sort_values('rebound_score', ascending=False).head(15)

    margin_short_squeeze = df[
        (df['Margin_Net'] < 0) &
        (df['Change_Pct'] > 2) &
        (df['Total_Net'] > 0)
    ].copy()
    margin_short_squeeze['squeeze_score'] = (
        _score_series(-margin_short_squeeze['Margin_Net']) * 0.38 +
        _score_series(margin_short_squeeze['Change_Pct']) * 0.32 +
        _score_series(margin_short_squeeze['Total_Net']) * 0.2 +
        _score_series(margin_short_squeeze['Turnover_Value']) * 0.1
    ).round(1)
    margin_short_squeeze = margin_short_squeeze.sort_values('squeeze_score', ascending=False).head(15)

    liquidity_leaders = df.copy()
    liquidity_leaders['liquidity_score'] = (
        _score_series(liquidity_leaders['Turnover_Value']) * 0.55 +
        _score_series(liquidity_leaders['Volume']) * 0.25 +
        _score_series(abs(liquidity_leaders['Total_Net'])) * 0.2
    ).round(1)
    liquidity_leaders = liquidity_leaders.sort_values('liquidity_score', ascending=False).head(15)

    industry_rotation = industry.copy()
    industry_rotation['rotation_score'] = (
        _score_series(industry_rotation['avg_change']) * 0.3 +
        _score_series(industry_rotation['net']) * 0.3 +
        _score_series(industry_rotation['turnover']) * 0.25 +
        (100 - _score_series(industry_rotation['margin'])) * 0.15
    ).round(1)
    industry_rotation = industry_rotation.sort_values('rotation_score', ascending=False).head(12)

    stock_cols = ['Stock_ID', 'Stock_Name', 'Industry', 'Close', 'Change_Pct', 'Turnover_Value', 'Total_Net', 'Trust_Net', 'Foreign_Net', 'Margin_Net']

    return {
        "pulse": pulse,
        "industry_heatmap": industry_heatmap[['Industry', 'stocks', 'avg_change', 'net', 'turnover', 'margin', 'heat_score']].to_dict(orient='records'),
        "smart_money": smart_money[['Stock_ID', 'Stock_Name', 'Industry', 'Close', 'Change_Pct', 'Turnover_Value', 'Total_Net', 'Trust_Net', 'Margin_Net', 'smart_score']].to_dict(orient='records'),
        "risk_watch": risk_watch[['Stock_ID', 'Stock_Name', 'Industry', 'Close', 'Change_Pct', 'Turnover_Value', 'Total_Net', 'Margin_Net', 'risk_score']].to_dict(orient='records'),
        "opportunities": opportunities[['Stock_ID', 'Stock_Name', 'Industry', 'Close', 'Change_Pct', 'Turnover_Value', 'Total_Net', 'Trust_Net', 'Margin_Net', 'opportunity_score']].to_dict(orient='records'),
        "change_distribution": change_distribution.to_dict(orient='records'),
        "institutional_mix": institutional_mix,
        "turnover_concentration": turnover_concentration.to_dict(orient='records'),
        "margin_quadrants": margin_quadrants.to_dict(orient='records'),
        "momentum_leaders": momentum_leaders[stock_cols].to_dict(orient='records'),
        "defensive_candidates": defensive_candidates[stock_cols + ['defense_score']].to_dict(orient='records'),
        "sell_pressure": sell_pressure[stock_cols + ['sell_score']].to_dict(orient='records'),
        "trust_accumulation": trust_accumulation[stock_cols + ['trust_score']].to_dict(orient='records'),
        "foreign_accumulation": foreign_accumulation[stock_cols + ['foreign_score']].to_dict(orient='records'),
        "rebound_candidates": rebound_candidates[stock_cols + ['rebound_score']].to_dict(orient='records'),
        "margin_short_squeeze": margin_short_squeeze[stock_cols + ['squeeze_score']].to_dict(orient='records'),
        "liquidity_leaders": liquidity_leaders[stock_cols + ['Volume', 'liquidity_score']].to_dict(orient='records'),
        "industry_rotation": industry_rotation[['Industry', 'stocks', 'avg_change', 'net', 'turnover', 'margin', 'rotation_score']].to_dict(orient='records')
    }

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
             hist = hist.dropna(subset=['Close', 'Volume'])
             
             # MA & 扣抵值 (Deduction)
             hist['MA5'] = hist['Close'].rolling(window=5).mean().fillna(0)
             hist['MA20'] = hist['Close'].rolling(window=20).mean().fillna(0)
             # MA20 扣抵值：對應20天前的價格 (用於預判明日均線方向)
             hist['MA20_Deduction'] = hist['Close'].shift(19).fillna(0)

             # VWAP 主力動態成本線 (20日加權平均價)
             hist['Turnover'] = hist['Close'] * hist['Volume']
             hist['VWAP20'] = (hist['Turnover'].rolling(window=20).sum() / hist['Volume'].rolling(window=20).sum()).fillna(hist['Close'])

             # RSI (14日)
             delta = hist['Close'].diff()
             gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
             loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
             rs = gain / loss
             hist['RSI'] = (100 - (100 / (1 + rs))).fillna(50)

             # KD (9, 3, 3)
             hist['Low9'] = hist['Low'].rolling(window=9).min()
             hist['High9'] = hist['High'].rolling(window=9).max()
             hist['RSV'] = 100 * (hist['Close'] - hist['Low9']) / (hist['High9'] - hist['Low9'])
             hist['RSV'] = hist['RSV'].fillna(50)
             hist['K'] = hist['RSV'].ewm(com=2, adjust=False).mean()
             hist['D'] = hist['K'].ewm(com=2, adjust=False).mean()

             # MACD
             exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
             exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
             hist['MACD'] = exp1 - exp2
             hist['Signal_Line'] = hist['MACD'].ewm(span=9, adjust=False).mean()
             hist['MACD_Hist'] = hist['MACD'] - hist['Signal_Line']

             hist = patterns.identify_patterns(hist)

             hist_60 = hist.tail(60).reset_index(drop=True)

             # 取最新一筆的扣抵值與股價作比較，以文字呈現均線未來趨勢預判
             latest_close = hist_60['Close'].iloc[-1]
             latest_deduction = hist_60['MA20_Deduction'].iloc[-1]
             ma20_trend = "預計上揚 (具支撐)" if latest_close > latest_deduction else "預計下彎 (具壓力)"
             
             # 過濾出有型態的資料點
             pattern_points = []
             for i, row in hist_60.iterrows():
                 if pd.notna(row.get('Pattern')) and row['Pattern']:
                     pattern_points.append({
                         "date": row['Date'].strftime('%Y-%m-%d'),
                         "pattern": row['Pattern'],
                         "price": row['Low'] if '吞噬' in row['Pattern'] or '晨星' in row['Pattern'] else row['High']
                     })

             return {
                 "stock_id": stock_id,
                 "dates": hist_60['Date'].dt.strftime('%Y-%m-%d').tolist(),
                 "kline_data": hist_60[['Open', 'Close', 'Low', 'High']].values.tolist(),
                 "volumes": (hist_60['Volume'] / 1000).astype(int).tolist(),
                 "ma5": hist_60['MA5'].tolist(),
                 "ma20": hist_60['MA20'].tolist(),
                 "vwap20": hist_60['VWAP20'].tolist(),
                 "ma20_deduction": hist_60['MA20_Deduction'].tolist(),
                 "ma20_trend": ma20_trend,
                 "rsi": hist_60['RSI'].tolist(),
                 "k": hist_60['K'].tolist(),
                 "d": hist_60['D'].tolist(),
                 "macd": hist_60['MACD'].tolist(),
                 "macd_signal": hist_60['Signal_Line'].tolist(),
                 "macd_hist": hist_60['MACD_Hist'].tolist(),
                 "patterns": pattern_points
             }
    except Exception as e:
        print(f"Error fetching history for {stock_id}: {e}")
    return {"error": "Stock not found"}

def get_market_trend(period='3mo'):
    """ 獲取大盤加權指數(^TWII)歷史趨勢 """
    try:
        twii = yf.Ticker("^TWII")
        hist = twii.history(period=period)
        if not hist.empty:
            hist.reset_index(inplace=True)
            hist = hist.dropna(subset=['Close', 'Volume'])
            
            # MA
            hist['MA20'] = hist['Close'].rolling(window=20).mean().fillna(0)
            hist['MA60'] = hist['Close'].rolling(window=60).mean().fillna(0)
            
            return {
                "dates": hist['Date'].dt.strftime('%Y-%m-%d').tolist(),
                "kline_data": hist[['Open', 'Close', 'Low', 'High']].values.tolist(),
                "volumes": (hist['Volume'] / 100000000).round(2).tolist(), # 轉換為億股
                "ma20": hist['MA20'].tolist(),
                "ma60": hist['MA60'].tolist()
            }
    except Exception as e:
        print(f"Error fetching market trend: {e}")
    return {"error": "Trend data not found"}

def get_smart_money_advanced():
    """ 
    進階主力籌碼追蹤：
    1. 計算「籌碼集中度」(三大法人買超 / 成交量)
    2. 尋找「低位階 + 法人連買」標的 (基於現有當日資料模擬)
    3. 排除漲幅過大標的 (避免追高)
    """
    global df_combined
    if df_combined is None or df_combined.empty:
        return []
    
    df = df_combined.copy()
    
    # 1. 計算籌碼集中度 (%)
    # 注意：Volume 是張數 (1000股)，Total_Net 也是以張為單位 (前面除以1000了)
    df['Chip_Concentration'] = (df['Total_Net'] / df['Volume'] * 100).fillna(0)
    
    # 2. 篩選條件
    # - 法人買超佔比 > 10%
    # - 漲幅不可太大 ( < 5%) 
    # - 成交值不可太小 ( > 50百萬)
    smart_candidates = df[
        (df['Chip_Concentration'] > 10) &
        (df['Change_Pct'] < 5) &
        (df['Turnover_Value'] > 50)
    ].copy()
    
    # 3. 評分
    smart_candidates['conviction_score'] = (
        _score_series(smart_candidates['Chip_Concentration']) * 0.6 +
        _score_series(smart_candidates['Trust_Net']) * 0.3 +
        (100 - _score_series(smart_candidates['Change_Pct'])) * 0.1
    ).round(1)
    
    smart_candidates = smart_candidates.sort_values('conviction_score', ascending=False).head(30)
    
    return smart_candidates[['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Volume', 'Total_Net', 'Trust_Net', 'Chip_Concentration', 'conviction_score']].to_dict(orient='records')

def get_stock_heatmap_data():
    """
    股票熱力圖資料：
    以產業分組，每檔股票以成交值(Turnover_Value)決定方塊大小，
    以漲跌幅(Change_Pct)決定顏色（紅漲綠跌）。
    回傳巢狀 treemap 結構。
    """
    if df_combined is None or df_combined.empty:
        return {"error": "Data not ready yet"}

    df = df_combined.copy()
    # 過濾掉成交值太小的股票，避免圖表雜訊
    df = df[df['Turnover_Value'] > 1]
    df = df[df['Industry'] != '未知']

    industries = []
    for industry_name, group in df.groupby('Industry'):
        # 取成交值前50大的股票（避免太多小型股佔滿空間）
        top_stocks = group.nlargest(50, 'Turnover_Value')
        children = []
        for _, row in top_stocks.iterrows():
            children.append({
                "name": row['Stock_Name'],
                "stock_id": row['Stock_ID'],
                "value": round(_safe_float(row['Turnover_Value']), 2),
                "change_pct": round(_safe_float(row['Change_Pct']), 2),
                "close": round(_safe_float(row['Close']), 2),
                "volume": round(_safe_float(row['Volume']), 0),
                "total_net": round(_safe_float(row['Total_Net']), 1),
            })

        if children:
            industry_turnover = sum(c['value'] for c in children)
            industry_avg_change = sum(c['change_pct'] * c['value'] for c in children) / industry_turnover if industry_turnover > 0 else 0
            industries.append({
                "name": industry_name,
                "value": round(industry_turnover, 2),
                "change_pct": round(industry_avg_change, 2),
                "children": children
            })

    # 按成交值排序，最大的產業排最前面
    industries.sort(key=lambda x: x['value'], reverse=True)

    # 市場統計摘要
    total_up = int((df_combined['Change_Pct'] > 0).sum())
    total_down = int((df_combined['Change_Pct'] < 0).sum())
    total_unchanged = int((df_combined['Change_Pct'] == 0).sum())
    avg_change = round(float(df_combined['Change_Pct'].mean()), 2)

    return {
        "date": last_update_date,
        "industries": industries,
        "summary": {
            "total_stocks": len(df_combined),
            "up": total_up,
            "down": total_down,
            "unchanged": total_unchanged,
            "avg_change": avg_change
        }
    }

def screen_stocks(criteria):
    """ 多條件選股 """
    global df_combined
    if df_combined is None or df_combined.empty:
        return []
    
    df = df_combined.copy()
    
    if criteria.get('min_price'):
        df = df[df['Close'] >= criteria['min_price']]
    if criteria.get('max_price'):
        df = df[df['Close'] <= criteria['max_price']]
    if criteria.get('min_change_pct'):
        df = df[df['Change_Pct'] >= criteria['min_change_pct']]
    if criteria.get('min_total_net'):
        df = df[df['Total_Net'] >= criteria['min_total_net']]
    if criteria.get('min_turnover_value'):
        df = df[df['Turnover_Value'] >= criteria['min_turnover_value']]
    if criteria.get('industry'):
        df = df[df['Industry'] == criteria['industry']]
        
    return df.head(100).to_dict(orient='records')
