# 偵測中共攻台威脅指數儀表板

本專案是一個基於 Python Flask 的網頁應用程式，旨在透過公開資料與 AI 分析，提供一個關於潛在台海衝突風險的量化指標儀表板。

## 功能

- **一鍵觸發**: 在網頁上點擊按鈕，即可啟動最新的資料蒐集與分析流程。
- **多面向資料蒐集**: 自動爬取與軍事、經濟、外交、輿情相關的公開資訊。
- **量化指標分析**: 將蒐集到的非結構化資料，轉換為可追蹤的量化指標。
- **AI 綜合報告**: 使用 OpenAI API，根據指標與原始資料生成中英雙語的 PDF 分析報告。
- **視覺化呈現**: 在前端使用表格與互動式圖表展示關鍵指標。
- **可擴充設計**: 程式碼採模組化設計，方便未來新增資料來源或分析維度。

## 專案結構

```
/
├── app.py                  # Flask 主應用程式
├── requirements.txt        # Python 套件依賴列表
├── .env                    # 儲存 OpenAI API 金鑰
├── README.md               # 專案說明與部署指南
│
├── scraper/                # 網路爬蟲模組
├── analyzer/               # 資料分析模組
├── utils/                  # 工具函式模組
├── templates/              # Flask 網頁模板
└── static/                 # 靜態檔案 (CSS, JavaScript)
```

## 安裝與執行

### 1. 前置需求

- Python 3.8+
- Git

### 2. 複製專案

```bash
git clone <repository-url>
cd <repository-directory>
```

### 3. 設定虛擬環境

- **Windows**:
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 4. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 5. 設定 API 金鑰

將您的 OpenAI API 金鑰設定為環境變數。

建立一個名為 `.env` 的檔案，並在其中加入以下內容：

```
# 請將您的 OpenAI API 金鑰貼在此處
OPENAI_API_KEY="sk-..."
```

應用程式會自動從這個檔案讀取金鑰。

### 6. 執行本地伺服器

```bash
flask run
```

執行後，在瀏覽器中開啟 `http://127.0.0.1:5000` 即可看到應用程式介面。

## 部署到伺服器

若要將此應用程式部署到生產環境伺服器（例如 Heroku, AWS, GCP），建議使用生產級的 WSGI 伺服器，例如 Gunicorn 或 Waitress。

### 使用 Waitress (Windows)

Waitress 是一個適用於 Windows 環境的純 Python WSGI 伺服器。

1. **安裝 Waitress**:
   ```bash
   pip install waitress
   ```

2. **啟動應用程式**:
   ```bash
   waitress-serve --host 0.0.0.0 --port 8000 app:app
   ```

### 使用 Gunicorn (Linux/macOS)

Gunicorn 是在 Unix-like 系統上最廣泛使用的 WSGI 伺服器。

1. **安裝 Gunicorn**:
   ```bash
   pip install gunicorn
   ```

2. **啟動應用程式**:
   ```bash
   gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
   ```

## 注意事項

- **網路爬蟲**: 本專案的爬蟲僅為示範性質，目標網站的結構若有變更，可能會導致爬蟲失效，屆時需要更新爬蟲程式碼。
- **資料準確性**: 自動化分析的結果僅供參考，不應作為任何決策的唯一依據。
- **API 費用**: 使用 OpenAI API 會產生費用，請注意您的用量。
