import os
import json
import logging
import threading
import uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# 匯入我們的模組
from scraper.military_scraper import scrape_military_data
from scraper.news_scraper import scrape_news_data
from scraper.gold_scraper import scrape_gold_prices
from scraper.food_scraper import scrape_food_prices
from analyzer.indicator_calculator import calculate_indicators, calculate_threat_probability
from analyzer.report_generator import generate_ai_report

load_dotenv()

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
        # 嘗試導入資料庫相關的功能
        from utils.db_helper import (init_db, create_user, verify_user, 
                                   get_remaining_credits, deduct_credits, add_credits)
        init_db()
        
        # 創建預設管理員帳戶
        default_admin_email = "admin@example.com"
        default_admin_password = "admin123"
        create_user("admin", default_admin_email, default_admin_password)
        add_credits(default_admin_email, 10)  # 給管理員 10 點初始點數
        
        logging.info("資料庫和預設使用者初始化完成")
    except ImportError:
        logging.warning("資料庫模組未找到，應用程式將在無認證模式下運行")
        # 定義空函數以避免錯誤
        def verify_user(email, password): return None
        def get_remaining_credits(email): return float('inf')
        def deduct_credits(email, amount): pass
        def create_user(username, email, password): return True
        def add_credits(email, amount): pass

# --- 使用者認證路由 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = verify_user(email, password)
        if user:
            session['user_email'] = email
            flash('登入成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('電子郵件或密碼錯誤。', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # 簡單驗證
        if len(password) < 6:
            flash('密碼至少需要6個字符。', 'error')
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
    """渲染主頁面"""
    return render_template('index.html')

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
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(scrape_military_data): 'military',
                    executor.submit(scrape_news_data): 'news',
                    executor.submit(scrape_gold_prices): 'gold',
                    executor.submit(scrape_food_prices): 'food'
                }

                raw_data = {}
                for future in as_completed(futures):
                    data_type = futures[future]
                    try:
                        result = future.result()
                        raw_data[data_type] = result
                        logging.info(f"[{task_id}] {data_type.title()} data collected successfully")
                    except Exception as exc:
                        logging.error(f"[{task_id}] {data_type.title()} data collection failed: {exc}")
                        raw_data[data_type] = {"error": str(exc)}

            # --- 計算指標 ---
            indicators = calculate_indicators(
                raw_data.get('military', {}),
                raw_data.get('news', {}), 
                raw_data.get('gold', {}),
                raw_data.get('food', {})
            )
            
            overall_threat_level = calculate_threat_probability(indicators)
            
            logging.info(f"[{task_id}] Phase 2: Generating AI Report...")
            tasks[task_id]['phase'] = 'report'

            # --- 生成完整報告 ---
            report = generate_ai_report(
                military_data=raw_data.get('military', {}),
                news_data=raw_data.get('news', {}),
                gold_data=raw_data.get('gold', {}),
                food_data=raw_data.get('food', {}),
                military_indicator=indicators.get('military', 0),
                economic_indicator=indicators.get('economic', 0),
                overall_threat_level=overall_threat_level
            )

            # --- 扣除使用者點數 ---
            deduct_credits(user_email, 1)

            # --- 完成任務 ---
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['threat_level'] = overall_threat_level
            tasks[task_id]['indicators'] = indicators
            tasks[task_id]['raw_data'] = raw_data
            tasks[task_id]['report'] = report
            tasks[task_id]['timestamp'] = datetime.now().isoformat()
            
            logging.info(f"[{task_id}] Task completed successfully")

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
    print("伺服器已啟動。")
    app.run(debug=True, port=5001)
