from database import get_db

def run_check_moq():
    """移植自 MDB Check MOQ 查詢
    
    ND → new_safety_qty = 0
    RF → new_safety_qty = MAX(MOQ, 原本值)
    """
    db = get_db()

    nd_cur = db.execute("""
        UPDATE final_result
        SET new_safety_qty = 0,
            moq_checked = 1
        WHERE new_rp_type = 'ND'
          AND (moq_checked = 0 OR moq_checked IS NULL)
    """)

    rf_cur = db.execute("""
        UPDATE final_result
        SET new_safety_qty = (
            SELECT CASE
                WHEN CAST(d001_moq.moq AS INTEGER) > COALESCE(CAST(final_result.new_safety_qty AS INTEGER), 0)
                THEN CAST(d001_moq.moq AS INTEGER)
                ELSE COALESCE(CAST(final_result.new_safety_qty AS INTEGER), 0)
            END
        ),
        moq_checked = 1
        FROM d001_moq
        WHERE final_result.article = d001_moq.sku
          AND (final_result.new_rp_type IS NULL OR final_result.new_rp_type = '' OR final_result.new_rp_type != 'ND')
          AND CAST(d001_moq.moq AS INTEGER) > COALESCE(CAST(final_result.new_safety_qty AS INTEGER), 0)
          AND (final_result.moq_checked = 0 OR final_result.moq_checked IS NULL)
    """)

    untouched = db.execute("""
        UPDATE final_result
        SET moq_checked = 1
        WHERE moq_checked = 0 OR moq_checked IS NULL
    """)

    db.commit()
    return {
        "updated": (nd_cur.rowcount if nd_cur else 0)
                  + (rf_cur.rowcount if rf_cur else 0),
        "detail": {
            "nd_set_to_zero": nd_cur.rowcount if nd_cur else 0,
            "rf_overridden_by_moq": rf_cur.rowcount if rf_cur else 0,
        }
    }


def apply_ideal_stock():
    """移植自 MDB Final Result 2 查詢
    
    只對 Shop_Class 中有記錄的 site 套用理想庫存，
    覆蓋 new_safety_qty。
    """
    db = get_db()

    cur = db.execute("""
        UPDATE final_result
        SET new_safety_qty = (
            SELECT CAST(ideal.ideal_stock AS INTEGER)
            FROM ideal_stock AS ideal
            WHERE ideal.site = final_result.site
              AND ideal.article = final_result.article
        ),
        ideal_stock_applied = 1
        WHERE EXISTS (
            SELECT 1 FROM shop_class
            WHERE shop_class.shop = final_result.site
        )
        AND EXISTS (
            SELECT 1 FROM ideal_stock AS ideal
            WHERE ideal.site = final_result.site
              AND ideal.article = final_result.article
              AND CAST(ideal.ideal_stock AS INTEGER) != COALESCE(CAST(final_result.new_safety_qty AS INTEGER), 0)
        )
    """)

    untouched = db.execute("""
        UPDATE final_result
        SET ideal_stock_applied = 1
        WHERE ideal_stock_applied = 0 OR ideal_stock_applied IS NULL
    """)

    db.commit()
    return {
        "updated": cur.rowcount if cur else 0,
        "detail": {
            "overridden_by_ideal_stock": cur.rowcount if cur else 0,
        }
    }


