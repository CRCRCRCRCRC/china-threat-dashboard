import os
import requests
from dotenv import load_dotenv

# 讀取 .env 檔案
load_dotenv()

# 從環境變數中取得您的 API 金鑰
API_KEY = os.getenv("COMMODITYPRICEAPI_KEY")

# --- 這是我們要測試的兩個 API 端點 ---
LATEST_URL = "https://api.commoditypriceapi.com/v2/latest"
FLUCTUATION_URL = "https://api.commoditypriceapi.com/v2/fluctuation"

def test_commodity_api():
    """
    一個獨立的測試腳本，用來直接驗證您的 API 金鑰是否有效。
    """
    if not API_KEY:
        print("!!! 測試失敗：在 .env 檔案中找不到 COMMODITYPRICEAPI_KEY。")
        print("請確認您的 .env 檔案是否在專案根目錄，且內容為：COMMODITYPRICEAPI_KEY=您的金鑰")
        return

    print(f"*** 正在使用金鑰的前五碼 '{API_KEY[:5]}...' 進行測試 ***\n")

    # --- 測試 1: 獲取最新價格 (通常免費方案可用) ---
    print("--- 測試 1: 獲取最新黃金價格 (latest) ---")
    latest_params = {'apiKey': API_KEY, 'symbols': 'XAU'}
    try:
        response_latest = requests.get(LATEST_URL, params=latest_params, timeout=10)
        print(f"狀態碼: {response_latest.status_code}")
        print("伺服器回應:")
        print(response_latest.json())
        if not response_latest.json().get('success'):
             print("\n!!! 'latest' 測試可能未通過：success 欄位不是 true。請檢查回應中的 'message'。")
    except requests.RequestException as e:
        print(f"發生網路錯誤: {e}")
    
    print("\n" + "="*50 + "\n")

    # --- 測試 2: 獲取價格變動 (fluctuation) (常常需要付費方案) ---
    print("--- 測試 2: 獲取黃金價格變動 (fluctuation) ---")
    fluctuation_params = {
        'apiKey': API_KEY,
        'symbols': 'XAU',
        'startDate': '2024-07-20',
        'endDate': '2024-07-21'
    }
    try:
        response_fluctuation = requests.get(FLUCTUATION_URL, params=fluctuation_params, timeout=10)
        print(f"狀態碼: {response_fluctuation.status_code}")
        print("伺服器回應:")
        print(response_fluctuation.json())
        if not response_fluctuation.json().get('success'):
             print("\n!!! 'fluctuation' 測試未通過：success 欄位不是 true。這很可能是 API 方案權限問題。")
    except requests.RequestException as e:
        print(f"發生網路錯誤: {e}")

if __name__ == '__main__':
    test_commodity_api() 