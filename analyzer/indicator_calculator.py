import random
from datetime import datetime, timedelta
import numpy as np
import logging
import statistics

def _normalize(value, max_value, high_is_bad=True):
    """將數值正規化到 0-100 的區間。"""
    if max_value == 0:
        return 0
    # 將值限制在 0 和 max_value 之間，避免超過 100%
    normalized_value = np.clip(value / max_value, 0, 1.0) * 100
    return normalized_value if high_is_bad else 100 - normalized_value

class IndicatorCalculator:
    """
    根據原始爬取資料計算各項指標分數。
    """
    def _calculate_military_score(self, military_data):
        """計算軍事威脅分數"""
        headlines = military_data.get("headlines", [])
        if not headlines or "error" in military_data:
            return 0
        
        score = len(headlines) * 15  # 每則動態計15分
        # 可以根據關鍵字進一步加權，例如 "共機", "繞台"
        for headline in headlines:
            if "共機" in headline or "共艦" in headline:
                score += 5
            if "飛越" in headline or "中線" in headline:
                score += 10
        return min(score, 100)

    def _calculate_economic_score(self, news_data, gold_data, food_data):
        """計算經濟穩定分數"""
        score = 100
        # 新聞影響
        economic_news = news_data.get("economic_news", [])
        score -= len(economic_news) * 5 # 每則負面經濟新聞扣5分

        # 黃金價格影響 (假設價格為 TWD/gram)
        gold_price = gold_data.get("price_twd_per_gram", 0)
        if gold_price > 2500: # 假設超過2500台幣/克為高價
            score -= (gold_price - 2500) / 50 # 每高出50元扣1分
            
        # 糧食價格影響
        food_prices = food_data.get("prices", {})
        if not food_prices:
             score -= 10 # 如果無法獲取糧價，視為不穩定

        return max(score, 0)

    def _calculate_social_sentiment_score(self, news_data):
        """計算社會輿情分數"""
        score = 100
        # 外交新聞影響
        diplomatic_news = news_data.get("diplomatic_news", [])
        score -= len(diplomatic_news) * 4 # 每則負面外交新聞扣4分

        # 社會輿情新聞影響
        public_opinion_news = news_data.get("public_opinion_news", [])
        score -= len(public_opinion_news) * 6 # 每則負面輿情新聞扣6分

        return max(score, 0)

    def calculate(self, raw_data):
        """
        主計算函式，接收所有原始資料並回傳指標字典。
        """
        logging.info("Calculating indicators from raw data...")
        
        military_score = self._calculate_military_score(raw_data.get("military", {}))
        economic_score = self._calculate_economic_score(
            raw_data.get("news", {}),
            raw_data.get("gold", {}),
            raw_data.get("food", {})
        )
        social_sentiment_score = self._calculate_social_sentiment_score(raw_data.get("news", {}))

        # 計算總體威脅機率
        # 這是一個簡化的加權平均模型
        # 軍事權重最高(50%)，經濟(30%)，社會(20%)
        # 分數越低，威脅越高
        threat_prob = ( (100 - military_score) * 0.5 +
                        (100 - economic_score) * 0.3 +
                        (100 - social_sentiment_score) * 0.2 )
        
        indicators = {
            "military_score": round(military_score),
            "economic_score": round(economic_score),
            "social_sentiment_score": round(social_sentiment_score),
            "threat_probability": round(threat_prob)
        }
        
        logging.info(f"Indicator calculation complete: {indicators}")
        return indicators

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
