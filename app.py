import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from dotenv import load_dotenv

# --- 匯入我們的模組 ---
from scraper.news_scraper import NewsScraper
from scraper.gold_scraper import GoldScraper
from scraper.military_scraper import MilitaryScraper
from scraper.food_scraper import FoodScraper
from analyzer.indicator_calculator import IndicatorCalculator
from analyzer.report_generator import ReportGenerator
from utils.db import (
    create_user,
    get_user,
    check_password,
    use_credit,
    get_remaining_credits,
    initialize_special_user
)

# --- 初始化 ---
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
logging.basicConfig(level=logging.INFO)

# --- 資料庫與特殊使用者初始化 ---
# 在應用程式啟動時，檢查並確保特殊使用者存在於資料庫中。
# 注意：在 Vercel 環境中，這可能會在每次函數冷啟動時運行。
with app.app_context():
    try:
        # 這會嘗試連接 Vercel KV。如果環境變數未設定 (例如在本地開發)，它會失敗。
        initialize_special_user()
        logging.info("Special user initialization check complete.")
    except Exception as e:
        logging.warning(
            f"Could not initialize special user. This is expected if running locally "
            f"without Vercel KV environment variables. Error: {e}"
        )

# --- 登入/註冊/登出路由 ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_email' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = get_user(email)
        
        if user and check_password(user['password_hash'], password):
            session['user_email'] = user['email']
            session['username'] = user['username']
            flash('登入成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('電子郵件或密碼錯誤，請重試。', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_email' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('兩次輸入的密碼不一致！', 'error')
            return redirect(url_for('register'))

        if get_user(email):
            flash('此電子郵件已經被註冊！', 'error')
            return redirect(url_for('register'))

        new_user = create_user(username, email, password)
        if new_user:
            flash('註冊成功，請登入！', 'success')
            return redirect(url_for('login'))
        else:
            flash('註冊過程中發生錯誤，請稍後再試。', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功登出。', 'success')
    return redirect(url_for('login'))

# --- 主應用程式路由 ---

@app.route('/')
def index():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    try:
        remaining_credits = get_remaining_credits(session['user_email'])
    except Exception as e:
        logging.error(f"Error getting credits for {session['user_email']}: {e}")
        remaining_credits = "錯誤"

    return render_template('index.html', username=session.get('username'), remaining_credits=remaining_credits)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user_email' not in session:
        return jsonify({'error': '未授權的存取，請先登入。'}), 401

    user_email = session['user_email']
    
    # 在執行分析前檢查點數
    try:
        remaining_credits = get_remaining_credits(user_email)
        if isinstance(remaining_credits, int) and remaining_credits <= 0:
            return jsonify({'error': '您的免費分析次數已用盡。'}), 403
    except Exception as e:
        logging.error(f"Could not check credits for {user_email}: {e}")
        return jsonify({'error': '無法驗證您的帳戶狀態，請稍後再試。'}), 500

    try:
        # 1. 實例化所有爬蟲和分析器
        news_scraper = NewsScraper()
        gold_scraper = GoldScraper()
        military_scraper = MilitaryScraper()
        food_scraper = FoodScraper()
        indicator_calculator = IndicatorCalculator()
        report_generator = ReportGenerator()

        # 2. 執行資料搜集
        logging.info("Starting data scraping...")
        news_data = news_scraper.scrape()
        gold_data = gold_scraper.scrape()
        military_data = military_scraper.scrape()
        food_data = food_scraper.scrape()
        logging.info("Data scraping complete.")

        # 3. 整合原始資料並計算指標
        raw_data = {
            "military": military_data,
            "news": news_data,
            "gold": gold_data,
            "food": food_data
        }
        logging.info("Calculating indicators...")
        indicators = indicator_calculator.calculate(raw_data)
        logging.info("Indicator calculation complete.")

        # 4. 生成報告
        logging.info("Generating report...")
        report, chart_image_url = report_generator.generate_report(indicators)
        logging.info("Report generation complete.")

        # 5. 扣除點數
        use_credit(user_email)
        
        # 取得更新後的點數
        updated_credits = get_remaining_credits(user_email)

        return jsonify({
            'report': report,
            'chart_image_url': chart_image_url,
            'updated_credits': updated_credits
        })
        
    except Exception as e:
        logging.error(f"An error occurred during analysis: {e}", exc_info=True)
        return jsonify({'error': f"分析過程中發生內部錯誤: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
