import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from dotenv import load_dotenv
from threading import Thread
import uuid

# --- 環境變數與 Matplotlib 設定 ---

# 僅在非 Vercel 環境 (例如本地開發) 中載入 .env 檔案
if not os.environ.get('VERCEL'):
    load_dotenv()

# 為 Vercel 的可寫入 /tmp 資料夾設定 Matplotlib 設定目錄
# 這必須在任何其他模組導入 matplotlib 之前完成
if os.environ.get('VERCEL'):
    matplotlib_config_dir = '/tmp/matplotlib'
    os.makedirs(matplotlib_config_dir, exist_ok=True)
    os.environ['MPLCONFIGDIR'] = matplotlib_config_dir

# --- 匯入我們的模組 ---
# Trigger new deployment to apply the latest environment variable settings
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
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
logging.basicConfig(level=logging.INFO)

# --- 資料庫與特殊使用者初始化 ---
# 在應用程式啟動時，檢查並確保特殊使用者存在於資料庫中。
# 注意：在 Vercel 環境中，這可能會在每次函數冷啟動時運行。
# 注意：在無伺服器環境中，這種 'in-memory' 的快取方式只對單一熱實例有效。
# 對於需要跨實例狀態的應用，應使用 Redis 或資料庫。
task_cache = {}

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

def run_full_analysis_async(task_id, user_email):
    """在背景執行緒中執行完整的分析流程。"""
    with app.app_context():
        try:
            # 階段 1: 爬取資料 & 計算指標
            logging.info(f"[{task_id}] Phase 1: Scraping and Calculating Indicators...")
            news_data = NewsScraper().scrape()
            gold_data = GoldScraper().scrape()
            military_data = MilitaryScraper().scrape()
            food_data = FoodScraper().scrape()
            
            raw_data = {"military": military_data, "news": news_data, "gold": gold_data, "food": food_data}
            indicators = IndicatorCalculator().calculate(raw_data)
            sources = {
                'military': military_data.get('source_url'),
                'gold': gold_data.get('source_url'),
                'food': food_data.get('source_url'),
                'news': news_data.get('sources', {})
            }
            
            task_cache[task_id] = {'status': 'indicators_ready', 'indicators': indicators, 'sources': sources}
            logging.info(f"[{task_id}] Phase 1 Complete. Indicators are ready.")

            # 階段 2: 生成 AI 報告
            logging.info(f"[{task_id}] Phase 2: Generating AI Report...")
            report, chart_url = ReportGenerator().generate_report(indicators)
            
            # 階段 3: 扣除點數並完成
            use_credit(user_email)
            updated_credits = get_remaining_credits(user_email)
            
            task_cache[task_id] = {
                'status': 'completed',
                'indicators': indicators,
                'sources': sources,
                'report': report,
                'chart_image_url': chart_url,
                'updated_credits': updated_credits
            }
            logging.info(f"[{task_id}] Phase 2 Complete. Report generated.")

        except Exception as e:
            logging.error(f"[{task_id}] Error during async analysis: {e}", exc_info=True)
            task_cache[task_id] = {'status': 'failed', 'error': str(e)}

@app.route('/analyze', methods=['POST'])
def analyze_start():
    if 'user_email' not in session:
        return jsonify({'error': '未授權'}), 401

    # 檢查點數
    if get_remaining_credits(session['user_email']) <= 0:
        return jsonify({'error': '您的免費分析次數已用盡。'}), 403

    task_id = str(uuid.uuid4())
    task_cache[task_id] = {'status': 'pending'}
    
    # 啟動背景執行緒
    thread = Thread(target=run_full_analysis_async, args=(task_id, session['user_email']))
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/get_report/<task_id>', methods=['GET'])
def get_task_status(task_id):
    if 'user_email' not in session:
        return jsonify({'error': '未授權'}), 401
    
    task_result = task_cache.get(task_id, {'status': 'not_found'})
    
    # 如果任務完成，從快取中移除以節省記憶體
    if task_result.get('status') in ['completed', 'failed']:
        # 使用 pop 但提供預設值以防競態條件
        task_to_return = task_cache.pop(task_id, task_result)
        return jsonify(task_to_return)
        
    return jsonify(task_result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
