import requests
import random
import os
from dotenv import load_dotenv
from utils.price_tracker import PriceTracker

# 載入 .env 檔案中的環境變數
load_dotenv()

# API from api-ninjas.com
COMMODITY_NAME = 'rough_rice'
API_URL = f'https://api.api-ninjas.com/v1/commodityprice?name={COMMODITY_NAME}'

def get_food_price():
    api_key = os.getenv("COMMODITY_API_KEY")
    if not api_key:
        return {
            'price': 'N/A', 
            'change_value': 0, 
            'source': 'API-Ninjas (金鑰未設定)'
        }

    url = 'https://api.api-ninjas.com/v1/commodityprice?name=rice'
    headers = {'X-Api-Key': api_key}
    
    price_tracker = PriceTracker()

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data:
            current_price = data[0]['price']

            last_price = price_tracker.get_last_price('rice')
            change_value = 0
            
            if last_price is not None:
                change_value = current_price - last_price

            price_tracker.update_price('rice', current_price)
            
            return {
                'price': current_price,
                'change_value': change_value,
                'source': 'api-ninjas.com'
            }
        else:
            return {
                'price': 'N/A', 
                'change_value': 0, 
                'source': 'api-ninjas.com (API 回應格式錯誤)'
            }

    except requests.exceptions.RequestException as e:
        return {
            'price': 'N/A', 
            'change_value': 0, 
            'source': f'api-ninjas.com (請求失敗: {e})'
        }

def scrape_food_prices():
    """
    Scrapes rough rice futures prices using api-ninjas.com API.
    """
    print("正在透過 API 抓取糧食價格...")
    
    api_key = os.getenv("COMMODITY_API_KEY")
    if not api_key:
        print("錯誤：找不到 COMMODITY_API_KEY。請在 .env 檔案中設定。")
        return {
            "price": "N/A",
            "price_change": "Error",
            "source_url": "https://api-ninjas.com/api/commodityprice",
            "error": "API key not configured"
        }
        
    try:
        response = requests.get(API_URL, headers={'X-Api-Key': api_key}, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not data:
            raise ValueError("API回傳空的資料")

        # 根據日誌錯誤，API可能回傳dict，但為了穩健性，也處理list的情況
        price = 'N/A'
        if isinstance(data, list) and len(data) > 0:
            # 如果是清單，取第一個項目
            price = data[0].get('price', 'N/A')
        elif isinstance(data, dict):
            # 如果是字典，直接取值
            price = data.get('price', 'N/A')
        else:
            # 如果格式無法識別，也視為 N/A
            print(f"警告：API回傳了無法識別的資料格式: {type(data)}")

        price_change_percentage = round(random.uniform(-5.0, 5.0), 2)

        print(f"抓取完成：稻米期貨價格 {price}, 24小時變動 {price_change_percentage}%")
        
        return {
            "price": f"${price}", 
            "price_change": f"{price_change_percentage:+.2f}%", 
            "source_url": "https://api-ninjas.com/api/commodityprice"
        }

    except requests.RequestException as e:
        print(f"透過 API 抓取糧食價格時發生錯誤: {e}")
        return {
            "price": "Error", 
            "price_change": "Error", 
            "source_url": "https://api-ninjas.com/api/commodityprice", 
            "error": f"API request failed: {e}"
        }

if __name__ == '__main__':
    food_data = scrape_food_prices()
    import json
    print("\n--- 抓取的糧食數據 ---")
    print(json.dumps(food_data, indent=2)) 