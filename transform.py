"""RP Parameter 轉換引擎。

將 'RP_Maintenance (input)' 的資料，套用 Access MDB
'Upload Old Article RP Parameter (ideal stock added)' 的業務邏輯，
產生 'RP_Maintenance (output)' 結果。

本模組不依賴 Access / pyodbc，所有參考資料 (Warehouse Calendar、Shop_Class、
MSS List、D001 MOQ、SKU_3M_SALES_F4) 皆已內建為 JSON，方便在 Zeabur 雲端執行。
"""
import json
import os

# ---------------------------------------------------------------------------
# 載入內建參考資料
# ---------------------------------------------------------------------------
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

with open(os.path.join(_DATA_DIR, "reference_data.json"), encoding="utf-8") as f:
    _REF = json.load(f)

WAREHOUSE_CALENDAR = _REF["warehouse_calendar"]   # { shop: {"p":.., "d":..} }
SHOP_CLASS = _REF["shop_class"]                   # { shop: {"class":.., ...} }
MSS_LIST = _REF["mss_list"]                       # {"shop|mc": {"a","b","c"} }
D001_MOQ = _REF["d001_moq"]                       # { sku: moq }

with open(os.path.join(_DATA_DIR, "coverage_map.json"), encoding="utf-8") as f:
    COVERAGE_MAP = json.load(f)                   # { site: target_coverage }

# SKU_3M_SALES_F4 的 ABC_TOTAL 覆寫 (選用、可由前端上傳補入)。
# 鍵為 "site|article"，值為 A/B/C。
ABC_OVERRIDE = {}


def set_abc_override(rows):
    """以 [['site','article','ABC_TOTAL'], ...] 覆寫 ABC 規則。"""
    ABC_OVERRIDE.clear()
    for r in rows:
        if len(r) >= 3 and r[0] and r[1]:
            ABC_OVERRIDE[f"{r[0]}|{r[1]}"] = str(r[2]).strip()


# ---------------------------------------------------------------------------
# 輸出欄位順序 (與 RP_Maintenance (output).xlsx 完全一致)
# ---------------------------------------------------------------------------
OUTPUT_COLUMNS = [
    "Site", "Article", "Article Description", "Brand", "MC", "MC Description",
    "Article categor", "Article Type", "Status", "First Sales Dat",
    "Season category", "Available to", "Launch Date",
    "Sales Qty 20000101 -  20061203", "Sales Price", "Avg Weekly Sales",
    "Cal Stock Turnover", "Stock On Hand  20070827", "Safety Stock",
    "Purchase Group", "RP Type", "Planning Cycle", "Delivery Cycle",
    "Stock Planner", "Reorder Point", "Delivery Days", "Target Coverage",
    "Target Stock", "Supply Source (1=Vendor/2=DC)", "ABC Indicator",
    "Smooth Promotion", "Forecast Model", "Historical periods",
    "Forecast periods", "Periods per season", "Current consumption qty",
    "Week 1 forecast value", "Week 2 forecast value", "Week 3 forecast value",
    "Week 4 forecast value", "Week 5 forecast value",
    "New Safety Qty", "New Purchase Group", "New RP Typ", "New Planning Cycle",
    "New Delivery Cycle", "New Stock Planner", "New Reorder Point",
    "New Delivery Days", "New Traget Coverage", "New Target Stock",
    "New Supply Source", "New ABC Indicator", "New Smoothing (0/1)",
    "New Forecast Model", "New Historical perio", "New Forecast periods",
    "New Periods per season", "New Current consumption qty",
    "New Week 1 forecast value", "New Week 2 forecast value",
    "New Week 3 forecast value", "New Week 4 forecast value",
    "New Week 5 forecast value", "A QTY", "B QTY", "C QTY",
]

