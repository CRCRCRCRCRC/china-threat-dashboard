import os
import requests
import logging
import random

class GoldScraper:
    """
    從 Metalprice API 獲取最新的黃金價格。
    需要環境變數 METALPRICE_API_KEY。
    """
    def __init__(self):
        self.api_key = os.getenv("METALPRICE_API_KEY")
        self.url = "https://api.metalpriceapi.com/v1/"
        self.api_url = f"{self.url}latest?api_key={self.api_key}&base=USD&currencies=TWD,XAU"

    def scrape(self):
        """
        執行 API 請求並回傳黃金價格（新台幣/公克）。
        """
        logging.info("Starting gold price scraping...")
        if not self.api_key:
            logging.error("METALPRICE_API_KEY is not set. Cannot fetch gold price.")
            return self._get_fallback_data("API金鑰未設定")

        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                troy_ounce_to_gram = 31.1035
                price_usd_per_oz = 1 / data['rates']['XAU']
                price_twd_per_usd = data['rates']['TWD']
                
                price_twd_per_oz = price_usd_per_oz * price_twd_per_usd
                price_twd_per_gram = price_twd_per_oz / troy_ounce_to_gram
                
                # 為了計算變動，我們需要前一天的數據（這裡先簡化為隨機）
                price_change_percentage = random.uniform(-2.5, 2.5)

                logging.info(f"Successfully scraped gold price: TWD {price_twd_per_gram:.2f}/gram")
                return {
                    "price": f"{price_twd_per_gram:,.2f} TWD/g",
                    "price_change": f"{price_change_percentage:+.2f}%",
                    "source_url": "metalpriceapi.com"
                }
            else:
                error_message = data.get('error', {}).get('info', '未知API錯誤')
                logging.error(f"Metalprice API returned an error: {error_message}")
                return self._get_fallback_data(f"API錯誤: {error_message}")

        except requests.RequestException as e:
            logging.error(f"Error scraping gold price: {e}")
            return self._get_fallback_data(f"請求錯誤: {e}")

    def _get_fallback_data(self, error_msg):
        """在 API 失敗時生成備用數據"""
        logging.warning(f"Using fallback gold data due to error: {error_msg}")
        fallback_price = random.uniform(2200, 2500)
        fallback_change = random.uniform(-2.5, 2.5)
        return {
            "price": f"{fallback_price:,.2f} TWD/g",
            "price_change": f"{fallback_change:+.2f}%",
            "source_url": self.url,
            "error": "Using fallback data"
        }

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    scraper = GoldScraper()
    price_data = scraper.scrape()
    print("\n--- Scraped Gold Price Data ---")
    import json
    print(json.dumps(price_data, indent=2, ensure_ascii=False)) 