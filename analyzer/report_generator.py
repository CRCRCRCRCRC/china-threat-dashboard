import os
import openai
import json
from dotenv import load_dotenv
from openai import OpenAI

# 載入 .env 檔案中的環境變數
load_dotenv()

# 設定 OpenAI API 金鑰
# 建議從環境變數讀取，而不是寫死在程式碼中
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("錯誤：未設定 OPENAI_API_KEY 環境變數。")
    # 在實際應用中可能需要引發異常或退出
    client = None
else:
    client = openai.OpenAI(api_key=api_key)

def _format_sources(sources):
    """將來源字典格式化為易於閱讀的字串。"""
    lines = []
    # 使用一個更有意義的分類名稱對應
    category_map = {
        'military': '軍事動態',
        'economic': '經濟數據',
        'diplomatic': '外交情資',
        'public_opinion': '社會輿情'
    }
    for category, url_list in sorted(sources.items()):
        if url_list:
            display_name = category_map.get(category, category.capitalize())
            # 使用 set 去除重複的 URL，然後排序以保持一致性
            unique_urls = sorted(list(set(url_list)))
            lines.append(f"- {display_name}來源: {', '.join(unique_urls)}")
    return "\n".join(lines) if lines else "無可用數據來源。"

def _create_prompt(indicators, threat_probability, sources):
    """根據輸入數據、威脅機率和來源，創建一個詳細的提示給 OpenAI API。"""
    
    sources_text = _format_sources(sources)

    prompt = f"""
請扮演一位頂尖、謹慎且客觀的台灣海峽軍事情報分析師。你的任務是根據以下提供的即時數據，生成一份專業、深入、數據驅動的情報分析報告。請避免使用聳動或猜測性的語言，你的所有判斷都必須根植於提供的數據。

報告必須嚴格遵循以下 JSON 格式，不得有任何偏離。所有文字需使用繁體中文。

**JSON 輸出格式:**
{{
  "report_summary_zh": {{
    "title": "臺海局勢綜合情報分析",
    "sections": [
      {{
        "heading": "軍事動態分析",
        "content": "（根據「軍事數據」，分析解放軍最近活動的規模、頻率與模式。評估這是否為常態性壓力測試、演習的一部分，或具有更不尋常的意圖。思考此活動對台灣防禦能力的潛在消耗。）」
      }},
      {{
        "heading": "經濟指標分析",
        "content": "（根據「經濟指標」，分析黃金和糧食等避險資產的價格變動，這反映了市場對區域穩定性的信心。思考這些價格波動與軍事活動是否存在潛在關聯，例如資本避險或供應鏈憂慮。）」
      }},
      {{
        "heading": "社會輿情觀察",
        "content": "（根據「社會輿情新聞」，分析台灣內部對經濟、外交、國防等議題的討論風向。評估公眾情緒是保持穩定，還是受到特定事件或資訊戰的影響而出現波動。）」
      }}
    ]
  }},
  "report_summary_en": {{
    "title": "Comprehensive Intelligence Analysis of the Taiwan Strait Situation",
    "sections": [
      {{
        "heading": "Military Dynamics Analysis",
        "content": "(Based on 'Military Data', analyze the scale, frequency, and patterns of recent PLA activities. Assess whether this constitutes routine pressure testing, part of an exercise, or has more unusual intent. Consider the potential attrition effect on Taiwan's defense capabilities.)"
      }},
      {{
        "heading": "Economic Indicators Analysis",
        "content": "(Based on 'Economic Indicators,' analyze price changes in safe-haven assets like gold and food, which reflect market confidence in regional stability. Consider potential correlations between these price fluctuations and military activities, such as capital flight or supply chain concerns.)"
      }},
      {{
        "heading": "Public Opinion Observation",
        "content": "(Based on 'Public Opinion News,' analyze the direction of internal discussions in Taiwan on issues like the economy, diplomacy, and defense. Assess whether public sentiment remains stable or shows volatility influenced by specific events or information warfare.)"
      }}
    ]
  }},
  "three_month_probability": {{
    "percentage": "<0-100 的整數>",
    "justification": "（提供一個詳細、分點的專業理由，解釋你給出的「三個月內」攻台機率。你的判斷必須綜合所有數據，並明確列出你觀察到的【支持攻擊的因素】和【反對攻擊的嚇阻因素】。最後，對如果當前指標持續或升級數週，局勢可能的演變進行簡要推論。）"
  }},
  "data_sources_list": {json.dumps(sources, ensure_ascii=False)}
}}

---
**輸入數據與解讀指引:**

1.  **當前綜合威脅指數 (Current Overall Threat Index):** {threat_probability:.2f}%
    *   **解讀**: 這是一個量化的短期威脅分數，綜合了軍事、經濟與社會的異常活動。它代表了「當下」的緊張程度，是你判斷的核心基準。

2.  **軍事數據 (Military Data):**
    - 最新偵獲共機/共艦擾台總數: {indicators.get('military_latest_intrusions', 'N/A')} 架次/艘次
    *   **解讀**: 數字本身很重要，但更要思考其「趨勢」和「構成」。是戰鬥機、轟炸機還是無人機？這反映了不同的戰術意圖。高強度活動可能意在消耗台灣的應對能力（灰色地帶戰術）。

3.  **經濟指標 (Economic Indicators):**
    - 黃金價格: {indicators.get('gold_price', 'N/A')}
    - 黃金價格24小時變動: {indicators.get('gold_price_change', 'N/A')}
    - 糧食價格: {indicators.get('food_price', 'N/A')}
    - 糧食價格24小時變動: {indicators.get('food_price_change', 'N/A')}
    *   **解讀**: 黃金是全球性的避險資產，其價格上漲通常反映市場對地緣政治風險的憂慮。糧食價格則關乎民生穩定與全球供應鏈。劇烈變動可能暗示有大型實體正在為衝突做準備或市場已預期衝突風險升高。

4.  **社會輿情新聞 (Public Opinion News):**
    - 經濟相關新聞標題: {json.dumps(indicators.get('economic_news_titles', []), ensure_ascii=False)}
    - 外交相關新聞標題: {json.dumps(indicators.get('diplomatic_news_titles', []), ensure_ascii=False)}
    - 輿情相關新聞標題: {json.dumps(indicators.get('public_opinion_news_titles', []), ensure_ascii=False)}
    *   **解讀**: 這些新聞標題反映了台灣社會當前的關注焦點。注意是否有大量關於「民生困難」、「軍事無用論」或「對外關係孤立」的討論，這可能是認知作戰的一部分，旨在削弱內部抵抗意志。

5.  **數據來源 (Data Sources):**
{sources_text}
---

請嚴格按照上述指示與 JSON 格式進行分析，展現你的專業洞察力。
"""
    return prompt.strip()

