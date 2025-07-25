import random
from datetime import datetime, timedelta
<<<<<<< HEAD
=======
import logging
import statistics
>>>>>>> 582f439752d7dd09671e0ddbe1ded2923f47c81d

def _normalize(value, max_value, high_is_bad=True):
    """將數值正規化到 0-100 的區間。"""
    if max_value == 0:
        return 0
<<<<<<< HEAD
    # 將值限制在 0 和 max_value 之間，避免超過 100%
    normalized_value = max(0, min(value / max_value, 1.0)) * 100
=======
    # 將值限制在 0 和 1 之間
    clipped_value = max(0, min(value / max_value, 1.0))
    normalized_value = clipped_value * 100
>>>>>>> 582f439752d7dd09671e0ddbe1ded2923f47c81d
    return normalized_value if high_is_bad else 100 - normalized_value

def calculate_indicators(raw_data):
    """
    從原始數據計算各項指標分數 (0-100)，並整理資料來源。
    分數越高代表威脅程度越高。
    """
<<<<<<< HEAD
    indicators = {}
    sources = {}

    def merge_sources(new_sources):
        """輔助函式，用於合併來源字典，並將相同分類的 URL 合併到一個列表中。"""
        for category, url_list in new_sources.items():
            if category not in sources:
                sources[category] = []
            # 避免重複加入
            for url in url_list:
                if url not in sources[category]:
                    sources[category].append(url)

    # --- 1. 軍事指標 ---
    military_data = raw_data.get('military', {})
    latest_intrusions = military_data.get('latest_aircrafts', 0) + military_data.get('latest_ships', 0)
    indicators['military_score'] = _normalize(latest_intrusions, 50)
    indicators['military_latest_intrusions'] = latest_intrusions
    indicators['military_total_incursions_last_week'] = military_data.get('total_incursions_last_week', 0)
    indicators['military_daily_chart_data'] = military_data.get('daily_incursions_chart_data', {})
    merge_sources(military_data.get('sources', {}))

    # --- 2. 經濟指標 ---
    gold_data = raw_data.get('gold', {})
    food_data = raw_data.get('food', {})
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
        
    gold_score = _normalize(abs(gold_change_percent), 5, high_is_bad=True)
    food_score = _normalize(abs(food_change_percent), 5, high_is_bad=True)
    indicators['economic_score'] = (gold_score + food_score) / 2
    indicators['gold_price'] = gold_data.get('price', 'N/A')
    indicators['gold_price_change'] = gold_data.get('price_change', 'N/A')
    indicators['food_price'] = food_data.get('price', 'N/A')
    indicators['food_price_change'] = food_data.get('price_change', 'N/A')
    merge_sources(gold_data.get('sources', {}))
    merge_sources(food_data.get('sources', {}))

    # --- 3. 社會輿情指標 ---
    news_data = raw_data.get('news', {})
    economic_news_count = len(news_data.get('economic_news', []))
    diplomatic_news_count = len(news_data.get('diplomatic_news', []))
    public_opinion_news_count = len(news_data.get('public_opinion_news', []))
    total_news_count = economic_news_count + diplomatic_news_count + public_opinion_news_count
    
    indicators['social_sentiment_score'] = _normalize(total_news_count, 15)
    indicators['total_news_count'] = total_news_count
    indicators['economic_news_titles'] = news_data.get('economic_news', [])
    indicators['diplomatic_news_titles'] = news_data.get('diplomatic_news', [])
    indicators['public_opinion_news_titles'] = news_data.get('public_opinion_news', [])
    merge_sources(news_data.get('sources', {}))

    print("指標計算完成。")
    return indicators, sources
=======
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
>>>>>>> 582f439752d7dd09671e0ddbe1ded2923f47c81d

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
<<<<<<< HEAD
    return round(max(0, min(threat_probability, 100)), 2)
=======
    clipped_prob = max(0, min(threat_probability, 100))
    return round(clipped_prob, 2)

# 供其他模組或舊程式碼直接呼叫
def calculate_indicators(raw_data):
    return IndicatorCalculator().calculate(raw_data)
>>>>>>> 582f439752d7dd09671e0ddbe1ded2923f47c81d

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
            "sources": {"military": ["https://www.mnd.gov.tw/"]}
        },
        "gold": {
            "price": "$2350.50",
            "price_change": "+1.5%",
            "sources": {"economic": ["https://commoditypriceapi.com/"]}
        },
        "food": {
            "price": "$17.80",
            "price_change": "-0.5%",
            "sources": {"economic": ["https://commoditypriceapi.com/"]}
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
