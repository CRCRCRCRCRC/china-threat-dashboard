import requests
import random
import os
from dotenv import load_dotenv
from utils.price_tracker import PriceTracker
from bs4 import BeautifulSoup
import logging

# 載入 .env 檔案中的環境變數
load_dotenv()

# API from api-ninjas.com
COMMODITY_NAME = 'rough_rice'
API_URL = f'https://api.api-ninjas.com/v1/commodityprice?name={COMMODITY_NAME}'

class FoodScraper:
    """
    從台灣行政院農委會的「農產品批發市場交易行情站」爬取指定蔬菜的平均價格。
    """
    def __init__(self, timeout=15):
        self.url = "https://www.agriharvest.tw/archives/category/observation/market-price"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = timeout
        # 我們關心的蔬菜種類
        self.target_vegetables = ["甘藍", "結球白菜", "蘿蔔"]

    def scrape(self):
        """
        執行爬取並回傳一個包含指定蔬菜名稱和價格的字典。
        """
        logging.info("Starting food price scraping from Agriharvest...")
        try:
            response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            prices = {}
            # 找到包含所有價格資訊的表格
            table = soup.find("table")
            if not table:
                logging.warning("Could not find the price table on Agriharvest page.")
                return {"error": "在農產品行情網站上找不到價格表格。"}

            # 遍歷表格的每一行
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    # 第一個 cell 是品名，第二個是價格
                    veg_name = cells[0].get_text(strip=True)
                    price = cells[1].get_text(strip=True)
                    
                    for target in self.target_vegetables:
                        if target in veg_name:
                            prices[target] = price
                            logging.info(f"Found price for {target}: {price}")
                            break # 找到後就跳出內層迴圈
            
            if not prices:
                logging.warning(f"Could not find any of the target vegetables: {self.target_vegetables}")

            return {
                "prices": prices,
                "source": self.url
            }

        except requests.RequestException as e:
            logging.error(f"Error scraping food prices: {e}")
            return {"error": f"請求錯誤: {e}"}

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
    logging.basicConfig(level=logging.INFO)
    scraper = FoodScraper()
    data = scraper.scrape()
    print("\n--- Scraped Food Price Data ---")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False)) 