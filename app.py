import os
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from functools import wraps
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
# 建立一個安全的密鑰供 session 使用
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_very_secretive_and_secure_default_key")

# --- 驗證裝飾器 ---
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# --- 登入/登出路由 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        api_key = request.form.get('api_key')
        
        # 使用環境變數中的密碼或一個預設密碼
        correct_password = os.getenv("APP_PASSWORD", "1234")

        if password == correct_password and api_key and api_key.startswith('sk-'):
            session['logged_in'] = True
            session['openai_api_key'] = api_key
            return redirect(url_for('index'))
        else:
            error_message = "密碼錯誤或 API 金鑰無效。"
            return render_template('login.html', error=error_message)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('openai_api_key', None)
    return redirect(url_for('login'))

# --- 主應用程式路由 ---
@app.route('/')
@requires_auth
def index():
    """渲染主頁面"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
@requires_auth
def analyze():
    api_key = session.get('openai_api_key')
    if not api_key:
        return jsonify({"error": "未在 session 中找到 API 金鑰。請重新登入。"}), 401

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
        
        print("分析完成，回傳數據給前端。")
        return jsonify(response_data)

    except Exception as e:
        print(f"分析過程中發生嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # 預設密碼為 1234，您可以在 .env 檔案中設定 APP_PASSWORD 來覆寫
    print("伺服器已啟動。預設密碼為 '1234'。")
    app.run(debug=True, port=5001)