def find_problem_transactions():
    """移植自 MDB Problem Transaction 查詢
    
    檢查三類問題：
    1. new_safety_qty < 0
    2. new_rp_type 為空
    3. article 不在 article_master 中
    """
    db = get_db()

    db.execute("DELETE FROM problem_transactions")

    db.execute("""
        INSERT INTO problem_transactions (site, article, mc, mc_description, reason)
        SELECT site, article, mc, mc_description, 'Negative safety stock'
        FROM final_result
        WHERE CAST(new_safety_qty AS INTEGER) < 0
    """)

    db.execute("""
        INSERT INTO problem_transactions (site, article, mc, mc_description, reason)
        SELECT site, article, mc, mc_description, 'Missing RP type'
        FROM final_result
        WHERE new_rp_type IS NULL OR new_rp_type = ''
    """)

    db.execute("""
        INSERT INTO problem_transactions (site, article, mc, mc_description, reason)
        SELECT site, article, mc, mc_description, 'Article not in master'
        FROM final_result fr
        WHERE NOT EXISTS (
            SELECT 1 FROM article_master am WHERE am.article = fr.article
        )
    """)

    db.commit()

    count = db.execute("SELECT COUNT(*) as c FROM problem_transactions").fetchone()["c"]
    return {"problem_count": count}


def process_type_conversions():
    """移植自 MDB Step 2 整組查詢
    
    1. 記錄類型變更到 nd_to_rf / rf_to_nd 表
    2. 實際計算並更新 new_* 欄位
    """
    db = get_db()

    db.execute("DELETE FROM nd_to_rf")
    db.execute("DELETE FROM rf_to_nd")

    nd_to_rf = db.execute("""
        INSERT INTO nd_to_rf
        SELECT NULL, site, article, article_description, brand, mc, mc_description,
               article_category, article_type, status, first_sales_date,
               season_category, available_to, launch_date,
               sales_qty, sales_price, avg_weekly_sales, cal_stock_turnover, stock_on_hand,
               safety_stock, purchase_group, rp_type, planning_cycle, delivery_cycle,
               stock_planner, reorder_point, delivery_days, target_coverage,
               supply_source, abc_indicator, smooth_promotion, forecast_model,
               historical_periods, forecast_periods, periods_per_season,
               current_consumption_qty,
               week1_forecast, week2_forecast, week3_forecast, week4_forecast, week5_forecast,
               new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
               new_delivery_cycle, new_stock_planner, new_reorder_point,
               new_delivery_days, new_target_coverage, new_supply_source,
               new_abc_indicator, new_smoothing, new_forecast_model,
               new_historical_periods, new_forecast_periods, new_periods_per_season,
               new_current_consumption_qty,
               new_week1_forecast, new_week2_forecast, new_week3_forecast,
               new_week4_forecast, new_week5_forecast,
               datetime('now')
        FROM final_result
        WHERE rp_type = 'ND' AND new_rp_type = 'RF'
    """)
    nd_to_rf_count = nd_to_rf.rowcount

    rf_to_nd = db.execute("""
        INSERT INTO rf_to_nd
        SELECT NULL, site, article, article_description, brand, mc, mc_description,
               article_category, article_type, status, first_sales_date,
               season_category, available_to, launch_date,
               sales_qty, sales_price, avg_weekly_sales, cal_stock_turnover, stock_on_hand,
               safety_stock, purchase_group, rp_type, planning_cycle, delivery_cycle,
               stock_planner, reorder_point, delivery_days, target_coverage,
               supply_source, abc_indicator, smooth_promotion, forecast_model,
               historical_periods, forecast_periods, periods_per_season,
               current_consumption_qty,
               week1_forecast, week2_forecast, week3_forecast, week4_forecast, week5_forecast,
               new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
               new_delivery_cycle, new_stock_planner, new_reorder_point,
               new_delivery_days, new_target_coverage, new_supply_source,
               new_abc_indicator, new_smoothing, new_forecast_model,
               new_historical_periods, new_forecast_periods, new_periods_per_season,
               new_current_consumption_qty,
               new_week1_forecast, new_week2_forecast, new_week3_forecast,
               new_week4_forecast, new_week5_forecast,
               datetime('now')
        FROM final_result
        WHERE rp_type = 'RF' AND new_rp_type = 'ND'
    """)
    rf_to_nd_count = rf_to_nd.rowcount

    db.commit()

    rf_to_nd_updated = _calculate_rf_to_nd_params(db)
    nd_to_rf_updated = _calculate_nd_to_rf_params(db)

    return {
        "nd_to_rf": nd_to_rf_count,
        "rf_to_nd": rf_to_nd_count,
        "rf_to_nd_params_updated": rf_to_nd_updated,
        "nd_to_rf_params_updated": nd_to_rf_updated,
    }


