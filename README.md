# 中共攻台威脅分析儀表板

這是一個使用 Python (Flask)、網路爬蟲與 OpenAI API (GPT-4o) 建置的即時儀表板，旨在從公開網路資訊中蒐集多維度數據，分析並量化中華人民共和國對台灣構成的潛在威脅。

---

## 🚀 線上應用程式 (Live Demo)

您可以直接透過以下連結與憑證存取已部署的應用程式：

- **網址**:
- **[https://china-threat-dashboard.vercel.app/](https://china-threat-dashboard.vercel.app/)**
- **[https://cn8964.dpdns.org](https://cn8964.dpdns.org)**

- **帳號**: `cn8964@8964.com`
- **密碼**: `cn8964`

登入後，點擊「開始分析」按鈕，系統將在 1-2 分鐘內完成數據蒐集與分析，並將結果呈現在儀表板上。

---

## ✨ 主要功能

- **即時數據蒐集**：自動爬取台灣國防部發布的軍事動態、國際新聞、黃金價格與糧食價格等公開數據。
- **量化指標分析**：根據蒐集到的數據，計算出軍事、經濟、輿情等多個面向的威脅分數，並整合成一個 0-100% 的綜合威脅指數。
- **AI 報告生成**：利用 `gpt-4o` 模型，根據量化指標和資料來源，深度分析當前局勢，並預測三個月內的衝突機率。
- **視覺化儀表板**：使用 Chart.js 將數據以儀表盤、趨勢圖等方式呈現，並將 AI 生成的中、英文報告並列顯示。
- **響應式網頁介面**：針對桌面及行動裝置優化，確保在各種螢幕尺寸上都有良好的瀏覽體驗。
- **安全登入機制**：採用固定的帳號密碼進行驗證，API 金鑰等敏感資訊安全地儲存在伺服器後端。
- **未來可能會新增更多功能**

## 🛠️ 技術棧

- **後端**: Flask, Gunicorn
- **資料蒐集**: BeautifulSoup, Requests
- **數據分析**: OpenAI API, Numpy
- **前端**: HTML, CSS, JavaScript, Chart.js
- **部署**: Vercel

## ⚠️ 免責聲明

本系統所有數據均來自公開網路資訊，分析結果僅供學術研究與參考，不構成任何形式的投資或決策建議。所有 AI 生成內容可能存在錯誤或偏見，請謹慎評估。

---

## 👨‍💻 開發者資訊 (For Developers)

以下部分提供給想要在本地端運行或自行部署此專案的開發者參考。

### 本地開發設定

1.  **Clone 專案**
    ```bash
    git clone https://github.com/CRCRCRCRCRC/china-threat-dashboard.git
    cd china-threat-dashboard
    ```

2.  **建立並啟動虛擬環境**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **安裝依賴套件**
    ```bash
    pip install -r requirements.txt
    ```

4.  **設定環境變數**
    在專案根目錄建立一個名為 `.env` 的檔案，並填入以下內容：
    ```env
    FLASK_SECRET_KEY="any_random_strong_string_for_session"
    OPENAI_API_KEY="OPENAI_API_KEY"
    METALPRICE_API_KEY="YOUR_METALPRICE_API_KEY"
    COMMODITY_API_KEY="YOUR_COMMODITY_API_KEY"
    ```

5.  **啟動應用程式**
    ```bash
    flask run --port=5001
    ```
    現在您可以透過終端機提示的網址開啟並查看網站。