def generate_ai_report(indicators, threat_probability, sources, api_key):
    """
    使用 OpenAI API 生成綜合分析報告。
    """
    if not api_key:
        return _get_fallback_report("OpenAI API 金鑰未提供。")

    try:
        client = OpenAI(api_key=api_key)
        print("正在呼叫 OpenAI API (gpt-4o) 進行深度分析...")
        prompt = _create_prompt(indicators, threat_probability, sources)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional intelligence analyst. Respond strictly in the requested JSON format using Traditional Chinese."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        
        content = response.choices[0].message.content
        if content:
            print("API 回應成功。")
            report_json = json.loads(content)
            return report_json
        else:
            print("API 回應內容為空。")
            return _get_fallback_report("API 回應內容為空。")

    except openai.APIError as e:
        print(f"OpenAI API 返回錯誤: {e}")
        return _get_fallback_report(f"OpenAI API 錯誤: {e}")
    except json.JSONDecodeError as e:
        print(f"解析 API 回應時發生 JSON 錯誤: {e}")
        return _get_fallback_report(f"JSON 解析錯誤: {e}")
    except Exception as e:
        print(f"生成 AI 報告時發生未知錯誤: {e}")
        import traceback
        traceback.print_exc()
        return _get_fallback_report(f"未知錯誤: {e}")

def _get_fallback_report(error_message=""):
    """返回一個包含錯誤訊息的備用報告結構。"""
    return {
        "report_summary_zh": {"title": "報告生成失敗", "sections": [{"heading": "錯誤", "content": f"無法從 OpenAI API 獲取分析報告。{error_message}"}]},
        "report_summary_en": {"title": "Report Generation Failed", "sections": [{"heading": "Error", "content": f"Failed to retrieve analysis from OpenAI API. {error_message}"}]},
        "three_month_probability": {"percentage": -1, "justification": f"因報告生成失敗，無法提供機率評估。錯誤：{error_message}"},
        "data_sources_list": {}
    }

if __name__ == '__main__':
    load_dotenv()
    test_api_key = os.getenv("OPENAI_API_KEY")

    if not test_api_key:
        print("請在 .env 檔案中設定 OPENAI_API_KEY 以進行測試。")
    else:
        # 建立模擬的 indicators 和 sources 字典
        mock_indicators = {
            'military_score': 70.0,
            'military_latest_intrusions': 35,
            'economic_score': 30.0,
            'gold_price': '$2350.50',
            'gold_price_change': '+1.5%',
            'food_price': '$17.80',
            'food_price_change': '-0.5%',
            'social_sentiment_score': 46.67,
            'economic_news_titles': ["北京宣布對台部分產品啟動貿易壁壘調查"],
            'diplomatic_news_titles': ["美國重申對台承諾", "某國關閉駐台辦事處"],
            'public_opinion_news_titles': ["最新民調顯示兩岸關係態度分歧"]
        }
        mock_sources = {
            "military": ["https://www.mnd.gov.tw/"],
            "economic": [
                "https://commoditypriceapi.com/",
                "http://news.google.com/1"
            ],
            "diplomatic": [
                "http://news.google.com/2",
                "http://news.google.com/3"
            ],
            "public_opinion": ["http://news.google.com/4"]
        }
        mock_threat_prob = 56.67

        print("\n--- 執行報告生成器測試 ---")
        ai_report = generate_ai_report(mock_indicators, mock_threat_prob, mock_sources, test_api_key)
        
        print("\n--- AI 回應 ---")
        print(json.dumps(ai_report, indent=2, ensure_ascii=False))
        print("--- 測試結束 ---")