def _calculate_rf_to_nd_params(db):
    """移植自 MDB 'RF to ND (update)' 查詢
    
    RF→ND 時重新計算補貨參數：
    - new_safety_qty = 0
    - new_rp_type = 'ND' (已設定)
    - new_planning_cycle = Warehouse Calendar.P
    - new_delivery_cycle = Warehouse Calendar.D
    - new_delivery_days = 3
    - new_target_coverage = min(delivery_days + ABC_extra, Shop_Class.coverage)
    - new_supply_source = 2
    - new_abc_indicator = 保留原值或 'A'
    - new_smoothing = 0
    - new_forecast_model = 'G'
    - new_historical_periods = 3
    - new_forecast_periods = 5
    - new_periods_per_season = 52
    """
    total = 0

    rows = db.execute("""
        SELECT fr.rowid AS rid, fr.site, fr.article, fr.new_abc_indicator,
               wc.p AS wc_p, wc.d AS wc_d,
               sc.coverage_a_items, sc.coverage_b_items, sc.coverage_c_items
        FROM final_result fr
        LEFT JOIN warehouse_calendar wc ON fr.site = wc.shop
        LEFT JOIN shop_class sc ON fr.site = sc.shop
        WHERE fr.rp_type = 'RF' AND fr.new_rp_type = 'ND'
    """).fetchall()

    for r in rows:
        abc = (r["new_abc_indicator"] or "").strip()
        if not abc:
            abc = "A"

        delivery_days = 3

        if abc == "A":
            coverage = delivery_days + 12
            max_cov = r["coverage_a_items"]
            target_coverage = min(coverage, max_cov) if max_cov else coverage
        elif abc == "B":
            coverage = delivery_days + 7
            max_cov = r["coverage_b_items"]
            target_coverage = min(coverage, max_cov) if max_cov else coverage
        else:
            coverage = delivery_days + 4
            max_cov = r["coverage_c_items"]
            target_coverage = min(coverage, max_cov) if max_cov else coverage

        db.execute("""
            UPDATE final_result
            SET new_safety_qty = 0,
                new_planning_cycle = ?,
                new_delivery_cycle = ?,
                new_delivery_days = ?,
                new_target_coverage = ?,
                new_supply_source = 2,
                new_abc_indicator = ?,
                new_smoothing = 0,
                new_forecast_model = 'G',
                new_historical_periods = 3,
                new_forecast_periods = 5,
                new_periods_per_season = 52
            WHERE rowid = ?
        """, (
            r["wc_p"] or "", r["wc_d"] or "",
            delivery_days, target_coverage, abc,
            r["rid"]
        ))
        total += 1

    db.commit()
    return total


