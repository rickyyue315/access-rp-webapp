"""Export MDB tables to CSV and import into Flask SQLite database.

Usage:
    python tools/export_mdb_to_csv.py               # export CSV only
    python tools/export_mdb_to_csv.py --import-db    # export CSV + load DB
    python tools/export_mdb_to_csv.py --skip-csv     # load existing CSV to DB
"""

import os, sys, csv
sys.stdout.reconfigure(encoding='utf-8')

# Use working directory (the Flask project root) to locate assets
PROJECT = os.getcwd()
CSV_DIR = os.path.join(PROJECT, 'data', 'csv_exports')
MDB_DIR = os.path.normpath(os.path.join(PROJECT, '..'))
MDB_FILE = [f for f in os.listdir(MDB_DIR) if f.lower().endswith('.mdb')]
MDB = os.path.join(MDB_DIR, MDB_FILE[0]) if MDB_FILE else ''

sys.path.insert(0, PROJECT)
from database import get_db

MAP = {}

def reg(mdb_name, table, key, cols):
    MAP[mdb_name] = [table, key, cols]

reg('Article Master', 'article_master', 'Article Number', {
    'Article Number': 'article', 'Article Description': 'article_description',
    'Brand': 'brand', 'Merchandise Category': 'mc',
    'Merchandise Category _(For reference)': 'mc_description',
    'Article Category': 'article_category', 'Article Type': 'article_type',
    'Status': 'status', 'First Sales Dat': 'first_sales_date',
    'Season Category': 'season_category', 'Available to': 'available_to',
    'Launch Date': 'launch_date', 'Major Vendor(SAP)': 'major_vendor_sap',
    'Supplu Source': 'supplu_source',
})

reg('Final Result', 'final_result', 'Article', {
    'Site': 'site', 'Article': 'article', 'Article Description': 'article_description',
    'Brand': 'brand', 'MC': 'mc', 'MC Description': 'mc_description',
    'Article categor': 'article_category', 'Article Type': 'article_type',
    'Status': 'status', 'First Sales Dat': 'first_sales_date',
    'Season category': 'season_category', 'Available to': 'available_to',
    'Launch Date': 'launch_date',
    'Sales Qty 20000101 -  20061203': 'sales_qty', 'Sales Price': 'sales_price',
    'Avg Weekly Sales': 'avg_weekly_sales', 'Cal Stock Turnover': 'cal_stock_turnover',
    'Stock On Hand  20070827': 'stock_on_hand', 'Safety Stock': 'safety_stock',
    'Purchase Group': 'purchase_group', 'RP Type': 'rp_type',
    'Planning Cycle': 'planning_cycle', 'Delivery Cycle': 'delivery_cycle',
    'Stock Planner': 'stock_planner', 'Reorder Point': 'reorder_point',
    'Delivery Days': 'delivery_days', 'Target Coverage': 'target_coverage',
    'Supply Source (1=Vendor/2=DC)': 'supply_source', 'ABC Indicator': 'abc_indicator',
    'Smooth Promotion': 'smooth_promotion', 'Forecast Model': 'forecast_model',
    'Historical periods': 'historical_periods', 'Forecast periods': 'forecast_periods',
    'Periods per season': 'periods_per_season',
    'Current consumption qty': 'current_consumption_qty',
    'Week 1 forecast value': 'week1_forecast', 'Week 2 forecast value': 'week2_forecast',
    'Week 3 forecast value': 'week3_forecast', 'Week 4 forecast value': 'week4_forecast',
    'Week 5 forecast value': 'week5_forecast',
    'New Safety Qty': 'new_safety_qty', 'New Purchase Group': 'new_purchase_group',
    'New RP Typ': 'new_rp_type', 'New Planning Cycle': 'new_planning_cycle',
    'New Delivery Cycle': 'new_delivery_cycle', 'New Stock Planner': 'new_stock_planner',
    'New Reorder Point': 'new_reorder_point', 'New Delivery Days': 'new_delivery_days',
    'New Traget Coverage': 'new_target_coverage', 'New Supply Source': 'new_supply_source',
    'New ABC Indicator': 'new_abc_indicator', 'New Smoothing (0/1)': 'new_smoothing',
    'New Forecast Model': 'new_forecast_model',
    'New Historical perio': 'new_historical_periods',
    'New Forecast periods': 'new_forecast_periods',
    'New Periods per season': 'new_periods_per_season',
    'New Current consumption qty': 'new_current_consumption_qty',
    'New Week 1 forecast value': 'new_week1_forecast',
    'New Week 2 forecast value': 'new_week2_forecast',
    'New Week 3 forecast value': 'new_week3_forecast',
    'New Week 4 forecast value': 'new_week4_forecast',
    'New Week 5 forecast value': 'new_week5_forecast',
    'A QTY': 'a_qty', 'B QTY': 'b_qty', 'C QTY': 'c_qty',
})

