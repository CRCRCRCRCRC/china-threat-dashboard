import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

def scrape_food_prices_yahoo() -> Dict[str, Any]:
    """
    使用 Yahoo Finance API 爬取糧食價格 (小麥期貨)
    """
    print("正在透過 Yahoo Finance API 抓取小麥價格...")
    
    try:
        # 使用小麥期貨 (ZW=F) 作為糧食指標
        url = "https://query1.finance.yahoo.com/v8/finance/chart/ZW=F"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            meta = result['meta']
            
            current_price = meta.get('regularMarketPrice', 0)
            prev_close = meta.get('previousClose', 0)
            
            if current_price and prev_close:
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
                
                price_display = f"${current_price:.2f} /bushel"
                change_display = f"{change_percent:+.2f}%"
                
                print(f"抓取完成：小麥價格 {price_display}, 24小時變動 {change_display}")
                
                return {
                    "price": price_display,
                    "price_change": change_display,
                    "sources": {"economic": ["https://finance.yahoo.com/"]}
                }
            else:
                raise ValueError("無法獲取有效的價格數據")
        else:
            raise ValueError("API 回應格式異常")
        
    except Exception as e:
        print(f"Yahoo Finance API 錯誤: {e}")
        raise

def scrape_food_prices_fmp() -> Dict[str, Any]:
    """
    使用 Financial Modeling Prep API 爬取玉米價格
    """
    print("正在透過 Financial Modeling Prep API 抓取玉米價格...")
    
    try:
        # 玉米期貨
        url = "https://financialmodelingprep.com/api/v3/quote/CORNUSD"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            quote = data[0]
            price = quote.get('price', 0)
            
            if price:
                change_percent = quote.get('changesPercentage', 0)
                
                price_display = f"${price:.2f} /bushel"
                change_display = f"{change_percent:+.2f}%"
                
                print(f"抓取完成：玉米價格 {price_display}, 24小時變動 {change_display}")
                
                return {
                    "price": price_display,
                    "price_change": change_display,
                    "sources": {"economic": ["https://financialmodelingprep.com/"]}
                }
            else:
                raise ValueError("無法獲取有效的價格數據")
        else:
            raise ValueError("API 回應為空")
        
    except Exception as e:
        print(f"Financial Modeling Prep API 錯誤: {e}")
        raise

def scrape_food_prices_commodities() -> Dict[str, Any]:
    """
    使用 Commodities API 爪取大豆價格
    """
    print("正在透過 Commodities API 抓取大豆價格...")
    
    try:
        # 大豆期貨 - 免費 API (無需 key)
        url = "https://api.marketdata.app/v1/options/chain/SOYB"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        # 這是一個示例，實際的 API 結構可能不同
        # 在生產環境中需要根據實際 API 調整
        print("注意：此 API 需要進一步調整以獲取實際數據")
        raise Exception("API 需要進一步實作")
        
    except Exception as e:
        print(f"Commodities API 錯誤: {e}")
        raise

def scrape_food_prices() -> Dict[str, Any]:
    """
    主要糧食價格爬取函數，使用多個免費 API 作為備援
    """
    # 定義 API 列表 (按優先順序)
    apis = [
        ("Yahoo Finance (小麥)", scrape_food_prices_yahoo),
        ("Financial Modeling Prep (玉米)", scrape_food_prices_fmp),
    ]
    
    for api_name, api_func in apis:
        try:
            print(f"嘗試使用 {api_name}...")
            return api_func()
        except Exception as e:
            print(f"{api_name} 失敗: {e}")
            continue
    
    # 所有 API 都失敗
    print("❌ 所有糧食價格 API 都失敗，無法獲取真實數據")
    raise Exception("無法從任何 API 獲取糧食價格數據")

if __name__ == '__main__':
    try:
        food_data = scrape_food_prices()
        print("\n=== 糧食價格資料 ===")
        print(f"價格: {food_data['price']}")
        print(f"漲跌幅: {food_data['price_change']}")
        print(f"資料來源: {food_data['sources']}")
    except Exception as e:
        print(f"程式執行失敗: {e}") 