def _calculate_nd_to_rf_params(db):
    """移植自 MDB 'Vendor: ND to RF (update)' 及 'Warehouse: ND to RF (update)' 查詢
    
    ND→RF 時依 supply_source 分兩路計算：
    
    Vendor (Supply Source=1):
    - new_rp_type = 'RF' if Article starts with '1', else 'ND'
    - new_safety_qty = 依 ABC 等級取 A/B/C QTY
    - new_planning_cycle = vendor_schedule.planning_s
    - new_delivery_cycle = vendor_schedule.delivery_s
    - new_delivery_days = lead_time
    - new_target_coverage = Round(lead_time, 0) for A, lead_time for B/C
    - new_supply_source = article_master.supplu_source
    
    Warehouse (Supply Source=2):
    - new_rp_type = 'RF' if Article starts with '1', else 'ND'  
    - new_delivery_days = 3
    - new_target_coverage = 3
    - new_supply_source = 2
    
    共用：
    - new_abc_indicator = 從 SKU_3M_SALES_F4 更新或保留
    - new_forecast_model = 'G', periods = 3, 5, 52
    - A/B/C QTY 從 exemption_qty 或 mc_stock_ref 取得
    """
    total = 0

    rows = db.execute("""
        SELECT fr.rowid AS rid, fr.site, fr.article, fr.mc,
               fr.abc_indicator, fr.new_abc_indicator,
               wc.p AS wc_p, wc.d AS wc_d,
               sc.class AS shop_class, sc.coverage_a_items, sc.coverage_b_items, sc.coverage_c_items,
               am.supplu_source,
               vs.planning_s, vs.delivery_s, vs.lead_time,
               sf.abc_total,
               eq.a_a, eq.a_b, eq.a_c, eq.b_a, eq.b_b, eq.b_c, eq.c_a, eq.c_b, eq.c_c,
               msr.a_qty AS msr_a, msr.b_qty AS msr_b, msr.c_qty AS msr_c
        FROM final_result fr
        LEFT JOIN warehouse_calendar wc ON fr.site = wc.shop
        LEFT JOIN shop_class sc ON fr.site = sc.shop
        LEFT JOIN article_master am ON fr.article = am.article
        LEFT JOIN vendor_schedule vs ON fr.site = vs.shop AND am.major_vendor_sap = vs.vendor
        LEFT JOIN sku_3m_sales_f4 sf ON fr.article = sf.sku AND fr.site = sf.location_code
        LEFT JOIN exemption_qty eq ON fr.article = eq.sku
        LEFT JOIN mc_stock_ref msr ON fr.site = msr.shop AND fr.mc = msr.mc
        WHERE fr.rp_type = 'ND' AND fr.new_rp_type = 'RF'
    """).fetchall()

    for r in rows:
        article_str = str(r["article"] or "")
        supplu_source = r["supplu_source"] if r["supplu_source"] is not None else 2

        new_rp_type = "RF" if article_str.startswith("1") else "ND"
        new_supply_source = 2 if new_rp_type == "ND" else supplu_source

        abc_indicator = (r["abc_indicator"] or "").strip()
        if not abc_indicator or abc_indicator == " ":
            new_abc = "C"
        else:
            abc_total = (r["abc_total"] or "").strip() if r["abc_total"] else None
            if abc_total and abc_total != abc_indicator:
                new_abc = abc_total
            else:
                new_abc = abc_indicator

        is_warehouse = (new_supply_source == 2)

        if is_warehouse:
            new_planning_cycle = r["wc_p"] or ""
            new_delivery_cycle = r["wc_d"] or ""
            new_delivery_days = 3
            new_target_coverage = 3
        else:
            if new_rp_type == "ND":
                new_planning_cycle = r["wc_p"] or ""
                new_delivery_cycle = r["wc_d"] or ""
            else:
                new_planning_cycle = r["planning_s"] or ""
                new_delivery_cycle = r["delivery_s"] or ""
            lead_time = r["lead_time"] if r["lead_time"] else 0
            new_delivery_days = lead_time
            if new_abc == "A":
                new_target_coverage = round(lead_time)
            else:
                new_target_coverage = lead_time

        shop_class = (r["shop_class"] or "").strip()
        if r["a_a"] is not None:
            if shop_class == "A":
                item_a = r["a_a"]
                item_b = r["a_b"]
                item_c = r["a_c"]
            elif shop_class == "B":
                item_a = r["b_a"]
                item_b = r["b_b"]
                item_c = r["b_c"]
            else:
                item_a = r["c_a"]
                item_b = r["c_b"]
                item_c = r["c_c"]
        else:
            item_a = r["msr_a"] or 0
            item_b = r["msr_b"] or 0
            item_c = r["msr_c"] or 0

        if new_rp_type == "ND":
            new_safety_qty = 0
        elif new_abc == "A":
            new_safety_qty = item_a
        elif new_abc == "B":
            new_safety_qty = item_b
        else:
            new_safety_qty = item_c

        db.execute("""
            UPDATE final_result
            SET new_safety_qty = ?,
                new_rp_type = ?,
                new_planning_cycle = ?,
                new_delivery_cycle = ?,
                new_delivery_days = ?,
                new_target_coverage = ?,
                new_supply_source = ?,
                new_abc_indicator = ?,
                new_smoothing = 0,
                new_forecast_model = 'G',
                new_historical_periods = 3,
                new_forecast_periods = 5,
                new_periods_per_season = 52,
                a_qty = ?,
                b_qty = ?,
                c_qty = ?
            WHERE rowid = ?
        """, (
            new_safety_qty, new_rp_type,
            new_planning_cycle, new_delivery_cycle,
            new_delivery_days, new_target_coverage,
            new_supply_source, new_abc,
            item_a, item_b, item_c,
            r["rid"]
        ))
        total += 1

    db.commit()
    return total


