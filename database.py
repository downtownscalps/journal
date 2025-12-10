import sqlite3
from pathlib import Path
from settings import BASELINE_EQUITY  # e.g. BASELINE_EQUITY = 0.0

DB_PATH = Path("journal.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Ensure the 'days' and 'trades' tables exist.
    If 'trades' already exists but lacks 'event_type', add it.
    Also clean any duplicate real MT5 deals (ticket > 0).
    """
    conn = get_connection()
    cur = conn.cursor()

    # ---- DAYS TABLE ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS days (
        date TEXT PRIMARY KEY,
        starting_balance REAL,
        ending_balance REAL,
        pnl REAL,
        num_trades INTEGER,
        win_rate REAL
    );
    """)

    # ---- TRADES TABLE ----
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades';")
    exists = cur.fetchone() is not None

    if not exists:
        # Fresh create with full schema
        cur.execute("""
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            ticket INTEGER,
            time TEXT,
            symbol TEXT,
            side TEXT,
            event_type TEXT,
            size REAL,
            entry REAL,
            exit REAL,
            pnl REAL,
            chart_url TEXT,
            commission REAL,
            swap REAL,
            magic INTEGER,
            comment TEXT
        );
        """)
    else:
        # Ensure event_type column exists
        cur.execute("PRAGMA table_info(trades);")
        cols = [row[1] for row in cur.fetchall()]  # row[1] = column name

        if "event_type" not in cols:
            cur.execute("ALTER TABLE trades ADD COLUMN event_type TEXT DEFAULT 'TRADE';")

        # Clean duplicates for real MT5 deals (ticket > 0)
        # Keep the earliest id per ticket, drop the rest
        try:
            cur.execute("""
                DELETE FROM trades
                WHERE ticket > 0
                  AND id NOT IN (
                    SELECT MIN(id) FROM trades
                    WHERE ticket > 0
                    GROUP BY ticket
                  );
            """)
        except sqlite3.OperationalError:
            # If older SQLite without subquery support or empty table, just ignore
            pass

    conn.commit()
    conn.close()


def get_days():
    """
    Return day rows with equity-chained starting/ending balances,
    based on BASELINE_EQUITY from settings.py.
    Ordered DESC (latest day on top).
    """
    conn = get_connection()
    rows = conn.execute("SELECT * FROM days ORDER BY date ASC").fetchall()
    conn.close()

    days = [dict(r) for r in rows]

    equity = float(BASELINE_EQUITY)
    for d in days:
        pnl = d.get("pnl") or 0.0
        try:
            pnl = float(pnl)
        except (TypeError, ValueError):
            pnl = 0.0

        d["starting_balance"] = equity
        equity += pnl
        d["ending_balance"] = equity

    # UI: latest day first
    return list(reversed(days))


