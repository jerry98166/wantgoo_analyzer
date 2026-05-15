from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import scraper
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from database import get_db, Watchlist, Alert

# --- Pydantic Models ---
class WatchlistCreate(BaseModel):
    stock_id: str
    stock_name: str

class WatchlistResponse(BaseModel):
    id: int
    stock_id: str
    stock_name: str
    close: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[float] = None
    
    class Config:
        orm_mode = True

class AlertCreate(BaseModel):
    stock_id: str
    condition_type: str
    target_value: float

class AlertResponse(BaseModel):
    id: int
    stock_id: str
    condition_type: str
    target_value: float
    is_active: bool
    
    class Config:
        orm_mode = True

def update_daily_data():
    print("Fetching daily market data (Price, T86, Margin, Industry)...")
    scraper.fetch_all_daily_data()
    print("Update complete.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時先更新一次資料
    update_daily_data()
    
    # 排程設定：多次嘗試，因為 TWSE OpenAPI 更新時間不固定 (約 17:30~19:00)
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_daily_data, 'cron', hour=14, minute=30, id='update_1430')  # 盤中更新
    scheduler.add_job(update_daily_data, 'cron', hour=17, minute=15, id='update_1715')  # 收盤後首次
    scheduler.add_job(update_daily_data, 'cron', hour=17, minute=45, id='update_1745')  # 第二次重試
    scheduler.add_job(update_daily_data, 'cron', hour=18, minute=30, id='update_1830')  # 第三次重試
    scheduler.start()
    
    yield
    scheduler.shutdown()

app = FastAPI(title="WantGoo Analyzer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/data-status")
def get_data_status():
    """查詢目前快取資料的日期與狀態"""
    import pytz
    from datetime import datetime
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    expected_date = scraper.get_latest_trading_date()
    actual_date = scraper.last_update_date
    stock_count = len(scraper.df_combined) if scraper.df_combined is not None else 0
    return {
        "server_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "expected_date": expected_date,
        "actual_data_date": actual_date,
        "is_current": actual_date == expected_date,
        "stock_count": stock_count
    }

@app.post("/api/refresh-data")
def refresh_data():
    """手動觸發重新抓取資料"""
    old_date = scraper.last_update_date
    update_daily_data()
    new_date = scraper.last_update_date
    stock_count = len(scraper.df_combined) if scraper.df_combined is not None else 0
    return {
        "message": "Data refreshed",
        "previous_date": old_date,
        "new_date": new_date,
        "stock_count": stock_count
    }

@app.get("/api/market-summary")
def get_market_summary():
    return scraper.get_market_summary()

@app.get("/api/news")
def get_news():
    return scraper.scrape_wantgoo_hot_articles()

@app.get("/api/institutional-tracking")
def get_institutional_tracking():
    return scraper.get_institutional_tracking()

@app.get("/api/market-breadth-industry")
def get_market_breadth_industry():
    return scraper.get_market_breadth_industry()

@app.get("/api/retail-and-leaders")
def get_retail_and_leaders():
    return scraper.get_retail_and_leaders()

@app.get("/api/market-trend")
def get_market_trend():
    return scraper.get_market_trend()

@app.get("/api/investor-dashboard")
def get_investor_dashboard():
    return scraper.get_investor_dashboard()

@app.get("/api/smart-money-advanced")
def get_smart_money_advanced():
    return scraper.get_smart_money_advanced()

@app.get("/api/stock-heatmap")
def get_stock_heatmap():
    return scraper.get_stock_heatmap_data()

class ScreenerCriteria(BaseModel):
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_change_pct: Optional[float] = None
    min_total_net: Optional[float] = None
    min_turnover_value: Optional[float] = None
    industry: Optional[str] = None

@app.post("/api/screener")
def screen_stocks(criteria: ScreenerCriteria):
    return scraper.screen_stocks(criteria.dict())

@app.get("/api/stock/{stock_id}")
def get_stock(stock_id: str):
    return scraper.get_stock_history_data(stock_id)

# --- Watchlist Endpoints ---
@app.get("/api/watchlist", response_model=List[WatchlistResponse])
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(Watchlist).all()
    res = []
    df = scraper.df_combined
    for item in items:
        close_val = None
        change_pct_val = None
        vol_val = None
        if df is not None and not df.empty and item.stock_id in df['Stock_ID'].values:
            row = df[df['Stock_ID'] == item.stock_id].iloc[0]
            close_val = row.get('Close')
            change_pct_val = row.get('Change_Pct')
            vol_val = row.get('Volume')
            
        res.append({
            "id": item.id,
            "stock_id": item.stock_id,
            "stock_name": item.stock_name,
            "close": close_val,
            "change_pct": change_pct_val,
            "volume": vol_val
        })
    return res

@app.post("/api/watchlist", response_model=WatchlistResponse)
def add_to_watchlist(item: WatchlistCreate, db: Session = Depends(get_db)):
    db_item = db.query(Watchlist).filter(Watchlist.stock_id == item.stock_id).first()
    if db_item:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")
    new_item = Watchlist(stock_id=item.stock_id, stock_name=item.stock_name)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.delete("/api/watchlist/{stock_id}")
def remove_from_watchlist(stock_id: str, db: Session = Depends(get_db)):
    db_item = db.query(Watchlist).filter(Watchlist.stock_id == stock_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")
    db.delete(db_item)
    db.commit()
    return {"message": "Removed successfully"}

# --- Alert Endpoints ---
@app.get("/api/alerts", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).all()

@app.post("/api/alerts", response_model=AlertResponse)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    new_alert = Alert(
        stock_id=alert.stock_id, 
        condition_type=alert.condition_type, 
        target_value=alert.target_value
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert

@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not db_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(db_alert)
    db.commit()
    return {"message": "Deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
