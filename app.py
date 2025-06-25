import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from dotenv import load_dotenv
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

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
tasks = {}

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

def run_analysis_task(task_id, user_email):
    """
    在背景執行緒中執行完整的分析流程，使用並行處理來加速爬蟲。
    """
    with app.app_context():
        try:
            logging.info(f"[{task_id}] Phase 1: Scraping and Calculating Indicators...")
            tasks[task_id]['status'] = 'processing'
            tasks[task_id]['phase'] = 'indicators'

            # --- 並行執行所有爬蟲 ---
            scrapers = {
                'military': MilitaryScraper(),
                'gold': GoldScraper(),
                'food': FoodScraper(),
                'news': NewsScraper()
            }
            
            scraped_data = {}
            with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
                future_to_scraper = {executor.submit(s.scrape): name for name, s in scrapers.items()}
                for future in as_completed(future_to_scraper):
                    scraper_name = future_to_scraper[future]
                    try:
                        data = future.get()
                        scraped_data[scraper_name] = data
                    except Exception as exc:
                        logging.error(f"Scraper '{scraper_name}' generated an exception: {exc}")
                        scraped_data[scraper_name] = {} # 使用空字典作為後備

            # --- 計算指標 ---
            raw_data = {
                "military": scraped_data.get('military', {}),
                "news": scraped_data.get('news', {}),
                "gold": scraped_data.get('gold', {}),
                "food": scraped_data.get('food', {})
            }
            indicators = IndicatorCalculator().calculate(raw_data)
            sources = {
                'military': scraped_data.get('military', {}).get('source_url'),
                'gold': scraped_data.get('gold', {}).get('source_url'),
                'food': scraped_data.get('food', {}).get('source_url'),
                'news': scraped_data.get('news', {}).get('sources', {})
            }
            tasks[task_id]['indicators'] = indicators
            tasks[task_id]['sources'] = sources
            logging.info(f"[{task_id}] Phase 1 complete. Indicators calculated.")
            
            # --- 生成 AI 報告 ---
            logging.info(f"[{task_id}] Phase 2: Generating AI Report...")
            tasks[task_id]['phase'] = 'report'
            
            report, chart_data = ReportGenerator().generate_report(indicators)
            
            # --- 最終化任務 ---
            use_credit(user_email)
            updated_credits = get_remaining_credits(user_email)

            tasks[task_id].update({
                'status': 'completed',
                'report': report,
                'chart_data': chart_data,
                'updated_credits': updated_credits
            })
            logging.info(f"[{task_id}] Task complete. Report generated.")

        except Exception as e:
            logging.error(f"Error during analysis task {task_id}: {e}", exc_info=True)
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['report'] = f"報告生成失敗：{e}"

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user_email' not in session:
        return jsonify({'error': '未授權'}), 401
    
    user_email = session['user_email']
    remaining_credits = get_remaining_credits(user_email)
    if remaining_credits <= 0:
        return jsonify({'error': '點數不足，請儲值'}), 403

    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'task_id': task_id}
    
    # 啟動背景執行緒
    background_thread = threading.Thread(target=run_analysis_task, args=(task_id, user_email))
    background_thread.start()
    
    return jsonify({"task_id": task_id})

@app.route('/get_report/<task_id>', methods=['GET'])
def get_report(task_id):
    if 'user_email' not in session:
        return jsonify({'error': '未授權'}), 401
    
    task_result = tasks.get(task_id, {'status': 'not_found'})
    
    # 如果任務完成或失敗，從記憶體中移除
    if task_result.get('status') in ['completed', 'failed']:
        task_to_return = tasks.pop(task_id, task_result)
        return jsonify(task_to_return)
        
    return jsonify(task_result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
