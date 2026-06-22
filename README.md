# RP參數計算系統 (Web版)

將原本 Access MDB 的補貨參數計算邏輯移植到 Python Flask Web 應用。

## 本地執行

`ash
pip install flask gunicorn
python app.py
`

瀏覽器開啟 http://localhost:5000

## Zeabur 部署步驟

### 方法一：透過 GitHub（推薦）

1. **建立 GitHub Repository**
   - 瀏覽 https://github.com 並登入
   - 點「New repository」，取名如 
p-parameter-webapp
   - 不要勾選任何初始化選項

2. **推送程式碼到 GitHub**
   `ash
   git remote add origin https://github.com/你的帳號/rp-parameter-webapp.git
   git branch -M main
   git push -u origin main
   `

3. **在 Zeabur 部署**
   - 瀏覽 https://zeabur.com 並登入（可用 GitHub 帳號）
   - 點「Create Project」→「Deploy from GitHub」
   - 授權 Zeabur 存取 GitHub，選擇 
p-parameter-webapp
   - Zeabur 會自動偵測 Python/Flask，無需額外設定

4. **設定 Persistent Storage（重要）**
   - 在 Zeabur 專案儀表板，點你的 service
   - 選「Storage」→「Add Volume」
   - Mount Path 填 /app/data（讓 SQLite 資料不會因重啟而遺失）

### 方法二：透過 Zeabur CLI

`ash
# 安裝 Zeabur CLI
npm install -g @zeabur/cli

# 登入
zeabur login

# 部署
zeabur deploy
`

## 注意事項

- SQLite 資料庫在 Zeabur 若無掛載 Persistent Volume，每次重新部署資料會遺失
- 建議設定 Volume 掛載到 /app/data 目錄
- CSV 上傳檔案同樣建議使用 Volume 或物件儲存
