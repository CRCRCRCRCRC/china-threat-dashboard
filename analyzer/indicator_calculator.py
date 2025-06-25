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
        if "error" in military_data or not military_data:
            logging.warning("Military data contains error or is empty, returning low threat score.")
            return 10 # 如果資料有誤，給一個較低的固定分數

        # 分數基於多個因素，總分100
        # 1. 最近一周總侵擾次數 (權重最高)
        #    假設一周超過 100 架次/艘次為極高風險
        total_incursions = military_data.get("total_incursions_last_week", 0)
        incursion_score = _normalize(total_incursions, 100) # 100次為滿分100

        # 2. 最新單日侵擾強度
        #    假設單日超過 30 架次/艘次為極高風險
        latest_aircrafts = military_data.get("latest_aircrafts", 0)
        latest_ships = military_data.get("latest_ships", 0)
        latest_total = latest_aircrafts + latest_ships
        latest_incursion_score = _normalize(latest_total, 30) # 30次為滿分100

        # 組合分數 (範例：70% 總數, 30% 最新強度)
        final_score = (incursion_score * 0.7) + (latest_incursion_score * 0.3)
        
        logging.info(f"Calculated military score: {final_score:.2f} (from total incursions: {total_incursions}, latest: {latest_total})")
        return min(final_score, 100)

    def _calculate_economic_score(self, news_data, gold_data, food_data):
        """計算經濟穩定分數"""
        score = 100
        # 新聞影響
        economic_news = news_data.get("news_by_category", {}).get("economic", [])
        score -= len(economic_news) * 5 # 每則負面經濟新聞扣5分

        # 黃金價格影響
        # 假設價格變動超過 +/- 5% 就開始影響分數
        gold_price_change_str = gold_data.get("price_change", "0%")
        try:
            gold_change = float(gold_price_change_str.strip('%'))
            if abs(gold_change) > 5:
                score -= (abs(gold_change) - 5) * 2 # 波動每多1%扣2分
        except (ValueError, TypeError):
            logging.warning(f"Could not parse gold price change: {gold_price_change_str}")

        # 糧食價格影響
        # 假設價格變動超過 +/- 10% 就開始影響分數
        food_price_change_str = food_data.get("price_change", "0%")
        try:
            food_change = float(food_price_change_str.strip('%'))
            if abs(food_change) > 10:
                score -= (abs(food_change) - 10) # 波動每多1%扣1分
        except (ValueError, TypeError):
            logging.warning(f"Could not parse food price change: {food_price_change_str}")
        
        return max(score, 0)

    def _calculate_social_sentiment_score(self, news_data):
        """計算社會輿情分數"""
        score = 100
        # 外交新聞影響
        diplomatic_news = news_data.get("news_by_category", {}).get("diplomatic", [])
        score -= len(diplomatic_news) * 4 # 每則負面外交新聞扣4分

        # 社會輿情新聞影響
        public_opinion_news = news_data.get("news_by_category", {}).get("public_opinion", [])
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
        
        # --- 前端額外需要的欄位（缺資料時給 None 由前端顯示 --） ---
        latest_aircrafts = raw_data.get("military", {}).get("latest_aircrafts")
        latest_ships = raw_data.get("military", {}).get("latest_ships")
        
        if latest_aircrafts is not None and latest_ships is not None:
            military_latest_intrusions = f"{latest_aircrafts} 架次 / {latest_ships} 艘次"
        else:
            military_latest_intrusions = None

        indicators = {
            "military_score": round(military_score),
            "economic_score": round(economic_score),
            "social_sentiment_score": round(social_sentiment_score),
            "threat_probability": round(threat_prob),

            # --- 前端額外需要的欄位 ---
            "military_latest_intrusions": military_latest_intrusions,
            "military_total_incursions_last_week": raw_data.get("military", {}).get("total_incursions_last_week"),
            "military_daily_chart_data": raw_data.get("military", {}).get("daily_incursions_chart_data"),

            "total_news_count": raw_data.get("news", {}).get("total_news_count", 0),

            "gold_price": raw_data.get("gold", {}).get("price"),
            "gold_price_change": raw_data.get("gold", {}).get("price_change"),

            "food_price": raw_data.get("food", {}).get("price"),
            "food_price_change": raw_data.get("food", {}).get("price_change")
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

# 供其他模組或舊程式碼直接呼叫
def calculate_indicators(raw_data):
    return IndicatorCalculator().calculate(raw_data)

if __name__ == '__main__':
    # 用於直接測試的模擬數據
    mock_raw_data = {
        "military": {
            "latest_aircrafts": 25,
            "latest_ships": 10,
            "total_incursions_last_week": 85,
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
            "total_news_count": 4,
            "news_by_category": {
                "economic": [{'title': '北京宣布對台部分產品啟動貿易壁壘調查', 'url': '#'}],
                "diplomatic": [{'title': '美國重申對台承諾', 'url': '#'}, {'title': '某國關閉駐台辦事處', 'url': '#'}],
                "public_opinion": [{'title': '最新民調顯示兩岸關係態度分歧', 'url': '#'}]
            },
            "sources": {
                "中央社": "https://www.cna.com.tw",
                "聯合新聞網": "https://udn.com"
            }
        }
    }
    
    calculated_indicators = calculate_indicators(mock_raw_data)
    threat_prob = calculate_threat_probability(calculated_indicators)
    
    import json
    print("--- Calculated Indicators ---")
    print(json.dumps(calculated_indicators, indent=2, ensure_ascii=False))
    print(f"\nCalculated Threat Probability: {threat_prob}%")
