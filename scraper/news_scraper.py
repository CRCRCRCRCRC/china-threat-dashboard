import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import logging

class NewsScraper:
    """
    從 Google 新聞爬取與台灣相關的經濟、外交和輿情新聞。
    """
    def __init__(self, timeout=15):
        self.base_url = "https://news.google.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = timeout
        self.news_keywords = {
            "economic": ["台灣 中國 經濟制裁", "台灣 出口禁令", "ECFA"],
            "diplomatic": ["台灣 外交聲明", "美國 台灣關係法", "中國 軍事威脅 譴責"],
            "public_opinion": ["台灣民意調查 統一", "台灣 國防信心", "台灣社會輿論 兩岸"]
        }

    def _search(self, query):
        """輔助函式，用於搜尋特定關鍵字的 Google 新聞。"""
        formatted_query = quote_plus(query)
        search_url = f"{self.base_url}/search?q={formatted_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            for article_div in soup.find_all('div', {'class': 'SoaBEf'}, limit=5):
                link_tag = article_div.find('a', href=True)
                title_tag = article_div.find('h3') # Google's structure may use h3 now
                if not title_tag:
                     title_tag = article_div.find('div', {'role': 'heading'})

                if link_tag and title_tag:
                    title = title_tag.get_text(strip=True)
                    relative_url = link_tag['href'].lstrip('.')
                    url = urljoin(self.base_url, relative_url)
                    articles.append({"title": title, "url": url})
            return articles

        except requests.RequestException as e:
            logging.error(f"Error searching Google News for '{query}': {e}")
            return []

    def scrape(self):
        """
        執行所有類別的新聞爬取並回傳結構化資料。
        """
        logging.info("Starting news scraping from Google News...")
        
        all_news = {}
        all_sources = {}

        for category, keywords in self.news_keywords.items():
            query = " OR ".join(keywords)
            articles = self._search(query)
            
            all_news[category] = [article["title"] for article in articles]
            all_sources[category] = [article["url"] for article in articles]

            if not all_news[category]:
                logging.warning(f"No news found for category '{category}', using fallback data.")
                all_news[category] = [f"無法獲取相關新聞（{category}）"]
                all_sources[category] = [self.base_url]

        logging.info("News scraping complete.")
        return {
            "economic_news": all_news.get("economic", []),
            "diplomatic_news": all_news.get("diplomatic", []),
            "public_opinion_news": all_news.get("public_opinion", []),
            "sources": all_sources
        }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    scraper = NewsScraper()
    data = scraper.scrape()
    print("\n--- Scraped News Data ---")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))
