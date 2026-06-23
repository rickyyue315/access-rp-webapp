import sqlite3
import os

DB_PATH = os.environ.get('RP_DB_PATH',
    os.path.join(os.path.dirname(__file__), 'data', 'rp_database.db'))

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    init_schema(conn)
    return conn

def init_schema(conn):
    tables = [
        """CREATE TABLE IF NOT EXISTS article_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article TEXT NOT NULL, article_description TEXT, brand TEXT,
            mc TEXT, mc_description TEXT, article_category INTEGER,
            article_type TEXT, status TEXT, first_sales_date TEXT,
            season_category INTEGER, available_to TEXT, launch_date TEXT,
            major_vendor_sap TEXT, supplu_source INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS shop_class (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop TEXT NOT NULL, class TEXT NOT NULL, status TEXT DEFAULT 'M',
            coverage_a_items INTEGER DEFAULT 8, coverage_b_items INTEGER DEFAULT 5,
            coverage_c_items INTEGER DEFAULT 3
        )""",
        """CREATE TABLE IF NOT EXISTS vendor_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop TEXT NOT NULL, vendor TEXT NOT NULL,
            delivery_s TEXT, planning_s TEXT, lead_time INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS warehouse_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop TEXT NOT NULL, p TEXT, d TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS d001_moq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL, moq INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS exemption_qty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            a_a INTEGER DEFAULT 0, a_b INTEGER DEFAULT 0, a_c INTEGER DEFAULT 0,
            b_a INTEGER DEFAULT 0, b_b INTEGER DEFAULT 0, b_c INTEGER DEFAULT 0,
            c_a INTEGER DEFAULT 0, c_b INTEGER DEFAULT 0, c_c INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS ideal_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT NOT NULL, article TEXT NOT NULL, ideal_stock INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS sku_3m_sales_f4 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL, location_code TEXT NOT NULL,
            week1_forecast REAL DEFAULT 0, week2_forecast REAL DEFAULT 0,
            week3_forecast REAL DEFAULT 0, week4_forecast REAL DEFAULT 0,
            week5_forecast REAL DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS problem_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT, article TEXT, article_description TEXT,
            mc TEXT, mc_description TEXT, reason TEXT,
            field_name TEXT, field_value TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS final_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT NOT NULL, article TEXT NOT NULL,
            article_description TEXT, brand TEXT, mc TEXT, mc_description TEXT,
            article_category INTEGER, article_type TEXT, status TEXT,
            first_sales_date TEXT, season_category INTEGER,
            available_to TEXT, launch_date TEXT,
            sales_qty REAL DEFAULT 0, sales_price REAL DEFAULT 0,
            avg_weekly_sales REAL DEFAULT 0, cal_stock_turnover REAL DEFAULT 0,
            stock_on_hand REAL DEFAULT 0,
            safety_stock INTEGER DEFAULT 0, purchase_group INTEGER DEFAULT 0,
            rp_type TEXT DEFAULT 'RF', planning_cycle TEXT, delivery_cycle TEXT,
            stock_planner INTEGER DEFAULT 0, reorder_point INTEGER DEFAULT 0,
            delivery_days INTEGER DEFAULT 0, target_coverage INTEGER DEFAULT 0,
            supply_source INTEGER DEFAULT 1, abc_indicator TEXT DEFAULT 'C',
            smooth_promotion TEXT, forecast_model TEXT,
            historical_periods INTEGER DEFAULT 0, forecast_periods INTEGER DEFAULT 0,
            periods_per_season INTEGER DEFAULT 0,
            current_consumption_qty REAL DEFAULT 0,
            week1_forecast REAL DEFAULT 0, week2_forecast REAL DEFAULT 0,
            week3_forecast REAL DEFAULT 0, week4_forecast REAL DEFAULT 0,
            week5_forecast REAL DEFAULT 0,
            new_safety_qty INTEGER DEFAULT 0, new_purchase_group TEXT,
            new_rp_type TEXT, new_planning_cycle TEXT, new_delivery_cycle TEXT,
            new_stock_planner TEXT, new_reorder_point TEXT, new_delivery_days TEXT,
            new_target_coverage TEXT, new_supply_source TEXT, new_abc_indicator TEXT,
            new_smoothing TEXT, new_forecast_model TEXT,
            new_historical_periods TEXT, new_forecast_periods TEXT,
            new_periods_per_season TEXT, new_current_consumption_qty TEXT,
            new_week1_forecast TEXT, new_week2_forecast TEXT,
            new_week3_forecast TEXT, new_week4_forecast TEXT,
            new_week5_forecast TEXT,
            a_qty INTEGER DEFAULT 0, b_qty INTEGER DEFAULT 0, c_qty INTEGER DEFAULT 0,
            moq_checked INTEGER DEFAULT 0, ideal_stock_applied INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS nd_to_rf (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT NOT NULL, article TEXT NOT NULL,
            article_description TEXT, brand TEXT, mc TEXT, mc_description TEXT,
            article_category INTEGER, article_type TEXT, status TEXT,
            first_sales_date TEXT, season_category INTEGER,
            available_to TEXT, launch_date TEXT,
            sales_qty REAL DEFAULT 0, sales_price REAL DEFAULT 0,
            avg_weekly_sales REAL DEFAULT 0, cal_stock_turnover REAL DEFAULT 0,
            stock_on_hand REAL DEFAULT 0,
            safety_stock INTEGER DEFAULT 0, purchase_group INTEGER DEFAULT 0,
            rp_type TEXT, planning_cycle TEXT, delivery_cycle TEXT,
            stock_planner INTEGER DEFAULT 0, reorder_point INTEGER DEFAULT 0,
            delivery_days INTEGER DEFAULT 0, target_coverage INTEGER DEFAULT 0,
            supply_source INTEGER DEFAULT 1, abc_indicator TEXT,
            smooth_promotion TEXT, forecast_model TEXT,
            historical_periods INTEGER DEFAULT 0, forecast_periods INTEGER DEFAULT 0,
            periods_per_season INTEGER DEFAULT 0,
            new_safety_qty INTEGER DEFAULT 0, new_purchase_group TEXT,
            new_rp_type TEXT, new_planning_cycle TEXT, new_delivery_cycle TEXT,
            new_stock_planner TEXT, new_reorder_point TEXT,
            new_delivery_days TEXT, new_target_coverage TEXT,
            new_supply_source TEXT, new_abc_indicator TEXT,
            new_smoothing TEXT, new_forecast_model TEXT,
            new_historical_periods TEXT, new_forecast_periods TEXT,
            new_periods_per_season TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS rf_to_nd (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT NOT NULL, article TEXT NOT NULL,
            article_description TEXT, brand TEXT, mc TEXT, mc_description TEXT,
            article_category INTEGER, article_type TEXT, status TEXT,
            first_sales_date TEXT, season_category INTEGER,
            available_to TEXT, launch_date TEXT,
            sales_qty REAL DEFAULT 0, sales_price REAL DEFAULT 0,
            avg_weekly_sales REAL DEFAULT 0, cal_stock_turnover REAL DEFAULT 0,
            stock_on_hand REAL DEFAULT 0,
            safety_stock INTEGER DEFAULT 0, purchase_group INTEGER DEFAULT 0,
            rp_type TEXT, planning_cycle TEXT, delivery_cycle TEXT,
            stock_planner INTEGER DEFAULT 0, reorder_point INTEGER DEFAULT 0,
            delivery_days INTEGER DEFAULT 0, target_coverage INTEGER DEFAULT 0,
            supply_source INTEGER DEFAULT 1, abc_indicator TEXT,
            smooth_promotion TEXT, forecast_model TEXT,
            historical_periods INTEGER DEFAULT 0, forecast_periods INTEGER DEFAULT 0,
            periods_per_season INTEGER DEFAULT 0,
            new_safety_qty INTEGER DEFAULT 0, new_purchase_group TEXT,
            new_rp_type TEXT, new_planning_cycle TEXT, new_delivery_cycle TEXT,
            new_stock_planner TEXT, new_reorder_point TEXT,
            new_delivery_days TEXT, new_target_coverage TEXT,
            new_supply_source TEXT, new_abc_indicator TEXT,
            new_smoothing TEXT, new_forecast_model TEXT,
            new_historical_periods TEXT, new_forecast_periods TEXT,
            new_periods_per_season TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS rp_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT, article TEXT, article_description TEXT, brand TEXT,
            mc TEXT, mc_description TEXT, article_category INTEGER,
            article_type TEXT, status TEXT, first_sales_date TEXT,
            season_category INTEGER, available_to TEXT, launch_date TEXT,
            sales_qty REAL, sales_price REAL, avg_weekly_sales REAL,
            cal_stock_turnover REAL, stock_on_hand REAL,
            safety_stock INTEGER, purchase_group INTEGER,
            rp_type TEXT, planning_cycle TEXT, delivery_cycle TEXT,
            stock_planner INTEGER, reorder_point INTEGER,
            delivery_days INTEGER, target_coverage INTEGER,
            supply_source INTEGER, abc_indicator TEXT,
            smooth_promotion TEXT, forecast_model TEXT,
            historical_periods INTEGER, forecast_periods INTEGER,
            periods_per_season INTEGER,
            current_consumption_qty REAL,
            week1_forecast REAL, week2_forecast REAL, week3_forecast REAL,
            week4_forecast REAL, week5_forecast REAL,
            new_safety_qty INTEGER, new_purchase_group TEXT,
            new_rp_type TEXT, new_planning_cycle TEXT,
            new_delivery_cycle TEXT, new_stock_planner TEXT,
            new_reorder_point TEXT, new_delivery_days TEXT,
            new_target_coverage TEXT, new_supply_source TEXT,
            new_abc_indicator TEXT, new_smoothing TEXT,
            new_forecast_model TEXT, new_historical_periods TEXT,
            new_forecast_periods TEXT, new_periods_per_season TEXT,
            new_current_consumption_qty TEXT,
            new_week1_forecast TEXT, new_week2_forecast TEXT,
            new_week3_forecast TEXT, new_week4_forecast TEXT,
            new_week5_forecast TEXT,
            a_qty INTEGER, b_qty INTEGER, c_qty INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS mc_stock_ref (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop TEXT NOT NULL, mc INTEGER DEFAULT 0,
            a_qty INTEGER DEFAULT 0, b_qty INTEGER DEFAULT 0, c_qty INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS mss_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT, article TEXT, article_description TEXT, brand TEXT,
            mc TEXT, mc_description TEXT, article_category INTEGER,
            article_type TEXT, status TEXT, first_sales_date TEXT,
            season_category INTEGER, available_to TEXT, launch_date TEXT,
            sales_qty REAL, sales_price REAL, avg_weekly_sales REAL,
            cal_stock_turnover REAL, stock_on_hand REAL,
            safety_stock INTEGER, purchase_group INTEGER,
            rp_type TEXT, planning_cycle TEXT, delivery_cycle TEXT,
            stock_planner INTEGER, reorder_point INTEGER,
            delivery_days INTEGER, target_coverage INTEGER,
            supply_source INTEGER, abc_indicator TEXT,
            smooth_promotion TEXT, forecast_model TEXT,
            historical_periods INTEGER, forecast_periods INTEGER,
            periods_per_season INTEGER,
            current_consumption_qty REAL,
            week1_forecast REAL, week2_forecast REAL, week3_forecast REAL,
            week4_forecast REAL, week5_forecast REAL,
            new_safety_qty INTEGER, new_purchase_group TEXT,
            new_rp_type TEXT, new_planning_cycle TEXT,
            new_delivery_cycle TEXT, new_stock_planner TEXT,
            new_reorder_point TEXT, new_delivery_days TEXT,
            new_target_coverage TEXT, new_supply_source TEXT,
            new_abc_indicator TEXT, new_smoothing TEXT,
            new_forecast_model TEXT, new_historical_periods TEXT,
            new_forecast_periods TEXT, new_periods_per_season TEXT,
            new_current_consumption_qty TEXT,
            new_week1_forecast TEXT, new_week2_forecast TEXT,
            new_week3_forecast TEXT, new_week4_forecast TEXT,
            new_week5_forecast TEXT,
            a_qty INTEGER, b_qty INTEGER, c_qty INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    ]
    for sql in tables:
        conn.execute(sql)
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_am_article ON article_master(article)",
        "CREATE INDEX IF NOT EXISTS idx_sc_shop ON shop_class(shop)",
        "CREATE INDEX IF NOT EXISTS idx_moq_sku ON d001_moq(sku)",
        "CREATE INDEX IF NOT EXISTS idx_fr_site_article ON final_result(site, article)",
        "CREATE INDEX IF NOT EXISTS idx_is_site_article ON ideal_stock(site, article)",
        "CREATE INDEX IF NOT EXISTS idx_sf_sku_loc ON sku_3m_sales_f4(sku, location_code)",
        "CREATE INDEX IF NOT EXISTS idx_msr_shop_mc ON mc_stock_ref(shop, mc)",

    ]
    for idx in indexes:
        conn.execute(idx)

    migrations = [
        "ALTER TABLE article_master ADD COLUMN major_vendor_sap TEXT DEFAULT ''",
        "ALTER TABLE article_master ADD COLUMN supplu_source INTEGER DEFAULT 1",
        "ALTER TABLE final_result ADD COLUMN moq_checked INTEGER DEFAULT 0",
        "ALTER TABLE final_result ADD COLUMN ideal_stock_applied INTEGER DEFAULT 0",
    ]
    for m in migrations:
        try:
            conn.execute(m)
        except Exception:
            pass

    conn.commit()
    print("Database schema initialized")
