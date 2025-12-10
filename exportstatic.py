from pathlib import Path
from datetime import datetime

import database


def html_escape(s: str) -> str:
    """Very small HTML escaper."""
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def build_table_days(days):
    rows_html = []
    for d in days:
        pnl = float(d.get("pnl") or 0.0)
        pnl_class = "pos" if pnl >= 0 else "neg"
        rows_html.append(
            f"<tr>"
            f"<td>{html_escape(d['date'])}</td>"
            f"<td>{d['starting_balance']:.2f}</td>"
            f"<td class='{pnl_class}'>{pnl:+.2f}</td>"
            f"<td>{d['ending_balance']:.2f}</td>"
            f"<td>{int(d.get('num_trades') or 0)}</td>"
            f"<td>{float(d.get('win_rate') or 0.0):.1f}%</td>"
            f"</tr>"
        )
    if not rows_html:
        rows_html.append(
            "<tr><td colspan='6'><em>No days found in journal.</em></td></tr>"
        )
    return "\n".join(rows_html)


def build_table_flows(flows):
    rows_html = []
    for f in flows:
        pnl = float(f.get("pnl") or 0.0)
        pnl_class = "pos" if pnl >= 0 else "neg"
        rows_html.append(
            f"<tr>"
            f"<td>{html_escape(f['date'])}</td>"
            f"<td>{html_escape(f.get('time') or '')}</td>"
            f"<td>{html_escape(f.get('event_type') or '')}</td>"
            f"<td>{html_escape(f.get('symbol') or '')}</td>"
            f"<td class='{pnl_class}'>{pnl:+.2f}</td>"
            f"<td>{html_escape(f.get('comment') or '')}</td>"
            f"</tr>"
        )
    if not rows_html:
        rows_html.append(
            "<tr><td colspan='6'><em>No deposits or withdrawals recorded.</em></td></tr>"
        )
    return "\n".join(rows_html)


def build_table_monthly(months):
    rows_html = []
    for m in months:
        trade_pnl = float(m.get("trade_pnl") or 0.0)
        nontrade_pnl = float(m.get("nontrade_pnl") or 0.0)
        total_pnl = float(m.get("total_pnl") or 0.0)
        trade_cls = "pos" if trade_pnl >= 0 else "neg"
        nontrade_cls = "pos" if nontrade_pnl >= 0 else "neg"
        total_cls = "pos" if total_pnl >= 0 else "neg"
        rows_html.append(
            f"<tr>"
            f"<td>{html_escape(m['month'])}</td>"
            f"<td class='{trade_cls}'>{trade_pnl:+.2f}</td>"
            f"<td class='{nontrade_cls}'>{nontrade_pnl:+.2f}</td>"
            f"<td class='{total_cls}'>{total_pnl:+.2f}</td>"
            f"<td>{int(m.get('num_trades') or 0)}</td>"
            f"<td>{int(m.get('trade_days') or 0)}</td>"
            f"<td>{float(m.get('win_rate') or 0.0):.1f}%</td>"
            f"</tr>"
        )
    if not rows_html:
        rows_html.append(
            "<tr><td colspan='7'><em>No monthly stats yet.</em></td></tr>"
        )
    return "\n".join(rows_html)


def build_table_yearly(years):
    rows_html = []
    for y in years:
        trade_pnl = float(y.get("trade_pnl") or 0.0)
        nontrade_pnl = float(y.get("nontrade_pnl") or 0.0)
        total_pnl = float(y.get("total_pnl") or 0.0)
        trade_cls = "pos" if trade_pnl >= 0 else "neg"
        nontrade_cls = "pos" if nontrade_pnl >= 0 else "neg"
        total_cls = "pos" if total_pnl >= 0 else "neg"
        rows_html.append(
            f"<tr>"
            f"<td>{html_escape(y['year'])}</td>"
            f"<td class='{trade_cls}'>{trade_pnl:+.2f}</td>"
            f"<td class='{nontrade_cls}'>{nontrade_pnl:+.2f}</td>"
            f"<td class='{total_cls}'>{total_pnl:+.2f}</td>"
            f"<td>{int(y.get('num_trades') or 0)}</td>"
            f"<td>{int(y.get('trade_days') or 0)}</td>"
            f"<td>{float(y.get('win_rate') or 0.0):.1f}%</td>"
            f"</tr>"
        )
    if not rows_html:
        rows_html.append(
            "<tr><td colspan='7'><em>No yearly stats yet.</em></td></tr>"
        )
    return "\n".join(rows_html)


