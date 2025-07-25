<<<<<<< HEAD
import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import quote_plus, urljoin
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Google News 基礎 URL
GOOGLE_NEWS_URL = "https://news.google.com"

def _search_google_news(query: str) -> List[Dict[str, str]]:
    """輔助函式，用於搜尋特定關鍵字的 Google 新聞"""
    formatted_query = quote_plus(query)
    search_url = f"{GOOGLE_NEWS_URL}/search?q={formatted_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        response = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles: List[Dict[str, str]] = []
        # Google News 的 HTML 結構可能會變，此選擇器相對穩定
        for article_div in soup.find_all('div', {'class': 'SoaBEf'}, limit=8):
            if not isinstance(article_div, Tag):
                continue

            link_tag = article_div.find('a', href=True)
            # 'role' is an attribute, so we search it in attrs
            title_tag = article_div.find('div', attrs={'role': 'heading'})

            if (link_tag and isinstance(link_tag, Tag) and
                title_tag and isinstance(title_tag, Tag)):
                
                title = title_tag.get_text().strip()
                href = link_tag.get('href')

                if href and isinstance(href, str) and title:
                    # 相對路徑轉絕對路徑
                    url = urljoin(GOOGLE_NEWS_URL, href)
                    articles.append({"title": title, "url": url})

        return articles

    except requests.RequestException as e:
        print(f"搜尋 Google 新聞 '{query}' 時發生錯誤: {e}")
        return []

def scrape_news_data() -> Dict[str, Any]:
    """從 Google 新聞爬取經濟、外交和輿情相關新聞"""
    print("正在從 Google News 爬取新聞資料...")

    news_keywords: Dict[str, List[str]] = {
        "economic": ["台灣 中國 經濟制裁", "台灣 出口禁令", "ECFA"],
        "diplomatic": ["台灣 外交聲明", "美國 台灣關係法", "中國 軍事威脅 譴責"],
        "public_opinion": ["台灣民意調查 統一", "台灣 國防信心", "台灣社會輿論 兩岸"]
    }

    all_news: Dict[str, List[str]] = {}
    all_sources: Dict[str, List[str]] = {}

    for category, keywords in news_keywords.items():
        query: str = " OR ".join(keywords)
        articles: List[Dict[str, str]] = _search_google_news(query)
        
        all_news[category] = [article["title"] for article in articles]
        all_sources[category] = [article["url"] for article in articles]

        if not all_news[category]:
            all_news[category] = [f"模擬 {category} 新聞標題 1 (備用資料)"]
            all_sources[category] = [GOOGLE_NEWS_URL]

    print("新聞爬取完成。")
    return {
        "economic_news": all_news.get("economic", []),
        "diplomatic_news": all_news.get("diplomatic", []),
        "public_opinion_news": all_news.get("public_opinion", []),
        "sources": all_sources
    }
=======
import logging
import os
from gnews import GNews
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

class NewsScraper:
    """
    A scraper for fetching news articles related to Taiwan from Google News.
    """
    def __init__(self):
        self.gnews = GNews(language='zh-Hant', country='TW', period='7d')
        self.categories = {
            "military": '("共機" OR "共艦" OR "擾台" OR "國防部" OR "台灣軍事") AND ("演習" OR "威脅" OR "動態")',
            "economic": '("台灣經濟" OR "台股") AND ("中國影響" OR "貿易戰" OR "供應鏈")',
            "diplomatic": '"台灣外交" AND ("美國" OR "中國" OR "國際空間" OR "邦交國")',
            "public_opinion": '"台灣民意調查" AND ("統一" OR "獨立" OR "兩岸關係" OR "國防信心")'
        }

    def _fetch_category(self, category, query):
        """Fetches news for a single category."""
        logging.info(f"Fetching news for category: {category}")
        try:
            articles = self.gnews.get_news(query)
            if articles:
                logging.info(f"Found {len(articles)} articles for category '{category}'.")
                return category, articles
            else:
                logging.warning(f"No news found for category '{category}', using fallback.")
                return category, self._get_fallback_data(category)
        except Exception as e:
            # This is often due to network issues or being blocked by the provider.
            logging.error(f"Error fetching GNews for category '{category}': {e}")
            return category, self._get_fallback_data(category)

    def scrape(self):
        """
        Scrapes news for all defined categories concurrently and compiles the results.
        """
        logging.info("Starting concurrent news scraping from GNews...")
        all_news = {}
        total_articles = 0
        all_sources = {}

        with ThreadPoolExecutor(max_workers=len(self.categories)) as executor:
            future_to_category = {executor.submit(self._fetch_category, category, query): category for category, query in self.categories.items()}
            
            for future in as_completed(future_to_category):
                category, articles = future.result()
                all_news[category] = articles
                
                # Exclude fallback data from total count and source collection
                if not (len(articles) == 1 and articles[0]['url'] == '#'):
                    total_articles += len(articles)
                    for article in articles:
                        if article.get('publisher') and isinstance(article['publisher'], dict):
                            all_sources[article['publisher']['title']] = article['publisher']['href']

        logging.info(f"News scraping complete. Total valid articles found: {total_articles}")
        
        return {
            "total_news_count": total_articles,
            "news_by_category": all_news,
            "sources": all_sources
        }
>>>>>>> 582f439752d7dd09671e0ddbe1ded2923f47c81d

    def _get_fallback_data(self, category):
        """Provides fallback data for a given category when scraping fails."""
        logging.warning(f"Using fallback data for news category: {category}")
        return [{
            'title': f'無法載入「{category}」類別新聞',
            'description': '由於網路連線或來源網站問題，暫時無法取得即時新聞。',
            'published date': (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            'url': '#',
            'publisher': {'title': '系統訊息', 'href': '#'}
        }]

if __name__ == '__main__':
<<<<<<< HEAD
    news_data = scrape_news_data()
    print("\n--- 爬取的新聞資料 ---")
    print(f"經濟新聞: {news_data['economic_news']}")
    print(f"外交新聞: {news_data['diplomatic_news']}")
    print(f"輿情新聞: {news_data['public_opinion_news']}")
    print(f"資料來源: {news_data['sources']}")
=======
    logging.basicConfig(level=logging.INFO)
    scraper = NewsScraper()
    results = scraper.scrape()
    import json
    print(json.dumps(results, indent=2, ensure_ascii=False))
>>>>>>> 582f439752d7dd09671e0ddbe1ded2923f47c81d
