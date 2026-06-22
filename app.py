import os, csv, io, sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_file, Response
from database import get_db
from calculation_service import *

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    try:
        stats = get_dashboard_stats()
        return render_template('index.html', data=stats)
    except Exception as e:
        return render_template('index.html', error=str(e), data={})

@app.route('/articles')
def articles():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    search = request.args.get('search', '')
    db = get_db()
    if search:
        total = db.execute("SELECT COUNT(*) as c FROM article_master WHERE article LIKE ?", (f'%{search}%',)).fetchone()['c']
        rows = db.execute("SELECT * FROM article_master WHERE article LIKE ? ORDER BY article LIMIT ? OFFSET ?", (f'%{search}%', per_page, offset)).fetchall()
    else:
        total = db.execute("SELECT COUNT(*) as c FROM article_master").fetchone()['c']
        rows = db.execute("SELECT * FROM article_master ORDER BY article LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
    return render_template('articles.html', data={
        'articles': [dict(r) for r in rows],
        'page': page, 'total_pages': max(1, (total + per_page - 1) // per_page),
        'total': total, 'search': search
    })

@app.route('/articles/import', methods=['POST'])
def import_articles():
    file = request.files.get('file')
    if not file: return redirect(url_for('articles', error='No file'))
    path = os.path.join(app.config['UPLOAD_FOLDER'], 'articles_import.csv')
    file.save(path)
    db = get_db()
    count = 0
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.execute("""INSERT OR REPLACE INTO article_master (article, article_description, brand, mc, mc_description, article_category, article_type, status, first_sales_date, season_category, available_to, launch_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (row.get('article',''), row.get('article_description',''), row.get('brand',''), row.get('mc',''), row.get('mc_description',''),
                 row.get('article_category',0), row.get('article_type',''), row.get('status',''), row.get('first_sales_date',''),
                 row.get('season_category',0), row.get('available_to',''), row.get('launch_date','')))
            count += 1
    db.commit()
    return redirect(url_for('articles'))
@app.route('/final-result')
def final_result():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    site = request.args.get('site', '')
    article = request.args.get('article', '')
    rp_type = request.args.get('rp_type', '')
    filters = {'site': site, 'article': article, 'rp_type': rp_type}
    
    db = get_db()
    where = []
    params = []
    if site: where.append("fr.site LIKE ?"); params.append(f'%{site}%')
    if article: where.append("fr.article LIKE ?"); params.append(f'%{article}%')
    if rp_type: where.append("fr.rp_type = ?"); params.append(rp_type)
    w = " AND ".join(where) if where else "1=1"
    
    total = db.execute(f"SELECT COUNT(*) as c FROM final_result fr WHERE {w}", params).fetchone()['c']
    rows = db.execute(f"SELECT fr.* FROM final_result fr WHERE {w} ORDER BY fr.site, fr.article LIMIT ? OFFSET ?", params + [per_page, offset]).fetchall()
    return render_template('final_result.html', data={
        'rows': [dict(r) for r in rows],
        'page': page, 'total_pages': max(1, (total + per_page - 1) // per_page),
        'total_rows': total, 'filters': filters
    })

@app.route('/final-result/update/<int:rid>', methods=['POST'])
def update_final_result(rid):
    db = get_db()
    fields = ['new_rp_type', 'new_safety_qty', 'new_purchase_group', 'new_planning_cycle',
              'new_delivery_cycle', 'new_stock_planner', 'new_reorder_point', 'new_delivery_days',
              'new_target_coverage', 'new_supply_source', 'new_abc_indicator', 'new_smoothing',
              'new_forecast_model', 'new_historical_periods', 'new_forecast_periods',
              'new_periods_per_season', 'new_current_consumption_qty',
              'new_week1_forecast', 'new_week2_forecast', 'new_week3_forecast',
              'new_week4_forecast', 'new_week5_forecast']
    updates = []
    params = []
    for f in fields:
        val = request.form.get(f, '')
        updates.append(f"{f} = ?")
        params.append(val)
    params.append(rid)
    db.execute(f"UPDATE final_result SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    return redirect(url_for('final_result', site=request.args.get('site',''), article=request.args.get('article',''), rp_type=request.args.get('rp_type','')))

@app.route('/final-result/export')
def export_final_result():
    db = get_db()
    rows = db.execute('SELECT * FROM final_result ORDER BY site, article').fetchall()
    if not rows:
        return redirect(url_for('final_result'))
    keys = rows[0].keys()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(keys)
    for r in rows: writer.writerow([r[k] for k in keys])
    buf.seek(0)
    return Response(buf.getvalue(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=final_result.csv"})

@app.route('/calculate/check-moq')
def calc_check_moq():
    try:
        result = run_check_moq()
        return render_template('calculations.html', data={'step_name': 'MOQ 檢查', 'result_message': f'已更新 {result["updated"]} 筆記錄', 'result': result})
    except Exception as e:
        return render_template('calculations.html', data={'step_name': 'MOQ 檢查', 'result_message': f'錯誤: {str(e)}', 'result': {}})

@app.route('/calculate/apply-ideal-stock')
def calc_apply_ideal_stock():
    try:
        result = apply_ideal_stock()
        return render_template('calculations.html', data={'step_name': '套用理想庫存', 'result_message': f'已更新 {result["updated"]} 筆記錄', 'result': result})
    except Exception as e:
        return render_template('calculations.html', data={'step_name': '套用理想庫存', 'result_message': f'錯誤: {str(e)}', 'result': {}})

@app.route('/calculate/problem-transactions')
def calc_problem_transactions():
    try:
        result = find_problem_transactions()
        return render_template('calculations.html', data={'step_name': '問題交易', 'result_message': f'發現 {result["problem_count"]} 個問題', 'result': result})
    except Exception as e:
        return render_template('calculations.html', data={'step_name': '問題交易', 'result_message': f'錯誤: {str(e)}', 'result': {}})

@app.route('/calculate/type-conversions')
def calc_type_conversions():
    try:
        result = process_type_conversions()
        msg = f'ND→RF: {result["nd_to_rf"]} 筆, RF→ND: {result["rf_to_nd"]} 筆'
        return render_template('calculations.html', data={'step_name': '類型轉換', 'result_message': msg, 'result': result})
    except Exception as e:
        return render_template('calculations.html', data={'step_name': '類型轉換', 'result_message': f'錯誤: {str(e)}', 'result': {}})

@app.route('/reference/shop-class', methods=['GET', 'POST'])
def shop_class():
    db = get_db()
    if request.method == 'POST':
        shop = request.form.get('shop', '')
        cls = request.form.get('class', '')
        cov_a = request.form.get('coverage_a_items', 8)
        cov_b = request.form.get('coverage_b_items', 5)
        cov_c = request.form.get('coverage_c_items', 3)
        status = request.form.get('status', 'M')
        db.execute("INSERT OR REPLACE INTO shop_class (shop, class, status, coverage_a_items, coverage_b_items, coverage_c_items) VALUES (?,?,?,?,?,?)",
                   (shop, cls, status, cov_a, cov_b, cov_c))
        db.commit()
        return redirect(url_for('shop_class'))
    rows = db.execute("SELECT * FROM shop_class ORDER BY shop").fetchall()
    return render_template('reference.html', data={
        'page_title': '店舖分類', 'columns': ['shop', 'class', 'status', 'coverage_a_items', 'coverage_b_items', 'coverage_c_items'],
        'rows': [dict(r) for r in rows],
        'fields': [{'name': 'shop', 'label': 'Shop'}, {'name': 'class', 'label': 'Class'}, {'name': 'status', 'label': 'Status'}]
    })
@app.route('/reference/vendor-schedule', methods=['GET', 'POST'])
def vendor_schedule():
    db = get_db()
    if request.method == 'POST':
        db.execute("INSERT OR REPLACE INTO vendor_schedule (shop, vendor, delivery_s, planning_s, lead_time) VALUES (?,?,?,?,?)",
                   (request.form.get('shop',''), request.form.get('vendor',''), request.form.get('delivery_s',''), request.form.get('planning_s',''), request.form.get('lead_time',0)))
        db.commit()
        return redirect(url_for('vendor_schedule'))
    rows = db.execute("SELECT * FROM vendor_schedule ORDER BY shop, vendor").fetchall()
    return render_template('reference.html', data={
        'page_title': '供應商排程', 'columns': ['shop', 'vendor', 'delivery_s', 'planning_s', 'lead_time'],
        'rows': [dict(r) for r in rows],
        'fields': [{'name': 'shop', 'label': 'Shop'}, {'name': 'vendor', 'label': 'Vendor'}, {'name': 'delivery_s', 'label': 'Delivery S'}, {'name': 'planning_s', 'label': 'Planning S'}, {'name': 'lead_time', 'label': 'Lead Time'}]
    })

@app.route('/reference/warehouse-calendar', methods=['GET', 'POST'])
def warehouse_calendar():
    db = get_db()
    if request.method == 'POST':
        db.execute("INSERT OR REPLACE INTO warehouse_calendar (shop, p, d) VALUES (?,?,?)",
                   (request.form.get('shop',''), request.form.get('p',''), request.form.get('d','')))
        db.commit()
        return redirect(url_for('warehouse_calendar'))
    rows = db.execute("SELECT * FROM warehouse_calendar ORDER BY shop").fetchall()
    return render_template('reference.html', data={
        'page_title': '倉庫日曆', 'columns': ['shop', 'p', 'd'],
        'rows': [dict(r) for r in rows],
        'fields': [{'name': 'shop', 'label': 'Shop'}, {'name': 'p', 'label': 'P'}, {'name': 'd', 'label': 'D'}]
    })

@app.route('/reference/moq')
def moq_list():
    db = get_db()
    rows = db.execute("SELECT * FROM d001_moq ORDER BY sku LIMIT 200").fetchall()
    return render_template('moq.html', data={'rows': [dict(r) for r in rows]})

@app.route('/reference/moq/import', methods=['POST'])
def import_moq():
    file = request.files.get('file')
    if not file: return redirect(url_for('moq_list'))
    path = os.path.join(app.config['UPLOAD_FOLDER'], 'moq_import.csv')
    file.save(path)
    db = get_db()
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.execute("INSERT OR REPLACE INTO d001_moq (sku, moq) VALUES (?,?)", (row.get('sku','') or row.get('SKU',''), row.get('moq',0) or row.get('MOQ',0)))
    db.commit()
    return redirect(url_for('moq_list'))

@app.route('/ideal-stock')
def ideal_stock():
    page = int(request.args.get('page', 1))
    per_page = 100
    offset = (page - 1) * per_page
    db = get_db()
    total = db.execute("SELECT COUNT(*) as c FROM ideal_stock").fetchone()['c']
    rows = db.execute("SELECT * FROM ideal_stock ORDER BY site, article LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
    return render_template('ideal_stock.html', data={
        'rows': [dict(r) for r in rows],
        'page': page, 'total_pages': max(1, (total + per_page - 1) // per_page)
    })

@app.route('/ideal-stock/import', methods=['POST'])
def import_ideal_stock():
    file = request.files.get('file')
    if not file: return redirect(url_for('ideal_stock'))
    path = os.path.join(app.config['UPLOAD_FOLDER'], 'ideal_stock_import.csv')
    file.save(path)
    db = get_db()
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.execute("INSERT OR REPLACE INTO ideal_stock (site, article, ideal_stock) VALUES (?,?,?)",
                       (row.get('site','') or row.get('Site',''), row.get('article','') or row.get('Article',''), row.get('ideal_stock',0) or row.get('Ideal_Stock',0)))
    db.commit()
    return redirect(url_for('ideal_stock'))

@app.route('/output/rp-list')
def output_rp_list():
    db = get_db()
    rows = db.execute("SELECT * FROM rp_list ORDER BY site, article LIMIT 200").fetchall()
    total = db.execute("SELECT COUNT(*) as c FROM rp_list").fetchone()['c']
    return render_template('output.html', data={'page_title': 'RP 清單', 'total_rows': total, 'rows': [dict(r) for r in rows]})

@app.route('/output/mss-list')
def output_mss_list():
    db = get_db()
    rows = db.execute("SELECT * FROM mss_list ORDER BY site, article LIMIT 200").fetchall()
    total = db.execute("SELECT COUNT(*) as c FROM mss_list").fetchone()['c']
    return render_template('output.html', data={'page_title': 'MSS 清單', 'total_rows': total, 'rows': [dict(r) for r in rows]})

@app.route('/output/clear-all')
def output_clear_all():
    try:
        result = clear_all()
        return render_template('calculations.html', data={'step_name': '清除全部', 'result_message': '所有輸出已清除，計算標記已重置', 'result': result})
    except Exception as e:
        return render_template('calculations.html', data={'step_name': '清除全部', 'result_message': f'錯誤: {str(e)}', 'result': {}})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