reg('D001 MOQ', 'd001_moq', 'SKU', {'SKU': 'sku', 'MOQ': 'moq'})
reg('Exemption Qty', 'exemption_qty', 'SKU', {
    'SKU': 'sku', 'A_A': 'a_a', 'A_B': 'a_b', 'A_C': 'a_c',
    'B_A': 'b_a', 'B_B': 'b_b', 'B_C': 'b_c',
    'C_A': 'c_a', 'C_B': 'c_b', 'C_C': 'c_c',
})
reg('Shop_Class', 'shop_class', 'Shop', {
    'Shop': 'shop', 'Class': 'class', 'Status': 'status',
    'Coverage - A Items': 'coverage_a_items',
    'Coverage - B Items': 'coverage_b_items',
    'Coverage - C Items': 'coverage_c_items',
})
reg('Vendor Schedule', 'vendor_schedule', 'Shop', {
    'Shop': 'shop', 'Vendor': 'vendor',
    'Delivery S': 'delivery_s', 'Planning S': 'planning_s',
    'Lead Time': 'lead_time',
})
reg('Warehouse Calendar', 'warehouse_calendar', 'Shop', {
    'Shop': 'shop', 'P': 'p', 'D': 'd',
})
reg('MSS List', 'mc_stock_ref', 'Shop', {
    'Shop': 'shop', 'MC': 'mc', 'A': 'a_qty', 'B': 'b_qty', 'C': 'c_qty',
})
reg('ND to RF', 'nd_to_rf', 'Article', {
    'Site': 'site', 'Article': 'article', 'Article Description': 'article_description',
    'Brand': 'brand', 'MC': 'mc', 'MC Description': 'mc_description',
    'Article categor': 'article_category', 'Article Type': 'article_type',
    'Status': 'status', 'First Sales Dat': 'first_sales_date',
    'Season category': 'season_category', 'Available to': 'available_to',
    'Launch Date': 'launch_date',
    'Sales Qty 20000101 -  20061203': 'sales_qty', 'Sales Price': 'sales_price',
    'Avg Weekly Sales': 'avg_weekly_sales', 'Cal Stock Turnover': 'cal_stock_turnover',
    'Stock On Hand  20070827': 'stock_on_hand', 'Safety Stock': 'safety_stock',
    'Purchase Group': 'purchase_group', 'RP Type': 'rp_type',
    'Planning Cycle': 'planning_cycle', 'Delivery Cycle': 'delivery_cycle',
    'Stock Planner': 'stock_planner', 'Reorder Point': 'reorder_point',
    'Delivery Days': 'delivery_days', 'Target Coverage': 'target_coverage',
    'Supply Source (1=Vendor/2=DC)': 'supply_source', 'ABC Indicator': 'abc_indicator',
    'Smooth Promotion': 'smooth_promotion', 'Forecast Model': 'forecast_model',
    'Historical periods': 'historical_periods', 'Forecast periods': 'forecast_periods',
    'Periods per season': 'periods_per_season',
    'New Safety Qty': 'new_safety_qty', 'New Purchase Group': 'new_purchase_group',
    'New RP Typ': 'new_rp_type', 'New Planning Cycle': 'new_planning_cycle',
    'New Delivery Cycle': 'new_delivery_cycle', 'New Stock Planner': 'new_stock_planner',
    'New Reorder Point': 'new_reorder_point', 'New Delivery Days': 'new_delivery_days',
    'New Traget Coverage': 'new_target_coverage', 'New Supply Source': 'new_supply_source',
    'New ABC Indicator': 'new_abc_indicator', 'New Smoothing (0/1)': 'new_smoothing',
    'New Forecast Model': 'new_forecast_model',
    'New Historical perio': 'new_historical_periods',
    'New Forecast periods': 'new_forecast_periods',
    'New Periods per season': 'new_periods_per_season',
})
reg('RP_List', 'rp_list', 'Article', {
    'Site': 'site', 'Article': 'article', 'Article Description': 'article_description',
    'Brand': 'brand', 'MC': 'mc', 'MC Description': 'mc_description',
    'Article categor': 'article_category', 'Article Type': 'article_type',
    'Status': 'status', 'First Sales Dat': 'first_sales_date',
    'Season category': 'season_category', 'Available to': 'available_to',
    'Launch Date': 'launch_date',
    'Sales Qty# 20000101 -  20091009': 'sales_qty', 'Sales Price': 'sales_price',
    'Avg# Weekly Sales': 'avg_weekly_sales', 'Cal# Stock Turnover': 'cal_stock_turnover',
    'Stock On Hand  20130812': 'stock_on_hand', 'Safety Stock': 'safety_stock',
    'Purchase Group': 'purchase_group', 'RP Type': 'rp_type',
    'Planning Cycle': 'planning_cycle', 'Delivery Cycle': 'delivery_cycle',
    'Stock Planner': 'stock_planner', 'Reorder Point': 'reorder_point',
    'Delivery Days': 'delivery_days', 'Target Coverage': 'target_coverage',
    'Supply Source (1=Vendor/2=DC)': 'supply_source', 'ABC Indicator': 'abc_indicator',
    'Smooth Promotion': 'smooth_promotion', 'Forecast Model': 'forecast_model',
    'Historical periods': 'historical_periods', 'Forecast periods': 'forecast_periods',
    'Periods per season': 'periods_per_season',
    'Current consumption qty': 'current_consumption_qty',
    'Week 1 forecast value': 'week1_forecast', 'Week 2 forecast value': 'week2_forecast',
    'Week 3 forecast value': 'week3_forecast', 'Week 4 forecast value': 'week4_forecast',
    'Week 5 forecast value': 'week5_forecast',
    'New Safety Qty': 'new_safety_qty', 'New Purchase Group': 'new_purchase_group',
    'New RP Typ': 'new_rp_type', 'New Planning Cycle': 'new_planning_cycle',
    'New Delivery Cycle': 'new_delivery_cycle', 'New Stock Planner': 'new_stock_planner',
    'New Reorder Point': 'new_reorder_point', 'New Delivery Days': 'new_delivery_days',
    'New Traget Coverage': 'new_target_coverage', 'New Supply Source': 'new_supply_source',
    'New ABC Indicator': 'new_abc_indicator', 'New Smoothing (0/1)': 'new_smoothing',
    'New Forecast Model': 'new_forecast_model',
    'New Historical perio': 'new_historical_periods',
    'New Forecast periods': 'new_forecast_periods',
    'New Periods per season': 'new_periods_per_season',
    'New consumption qty': 'new_current_consumption_qty',
    'New Week 1 forecast': 'new_week1_forecast',
    'New Week 2 forecast': 'new_week2_forecast',
    'New Week 3 forecast': 'new_week3_forecast',
    'New Week 4 forecast': 'new_week4_forecast',
    'New Week 5 forecast': 'new_week5_forecast',
})

