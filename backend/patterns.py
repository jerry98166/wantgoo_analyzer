import pandas as pd

def identify_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    辨識基本的 K 線型態 (不依賴 TA-Lib，純 pandas 實作)
    傳入的 DataFrame 預期包含: ['Open', 'High', 'Low', 'Close']
    """
    if df.empty or len(df) < 3:
        df['Pattern'] = None
        return df

    # 確保有這些欄位
    for col in ['Open', 'High', 'Low', 'Close']:
        if col not in df.columns:
            df['Pattern'] = None
            return df

    # 初始化 Pattern 欄位
    df['Pattern'] = None

    # 1. 判斷多頭吞噬 (Bullish Engulfing)
    # 條件：前一根陰線 (Close < Open)，當前陽線 (Close > Open)，且當前實體完全包覆前一根實體
    prev_close = df['Close'].shift(1)
    prev_open = df['Open'].shift(1)
    curr_close = df['Close']
    curr_open = df['Open']

    is_prev_bearish = prev_close < prev_open
    is_curr_bullish = curr_close > curr_open
    engulfing = is_prev_bearish & is_curr_bullish & (curr_close > prev_open) & (curr_open < prev_close)
    
    # 2. 判斷晨星 (Morning Star)
    # 條件：前兩天大陰線，前一天十字星或小實體(跳空)，今天大陽線(收盤大於前兩天實體一半)
    prev2_close = df['Close'].shift(2)
    prev2_open = df['Open'].shift(2)
    is_prev2_bearish = prev2_close < prev2_open
    
    # 簡單定義：前一天實體很小 (絕對值小於前兩天實體的 30%)
    prev2_body = (prev2_open - prev2_close).abs()
    prev1_body = (prev_open - prev_close).abs()
    is_star = prev1_body < (prev2_body * 0.3)
    
    # 今天陽線且收盤深入前兩天陰線實體 (大於一半)
    morning_star = is_prev2_bearish & is_star & is_curr_bullish & (curr_close > (prev2_close + prev2_body * 0.5))

    # 標記型態 (優先顯示晨星，再來是多頭吞噬)
    df.loc[engulfing, 'Pattern'] = '多頭吞噬 (Bullish Engulfing)'
    df.loc[morning_star, 'Pattern'] = '晨星 (Morning Star)'
    
    return df
