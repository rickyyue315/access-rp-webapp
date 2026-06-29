# RP Maintenance 參數轉換 (Zeabur)

將原本在 Access MDB **「Upload Old Article RP Parameter (ideal stock added)_2003 新壓縮版本」**
中運作的業務邏輯，重新實作為一個網頁服務。

只需**上傳 `RP_Maintenance (input)`** 檔案，即可自動產生 **`RP_Maintenance (output)`** 結果下載。

---

## ✨ 功能

- 上傳一個檔案 → 下載結果，**一個動作完成**（不需要分步驟操作）
- 支援輸入格式：`.txt`（Tab 分隔，SAP 原始匯出）、`.csv`、`.xls`、`.xlsx`
- 輸出為與原 Access 完全一致欄位順序的 `.xlsx`
- **不依賴 Access / pyodbc / MDB 驅動**，所有參考資料已內建，可在 Zeabur 雲端直接運行

## 🧠 轉換邏輯（移植自 Access MDB）

對每一列 (Site + Article) 計算 `New_*` 欄位：

| 輸出欄位 | 計算來源 |
|---|---|
| `New Planning Cycle` | `Warehouse Calendar` 中該 Site 的 `P` |
| `New Delivery Cycle` | `Warehouse Calendar` 中該 Site 的 `D` |
| `New Delivery Days` | 固定 `1` |
| `New Traget Coverage` | 該 Site 的 Target Coverage 對照表 |
| `New Supply Source` | 固定 `2`（DC / 倉庫） |
| `New ABC Indicator` | 沿用輸入 ABC，空白預設 `C`（可被 ABC 覆寫檔覆蓋） |
| `New Smoothing (0/1)` | 固定 `0` |
| `New Forecast Model` | 固定 `G` |
| `New Historical perio` | 固定 `2` |
| `New Forecast periods` | 固定 `5` |
| `New Periods per season` | 固定 `52` |
| `New RP Typ` | 空白（沿用） |
| `New Safety Qty` | 空白 |
| `A QTY / B QTY / C QTY` | `MSS List` 中該 Site + MC 的 A / B / C 安全庫存 |

> 內建參考資料：165 個店鋪 (Warehouse Calendar)、231 個店鋪 (Shop_Class)、
> 117,263 筆 MSS List、35,224 筆 D001 MOQ，皆由原 Access MDB 匯出。

## 🧪 驗證結果

以 `RP_Maintenance (input).txt`（264 列、17,688 個欄位值）測試，
對照原 `RP_Maintenance (output).xlsx`：

- **核心邏輯：100% 欄位值完全相符**（搭配 ABC 覆寫檔時為 100%）
- 未提供 ABC 覆寫檔時：**99.98%** 相符，僅 4 個 `New ABC Indicator` 值差異
  （這 4 個來自 `SKU_3M_SALES_F4.ABC_TOTAL` 外部資料，可用「進階」分頁上傳補入）

## 🚀 本地執行

```bash
pip install -r requirements.txt
python app.py
# 開啟 http://localhost:8080
```

## ☁️ 部署到 Zeabur

1. 將整個 `rp-zeabur` 資料夾推到 GitHub 儲存庫
2. 在 Zeabur 建立新服務 → 選擇 **Git Repository**
3. Zeabur 會自動偵測 Python 專案：
   - 安裝 `requirements.txt`
   - 以 `Procfile` 的指令（gunicorn）啟動
4. 在 Zeabur 設定中加入網域（Generate Domain）即可使用

> 若 Zeabur 未自動偵測啟動指令，可在服務設定中將
> **Start Command** 設為：
> ```
> gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
> ```

## 📁 檔案結構

```
rp-zeabur/
├── app.py              # Flask 主程式（網頁 + API）
├── transform.py        # 轉換引擎（核心業務邏輯）
├── input_parser.py     # 輸入檔剖析（txt/csv/xls/xlsx）
├── templates/
│   └── index.html      # 上傳介面
├── data/
│   ├── reference_data.json   # 內建參考資料（Warehouse Calendar / MSS List / MOQ）
│   └── coverage_map.json     # Site → Target Coverage 對照
├── requirements.txt
├── runtime.txt         # Python 版本
├── Procfile            # Zeabur / Heroku 啟動指令
└── zeabur.json         # Zeabur 設定
```

## 🔌 程式化 API

除了網頁介面，亦提供 JSON API：

```bash
curl -F "file=@RP_Maintenance (input).txt" \
     https://你的網域/api/process
```

回傳處理統計與前 5 列預覽。完整結果請用網頁的 `POST /process`（直接下載 xlsx）。