def build_html(days, flows, months, years):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    days_html = build_table_days(days)
    flows_html = build_table_flows(flows)
    monthly_html = build_table_monthly(months)
    yearly_html = build_table_yearly(years)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>MT5 Trading Journal — Static Report</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 20px;
      background: #f5f5f5;
      color: #111827;
    }}
    h1, h2 {{
      margin-top: 1.5rem;
      margin-bottom: 0.5rem;
    }}
    .meta {{
      font-size: 0.85rem;
      color: #6b7280;
      margin-bottom: 1rem;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin-bottom: 1.5rem;
      font-size: 0.9rem;
      background: #ffffff;
    }}
    th, td {{
      border: 1px solid #d4d4d4;
      padding: 6px 8px;
      text-align: right;
    }}
    th {{
      background: #e5e7eb;
      font-weight: 600;
    }}
    th:first-child, td:first-child {{
      text-align: left;
    }}
    .pos {{
      color: #16a34a;
    }}
    .neg {{
      color: #dc2626;
    }}
    .section {{
      margin-bottom: 2.5rem;
    }}
    .small-note {{
      font-size: 0.8rem;
      color: #6b7280;
    }}
  </style>
</head>
<body>
  <h1>MT5 Trading Journal — Static Report</h1>
  <div class="meta">
    Generated at: {html_escape(generated_at)}<br/>
    This is a read-only snapshot exported from your local journal.
  </div>

  <div class="section">
    <h2>Daily PNL Overview</h2>
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Start</th>
          <th>PnL</th>
          <th>End</th>
          <th># Trades</th>
          <th>Win %</th>
        </tr>
      </thead>
      <tbody>
        {days_html}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>Deposits & Withdrawals</h2>
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Time</th>
          <th>Type</th>
          <th>Symbol</th>
          <th>Amount</th>
          <th>Comment</th>
        </tr>
      </thead>
      <tbody>
        {flows_html}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>Monthly Statistics</h2>
    <table>
      <thead>
        <tr>
          <th>Month</th>
          <th>Trade PnL</th>
          <th>Non-Trade PnL</th>
          <th>Total PnL</th>
          <th># Trades</th>
          <th>Trade Days</th>
          <th>Win %</th>
        </tr>
      </thead>
      <tbody>
        {monthly_html}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>Yearly Statistics</h2>
    <table>
      <thead>
        <tr>
          <th>Year</th>
          <th>Trade PnL</th>
          <th>Non-Trade PnL</th>
          <th>Total PnL</th>
          <th># Trades</th>
          <th>Trade Days</th>
          <th>Win %</th>
        </tr>
      </thead>
      <tbody>
        {yearly_html}
      </tbody>
    </table>
  </div>

  <div class="small-note">
    Backend: MT5 + Flask + SQLite (local).<br/>
    This HTML file can be hosted on GitHub Pages or any static host.
  </div>
</body>
</html>
"""


def main():
    # Make sure DB exists / schema is initialized
    database.init_db()

    # Pull data from your existing functions
    days = database.get_days()
    flows = database.get_flows()
    monthly = database.get_monthly_stats()
    yearly = database.get_yearly_stats()

    # Build HTML
    html = build_html(days, flows, monthly, yearly)

    # Output folder: ./site/index.html
    out_dir = Path("site")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(html, encoding="utf-8")

    print(f"Static report written to: {out_file.resolve()}")


if __name__ == "__main__":
    main()
