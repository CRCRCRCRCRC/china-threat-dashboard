import os
import requests
import logging

class GoldScraper:
    """
    從 Metalprice API 獲取最新的黃金價格。
    需要環境變數 METALPRICE_API_KEY。
    """
    def __init__(self):
        self.api_key = os.getenv("METALPRICE_API_KEY")
        self.api_url = f"https://api.metalpriceapi.com/v1/latest?api_key={self.api_key}&base=USD&currencies=TWD"

    def scrape(self):
        """
        執行 API 請求並回傳黃金價格（新台幣/盎司）。
        """
        logging.info("Starting gold price scraping...")
        if not self.api_key:
            logging.error("METALPRICE_API_KEY is not set. Cannot fetch gold price.")
            return {"error": "API金鑰未設定，無法獲取黃金價格。"}

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
                
                logging.info(f"Successfully scraped gold price: TWD {price_twd_per_gram:.2f}/gram")
                return {
                    "price_twd_per_gram": round(price_twd_per_gram, 2),
                    "source": "metalpriceapi.com"
                }
            else:
                error_message = data.get('error', {}).get('info', '未知API錯誤')
                logging.error(f"Metalprice API returned an error: {error_message}")
                return {"error": f"API錯誤: {error_message}"}

        except requests.RequestException as e:
            logging.error(f"Error scraping gold price: {e}")
            return {"error": f"請求錯誤: {e}"}

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    scraper = GoldScraper()
    price_data = scraper.scrape()
    print("\n--- Scraped Gold Price Data ---")
    import json
    print(json.dumps(price_data, indent=2, ensure_ascii=False)) 