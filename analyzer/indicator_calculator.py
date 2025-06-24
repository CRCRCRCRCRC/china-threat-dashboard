import random
from datetime import datetime, timedelta
import numpy as np

def _normalize(value, max_value, high_is_bad=True):
    """將數值正規化到 0-100 的區間。"""
    if max_value == 0:
        return 0
    # 將值限制在 0 和 max_value 之間，避免超過 100%
    normalized_value = np.clip(value / max_value, 0, 1.0) * 100
    return normalized_value if high_is_bad else 100 - normalized_value

def calculate_indicators(raw_data):
    """
    從原始數據計算各項指標分數 (0-100)，並整理資料來源。
    分數越高代表威脅程度越高。
    """
    indicators = {}
    sources = {}

    # --- 1. 軍事指標 ---
    military_data = raw_data.get('military', {})
    # 使用 'latest_aircrafts' 和 'latest_ships' 計算當日總和
    latest_intrusions = military_data.get('latest_aircrafts', 0) + military_data.get('latest_ships', 0)
    # 假設單日擾台超過 50 架/艘次為極高威脅
    indicators['military_score'] = _normalize(latest_intrusions, 50)
    indicators['military_latest_intrusions'] = latest_intrusions
    indicators['military_total_incursions_last_week'] = military_data.get('total_incursions_last_week', 0)
    indicators['military_daily_chart_data'] = military_data.get('daily_incursions_chart_data', {})
    sources['military'] = military_data.get('source_url', 'N/A')

    # --- 2. 經濟指標 ---
    gold_data = raw_data.get('gold', {})
    food_data = raw_data.get('food', {})
    # 移除 '%' 和 '+' 符號，並轉換為浮點數
    try:
        gold_change_str = gold_data.get('price_change', '0').replace('%', '').replace('+', '')
        gold_change_percent = float(gold_change_str)
    except (ValueError, TypeError):
        gold_change_percent = 0
    
    try:
        food_change_str = food_data.get('price_change', '0').replace('%', '').replace('+', '')
        food_change_percent = float(food_change_str)
    except (ValueError, TypeError):
        food_change_percent = 0
        
    # 黃金和糧食價格上漲視為不穩定，分數增加。假設單日變動 5% 為極高風險。
    gold_score = _normalize(abs(gold_change_percent), 5, high_is_bad=True)
    food_score = _normalize(abs(food_change_percent), 5, high_is_bad=True)
    indicators['economic_score'] = (gold_score + food_score) / 2
    indicators['gold_price'] = gold_data.get('price', 'N/A')
    indicators['gold_price_change'] = gold_data.get('price_change', 'N/A')
    indicators['food_price'] = food_data.get('price', 'N/A')
    indicators['food_price_change'] = food_data.get('price_change', 'N/A')
    sources['gold'] = gold_data.get('source_url', 'N/A')
    sources['food'] = food_data.get('source_url', 'N/A')

    # --- 3. 社會輿情指標 ---
    news_data = raw_data.get('news', {})
    # 這裡我們基於新聞數量來做一個簡化版的指標
    # 假設單一類別超過 5 篇相關負面新聞就算高
    economic_news_count = len(news_data.get('economic_news', []))
    diplomatic_news_count = len(news_data.get('diplomatic_news', []))
    public_opinion_news_count = len(news_data.get('public_opinion_news', []))
    total_news_count = economic_news_count + diplomatic_news_count + public_opinion_news_count
    
    # 正規化，假設 15 篇以上總新聞量為高威脅
    indicators['social_sentiment_score'] = _normalize(total_news_count, 15)
    indicators['total_news_count'] = total_news_count
    indicators['economic_news_titles'] = news_data.get('economic_news', [])
    indicators['diplomatic_news_titles'] = news_data.get('diplomatic_news', [])
    indicators['public_opinion_news_titles'] = news_data.get('public_opinion_news', [])
    sources['news'] = news_data.get('sources', {}) # news_scraper 回傳的是包含分類的字典

    print("指標計算完成。")
    return indicators, sources

def calculate_threat_probability(indicators):
    """
    根據各項指標分數，使用加權平均計算最終的威脅機率。
    """
    weights = {
        'military': 0.5,      # 軍事權重最高
        'economic': 0.25,     # 經濟次之
        'social': 0.25        # 社會輿情
    }

    military_score = indicators.get('military_score', 0)
    economic_score = indicators.get('economic_score', 0)
    social_score = indicators.get('social_sentiment_score', 0)

    # 加權計算總機率
    threat_probability = (
        military_score * weights['military'] +
        economic_score * weights['economic'] +
        social_score * weights['social']
    )
    
    # 確保機率在 0-100 之間
    return round(np.clip(threat_probability, 0, 100), 2)

if __name__ == '__main__':
    # 用於直接測試的模擬數據
    mock_raw_data = {
        "military": {
            "latest_aircrafts": 25,
            "latest_ships": 10,
            "daily_incursions_chart_data": {
                "labels": ["07-01", "07-02", "07-03"],
                "data": [10, 20, 35]
            },
            "source_url": "https://www.mnd.gov.tw/"
        },
        "gold": {
            "price": "$2350.50",
            "price_change": "+1.5%",
            "source_url": "https://metalpriceapi.com/"
        },
        "food": {
            "price": "$17.80",
            "price_change": "-0.5%",
            "source_url": "https://api-ninjas.com/api/commodityprice"
        },
        "news": {
            "economic_news": ["北京宣布對台部分產品啟動貿易壁壘調查"],
            "diplomatic_news": ["美國重申對台承諾", "某國關閉駐台辦事處"],
            "public_opinion_news": ["最新民調顯示兩岸關係態度分歧"],
            "sources": {
                "economic": ["http://news.google.com/1"],
                "diplomatic": ["http://news.google.com/2", "http://news.google.com/3"],
                "public_opinion": ["http://news.google.com/4"],
            }
        }
    }
    
    calculated_indicators, calculated_sources = calculate_indicators(mock_raw_data)
    threat_prob = calculate_threat_probability(calculated_indicators)
    
    import json
    print("--- Calculated Indicators ---")
    print(json.dumps(calculated_indicators, indent=2, ensure_ascii=False))
    print("\n--- Calculated Sources ---")
    print(json.dumps(calculated_sources, indent=2, ensure_ascii=False))
    print(f"\nCalculated Threat Probability: {threat_prob}%")
