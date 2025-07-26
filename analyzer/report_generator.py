import os
import openai
import logging
from typing import Dict, Any
from datetime import datetime

def generate_ai_report(military_data: Dict[str, Any], 
                      news_data: Dict[str, Any],
                      gold_data: Dict[str, Any], 
                      food_data: Dict[str, Any],
                      military_indicator: float,
                      economic_indicator: float,
                      overall_threat_level: float) -> str:
    """
    使用 OpenAI API 生成威脅分析報告
    """
    
    # 設定 OpenAI API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.warning("OPENAI_API_KEY 未設定，使用預設報告")
        return generate_fallback_report(overall_threat_level, military_indicator, economic_indicator)
    
    try:
        # 設定 OpenAI 客戶端
        client = openai.OpenAI(api_key=api_key)
        
        # 準備分析資料摘要
        data_summary = prepare_data_summary(military_data, news_data, gold_data, food_data)
        
        # 建構提示詞
        prompt = f"""
作為一位專業的地緣政治分析師，請根據以下資料生成一份關於台海情勢的威脅評估報告：

數據摘要：
{data_summary}

威脅指標：
- 軍事威脅指標：{military_indicator:.1f}/100
- 經濟威脅指標：{economic_indicator:.1f}/100
- 總體威脅等級：{overall_threat_level:.1f}/100

請生成一份專業的分析報告，包含：
1. 情勢概述
2. 各項威脅分析
3. 風險評估
4. 建議與結論

報告應該客觀、專業，避免過度煽動性言論。長度約 300-500 字。
"""

        # 呼叫 OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位專業的地緣政治分析師，擅長台海情勢分析。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        report = response.choices[0].message.content.strip()
        logging.info("成功生成 AI 威脅分析報告")
        return report
        
    except Exception as e:
        logging.error(f"AI 報告生成失敗: {e}")
        return generate_fallback_report(overall_threat_level, military_indicator, economic_indicator)

def prepare_data_summary(military_data: Dict[str, Any], 
                        news_data: Dict[str, Any],
                        gold_data: Dict[str, Any], 
                        food_data: Dict[str, Any]) -> str:
    """
    準備資料摘要供 AI 分析
    """
    summary_parts = []
    
    # 軍事資料摘要
    if military_data:
        total_incursions = military_data.get('total_incursions_last_week', 0)
        latest_aircrafts = military_data.get('latest_aircrafts', 0)
        latest_ships = military_data.get('latest_ships', 0)
        summary_parts.append(
            f"軍事動態：過去一週共偵獲擾台活動 {total_incursions} 次，"
            f"最新一日偵獲共機 {latest_aircrafts} 架次、共艦 {latest_ships} 艘次。"
        )
    
    # 經濟資料摘要
    if gold_data:
        gold_price = gold_data.get('current_price', 'N/A')
        gold_change = gold_data.get('daily_change_percent', 0)
        summary_parts.append(
            f"黃金價格：目前 ${gold_price}/盎司，日變動 {gold_change:+.2f}%。"
        )
    
    if food_data:
        food_price = food_data.get('wheat_price', 'N/A')
        food_change = food_data.get('daily_change_percent', 0)
        summary_parts.append(
            f"糧食價格：小麥期貨 ${food_price}/蒲式耳，日變動 {food_change:+.2f}%。"
        )
    
    # 新聞資料摘要
    if news_data:
        total_articles = news_data.get('total_articles', 0)
        summary_parts.append(f"新聞動態：共收集到 {total_articles} 則相關新聞。")
    
    return " ".join(summary_parts)

def generate_fallback_report(overall_threat_level: float, 
                            military_indicator: float, 
                            economic_indicator: float) -> str:
    """
    生成備用報告（當 OpenAI API 不可用時）
    """
    current_date = datetime.now().strftime("%Y年%m月%d日")
    
    # 根據威脅等級決定基調
    if overall_threat_level >= 70:
        threat_level_desc = "高度"
        situation_desc = "情勢較為緊張"
    elif overall_threat_level >= 40:
        threat_level_desc = "中等"
        situation_desc = "情勢保持關注"
    else:
        threat_level_desc = "相對較低"
        situation_desc = "情勢相對穩定"
    
    report = f"""
台海威脅情勢分析報告 ({current_date})

【情勢概述】
根據最新收集的多維度資料分析，當前台海地區威脅等級為 {overall_threat_level:.1f}/100，屬於{threat_level_desc}風險水平。整體而言，{situation_desc}。

【威脅分析】
軍事層面：威脅指標為 {military_indicator:.1f}/100。從最新軍事動態來看，解放軍活動頻率處於監控範圍內，相關單位持續密切觀察中。

經濟層面：威脅指標為 {economic_indicator:.1f}/100。國際經濟環境變化對區域穩定性的影響值得關注，特別是大宗商品價格波動可能反映市場對地緣政治風險的敏感度。

【風險評估】
綜合各項指標，當前風險主要來自於軍事活動的不確定性以及經濟環境的波動。建議相關單位持續監控各項指標變化，並保持適當的警戒水平。

【建議與結論】
1. 持續強化情資收集與分析能力
2. 密切關注國際經濟動向對區域穩定的影響
3. 加強與友邦的溝通協調機制
4. 提升民眾對當前情勢的正確認知

本報告基於公開資料分析生成，僅供參考。實際情勢發展請以官方權威發佈為準。
"""
    
    return report.strip()

if __name__ == '__main__':
    # 測試用的模擬資料
    test_military_data = {"total_incursions_last_week": 20, "latest_aircrafts": 5, "latest_ships": 2}
    test_news_data = {"total_articles": 8}
    test_gold_data = {"current_price": 2000, "daily_change_percent": 1.2}
    test_food_data = {"wheat_price": 600, "daily_change_percent": -0.5}
    
    report = generate_ai_report(
        test_military_data, test_news_data, test_gold_data, test_food_data,
        45.0, 25.0, 35.0
    )
    
    print("=== 測試報告 ===")
    print(report)
