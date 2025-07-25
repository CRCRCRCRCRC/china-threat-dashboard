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
                
                price_display = f"${current_price:.2f} / oz"
                change_display = f"{change_percent:+.2f}%"
                
                print(f"抓取完成：黃金價格 {price_display}, 24小時變動 {change_display}")
                
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

def scrape_gold_prices_fmp() -> Dict[str, Any]:
    """
    使用 Financial Modeling Prep API 爬取黃金價格 (免費 250 次/日)
    """
    print("正在透過 Financial Modeling Prep API 抓取黃金價格...")
    
    try:
        # 黃金對美元匯率
        url = "https://financialmodelingprep.com/api/v3/quote/XAUUSD"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            quote = data[0]
            price = quote.get('price', 0)
            
            if price:
                change_percent = quote.get('changesPercentage', 0)
                
                price_display = f"${price:.2f} / oz"
                change_display = f"{change_percent:+.2f}%"
                
                print(f"抓取完成：黃金價格 {price_display}, 24小時變動 {change_display}")
                
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

def scrape_gold_prices() -> Dict[str, Any]:
    """
    主要黃金價格爬取函數，使用多個免費 API 作為備援
    """
    apis = [
        ("Yahoo Finance", scrape_gold_prices_yahoo),
        ("Financial Modeling Prep", scrape_gold_prices_fmp)
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

if __name__ == '__main__':
    gold_data = scrape_gold_prices()
    import json
    print("\n--- 抓取的黃金數據 ---")
    print(json.dumps(gold_data, indent=2, ensure_ascii=False)) 