def run_step1_clear_all():
    """移植自 MDB Step 1 巨集 'Clear Import File - Step 1'
    
    清除所有資料表，準備重新匯入。
    """
    db = get_db()

    results = {}
    results["article_master"] = db.execute("DELETE FROM article_master").rowcount
    results["nd_to_rf"] = db.execute("DELETE FROM nd_to_rf").rowcount
    results["rf_to_nd"] = db.execute("DELETE FROM rf_to_nd").rowcount
    results["problem_transactions"] = db.execute("DELETE FROM problem_transactions").rowcount
    results["final_result"] = db.execute("DELETE FROM final_result").rowcount
    results["rp_list"] = db.execute("DELETE FROM rp_list").rowcount
    results["mss_list"] = db.execute("DELETE FROM mss_list").rowcount

    db.commit()
    return {
        "step": "Step 1: 清除全部資料",
        "detail": results,
    }


def run_step2_generate_result():
    """移植自 MDB Step 2 巨集 'Generate Result - Step 2'
    
    依序執行：
    1. RF→ND 轉換參數計算
    2. ND→RF 轉換參數計算（Vendor + Warehouse）
    3. 問題交易檢查
    4. 記錄類型變更
    """
    db = get_db()

    rf_to_nd_count = _calculate_rf_to_nd_params(db)
    nd_to_rf_count = _calculate_nd_to_rf_params(db)

    nd_to_rf_logged = 0
    rf_to_nd_logged = 0

    existing_nd_to_rf = db.execute("""
        SELECT COUNT(*) as c FROM nd_to_rf
    """).fetchone()["c"]

    if existing_nd_to_rf == 0:
        cur = db.execute("""
            INSERT INTO nd_to_rf
            SELECT NULL, site, article, article_description, brand, mc, mc_description,
                   article_category, article_type, status, first_sales_date,
                   season_category, available_to, launch_date,
                   sales_qty, sales_price, avg_weekly_sales, cal_stock_turnover, stock_on_hand,
                   safety_stock, purchase_group, rp_type, planning_cycle, delivery_cycle,
                   stock_planner, reorder_point, delivery_days, target_coverage,
                   supply_source, abc_indicator, smooth_promotion, forecast_model,
                   historical_periods, forecast_periods, periods_per_season,
                   current_consumption_qty,
                   week1_forecast, week2_forecast, week3_forecast, week4_forecast, week5_forecast,
                   new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
                   new_delivery_cycle, new_stock_planner, new_reorder_point,
                   new_delivery_days, new_target_coverage, new_supply_source,
                   new_abc_indicator, new_smoothing, new_forecast_model,
                   new_historical_periods, new_forecast_periods, new_periods_per_season,
                   new_current_consumption_qty,
                   new_week1_forecast, new_week2_forecast, new_week3_forecast,
                   new_week4_forecast, new_week5_forecast,
                   datetime('now')
            FROM final_result
            WHERE rp_type = 'ND' AND new_rp_type = 'RF'
        """)
        nd_to_rf_logged = cur.rowcount

    existing_rf_to_nd = db.execute("""
        SELECT COUNT(*) as c FROM rf_to_nd
    """).fetchone()["c"]

    if existing_rf_to_nd == 0:
        cur = db.execute("""
            INSERT INTO rf_to_nd
            SELECT NULL, site, article, article_description, brand, mc, mc_description,
                   article_category, article_type, status, first_sales_date,
                   season_category, available_to, launch_date,
                   sales_qty, sales_price, avg_weekly_sales, cal_stock_turnover, stock_on_hand,
                   safety_stock, purchase_group, rp_type, planning_cycle, delivery_cycle,
                   stock_planner, reorder_point, delivery_days, target_coverage,
                   supply_source, abc_indicator, smooth_promotion, forecast_model,
                   historical_periods, forecast_periods, periods_per_season,
                   current_consumption_qty,
                   week1_forecast, week2_forecast, week3_forecast, week4_forecast, week5_forecast,
                   new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
                   new_delivery_cycle, new_stock_planner, new_reorder_point,
                   new_delivery_days, new_target_coverage, new_supply_source,
                   new_abc_indicator, new_smoothing, new_forecast_model,
                   new_historical_periods, new_forecast_periods, new_periods_per_season,
                   new_current_consumption_qty,
                   new_week1_forecast, new_week2_forecast, new_week3_forecast,
                   new_week4_forecast, new_week5_forecast,
                   datetime('now')
            FROM final_result
            WHERE rp_type = 'RF' AND new_rp_type = 'ND'
        """)
        rf_to_nd_logged = cur.rowcount

    db.commit()

    return {
        "step": "Step 2: 產生計算結果",
        "detail": {
            "rf_to_nd_params_updated": rf_to_nd_count,
            "nd_to_rf_params_updated": nd_to_rf_count,
            "nd_to_rf_logged": nd_to_rf_logged,
            "rf_to_nd_logged": rf_to_nd_logged,
        }
    }


