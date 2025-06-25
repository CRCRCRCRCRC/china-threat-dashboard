import logging
import os
from gnews import GNews
from datetime import datetime, timedelta

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

    def scrape(self):
        """
        Scrapes news for all defined categories and compiles the results.
        """
        logging.info("Starting news scraping from GNews...")
        all_news = {}
        total_articles = 0
        all_sources = {}

        for category, query in self.categories.items():
            logging.info(f"Fetching news for category: {category}")
            try:
                articles = self.gnews.get_news(query)
                if articles:
                    all_news[category] = articles
                    total_articles += len(articles)
                    for article in articles:
                        all_sources[article['publisher']['title']] = article['publisher']['href']
                    logging.info(f"Found {len(articles)} articles for category '{category}'.")
                else:
                    logging.warning(f"No news found for category '{category}', using fallback data.")
                    all_news[category] = self._get_fallback_data(category)
            except Exception as e:
                logging.error(f"Error fetching GNews for category '{category}': {e}", exc_info=True)
                all_news[category] = self._get_fallback_data(category)
        
        logging.info(f"News scraping complete. Total articles found: {total_articles}")
        
        return {
            "total_news_count": total_articles,
            "news_by_category": all_news,
            "sources": all_sources
        }

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
    logging.basicConfig(level=logging.INFO)
    scraper = NewsScraper()
    results = scraper.scrape()
    import json
    print(json.dumps(results, indent=2, ensure_ascii=False))
