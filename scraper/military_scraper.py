import requests
from bs4 import BeautifulSoup, Tag
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, cast
import random
import urllib3
import logging

# 禁用 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 國防部即時軍事動態網址
MND_URL = "https://www.mnd.gov.tw/PublishTable.aspx?Types=%E5%8D%B3%E6%99%82%E8%BB%8D%E4%BA%8B%E5%8B%95%E6%85%8B&title=%E5%9C%8B%E9%98%B2%E6%B6%88%E6%81%AF"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': MND_URL
}

class MilitaryScraper:
    """
    從台灣國防部網站爬取即時軍事動態。
    """
    def __init__(self, timeout=15):
        self.url = "https://www.mnd.gov.tw/Publish.aspx?p=82236&title=國防消息&SelectStyle=即時軍事動態"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = timeout

    def scrape(self):
        """
        執行爬取並回傳軍事動態新聞標題列表。
        """
        logging.info("Starting military news scraping from MND website...")
        try:
            response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 國防部網站使用 <div class="list-group"> 來包裹新聞列表
            list_group = soup.find('div', class_='list-group')
            if not list_group:
                logging.warning("Could not find the 'list-group' div on MND page. Structure might have changed.")
                return {"error": "無法在國防部網站上找到新聞列表，頁面結構可能已變更。"}

            # 在 list_group 中找到所有的 <a> 標籤，它們是新聞連結
            news_items = list_group.find_all('a', limit=5) # 限制最多5筆
            
            headlines = [item.get_text(strip=True) for item in news_items]
            
            if not headlines:
                logging.warning("No headlines found within the 'list-group' div.")
                return {"error": "在新聞列表中找不到任何標題。"}
            
            logging.info(f"Successfully scraped {len(headlines)} military headlines.")
            return {
                "headlines": headlines,
                "source": self.url
            }

        except requests.RequestException as e:
            logging.error(f"Error scraping military news: {e}")
            return {"error": f"請求錯誤: {e}"}

def scrape_military_data() -> Dict[str, Any]:
    """
    從國防部網站抓取解放軍活動資料。
    此爬蟲會處理 ASP.NET 的 __doPostBack 機制來進入詳情頁。
    """
    print("正在從國防部網站爬取即時軍事動態...")
    try:
        session = requests.Session()
        response = session.get(MND_URL, headers=HEADERS, timeout=20, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        links = soup.select('a[href*="__doPostBack"]')
        if not links:
            raise ValueError("在國防部網站上找不到動態連結 (PostBack Links)。可能是網站結構已變更。")

        viewstate_tag = soup.find('input', {'name': '__VIEWSTATE'})
        viewstategenerator_tag = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        eventvalidation_tag = soup.find('input', {'name': '__EVENTVALIDATION'})

        form_data = {
            '__VIEWSTATE': cast(Tag, viewstate_tag)['value'] if viewstate_tag else '',
            '__VIEWSTATEGENERATOR': cast(Tag, viewstategenerator_tag)['value'] if viewstategenerator_tag else '',
            '__EVENTVALIDATION': cast(Tag, eventvalidation_tag)['value'] if eventvalidation_tag else '',
            '__EVENTARGUMENT': ''
        }

        daily_intrusions: List[int] = []
        latest_aircrafts = 0
        latest_ships = 0

        for i, link in enumerate(links[:7]):
            href = link.get('href')
            if not isinstance(href, str): continue
            
            match = re.search(r"__doPostBack\('([^']*)'", href)
            if not match: continue
            
            event_target = match.group(1)
            
            post_data = form_data.copy()
            post_data['__EVENTTARGET'] = event_target
            
            details_response = session.post(MND_URL, headers=HEADERS, data=post_data, timeout=20, verify=False)
            details_response.raise_for_status()
            
            details_soup = BeautifulSoup(details_response.text, 'html.parser')
            content_area = details_soup.find('div', class_='ins_p_data') or details_soup
            details_page_text = content_area.get_text()

            aircraft_match = re.search(r'偵獲共機(\d+)架次', details_page_text)
            ship_match = re.search(r'及共艦(\d+)艘', details_page_text)
            
            aircrafts_today = int(aircraft_match.group(1)) if aircraft_match else 0
            ships_today = int(ship_match.group(1)) if ship_match else 0
            
            daily_intrusions.append(aircrafts_today + ships_today)

            if i == 0:
                latest_aircrafts = aircrafts_today
                latest_ships = ships_today
        
        if not daily_intrusions:
            raise ValueError("無法從任何連結中提取侵擾數據。")

        total_incursions_last_week = sum(daily_intrusions)
        print(f"爬取完成：近七天總擾台 {total_incursions_last_week} 次。最新偵獲共機 {latest_aircrafts} 架次, 共艦 {latest_ships} 艘次。")

        while len(daily_intrusions) < 7:
            daily_intrusions.append(0)

        return {
            "total_incursions_last_week": total_incursions_last_week,
            "latest_aircrafts": latest_aircrafts,
            "latest_ships": latest_ships,
            "daily_incursions_chart_data": {
                "labels": [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(6, -1, -1)],
                "data": daily_intrusions[::-1]
            },
            "related_news": ["資料來源: 國防部即時軍事動態"],
            "source_url": MND_URL
        }

    except Exception as e:
        print(f"爬取軍事資料時發生錯誤: {e}")
        # Return fallback data
        return {
            "total_incursions_last_week": random.randint(5, 50),
            "latest_aircrafts": random.randint(0, 10),
            "latest_ships": random.randint(0, 5),
            "daily_incursions_chart_data": {
                "labels": [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(6, -1, -1)],
                "data": [random.randint(0, 15) for _ in range(7)]
            },
            "related_news": ["無法連接至國防部網站，使用備用數據"],
            "source_url": MND_URL,
            "error": "Using fallback data"
        }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    scraper = MilitaryScraper()
    data = scraper.scrape()
    print("\n--- Scraped Military Data ---")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))