def run_step3_apply_ideal_stock():
    """移植自 MDB Step 3 巨集 'Generate Result - Step 3' + 'Final Result 2' 查詢
    
    套用 ideal stock 覆蓋 new_safety_qty，
    只對 Shop_Class 中存在的 site 生效。
    """
    return apply_ideal_stock()


def run_full_workflow():
    """執行完整三步驟工作流程"""
    step1 = run_step1_clear_all()
    step2 = run_step2_generate_result()
    step3 = run_step3_apply_ideal_stock()
    return {
        "step1": step1,
        "step2": step2,
        "step3": step3,
    }


def generate_rp_list():
    """移植自 MDB RP_List 查詢邏輯
    
    從 final_result 中篩選 new_rp_type 有值的記錄輸出為 RP 清單。
    """
    db = get_db()
    db.execute("DELETE FROM rp_list")

    cur = db.execute("""
        INSERT INTO rp_list
        SELECT NULL, site, article, article_description, brand, mc, mc_description,
               article_category, article_type, status, first_sales_date,
               season_category, available_to, launch_date,
               sales_qty, sales_price, avg_weekly_sales, cal_stock_turnover, stock_on_hand,
               safety_stock, purchase_group, rp_type, planning_cycle, delivery_cycle,
               stock_planner, reorder_point, delivery_days, target_coverage,
               supply_source, abc_indicator, smooth_promotion, forecast_model,
               historical_periods, forecast_periods, periods_per_season,
               current_consumption_qty,
               week1_forecast, week2_forecast, week3_forecast,
               week4_forecast, week5_forecast,
               new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
               new_delivery_cycle, new_stock_planner, new_reorder_point,
               new_delivery_days, new_target_coverage, new_supply_source,
               new_abc_indicator, new_smoothing, new_forecast_model,
               new_historical_periods, new_forecast_periods, new_periods_per_season,
               new_current_consumption_qty,
               new_week1_forecast, new_week2_forecast, new_week3_forecast,
               new_week4_forecast, new_week5_forecast,
               a_qty, b_qty, c_qty, datetime('now')
        FROM final_result
        WHERE new_rp_type IS NOT NULL AND new_rp_type != ''
    """)

    db.commit()
    return {"generated": cur.rowcount}


