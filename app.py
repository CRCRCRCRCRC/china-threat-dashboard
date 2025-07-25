import os
import json
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# 匯入我們的模組
from scraper.military_scraper import scrape_military_data
from scraper.news_scraper import scrape_news_data
from scraper.gold_scraper import scrape_gold_prices
from scraper.food_scraper import scrape_food_prices
from analyzer.indicator_calculator import calculate_indicators, calculate_threat_probability
from analyzer.report_generator import generate_ai_report

load_dotenv()

app = Flask(__name__)
# 不再需要 session，可以移除 secret_key
# app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_very_secretive_and_secure_default_key")

# --- 主應用程式路由 ---
@app.route('/')
def index():
    """渲染主頁面"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 金鑰現在由 report_generator 自行從 .env 讀取，前端不再需要傳遞或驗證
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "伺服器端未設定 OPENAI_API_KEY。"}), 500

    try:
        # --- 1. 資料蒐集 ---
        military_data = scrape_military_data()
        news_data = scrape_news_data()
        gold_data = scrape_gold_prices()
        food_data = scrape_food_prices()
        
        raw_data = {
            "military": military_data,
            "news": news_data,
            "gold": gold_data,
            "food": food_data
        }

        # --- 2. 指標計算 ---
        indicators, sources = calculate_indicators(raw_data)
        threat_probability = calculate_threat_probability(indicators)

        # --- 3. AI 報告生成 ---
        ai_report = generate_ai_report(indicators, threat_probability, sources, api_key)

        # --- 4. 準備傳送到前端的資料 ---
        response_data = {
            "indicators": indicators,
            "threat_probability": threat_probability,
            "ai_report": ai_report,
            "chart_data": {
                "labels": ["軍事威脅", "經濟穩定", "社會輿情"],
                "values": [
                    indicators.get('military_score', 0),
                    indicators.get('economic_score', 0),
                    indicators.get('social_sentiment_score', 0)
                ]
            },
            "sources": sources
        }
        
        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f"分析過程中發生嚴重錯誤: {e}"}), 500

if __name__ == '__main__':
    print("伺服器已啟動。")
    app.run(debug=True, port=5001)
