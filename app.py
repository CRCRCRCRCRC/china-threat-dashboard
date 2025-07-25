import os
import json
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import threading
import uuid
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
<<<<<<< HEAD
# 不再需要 session，可以移除 secret_key
# app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_very_secretive_and_secure_default_key")
=======
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
>>>>>>> 582f439752d7dd09671e0ddbe1ded2923f47c81d

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
<<<<<<< HEAD
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
=======
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
>>>>>>> 582f439752d7dd09671e0ddbe1ded2923f47c81d

if __name__ == '__main__':
    print("伺服器已啟動。")
    app.run(debug=True, port=5001)
