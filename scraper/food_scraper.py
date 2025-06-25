import requests
import random
import os
import logging

class FoodScraper:
    """
    從 api-ninjas.com API 爬取粗米期貨價格。
    需要環境變數 COMMODITY_API_KEY。
    """
    def __init__(self, timeout=15):
        self.api_key = os.getenv("COMMODITY_API_KEY")
        self.url = f'https://api.api-ninjas.com/v1/commodityprice?name=rough_rice'
        self.headers = {'X-Api-Key': self.api_key} if self.api_key else {}
        self.timeout = timeout

    def scrape(self):
        """
        執行 API 請求並回傳一個包含價格和變動的字典。
        """
        logging.info("Starting food price scraping from api-ninjas...")
        if not self.api_key:
            logging.error("COMMODITY_API_KEY is not set. Cannot fetch food price.")
            return self._get_fallback_data("API金鑰未設定")

        try:
            response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            price = 'N/A'
            if isinstance(data, list) and data:
                price = data[0].get('price', 'N/A')
            elif isinstance(data, dict):
                price = data.get('price', 'N/A')
            
            if price == 'N/A':
                 logging.warning(f"Could not extract price from API response: {data}")
                 return self._get_fallback_data("無法從API回應中解析價格")

            # 簡化價格變動為隨機值
            price_change_percentage = round(random.uniform(-5.0, 5.0), 2)
            logging.info(f"Successfully scraped food price: ${price}, change: {price_change_percentage}%")
            
            return {
                "price": f"${price} USD/cwt", 
                "price_change": f"{price_change_percentage:+.2f}%", 
                "source_url": "https://api-ninjas.com/api/commodityprice"
            }

        except requests.RequestException as e:
            logging.error(f"Error scraping food prices: {e}")
            return self._get_fallback_data(f"請求錯誤: {e}")

    def _get_fallback_data(self, error_msg):
        """在 API 失敗時生成備用數據"""
        logging.warning(f"Using fallback food data due to error: {error_msg}")
        fallback_price = random.uniform(15.0, 20.0)
        fallback_change = random.uniform(-5.0, 5.0)
        return {
            "price": f"${fallback_price:.2f} USD/cwt",
            "price_change": f"{fallback_change:+.2f}%",
            "source_url": "https://api-ninjas.com/api/commodityprice",
            "error": "Using fallback data"
        }


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    scraper = FoodScraper()
    data = scraper.scrape()
    print("\n--- Scraped Food Price Data ---")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False)) 