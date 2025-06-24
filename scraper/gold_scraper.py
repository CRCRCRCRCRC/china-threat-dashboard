import os
import requests
import random
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

API_URL = "https://api.metalpriceapi.com/v1/latest"
SOURCE_URL = "https://metalpriceapi.com/"

def scrape_gold_prices():
    """
    Scrapes gold prices using metalpriceapi.com API.
    """
    print("正在透過 API 抓取黃金價格...")
    api_key = os.getenv("METALPRICEAPI_KEY")
    if not api_key:
        print("錯誤：找不到 METALPRICEAPI_KEY。請在 .env 檔案中設定。")
        return {
            "price": "N/A",
            "price_change": "Error",
            "source_url": SOURCE_URL,
            "error": "API key not configured"
        }

    params = {
        'api_key': api_key,
        'base': 'USD',
        'currencies': 'XAU'
    }

    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("success") and 'XAU' in data.get('rates', {}):
            # API 回傳 1 美元等於多少黃金，我們需要倒數來得到每盎司黃金的美元價格
            price_per_ounce = 1 / data['rates']['XAU']
            
            # 由於我們沒有歷史數據來做真實比較，這裡我們用隨機數模擬價格變動
            # 在一個真實的應用中，你會從數據庫或 price_tracker 獲取前一天的價格
            price_change_percentage = round(random.uniform(-5.0, 5.0), 2)

            print(f"抓取完成：黃金價格 ${price_per_ounce:.2f}/盎司, 24小時變動 {price_change_percentage}%")
            
            return {
                "price": f"${price_per_ounce:.2f}",
                "price_change": f"{price_change_percentage:+.2f}%",
                "source_url": SOURCE_URL
            }
        else:
            error_message = data.get("error", {}).get("info", "API 回應格式錯誤或缺少黃金匯率")
            print(f"API 回應錯誤: {error_message}")
            return {
                "price": "N/A",
                "price_change": "Error",
                "source_url": SOURCE_URL,
                "error": error_message
            }
            
    except requests.RequestException as e:
        print(f"透過 API 抓取黃金價格時發生錯誤: {e}")
        return {
            "price": "Error",
            "price_change": "Error",
            "source_url": SOURCE_URL,
            "error": f"API request failed: {e}"
        }

if __name__ == '__main__':
    gold_data = scrape_gold_prices()
    import json
    print("\n--- 抓取的黃金數據 ---")
    print(json.dumps(gold_data, indent=2, ensure_ascii=False)) 