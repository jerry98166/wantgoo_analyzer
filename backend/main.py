from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import scraper
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

df_combined = None
date_str = None

def update_daily_data():
    global df_combined, date_str
    print("Fetching and updating daily data...")
    df_combined, date_str = scraper.get_combined_data()
    print(f"Data updated for {date_str}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load data on startup
    update_daily_data()
    
    # Setup scheduler for daily update at 17:05
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_daily_data, 'cron', hour=17, minute=5)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="WantGoo Analyzer API", lifespan=lifespan)

# Setup CORS to allow Vue frontend to fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data variables are managed by lifespan

@app.get("/api/meta")
def get_meta():
    return {"date": date_str}

@app.get("/api/top-stocks")
def get_top_stocks():
    return scraper.analyze_top_stocks(df_combined, n=20)

@app.get("/api/industry-focus")
def get_industry_focus():
    return scraper.analyze_industry(df_combined)

@app.get("/api/correlation")
def get_correlation():
    return scraper.analyze_correlation(df_combined)

@app.get("/api/market-breadth")
def get_market_breadth():
    return scraper.analyze_market_breadth(df_combined)

@app.get("/api/synchrony")
def get_synchrony():
    return scraper.analyze_synchrony(df_combined)

@app.get("/api/participation")
def get_participation():
    return scraper.analyze_participation(df_combined)

@app.get("/api/volume-leaders")
def get_volume_leaders():
    return scraper.analyze_volume_leaders(df_combined)

@app.get("/api/smart-money")
def get_smart_money():
    return scraper.analyze_smart_money(df_combined)

@app.get("/api/all-stocks")
def get_all_stocks():
    return df_combined.fillna(0).to_dict(orient='records')

@app.get("/api/turnover-leaders")
def get_turnover_leaders():
    leaders = df_combined.sort_values('Turnover_Value', ascending=False).head(20)
    return leaders[['Stock_ID', 'Stock_Name', 'Close', 'Change_Pct', 'Volume', 'Total_Net', 'Industry', 'Turnover_Value']].fillna(0).to_dict(orient='records')

@app.get("/api/institutional-radar")
def get_institutional_radar():
    return scraper.analyze_institutional_radar(df_combined)

@app.get("/api/day-trading")
def get_day_trading():
    return scraper.analyze_day_trading(df_combined)

@app.get("/api/retail-sentiment")
def get_retail_sentiment():
    return scraper.analyze_retail_sentiment(df_combined)

@app.get("/api/stock/{stock_id}")
def get_stock(stock_id: str):
    data = scraper.get_stock_history_data(stock_id)
    if not data:
        return {"error": "Stock not found"}
    return data

@app.get("/api/articles")
def get_articles():
    return scraper.scrape_wantgoo_hot_articles()

@app.get("/api/historical-stats")
def get_historical_stats():
    return scraper.get_historical_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
