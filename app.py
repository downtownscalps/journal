from flask import Flask, render_template, jsonify, request
import json

from database import (
    init_db,
    get_days,
    get_trades_by_date,
    insert_trade,
    recompute_day,
    get_flows,
    get_monthly_stats,
    get_yearly_stats,
)

app = Flask(__name__)

# Ensure DB schema is ready
init_db()


@app.route("/")
def index():
    # Uses templates/pnl.html
    return render_template("pnl.html")


# ---- API: daily summary list (for the main table) ----
@app.route("/api/days")
def api_days():
    days = get_days()
    return jsonify(days)


# ---- API: trades/events for a specific date ----
@app.route("/api/days/<date>/trades")
def api_trades(date):
    trades = get_trades_by_date(date)
    return jsonify(trades)


# ---- API: ingestion endpoint from MT5 (history + live) ----
@app.route("/api/ingest_trade", methods=["POST"])
def ingest_trade_api():
    # MT5 can send trailing nulls; strip whitespace and null bytes
    raw = request.get_data()
    clean = raw.rstrip(b"\x00 \t\r\n")

    try:
        trade = json.loads(clean.decode("utf-8"))
    except Exception as e:
        print("JSON decode error:", e)
        print("Raw body:", raw)
        return {"error": "invalid json", "details": str(e)}, 400

    if "date" not in trade:
        return {"error": "Missing 'date'"}, 400

    # Insert + update day stats
    insert_trade(trade)
    recompute_day(trade["date"])

    return {"status": "ok"}


# ---- Optional admin: manual daily adjustment ----
# POST /api/admin/adjust_day
# { "date": "YYYY-MM-DD", "pnl_adjustment": 100.0 }
@app.route("/api/admin/adjust_day", methods=["POST"])
def admin_adjust_day():
    try:
        payload = request.get_json(force=True)
    except Exception as e:
        return {"error": "invalid json", "details": str(e)}, 400

    date = payload.get("date")
    adj = payload.get("pnl_adjustment")

    if not date or adj is None:
        return {"error": "Missing 'date' or 'pnl_adjustment'"}, 400

    try:
        adj = float(adj)
    except ValueError:
        return {"error": "pnl_adjustment must be numeric"}, 400

    trade = {
        "date": date,
        "ticket": 0,
        "time": "00:00:00",
        "symbol": "ADJ",
        "side": "ADJUST",
        "event_type": "ADJUST",
        "size": 0.0,
        "entry": 0.0,
        "exit": 0.0,
        "pnl": adj,
        "chart_url": "",
        "commission": 0.0,
        "swap": 0.0,
        "magic": 999999,
        "comment": "Manual adjustment",
    }

    insert_trade(trade)
    recompute_day(date)

    return {"status": "ok", "date": date, "pnl_adjustment": adj}


# ---- NEW: Deposit / Withdrawal flows ----
@app.route("/api/flows")
def api_flows():
    flows = get_flows()
    return jsonify(flows)


# ---- NEW: Monthly stats ----
@app.route("/api/stats/monthly")
def api_stats_monthly():
    stats = get_monthly_stats()
    return jsonify(stats)


# ---- NEW: Yearly stats ----
@app.route("/api/stats/yearly")
def api_stats_yearly():
    stats = get_yearly_stats()
    return jsonify(stats)


if __name__ == "__main__":
    print("Running PnL Journal on http://127.0.0.1:5000")
    app.run(debug=True)
