import os
import openai
import json
from dotenv import load_dotenv
from openai import OpenAI
import logging
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from io import BytesIO
import base64

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

class ReportGenerator:
    """
    使用 OpenAI GPT-4o 生成分析報告，並附帶一個雷達圖。
    """
    def __init__(self):
        # 檢查並設定 OpenAI API Key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        openai.api_key = self.api_key
        
        # 設定字體，以便 Matplotlib 可以顯示中文
        # 注意：在 Vercel 環境中，需要確保有中文字體可用。
        # 我們可以使用 'Noto Sans TC' 的思源黑體。
        try:
            # 在 Vercel 上，我們可能需要提供字體檔案。
            # 一個常見的做法是將 .ttf 檔案包含在專案中。
            # 為簡單起見，我們先嘗試系統字體。
            plt.rcParams['font.sans-serif'] = ['Noto Sans TC', 'Microsoft JhengHei'] 
            plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題
        except Exception as e:
            logging.warning(f"Could not set Chinese font for Matplotlib: {e}")

    def _create_radar_chart(self, indicators):
        """
        根據指標分數創建一個 Base64 編碼的雷達圖。
        """
        labels = ['軍事威脅', '經濟穩定', '社會輿情']
        # 分數越高越好，但軍事威脅是分數越低越好，所以要反轉
        stats = [
            100 - indicators.get('military_score', 50), # 威脅越高，在圖上越突出
            indicators.get('economic_score', 50),
            indicators.get('social_sentiment_score', 50)
        ]

        angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
        stats += stats[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.plot(angles, stats, color='red', linewidth=2)
        ax.fill(angles, stats, color='red', alpha=0.25)
        
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=14)

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0.1)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    def generate_report(self, indicators):
        """
        向 OpenAI API 發送請求，生成綜合分析報告。
        """
        logging.info("Generating AI analysis report...")
        
        threat_level = "低"
        prob = indicators.get('threat_probability', 0)
        if prob > 70:
            threat_level = "高"
        elif prob > 40:
            threat_level = "中"
            
        system_prompt = f"""
        你是一位頂尖的軍事安全與國情分析師，專精於分析台灣海峽的緊張局勢。你的任務是根據我提供的量化指標，生成一份專業、客觀、精煉的綜合分析報告。

        報告需包含以下部分：
        1.  **總體評估**：基於總體威脅機率，用一句話明確指出當前的綜合威脅等級（高、中、低）。
        2.  **指標分析**：
            *   **軍事動態**：根據軍事威脅分數，解讀當前解放軍活動的強度。分數越低代表軍事活動越少，局勢越穩定。
            *   **經濟穩定**：根據經濟穩定分數，評估台灣的經濟韌性。分數越高代表經濟越穩定。
            *   **社會輿情**：根據社會輿情分數，分析台灣內部的穩定性與民心士氣。分數越高代表社會越穩定。
        3.  **潛在風險與建議**：根據分數最低的維度，指出當前最主要的風險領域，並提供簡短的觀察或建議。
        4.  **格式要求**：請使用 Markdown 格式，重點部分使用粗體。用詞需專業、中立。
        """
        
        user_prompt = f"""
        請根據以下最新指標數據生成分析報告：
        - **軍事威脅分數**：{indicators.get('military_score', 'N/A')} / 100 (分數越低越安全)
        - **經濟穩定分數**：{indicators.get('economic_score', 'N/A')} / 100 (分數越高越穩定)
        - **社會輿情分數**：{indicators.get('social_sentiment_score', 'N/A')} / 100 (分數越高越穩定)
        - **綜合威脅機率**：{prob}% (機率越高，威脅越大)
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            report_content = response.choices[0].message.content

            # 同時生成圖表
            chart_url = self._create_radar_chart(indicators)
            
            logging.info("AI report and chart generated successfully.")
            return report_content, chart_url

        except Exception as e:
            logging.error(f"Error generating OpenAI report: {e}")
            return f"生成AI報告時發生錯誤: {e}", None

def _format_sources(sources):
    """將來源字典格式化為易於閱讀的字串。"""
    lines = []
    lines.append(f"- 軍事動態來源: {sources.get('military', 'N/A')}")
    lines.append(f"- 黃金價格來源: {sources.get('gold', 'N/A')}")
    lines.append(f"- 糧食價格來源: {sources.get('food', 'N/A')}")
    
    news_sources = sources.get('news', {})
    if news_sources:
        lines.append("- 新聞來源:")
        for category, urls in news_sources.items():
            if urls:
                url_list = ", ".join(urls)
                lines.append(f"  - {category.capitalize()}: {url_list}")
    return "\n".join(lines)

def _create_prompt(indicators, threat_probability, sources):
    """根據輸入數據、威脅機率和來源，創建一個詳細的提示給 OpenAI API。"""
    
    sources_text = _format_sources(sources)

    prompt = f"""