def get_trades_by_date(date: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM trades WHERE date = ? ORDER BY time ASC, id ASC",
        (date,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_trade(trade: dict):
    """
    Insert one trade/event row.

    For real MT5 deals (ticket > 0), skip insert if that ticket already exists
    so re-running the script for overlapping history does NOT double-count.
    """
    conn = get_connection()
    cur = conn.cursor()

    ticket = trade.get("ticket", 0)

    # For real MT5 deals, enforce uniqueness on ticket
    if ticket and ticket > 0:
        row = cur.execute(
            "SELECT 1 FROM trades WHERE ticket = ?",
            (ticket,)
        ).fetchone()
        if row:
            # Duplicate deal -> ignore
            conn.close()
            return

    cur.execute("""
        INSERT INTO trades (
            date,
            ticket,
            time,
            symbol,
            side,
            event_type,
            size,
            entry,
            exit,
            pnl,
            chart_url,
            commission,
            swap,
            magic,
            comment
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trade["date"],
        ticket,
        trade.get("time", "00:00:00"),
        trade.get("symbol", ""),
        trade.get("side", ""),
        trade.get("event_type", "TRADE"),
        trade.get("size", 0.0),
        trade.get("entry", 0.0),
        trade.get("exit", 0.0),
        trade.get("pnl", 0.0),
        trade.get("chart_url", ""),
        trade.get("commission", 0.0),
        trade.get("swap", 0.0),
        trade.get("magic", 0),
        trade.get("comment", ""),
    ))
    conn.commit()
    conn.close()


def recompute_day(date: str):
    """
    Recalculate and upsert 'days' row for this date
    based on all trades/events for that date.

    - pnl: sum of *all* pnl (trades + deposits + withdrawals + corrections + ADJ)
    - num_trades: count of TRADE events only
    - win_rate: % of TRADE events with pnl > 0
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM trades WHERE date = ?",
        (date,)
    ).fetchall()

    if not rows:
        conn.close()
        return

    trades = [dict(r) for r in rows]

    total_pnl = sum((t.get("pnl") or 0.0) for t in trades)

    trade_events = [t for t in trades if t.get("event_type") == "TRADE"]
    num_trades = len(trade_events)
    if num_trades:
        wins = sum(1 for t in trade_events if (t.get("pnl") or 0.0) > 0)
        win_rate = wins / num_trades * 100.0
    else:
        win_rate = 0.0

    conn.execute("""
        INSERT INTO days (date, starting_balance, ending_balance, pnl, num_trades, win_rate)
        VALUES (?, 0, 0, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            starting_balance = 0,
            ending_balance = 0,
            pnl = excluded.pnl,
            num_trades = excluded.num_trades,
            win_rate = excluded.win_rate;
    """, (
        date,
        total_pnl,
        num_trades,
        win_rate,
    ))

    conn.commit()
    conn.close()


# ---------- Flows / monthly / yearly ----------

def get_flows():
    """
    Return all DEPOSIT / WITHDRAWAL events sorted by date/time.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT date, time, event_type, symbol, pnl, comment
        FROM trades
        WHERE event_type IN ('DEPOSIT', 'WITHDRAWAL')
        ORDER BY date ASC, time ASC, id ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_monthly_stats():
    """
    Monthly stats grouped by YYYY-MM.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            substr(date, 1, 7) AS month,
            SUM(CASE WHEN event_type = 'TRADE' THEN pnl ELSE 0 END) AS trade_pnl,
            SUM(CASE WHEN event_type <> 'TRADE' THEN pnl ELSE 0 END) AS nontrade_pnl,
            SUM(pnl) AS total_pnl,
            SUM(CASE WHEN event_type = 'TRADE' THEN 1 ELSE 0 END) AS num_trades,
            SUM(CASE WHEN event_type = 'TRADE' AND pnl > 0 THEN 1 ELSE 0 END) AS wins,
            COUNT(DISTINCT CASE WHEN event_type = 'TRADE' THEN date END) AS trade_days
        FROM trades
        GROUP BY month
        ORDER BY month DESC
    """).fetchall()
    conn.close()

    stats = []
    for r in rows:
        d = dict(r)
        num_trades = d.get("num_trades") or 0
        wins = d.get("wins") or 0
        if num_trades:
            win_rate = wins / num_trades * 100.0
        else:
            win_rate = 0.0
        d["win_rate"] = win_rate
        stats.append(d)
    return stats


def get_yearly_stats():
    """
    Yearly stats grouped by YYYY.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            substr(date, 1, 4) AS year,
            SUM(CASE WHEN event_type = 'TRADE' THEN pnl ELSE 0 END) AS trade_pnl,
            SUM(CASE WHEN event_type <> 'TRADE' THEN pnl ELSE 0 END) AS nontrade_pnl,
            SUM(pnl) AS total_pnl,
            SUM(CASE WHEN event_type = 'TRADE' THEN 1 ELSE 0 END) AS num_trades,
            SUM(CASE WHEN event_type = 'TRADE' AND pnl > 0 THEN 1 ELSE 0 END) AS wins,
            COUNT(DISTINCT CASE WHEN event_type = 'TRADE' THEN date END) AS trade_days
        FROM trades
        GROUP BY year
        ORDER BY year DESC
    """).fetchall()
    conn.close()

    stats = []
    for r in rows:
        d = dict(r)
        num_trades = d.get("num_trades") or 0
        wins = d.get("wins") or 0
        if num_trades:
            win_rate = wins / num_trades * 100.0
        else:
            win_rate = 0.0
        d["win_rate"] = win_rate
        stats.append(d)
    return stats
