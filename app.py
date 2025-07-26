import os
import json
import logging
import threading
import uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request
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
logging.basicConfig(level=logging.INFO)

# 全域任務儲存
tasks = {}

# 恢復 try...except 區塊以處理資料庫模組不存在的情況
with app.app_context():
    try:
        from utils.db_helper import init_db
        init_db()
        logging.info("資料庫初始化完成 (如果存在)")
    except ImportError:
        logging.warning("資料庫模組 'db_helper' 未找到，將在無資料庫模式下運行。")
    except Exception as e:
        logging.error(f"資料庫初始化時發生錯誤: {e}")

@app.route('/')
def index():
    """渲染主頁面"""
    return render_template('index.html')

def run_analysis_task(task_id):
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
    """開始威脅分析"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'task_id': task_id}
    
    # 啟動背景執行緒
    background_thread = threading.Thread(target=run_analysis_task, args=(task_id,))
    background_thread.start()
    
    return jsonify({"task_id": task_id})

@app.route('/get_report/<task_id>', methods=['GET'])
def get_report(task_id):
    """獲取分析報告"""
    task_result = tasks.get(task_id, {'status': 'not_found'})
    
    # 如果任務完成或失敗，從記憶體中移除
    if task_result.get('status') in ['completed', 'failed']:
        task_to_return = tasks.pop(task_id, task_result)
        return jsonify(task_to_return)
        
    return jsonify(task_result)

if __name__ == '__main__':
    print("伺服器已啟動。")
    app.run(debug=True, port=5001)
