import random
from typing import Dict, Any

def calculate_indicators(military_data: Dict[str, Any], news_data: Dict[str, Any], 
                        gold_data: Dict[str, Any], food_data: Dict[str, Any]) -> Dict[str, float]:
    """
    根據各種資料來源計算威脅指標
    """
    
    # 軍事威脅指標 (0-100)
    military_score = 0.0
    if military_data:
        # 基於擾台次數計算
        total_incursions = military_data.get('total_incursions_last_week', 0)
        latest_aircrafts = military_data.get('latest_aircrafts', 0)
        latest_ships = military_data.get('latest_ships', 0)
        
        # 計算軍事威脅分數
        military_score = min(100, (total_incursions * 2) + (latest_aircrafts * 3) + (latest_ships * 5))
    
    # 經濟威脅指標 (0-100)
    economic_score = 0.0
    if gold_data and food_data:
        # 基於價格變動計算經濟不穩定性
        gold_change = gold_data.get('daily_change_percent', 0)
        food_change = food_data.get('daily_change_percent', 0)
        
        # 價格波動越大，經濟威脅越高
        economic_score = min(100, abs(gold_change) * 10 + abs(food_change) * 15)
    
    # 新聞輿情指標 (0-100)
    news_score = 0.0
    if news_data:
        total_articles = news_data.get('total_articles', 0)
        # 基於新聞數量和類型計算輿情分數
        news_score = min(100, total_articles * 5)
    
    return {
        'military': round(military_score, 2),
        'economic': round(economic_score, 2),
        'news': round(news_score, 2)
    }

def calculate_threat_probability(indicators: Dict[str, float]) -> float:
    """
    根據各項指標計算總體威脅等級
    """
    military_weight = 0.4
    economic_weight = 0.3
    news_weight = 0.3
    
    weighted_score = (
        indicators.get('military', 0) * military_weight +
        indicators.get('economic', 0) * economic_weight +
        indicators.get('news', 0) * news_weight
    )
    
    return round(min(100, weighted_score), 2)

# 向後兼容的舊函數名稱
def calculate_military_threat_indicator(military_data: Dict[str, Any]) -> float:
    """向後兼容函數"""
    indicators = calculate_indicators(military_data, {}, {}, {})
    return indicators.get('military', 0)

def calculate_economic_threat_indicator(news_data: Dict[str, Any], 
                                      gold_data: Dict[str, Any], 
                                      food_data: Dict[str, Any]) -> float:
    """向後兼容函數"""
    indicators = calculate_indicators({}, news_data, gold_data, food_data)
    return indicators.get('economic', 0)
