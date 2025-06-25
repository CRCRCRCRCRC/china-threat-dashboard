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
# 從環境變數讀取 OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- 驗證裝飾器 ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- 登入/登出路由 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 寫死的帳號密碼
        if username == 'cn8964@8964.com' and password == 'cn8964':
            session['logged_in'] = True
            flash('登入成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('帳號或密碼錯誤，請重新輸入。', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('您已成功登出。', 'info')
    return redirect(url_for('login'))

# --- 主應用程式路由 ---
@app.route('/')
@login_required
def index():
    """渲染主頁面"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    if not OPENAI_API_KEY:
        return jsonify({"error": "伺服器未設定 OpenAI API 金鑰。"}), 500

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
        ai_report = generate_ai_report(indicators, threat_probability, sources, OPENAI_API_KEY)

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
    print("伺服器已啟動。")
    app.run(debug=True, port=5001)
