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
            
            if link_tag and title_tag:
                # Google News 連結處理
                href = link_tag['href']
                if href.startswith('./'):
                    href = urljoin(GOOGLE_NEWS_URL, href)
                
                articles.append({
                    'title': title_tag.get_text().strip(),
                    'url': href
                })
        
        return articles
    except Exception as e:
        print(f"搜尋 '{query}' 時發生錯誤: {e}")
        return []

def scrape_news_data() -> Dict[str, Any]:
    """從 Google 新聞搜尋與台海情勢相關的新聞"""
    print("正在爬取相關新聞...")
    
    # 定義關鍵字
    keywords = {
        "economic": [
            "台灣 經濟", "台海 貿易", "兩岸 經濟", "台灣 出口", "半導體"
        ],
        "diplomatic": [
            "台灣 外交", "美台關係", "台日關係", "台歐關係", "國際 台灣"
        ],
        "public_opinion": [
            "台海 民調", "兩岸 民意", "台灣 輿論", "兩岸關係", "台海情勢"
        ]
    }
    
    all_news = {}
    all_sources = {}
    
    for category, keyword_list in keywords.items():
        category_news = []
        category_sources = []
        
        # 隨機選取關鍵字並搜尋
        selected_keywords = random.sample(keyword_list, min(3, len(keyword_list)))
        
        for keyword in selected_keywords:
            articles = _search_google_news(keyword)
            category_news.extend([article['title'] for article in articles])
            category_sources.extend([article['url'] for article in articles])
        
        # 移除重複並限制數量
        category_news = list(dict.fromkeys(category_news))[:10]
        category_sources = list(dict.fromkeys(category_sources))[:10]
        
        all_news[category] = category_news
        all_sources[category] = category_sources
        
        # 如果沒有取得新聞，使用備用資料
        if not category_news:
            all_news[category] = [f"模擬 {category} 新聞標題 1 (備用資料)"]
            all_sources[category] = [GOOGLE_NEWS_URL]

    print("新聞爬取完成。")
    return {
        "economic_news": all_news.get("economic", []),
        "diplomatic_news": all_news.get("diplomatic", []),
        "public_opinion_news": all_news.get("public_opinion", []),
        "sources": all_sources
    }

if __name__ == '__main__':
    news_data = scrape_news_data()
    print("\n--- 爬取的新聞資料 ---")
    print(f"經濟新聞: {news_data['economic_news']}")
    print(f"外交新聞: {news_data['diplomatic_news']}")
    print(f"輿情新聞: {news_data['public_opinion_news']}")
    print(f"資料來源: {news_data['sources']}")
