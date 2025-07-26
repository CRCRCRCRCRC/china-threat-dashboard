import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import quote_plus, urljoin
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

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
            title_tag = article_div.find('div', attrs={'role': 'heading'})
            time_tag = article_div.find('time')
            
            # 抓取來源資訊
            source_tag = article_div.find('div', attrs={'data-n-tid': lambda x: x and 'source' in x})
            
            if link_tag and title_tag:
                # Google News 的連結需要處理
                href = link_tag.get('href', '')
                if href.startswith('./'):
                    href = href[2:]  # 移除 './'
                full_url = urljoin(GOOGLE_NEWS_URL, href)
                
                article = {
                    'title': title_tag.get_text(strip=True),
                    'url': full_url,
                    'published_date': time_tag.get('datetime', '') if time_tag else '',
                    'source': source_tag.get_text(strip=True) if source_tag else '未知來源'
                }
                articles.append(article)
        
        return articles
        
    except Exception as e:
        logging.warning(f"搜尋 Google 新聞時發生錯誤 (查詢: {query}): {e}")
        return []

def scrape_news_data() -> Dict[str, Any]:
    """
    從 Google 新聞抓取與中國相關的新聞資料
    """
    print("正在從 Google 新聞抓取相關新聞...")
    
    try:
        # 定義搜尋關鍵字
        economic_keywords = ["中國經濟", "中美貿易", "台海經濟", "兩岸貿易"]
        diplomatic_keywords = ["中國外交", "兩岸關係", "台海情勢", "中美關係"]
        opinion_keywords = ["中國輿情", "兩岸民意", "台海局勢", "中國社會"]
        
        economic_news = []
        diplomatic_news = []
        public_opinion_news = []
        sources = []
        
        # 搜尋經濟相關新聞
        for keyword in economic_keywords[:2]:  # 限制搜尋數量避免超時
            articles = _search_google_news(keyword)
            economic_news.extend(articles)
            
        # 搜尋外交相關新聞
        for keyword in diplomatic_keywords[:2]:
            articles = _search_google_news(keyword)
            diplomatic_news.extend(articles)
            
        # 搜尋輿情相關新聞
        for keyword in opinion_keywords[:2]:
            articles = _search_google_news(keyword)
            public_opinion_news.extend(articles)
        
        # 收集所有來源
        all_articles = economic_news + diplomatic_news + public_opinion_news
        sources = list(set([article['source'] for article in all_articles if article['source']]))
        
        # 如果沒有抓到新聞，提供備用資料
        if not all_articles:
            logging.warning("無法從 Google 新聞抓取到任何文章，使用備用資料")
            return _get_fallback_news_data()
        
        return {
            "economic_news": economic_news[:5],  # 限制數量
            "diplomatic_news": diplomatic_news[:5],
            "public_opinion_news": public_opinion_news[:5],
            "sources": sources[:10],  # 限制來源數量
            "total_articles": len(all_articles)
        }
        
    except Exception as e:
        logging.error(f"抓取新聞資料時發生錯誤: {e}")
        return _get_fallback_news_data()

def _get_fallback_news_data() -> Dict[str, Any]:
    """提供備用新聞資料"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    fallback_articles = [
        {
            'title': '中美貿易關係持續關注中',
            'url': '#',
            'published_date': current_time,
            'source': '財經新聞'
        },
        {
            'title': '兩岸關係發展備受矚目',
            'url': '#',
            'published_date': current_time,
            'source': '政治新聞'
        },
        {
            'title': '台海局勢持續穩定發展',
            'url': '#',
            'published_date': current_time,
            'source': '國際新聞'
        }
    ]
    
    return {
        "economic_news": [fallback_articles[0]],
        "diplomatic_news": [fallback_articles[1]],
        "public_opinion_news": [fallback_articles[2]],
        "sources": ['財經新聞', '政治新聞', '國際新聞'],
        "total_articles": 3,
        "error": "Using fallback data"
    }

if __name__ == '__main__':
    news_data = scrape_news_data()
    print("\n--- 爬取的新聞資料 ---")
    print(f"經濟新聞: {news_data['economic_news']}")
    print(f"外交新聞: {news_data['diplomatic_news']}")
    print(f"輿情新聞: {news_data['public_opinion_news']}")
    print(f"資料來源: {news_data['sources']}")
