import requests
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any

def scrape_food_prices_yahoo() -> Dict[str, Any]:
    """
    使用 Yahoo Finance API 爬取糧食價格 (小麥期貨)
    """
    try:
        # 使用小麥期貨 (ZW=F) 作為糧食指標
        url = "https://query1.finance.yahoo.com/v8/finance/chart/ZW=F"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        params = {
            'interval': '1d',
            'range': '5d'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            
            # 獲取最新價格
            current_price = result['meta']['regularMarketPrice']
            previous_close = result['meta']['previousClose']
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            # 獲取歷史價格數據計算趨勢
            quotes = result['indicators']['quote'][0]
            prices = quotes['close']
            
            if len(prices) >= 2:
                week_change = current_price - prices[0]
                week_change_percent = (week_change / prices[0]) * 100
            else:
                week_change = 0
                week_change_percent = 0
            
            return {
                "wheat_price": round(current_price, 2),
                "previous_close": round(previous_close, 2),
                "daily_change": round(change, 2),
                "daily_change_percent": round(change_percent, 2),
                "week_change": round(week_change, 2),
                "week_change_percent": round(week_change_percent, 2),
                "currency": "USD",
                "unit": "per bushel",
                "last_updated": datetime.now().isoformat(),
                "source": "Yahoo Finance"
            }
            
    except Exception as e:
        logging.warning(f"Yahoo Finance 糧食價格抓取失敗: {e}")
        return None

def scrape_food_prices() -> Dict[str, Any]:
    """
    主要的糧食價格爬取函數
    """
    print("正在爬取糧食價格資料...")
    
    # 嘗試 Yahoo Finance
    food_data = scrape_food_prices_yahoo()
    
    if food_data:
        print("成功從 Yahoo Finance 獲取糧食價格")
        return food_data
    
    # 如果失敗，提供模擬數據
    print("糧食價格來源失敗，使用模擬數據")
    current_price = round(random.uniform(500, 800), 2)  # 小麥價格通常在這個範圍
    
    return {
        "wheat_price": current_price,
        "previous_close": round(current_price * random.uniform(0.995, 1.005), 2),
        "daily_change": round(random.uniform(-20, 20), 2),
        "daily_change_percent": round(random.uniform(-3, 3), 2),
        "week_change": round(random.uniform(-50, 50), 2),
        "week_change_percent": round(random.uniform(-5, 5), 2),
        "currency": "USD",
        "unit": "per bushel",
        "last_updated": datetime.now().isoformat(),
        "source": "模擬數據",
        "error": "Using fallback data"
    }

if __name__ == '__main__':
    food_data = scrape_food_prices()
    print("\n--- 爬取的糧食數據 ---")
    print(json.dumps(food_data, indent=2, ensure_ascii=False)) 