def generate_mss_list():
    """移植自 Access MSS 清單邏輯
    
    從 final_result 輸出完整的 MSS 清單。
    """
    db = get_db()
    db.execute("DELETE FROM mss_list")

    cur = db.execute("""
        INSERT INTO mss_list
        SELECT NULL, site, article, article_description, brand, mc, mc_description,
               article_category, article_type, status, first_sales_date,
               season_category, available_to, launch_date,
               sales_qty, sales_price, avg_weekly_sales, cal_stock_turnover, stock_on_hand,
               safety_stock, purchase_group, rp_type, planning_cycle, delivery_cycle,
               stock_planner, reorder_point, delivery_days, target_coverage,
               supply_source, abc_indicator, smooth_promotion, forecast_model,
               historical_periods, forecast_periods, periods_per_season,
               current_consumption_qty,
               week1_forecast, week2_forecast, week3_forecast,
               week4_forecast, week5_forecast,
               new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
               new_delivery_cycle, new_stock_planner, new_reorder_point,
               new_delivery_days, new_target_coverage, new_supply_source,
               new_abc_indicator, new_smoothing, new_forecast_model,
               new_historical_periods, new_forecast_periods, new_periods_per_season,
               new_current_consumption_qty,
               new_week1_forecast, new_week2_forecast, new_week3_forecast,
               new_week4_forecast, new_week5_forecast,
               a_qty, b_qty, c_qty, datetime('now')
        FROM final_result
    """)

    db.commit()
    return {"generated": cur.rowcount}


def clear_all():
    """清除所有輸出並重設計算標記"""
    db = get_db()
    db.execute("DELETE FROM rp_list")
    db.execute("DELETE FROM mss_list")
    db.execute("DELETE FROM nd_to_rf")
    db.execute("DELETE FROM rf_to_nd")
    db.execute("DELETE FROM problem_transactions")
    db.execute("UPDATE final_result SET moq_checked = 0, ideal_stock_applied = 0")
    db.commit()
    return {"cleared": True}


def get_dashboard_stats():
    """取得儀表板統計資料"""
    db = get_db()

    stats = {}
    stats["total_articles"] = db.execute(
        "SELECT COUNT(*) as c FROM final_result"
    ).fetchone()["c"]

    stats["by_rp_type"] = [
        dict(r) for r in db.execute(
            "SELECT rp_type, COUNT(*) as c FROM final_result GROUP BY rp_type"
        ).fetchall()
    ]

    stats["by_new_rp_type"] = [
        dict(r) for r in db.execute(
            "SELECT new_rp_type, COUNT(*) as c FROM final_result WHERE new_rp_type IS NOT NULL AND new_rp_type != '' GROUP BY new_rp_type"
        ).fetchall()
    ]

    stats["problem_count"] = db.execute(
        "SELECT COUNT(*) as c FROM problem_transactions"
    ).fetchone()["c"]

    stats["moq_checked"] = db.execute(
        "SELECT COUNT(*) as c FROM final_result WHERE moq_checked = 1"
    ).fetchone()["c"]

    stats["ideal_stock_applied"] = db.execute(
        "SELECT COUNT(*) as c FROM final_result WHERE ideal_stock_applied = 1"
    ).fetchone()["c"]

    stats["shop_count"] = db.execute(
        "SELECT COUNT(*) as c FROM shop_class"
    ).fetchone()["c"]

    return stats
