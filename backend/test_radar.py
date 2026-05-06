import scraper
import traceback
df, date = scraper.get_combined_data()
try:
    res = scraper.analyze_institutional_radar(df)
    print("Success")
except Exception as e:
    traceback.print_exc()