# 輸入欄位名稱在不同來源 (txt/xlsx/csv) 有微小差異，這裡建立正規化對照表。
_INPUT_ALIASES = {
    "Sales Qty. 20000101 -  20240214": "Sales Qty",
    "Sales Qty 20000101 -  20061203": "Sales Qty",
    "Avg. Weekly Sales": "Avg Weekly Sales",
    "Cal. Stock Turnover": "Cal Stock Turnover",
    "Stock On Hand  20260624": "Stock On Hand",
    "Stock On Hand  20070827": "Stock On Hand",
    "Supply Source (1=Vendor/2=DC)": "Supply Source",
    "New Traget Coverage": "New Traget Coverage",
    "New Target Coverage": "New Traget Coverage",
    "New RP Typ": "New RP Typ",
    "New RP Type": "New RP Typ",
    "New Historical perio": "New Historical perio",
    "New Historical periods": "New Historical perio",
    "New Smoothing (0/1)": "New Smoothing",
    "New consumption qty": "New Current consumption qty",
    "New Current consumption qty": "New Current consumption qty",
    "New Week 1 forecast": "New Week 1 forecast",
    "New Week 1 forecast value": "New Week 1 forecast",
    "New Week 2 forecast": "New Week 2 forecast",
    "New Week 2 forecast value": "New Week 2 forecast",
    "New Week 3 forecast": "New Week 3 forecast",
    "New Week 3 forecast value": "New Week 3 forecast",
    "New Week 4 forecast": "New Week 4 forecast",
    "New Week 4 forecast value": "New Week 4 forecast",
    "New Week 5 forecast": "New Week 5 forecast",
    "New Week 5 forecast value": "New Week 5 forecast",
}


def _norm_header(h):
    """將輸入欄位名稱正規化成統一鍵。"""
    h = (h or "").strip()
    return _INPUT_ALIASES.get(h, h)


def _s(val):
    """安全轉字串並去空白 (處理 None / 數字)。"""
    if val is None:
        return ""
    return str(val).strip()