SKIP_TABLES = {'\u8cbc\u4e0a\u932f\u8aa4', 'Paste Errors',
               'MSS_List_\u532f\u51fa\u932f\u8aa4', 'RF to ND', 'Problem Transactions'}


def export_all():
    import pyodbc
    conn = pyodbc.connect(f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={MDB};")
    all_tables = [t.table_name for t in conn.cursor().tables()
                  if t.table_type == 'TABLE' and not t.table_name.startswith('MSys')
                  and not t.table_name.startswith('~')]
    total = 0
    for t in all_tables:
        if t in SKIP_TABLES:
            print(f'  {t}: skip')
            continue
        safe = t.replace(' ', '_').replace('#', '').replace('(', '').replace(')', '')
        csv_path = os.path.join(CSV_DIR, safe + '.csv')
        rows = conn.execute(f'SELECT * FROM [{t}]').fetchall()
        if not rows:
            print(f'  {t}: 0 rows, skip')
            continue
        cols = [c.column_name for c in conn.cursor().columns(table=t)]
        os.makedirs(CSV_DIR, exist_ok=True)
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow([str(v) if v is not None else '' for v in r])
        print(f'  {t} -> {csv_path} ({len(rows)} rows)')
        total += len(rows)
    conn.close()
    print(f'\nTotal exported: {total} rows')
    return total


def import_all():
    db = get_db()
    db.execute('PRAGMA foreign_keys=OFF')
    total = 0
    for mdb_name, (table, key_field, col_map) in MAP.items():
        safe = mdb_name.replace(' ', '_').replace('#', '').replace('(', '').replace(')', '')
        csv_path = os.path.join(CSV_DIR, safe + '.csv')
        if not os.path.exists(csv_path):
            print(f'  [skip] CSV not found: {csv_path}')
            continue
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            stripped = [c.strip() for c in reader.fieldnames]
            reader.fieldnames = stripped
            mapping = {}
            for mdb_col, db_col in col_map.items():
                found = next((c for c in stripped if c.lower() == mdb_col.lower()), None)
                if found:
                    mapping[found] = db_col
            if not mapping:
                print(f'  [warn] No columns matched for {table}')
                continue
            keys = list(mapping.values())
            sql = f"INSERT OR REPLACE INTO {table} ({','.join(keys)}) VALUES ({','.join(['?']*len(keys))})"
            count = 0
            for row in reader:
                if key_field and not (row.get(key_field) or '').strip():
                    continue
                vals = [row.get(c) for c in mapping]
                try:
                    db.execute(sql, vals)
                    count += 1
                except Exception:
                    pass
                if count % 500 == 0:
                    db.commit()
            db.commit()
        print(f'  {table}: {count} rows')
        total += count
    db.execute('PRAGMA foreign_keys=ON')
    print(f'\nTotal imported: {total} rows into SQLite')


def verify():
    db = get_db()
    tables = ['article_master','final_result','d001_moq','exemption_qty',
              'shop_class','vendor_schedule','warehouse_calendar','mc_stock_ref',
              'nd_to_rf','rp_list','problem_transactions','mss_list']
    print('\nDatabase verification:')
    for t in tables:
        try:
            c = db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
            print(f'  {t}: {c} rows')
        except Exception as e:
            print(f'  {t}: ERROR - {e}')


def main():
    import argparse
    p = argparse.ArgumentParser(description='Export MDB tables to CSV and import into SQLite')
    p.add_argument('--import-db', action='store_true', help='export CSV then load into SQLite')
    p.add_argument('--skip-csv', action='store_true', help='skip CSV export, load from existing CSV')
    p.add_argument('--clear', action='store_true', help='clear existing data before importing')
    p.add_argument('--verify', action='store_true', help='verify database row counts')
    args = p.parse_args()

    if args.clear:
        db = get_db()
        for _, (table, _, _) in MAP.items():
            db.execute(f'DELETE FROM {table}')
        db.commit()
        print(f'Cleared all {len(MAP)} tables')

    if not args.skip_csv:
        print('=== Step 1: Export MDB to CSV ===')
        export_all()
    else:
        print('=== Skip CSV export ===')

    if args.import_db or args.skip_csv:
        print('\n=== Step 2: Import CSV into SQLite ===')
        import_all()

    if args.verify or args.import_db:
        verify()

    print('\nDone!')
    if not args.import_db and not args.skip_csv:
        print('Tip: add --import-db to also load data into SQLite')
    print(f'CSV files: {CSV_DIR}')


if __name__ == '__main__':
    main()
