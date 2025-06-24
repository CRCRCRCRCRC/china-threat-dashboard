import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import quote_plus, urljoin
import random
from datetime import datetime, timedelta

# Google News 基礎 URL
GOOGLE_NEWS_URL = "https://news.google.com"

def _search_google_news(query):
    """輔助函式，用於搜尋特定關鍵字的 Google 新聞"""
    formatted_query = quote_plus(query)
    search_url = f"{GOOGLE_NEWS_URL}/search?q={formatted_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    try:
        response = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        # Google News 的 HTML 結構可能會變，此選擇器相對穩定
        for article_div in soup.find_all('div', {'class': 'SoaBEf'}, limit=8):
            title = "N/A"
            url = None

            # 確保 article_div 是 Tag 類型
            if not isinstance(article_div, Tag):
                continue

            link_tag = article_div.find('a', href=True)
            if link_tag and isinstance(link_tag, Tag):
                # 獲取標題
                title_tag = article_div.find('div', {'role': 'heading'})
                if title_tag and isinstance(title_tag, Tag):
                    title = title_tag.get_text().strip()

                # 獲取並組合 URL
                relative_url = link_tag.get('href')
                if relative_url and isinstance(relative_url, str):
                    url = urljoin(GOOGLE_NEWS_URL, relative_url)
            
            if url and title != "N/A":
                articles.append({"title": title, "url": url})

        return articles

    except requests.RequestException as e:
        print(f"搜尋 Google 新聞 '{query}' 時發生錯誤: {e}")
        return []

def scrape_news_data():
    """從 Google 新聞爬取經濟、外交和輿情相關新聞"""
    print("正在從 Google News 爬取新聞資料...")

    news_keywords = {
        "economic": ["台灣 中國 經濟制裁", "台灣 出口禁令", "ECFA"],
        "diplomatic": ["台灣 外交聲明", "美國 台灣關係法", "中國 軍事威脅 譴責"],
        "public_opinion": ["台灣民意調查 統一", "台灣 國防信心", "台灣社會輿論 兩岸"]
    }

    all_news = {}
    all_sources = {}

    for category, keywords in news_keywords.items():
        query = " OR ".join(keywords)
        articles = _search_google_news(query)
        
        all_news[category] = [article["title"] for article in articles if article.get("title") != "N/A"]
        all_sources[category] = [article["url"] for article in articles if article.get("title") != "N/A"]

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

if __name__ == '__main__':
    news_data = scrape_news_data()
    print("\n--- 爬取的新聞資料 ---")
    print(f"經濟新聞: {news_data['economic_news']}")
    print(f"外交新聞: {news_data['diplomatic_news']}")
    print(f"輿情新聞: {news_data['public_opinion_news']}")
    print(f"資料來源: {news_data['sources']}")