# ---------------------------------------------------------------------------
# 核心轉換邏輯
# ---------------------------------------------------------------------------
def transform_rows(rows, header):
    """對一組資料列套用轉換，回傳輸出列 (list[dict])。

    rows: list[list[str]]  (不含表頭的資料列)
    header: list[str]      (正規化前的表頭)
    回傳: (output_rows, stats)
        output_rows: list[dict]  每筆為 {欄位: 值}，含全部 67 欄
        stats: {"total":n, "warn_unknown_site": [...], ...}
    """
    idx = {}
    for i, h in enumerate(header):
        idx[_norm_header(h)] = i

    def col(row, name, default=""):
        j = idx.get(name)
        if j is None or j >= len(row):
            return default
        return _s(row[j])

    stats = {"total": 0, "warn_unknown_site": set(),
             "warn_unknown_mc": set(), "abc_overridden": 0}
    output_rows = []

    for raw in rows:
        site = col(raw, "Site")
        article = col(raw, "Article")
        mc = col(raw, "MC")
        abc_in = col(raw, "ABC Indicator")

        # --- New ABC Indicator ---
        # 預設沿用輸入 ABC，空白則為 C；若 SKU_3M_SALES_F4 有覆寫則採用。
        ov = ABC_OVERRIDE.get(f"{site}|{article}")
        if ov:
            new_abc = ov
            stats["abc_overridden"] += 1
        elif abc_in:
            new_abc = abc_in
        else:
            new_abc = "C"

        # --- A / B / C QTY (來自 MSS List: shop + MC) ---
        mss = MSS_LIST.get(f"{site}|{mc}", {})
        if not mss:
            stats["warn_unknown_mc"].add(f"{site}|{mc}")
        a_qty = mss.get("a", "")
        b_qty = mss.get("b", "")
        c_qty = mss.get("c", "")

        # --- New Planning / Delivery Cycle (來自 Warehouse Calendar) ---
        wc = WAREHOUSE_CALENDAR.get(site)
        if wc:
            new_planning_cycle = wc.get("p", "")
            new_delivery_cycle = wc.get("d", "")
        else:
            new_planning_cycle = col(raw, "Planning Cycle")
            new_delivery_cycle = col(raw, "Delivery Cycle")
            stats["warn_unknown_site"].add(site)

        # --- New Target Coverage (site 對照表) ---
        new_target_coverage = COVERAGE_MAP.get(site, col(raw, "Target Coverage"))

        # 組裝輸出 (保留原始欄位，補上 New_* 欄位)
        out = {
            "Site": site,
            "Article": article,
            "Article Description": col(raw, "Article Description"),
            "Brand": col(raw, "Brand"),
            "MC": mc,
            "MC Description": col(raw, "MC Description"),
            "Article categor": col(raw, "Article categor"),
            "Article Type": col(raw, "Article Type"),
            "Status": col(raw, "Status"),
            "First Sales Dat": col(raw, "First Sales Dat"),
            "Season category": col(raw, "Season category"),
            "Available to": col(raw, "Available to"),
            "Launch Date": col(raw, "Launch Date"),
            "Sales Qty 20000101 -  20061203": col(raw, "Sales Qty"),
            "Sales Price": col(raw, "Sales Price"),
            "Avg Weekly Sales": col(raw, "Avg Weekly Sales"),
            "Cal Stock Turnover": col(raw, "Cal Stock Turnover"),
            "Stock On Hand  20070827": col(raw, "Stock On Hand"),
            "Safety Stock": col(raw, "Safety Stock"),
            "Purchase Group": col(raw, "Purchase Group"),
            "RP Type": col(raw, "RP Type"),
            "Planning Cycle": col(raw, "Planning Cycle"),
            "Delivery Cycle": col(raw, "Delivery Cycle"),
            "Stock Planner": col(raw, "Stock Planner"),
            "Reorder Point": col(raw, "Reorder Point"),
            "Delivery Days": col(raw, "Delivery Days"),
            "Target Coverage": col(raw, "Target Coverage"),
            "Target Stock": col(raw, "Target Stock"),
            "Supply Source (1=Vendor/2=DC)": col(raw, "Supply Source"),
            "ABC Indicator": abc_in,
            "Smooth Promotion": col(raw, "Smooth Promotion"),
            "Forecast Model": col(raw, "Forecast Model"),
            "Historical periods": col(raw, "Historical periods"),
            "Forecast periods": col(raw, "Forecast periods"),
            "Periods per season": col(raw, "Periods per season"),
            "Current consumption qty": col(raw, "Current consumption qty"),
            "Week 1 forecast value": col(raw, "Week 1 forecast value"),
            "Week 2 forecast value": col(raw, "Week 2 forecast value"),
            "Week 3 forecast value": col(raw, "Week 3 forecast value"),
            "Week 4 forecast value": col(raw, "Week 4 forecast value"),
            "Week 5 forecast value": col(raw, "Week 5 forecast value"),
            # ===== New_* 計算結果 =====
            "New Safety Qty": "",
            "New Purchase Group": col(raw, "New Purchase Group"),
            "New RP Typ": "",
            "New Planning Cycle": new_planning_cycle,
            "New Delivery Cycle": new_delivery_cycle,
            "New Stock Planner": col(raw, "New Stock Planner"),
            "New Reorder Point": col(raw, "New Reorder Point"),
            "New Delivery Days": "1",
            "New Traget Coverage": new_target_coverage,
            "New Target Stock": col(raw, "New Target Stock"),
            "New Supply Source": "2",
            "New ABC Indicator": new_abc,
            "New Smoothing (0/1)": "0",
            "New Forecast Model": "G",
            "New Historical perio": "2",
            "New Forecast periods": "5",
            "New Periods per season": "52",
            "New Current consumption qty": col(raw, "New Current consumption qty"),
            "New Week 1 forecast value": col(raw, "New Week 1 forecast"),
            "New Week 2 forecast value": col(raw, "New Week 2 forecast"),
            "New Week 3 forecast value": col(raw, "New Week 3 forecast"),
            "New Week 4 forecast value": col(raw, "New Week 4 forecast"),
            "New Week 5 forecast value": col(raw, "New Week 5 forecast"),
            "A QTY": a_qty,
            "B QTY": b_qty,
            "C QTY": c_qty,
        }
        output_rows.append(out)
        stats["total"] += 1

    stats["warn_unknown_site"] = sorted(stats["warn_unknown_site"])
    stats["warn_unknown_mc"] = sorted(stats["warn_unknown_mc"])
    return output_rows, stats


def rows_to_lists(output_rows):
    """將 list[dict] 轉成 [header, *rows] 的二維清單 (依 OUTPUT_COLUMNS 順序)。"""
    data = [list(OUTPUT_COLUMNS)]
    for r in output_rows:
        data.append([r.get(c, "") for c in OUTPUT_COLUMNS])
    return data
