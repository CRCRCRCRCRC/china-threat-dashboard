import requests
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

def scrape_food_prices_yahoo() -> Dict[str, Any]:
    """
    從 Yahoo Finance 抓取小麥價格資料
    """
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/ZW=F"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        params = {
            'interval': '1d',
            'range': '7d'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            
            # 獲取價格數據
            timestamps = result['timestamp']
            prices = result['indicators']['quote'][0]['close']
            
            # 過濾掉 None 值
            valid_prices = [p for p in prices if p is not None]
            
            if not valid_prices:
                return None
                
            current_price = valid_prices[-1]
            previous_close = valid_prices[-2] if len(valid_prices) > 1 else current_price
            
            # 計算日變化
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
            
            # 計算7天內的價格變化
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
                "unit": "蒲式耳",
                "last_updated": datetime.now().isoformat(),
                "source": "Yahoo Finance"
            }
            
    except Exception as e:
        logging.warning(f"Yahoo Finance 小麥價格抓取失敗: {e}")
        return None

def scrape_food_prices() -> Dict[str, Any]:
    """
    主要的食品價格爬取函數
    """
    print("正在爬取食品價格資料...")
    
    # 嘗試 Yahoo Finance
    food_data = scrape_food_prices_yahoo()
    
    if food_data:
        print("成功從 Yahoo Finance 獲取小麥價格")
        return food_data
    
    # 如果失敗，提供模擬數據
    print("小麥價格來源失敗，使用模擬數據")
    current_price = round(random.uniform(5.0, 8.0), 2)
    
    return {
        "wheat_price": current_price,
        "previous_close": round(current_price * random.uniform(0.995, 1.005), 2),
        "daily_change": round(random.uniform(-0.5, 0.5), 2),
        "daily_change_percent": round(random.uniform(-5, 5), 2),
        "week_change": round(random.uniform(-1, 1), 2),
        "week_change_percent": round(random.uniform(-10, 10), 2),
        "currency": "USD",
        "unit": "蒲式耳",
        "last_updated": datetime.now().isoformat(),
        "source": "模擬數據",
        "error": "Using fallback data"
    }

if __name__ == '__main__':
    data = scrape_food_prices()
    print(json.dumps(data, indent=2, ensure_ascii=False)) 