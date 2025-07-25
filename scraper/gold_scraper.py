import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

def scrape_gold_prices_yahoo() -> Dict[str, Any]:
    """
    使用 Yahoo Finance API 爬取黃金價格 (完全免費，無需 API key)
    """
    print("正在透過 Yahoo Finance API 抓取黃金價格...")
    
    try:
        # 使用黃金期貨 (GC=F) 獲取即時價格
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data['chart']['result'][0]
        meta = result['meta']
        
        current_price_usd = meta['regularMarketPrice']
        previous_close = meta['previousClose']
        
        # 簡單的匯率轉換 (實際應用中應該獲取即時匯率)
        usd_to_twd = 31.5  # 大概的匯率
        price_twd_per_oz = current_price_usd * usd_to_twd
        
        # 1 盎司 = 31.1035 公克
        price_twd_per_gram = price_twd_per_oz / 31.1035
        
        change_percent = ((current_price_usd - previous_close) / previous_close) * 100
        
        print(f"✅ Yahoo Finance API 成功: 黃金價格 ${current_price_usd:.2f}/盎司")
        
        return {
            "current_price_usd_per_oz": round(current_price_usd, 2),
            "current_price_twd_per_gram": round(price_twd_per_gram, 2),
            "change_percent": round(change_percent, 2),
            "last_updated": datetime.now().isoformat(),
            "source": "Yahoo Finance",
            "currency": "USD"
        }
        
    except Exception as e:
        print(f"Yahoo Finance API 錯誤: {e}")
        raise

def scrape_gold_prices_metals() -> Dict[str, Any]:
    """
    使用 Metals API 爬取黃金價格 (需要 API key，但有免費額度)
    """
    print("正在透過 Metals API 抓取黃金價格...")
    
    try:
        # 如果沒有 API key，直接拋出異常
        api_key = "YOUR_METALS_API_KEY"  # 請替換為實際的 API key
        if api_key == "YOUR_METALS_API_KEY":
            raise Exception("Metals API key 未設定")
        
        url = f"https://api.metals.live/v1/spot/gold?api_key={api_key}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current_price_usd = data['price']
        
        # 簡單的匯率轉換
        usd_to_twd = 31.5
        price_twd_per_oz = current_price_usd * usd_to_twd
        price_twd_per_gram = price_twd_per_oz / 31.1035
        
        print(f"✅ Metals API 成功: 黃金價格 ${current_price_usd:.2f}/盎司")
        
        return {
            "current_price_usd_per_oz": round(current_price_usd, 2),
            "current_price_twd_per_gram": round(price_twd_per_gram, 2),
            "change_percent": 0,  # Metals API 可能不提供變化百分比
            "last_updated": datetime.now().isoformat(),
            "source": "Metals API",
            "currency": "USD"
        }
        
    except Exception as e:
        print(f"Metals API 錯誤: {e}")
        raise

def scrape_gold_prices() -> Dict[str, Any]:
    """
    主要的黃金價格爬取函數，會嘗試多個 API 直到成功為止
    """
    # 定義 API 列表 (按優先順序)
    apis = [
        ("Yahoo Finance API", scrape_gold_prices_yahoo),
        ("Metals API", scrape_gold_prices_metals),
    ]
    
    for api_name, api_func in apis:
        try:
            print(f"嘗試使用 {api_name}...")
            return api_func()
        except Exception as e:
            print(f"{api_name} 失敗: {e}")
            continue
    
    # 所有 API 都失敗
    print("❌ 所有黃金價格 API 都失敗，無法獲取真實數據")
    raise Exception("無法從任何 API 獲取黃金價格數據")

if __name__ == "__main__":
    try:
        gold_data = scrape_gold_prices()
        print("\n=== 黃金價格資料 ===")
        print(f"美元/盎司: ${gold_data['current_price_usd_per_oz']}")
        print(f"新台幣/公克: NT${gold_data['current_price_twd_per_gram']}")
        print(f"漲跌幅: {gold_data['change_percent']:.2f}%")
        print(f"資料來源: {gold_data['source']}")
        print(f"更新時間: {gold_data['last_updated']}")
    except Exception as e:
        print(f"程式執行失敗: {e}") 