請扮演一位頂尖的台灣海峽軍事情報分析師。你的任務是根據以下提供的即時數據，生成一份專業、深入、數據驅動的情報分析報告。

報告必須嚴格遵循以下 JSON 格式，不得有任何偏離。所有文字需使用繁體中文。

**JSON 輸出格式:**
{{
  "report_summary_zh": {{
    "title": "臺海局勢綜合情報分析",
    "sections": [
      {{
        "heading": "軍事動態分析",
        "content": "（根據「軍事數據」分析解放軍最近的活動規模、頻率與模式，並評估其潛在意圖。）」
      }},
      {{
        "heading": "經濟指標分析",
        "content": "（根據「經濟指標」分析黃金與糧食價格變動所反映的市場避險情緒與全球供應鏈穩定性，評估其與區域緊張局勢的關聯。）」
      }},
      {{
        "heading": "社會輿情觀察",
        "content": "（根據「社會輿情新聞」，分析台灣內部對於經濟、外交、兩岸關係的討論熱點，評估民心士氣與外部資訊影響的可能性。）」
      }}
    ]
  }},
  "report_summary_en": {{
    "title": "Comprehensive Intelligence Analysis of the Taiwan Strait Situation",
    "sections": [
      {{
        "heading": "Military Dynamics Analysis",
        "content": "(Analyze the scale, frequency, and patterns of recent PLA activities based on 'Military Data', and assess their potential intent.)"
      }},
      {{
        "heading": "Economic Indicators Analysis",
        "content": "(Based on 'Economic Indicators,' analyze market risk aversion and global supply chain stability as reflected by gold and food price changes, and assess their correlation with regional tensions.)"
      }},
      {{
        "heading": "Public Opinion Observation",
        "content": "(Based on 'Public Opinion News,' analyze the focal points of discussion within Taiwan regarding the economy, diplomacy, and cross-strait relations, assessing public morale and the potential for external information influence.)"
      }}
    ]
  }},
  "three_month_probability": {{
    "percentage": "<0-100 的整數>",
    "justification": "（提供一個詳細、分點說明的專業理由，解釋為什麼你給出這個「三個月內」攻台的機率。你的判斷必須綜合所有數據，並點出支持與反對你結論的關鍵因素。）"
  }},
  "data_sources_list": {{
      "military": "{sources.get('military', 'N/A')}",
      "gold": "{sources.get('gold', 'N/A')}",
      "food": "{sources.get('food', 'N/A')}",
      "news": {{
          "economic": {json.dumps(sources.get('news', {}).get('economic', []))},
          "diplomatic": {json.dumps(sources.get('news', {}).get('diplomatic', []))},
          "public_opinion": {json.dumps(sources.get('news', {}).get('public_opinion', []))}
      }}
  }}
}}

---
**輸入數據:**

1.  **當前綜合威脅指數 (Current Overall Threat Index):** {threat_probability:.2f}%
    *這是一個基於軍事、經濟、社會指標計算的量化威脅分數。分數越高，短期異常活動越多。請以此為核心參考。*

2.  **軍事數據 (Military Data):**
    - 最新偵獲共機/共艦擾台總數: {indicators.get('military_latest_intrusions', 'N/A')} 架次/艘次

3.  **經濟指標 (Economic Indicators):**
    - 黃金價格: {indicators.get('gold_price', 'N/A')}
    - 黃金價格24小時變動: {indicators.get('gold_price_change', 'N/A')}
    - 糧食價格: {indicators.get('food_price', 'N/A')}
    - 糧食價格24小時變動: {indicators.get('food_price_change', 'N/A')}

4.  **社會輿情新聞 (Public Opinion News):**
    - 經濟相關新聞標題: {json.dumps(indicators.get('economic_news_titles', []), ensure_ascii=False)}
    - 外交相關新聞標題: {json.dumps(indicators.get('diplomatic_news_titles', []), ensure_ascii=False)}
    - 輿情相關新聞標題: {json.dumps(indicators.get('public_opinion_news_titles', []), ensure_ascii=False)}

5.  **數據來源 (Data Sources):**
{sources_text}
---

請嚴格按照上述指示與 JSON 格式進行分析。
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
            "military": "https://www.mnd.gov.tw/",
            "gold": "https://metalpriceapi.com/",
            "food": "https://api-ninjas.com/api/commodityprice",
            "news": {
                "economic": ["http://news.google.com/1"],
                "diplomatic": ["http://news.google.com/2", "http://news.google.com/3"],
                "public_opinion": ["http://news.google.com/4"],
            }
        }
        mock_threat_prob = 56.67

        print("\n--- 執行報告生成器測試 ---")
        ai_report = generate_ai_report(mock_indicators, mock_threat_prob, mock_sources, test_api_key)
        
        print("\n--- AI 回應 ---")
        print(json.dumps(ai_report, indent=2, ensure_ascii=False))
        print("--- 測試結束 ---")
