from database import get_db

def run_check_moq():
    """Ported from Access Check MOQ query"""
    db = get_db()
    cur = db.execute("""
        UPDATE final_result
        SET new_safety_qty = CASE
            WHEN new_rp_type = 'ND' THEN 0
            WHEN d001_moq.moq IS NULL THEN COALESCE(final_result.new_safety_qty, 0)
            WHEN CAST(d001_moq.moq AS INTEGER) > COALESCE(final_result.new_safety_qty, 0)
                THEN CAST(d001_moq.moq AS INTEGER)
            ELSE COALESCE(final_result.new_safety_qty, 0)
        END,
        moq_checked = 1
        FROM d001_moq
        WHERE final_result.article = d001_moq.sku
    """)
    db.execute("UPDATE final_result SET moq_checked = 1 WHERE moq_checked = 0")
    db.commit()
    return {"updated": cur.rowcount}

def apply_ideal_stock():
    """Ported from Access Final Result 2 query - overrides with ideal stock"""
    db = get_db()
    cur = db.execute("""
        UPDATE final_result
        SET new_safety_qty = CAST(ideal_stock.ideal_stock AS INTEGER),
            ideal_stock_applied = 1
        FROM ideal_stock
        INNER JOIN shop_class ON final_result.site = shop_class.shop
        WHERE final_result.article = ideal_stock.article
          AND final_result.site = ideal_stock.site
          AND CAST(final_result.new_safety_qty AS INTEGER) != CAST(ideal_stock.ideal_stock AS INTEGER)
    """)
    db.execute("UPDATE final_result SET ideal_stock_applied = 1 WHERE ideal_stock_applied = 0")
    db.commit()
    return {"updated": cur.rowcount}

def find_problem_transactions():
    """Ported from Access Problem Transaction query"""
    db = get_db()
    db.execute("DELETE FROM problem_transactions")
    db.execute("""
        INSERT INTO problem_transactions (site, article, article_description, mc, mc_description, reason, field_name, field_value)
        SELECT site, article, article_description, mc, mc_description,
               'Negative safety stock', 'new_safety_qty', CAST(new_safety_qty AS TEXT)
        FROM final_result WHERE CAST(new_safety_qty AS INTEGER) < 0
    """)
    db.execute("""
        INSERT INTO problem_transactions (site, article, article_description, mc, mc_description, reason, field_name, field_value)
        SELECT site, article, article_description, mc, mc_description,
               'Missing RP type', 'new_rp_type', COALESCE(new_rp_type, 'NULL')
        FROM final_result WHERE new_rp_type IS NULL OR new_rp_type = ''
    """)
    db.execute("""
        INSERT INTO problem_transactions (site, article, article_description, mc, mc_description, reason, field_name, field_value)
        SELECT site, article, article_description, mc, mc_description,
               'Article not in master', 'article', article
        FROM final_result fr
        WHERE NOT EXISTS (SELECT 1 FROM article_master am WHERE am.article = fr.article)
    """)
    db.commit()
    count = db.execute("SELECT COUNT(*) as c FROM problem_transactions").fetchone()["c"]
    return {"problem_count": count}

def process_type_conversions():
    """Ported from Access ND/RF conversion queries"""
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
               new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
               new_delivery_cycle, new_stock_planner, new_reorder_point,
               new_delivery_days, new_target_coverage, new_supply_source,
               new_abc_indicator, new_smoothing, new_forecast_model,
               new_historical_periods, new_forecast_periods, new_periods_per_season,
               datetime('now')
        FROM final_result
        WHERE rp_type = 'ND' AND new_rp_type = 'RF'
    """)
    
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
               new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
               new_delivery_cycle, new_stock_planner, new_reorder_point,
               new_delivery_days, new_target_coverage, new_supply_source,
               new_abc_indicator, new_smoothing, new_forecast_model,
               new_historical_periods, new_forecast_periods, new_periods_per_season,
               datetime('now')
        FROM final_result
        WHERE rp_type = 'RF' AND new_rp_type = 'ND'
    """)
    db.commit()
    return {"nd_to_rf": nd_to_rf.rowcount, "rf_to_nd": rf_to_nd.rowcount}

def generate_rp_list():
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
               current_consumption_qty, week1_forecast, week2_forecast, week3_forecast,
               week4_forecast, week5_forecast,
               new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
               new_delivery_cycle, new_stock_planner, new_reorder_point,
               new_delivery_days, new_target_coverage, new_supply_source,
               new_abc_indicator, new_smoothing, new_forecast_model,
               new_historical_periods, new_forecast_periods, new_periods_per_season,
               new_current_consumption_qty, new_week1_forecast, new_week2_forecast,
               new_week3_forecast, new_week4_forecast, new_week5_forecast,
               a_qty, b_qty, c_qty, datetime('now')
        FROM final_result
        WHERE new_rp_type IS NOT NULL AND new_rp_type != ''
    """)
    db.commit()
    return {"generated": cur.rowcount}

def generate_mss_list():
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
               current_consumption_qty, week1_forecast, week2_forecast, week3_forecast,
               week4_forecast, week5_forecast,
               new_safety_qty, new_purchase_group, new_rp_type, new_planning_cycle,
               new_delivery_cycle, new_stock_planner, new_reorder_point,
               new_delivery_days, new_target_coverage, new_supply_source,
               new_abc_indicator, new_smoothing, new_forecast_model,
               new_historical_periods, new_forecast_periods, new_periods_per_season,
               new_current_consumption_qty, new_week1_forecast, new_week2_forecast,
               new_week3_forecast, new_week4_forecast, new_week5_forecast,
               a_qty, b_qty, c_qty, datetime('now')
        FROM final_result
    """)
    db.commit()
    return {"generated": cur.rowcount}

def clear_all():
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
    db = get_db()
    stats = {}
    stats["total_articles"] = db.execute("SELECT COUNT(*) as c FROM final_result").fetchone()["c"]
    stats["by_rp_type"] = [dict(r) for r in db.execute("SELECT rp_type, COUNT(*) as c FROM final_result GROUP BY rp_type").fetchall()]
    stats["by_new_rp_type"] = [dict(r) for r in db.execute("SELECT new_rp_type, COUNT(*) as c FROM final_result WHERE new_rp_type IS NOT NULL AND new_rp_type != '' GROUP BY new_rp_type").fetchall()]
    stats["problem_count"] = db.execute("SELECT COUNT(*) as c FROM problem_transactions").fetchone()["c"]
    stats["moq_checked"] = db.execute("SELECT COUNT(*) as c FROM final_result WHERE moq_checked = 1").fetchone()["c"]
    stats["ideal_stock_applied"] = db.execute("SELECT COUNT(*) as c FROM final_result WHERE ideal_stock_applied = 1").fetchone()["c"]
    stats["shop_count"] = db.execute("SELECT COUNT(*) as c FROM shop_class").fetchone()["c"]
    return stats

