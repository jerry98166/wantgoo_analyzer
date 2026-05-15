# 匯入自定義的 scraper 模組，用於呼叫爬蟲與資料分析功能
import scraper
# 匯入 traceback 模組，用於捕捉並印出詳細的錯誤堆疊追蹤資訊 (Error Stack Trace)
import traceback

# 步驟 1: 呼叫 get_combined_data() 函式，抓取並整合當日的台股各項數據
# 回傳整理好的 DataFrame (df) 與 資料日期字串 (date)
df, date = scraper.get_combined_data()

try:
    # 步驟 2: 將取得的 DataFrame 傳入 analyze_institutional_radar 函式進行測試
    # 此函式專門分析投信作帳(高參與率)與自營商短線避雷(異常買超)
    res = scraper.analyze_institutional_radar(df)
    
    # 若執行過程中無發生錯誤，則印出 Success 表示測試成功
    print("Success")
except Exception as e:
    # 若執行過程中發生任何例外錯誤，使用 traceback 完整印出錯誤發生的位置與原因，方便除錯
    traceback.print_exc()
